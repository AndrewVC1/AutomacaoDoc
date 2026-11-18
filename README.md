# AutomacaoDoc

Estrutura de exemplo para enviar relatórios PDF pelo WhatsApp Business Cloud API.

O repositório não traz credenciais, planilhas nem PDFs. Copie `.env.example` para `.env` e preencha com os dados da sua conta na Meta.

## O que cada arquivo faz

- `main.py` lê a planilha, localiza o PDF de cada cliente e envia a mensagem.
- `config.py` lê as configurações do ambiente.
- `webhook.py` recebe status e mensagens da API.
- `.env.example` lista as variáveis usadas pelo projeto.
- `criar_estrutura_exemplo.py` gera uma planilha de demonstração.

## Como executar

```bash
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Sem token e sem Phone Number ID, o `main.py` apenas valida a planilha e os PDFs.

Pastas padrão, se não forem alteradas no `.env`:

- planilha: `C:/PlanilhaRelatorios`
- PDFs: `C:/Relatoriosautomatizados`

O nome esperado do PDF é `XPerformance - 12345 - Ref.31.10.pdf`.

Para o webhook:

```bash
python webhook.py
```

O servidor sobe na porta `8000`. Os passos da Meta estão em `GUIA_CONFIGURACAO_WHATSAPP.md` e `GUIA_WEBHOOK.md`.
