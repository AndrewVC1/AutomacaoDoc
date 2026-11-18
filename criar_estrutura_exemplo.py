"""
Script auxiliar para criar estrutura de exemplo do projeto
"""

import os
from pathlib import Path
import pandas as pd


def criar_estrutura():
    """Cria estrutura de pastas e arquivos de exemplo"""
    
    print("Criando estrutura de exemplo...")
    
    # Cria pastas
    pastas = ['logs', 'relatorios']
    for pasta in pastas:
        Path(pasta).mkdir(exist_ok=True)
        print(f"✓ Pasta '{pasta}' criada")
    
    # Cria planilha de exemplo
    dados_exemplo = {
        'id_cliente': ['12345', '67890', '11111'],
        'nome_cliente': ['Cliente Exemplo 1', 'Cliente Exemplo 2', 'Cliente Exemplo 3'],
        'telefone_whatsapp': ['5511999999999', '5511888888888', '5511777777777']
    }
    
    df = pd.DataFrame(dados_exemplo)
    df.to_excel('clientes.xlsx', index=False)
    print("✓ Arquivo 'clientes.xlsx' criado com exemplo")
    
    # Cria arquivo README de instruções rápidas
    instrucoes = """
INSTRUÇÕES RÁPIDAS:

1. Configure o arquivo config.py com suas credenciais do WhatsApp Business API
2. Preencha a planilha clientes.xlsx com seus clientes reais
3. Coloque os PDFs na pasta relatorios/ (formato: REL_<id_cliente>_<periodo>.pdf)
4. Execute: python main.py

IMPORTANTE:
- Os PDFs devem seguir o padrão: REL_<id_cliente>_<periodo>.pdf
- Os telefones devem estar no formato internacional (ex: 5511999999999)
- Os IDs dos clientes devem corresponder entre o nome do arquivo e a planilha
"""
    
    with open('INSTRUCOES.txt', 'w', encoding='utf-8') as f:
        f.write(instrucoes)
    
    print("✓ Arquivo 'INSTRUCOES.txt' criado")
    print("\n" + "="*60)
    print("Estrutura criada com sucesso!")
    print("="*60)
    print("\nPróximos passos:")
    print("1. Configure config.py com suas credenciais")
    print("2. Preencha clientes.xlsx com dados reais")
    print("3. Adicione seus PDFs na pasta relatorios/")
    print("4. Execute: python main.py")


if __name__ == "__main__":
    criar_estrutura()

