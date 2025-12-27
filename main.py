import os
import logging
import math
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

# --- WEB SERVER (Resume & Speed Logic) ---
routes = web.RouteTableDef()

@routes.get("/")
async def root_handler(request):
    return web.Response(text="Bot is Online with High Speed & Resume Support! 🚀", status=200)

@routes.get("/dl/{message_id}")
async def stream_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        
        # 1. File Fetch
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception:
            return web.Response(status=404, text="File Not Found in Storage")

        media = message.document or message.video or message.audio or message.photo
        if not media:
            return web.Response(status=404, text="Media Not Found")

        # 2. Details
        file_name = getattr(media, "file_name", f"file_{message_id}.mp4")
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "application/octet-stream")

        # 3. Range Handling (Resume Support ka Jaadu)
        range_header = request.headers.get("Range", 0)
        from_bytes, until_bytes = 0, file_size - 1

        if range_header:
            from_bytes = int(range_header.replace("bytes=", "").split("-")[0])
            # Agar user ne pause/resume kiya hai, to hum wahi se start karenge
        
        content_length = file_size - from_bytes
        status_code = 206 if range_header else 200

        # 4. Headers (Browser ko batana ki hum Resume support karte hain)
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {from_bytes}-{until_bytes}/{file_size}',
            'Content-Length': str(content_length)
        }

        response = web.StreamResponse(status=status_code, headers=headers)
        await response.prepare(request)

        # 5. Speed & Resume Logic
        # Hum file ko download karenge lekin user ke requested part tak skip karenge
        # Note: Koyeb free tier par True Seeking mushkil hai, ye method bandwidth use karta hai
        # lekin Resume button ko enable kar deta hai.
        
        offset = 0
        chunk_size = 1024 * 1024  # 1MB Chunks (Badi speed ke liye)
        
        async for chunk in bot.download_media(message, stream=True):
            # Logic: Agar user ne aadha download kar liya tha, to shuru ke bytes ignore karo
            if offset < from_bytes:
                if (offset + len(chunk)) > from_bytes:
                    # Hamein is chunk ka thoda hissa chahiye
                    relevant_chunk = chunk[from_bytes - offset:]
                    await response.write(relevant_chunk)
                offset += len(chunk)
                continue
            
            # Normal Download
            try:
                await response.write(chunk)
                offset += len(chunk)
            except Exception:
                break
            
        return response

    except Exception as e:
        logger.error(f"Error: {e}")
        return web.Response(status=500, text="Server Error")

# --- BOT COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await message.reply_text(f"🚀 **Fast Bot Online!**\nLink: {APP_URL}")

@bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def file_handler(client, message):
    if message.from_user.id not in OWNER_IDS: return
    
    sts = await message.reply("⏳ **Generating Resume-able Link...**")
    try:
        log_msg = await message.forward(LOG_CHANNEL_ID)
        link = f"{APP_URL}/dl/{log_msg.id}"
        await sts.edit_text(f"✅ **Link Ready!**\n📂 {getattr(message.document or message.video, 'file_name', 'File')}\n🔗 `{link}`")
    except Exception as e:
        await sts.edit_text(f"Error: {e}")

# --- START ---
async def start_services():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    await bot.start()
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    
