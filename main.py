import os
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.file_id import FileId
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputFileLocation
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL, LOG_CHANNEL_ID

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CUSTOM STREAMER CLASS ---
class ByteStreamer:
    def __init__(self, client, file_id):
        self.client = client
        self.file_id = file_id

    async def yield_chunks(self, offset=0, chunk_size=1024 * 1024):
        try:
            decoded = FileId.decode(self.file_id)
            location = decoded.make_input_location(
                file_reference=decoded.file_reference
            )
            
            while True:
                req = GetFile(
                    location=location,
                    offset=offset,
                    limit=chunk_size
                )
                result = await self.client.invoke(req)
                
                if not result.bytes:
                    break
                
                yield result.bytes
                offset += len(result.bytes)
        except Exception as e:
            logger.error(f"ByteStreamer Error: {e}")

# --- BOT SETUP ---
bot = Client(
    "my_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    ipv6=False,
    workers=4
)

# --- WEB SERVER ---
routes = web.RouteTableDef()

@routes.get("/")
async def root_handler(request):
    return web.Response(text="Bot is Online! 🟢", status=200)

@routes.get("/dl/{message_id}")
async def stream_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception:
            return web.Response(status=404, text="File Not Found")

        media = message.document or message.video or message.audio or message.photo
        if not media:
            return web.Response(status=404, text="No Media Found")

        file_name = getattr(media, "file_name", f"file_{message_id}.mp4")
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "application/octet-stream")
        file_id = media.file_id

        # Headers logic
        range_header = request.headers.get("Range", 0)
        from_bytes = 0
        if range_header:
            try:
                from_bytes = int(range_header.replace("bytes=", "").split("-")[0])
            except:
                from_bytes = 0
        
        content_length = file_size - from_bytes
        status_code = 206 if range_header else 200

        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(content_length)
        }

        response = web.StreamResponse(status=status_code, headers=headers)
        await response.prepare(request)
        
        # Start Streaming
        streamer = ByteStreamer(bot, file_id)
        async for chunk in streamer.yield_chunks(offset=from_bytes):
            try:
                await response.write(chunk)
            except Exception:
                break
            
        return response

    except Exception as e:
        logger.error(f"Server Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

# --- COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await message.reply_text(f"🟢 **Bot Online!**\n{APP_URL}")

# ERROR YAHAN THA, AB FIX HAI (Bracket check kar liya hai)
@bot.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def file_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    
    sts = await message.reply("⚡ **Generating Link...**")
    try:
        log_msg = await message.forward(LOG_CHANNEL_ID)
        link = f"{APP_URL}/dl/{log_msg.id}"
        await sts.edit_text(f"✅ **Link Ready:**\n`{link}`")
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
    print("Bot Started!")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    
