# Guia de Configuração do WhatsApp Business Cloud API

Este guia explica passo a passo como configurar o WhatsApp Business Cloud API para enviar mensagens através do sistema.

## 📋 Pré-requisitos

1. ✅ App Meta do Facebook criado (você já fez isso!)
2. Conta Meta Business (Facebook Business)
3. Número de telefone para WhatsApp Business (ou usar número de teste)

## 🚀 Passo a Passo

### ETAPA 1: Adicionar o Produto WhatsApp ao App

1. Acesse o [Facebook Developers](https://developers.facebook.com/)
2. Vá em **Meus Apps** e selecione o app que você criou
3. No painel do app, clique em **Adicionar Produto**
4. Procure por **WhatsApp** e clique em **Configurar**

### ETAPA 2: Configurar WhatsApp Business API

1. No painel do WhatsApp, você verá a seção **API Setup**
2. Você precisará de:
   - **Temporary Access Token** (para testes)
   - **Phone Number ID** (ID do número de telefone)
   - **WhatsApp Business Account ID** (opcional, para produção)

### ETAPA 3: Obter Access Token

#### Para TESTES (Temporary Token):

1. Na seção **API Setup**, role até **Temporary access token**
2. Clique em **Generate token**
3. **COPIE O TOKEN** - ele só aparece uma vez!
4. Este token expira em 24 horas (para testes)

#### Para PRODUÇÃO (Permanent Token):

1. Vá em **Configurações** > **Básico**
2. Adicione um **App Secret** (se ainda não tiver)
3. Vá em **Ferramentas** > **Graph API Explorer**
4. Selecione seu app
5. Gere um token com permissões:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
6. Ou use **System Users** para tokens permanentes

### ETAPA 4: Obter Phone Number ID

1. No painel do WhatsApp, vá em **API Setup**
2. Procure por **Phone number ID**
3. Você verá algo como: `123456789012345`
4. **COPIE ESTE NÚMERO**

### ETAPA 5: Configurar Número de Telefone (Opcional para Testes)

#### Opção A: Usar Número de Teste (⚠️ LIMITAÇÕES)

**IMPORTANTE:** Números de teste têm limitações:
- ⚠️ Podem **NÃO entregar mensagens reais** aos destinatários
- ⚠️ São apenas para **desenvolvimento e testes da API**
- ⚠️ A API pode aceitar a mensagem, mas ela pode não chegar
- ✅ Útil para testar se o código está funcionando
- ✅ Para envios reais, você **PRECISA** verificar seu número real

1. No painel do WhatsApp, vá em **API Setup**
2. Role até **To** (campo de teste)
3. Você pode usar números de teste fornecidos pela Meta
4. Ou adicionar seu próprio número para testes

#### Opção B: Adicionar Número Real

1. Vá em **Configurações** > **WhatsApp** > **Números de telefone**
2. Clique em **Adicionar número de telefone**
3. Siga o processo de verificação

### ETAPA 6: Configurar no Sistema

1. Abra o arquivo `config.py`
2. Preencha as variáveis:

```python
WHATSAPP_ACCESS_TOKEN = 'SEU_TOKEN_AQUI'
WHATSAPP_PHONE_NUMBER_ID = 'SEU_PHONE_NUMBER_ID_AQUI'
```

**Exemplo:**
```python
WHATSAPP_ACCESS_TOKEN = 'SEU_ACCESS_TOKEN_AQUI'
WHATSAPP_PHONE_NUMBER_ID = '123456789012345'
```

### ETAPA 7: Testar a Configuração

1. Execute o sistema:
   ```bash
   python main.py
   ```

2. O sistema irá:
   - Validar as configurações
   - Carregar os clientes
   - Tentar enviar o primeiro relatório

3. Verifique os logs para ver se o envio foi bem-sucedido

## 🔍 Onde Encontrar as Informações

### Access Token:
- **Temporário**: WhatsApp > API Setup > Temporary access token
- **Permanente**: Configurações > System Users ou Graph API Explorer

### Phone Number ID:
- WhatsApp > API Setup > Phone number ID
- Ou: WhatsApp > Configurações > Números de telefone > [Seu número] > ID

### WhatsApp Business Account ID:
- WhatsApp > Configurações > Conta comercial do WhatsApp > ID

## ⚠️ Importante

1. **Tokens Temporários**: Expiram em 24 horas. Use apenas para testes iniciais.

2. **Tokens Permanentes**: Para produção, configure System Users ou use App Secret.

3. **Limites de Teste**: 
   - Números de teste têm limites de mensagens
   - Para produção, você precisa verificar seu número

4. **Permissões**: Certifique-se de que o token tem as permissões necessárias:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`

5. **Segurança**: 
   - NUNCA compartilhe seu Access Token
   - Use variáveis de ambiente em produção
   - Não commite tokens no Git

## 🐛 Solução de Problemas

### Erro: "Invalid OAuth access token"
- Token expirou ou está incorreto
- Gere um novo token

### Erro: "Phone number ID not found"
- Verifique se o Phone Number ID está correto
- Certifique-se de que o número está ativo

### Erro: "Recipient phone number not valid"
- Formato do telefone deve ser internacional (sem +)
- Exemplo: `5511999999999` (Brasil)

### Erro: "Message template not approved"
- Para mensagens personalizadas, você precisa de templates aprovados
- Use mensagens do tipo "Utility" (permitidas)

## 📚 Recursos Úteis

- [Documentação Oficial WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [WhatsApp Business API Setup](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

## ✅ Checklist de Configuração

- [ ] App Meta criado
- [ ] Produto WhatsApp adicionado ao app
- [ ] Access Token obtido
- [ ] Phone Number ID obtido
- [ ] Número de telefone configurado (ou usando teste)
- [ ] Configurações preenchidas no `config.py`
- [ ] Sistema testado com sucesso

---

**Pronto para começar!** 🚀

