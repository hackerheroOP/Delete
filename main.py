from telethon import TelegramClient, events
from telethon.tl.types import Channel
import re
import json
import asyncio
import os

# URL Pattern for link detection
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
# List of admin user IDs
ADMIN_IDS = [5847637609, 1251111009]


class Bot:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                # Ensure all required keys exist
                if 'monitored_channels' not in config:
                    config['monitored_channels'] = []
                if 'banned_words' not in config:
                    config['banned_words'] = []
                if 'allowed_links' not in config:
                    config['allowed_links'] = []
                self.save_config(config)
                return config
        except FileNotFoundError:
            default_config = {
                'monitored_channels': [],
                'banned_words': [],
                'allowed_links': []
            }
            self.save_config(default_config)
            return default_config
            
    def save_config(self, config=None):
        if config is None:
            config = self.config
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
    def contains_banned_word(self, text):
        if not text:
            return False, None
        text = text.lower()
        for word in self.config['banned_words']:
            if word.lower() in text:
                return True, word
        return False, None

# Initialize bot
bot = Bot()

# Initialize client
API_ID = 'Promorningstar'
API_HASH = 'Iz'
BOT_TOKEN = 'Promutthal apna'

client = TelegramClient('bot_session', API_ID, API_HASH)
def is_admin(user_id):
    return user_id in ADMIN_IDS


@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        await event.respond(
            "👋 Welcome to the Content Filter Bot!\n\n"
            "Available commands:\n\n"
            "🔤 Word Commands:\n"
            "/addword <word> - Add word to ban list\n"
            "/removeword <word> - Remove word from ban list\n"
            "/listwords - Show all banned words\n\n"
            "🔗 Link Commands:\n"
            "/allowlink <link> - Add link to whitelist\n"
            "/removelink <link> - Remove link from whitelist\n"
            "/listlinks - Show allowed links\n\n"
            "📢 Channel Commands:\n"
            "/addchannel <channel> - Monitor a channel\n"
            "/removechannel <channel> - Stop monitoring\n"
            "/listchannels - Show monitored channels\n\n"
            "/help - Show detailed help"
        )

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    if event.is_private:
        await event.respond(
            "📖 Detailed Help:\n\n"
            "🔤 Word Commands:\n"
            "/addword <word> - Add a word to ban list\n"
            "/removeword <word> - Remove a word from ban list\n"
            "/listwords - Show all banned words\n\n"
            "🔗 Link Commands:\n"
            "/allowlink <link> - Add link to whitelist\n"
            "/removelink <link> - Remove link from whitelist\n"
            "/listlinks - Show allowed links\n\n"
            "📢 Channel Commands:\n"
            "/addchannel <username/id> - Start monitoring a channel\n"
            "/removechannel <username/id> - Stop monitoring a channel\n"
            "/listchannels - Show all monitored channels\n\n"
            "Note: Bot must be admin in channels to work!"
        )

@client.on(events.NewMessage(pattern='/addword'))
async def add_word_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        word = event.raw_text.replace('/addword', '').strip().lower()
        if word:
            if word not in bot.config['banned_words']:
                bot.config['banned_words'].append(word)
                bot.save_config()
                await event.respond(f"✅ Added '{word}' to banned words list.")
            else:
                await event.respond(f"⚠️ '{word}' is already in banned words list.")
        else:
            await event.respond("❌ Please provide a word.\nUsage: /addword <word>")

@client.on(events.NewMessage(pattern='/removeword'))
async def remove_word_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        word = event.raw_text.replace('/removeword', '').strip().lower()
        if word:
            if word in bot.config['banned_words']:
                bot.config['banned_words'].remove(word)
                bot.save_config()
                await event.respond(f"✅ Removed '{word}' from banned words list.")
            else:
                await event.respond(f"⚠️ '{word}' is not in banned words list.")
        else:
            await event.respond("❌ Please provide a word.\nUsage: /removeword <word>")

@client.on(events.NewMessage(pattern='/listwords'))
async def list_words_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        words = bot.config['banned_words']
        if words:
            word_list = "\n".join(f"• {word}" for word in words)
            await event.respond(f"📋 Banned Words List:\n\n{word_list}")
        else:
            await event.respond("No words are banned yet.")

@client.on(events.NewMessage(pattern='/allowlink'))
async def allow_link_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        link = event.raw_text.replace('/allowlink', '').strip().lower()
        if link:
            if link not in bot.config['allowed_links']:
                bot.config['allowed_links'].append(link)
                bot.save_config()
                await event.respond(f"✅ Added '{link}' to allowed links list.")
            else:
                await event.respond(f"⚠️ '{link}' is already allowed.")
        else:
            await event.respond("❌ Please provide a link.\nUsage: /allowlink <link>")

@client.on(events.NewMessage(pattern='/removelink'))
async def remove_link_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        link = event.raw_text.replace('/removelink', '').strip().lower()
        if link:
            if link in bot.config['allowed_links']:
                bot.config['allowed_links'].remove(link)
                bot.save_config()
                await event.respond(f"✅ Removed '{link}' from allowed links list.")
            else:
                await event.respond(f"⚠️ '{link}' is not in allowed links list.")
        else:
            await event.respond("❌ Please provide a link.\nUsage: /removelink <link>")

@client.on(events.NewMessage(pattern='/listlinks'))
async def list_links_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        links = bot.config['allowed_links']
        if links:
            link_list = "\n".join(f"• {link}" for link in links)
            await event.respond(f"📋 Allowed Links List:\n\n{link_list}")
        else:
            await event.respond("No links are allowed yet.")

