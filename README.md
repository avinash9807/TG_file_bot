# 📂 Telegram File to Link Bot (Stream Bot)

A simple Telegram Bot that stores files in a private channel and generates **Direct Download Links**.
It supports high-speed streaming and files larger than **2GB**.

---

## 🔥 Features
- 🔗 **Permanent Links:** Files are stored safely (No 404 Errors).
- 👥 **Multi-Owner:** Supports multiple admins.
- ⚡ **Fast Speed:** High-speed direct download links.
- ✅ **Koyeb Ready:** Easy to deploy.

----

## 🛠️ Environment Variables (Settings)

To make the bot work, you need to add these 6 values in your Hosting Settings (Koyeb > Settings > Environment Variables).

### 1. API_ID
* **What is it?** A unique number for your application.
* **How to get it:** Go to `my.telegram.org`, login, click "API Development Tools", and copy the `App api_id`.
* **Example:** `1234567`

### 2. API_HASH
* **What is it?** A secret code for your application.
* **How to get it:** It is on the same page as `API_ID` at `my.telegram.org`.
* **Example:** `a1b2c3d4e5f6g7h8...`

### 3. BOT_TOKEN
* **What is it?** The main password for your bot.
* **How to get it:** Search for **@BotFather** on Telegram. Send `/newbot` and give your bot a name. It will give you the token.
* **Example:** `555555:AAHxyzABC...`

### 4. OWNER_IDS
* **What is it?** The User ID of the person (you) who will control the bot.
* **How to get it:** Search for **@userinfobot** on Telegram and start it. Copy the `Id`.
* **Note:** If you want multiple admins, separate them with a comma (e.g., `12345, 67890`).
* **Example:** `123456789`

### 5. LOG_CHANNEL_ID
* **What is it?** The ID of the Private Channel where your files will be stored.
* **How to get it:**
    1. Create a **Private Channel** on Telegram.
    2. **Make your Bot an Admin** in that channel (This is very important).
    3. Send a message "Hello" in that channel.
    4. Forward that message to **@userinfobot**.
    5. Copy the ID shown there (It must start with `-100`).
* **Example:** `-1001234567890`

### 6. APP_URL
* **What is it?** The website link of your deployed bot.
* **How to get it:** After deploying on Koyeb, copy the Public URL from the Dashboard.
* **Important:** It must start with `https://` and must NOT have a `/` at the end.
* **Example:** `https://my-app-name.koyeb.app`

---

## 🚀 How to Deploy on Koyeb (Step-by-Step)

1. **Fork/Copy Code:** Fork this repository to your GitHub account.
2. **Create Service:** Login to **[Koyeb](https://www.koyeb.com)** and create a new **Web Service**.
3. **Select Source:** Choose **GitHub** and select this repository.
4. **Add Variables:** Go to **Settings** → **Environment Variables** and add the 6 values explained above.
5. **Configure Port:**
   - Go to the **Settings** tab.
   - Change the **Port** to `8000`.
   - Set **Builder** to `Buildpack`.
6. **Deploy:** Click the **Deploy** button.

---

## 🤖 How to Use
1. Start the bot: `/start`
2. Send any file (Video, Audio, Document) to the bot.
3. The bot will automatically save it to your Storage Channel.
4. It will give you a **High-Speed Direct Download Link**.

---

### ⚠️ Common Errors & Fixes
* **Error: Peer id invalid:**
  - This means your `LOG_CHANNEL_ID` is wrong or the bot is not an Admin.
  - **Fix:** Make the bot an **Admin** in the storage channel.
* **Error: 502 Bad Gateway:**
  - This means the port is wrong.
  - **Fix:** Go to Koyeb Settings and ensure the **Port** is set to `8000`.

---
**Credits:** Created for Personal Use.

