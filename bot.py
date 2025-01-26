from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from instagrapi import Client as InstaClient
import yt_dlp
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
OWNER_ID = int(os.getenv("OWNER_ID"))
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Define required channels globally
REQUIRED_CHANNELS = ["@SR_ROBOTS", "@Xstream_links2"]  # Replace with your channel usernames

# Initialize Bot and Database
bot = Client("instagram_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize Instagram Client
insta_client = InstaClient()

# Login to Instagram
try:
    insta_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    print("Logged in to Instagram successfully!")
except Exception as e:
    print(f"Instagram login failed: {e}")
    exit()

# Initialize MongoDB Client
db_client = MongoClient(MONGO_URI)
db = db_client[DB_NAME]
users_collection = db["users"]

# Add user to the database if they send any message
@bot.on_message(filters.private & ~filters.service)
async def add_user_to_db(client, message: Message):
    user_id = message.from_user.id
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})
        print(f"Added new user: {user_id}")

# Check if the user is subscribed to the required channels
async def is_subscribed(client, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# Start Command
@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id

    # Check subscription
    if not await is_subscribed(client, user_id):
        buttons = [
            [InlineKeyboardButton("Join Channel 1", url=f"https://t.me/{REQUIRED_CHANNELS[0][1:]}")],
            [InlineKeyboardButton("Join Channel 2", url=f"https://t.me/{REQUIRED_CHANNELS[1][1:]}")],
            [InlineKeyboardButton("Join Channel 3", url="https://t.me/+6HvyRM1ccNM5YzE1")],  # New button added here, moved to 3rd position
            [InlineKeyboardButton("I Joined ✅", callback_data="check_subscription")]
        ]
        await message.reply(
            "You need to join our channels to use this bot:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    await message.reply("Welcome! Send me an Instagram or YouTube video link to download it.")

# Check Subscription Callback
@bot.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(client, callback_query):
    user_id = callback_query.from_user.id
    if await is_subscribed(client, user_id):
        await callback_query.message.edit("Thank you for joining! Send me a video link to download.")
    else:
        await callback_query.answer("You haven't joined the channels yet!", show_alert=True)

# Download Media
@bot.on_message(filters.text)
async def download_media(client, message: Message):
    url = message.text.strip()

    # Ignore commands (messages starting with '/')
    if message.text.startswith('/'):
        return

    # Check subscription
    if not await is_subscribed(client, message.from_user.id):
        buttons = [
            [InlineKeyboardButton("Join Channel 1", url=f"https://t.me/{REQUIRED_CHANNELS[0][1:]}")],
            [InlineKeyboardButton("Join Channel 2", url=f"https://t.me/{REQUIRED_CHANNELS[1][1:]}")],
            [InlineKeyboardButton("Join Channel 3", url="https://t.me/+6HvyRM1ccNM5YzE1")],  # Moved to 3rd position
            [InlineKeyboardButton("I Joined ✅", callback_data="check_subscription")]
        ]
        await message.reply(
            "You need to join our channels to use this bot:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # Download Instagram content
    if "instagram.com" in url:
        try:
            media_path = insta_client.video_download(url)
            await message.reply_document(document=media_path, caption="Here is your Instagram video!")
            os.remove(media_path)  # Clean up
        except Exception as e:
            await message.reply(f"Failed to download Instagram media: {e}")

    # Download YouTube content
    elif "youtube.com" in url or "youtu.be" in url:
        ydl_opts = {
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "format": "best",
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                await message.reply_video(video=video_path, caption="Here is your YouTube video!")
                os.remove(video_path)  # Clean up
        except Exception as e:
            await message.reply(f"Failed to download YouTube video: {e}")

    else:
        await message.reply("Invalid link. Please send a valid Instagram or YouTube video link.")

# Broadcast Command
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_message(client, message: Message):
    if not message.reply_to_message:
        await message.reply("Please reply to a message to broadcast.")
        return

    broadcast_message = message.reply_to_message
    users = users_collection.find()

    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            await client.send_message(user["user_id"], broadcast_message.text or broadcast_message.caption)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send message to {user['user_id']}: {e}")
            failed_count += 1

    await message.reply(f"Broadcast completed.\nSent: {sent_count}\nFailed: {failed_count}")

# Users Command (To see how many users are in the bot)
@bot.on_message(filters.command("users") & filters.user(OWNER_ID))
async def users_count(client, message: Message):
    user_count = users_collection.count_documents({})
    await message.reply(f"There are currently {user_count} users in the bot.")

# Run the Bot
bot.run()
