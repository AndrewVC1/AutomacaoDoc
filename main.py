"""
Sistema Automatizado de Envio de Relatórios via WhatsApp Business Cloud API
Autor: EDS - Enterprise Development Solutions
Data: 2025
"""

import os
import re
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import requests
from openpyxl import load_workbook
from config import Config


class RelatorioProcessor:
    """Classe responsável por processar relatórios PDF e enviar via WhatsApp"""
    
    def __init__(self, config: Config):
        self.config = config
        self.setup_logging()
        self.clientes_df = None
        
    def setup_logging(self):
        """Configura o sistema de logs"""
        log_dir = Path(self.config.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"envio_relatorios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 80)
        self.logger.info("INÍCIO DO PROCESSAMENTO DE RELATÓRIOS")
        self.logger.info("=" * 80)
    
    def encontrar_excel_na_pasta(self, pasta_excel: str) -> Optional[str]:
        """Encontra o arquivo Excel na pasta especificada"""
        try:
            pasta_path = Path(pasta_excel)
            if not pasta_path.exists():
                self.logger.error(f"❌ Pasta não encontrada: {pasta_excel}")
                return None
            
            if not pasta_path.is_dir():
                self.logger.error(f"❌ Caminho não é uma pasta: {pasta_excel}")
                return None
            
            # Busca arquivos .xlsx na pasta
            arquivos_xlsx = list(pasta_path.glob("*.xlsx")) + list(pasta_path.glob("*.XLSX"))
            
            if not arquivos_xlsx:
                self.logger.error(f"❌ Nenhum arquivo Excel (.xlsx) encontrado na pasta: {pasta_excel}")
                return None
            
            # Remove duplicatas (case insensitive)
            arquivos_unicos = []
            nomes_vistos = set()
            for xlsx in arquivos_xlsx:
                nome_lower = xlsx.name.lower()
                if nome_lower not in nomes_vistos:
                    nomes_vistos.add(nome_lower)
                    arquivos_unicos.append(xlsx)
            
            if len(arquivos_unicos) > 1:
                self.logger.warning(f"⚠ Múltiplos arquivos Excel encontrados na pasta. Usando o primeiro: {arquivos_unicos[0].name}")
                for i, xlsx in enumerate(arquivos_unicos, 1):
                    self.logger.info(f"   {i}. {xlsx.name}")
            
            excel_path = str(arquivos_unicos[0].resolve())
            self.logger.info(f"✓ Arquivo Excel encontrado: {excel_path}")
            return excel_path
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar Excel na pasta {pasta_excel}: {str(e)}")
            return None
    
    def construir_caminho_pdf(self, id_cliente: str, periodo: Optional[str] = None) -> str:
        """Constrói o caminho do PDF na pasta fixa baseado no ID do cliente e período"""
        pasta_pdfs = Path(self.config.PASTA_PDFS)
        
        # Limpa o ID do cliente (remove .0 de números)
        id_cliente_limpo = str(id_cliente).replace('.0', '').strip()
        
        # Se tiver período, tenta encontrar arquivo com padrão: XPerformance - <id> - Ref.<periodo>.pdf
        if periodo:
            # Remove espaços e caracteres especiais do período para busca
            periodo_limpo = str(periodo).strip()
            # Tenta diferentes variações do nome do arquivo
            possiveis_nomes = [
                f"XPerformance - {id_cliente_limpo} - Ref.{periodo_limpo}.pdf",
                f"XPerformance-{id_cliente_limpo}-Ref.{periodo_limpo}.pdf",
                f"REL_{id_cliente_limpo}_{periodo_limpo}.pdf",
            ]
            
            for nome in possiveis_nomes:
                caminho_completo = pasta_pdfs / nome
                if caminho_completo.exists():
                    return str(caminho_completo.resolve())
        
        # Se não encontrou com período, busca qualquer PDF que contenha o ID do cliente
        # Busca padrão: *<id_cliente>*.pdf
        arquivos_pdf = list(pasta_pdfs.glob(f"*{id_cliente_limpo}*.pdf")) + list(pasta_pdfs.glob(f"*{id_cliente_limpo}*.PDF"))
        
        if arquivos_pdf:
            # Remove duplicatas
            arquivos_unicos = []
            nomes_vistos = set()
            for pdf in arquivos_pdf:
                nome_lower = pdf.name.lower()
                if nome_lower not in nomes_vistos:
                    nomes_vistos.add(nome_lower)
                    arquivos_unicos.append(pdf)
            
            if len(arquivos_unicos) == 1:
                return str(arquivos_unicos[0].resolve())
            elif len(arquivos_unicos) > 1:
                # Se houver múltiplos, retorna o mais recente
                arquivos_unicos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                self.logger.warning(f"⚠ Múltiplos PDFs encontrados para cliente {id_cliente_limpo}. Usando o mais recente: {arquivos_unicos[0].name}")
                return str(arquivos_unicos[0].resolve())
        
        # Se não encontrou, constrói caminho padrão esperado
        if periodo:
            return str(pasta_pdfs / f"XPerformance - {id_cliente_limpo} - Ref.{periodo}.pdf")
        else:
            return str(pasta_pdfs / f"REL_{id_cliente_limpo}.pdf")
        
    def extrair_caminho_hyperlink(self, formula: str) -> Optional[str]:
        """Extrai o caminho do arquivo de uma fórmula HYPERLINK do Excel"""
        try:
            if pd.isna(formula) or not isinstance(formula, str):
                return None
            
            # Padrão: HYPERLINK("caminho"; "texto") ou HYPERLINK("caminho", "texto")
            # Também pode ter referências como & A2 &
            padrao = r'HYPERLINK\(["\']([^"\']+)["\']'
            match = re.search(padrao, formula, re.IGNORECASE)
            
            if match:
                caminho = match.group(1)
                # Remove referências de células se houver (ex: & A2 &)
                caminho = re.sub(r'\s*&\s*A\d+\s*&\s*', '', caminho)
                return caminho
            
            # Se não for fórmula, pode ser o caminho direto
            if os.path.exists(str(formula)):
                return str(formula)
            
            return None
        except Exception as e:
            self.logger.warning(f"Erro ao extrair caminho de HYPERLINK: {str(e)}")
            return None
    
    def carregar_clientes(self) -> bool:
        """Carrega a planilha de clientes da pasta fixa e constrói caminhos dos PDFs"""
        try:
            self.logger.info("\n" + "="*80)
            self.logger.info("ETAPA 1: CARREGANDO PLANILHA DE CLIENTES")
            self.logger.info("="*80)
            
            # Determina o caminho do Excel
            if self.config.EXCEL_CLIENTES and os.path.exists(self.config.EXCEL_CLIENTES):
                # Se EXCEL_CLIENTES foi especificado e existe, usa ele
                excel_path = self.config.EXCEL_CLIENTES
                self.logger.info(f"Usando Excel especificado: {excel_path}")
            else:
                # Caso contrário, busca na pasta fixa
                self.logger.info(f"Buscando Excel na pasta fixa: {self.config.PASTA_EXCEL}")
                excel_path = self.encontrar_excel_na_pasta(self.config.PASTA_EXCEL)
                if not excel_path:
                    self.logger.error(f"❌ ERRO: Não foi possível encontrar o arquivo Excel!")
                    self.logger.error(f"   Pasta verificada: {self.config.PASTA_EXCEL}")
                    return False
            
            self.logger.info(f"✓ Planilha encontrada: {excel_path}")
            self.logger.info("Carregando planilha com openpyxl...")
            
            # Carrega com openpyxl para acessar fórmulas e hyperlinks
            wb = load_workbook(excel_path, data_only=False)
            ws = wb.active
            
            self.logger.info("✓ Planilha carregada com openpyxl")
            self.logger.info(f"   Total de linhas na planilha: {ws.max_row}")
            
            # Lê dados com pandas
            self.logger.info("Lendo dados com pandas...")
            self.clientes_df = pd.read_excel(excel_path)
            self.logger.info(f"✓ Dados lidos: {len(self.clientes_df)} linha(s) encontrada(s)")
            
            # Mapeia nomes de colunas (português para inglês)
            self.logger.info("\nVerificando colunas da planilha...")
            self.logger.info(f"   Colunas encontradas: {list(self.clientes_df.columns)}")
            
            mapeamento_colunas = {
                'Código do Cliente': 'id_cliente',
                'Nome do Cliente': 'nome_cliente',
                'WhatsApp': 'telefone_whatsapp',
                'Caminho do Arquivo': 'caminho_arquivo',
                'Caminho da Pasta': 'caminho_pasta',
                'Mensagem Padrão': 'mensagem_padrao',
                'Período': 'periodo'
            }
            
            # Renomeia colunas se necessário
            colunas_renomeadas = []
            for col_pt, col_en in mapeamento_colunas.items():
                if col_pt in self.clientes_df.columns:
                    self.clientes_df.rename(columns={col_pt: col_en}, inplace=True)
                    colunas_renomeadas.append(f"{col_pt} → {col_en}")
            
            if colunas_renomeadas:
                self.logger.info(f"✓ Colunas renomeadas: {', '.join(colunas_renomeadas)}")
            else:
                self.logger.info("✓ Nenhuma coluna precisou ser renomeada")
            
            # Valida colunas necessárias (caminho_arquivo não é mais obrigatório, será construído)
            self.logger.info("\nValidando colunas necessárias...")
            colunas_necessarias = ['id_cliente', 'nome_cliente', 'telefone_whatsapp']
            colunas_faltantes = [col for col in colunas_necessarias if col not in self.clientes_df.columns]
            
            if colunas_faltantes:
                self.logger.error(f"❌ ERRO: Colunas faltantes na planilha: {', '.join(colunas_faltantes)}")
                self.logger.info(f"   Colunas encontradas: {list(self.clientes_df.columns)}")
                wb.close()
                return False
            
            self.logger.info(f"✓ Todas as colunas necessárias encontradas: {', '.join(colunas_necessarias)}")
            
            # Constrói caminhos dos PDFs na pasta fixa
            self.logger.info("\n" + "="*80)
            self.logger.info("ETAPA 2: CONSTRUINDO CAMINHOS DOS PDFs NA PASTA FIXA")
            self.logger.info("="*80)
            self.logger.info(f"Pasta de PDFs: {self.config.PASTA_PDFS}")
            
            # Verifica se a pasta existe
            pasta_pdfs_path = Path(self.config.PASTA_PDFS)
            if not pasta_pdfs_path.exists():
                self.logger.warning(f"⚠ Pasta de PDFs não encontrada: {self.config.PASTA_PDFS}")
                self.logger.warning("   A pasta será criada automaticamente se necessário")
                pasta_pdfs_path.mkdir(parents=True, exist_ok=True)
            else:
                self.logger.info(f"✓ Pasta de PDFs encontrada: {pasta_pdfs_path.resolve()}")
            
            # Constrói caminhos dos PDFs para cada cliente
            self.logger.info(f"\nConstruindo caminhos dos PDFs para {len(self.clientes_df)} cliente(s)...")
            caminhos_reais = []
            linhas_ignoradas = 0
            
            # Lista de valores que indicam que a linha é um cabeçalho ou exemplo
            valores_cabecalho = [
                'código do cliente', 'codigo do cliente', 'id_cliente', 'id cliente',
                'nome do cliente', 'nome_cliente',
                'whatsapp', 'telefone_whatsapp', 'telefone whatsapp',
                'período', 'periodo',
                'caminho do arquivo', 'caminho_arquivo',
                'mensagem padrão', 'mensagem_padrao'
            ]
            
            for idx, linha in self.clientes_df.iterrows():
                # Limpa o ID do cliente (remove .0 de números)
                id_cliente_raw = linha['id_cliente']
                if pd.isna(id_cliente_raw):
                    id_cliente = None
                else:
                    id_cliente_str = str(id_cliente_raw).strip()
                    # Verifica se é um cabeçalho/exemplo
                    if id_cliente_str.lower() in valores_cabecalho:
                        self.logger.warning(f"    ⚠ Linha {idx + 1} ignorada: parece ser cabeçalho/exemplo (ID: '{id_cliente_str}')")
                        caminhos_reais.append(None)
                        linhas_ignoradas += 1
                        continue
                    
                    try:
                        # Tenta converter para número e depois para string sem .0
                        num_float = float(id_cliente_raw)
                        if num_float.is_integer():
                            id_cliente = str(int(num_float))
                        else:
                            id_cliente = str(num_float)
                    except (ValueError, TypeError):
                        id_cliente = id_cliente_str
                
                periodo = None
                if 'periodo' in linha and pd.notna(linha['periodo']):
                    periodo = str(linha['periodo']).strip()
                
                self.logger.info(f"\n  Cliente {idx + 1} - ID: {id_cliente}")
                
                if not id_cliente or id_cliente.lower() in ['nan', 'none', '']:
                    self.logger.warning(f"    ⚠ ID do cliente vazio ou inválido, pulando...")
                    caminhos_reais.append(None)
                    linhas_ignoradas += 1
                    continue
                
                # Constrói o caminho do PDF
                caminho_pdf = self.construir_caminho_pdf(id_cliente, periodo)
                caminhos_reais.append(caminho_pdf)
                
                if periodo:
                    self.logger.info(f"    ✓ Caminho construído (com período): {caminho_pdf}")
                else:
                    self.logger.info(f"    ✓ Caminho construído (sem período): {caminho_pdf}")
            
            # Adiciona coluna caminho_arquivo com os caminhos construídos
            self.clientes_df['caminho_arquivo'] = caminhos_reais
            
            if linhas_ignoradas > 0:
                self.logger.info(f"\n⚠ {linhas_ignoradas} linha(s) ignorada(s) por serem cabeçalhos/exemplos ou dados inválidos")
            
            # Remove espaços e converte tipos (remove .0 de números)
            # Converte para float primeiro, depois para int se possível, depois para string
            def limpar_numero(valor):
                """Remove .0 de números ao converter para string"""
                if pd.isna(valor):
                    return None
                try:
                    # Tenta converter para float primeiro
                    num_float = float(valor)
                    # Se for um número inteiro (sem parte decimal), converte para int
                    if num_float.is_integer():
                        return str(int(num_float))
                    else:
                        return str(num_float)
                except (ValueError, TypeError):
                    # Se não for número, retorna como string
                    return str(valor).strip()
            
            self.clientes_df['id_cliente'] = self.clientes_df['id_cliente'].apply(limpar_numero)
            self.clientes_df['nome_cliente'] = self.clientes_df['nome_cliente'].astype(str).str.strip()
            self.clientes_df['telefone_whatsapp'] = self.clientes_df['telefone_whatsapp'].apply(limpar_numero)
            
            # Remove linhas com dados inválidos e linhas que são cabeçalhos/exemplos
            total_antes = len(self.clientes_df)
            
            # Lista de valores que indicam que a linha é um cabeçalho ou exemplo
            valores_cabecalho = [
                'código do cliente', 'codigo do cliente', 'id_cliente', 'id cliente',
                'nome do cliente', 'nome_cliente',
                'whatsapp', 'telefone_whatsapp', 'telefone whatsapp',
                'período', 'periodo',
                'caminho do arquivo', 'caminho_arquivo',
                'mensagem padrão', 'mensagem_padrao'
            ]
            
            def eh_linha_valida(linha):
                """Verifica se a linha contém dados válidos (não é cabeçalho/exemplo)"""
                # Verifica se ID do cliente é válido (não é cabeçalho)
                id_cliente_str = str(linha['id_cliente']).strip().lower() if pd.notna(linha['id_cliente']) else ''
                if id_cliente_str in valores_cabecalho or id_cliente_str == '' or id_cliente_str == 'nan' or id_cliente_str == 'none':
                    return False
                
                # Verifica se nome do cliente é válido (não é cabeçalho)
                nome_cliente_str = str(linha['nome_cliente']).strip().lower() if pd.notna(linha['nome_cliente']) else ''
                if nome_cliente_str in valores_cabecalho or nome_cliente_str == '' or nome_cliente_str == 'nan' or nome_cliente_str == 'none':
                    return False
                
                # Verifica se telefone é válido (não é cabeçalho)
                telefone_str = str(linha['telefone_whatsapp']).strip().lower() if pd.notna(linha['telefone_whatsapp']) else ''
                if telefone_str in valores_cabecalho or telefone_str == '' or telefone_str == 'nan' or telefone_str == 'none':
                    return False
                
                # Verifica se o ID do cliente parece ser um número válido
                # IDs de clientes geralmente são números positivos
                try:
                    id_num = float(id_cliente_str)
                    # Se for número muito pequeno, zero ou negativo, provavelmente não é um ID válido
                    if id_num < 1:
                        return False
                except (ValueError, TypeError):
                    # Se não conseguir converter para número, pode ser texto inválido
                    # Mas pode ser um ID alfanumérico válido em alguns casos
                    # Por segurança, vamos rejeitar se não for numérico
                    return False
                
                return True
            
            # Filtra linhas válidas
            self.clientes_df = self.clientes_df[self.clientes_df.apply(eh_linha_valida, axis=1)]
            
            # Remove também linhas com dados faltantes
            self.clientes_df = self.clientes_df[
                (self.clientes_df['id_cliente'].notna()) &
                (self.clientes_df['nome_cliente'].notna()) &
                (self.clientes_df['telefone_whatsapp'].notna()) &
                (self.clientes_df['caminho_arquivo'].notna())
            ]
            total_depois = len(self.clientes_df)
            
            if total_antes != total_depois:
                self.logger.warning(f"⚠ {total_antes - total_depois} linha(s) removida(s) por dados inválidos ou serem cabeçalhos/exemplos")
            
            self.logger.info(f"\n✓ {len(self.clientes_df)} cliente(s) válido(s) carregado(s) com sucesso")
            
            # Mostra resumo dos dados carregados
            self.logger.info("\n" + "="*80)
            self.logger.info("RESUMO DOS DADOS CARREGADOS DO EXCEL")
            self.logger.info("="*80)
            for idx, linha in self.clientes_df.iterrows():
                self.logger.info(f"\n  Cliente {idx + 1}:")
                self.logger.info(f"    ID: {linha['id_cliente']}")
                self.logger.info(f"    Nome: {linha['nome_cliente']}")
                self.logger.info(f"    WhatsApp: {linha['telefone_whatsapp']}")
                if 'periodo' in linha and pd.notna(linha['periodo']):
                    self.logger.info(f"    Período: {linha['periodo']}")
                if 'mensagem_padrao' in linha and pd.notna(linha['mensagem_padrao']):
                    msg = str(linha['mensagem_padrao'])[:60] + "..." if len(str(linha['mensagem_padrao'])) > 60 else str(linha['mensagem_padrao'])
                    self.logger.info(f"    Mensagem: {msg}")
                self.logger.info(f"    Caminho: {linha['caminho_arquivo']}")
            
            # Validação de arquivos e pastas
            self.logger.info("\n" + "="*80)
            self.logger.info("ETAPA 3: VALIDANDO ARQUIVOS E PASTAS")
            self.logger.info("="*80)
            
            arquivos_encontrados = 0
            arquivos_nao_encontrados = 0
            pastas_encontradas = 0
            pastas_nao_encontradas = 0
            
            for idx, linha in self.clientes_df.iterrows():
                caminho_arquivo = linha['caminho_arquivo']
                # Garante que os números não tenham .0
                id_cliente = str(linha['id_cliente']).replace('.0', '') if pd.notna(linha['id_cliente']) else 'N/A'
                nome_cliente = linha['nome_cliente']
                telefone_whatsapp = str(linha.get('telefone_whatsapp', 'N/A')).replace('.0', '') if pd.notna(linha.get('telefone_whatsapp')) else 'N/A'
                periodo = linha.get('periodo', 'N/A')
                mensagem_padrao = linha.get('mensagem_padrao', 'N/A')
                
                # Log dos dados extraídos do Excel
                self.logger.info(f"\n  {'='*70}")
                self.logger.info(f"  DADOS EXTRAÍDOS DO EXCEL - Linha {idx + 1}")
                self.logger.info(f"  {'='*70}")
                self.logger.info(f"    📋 ID do Cliente: {id_cliente}")
                self.logger.info(f"    👤 Nome do Cliente: {nome_cliente}")
                self.logger.info(f"    📱 WhatsApp: {telefone_whatsapp}")
                self.logger.info(f"    📅 Período: {periodo}")
                self.logger.info(f"    📄 Caminho do Arquivo: {caminho_arquivo}")
                if mensagem_padrao != 'N/A' and pd.notna(mensagem_padrao):
                    msg_preview = str(mensagem_padrao)[:80] + "..." if len(str(mensagem_padrao)) > 80 else str(mensagem_padrao)
                    self.logger.info(f"    💬 Mensagem Padrão: {msg_preview}")
                
                # Valida arquivo
                if caminho_arquivo and pd.notna(caminho_arquivo):
                    # Verifica se o caminho não é muito curto ou inválido (ex: "%", ".", etc)
                    caminho_str = str(caminho_arquivo).strip()
                    if len(caminho_str) <= 3 or caminho_str in ['%', '.', '..', 'nan', 'None']:
                        arquivos_nao_encontrados += 1
                        self.logger.error(f"    ❌ Caminho do arquivo inválido ou muito curto: '{caminho_str}'")
                        self.logger.warning(f"    ⚠ Pulando validação de pasta (caminho inválido)")
                        continue
                    
                    caminho_arquivo_path = Path(caminho_arquivo)
                    
                    self.logger.info(f"    Tentando acessar arquivo: {caminho_arquivo}")
                    
                    if caminho_arquivo_path.exists():
                        self.logger.info(f"    ✓ Arquivo existe no sistema")
                        if caminho_arquivo_path.is_file():
                            arquivos_encontrados += 1
                            try:
                                tamanho = caminho_arquivo_path.stat().st_size / 1024  # KB
                                tamanho_mb = tamanho / 1024  # MB
                                self.logger.info(f"    ✓ Arquivo é um arquivo válido")
                                self.logger.info(f"    📄 Tamanho: {tamanho:.2f} KB ({tamanho_mb:.2f} MB)")
                                self.logger.info(f"    📂 Caminho absoluto: {caminho_arquivo_path.resolve()}")
                                
                                # Verifica extensão
                                extensao = caminho_arquivo_path.suffix.lower()
                                self.logger.info(f"    📎 Extensão: {extensao}")
                                
                                if extensao == '.pdf':
                                    self.logger.info(f"    ✓ Extensão PDF confirmada")
                                else:
                                    self.logger.warning(f"    ⚠ Arquivo não é PDF (extensão: {extensao})")
                                
                                # Verifica permissões de leitura
                                try:
                                    with open(caminho_arquivo_path, 'rb') as teste:
                                        teste.read(1)
                                    self.logger.info(f"    ✓ Permissão de leitura: OK")
                                except PermissionError:
                                    self.logger.error(f"    ❌ Sem permissão de leitura no arquivo")
                                except Exception as e:
                                    self.logger.warning(f"    ⚠ Erro ao testar leitura: {str(e)}")
                                    
                            except Exception as e:
                                self.logger.error(f"    ❌ Erro ao obter informações do arquivo: {str(e)}")
                        else:
                            arquivos_nao_encontrados += 1
                            self.logger.error(f"    ❌ Caminho existe mas não é um arquivo")
                    else:
                        arquivos_nao_encontrados += 1
                        self.logger.error(f"    ❌ Arquivo NÃO encontrado: {caminho_arquivo}")
                        self.logger.error(f"    ❌ Verifique se o caminho está correto")
                    
                    # Valida pasta apenas se o arquivo existe ou caminho é válido
                    pasta_arquivo = caminho_arquivo_path.parent
                    
                    # Verifica se a pasta não é o diretório atual (onde está o projeto)
                    if pasta_arquivo.resolve() == Path.cwd():
                        self.logger.warning(f"    ⚠ Pasta do arquivo é o diretório do projeto, pulando validação")
                        pastas_nao_encontradas += 1
                    else:
                        self.logger.info(f"    Tentando acessar pasta: {pasta_arquivo}")
                        
                        if pasta_arquivo.exists():
                            self.logger.info(f"    ✓ Pasta existe no sistema")
                            if pasta_arquivo.is_dir():
                                pastas_encontradas += 1
                                self.logger.info(f"    ✓ Pasta é um diretório válido")
                                self.logger.info(f"    📂 Caminho absoluto da pasta: {pasta_arquivo.resolve()}")
                                
                                # Lista arquivos na pasta (apenas para informação)
                                try:
                                    # Busca PDFs (case insensitive) e remove duplicatas
                                    arquivos_pdf_lower = list(pasta_arquivo.glob("*.pdf"))
                                    arquivos_pdf_upper = list(pasta_arquivo.glob("*.PDF"))
                                    
                                    # Remove duplicatas comparando nomes em lowercase
                                    todos_arquivos = arquivos_pdf_lower + arquivos_pdf_upper
                                    arquivos_unicos = []
                                    nomes_vistos = set()
                                    
                                    for pdf in todos_arquivos:
                                        nome_lower = pdf.name.lower()
                                        if nome_lower not in nomes_vistos:
                                            nomes_vistos.add(nome_lower)
                                            arquivos_unicos.append(pdf)
                                    
                                    self.logger.info(f"    📁 Total de PDFs únicos na pasta: {len(arquivos_unicos)}")
                                    
                                    if len(arquivos_unicos) > 0:
                                        self.logger.info(f"    📋 Arquivos PDF encontrados na pasta:")
                                        for i, pdf in enumerate(arquivos_unicos, 1):
                                            tamanho_pdf = pdf.stat().st_size / 1024  # KB
                                            self.logger.info(f"       {i}. {pdf.name} ({tamanho_pdf:.2f} KB)")
                                    else:
                                        self.logger.info(f"    📋 Nenhum arquivo PDF encontrado na pasta")
                                    
                                    # Verifica permissões de leitura
                                    try:
                                        teste_leitura = list(pasta_arquivo.iterdir())[:1]
                                        self.logger.info(f"    ✓ Permissão de leitura: OK")
                                    except PermissionError:
                                        self.logger.warning(f"    ⚠ Sem permissão de leitura na pasta")
                                        
                                except Exception as e:
                                    self.logger.warning(f"    ⚠ Erro ao listar arquivos da pasta: {str(e)}")
                            else:
                                pastas_nao_encontradas += 1
                                self.logger.error(f"    ❌ Caminho existe mas não é um diretório")
                        else:
                            pastas_nao_encontradas += 1
                            self.logger.error(f"    ❌ Pasta NÃO encontrada: {pasta_arquivo}")
                            self.logger.error(f"    ❌ Verifique se o caminho está correto")
                else:
                    self.logger.warning(f"    ⚠ Caminho do arquivo está vazio ou inválido")
                    arquivos_nao_encontrados += 1
            
            self.logger.info(f"\n📊 Resumo da validação:")
            self.logger.info(f"   Arquivos encontrados: {arquivos_encontrados}/{len(self.clientes_df)}")
            self.logger.info(f"   Arquivos não encontrados: {arquivos_nao_encontrados}")
            self.logger.info(f"   Pastas encontradas: {pastas_encontradas}/{len(self.clientes_df)}")
            self.logger.info(f"   Pastas não encontradas: {pastas_nao_encontradas}")
            
            if arquivos_nao_encontrados > 0:
                self.logger.warning(f"\n⚠ ATENÇÃO: {arquivos_nao_encontrados} arquivo(s) não encontrado(s).")
                self.logger.warning("   Esses arquivos serão pulados durante o processamento.")
            
            wb.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar clientes: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def parse_nome_arquivo(self, nome_arquivo: str) -> Optional[Dict[str, str]]:
        """
        Extrai informações do nome do arquivo
        Padrão esperado: XPerformance - <id_cliente> - Ref.<periodo>.pdf
        Exemplo: XPerformance - 12345 - Ref.31.10.pdf
        """
        try:
            # Remove extensão
            nome_sem_ext = Path(nome_arquivo).stem
            
            # Padrão: XPerformance - <id_cliente> - Ref.<periodo>
            padrao = r'XPerformance\s*-\s*(\d+)\s*-\s*Ref\.(.+)'
            match = re.match(padrao, nome_sem_ext, re.IGNORECASE)
            
            if not match:
                self.logger.warning(f"Formato de arquivo inválido: {nome_arquivo}")
                return None
            
            id_cliente = match.group(1)
            periodo = match.group(2)
            
            return {
                'id_cliente': id_cliente,
                'periodo': periodo,
                'nome_arquivo': nome_arquivo
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar nome do arquivo {nome_arquivo}: {str(e)}")
            return None
    
    def buscar_cliente(self, id_cliente: str) -> Optional[Dict]:
        """Busca informações do cliente na planilha"""
        try:
            cliente = self.clientes_df[self.clientes_df['id_cliente'] == id_cliente]
            
            if cliente.empty:
                return None
            
            cliente_dict = cliente.iloc[0].to_dict()
            return {
                'id_cliente': cliente_dict['id_cliente'],
                'nome_cliente': cliente_dict['nome_cliente'],
                'telefone_whatsapp': cliente_dict['telefone_whatsapp']
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar cliente {id_cliente}: {str(e)}")
            return None
    
    def validar_telefone(self, telefone: str) -> bool:
        """Valida formato do telefone para WhatsApp"""
        # Remove caracteres não numéricos
        telefone_limpo = re.sub(r'\D', '', telefone)
        
        # WhatsApp precisa ter pelo menos 10 dígitos (formato internacional)
        if len(telefone_limpo) < 10:
            return False
        
        return True
    
    def formatar_telefone(self, telefone: str) -> str:
        """Formata telefone para formato internacional (sem +)"""
        telefone_limpo = re.sub(r'\D', '', telefone)
        return telefone_limpo
    
    def upload_media_whatsapp(self, arquivo_path: str) -> Optional[str]:
        """
        Faz upload do arquivo PDF para a API do WhatsApp Business Cloud
        Retorna o media_id se bem-sucedido
        """
        try:
            # Usa a versão mais recente da API
            ver = self.config.WHATSAPP_GRAPH_API_VERSION
            url = f"https://graph.facebook.com/{ver}/{self.config.WHATSAPP_PHONE_NUMBER_ID}/media"
            
            headers = {
                'Authorization': f'Bearer {self.config.WHATSAPP_ACCESS_TOKEN}'
            }
            
            with open(arquivo_path, 'rb') as arquivo:
                files = {
                    'file': (os.path.basename(arquivo_path), arquivo, 'application/pdf')
                }
                data = {
                    'messaging_product': 'whatsapp',
                    'type': 'document'
                }
                
                response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    media_id = response.json().get('id')
                    self.logger.info(f"✓ Upload realizado com sucesso. Media ID: {media_id}")
                    return media_id
                else:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('error', {})
                    error_code = error_msg.get('code', '')
                    error_type = error_msg.get('type', '')
                    error_message = error_msg.get('message', response.text)
                    
                    self.logger.error(f"Erro no upload: {response.status_code}")
                    self.logger.error(f"   Tipo: {error_type} (Código: {error_code})")
                    self.logger.error(f"   Mensagem: {error_message}")
                    
                    # Mensagens específicas para erros comuns
                    if error_code == 190 or 'OAuth' in error_type or 'access token' in error_message.lower():
                        self.logger.error("\n   ⚠ ERRO: Access Token inválido ou expirado!")
                        self.logger.error("   Solução: Gere um novo token em:")
                        self.logger.error("   WhatsApp > API Setup > Temporary access token > Generate token")
                        self.logger.error("   Tokens temporários expiram em 24 horas")
                    
                    return None
                    
        except Exception as e:
            self.logger.error(f"Erro ao fazer upload do arquivo {arquivo_path}: {str(e)}")
            return None
    
    def enviar_mensagem_whatsapp_template(
        self,
        telefone: str,
        media_id: str,
        nome_cliente: str,
        periodo_texto: str,
    ) -> bool:
        """
        Envia mensagem usando template aprovado (header document + corpo com variáveis).
        Espera template no Meta com documento no header e {{1}}=nome, {{2}}=período no corpo.
        """
        try:
            ver = self.config.WHATSAPP_GRAPH_API_VERSION
            url = f"https://graph.facebook.com/{ver}/{self.config.WHATSAPP_PHONE_NUMBER_ID}/messages"
            headers = {
                'Authorization': f'Bearer {self.config.WHATSAPP_ACCESS_TOKEN}',
                'Content-Type': 'application/json',
            }
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': self.formatar_telefone(telefone),
                'type': 'template',
                'template': {
                    'name': self.config.WHATSAPP_TEMPLATE_NAME,
                    'language': {'code': self.config.WHATSAPP_TEMPLATE_LANGUAGE},
                    'components': [
                        {
                            'type': 'header',
                            'parameters': [
                                {
                                    'type': 'document',
                                    'document': {
                                        'id': media_id,
                                        'filename': self.config.WHATSAPP_TEMPLATE_DOCUMENT_FILENAME,
                                    },
                                }
                            ],
                        },
                        {
                            'type': 'body',
                            'parameters': [
                                {'type': 'text', 'text': nome_cliente},
                                {'type': 'text', 'text': periodo_texto},
                            ],
                        },
                    ],
                },
            }
            token = self.config.WHATSAPP_ACCESS_TOKEN or ''
            token_preview = f"{token[:20]}..." if len(token) > 20 else '(vazio)'
            self.logger.info(f"   URL: {url}")
            self.logger.info(f"   Authorization (parcial): Bearer {token_preview}")
            self.logger.info(f"   Payload completo (JSON):\n{json.dumps(payload, indent=6, ensure_ascii=False)}")
            self.logger.info(f"\n   Resumo do payload:")
            self.logger.info(f"      messaging_product: whatsapp")
            self.logger.info(f"      recipient_type: individual")
            self.logger.info(f"      to: {payload['to']}")
            self.logger.info(f"      type: template")
            self.logger.info(f"      template.name: {self.config.WHATSAPP_TEMPLATE_NAME}")
            self.logger.info(f"      template.language: {self.config.WHATSAPP_TEMPLATE_LANGUAGE}")
            self.logger.info(f"      header.document.id: {media_id}")
            self.logger.info(f"      body.parameters[0] ({{1}}): {nome_cliente}")
            self.logger.info(f"      body.parameters[1] ({{2}}): {periodo_texto}")

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                self.logger.info(f"   Resposta da API (status 200):")
                self.logger.info(f"      {json.dumps(response_data, indent=6, ensure_ascii=False)}")
                if 'messages' in response_data:
                    mid = response_data['messages'][0].get('id', 'N/A')
                    self.logger.info(f"✓ Mensagem aceita pela API para {telefone}")
                    self.logger.info(f"   Message ID: {mid}")
                    if 'contacts' in response_data:
                        for contact in response_data['contacts']:
                            self.logger.info(f"   Contato: {contact.get('wa_id', 'N/A')}")
                    return True
                self.logger.warning(f"⚠ Resposta inesperada da API: {response_data}")
                return True
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {})
            self.logger.error(f"Erro ao enviar template: {response.status_code}")
            self.logger.error(f"   Mensagem: {error_msg.get('message', response.text)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar template WhatsApp: {str(e)}")
            return False

    def enviar_mensagem_whatsapp(self, telefone: str, media_id: str, mensagem: str) -> bool:
        """
        Envia mensagem com documento via WhatsApp Business Cloud API (sessão / legenda livre).
        """
        try:
            ver = self.config.WHATSAPP_GRAPH_API_VERSION
            url = f"https://graph.facebook.com/{ver}/{self.config.WHATSAPP_PHONE_NUMBER_ID}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.config.WHATSAPP_ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self.formatar_telefone(telefone),
                "type": "document",
                "document": {
                    "id": media_id,
                    "caption": mensagem
                }
            }
            
            # Log do payload para debug (sem mostrar token completo)
            payload_log = payload.copy()
            self.logger.info(f"payload_log: {payload_log}")
            self.logger.info(f"   URL: {url}")
            self.logger.info(f"   Payload enviado:")
            self.logger.info(f"      messaging_product: {payload_log['messaging_product']}")
            self.logger.info(f"      recipient_type: {payload_log['recipient_type']}")
            self.logger.info(f"      to: {payload_log['to']}")
            self.logger.info(f"      type: {payload_log['type']}")
            self.logger.info(f"      document.id: {payload_log['document']['id']}")
            self.logger.info(f"      document.caption: {payload_log['document']['caption'][:50]}...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Log completo da resposta
                self.logger.info(f"   Resposta da API (status 200):")
                self.logger.info(f"      {json.dumps(response_data, indent=6, ensure_ascii=False)}")
                
                # Verifica se há avisos ou erros na resposta
                if 'messages' in response_data:
                    message_id = response_data['messages'][0].get('id', 'N/A')
                    self.logger.info(f"✓ Mensagem aceita pela API para {telefone}")
                    self.logger.info(f"   Message ID: {message_id}")
                    
                    # Verifica status da mensagem (se disponível)
                    if 'contacts' in response_data:
                        for contact in response_data['contacts']:
                            self.logger.info(f"   Contato: {contact.get('wa_id', 'N/A')}")
                    
                    # Verifica se há avisos
                    if 'warnings' in response_data:
                        for warning in response_data['warnings']:
                            self.logger.warning(f"   ⚠ Aviso: {warning.get('message', '')}")
                    
                    # Aviso sobre números de teste
                    self.logger.warning("\n   ⚠ IMPORTANTE: Você está usando um NÚMERO DE TESTE!")
                    self.logger.warning("   Números de teste podem não entregar mensagens reais.")
                    self.logger.warning("   Para produção, você precisa verificar seu número real do WhatsApp Business.")
                    self.logger.warning("   A mensagem foi aceita pela API, mas pode não chegar ao destinatário.")
                    self.logger.warning("\n   DICA: Teste primeiro com 'Enviar mensagem' na interface do Facebook")
                    self.logger.warning("   para confirmar que o número de teste está funcionando.")
                    
                    return True
                else:
                    self.logger.warning(f"⚠ Resposta inesperada da API: {response_data}")
                    return True  # Ainda considera sucesso se status 200
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {})
                error_code = error_msg.get('code', '')
                error_type = error_msg.get('type', '')
                error_message = error_msg.get('message', response.text)
                error_details = error_msg.get('error_data', {}).get('details', '')
                
                self.logger.error(f"Erro ao enviar mensagem: {response.status_code}")
                self.logger.error(f"   Tipo: {error_type} (Código: {error_code})")
                self.logger.error(f"   Mensagem: {error_message}")
                if error_details:
                    self.logger.error(f"   Detalhes: {error_details}")
                
                # Mensagens específicas para erros comuns
                if error_code == 131030 or 'not in allowed list' in error_message.lower() or 'lista de permissão' in error_message.lower():
                    telefone_formatado = self.formatar_telefone(telefone)
                    self.logger.error("\n   ⚠ ERRO: Número do destinatário não está na lista de permissão!")
                    self.logger.error(f"   Número tentado: {telefone_formatado}")
                    self.logger.error("   Solução: Adicione o número à lista de números de teste:")
                    self.logger.error("   1. Acesse: WhatsApp > API Setup (ou Configuração da API)")
                    self.logger.error("   2. Na seção 'Até' (To), adicione o número:")
                    self.logger.error(f"      {telefone_formatado}")
                    self.logger.error("   3. No modo de teste, você pode adicionar até 5 números")
                    self.logger.error("   4. Execute o sistema novamente após adicionar")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
            return False
    
    def processar_relatorio_linha(self, linha_cliente: pd.Series, whatsapp_configurado: bool = True) -> Dict[str, any]:
        """
        Processa um único relatório baseado em uma linha da planilha
        """
        id_cliente = str(linha_cliente['id_cliente']).strip()
        nome_cliente = str(linha_cliente['nome_cliente']).strip()
        telefone = str(linha_cliente['telefone_whatsapp']).strip()
        caminho_arquivo = str(linha_cliente['caminho_arquivo']).strip()
        
        # Mensagem padrão do Excel ou template padrão
        mensagem_padrao = None
        if 'mensagem_padrao' in linha_cliente and pd.notna(linha_cliente['mensagem_padrao']):
            mensagem_padrao = str(linha_cliente['mensagem_padrao']).strip()
        
        # Período do Excel ou extraído do nome do arquivo
        periodo = None
        if 'periodo' in linha_cliente and pd.notna(linha_cliente['periodo']):
            periodo = str(linha_cliente['periodo']).strip()
        
        nome_arquivo = Path(caminho_arquivo).name
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"Processando: {nome_arquivo}")
        self.logger.info(f"Cliente: {nome_cliente} (ID: {id_cliente})")
        self.logger.info(f"{'='*80}")
        
        resultado = {
            'arquivo': nome_arquivo,
            'cliente': nome_cliente,
            'id_cliente': id_cliente,
            'sucesso': False,
            'erro': None,
            'periodo': periodo,
            'enviado': False
        }
        
        # 1. Validar se arquivo existe
        self.logger.info(f"\n  [1/6] Validando existência do arquivo...")
        self.logger.info(f"      Caminho completo: {caminho_arquivo}")
        
        if not os.path.exists(caminho_arquivo):
            resultado['erro'] = f"Arquivo não encontrado: {caminho_arquivo}"
            self.logger.error(f"      ❌ {resultado['erro']}")
            return resultado
        
        arquivo_path = Path(caminho_arquivo)
        tamanho_arquivo = arquivo_path.stat().st_size / 1024  # KB
        self.logger.info(f"      ✓ Arquivo encontrado! Tamanho: {tamanho_arquivo:.2f} KB")
        
        # 2. Extrair período do nome do arquivo se não estiver no Excel
        self.logger.info(f"\n  [2/6] Extraindo informações do arquivo...")
        self.logger.info(f"      Nome do arquivo: {nome_arquivo}")
        
        if not periodo:
            self.logger.info(f"      Período não encontrado no Excel, tentando extrair do nome...")
            info_arquivo = self.parse_nome_arquivo(nome_arquivo)
            if info_arquivo:
                periodo = info_arquivo['periodo']
                resultado['periodo'] = periodo
                self.logger.info(f"      ✓ Período extraído: {periodo}")
            else:
                self.logger.warning(f"      ⚠ Não foi possível extrair período do nome do arquivo")
        else:
            self.logger.info(f"      ✓ Período do Excel: {periodo}")
        
        # 3. Validar telefone
        self.logger.info(f"\n  [3/6] Validando telefone WhatsApp...")
        self.logger.info(f"      Telefone original: {telefone}")
        
        if not self.validar_telefone(telefone):
            resultado['erro'] = f"Telefone inválido: {telefone}"
            self.logger.warning(f"      ❌ {resultado['erro']}")
            return resultado
        
        telefone_formatado = self.formatar_telefone(telefone)
        self.logger.info(f"      ✓ Telefone válido! Formato internacional: {telefone_formatado}")
        
        usar_template_meta = (
            self.config.WHATSAPP_USE_MESSAGE_TEMPLATE
            and bool(str(self.config.WHATSAPP_TEMPLATE_NAME or '').strip())
        )
        periodo_para_corpo = periodo if periodo else "período informado"

        # 4. Texto (legenda livre) ou dados do template aprovado no Meta
        if usar_template_meta:
            self.logger.info(f"\n  [4/6] Preparando dados para o template aprovado...")
            self.logger.info(f"      ✓ Template: {self.config.WHATSAPP_TEMPLATE_NAME}")
            self.logger.info(f"      ✓ Nome do cliente ({{1}}): {nome_cliente}")
            self.logger.info(f"      ✓ Período ({{2}}): {periodo_para_corpo}")
            if mensagem_padrao:
                self.logger.info(f"      ⚠ Nota: Mensagem padrão do Excel será ignorada (usando template aprovado)")
            mensagem = None
        else:
            self.logger.info(f"\n  [4/6] Preparando mensagem (documento + legenda)...")
            if mensagem_padrao:
                mensagem = mensagem_padrao
                self.logger.info(f"      ✓ Usando mensagem padrão do Excel")
                self.logger.info(f"      Mensagem: {mensagem[:100]}..." if len(mensagem) > 100 else f"      Mensagem: {mensagem}")
            else:
                mensagem = self.config.MENSAGEM_TEMPLATE.format(
                    nome=nome_cliente,
                    periodo=periodo_para_corpo
                )
                self.logger.info(f"      ✓ Usando texto padrão configurado (MENSAGEM_TEMPLATE)")
                self.logger.info(f"      Mensagem: {mensagem}")
        
        # 5. Upload do arquivo (apenas se WhatsApp configurado)
        if whatsapp_configurado:
            self.logger.info(f"\n  [5/6] Fazendo upload do arquivo para WhatsApp API...")
            self.logger.info(f"      Arquivo: {nome_arquivo} ({tamanho_arquivo:.2f} KB)")
            media_id = self.upload_media_whatsapp(caminho_arquivo)
            if not media_id:
                resultado['erro'] = "Falha no upload do arquivo"
                self.logger.error(f"      ❌ {resultado['erro']}")
                return resultado
            
            self.logger.info(f"      ✓ Upload concluído! Media ID: {media_id}")
            
            # 6. Enviar mensagem
            if usar_template_meta:
                self.logger.info(f"\n  [6/6] Enviando mensagem via WhatsApp usando template...")
            else:
                self.logger.info(f"\n  [6/6] Enviando mensagem via WhatsApp (documento + legenda)...")
            self.logger.info(f"      Destinatário: {telefone_formatado}")
            self.logger.info(f"      Cliente: {nome_cliente}")
            if usar_template_meta:
                enviado = self.enviar_mensagem_whatsapp_template(
                    telefone_formatado,
                    media_id,
                    nome_cliente,
                    periodo_para_corpo,
                )
            else:
                enviado = self.enviar_mensagem_whatsapp(
                    telefone_formatado,
                    media_id,
                    mensagem,
                )
            
            if enviado:
                resultado['sucesso'] = True
                resultado['enviado'] = True
                self.logger.info(f"✓✓✓ RELATÓRIO ENVIADO COM SUCESSO! ✓✓✓")
            else:
                resultado['erro'] = "Falha no envio da mensagem"
        else:
            # Modo validação - apenas valida sem enviar
            self.logger.info(f"\n  [5/6] Validação completa - WhatsApp não configurado")
            self.logger.info(f"      ✓ Todos os dados validados com sucesso!")
            self.logger.info(f"      ✓ Arquivo: {nome_arquivo} ({tamanho_arquivo:.2f} KB)")
            self.logger.info(f"      ✓ Telefone: {telefone_formatado}")
            if mensagem:
                self.logger.info(f"      ✓ Mensagem preparada: {mensagem[:50]}...")
            self.logger.info(f"\n  [6/6] Modo validação - Nenhum envio realizado")
            resultado['sucesso'] = True
            resultado['enviado'] = False
            resultado['modo_validacao'] = True
            self.logger.info(f"✓✓✓ VALIDAÇÃO CONCLUÍDA COM SUCESSO! ✓✓✓")
        
        return resultado
    
    def processar_planilha(self, whatsapp_configurado: bool = True) -> List[Dict]:
        """
        Processa todos os relatórios da planilha
        """
        if self.clientes_df is None or len(self.clientes_df) == 0:
            self.logger.error("Nenhum cliente carregado da planilha")
            return []
        
        self.logger.info(f"\n" + "="*80)
        if whatsapp_configurado:
            self.logger.info("ETAPA 4: PROCESSANDO RELATÓRIOS E ENVIANDO VIA WHATSAPP")
        else:
            self.logger.info("ETAPA 4: VALIDANDO RELATÓRIOS (SEM ENVIO - WhatsApp não configurado)")
        self.logger.info("="*80)
        self.logger.info(f"Total de cliente(s) para processar: {len(self.clientes_df)}")
        if not whatsapp_configurado:
            self.logger.info("⚠ MODO VALIDAÇÃO: Nenhum envio será realizado")
        self.logger.info(f"{'='*80}\n")
        
        resultados = []
        
        for idx, linha in self.clientes_df.iterrows():
            self.logger.info(f"\n{'#'*80}")
            self.logger.info(f"PROCESSANDO CLIENTE {idx + 1}/{len(self.clientes_df)}")
            self.logger.info(f"{'#'*80}")
            resultado = self.processar_relatorio_linha(linha, whatsapp_configurado)
            resultados.append(resultado)
        
        return resultados
    
    def gerar_relatorio_final(self, resultados: List[Dict]):
        """Gera relatório final com estatísticas"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info("RELATÓRIO FINAL DE PROCESSAMENTO")
        self.logger.info(f"{'='*80}")
        
        total = len(resultados)
        sucessos = sum(1 for r in resultados if r['sucesso'])
        erros = total - sucessos
        
        self.logger.info(f"Total de arquivos processados: {total}")
        self.logger.info(f"Enviados com sucesso: {sucessos}")
        self.logger.info(f"Erros: {erros}")
        
        if erros > 0:
            self.logger.info("\nArquivos com erro:")
            for r in resultados:
                if not r['sucesso']:
                    self.logger.info(f"  - {r['arquivo']}: {r['erro']}")
        
        # Salva relatório em JSON
        relatorio_json = {
            'data_processamento': datetime.now().isoformat(),
            'total': total,
            'sucessos': sucessos,
            'erros': erros,
            'resultados': resultados
        }
        
        relatorio_path = Path(self.config.LOG_DIR) / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio_json, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\nRelatório JSON salvo em: {relatorio_path}")
        self.logger.info(f"{'='*80}\n")


def main():
    """Função principal"""
    try:
        print("\n" + "="*80)
        print("SISTEMA AUTOMATIZADO DE ENVIO DE RELATÓRIOS VIA WHATSAPP")
        print("="*80)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Carrega configurações
        print("\nCarregando configurações...")
        config = Config()
        
        print(f"  Pasta do Excel: {config.PASTA_EXCEL}")
        print(f"  Pasta dos PDFs: {config.PASTA_PDFS}")
        print(f"  Pasta de logs: {config.LOG_DIR}")
        print(f"  WhatsApp Phone Number ID: {config.WHATSAPP_PHONE_NUMBER_ID[:10]}..." if len(config.WHATSAPP_PHONE_NUMBER_ID) > 10 else f"  WhatsApp Phone Number ID: {config.WHATSAPP_PHONE_NUMBER_ID}")
        
        # Valida configurações do WhatsApp (opcional para validação)
        print("\nValidando configurações do WhatsApp...")
        whatsapp_configurado = config.validar_configuracao()
        
        if not whatsapp_configurado:
            print("\n⚠ AVISO: Configurações do WhatsApp não encontradas")
            print("   O sistema continuará apenas para VALIDAÇÃO de dados")
            print("   Nenhum envio será realizado sem as configurações do WhatsApp")
            print("   Configure o WHATSAPP_ACCESS_TOKEN e WHATSAPP_PHONE_NUMBER_ID no config.py")
        else:
            print("  ✓ Configurações do WhatsApp validadas")
        
        print("\n" + "="*80)
        print("INICIANDO VALIDAÇÃO DE DADOS...")
        print("="*80)
        
        # Cria processador
        processor = RelatorioProcessor(config)
        
        # Carrega clientes
        if not processor.carregar_clientes():
            print("\n❌ ERRO: Não foi possível carregar a planilha de clientes")
            print("   Verifique os logs acima para mais detalhes")
            return
        
        # Processa relatórios da planilha
        print("\n" + "="*80)
        print("RESUMO DA VALIDAÇÃO")
        print("="*80)
        print(f"Pasta do Excel: {config.PASTA_EXCEL}")
        print(f"Pasta dos PDFs: {config.PASTA_PDFS}")
        print(f"Total de clientes carregados: {len(processor.clientes_df)}")
        
        if whatsapp_configurado:
            print("\n⚠ ATENÇÃO: Os envios para o WhatsApp serão realizados agora!")
        else:
            print("\n⚠ MODO VALIDAÇÃO: Nenhum envio será realizado")
            print("   Apenas validação de dados será executada")
        
        # Processa relatórios
        resultados = processor.processar_planilha(whatsapp_configurado)
        
        if resultados:
            processor.gerar_relatorio_final(resultados)
        else:
            processor.logger.warning("Nenhum relatório foi processado")
        
        print("\nProcessamento concluído! Verifique os logs para mais detalhes.")
        
    except KeyboardInterrupt:
        print("\n\nProcessamento interrompido pelo usuário.")
    except Exception as e:
        print(f"\nERRO CRÍTICO: {str(e)}")
        logging.error(f"Erro crítico: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

