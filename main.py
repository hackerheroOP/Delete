from pyrogram import Client, filters
from pyrogram.types import Message, Chat
import asyncio
import json
import os
import re

# Bot configuration
API_ID = '2737672'
API_HASH = 'f4aae49f836134236a19d434f8597c45'
BOT_TOKEN = '7941752115:AAHAmDj-tUqNNuQGr32vt35-a2hv13aaL6Q'

# Initialize the client
app = Client('filter_bot_session', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Configuration file path
CONFIG_FILE = 'filter_config.json'

# URL pattern for detecting links
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

class FilterBot:
    def __init__(self):
        self.config = self.load_config()
        
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

# Initialize bot
bot = FilterBot()

# Flask app for health check (optional)
from flask import Flask, jsonify
from threading import Thread

app_flask = Flask(__name__)

@app_flask.route('/status', methods=['GET'])
def bot_status():
    return jsonify({
        "status": "running",
        "message": "The bot is active and monitoring channels."
    })

def run_web_server():
    app_flask.run(host="0.0.0.0", port=8000, debug=False)

# Start the Flask server in a separate thread
web_thread = Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()

@app.on_message(filters.command('start'))
async def start_command(client, message: Message):
    if message.chat.type == 'private':
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

@app.on_message(filters.command('addword'))
async def add_word_command(client, message: Message):
    if message.chat.type == 'private':
        word = message.text.replace('/addword', '').strip()
        if word:
            if bot.add_banned_word(word):
                await message.reply(f"✅ Added '{word}' to banned words.")
            else:
                await message.reply(f"⚠️ '{word}' is already banned.")
        else:
            await message.reply("Please provide a word to ban.\nUsage: /addword <word>")

@app.on_message(filters.command('removeword'))
async def remove_word_command(client, message: Message):
    if message.chat.type == 'private':
        word = message.text.replace('/removeword', '').strip()
        if word:
            if bot.remove_banned_word(word):
                await message.reply(f"❌ Removed '{word}' from banned words.")
            else:
                await message.reply(f"⚠️ '{word}' is not in banned words.")
        else:
            await message.reply("Please provide a word to remove.\nUsage: /removeword <word>")

@app.on_message(filters.command('listwords'))
async def list_words_command(client, message: Message):
    if message.chat.type == 'private':
        words = '\n'.join(bot.config['banned_words']) or 'No banned words yet'
        await message.reply(
            "📋 Banned Words List:\n\n"
            f"{words}"
        )

@app.on_message(filters.command('allowlink'))
async def allow_link_command(client, message: Message):
    if message.chat.type == 'private':
        link = message.text.replace('/allowlink', '').strip()
        if link:
            if bot.add_allowed_link(link):
                await message.reply(f"✅ Added '{link}' to allowed links.")
            else:
                await message.reply(f"⚠️ '{link}' is already allowed.")
        else:
            await message.reply("Please provide a link to allow.\nUsage: /allowlink <link>")

@app.on_message(filters.command('listlinks'))
async def list_links_command(client, message: Message):
    if message.chat.type == 'private':
        links = '\n'.join(bot.config['allowed_links']) or 'No links allowed yet'
        await message.reply(
            "📋 Allowed Links List:\n\n"
            f"{links}\n\n"
            "All other links will be deleted automatically."
        )

@app.on_message(filters.text)
async def handle_new_message(client, message: Message):
    try:
        # Check if message is in a monitored channel
        if message.chat.id in bot.config['monitored_channels']:
            if message.text:
                text = message.text
                
                # Check for banned words
                has_banned_word, banned_word = bot.contains_banned_word(text)
                if has_banned_word:
                    await message.delete()
                    print(f"Deleted message containing banned word: {banned_word}")
                    return
                
                # Check for unauthorized links
                links = re.findall(URL_PATTERN, text)
                if links:
                    for link in links:
                        if not bot.is_link_allowed(link):
                            await message.delete()
                            print(f"Deleted message containing unauthorized link: {link}")
                            return
    except Exception as e:
        print(f"Error processing message: {str(e)}")

@app.on_message(filters.command('addchannel'))
async def add_channel_command(client, message: Message):
    if message.chat.type == 'private':
        sender = message.from_user
        # Ensure only admins can add channels
        if not sender.is_bot:  # Customize admin check as needed
            channel_username_or_id = message.text.replace('/addchannel', '').strip()

            if channel_username_or_id:
                try:
                    # Attempt to get the channel entity
                    chat = await app.get_chat(channel_username_or_id)
                    if isinstance(chat, Chat) and chat.type == 'channel':
                        channel_id = str(chat.id)
                        if channel_id not in bot.config['monitored_channels']:
                            bot.config['monitored_channels'].append(channel_id)
                            bot.save_config()
                            await message.reply(f"✅ Channel '{channel_username_or_id}' added to monitored list.")
                        else:
                            await message.reply(f"⚠️ Channel '{channel_username_or_id}' is already monitored.")
                    else:
                        await message.reply("❌ The provided entity is not a valid channel.")
                except ValueError:
                    await message.reply("❌ The provided channel ID or username is not valid.")
                except Exception as e:
                    await message.reply(f"⚠️ Error adding channel: {str(e)}")
            else:
                await message.reply("❌ Please provide a valid channel username or ID.\nUsage: /addchannel <channel_username_or_id>")
        else:
            await message.reply("❌ Only admins can add channels.")

# Run the bot
app.run()
