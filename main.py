from pyrogram import Client, filters
from pyrogram.types import Message, Chat
import asyncio
import json
import os
import re
import time
from flask import Flask, jsonify

# Bot configuration
API_ID = '2737672'
API_HASH = 'f4aae49f836134236a19d434f8597c45'
BOT_TOKEN = '7941752115:AAHAmDj-tUqNNuQGr32vt35-a2hv13aaL6Q'

# Initialize the client
app = Client('filter_bot_session', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Flask app for web interface
flask_app = Flask(__name__)

# Configuration file path
CONFIG_FILE = 'filter_config.json'
LOG_FILE = 'bot_logs.json'

# URL pattern for detecting links
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

class FilterBot:
    def __init__(self):
        self.config = self.load_config()
        self.logs = self.load_logs()
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            'allowed_links': [],
            'banned_words': [],
            'monitored_channels': []
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def add_banned_word(self, word):
        """Add a word to banned words list"""
        word = word.lower().strip()
        if word and word not in self.config['banned_words']:
            self.config['banned_words'].append(word)
            self.save_config()
            return True
        return False
    
    def remove_banned_word(self, word):
        """Remove a word from banned words list"""
        word = word.lower().strip()
        if word in self.config['banned_words']:
            self.config['banned_words'].remove(word)
            self.save_config()
            return True
        return False

    def add_allowed_link(self, link):
        """Add a link to allowed links list"""
        cleaned_link = re.sub(r'https?://(www\.)?', '', link.lower())
        if cleaned_link not in self.config['allowed_links']:
            self.config['allowed_links'].append(cleaned_link)
            self.save_config()
            return True
        return False
    
    def remove_allowed_link(self, link):
        """Remove a link from allowed links list"""
        cleaned_link = re.sub(r'https?://(www\.)?', '', link.lower())
        if cleaned_link in self.config['allowed_links']:
            self.config['allowed_links'].remove(cleaned_link)
            self.save_config()
            return True
        return False

    def is_link_allowed(self, link):
        """Check if a link is in the allowed list"""
        cleaned_link = re.sub(r'https?://(www\.)?', '', link.lower())
        return any(allowed in cleaned_link for allowed in self.config['allowed_links'])

    def contains_banned_word(self, text):
        """Check if text contains any banned words"""
        text = text.lower()
        for word in self.config['banned_words']:
            if word in text:
                return True, word
        return False, None

    def log(self, event_type, message):
        """Log events to the logs list"""
        log_entry = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'event_type': event_type,
            'message': message
        }
        self.logs.append(log_entry)
        self.save_logs()

    def save_logs(self):
        """Save logs to file"""
        with open(LOG_FILE, 'w') as f:
            json.dump(self.logs, f, indent=4)

    def load_logs(self):
        """Load logs from file"""
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        return []


# Initialize bot
bot = FilterBot()

@app.on_message(filters.command('start'))
async def start_command(client, message: Message):
    if message.chat.type == 'private':
        bot.log('command', '/start command executed')
        await message.reply(
            "👋 Welcome to the Content Filter Bot!\n\n"
            "Available commands:\n"
            "🔤 Word Commands:\n"
            "/addword <word> - Add word to ban list\n"
            "/removeword <word> - Remove word from ban list\n"
            "/listwords - Show all banned words\n\n"
            "🔗 Link Commands:\n"
            "/allowlink <link> - Add link to whitelist\n"
            "/removelink <link> - Remove link from whitelist\n"
            "/listlinks - Show allowed links\n\n"
            "/help - Show detailed help"
        )

# Flask route to return bot logs in JSON format
@flask_app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify(bot.logs)

@app.on_message(filters.command('addword'))
async def add_word_command(client, message: Message):
    if message.chat.type == 'private':
        word = message.text.replace('/addword', '').strip()
        if word:
            if bot.add_banned_word(word):
                bot.log('command', f"/addword: Added '{word}' to banned words.")
                await message.reply(f"✅ Added '{word}' to banned words.")
            else:
                bot.log('command', f"/addword: '{word}' is already banned.")
                await message.reply(f"⚠️ '{word}' is already banned.")
        else:
            bot.log('command', "/addword: Missing word parameter.")
            await message.reply("Please provide a word to ban.\nUsage: /addword <word>")

# ... other commands go here

# Run both the bot and the Flask web server

from threading import Thread

# Function to run the bot
def run_bot():
    app.run()  # This will block, as it's the method that starts the bot

# Function to run the Flask web server
def run_flask():
    flask_app.run(host='0.0.0.0', port=8000)

# Function to run both bot and Flask app
def run_bot_and_flask():
    # Run Pyrogram bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.start()

    # Run Flask web server for logs
    run_flask()

# Start both the bot and the web server
if __name__ == '__main__':
    run_bot_and_flask()

# Start both the bot and the web server


