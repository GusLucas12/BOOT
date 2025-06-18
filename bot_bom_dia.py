import logging
import os
import datetime
import pytz
import tzlocal
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

async def job_diario(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Executando job diário...")
    for cid in chat_ids:
        mensagem = gerar_mensagem_gemini()
        await bot.send_message(chat_id=cid, text=f"🤖 Bot do Bom Dia diz:\n{mensagem}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid not in chat_ids:
        chat_ids.add(cid)
        await update.message.reply_text("Você foi registrado para receber mensagens diárias às 06:00. 🕕")
    else:
        await update.message.reply_text("Você já está registrado!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in chat_ids:
        chat_ids.remove(cid)
        await update.message.reply_text("Você foi removido da lista de envio diário. 😢")
    else:
        await update.message.reply_text("Você não estava registrado.")

async def main():
    global bot
    tzlocal.get_localzone = lambda: pytz.timezone("America/Sao_Paulo")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # Para testes, envie mensagem 1 minuto após início
    from datetime import timedelta
    app.job_queue.run_once(job_diario, when=timedelta(minutes=1))

    logging.info("Bot iniciado!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
