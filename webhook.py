"""
Servidor Webhook para WhatsApp Business Cloud API
Recebe notificações de status de mensagens e mensagens recebidas
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from config import Config

# Configuração de logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# Configura logger com saída forçada para stdout/stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"webhook_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Força stdout
    ],
    force=True  # Força reconfiguração
)
logger = logging.getLogger(__name__)

# Configura Flask para mostrar logs
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Adiciona handler para logs do Flask também
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

config = Config()


@app.route('/webhook-whatsapp', methods=['GET'])
def verify_webhook():
    """
    Verificação do webhook pela Meta
    A Meta envia um GET request com parâmetros hub.mode, hub.verify_token e hub.challenge
    """
    try:
        # Parâmetros enviados pela Meta
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # Print para garantir que apareça no console
        print("=" * 80, flush=True)
        print("VERIFICAÇÃO DO WEBHOOK - GET REQUEST", flush=True)
        print("=" * 80, flush=True)
        print(f"Mode: {mode}", flush=True)
        print(f"Token recebido: {token}", flush=True)
        print(f"Token esperado: {config.WHATSAPP_WEBHOOK_VERIFY_TOKEN}", flush=True)
        print(f"Challenge: {challenge}", flush=True)
        
        logger.info("=" * 80)
        logger.info("VERIFICAÇÃO DO WEBHOOK - GET REQUEST")
        logger.info("=" * 80)
        logger.info(f"Mode: {mode}")
        logger.info(f"Token recebido: {token}")
        logger.info(f"Token esperado: {config.WHATSAPP_WEBHOOK_VERIFY_TOKEN}")
        logger.info(f"Challenge: {challenge}")
        
        # Verifica se é uma requisição de verificação
        if mode == 'subscribe' and token == config.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            print("✓ Verificação bem-sucedida! Retornando challenge...", flush=True)
            logger.info("✓ Verificação bem-sucedida! Retornando challenge...")
            # Retorna o challenge para confirmar a verificação
            return challenge, 200
        else:
            print("⚠ Verificação falhou!", flush=True)
            print(f"   Mode esperado: 'subscribe', recebido: {mode}", flush=True)
            print(f"   Token esperado: '{config.WHATSAPP_WEBHOOK_VERIFY_TOKEN}', recebido: '{token}'", flush=True)
            logger.warning("⚠ Verificação falhou!")
            logger.warning(f"   Mode esperado: 'subscribe', recebido: {mode}")
            logger.warning(f"   Token esperado: '{config.WHATSAPP_WEBHOOK_VERIFY_TOKEN}', recebido: '{token}'")
            return jsonify({'error': 'Verification failed'}), 403
            
    except Exception as e:
        print(f"❌ Erro ao verificar webhook: {str(e)}", flush=True)
        logger.error(f"Erro ao verificar webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/webhook-whatsapp', methods=['POST'])
def webhook():
    """
    Recebe notificações do WhatsApp Business Cloud API
    Processa status de mensagens, mensagens recebidas, etc.
    """
    try:
        # Obtém o JSON do request
        data = request.get_json()
        
        # Print para garantir que apareça no console
        print("=" * 80, flush=True)
        print("NOTIFICAÇÃO RECEBIDA - POST REQUEST", flush=True)
        print("=" * 80, flush=True)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        if data:
            print(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}", flush=True)
        else:
            print("⚠ Nenhum dado recebido no POST", flush=True)
        
        logger.info("=" * 80)
        logger.info("NOTIFICAÇÃO RECEBIDA - POST REQUEST")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if data:
            logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Verifica se há dados
        if not data:
            logger.warning("⚠ Nenhum dado recebido no POST")
            return jsonify({'status': 'ok'}), 200
        
        # Processa diferentes tipos de notificações
        if 'object' in data and data['object'] == 'whatsapp_business_account':
            # Processa entradas (notificações)
            if 'entry' in data:
                for entry in data['entry']:
                    process_entry(entry)
        
        # Sempre retorna 200 para confirmar recebimento
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"❌ Erro ao processar webhook: {str(e)}", flush=True)
        logger.error(f"Erro ao processar webhook: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str, flush=True)
        logger.error(traceback_str)
        # Ainda retorna 200 para não causar retentativas desnecessárias
        return jsonify({'status': 'error', 'message': str(e)}), 200


def process_entry(entry):
    """
    Processa uma entrada de notificação do WhatsApp
    """
    try:
        print("\n" + "-" * 80, flush=True)
        print("PROCESSANDO ENTRY", flush=True)
        print("-" * 80, flush=True)
        print(f"Entry ID: {entry.get('id', 'N/A')}", flush=True)
        
        logger.info("\n" + "-" * 80)
        logger.info("PROCESSANDO ENTRY")
        logger.info("-" * 80)
        logger.info(f"Entry ID: {entry.get('id', 'N/A')}")
        
        # Processa mudanças (changes)
        if 'changes' in entry:
            for change in entry['changes']:
                process_change(change)
        
        # Processa mensagens (messages)
        if 'messaging' in entry:
            for message in entry['messaging']:
                process_message(message)
                
    except Exception as e:
        print(f"❌ Erro ao processar entry: {str(e)}", flush=True)
        logger.error(f"Erro ao processar entry: {str(e)}")


def process_change(change):
    """
    Processa uma mudança (change) na notificação
    Pode ser status de mensagem, mensagem recebida, etc.
    """
    try:
        change_value = change.get('value', {})
        change_field = change.get('field', 'unknown')
        
        print(f"\n  📋 Campo: {change_field}", flush=True)
        logger.info(f"\n  📋 Campo: {change_field}")
        
        # Status de mensagem enviada
        if 'statuses' in change_value:
            print("  📤 STATUS DE MENSAGEM ENVIADA", flush=True)
            logger.info("  📤 STATUS DE MENSAGEM ENVIADA")
            for status in change_value['statuses']:
                process_status(status)
        
        # Mensagem recebida
        if 'messages' in change_value:
            print("  📥 MENSAGEM RECEBIDA", flush=True)
            logger.info("  📥 MENSAGEM RECEBIDA")
            for message in change_value['messages']:
                process_incoming_message(message, change_value.get('contacts', []))
        
        # Outros tipos de mudanças
        if change_field == 'messages':
            print("  💬 Notificação de mensagem", flush=True)
            logger.info("  💬 Notificação de mensagem")
        elif change_field == 'message_status':
            print("  📊 Notificação de status de mensagem", flush=True)
            logger.info("  📊 Notificação de status de mensagem")
        else:
            print(f"  ℹ️ Tipo de mudança: {change_field}", flush=True)
            logger.info(f"  ℹ️ Tipo de mudança: {change_field}")
            
    except Exception as e:
        print(f"❌ Erro ao processar change: {str(e)}", flush=True)
        logger.error(f"Erro ao processar change: {str(e)}")


def process_status(status):
    """
    Processa status de uma mensagem enviada
    """
    try:
        message_id = status.get('id', 'N/A')
        status_type = status.get('status', 'unknown')
        recipient_id = status.get('recipient_id', 'N/A')
        timestamp = status.get('timestamp', 'N/A')
        
        print(f"\n    📨 Message ID: {message_id}", flush=True)
        print(f"    📱 Destinatário: {recipient_id}", flush=True)
        print(f"    📊 Status: {status_type}", flush=True)
        print(f"    🕐 Timestamp: {timestamp}", flush=True)
        
        logger.info(f"\n    📨 Message ID: {message_id}")
        logger.info(f"    📱 Destinatário: {recipient_id}")
        logger.info(f"    📊 Status: {status_type}")
        logger.info(f"    🕐 Timestamp: {timestamp}")
        
        # Status possíveis: sent, delivered, read, failed
        if status_type == 'sent':
            print("    ✓ Mensagem enviada com sucesso", flush=True)
            logger.info("    ✓ Mensagem enviada com sucesso")
        elif status_type == 'delivered':
            print("    ✓ Mensagem entregue ao destinatário", flush=True)
            logger.info("    ✓ Mensagem entregue ao destinatário")
        elif status_type == 'read':
            print("    ✓ Mensagem lida pelo destinatário", flush=True)
            logger.info("    ✓ Mensagem lida pelo destinatário")
        elif status_type == 'failed':
            error = status.get('errors', [])
            print(f"    ❌ Mensagem falhou: {error}", flush=True)
            logger.error(f"    ❌ Mensagem falhou: {error}")
        else:
            print(f"    ℹ️ Status desconhecido: {status_type}", flush=True)
            logger.info(f"    ℹ️ Status desconhecido: {status_type}")
            
    except Exception as e:
        print(f"❌ Erro ao processar status: {str(e)}", flush=True)
        logger.error(f"Erro ao processar status: {str(e)}")


def process_incoming_message(message, contacts):
    """
    Processa uma mensagem recebida
    """
    try:
        message_id = message.get('id', 'N/A')
        from_number = message.get('from', 'N/A')
        message_type = message.get('type', 'unknown')
        timestamp = message.get('timestamp', 'N/A')
        
        print(f"\n    📨 Message ID: {message_id}", flush=True)
        print(f"    📱 Remetente: {from_number}", flush=True)
        print(f"    📝 Tipo: {message_type}", flush=True)
        print(f"    🕐 Timestamp: {timestamp}", flush=True)
        
        logger.info(f"\n    📨 Message ID: {message_id}")
        logger.info(f"    📱 Remetente: {from_number}")
        logger.info(f"    📝 Tipo: {message_type}")
        logger.info(f"    🕐 Timestamp: {timestamp}")
        
        # Busca informações do contato
        contact_info = None
        for contact in contacts:
            if contact.get('wa_id') == from_number:
                contact_info = contact
                break
        
        if contact_info:
            contact_name = contact_info.get('profile', {}).get('name', 'N/A')
            print(f"    👤 Nome: {contact_name}", flush=True)
            logger.info(f"    👤 Nome: {contact_name}")
        
        # Processa diferentes tipos de mensagem
        if message_type == 'text':
            text = message.get('text', {}).get('body', '')
            text_display = text[:100] + "..." if len(text) > 100 else text
            print(f"    💬 Texto: {text_display}", flush=True)
            logger.info(f"    💬 Texto: {text_display}")
        elif message_type == 'image':
            print("    🖼️ Mensagem de imagem recebida", flush=True)
            logger.info("    🖼️ Mensagem de imagem recebida")
        elif message_type == 'document':
            print("    📄 Mensagem de documento recebida", flush=True)
            logger.info("    📄 Mensagem de documento recebida")
        elif message_type == 'audio':
            print("    🎵 Mensagem de áudio recebida", flush=True)
            logger.info("    🎵 Mensagem de áudio recebida")
        elif message_type == 'video':
            print("    🎥 Mensagem de vídeo recebida", flush=True)
            logger.info("    🎥 Mensagem de vídeo recebida")
        else:
            print(f"    ℹ️ Tipo de mídia: {message_type}", flush=True)
            logger.info(f"    ℹ️ Tipo de mídia: {message_type}")
            
    except Exception as e:
        print(f"❌ Erro ao processar mensagem recebida: {str(e)}", flush=True)
        logger.error(f"Erro ao processar mensagem recebida: {str(e)}")


def process_message(message):
    """
    Processa mensagem no formato antigo (compatibilidade)
    """
    try:
        logger.info("  📨 Processando mensagem (formato antigo)")
        logger.info(f"    Dados: {json.dumps(message, indent=4, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Erro ao processar message: {str(e)}")


@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint de health check
    """
    return jsonify({
        'status': 'ok',
        'service': 'WhatsApp Webhook',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """
    Página inicial com informações do webhook
    """
    return jsonify({
        'service': 'WhatsApp Business Cloud API Webhook',
        'endpoints': {
            'webhook': '/webhook-whatsapp',
            'health': '/health'
        },
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("=" * 80, flush=True)
    print("INICIANDO SERVIDOR WEBHOOK DO WHATSAPP", flush=True)
    print("=" * 80, flush=True)
    print(f"Token de verificação: {config.WHATSAPP_WEBHOOK_VERIFY_TOKEN}", flush=True)
    print(f"Endpoint: /webhook-whatsapp", flush=True)
    print(f"Porta padrão: 5000", flush=True)
    print("=" * 80, flush=True)
    print("\n⚠ IMPORTANTE:", flush=True)
    print("   Para usar em produção, você precisa:", flush=True)
    print("   1. Expor este servidor publicamente (usando ngrok, Cloudflare Tunnel, etc.)", flush=True)
    print("   2. Configurar a URL pública na Meta: https://seu-dominio.com/webhook-whatsapp", flush=True)
    print("   3. Configurar o mesmo token de verificação na Meta", flush=True)
    print("\n🚀 Iniciando servidor...\n", flush=True)
    
    logger.info("=" * 80)
    logger.info("INICIANDO SERVIDOR WEBHOOK DO WHATSAPP")
    logger.info("=" * 80)
    logger.info(f"Token de verificação: {config.WHATSAPP_WEBHOOK_VERIFY_TOKEN}")
    logger.info(f"Endpoint: /webhook-whatsapp")
    logger.info(f"Porta padrão: 5000")
    logger.info("=" * 80)
    logger.info("\n⚠ IMPORTANTE:")
    logger.info("   Para usar em produção, você precisa:")
    logger.info("   1. Expor este servidor publicamente (usando ngrok, Cloudflare Tunnel, etc.)")
    logger.info("   2. Configurar a URL pública na Meta: https://seu-dominio.com/webhook-whatsapp")
    logger.info("   3. Configurar o mesmo token de verificação na Meta")
    logger.info("\n🚀 Iniciando servidor...\n")
    
        # Obtém porta das variáveis de ambiente ou usa 5000 como padrão
    port = int(os.getenv('PORT', os.getenv('WEBHOOK_PORT', 8000)))
    host = os.getenv('WEBHOOK_HOST', '0.0.0.0')

    app.run(host=host, port=port, debug=False)

