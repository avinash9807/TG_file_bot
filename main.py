import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
BOT_TOKEN = "7517788313:AAFzuh06eU-junoxoaCOWXq1o8I8KRAmo4U"  # BotFather वाला टोकन यहाँ डालें
OWNER_ID = 123456789  # UserInfoBot से मिला हुआ अपना ID नंबर यहाँ डालें (बिना quotes के)

# Logging set karein taki koi error aaye to dikh jaye
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- SECURITY CHECK (Sirf Owner ke liye) ---
async def ensure_owner(update: Update):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        # Agar koi aur message bhejta hai, to use ignore karein ya mana karein
        await update.message.reply_text("⛔ Access Denied: यह बॉट सिर्फ मेरे मालिक के लिए है।")
        return False
    return True

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Pehle check karein ki kya ye owner hai
    if not await ensure_owner(update):
        return
    
    # Agar owner hai to hi ye message jayega
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="नमस्ते बॉस! 👋 मैं ऑनलाइन हूँ और सिर्फ आपकी बात सुनूँगा।"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_owner(update):
        return
    
    # Jo aap likhenge wahi wapas bolega (Testing ke liye)
    user_text = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"आपने कहा: {user_text}"
    )

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers add karein
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    
    print("Bot is running...")
    application.run_polling()
