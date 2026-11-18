# Guia de Configuração do Webhook WhatsApp

Este guia explica como configurar e usar o servidor webhook para receber notificações do WhatsApp Business Cloud API.

## 📋 O que é um Webhook?

Um webhook é um endpoint HTTP que recebe notificações em tempo real do WhatsApp sobre:
- ✅ Status de mensagens enviadas (enviada, entregue, lida, falhou)
- ✅ Mensagens recebidas dos clientes
- ✅ Outros eventos do WhatsApp Business API

## 🚀 Configuração Passo a Passo

### ETAPA 1: Configurar o Token de Verificação

1. Abra o arquivo `config.py`
2. Configure o `WHATSAPP_WEBHOOK_VERIFY_TOKEN` com uma string segura:

```python
WHATSAPP_WEBHOOK_VERIFY_TOKEN = 'seu_token_secreto_aqui'
```

**IMPORTANTE:** Escolha um token forte e único. Exemplo: `meu_token_webhook_2025_xyz123`

### ETAPA 2: Instalar Dependências

```bash
pip install -r requirements.txt
```

### ETAPA 3: Executar o Servidor Webhook

```bash
python webhook.py
```

O servidor iniciará na porta 5000 por padrão. Você verá:

```
================================================================================
INICIANDO SERVIDOR WEBHOOK DO WHATSAPP
================================================================================
Token de verificação: seu_token_secreto_aqui
Endpoint: /webhook-whatsapp
Porta padrão: 5000
================================================================================
```

### ETAPA 4: Expor o Servidor Publicamente

Para que a Meta possa enviar notificações, o servidor precisa estar acessível publicamente.

#### Opção A: Usando ngrok (Recomendado para testes)

1. Instale o ngrok: https://ngrok.com/download
2. Em outro terminal, execute:
   ```bash
   ngrok http 5000
   ```
3. Copie a URL HTTPS fornecida (ex: `https://abc123.ngrok.io`)

#### Opção B: Usando Cloudflare Tunnel

1. Instale cloudflared
2. Execute: `cloudflared tunnel --url http://localhost:5000`
3. Use a URL fornecida

#### Opção C: Deploy em Servidor (Produção)

- Deploy em servidor com IP público
- Configure domínio e certificado SSL
- Use a URL completa: `https://seu-dominio.com/webhook-whatsapp`

### ETAPA 5: Configurar o Webhook na Meta

1. Acesse o [Facebook Developers](https://developers.facebook.com/)
2. Vá em **Meus Apps** > Selecione seu app
3. Vá em **WhatsApp** > **Configuração** (ou **Configuration**)
4. Role até a seção **Webhook**
5. Clique em **Configurar webhook** ou **Editar**
6. Preencha:
   - **URL do retorno de chamada**: `https://sua-url-publica.com/webhook-whatsapp`
   - **Token de verificação**: O mesmo token configurado no `config.py`
7. Clique em **Verificar e salvar**

### ETAPA 6: Assinar Eventos

Após configurar o webhook, você precisa assinar os eventos que deseja receber:

1. Na mesma página de configuração do webhook
2. Marque os eventos desejados:
   - ✅ **messages** - Receber mensagens dos clientes
   - ✅ **message_status** - Receber status de mensagens enviadas
3. Clique em **Salvar**

## 📊 Verificando se Está Funcionando

### Teste 1: Verificação do Webhook

Quando você configurar o webhook na Meta, ela enviará um GET request para verificar. Você verá nos logs:

```
VERIFICAÇÃO DO WEBHOOK - GET REQUEST
Mode: subscribe
Token recebido: seu_token_secreto_aqui
✓ Verificação bem-sucedida! Retornando challenge...
```

### Teste 2: Enviar uma Mensagem

1. Execute o `main.py` para enviar uma mensagem
2. O webhook receberá notificações de status
3. Verifique os logs em `logs/webhook_YYYYMMDD.log`

### Teste 3: Health Check

Acesse no navegador:
- `http://localhost:5000/health` - Status do servidor
- `http://localhost:5000/` - Informações do webhook

## 📝 Logs

Os logs são salvos em:
- `logs/webhook_YYYYMMDD.log` - Log diário do webhook

Exemplo de log de notificação:

```
================================================================================
NOTIFICAÇÃO RECEBIDA - POST REQUEST
================================================================================
Timestamp: 2025-03-09 20:15:30
Dados recebidos: {
  "object": "whatsapp_business_account",
  "entry": [...]
}

PROCESSANDO ENTRY
--------------------------------------------------------------------------------
Entry ID: 123456789

  📋 Campo: messages
  📤 STATUS DE MENSAGEM ENVIADA
    📨 Message ID: wamid.xxx
    📱 Destinatário: 5511999999999
    📊 Status: delivered
    ✓ Mensagem entregue ao destinatário
```

## 🔧 Configurações Avançadas

### Alterar Porta

```bash
# Windows PowerShell
$env:WEBHOOK_PORT="8080"
python webhook.py

# Linux/Mac
export WEBHOOK_PORT=8080
python webhook.py
```

### Alterar Host

```bash
# Para aceitar apenas conexões locais
$env:WEBHOOK_HOST="127.0.0.1"
python webhook.py

# Para aceitar conexões externas (padrão)
$env:WEBHOOK_HOST="0.0.0.0"
python webhook.py
```

## ⚠️ Troubleshooting

### Erro: "Verification failed"

- Verifique se o token no `config.py` é **exatamente igual** ao configurado na Meta
- Certifique-se de que o servidor está rodando quando configurar o webhook

### Erro: "Connection refused"

- Verifique se o servidor está rodando
- Verifique se a porta está correta
- Verifique se o firewall permite conexões na porta

### Não recebe notificações

1. Verifique se o webhook está configurado corretamente na Meta
2. Verifique se os eventos estão assinados (messages, message_status)
3. Verifique se a URL pública está acessível
4. Verifique os logs do webhook

### ngrok não funciona

- Certifique-se de que o ngrok está atualizado
- Verifique se não há outro processo usando a porta 5000
- Tente usar uma porta diferente

## 🔒 Segurança

1. **Token de Verificação**: Use um token forte e único
2. **HTTPS**: Sempre use HTTPS em produção (ngrok fornece HTTPS)
3. **Firewall**: Configure firewall para permitir apenas conexões necessárias
4. **Logs**: Não compartilhe logs que contenham tokens ou dados sensíveis

## 📚 Recursos

- [Documentação WhatsApp Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

## ✅ Checklist

- [ ] Token de verificação configurado no `config.py`
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Servidor webhook rodando (`python webhook.py`)
- [ ] Servidor exposto publicamente (ngrok ou similar)
- [ ] Webhook configurado na Meta com URL pública
- [ ] Token de verificação configurado na Meta (mesmo do config.py)
- [ ] Eventos assinados (messages, message_status)
- [ ] Teste de envio realizado
- [ ] Logs sendo gerados corretamente

---

**Pronto!** Seu webhook está configurado e pronto para receber notificações do WhatsApp! 🎉



