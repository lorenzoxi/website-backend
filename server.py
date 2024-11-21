from quart import Quart, jsonify
from quart_cors import cors
from telethon import TelegramClient
from dotenv import load_dotenv
import re
import os
import json
import hypercorn.asyncio
import asyncio
from tinydb import TinyDB, Query
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")

# Telegram Bot credentials
channel_username = os.getenv(
    "CHANNEL_USERNAME"
)  # Public channel username (e.g., "@example_channel")
api_id = int(os.getenv("API_ID"))  # API ID from https://my.telegram.org
api_hash = os.getenv("API_HASH")  # API Hash from https://my.telegram.org
bot_token = os.getenv("BOT_TOKEN")  # Bot token from @BotFather

# Initialize Telethon client for the bot
client = TelegramClient("bot_session", api_id, api_hash)

# Initialize TinyDB
db = TinyDB("db.json")
message_table = db.table("messages")


@app.before_serving
async def startup():
    """Start the Telegram client when the server starts."""
    await client.start(bot_token=bot_token)
    if not client.is_connected():
        raise Exception("Failed to connect to Telegram.")


@app.after_serving
async def shutdown():
    """Disconnect the Telegram client when the server shuts down."""
    await client.disconnect()


@app.route("/", methods=["GET"])
async def index():
    """Health check endpoint."""
    return "<h1>Service is up and running.</h1>"


@app.route("/get_messages", methods=["GET"])
async def get_messages():
    """Fetch the last 10 messages from the public channel."""
    try:
        # Fetch updates from the Telegram Bot API
        updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.post(url=updates_url)
        updates = response.json()

        # list the attributes of the updates
        updates = updates["result"]

        # read the messages from the database
        messages = []
        messages = db.all()

        # Process each update and store in TinyDB if not already present
        for message in updates:

            res = {"text": "", "date": "", "edit_date": "", "message_id": ""}

            if "edited_channel_post" in message:
                message = message["edited_channel_post"]
                res["edit_date"] = datetime.fromtimestamp(message["edit_date"]).strftime("%Y-%m-%d")
            else:
                message = message["channel_post"]

            res["text"] = message["text"]
            res["message_id"] = message["message_id"]

            dt_object = datetime.fromtimestamp(message["date"])
            formatted_date = dt_object.strftime("%Y-%m-%d")
            res["date"] = formatted_date

            # check if message is already in the database
            Message = Query()
            if not db.search(Message.message_id == res["message_id"]):
                message_table.insert(res)
                messages.append(res)

    except Exception as e:
        print(f"Error fetching messages: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify(messages)


if __name__ == "__main__":
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:8080"]

    # Use Hypercorn ASGI server to run Quart app
    asyncio.run(hypercorn.asyncio.serve(app, config))
