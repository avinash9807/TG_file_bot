import os
import logging
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

# Config file se details le rahe hain
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT CLIENT ---
bot = Client(
    "my_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- WEB SERVER HANDLERS ---
routes = web.RouteTableDef()

@routes.get("/")
async def root_handler(request):
    return web.Response(text="Bot is Online & Working for Multiple Owners! 🚀")

# Naya Link Format: /dl/{user_id}/{message_id}
@routes.get("/dl/{chat_id}/{message_id}")
async def stream_handler(request):
    try:
        # URL se Chat ID aur Message ID nikalna
        chat_id = int(request.match_info['chat_id'])
        message_id = int(request.match_info['message_id'])
        
        # Security: Check karein ki file mangne wala Chat ID hamare Owners me hai ya nahi
        if chat_id not in OWNER_IDS:
            return web.Response(status=403, text="Access Denied: Unknown User File")

        # File ko sahi user ki chat se fetch karna
        message = await bot.get_messages(chat_id=chat_id, message_ids=message_id)
        media = message.document or message.video or message.audio or message.photo
        
        if not media:
            return web.Response(status=404, text="File Not Found")

        # File details
        file_name = getattr(media, "file_name", "file")
        mime_type = getattr(media, "mime_type", "application/octet-stream")
        
        # Streaming Response setup
        response = web.StreamResponse()
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        await response.prepare(request)
        
        # Stream download (Koyeb Friendly)
        async for chunk in bot.download_media(message, stream=True):
            await response.write(chunk)
            
        return response
        
    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return web.Response(status=500, text=f"Server Error: {e}")

# --- BOT COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    # Check karein ki user hamare Owners list me hai ya nahi
    if message.from_user.id not in OWNER_IDS:
        return await message.reply("⛔ यह बॉट प्राइवेट है।")
        
    await message.reply_text(
        "👋 **नमस्ते बॉस!**\n\n"
        "मैं अब **Dual Owner Mode** में हूँ।\n"
        "आप दोनों में से कोई भी फाइल भेजेगा, मैं उसका लिंक बना दूंगा।\n\n"
        f"🌍 **Server URL:** `{APP_URL}`"
    )

@bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def file_handler(client, message: Message):
    # Check User
    if message.from_user.id not in OWNER_IDS:
        return

    wait_msg = await message.reply_text("🔄 **लिंक जनरेट कर रहा हूँ...**")
    
    # URL Check
    if "example.com" in APP_URL or "placeholder" in APP_URL:
        await wait_msg.edit_text("⚠️ **Error:** `config.py` में Koyeb का URL अपडेट करें।")
        return

    # Link banana (Ab isme Chat ID bhi judega)
    chat_id = message.from_user.id
    msg_id = message.id
    stream_link = f"{APP_URL}/dl/{chat_id}/{msg_id}"
    
    file_name = getattr(message.document or message.video or message.audio, "file_name", "Media_File")
    
    await wait_msg.edit_text(
        f"✅ **लिंक तैयार है!**\n\n"
        f"📂 **फाइल:** `{file_name}`\n"
        f"🔗 **डाउनलोड लिंक:**\n`{stream_link}`\n\n"
        f"⚡ *यह लिंक आप किसी को भी शेयर कर सकते हैं।*"
    )

# --- START SERVICE ---
async def start_services():
    # Web App
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    # Bot Start
    await bot.start()
    logger.info("Bot Started & Web Server Live")
    
    # Idle
    from pyrogram import idle
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    
