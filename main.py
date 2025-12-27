import os
import logging
from aiohttp import web
from pyrogram import Client, filters, errors
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL, LOG_CHANNEL_ID

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT SETUP (High Speed Config) ---
bot = Client(
    "my_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    ipv6=False  # Koyeb par speed badhane ke liye false rakha hai
)

# --- WEB SERVER ---
routes = web.RouteTableDef()

@routes.get("/")
async def root_handler(request):
    return web.Response(text="Bot is Running High Speed! ⚡", status=200)

@routes.get("/dl/{message_id}")
async def stream_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        
        # 1. File dhoondna (Storage Channel se)
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception as e:
            return web.Response(status=404, text="File Not Found in Storage Channel")

        media = message.document or message.video or message.audio or message.photo
        
        if not media:
            return web.Response(status=404, text="Media Not Found")

        # 2. File Details nikalna
        file_name = getattr(media, "file_name", f"file_{message_id}.mp4")
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "application/octet-stream")

        # 3. Browser ko batana ki file aane wali hai (Headers)
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Length': str(file_size) # Ye Browser ko progress bar dikhayega
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        
        # 4. Stream Loop (Telegram -> Server -> User)
        # 1MB ke chunks me download karenge (1024*1024)
        async for chunk in bot.download_media(message, stream=True):
            try:
                await response.write(chunk)
            except Exception:
                # Agar user download cancel kar de ya connection toot jaye
                break
            
        return response

    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return web.Response(status=500, text="Server Error")

# --- BOT COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await message.reply_text(f"⚡ **Speed Bot Online!**\nServer: {APP_URL}")

@bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def file_handler(client, message):
    if message.from_user.id not in OWNER_IDS: return

    sts = await message.reply("⚡ **स्टोरेज में भेज रहा हूँ...**")
    try:
        # File Storage Channel me bhejna
        log_msg = await message.forward(LOG_CHANNEL_ID)
        
        link = f"{APP_URL}/dl/{log_msg.id}"
        
        await sts.edit_text(
            f"✅ **लिंक तैयार है!**\n\n"
            f"📂 **फाइल:** `{getattr(message.document or message.video, 'file_name', 'File')}`\n"
            f"🔗 **Link:**\n`{link}`\n\n"
            f"⚠️ *Browser या ADM का इस्तेमाल करें।*"
        )
    except Exception as e:
        await sts.edit_text(f"❌ Error: {e}")

# --- RUNNER ---
if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    
    # Port Config
    PORT = int(os.environ.get("PORT", 8000))
    
    # Run
    bot.start()
    logger.info(f"Bot Started on Port {PORT}")
    web.run_app(app, port=PORT)
    
