"""
Arquivo de Configuração do Sistema de Envio de Relatórios
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Classe de configuração do sistema"""
    
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')

    # Graph API (mídia + mensagens). Alinhar com o app no Meta (ex.: v24.0).
    WHATSAPP_GRAPH_API_VERSION = os.getenv('WHATSAPP_GRAPH_API_VERSION', 'v24.0')

    # Envio com template aprovado (recomendado para mensagens iniciadas pela empresa).
    _use_tpl = os.getenv('WHATSAPP_USE_MESSAGE_TEMPLATE', 'true').strip().lower()
    WHATSAPP_USE_MESSAGE_TEMPLATE = _use_tpl in ('1', 'true', 'yes', 'sim', 'on')
    WHATSAPP_TEMPLATE_NAME = os.getenv('WHATSAPP_TEMPLATE_NAME', 'relatorios')
    WHATSAPP_TEMPLATE_LANGUAGE = os.getenv('WHATSAPP_TEMPLATE_LANGUAGE', 'pt_BR')
    WHATSAPP_TEMPLATE_DOCUMENT_FILENAME = os.getenv('WHATSAPP_TEMPLATE_DOCUMENT_FILENAME', 'relatorio.pdf')

    PASTA_EXCEL = os.getenv('PASTA_EXCEL', r'C:\PlanilhaRelatorios')

    PASTA_PDFS = os.getenv('PASTA_PDFS', r'C:\Relatoriosautomatizados')

    EXCEL_CLIENTES = os.getenv('EXCEL_CLIENTES', None)
    
    # Pasta onde serão salvos os logs
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    MENSAGEM_TEMPLATE = os.getenv(
        'MENSAGEM_TEMPLATE',
        'Olá, {nome}, segue seu relatório referente ao período {periodo}.'
    )
    
    def validar_configuracao(self) -> bool:
        """Valida se as configurações essenciais estão preenchidas"""
        erros = []
        
        # Remove espaços e verifica se está configurado
        token_limpo = str(self.WHATSAPP_ACCESS_TOKEN).strip() if self.WHATSAPP_ACCESS_TOKEN else ''
        phone_id_limpo = str(self.WHATSAPP_PHONE_NUMBER_ID).strip() if self.WHATSAPP_PHONE_NUMBER_ID else ''
        
        if not token_limpo or token_limpo == 'SEU_ACCESS_TOKEN_AQUI' or len(token_limpo) < 50:
            erros.append("WHATSAPP_ACCESS_TOKEN não configurado ou inválido")
        
        if not phone_id_limpo or phone_id_limpo == 'SEU_PHONE_NUMBER_ID_AQUI' or len(phone_id_limpo) < 10:
            erros.append("WHATSAPP_PHONE_NUMBER_ID não configurado ou inválido")
        
        if erros:
            print("ERROS DE CONFIGURAÇÃO:")
            for erro in erros:
                print(f"  - {erro}")
            print("\nConfigure as variáveis no arquivo config.py ou como variáveis de ambiente")
            print("\n⚠ IMPORTANTE: Se o token expirou, gere um novo em:")
            print("   WhatsApp > API Setup > Temporary access token > Generate token")
            return False
        
        return True
    
    @staticmethod
    def criar_arquivo_exemplo_clientes():
        """Cria arquivo Excel de exemplo com estrutura de clientes"""
        import pandas as pd
        
        dados_exemplo = {
            'id_cliente': ['12345', '67890', '11111'],
            'nome_cliente': ['Cliente Exemplo 1', 'Cliente Exemplo 2', 'Cliente Exemplo 3'],
            'telefone_whatsapp': ['5511999999999', '5511888888888', '5511777777777']
        }
        
        df = pd.DataFrame(dados_exemplo)
        df.to_excel('clientes_exemplo.xlsx', index=False)
        print("Arquivo 'clientes_exemplo.xlsx' criado com sucesso!")


if __name__ == "__main__":
    # Permite criar arquivo de exemplo
    config = Config()
    config.criar_arquivo_exemplo_clientes()

