import logging
import os
import datetime
import pytz
import tzlocal
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

# Log
logging.basicConfig(level=logging.INFO)

# Variáveis de ambiente
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

chat_ids = set()
bot: Bot = None

def gerar_mensagem_gemini():
    headers = {"Content-Type": "application/json"}
    prompt = (
        'Bom dia. [Um apelidinho romântico zuado] [Curiosidade do dia] '
        'e ao final diga: "Lembre-se de dar bom dia ao Gustavo!"'
    )
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers=headers, json=data)
        response.raise_for_status()
        resposta_json = response.json()
        return resposta_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logging.error(f"Erro ao chamar Gemini API: {e}")
        return "Bom dia! Que seu dia seja incrível! 😉"

def job_diario(context: CallbackContext):
    logging.info("Executando job diário...")
    for cid in chat_ids:
        mensagem = gerar_mensagem_gemini()
        context.bot.send_message(chat_id=cid, text=f"🤖 Bot do Bom Dia diz:\n{mensagem}")

def start(update: Update, context: CallbackContext):
    cid = update.effective_chat.id
    if cid not in chat_ids:
        chat_ids.add(cid)
        update.message.reply_text("Você foi registrado para receber mensagens diárias às 06:00. 🕕")
    else:
        update.message.reply_text("Você já está registrado!")

def stop(update: Update, context: CallbackContext):
    cid = update.effective_chat.id
    if cid in chat_ids:
        chat_ids.remove(cid)
        update.message.reply_text("Você foi removido da lista de envio diário. 😢")
    else:
        update.message.reply_text("Você não estava registrado.")

def main():
    global bot
    tzlocal.get_localzone = lambda: pytz.timezone("America/Sao_Paulo")

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))

    # Agenda a tarefa diária
    job_queue = updater.job_queue
    sao_paulo = pytz.timezone("America/Sao_Paulo")
    job_queue.run_daily(job_diario, time=datetime.time(6, 0, tzinfo=sao_paulo))

    logging.info("Bot iniciado.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
