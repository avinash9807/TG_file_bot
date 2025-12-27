import logging
import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION (Yahan apni details daalein) ---
BOT_TOKEN = "7517788313:AAFzuh06eU-junoxoaCOWXq1o8I8KRAmo4U" 
OWNER_ID = 800000580

# --- FAKE WEB SERVER (Jugaad for Koyeb Web Service) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running! 🚀"

def run_web():
    # Port 8000 par fake server chalayenge
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- BOT CODE ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def ensure_owner(update: Update):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Access Denied")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_owner(update): return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="नमस्ते बॉस! बॉट ऑनलाइन है।")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_owner(update): return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"आपने कहा: {update.message.text}")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Pehle fake server start karein
    keep_alive()
    
    # Phir bot start karein
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    
    print("Bot started...")
    application.run_polling()
    
