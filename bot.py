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
    required_channels = ["@channel1", "@channel2"]  # Replace with your channel usernames
    for channel in required_channels:
        try:
            member = await client.get_chat_member(channel, user_id)
       
