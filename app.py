from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from transformers import pipeline
import re

app = Flask(__name__)
nlp = pipeline("text-classification", model="./meu_modelo")
account_sid = "SEU_ACCOUNT_SID"  # Substitua pelo seu SID do Twilio
auth_token = "SEU_AUTH_TOKEN"  # Substitua pelo seu Token do Twilio
client = Client(account_sid, auth_token)

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").lower()
    from_number = request.values.get("From", "")
    resp = MessagingResponse()
    msg = resp.message()

    # Detectar número do vizinho na mensagem (ex.: "número 302")
    vizinho_num = re.search(r"número (\d+)", incoming_msg)
    vizinho_id = vizinho_num.group(1) if vizinho_num else "desconhecido"

    # Classificar a reclamação com o modelo
    prediction = nlp(incoming_msg)[0]
    if prediction["label"] == "LABEL_0":  # Resposta ao reclamante
        msg.body(f"Olá Dona Maria, estaremos entrando em contato com o vizinho, mas não se preocupe, tudo é feito em sigilo para que possamos mediar qualquer tipo de conflito e evitar desentendimentos. Avisaremos você assim que notificarmos.")
        # Enviar mensagem ao vizinho (número fictício para teste)
        client.messages.create(
            body="Olá Fernando, vim te avisar que alguns vizinhos estão reclamando do barulho. Sei que você é uma pessoa respeitosa, por esse motivo acreditamos que pode ser um equívoco, mas ainda assim achei melhor notificar, lembrando sobre as regras do condomínio e venhamos a evitar qualquer desentendimento ou infrações. Tenha uma excelente noite, Sr. Fernando! Há, se tiver realizando algum tipo de trabalho, me informe aqui que eu posso te ajudar, sugerindo alternativas que podem mitigar qualquer desentendimento entre nossos colegas.",
            from_="whatsapp:+14155238886",  # Número do Twilio (sandbox)
            to="whatsapp:+55SEUNUMERO"  # Substitua pelo seu número de teste
        )
    return str(resp)

if __name__ == "__main__":
    app.run()