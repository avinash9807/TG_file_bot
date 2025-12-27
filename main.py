import os
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_IDS, APP_URL, LOG_CHANNEL_ID

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- QUEUE STREAMER CLASS (Ye Magic Hai) ---
# Ye class file ko download karte hi turant user ko bhej degi
class FileLikeObject:
    def __init__(self, queue):
        self.queue = queue
        self.name = "file" # Pyrogram needs a name attribute

    def write(self, data):
        # Jaise hi data mile, queue me daal do (Sync method called by Pyrogram)
        self.queue.put_nowait(data)
        return len(data)

    def close(self):
        pass

    def flush(self):
        pass

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
    return web.Response(text="Bot is Online with Queue System! 🟢", status=200)

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

        # 3. Headers (Download Start karne ke liye)
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Length': str(file_size)
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        
        # 4. QUEUE LOGIC (Sabse important hissa)
        # Hum ek Queue banayenge. Bot usme data dalega, aur Browser wahan se uthayega.
        
        data_queue = asyncio.Queue(maxsize=5) # Memory Bachane ke liye maxsize kam rakha hai
        file_writer = FileLikeObject(data_queue)
        
        # Download ko background me start karo (Task)
        # Hum 'file_name' me apna object denge, taaki Pyrogram usme write kare
        download_task = asyncio.create_task(
            bot.download_media(message, file_name=file_writer)
        )

        # 5. Data User ko bhejna
        downloaded_bytes = 0
        
        while True:
            # Queue se data nikalo
            # Hum wait karenge jab tak data na aaye ya download khatam na ho jaye
            try:
                # 5 second wait karenge data ka
                chunk = await asyncio.wait_for(data_queue.get(), timeout=5.0)
                
                if chunk is None: # End signal
                    break
                    
                await response.write(chunk)
                downloaded_bytes += len(chunk)
                
                # Agar download complete ho gaya
                if downloaded_bytes >= file_size:
                    break
                    
            except asyncio.TimeoutError:
                # Agar 5 second tak data nahi aaya, check karo ki task zinda hai ya nahi
                if download_task.done():
                    break
                continue
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                break

        # Cleanup
        if not download_task.done():
            download_task.cancel()
            
        return response

    except Exception as e:
        logger.error(f"Server Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

# --- COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await message.reply_text(f"🟢 **Queue Bot Online!**\n{APP_URL}")

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
    
