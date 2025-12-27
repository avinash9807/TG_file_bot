import os
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL, LOG_CHANNEL_ID

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT SETUP ---
bot = Client(
    "my_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    ipv6=False
)

# --- WEB SERVER (High Speed Logic) ---
routes = web.RouteTableDef()

@routes.get("/")
async def root_handler(request):
    return web.Response(text="Bot is Online & Healthy! 🟢", status=200)

@routes.get("/dl/{message_id}")
async def stream_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        
        # 1. File dhoondna (Storage Channel se)
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception:
            return web.Response(status=404, text="File Not Found in Storage Channel")

        media = message.document or message.video or message.audio or message.photo
        
        if not media:
            return web.Response(status=404, text="Media Not Found")

        # 2. File Details
        file_name = getattr(media, "file_name", f"file_{message_id}.mp4")
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "application/octet-stream")

        # 3. Headers (Browser ko size batane ke liye)
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Length': str(file_size)
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        
        # 4. Fast Download Stream
        async for chunk in bot.download_media(message, stream=True):
            try:
                await response.write(chunk)
            except Exception:
                break
            
        return response

    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return web.Response(status=500, text="Server Error")

# --- BOT COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await message.reply_text(f"✅ **Bot Online!**\nServer: {APP_URL}")

@bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def file_handler(client, message):
    if message.from_user.id not in OWNER_IDS: return

    sts = await message.reply("⚡ **Processing...**")
    try:
        log_msg = await message.forward(LOG_CHANNEL_ID)
        link = f"{APP_URL}/dl/{log_msg.id}"
        
        await sts.edit_text(
            f"✅ **Link Generated!**\n\n"
            f"📂 `{getattr(message.document or message.video, 'file_name', 'File')}`\n"
            f"🔗 `{link}`"
        )
    except Exception as e:
        await sts.edit_text(f"❌ Error: {e}")

# --- START SERVICE (Stable Method) ---
async def start_services():
    # 1. Web Server Start
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    # 2. Bot Start
    await bot.start()
    logger.info("Bot & Server Started Successfully!")
    
    # 3. Keep Alive (Idle)
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    