@client.on(events.NewMessage(pattern='/addchannel'))
async def add_channel_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        channel = event.raw_text.replace('/addchannel', '').strip()
        if channel:
            try:
                # Handle channel ID
                if channel.startswith('-100'):
                    channel_id = channel
                else:
                    channel_id = f"-100{channel}"
                
                try:
                    # Try to directly use the channel ID
                    int_channel_id = int(channel_id)
                    
                    # Add to monitored channels without additional checks
                    if channel_id not in bot.config['monitored_channels']:
                        bot.config['monitored_channels'].append(channel_id)
                        bot.save_config()
                        await event.respond(f"✅ Added channel to monitoring list.\nChannel ID: {channel_id}\n\nIf the bot cannot delete messages, please:\n1. Make sure bot is added to channel\n2. Give bot admin rights\n3. Verify the channel ID")
                    else:
                        await event.respond("⚠️ This channel is already being monitored!")
                    
                except ValueError:
                    await event.respond("❌ Invalid channel ID format. Please use the numeric ID.")
            except Exception as e:
                print(f"Debug - Error adding channel: {str(e)}")
                await event.respond("❌ Failed to add channel. Please make sure the channel ID is correct.")
        else:
            await event.respond("❌ Please provide a channel ID.\nUsage: /addchannel <channel_id>")

@client.on(events.NewMessage(pattern='/removechannel'))
async def remove_channel_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        channel = event.raw_text.replace('/removechannel', '').strip()
        if channel:
            try:
                # Handle channel ID
                if channel.startswith('-100'):
                    channel_id = channel
                else:
                    channel_id = f"-100{channel}"
                
                if channel_id in bot.config['monitored_channels']:
                    bot.config['monitored_channels'].remove(channel_id)
                    bot.save_config()
                    await event.respond(f"✅ Removed channel from monitoring list.\nChannel ID: {channel_id}")
                else:
                    await event.respond("⚠️ This channel is not in the monitoring list.")
            except Exception as e:
                await event.respond("❌ Failed to remove channel. Please verify the channel ID.")
        else:
            await event.respond("❌ Please provide a channel ID.\nUsage: /removechannel <channel_id>")

@client.on(events.NewMessage(pattern='/listchannels'))
async def list_channels_command(event):
    if event.is_private:
        if not is_admin(event.sender_id):
            await event.respond("❌ You are not authorized to use this bot.")
            return
        channels = bot.config['monitored_channels']
        if channels:
            channel_list = []
            for channel_id in channels:
                try:
                    # Convert channel_id to integer
                    int_channel_id = int(channel_id)
                    
                    try:
                        # Try to get channel info
                        channel = await client.get_entity(int_channel_id)
                        
                        # Get channel type (public/private)
                        if channel.username:
                            channel_type = "Public"
                            channel_info = f"@{channel.username}"
                        else:
                            channel_type = "Private"
                            channel_info = "Private Channel"
                        
                        # Add channel information to list
                        channel_list.append(
                            f"• {channel.title}\n"
                            f"  ID: {channel_id}\n"
                            f"  Type: {channel_type}\n"
                            f"  Link: {channel_info}\n"
                        )
                    except Exception as e:
                        # If can't get channel info, show basic info
                        channel_list.append(
                            f"• Unknown Channel\n"
                            f"  ID: {channel_id}\n"
                            f"  Type: Unknown\n"
                        )
                except ValueError:
                    channel_list.append(
                        f"• Invalid Channel ID\n"
                        f"  ID: {channel_id}\n"
                    )
            
            # Create formatted message
            message = "📋 **Monitored Channels List:**\n\n" + "\n".join(channel_list)
            
            # Add total count
            message += f"\n\n**Total Channels:** {len(channels)}"
            
            await event.respond(message)
        else:
            await event.respond("No channels are being monitored yet.")


@client.on(events.NewMessage)
async def handle_new_message(event):
    try:
        # Check if message is in a monitored channel
        chat_id = str(event.chat_id)
        if chat_id.startswith('-100'):
            channel_id = chat_id
        else:
            channel_id = f"-100{chat_id}"
            
        if channel_id in bot.config['monitored_channels']:
            message = event.message
            
            # Check for forwarded messages
            if message.forward:
                try:
                    await message.delete()
                    print(f"Deleted forwarded message in channel {channel_id}")
                except Exception as e:
                    print(f"Error deleting forwarded message: {str(e)}")
                return
            
            if message.text:
                # Check for banned words
                has_banned, word = bot.contains_banned_word(message.text)
                if has_banned:
                    try:
                        await message.delete()
                        print(f"Deleted message containing banned word '{word}' in channel {channel_id}")
                    except Exception as e:
                        print(f"Error deleting message with banned word: {str(e)}")
                    return

                # Check for links
                links = re.findall(URL_PATTERN, message.text)
                if links:
                    for link in links:
                        if not any(allowed in link.lower() for allowed in bot.config['allowed_links']):
                            try:
                                await message.delete()
                                print(f"Deleted message containing unauthorized link in channel {channel_id}")
                            except Exception as e:
                                print(f"Error deleting message with unauthorized link: {str(e)}")
                            return
    except Exception as e:
        print(f"Error processing message: {str(e)}")

async def main():
    print("Starting bot...")
    try:
        # Start the client
        await client.start(bot_token=BOT_TOKEN)
        print("Bot is running!")
        print(f"Monitored channels: {len(bot.config['monitored_channels'])}")
        print(f"Banned words: {len(bot.config['banned_words'])}")
        print(f"Allowed links: {len(bot.config['allowed_links'])}")
        
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Error starting bot: {str(e)}")

if __name__ == '__main__':
    # Run the bot
    asyncio.run(main())
