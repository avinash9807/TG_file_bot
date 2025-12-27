import os
import logging
import asyncio
import math
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.file_id import FileId
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputFileLocation
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL, LOG_CHANNEL_ID

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CUSTOM STREAMER CLASS (Ye Error Fix Karega) ---
# Pyrogram me stream=True nahi hota, isliye hum khud ka downloader banayenge
class ByteStreamer:
    def __init__(self, client, file_id):
        self.client = client
        self.file_id = file_id

    async def yield_chunks(self, offset=0, chunk_size=1024 * 1024):
        # File ID Decode karna
        decoded = FileId.decode(self.file_id)
        location = decoded.make_input_location(
            file_reference=decoded.file_reference
        )
        
        # Raw Telegram API Call
        while True:
            try:
                # Telegram se 1MB ka tukda mangna
                req = GetFile(
                    location=location,
                    offset=offset,
                    limit=chunk_size
                )
                result = await self.client.invoke(req)
                
                if not result.bytes:
                    break
                
                # Tukda User ko bhejna
                yield result.bytes
                offset += len(result.bytes)
                
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                break

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
    return web.Response(text="Bot is Online with Custom Streamer! 🟢", status=200)

@routes.get("/dl/{message_id}")
async def stream_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        
        # 1. File Dhoondna
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception:
            return web.Response(status=404, text="File Not Found")

        media = message.document or message.video or message.audio or message.photo
        if not media:
            return web.Response(status=404, text="No Media Found")

        # 2. Details
        file_name = getattr(media, "file_name", f"file_{message_id}.mp4")
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "application/octet-stream")
        file_id = media.file_id

        # 3. Headers (Resume Support ke sath)
        range_header = request.headers.get("Range", 0)
        from_bytes, until_bytes = 0, file_size - 1

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
            'Content-Range': f'bytes {from_bytes}-{until_bytes}/{file_size}',
            'Content-Length': str(content_length)
        }

        response = web.StreamResponse(status=status_code, headers=headers)
        await response.prepare(request)
        
        # 4. Custom Streaming (Magic starts here)
        # Hum `download_media` use nahi karenge, balki apna `ByteStreamer` use karenge
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
    await message.reply_text(f"🟢 **Fixed Bot Online!**\n{APP_URL}")

@bot.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def file_cmd(client, message
        
