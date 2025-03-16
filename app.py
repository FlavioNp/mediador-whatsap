import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from transformers import pipeline
from dotenv import load_dotenv
import re
import logging

# Carregar o .env explicitamente no início
load_dotenv()  # Carrega as variáveis do .env

# Debug para verificar o carregamento
print("DEBUG - Diretório atual:", os.getcwd())
print("DEBUG - Arquivos no diretório:", os.listdir())
print("DEBUG - TWILIO_ACCOUNT_SID:", os.getenv("TWILIO_ACCOUNT_SID"))

# Inicializar o Flask
app = Flask(__name__)

# Configurar logging com nível dinâmico
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))

# Verificar variáveis de ambiente obrigatórias
required_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "WHATSAPP_TEST_NUMBER"]
for var in required_vars:
    if not os.getenv(var):
        app.logger.error(f"Variável de ambiente {var} não definida.")
        raise EnvironmentError(f"Variável {var} é obrigatória.")

# Carregar credenciais e configurações
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)
to_number = os.getenv("WHATSAPP_TEST_NUMBER")

# Carregar o modelo de NLP
try:
    nlp = pipeline("text-classification", model="./meu_modelo")
except Exception as e:
    app.logger.error(f"Erro ao carregar o modelo de NLP: {e}")
    raise

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").lower()
    from_number = request.values.get("From", "")
    app.logger.info(f"Mensagem recebida de {from_number}: {incoming_msg}")

    resp = MessagingResponse()
    msg = resp.message()

    # Detectar número do vizinho
    vizinho_num = re.search(r"número (\d+)", incoming_msg)
    if not vizinho_num:
        app.logger.warning("Número do vizinho não detectado.")
        msg.body("Desculpe, não consegui identificar o número do vizinho. Tente novamente com 'número X'.")
        return str(resp)
    vizinho_id = vizinho_num.group(1)
    app.logger.info(f"Número do vizinho detectado: {vizinho_id}")

    try:
        # Classificar a reclamação
        prediction = nlp(incoming_msg)[0]
        app.logger.info(f"Predição do modelo: {prediction['label']}")

        if prediction["label"] == "LABEL_0":
            msg.body("Olá Dona Maria, estaremos entrando em contato com o vizinho, mas não se preocupe, tudo é feito em sigilo para que possamos mediar qualquer tipo de conflito e evitar desentendimentos. Avisaremos você assim que notificarmos.")
            app.logger.info("Enviando resposta ao reclamante.")

            # Enviar mensagem ao vizinho
            client.messages.create(
                body="Olá Fernando, vim te avisar que alguns vizinhos estão reclamando do barulho. Sei que você é uma pessoa respeitosa, por esse motivo acreditamos que pode ser um equívoco, mas ainda assim achei melhor notificar, lembrando sobre as regras do condomínio e venhamos a evitar qualquer desentendimento ou infrações. Tenha uma excelente noite, Sr. Fernando! Há, se tiver realizando algum tipo de trabalho, me informe aqui que eu posso te ajudar, sugerindo alternativas que podem mitigar qualquer desentendimento entre nossos colegas.",
                from_="whatsapp:+14155238886",
                to=to_number
            )
            app.logger.info(f"Mensagem enviada ao vizinho: {to_number}")
    except TwilioRestException as e:
        app.logger.error(f"Erro ao enviar mensagem via Twilio: {e}")
        msg.body("Erro ao enviar mensagem ao vizinho. Tente novamente.")
    except ValueError as e:
        app.logger.error(f"Erro no modelo de NLP: {e}")
        msg.body("Erro ao processar a mensagem. Tente novamente.")
    except Exception as e:
        app.logger.error(f"Erro inesperado: {e}")
        msg.body("Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente mais tarde.")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)