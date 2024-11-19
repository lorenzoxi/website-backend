from flask_cors import CORS
from quart import Quart, jsonify
from quart_cors import cors
from telethon import TelegramClient
from dotenv import load_dotenv
from dotenv import dotenv_values
import datetime
import re
import json
import os

load_dotenv()


# Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")

# Telegram API credentials
channel_username = os.getenv("CHANNEL")
channel_id = os.getenv("CHANNEL_ID")
api_hash = os.getenv("API_HASH")
api_id = os.getenv("API_ID")


# Initialize Telegram Client for a user
client = TelegramClient("backend-1", api_id, api_hash)


@app.before_serving
async def startup():
    # Start the Telegram client when the server starts
    await client.start()


@app.after_serving
async def shutdown():
    # Disconnect the Telegram client when the server shuts down
    await client.disconnect()


@app.route("/get_messages", methods=["GET"])
async def get_messages():
    messages = []
    try:
        # Resolve the channel entity
        channel = await client.get_entity(channel_username)
        async for message in client.iter_messages(channel, limit=10):
            message = message.to_dict()
            
            if "message" in message:
                res = {'message': '', 'date': '', 'edit_date': ''}
                res['message'] = message['message']        
                
                #check if message has date and edit_date 
                if "date" in message and message["date"] is not None:
                    date = message['date']
                    res['date'] = re.search(r'\d{4}-\d{2}-\d{2}', str(date)).group()
                date_edit = ""
                if "edit_date" in message and message["edit_date"] is not None:
                    date_edit = message['edit_date']
                    res['edit_date'] = re.search(r'\d{4}-\d{2}-\d{2}', str(date_edit)).group()
                    
                #print("-------------------")
                #print(res)
                #print(type(res))
                #print("-------------------")
                messages.append(json.dumps(res))
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    return jsonify(messages)


if __name__ == "__main__":
    app.run()
