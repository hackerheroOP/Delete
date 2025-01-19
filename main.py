
from flask import Flask, jsonify
from threading import Thread
from telethon import TelegramClient, events
from telethon.tl.types import Channel
import asyncio
import json
import os
import re

# Bot configuration
API_ID = '2737672'
API_HASH = 'f4aae49f836134236a19d434f8597c45'
BOT_TOKEN = '7941752115:AAHAmDj-tUqNNuQGr32vt35-a2hv13aaL6Q'

# Initialize the client
client = TelegramClient('filter_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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

# Flask app for health check
app = Flask(__name__)

@app.route('/status', methods=['GET'])
def bot_status():
    return jsonify({
        "status": "running",
        "message": "The bot is active and monitoring channels."
    })

def run_web_server():
    app.run(host="0.0.0.0", port=8000, debug=False)

# Start the Flask server in a separate thread
web_thread = Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()

@client.on(events.NewMessage(pattern='/addchannel'))
async def add_channel_command(event):
    if event.is_private:
        sender = await event.get_sender()
        # Ensure only admins can add channels
        if not sender.bot:  # Customize admin check as needed
            channel_username_or_id = event.raw_text.replace('/addchannel', '').strip()
            
            if channel_username_or_id:
                try:
                    chat = await client.get_entity(channel_username_or_id)
                    if isinstance(chat, Channel):
                        channel_id = str(chat.id)
                        if channel_id not in bot.config['monitored_channels']:
                            bot.config['monitored_channels'].append(channel_id)
                            bot.save_config()
                            await event.respond(f"âœ… Channel '{channel_username_or_id}' added to monitored list.")
                        else:
                            await event.respond(f"âš ï¸ Channel '{channel_username_or_id}' is already monitored.")
                    else:
                        await event.respond("âŒ The provided entity is not a valid channel.")
                except Exception as e:
                    await event.respond(f"âš ï¸ Error adding channel: {str(e)}")
            else:
                await event.respond("Please provide a valid channel username or ID.\nUsage: /addchannel <channel_username_or_id>")
        else:
            await event.respond("âŒ Only admins can add channels.")

@client.on(events.NewMessage())
async def handle_new_message(event):
    try:
        # Check if message is in a monitored channel
        if isinstance(event.message.peer_id, Channel):
            channel_id = str(event.message.peer_id.channel_id)
            if channel_id in bot.config['monitored_channels']:
                if event.message.message:
                    text = event.message.message
                    
                    # Check for banned words
                    has_banned_word, banned_word = bot.contains_banned_word(text)
                    if has_banned_word:
                        await event.delete()
                        print(f"Deleted message containing banned word: {banned_word}")
                        return
                    
                    # Check for unauthorized links
                    links = re.findall(URL_PATTERN, text)
                    if links:
                        for link in links:
                            if not bot.is_link_allowed(link):
                                await event.delete()
                                print(f"Deleted message containing unauthorized link: {link}")
                                return
                    
    except Exception as e:
        print(f"Error processing message: {str(e)}")

async def main():
    print("Bot started...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
