import os
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters, errors
from pyrogram.types import Message

# Config se details le rahe hain
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL, LOG_CHANNEL_ID

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT CLIENT ---
bot = Client(
    "my_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- WEB SERVER ---
routes = web.RouteTableDef()

@routes.get("/")
async def root_handler(request):
    return web.Response(text="Bot is Online with Storage Channel! 🚀")

@routes.get("/dl/{message_id}")
async def stream_handler(request):
    try:
        # URL se Message ID nikalna
        message_id = int(request.match_info['message_id'])
        
        # NOTE: Ab hum file 'Private Chat' se nahi, balki 'Storage Channel' se uthayenge
        # Isse 404 Error nahi aata.
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception as e:
             return web.Response(status=404, text="File Not Found in Storage Channel")

        media = message.document or message.video or message.audio or message.photo
        
        if not media:
            return web.Response(status=404, text="File Not Found")

        file_name = getattr(media, "file_name", "file")
        mime_type = getattr(media, "mime_type", "application/octet-stream")
        
        response = web.StreamResponse()
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        await response.prepare(request)
        
        async for chunk in bot.download_media(message, stream=True):
            await response.write(chunk)
            
        return response
        
    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return web.Response(status=500, text=f"Server Error: {e}")

# --- BOT COMMANDS ---

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if message.from_user.id not in OWNER_IDS:
        return await message.reply("⛔ यह बॉट प्राइवेट है।")
        
    await message.reply_text(
        "👋 **सिस्टम अपग्रेड हो गया है!**\n\n"
        "अब आप जो भी फाइल भेजेंगे, वो **Storage Channel** में सेव होगी "
        "और उसका लिंक कभी एक्सपायर नहीं होगा (No 404 Error)।\n\n"
        "🚀 **फाइल भेजें और जादू देखें!**"
    )

@bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def file_handler(client, message: Message):
    if message.from_user.id not in OWNER_IDS:
        return

    status_msg = await message.reply_text("🔄 **फाइल को स्टोरेज में सेव कर रहा हूँ...**")

    try:
        # 1. Pehle file ko Storage Channel me forward karein
        log_msg = await message.forward(LOG_CHANNEL_ID)
        
        # 2. Ab link us forwarded message ka banayenge
        stream_link = f"{APP_URL}/dl/{log_msg.id}"
        
        file_name = getattr(message.document or message.video or message.audio, "file_name", "Media_File")
        
        await status_msg.edit_text(
            f"✅ **लिंक तैयार है!** (100% Working)\n\n"
            f"📂 **फाइल:** `{file_name}`\n"
            f"🔗 **डाउनलोड लिंक:**\n`{stream_link}`\n\n"
            f"💾 *यह फाइल स्टोरेज चैनल में सुरक्षित है।*"
        )
    except errors.ChatAdminRequired:
        await status_msg.edit_text("❌ **Error:** बॉट को Storage Channel में **Admin** बनाएं।")
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {e}\n(Check LOG_CHANNEL_ID in Koyeb)")

# --- RUNNER ---
async def start_services():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    await bot.start()
    logger.info("Bot Started!")
    
    from pyrogram import idle
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    
