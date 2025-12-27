import os
import logging
import asyncio
import time
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
        
        # 1. File Dhoondna
        try:
            message = await bot.get_messages(chat_id=LOG_CHANNEL_ID, message_ids=message_id)
        except Exception:
            return web.Response(status=404, text="File Not Found")

        media = message.document or message.video or message.audio or message.photo
        if not media:
            return web.Response(status=404, text="No Media Found")

        # 2. File Details
        file_name = getattr(media, "file_name", f"file_{message_id}.mp4")
        file_size = getattr(media, "file_size", 0)
        mime_type = getattr(media, "mime_type", "application/octet-stream")
        
        # Temp path (Linux ka sabse fast folder)
        unique_file_path = f"/tmp/download_{message_id}_{int(time.time())}.temp"

        # 3. Headers
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Length': str(file_size)
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        
        # 4. INSTANT STREAM LOGIC
        
        # Step A: Download Task Start
        download_task = asyncio.create_task(
            bot.download_media(message, file_name=unique_file_path)
        )

        # Step B: File banna shuru hone ka wait (Timeout badha diya hai)
        start_time = time.time()
        file_created = False
        
        while not file_created:
            # Agar file disk par aa gayi, to loop todo
            if os.path.exists(unique_file_path):
                # Check karo file khali to nahi hai (size > 0)
                if os.path.getsize(unique_file_path) > 0:
                    file_created = True
                    break

            # Agar Task fail ho gaya (Telegram error)
            if download_task.done():
                try:
                    # Error kya tha? wo check karo
                    await download_task
                except Exception as e:
                    logger.error(f"Download Task Failed: {e}")
                    return web.Response(status=500, text=f"Download Failed: {e}")
                break

            # Timeout check (60 Seconds)
            if time.time() - start_time > 60:
                logger.error("Timeout: File start hone me der lag rahi hai.")
                # Task cancel karo
                if not download_task.done():
                    download_task.cancel()
                return web.Response(status=504, text="Timeout: Telegram didn't respond in 60s")

            await asyncio.sleep(0.5)

        # Step C: File Padho aur Bhejo (Read-While-Write)
        # Hum 'with open' use karenge taaki file jarur close ho
        try:
            with open(unique_file_path, "rb") as f:
                while True:
                    chunk = f.read(1024 * 1024) # 1MB Chunk
                    
                    if chunk:
                        try:
                            await response.write(chunk)
                        except Exception:
                            # User disconnect
                            break
                    else:
                        # Agar chunk nahi mila, check karo download khatam hua kya
                        if download_task.done():
                            break
                        # Download chal raha hai, thoda wait karo
                        await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Streaming Error: {e}")
        
        # Cleanup
        if not download_task.done():
            download_task.cancel()
        if os.path.exists(unique_file_path):
            os.remove(unique_file_path)
            
        return response

    except Exception as e:
        logger.error(f"Main Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

# --- COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if message.from_user.id not in OWNER_IDS: return
    await message.reply_text(f"🟢 **Bot Online!**\n{APP_URL}")

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
