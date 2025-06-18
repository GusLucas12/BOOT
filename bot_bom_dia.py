import logging
import datetime
import pytz
import tzlocal
import requests

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuração
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

chat_ids = set()
bot: Bot

# Garante timezone de São Paulo
tzlocal.get_localzone = lambda: pytz.timezone("America/Sao_Paulo")


# Função que chama a API do Gemini
def gerar_mensagem_gemini():
    headers = {"Content-Type": "application/json"}
    prompt = (
        'Bom dia. [Um apelidinho romântico e zuado], [curiosidade interessante do dia], '
        'e ao final diga: Lembre-se de dar bom dia ao Gustavo!'
    )
    data = {"contents": [{"parts": [{"text": prompt}]}]}

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


# Envia mensagem para todos os chats registrados
async def job_diario(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Executando job diário...")
    mensagem = gerar_mensagem_gemini()
    for cid in list(chat_ids):  # lista para evitar RuntimeError se modificar durante loop
        try:
            await bot.send_message(cid, f"🤖 Bot do Bom Dia diz: \"{mensagem}\"")
            logging.info(f"Mensagem enviada para {cid}")
        except Exception as e:
            logging.error(f"Erro ao enviar para {cid}: {e}")


# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid not in chat_ids:
        chat_ids.add(cid)
        await update.message.reply_text("Você foi registrado! As mensagens diárias começarão a ser enviadas às 06:00.")
        logging.info(f"Usuário {cid} registrado.")
    else:
        await update.message.reply_text("Você já está registrado para receber as mensagens.")


# Comando /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in chat_ids:
        chat_ids.remove(cid)
        await update.message.reply_text("Você foi removido da lista e não receberá mais mensagens.")
        logging.info(f"Usuário {cid} removido.")
    else:
        await update.message.reply_text("Você não está registrado.")


# Função principal
def main():
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    global bot
    bot = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # Agenda o job diário para 06:00 da manhã (hora de São Paulo)
    app.job_queue.run_daily(job_diario, time=datetime.time(6, 0, tzinfo=pytz.timezone("America/Sao_Paulo")))

    logging.info("Bot iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
