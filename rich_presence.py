# rich_presence.py - Rich Presence for BrainAllianceFX Bot
# Fully editable by commands with image support

import discord
import json
import os

# =============================================================================
# RICH PRESENCE SETTINGS - Default values (can be overridden by commands)
# =============================================================================

# Default settings
DEFAULT_BOT_STATUS = discord.Status.dnd
DEFAULT_ACTIVITY_TYPE = discord.ActivityType.listening
DEFAULT_ACTIVITY_TEXT = "BrainAlliance 🧠"
DEFAULT_ENABLE_STREAMING = False
DEFAULT_STREAMING_TITLE = "FORMAZIONE"
DEFAULT_STREAMING_URL = "https://discord.com/channels/1388900966727680141/1424749308892151968"
DEFAULT_SHOW_SERVER_COUNT = False
DEFAULT_SHOW_MEMBER_COUNT = False
DEFAULT_LARGE_IMAGE = "brainalliance_logo"  # Upload this image to Discord Rich Presence assets
DEFAULT_LARGE_TEXT = "BrainAlliance VIP"
DEFAULT_SMALL_IMAGE = "brain_emoji"  # Upload this image to Discord Rich Presence assets
DEFAULT_SMALL_TEXT = "Brain"

# Settings file to store command changes
SETTINGS_FILE = 'rich_presence_settings.json'

# =============================================================================
# RICH PRESENCE MANAGER
# =============================================================================

class RichPresenceManager:
    def __init__(self):
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or use defaults"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                # Convert string values back to discord objects
                settings['bot_status'] = getattr(discord.Status, settings.get('bot_status', 'dnd'))
                settings['activity_type'] = getattr(discord.ActivityType, settings.get('activity_type', 'listening'))
                return settings
            else:
                return self.get_default_settings()
        except Exception as e:
            print(f"❌ Error loading settings: {e}")
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Get default settings"""
        return {
            'bot_status': DEFAULT_BOT_STATUS,
            'activity_type': DEFAULT_ACTIVITY_TYPE,
            'activity_text': DEFAULT_ACTIVITY_TEXT,
            'enable_streaming': DEFAULT_ENABLE_STREAMING,
            'streaming_title': DEFAULT_STREAMING_TITLE,
            'streaming_url': DEFAULT_STREAMING_URL,
            'show_server_count': DEFAULT_SHOW_SERVER_COUNT,
            'show_member_count': DEFAULT_SHOW_MEMBER_COUNT,
            'large_image': DEFAULT_LARGE_IMAGE,
            'large_text': DEFAULT_LARGE_TEXT,
            'small_image': DEFAULT_SMALL_IMAGE,
            'small_text': DEFAULT_SMALL_TEXT
        }
    
    def save_settings(self):
        """Save settings to file"""
        try:
            # Convert discord objects to strings for JSON
            settings_to_save = self.settings.copy()
            settings_to_save['bot_status'] = self.settings['bot_status'].name
            settings_to_save['activity_type'] = self.settings['activity_type'].name
            
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings_to_save, f, indent=4)
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
    def update_setting(self, key, value):
        """Update a setting and save to file"""
        self.settings[key] = value
        self.save_settings()
    
    async def set_presence(self, bot):
        """Set the bot's Rich Presence based on current settings"""
        try:
            # Build activity text
            activity_text = self.settings['activity_text']
            
            # Add server/member count if enabled
            if self.settings['show_server_count'] or self.settings['show_member_count']:
                server_count = len(bot.guilds)
                member_count = sum(guild.member_count for guild in bot.guilds if guild.member_count)
                
                info_parts = []
                if self.settings['show_server_count']:
                    info_parts.append(f"{server_count} server{'s' if server_count != 1 else ''}")
                if self.settings['show_member_count']:
                    info_parts.append(f"{member_count:,} members")
                
                if info_parts:
                    activity_text += f" | {', '.join(info_parts)}"
            
            # Create activity based on type
            if self.settings['enable_streaming']:
                activity = discord.Streaming(
                    name=self.settings['streaming_title'],
                    url=self.settings['streaming_url']
                )
            else:
                # Create activity
                activity = discord.Activity(
                    type=self.settings['activity_type'],
                    name=activity_text
                )
            
            # Set the presence
            await bot.change_presence(
                status=self.settings['bot_status'],
                activity=activity
            )
            
            print(f"🎭 Rich Presence set: {activity_text}")
            print(f"🖼️ Large Image: {self.settings['large_image']}")
            print(f"🖼️ Small Image: {self.settings['small_image']}")
            print(f"📝 Large Text: {self.settings['large_text']}")
            print(f"📝 Small Text: {self.settings['small_text']}")
            
        except Exception as e:
            print(f"❌ Error setting Rich Presence: {e}")
    
    async def set_custom_activity(self, bot, text, activity_type=None):
        """Set a custom activity (for commands)"""
        try:
            if activity_type is None:
                activity_type = self.settings['activity_type']
            
            activity = discord.Activity(
                type=activity_type,
                name=text
            )
            
            await bot.change_presence(
                status=self.settings['bot_status'],
                activity=activity
            )
            
            print(f"🎭 Custom activity set: {text}")
            
        except Exception as e:
            print(f"❌ Error setting custom activity: {e}")
    
    async def reset_presence(self, bot):
        """Reset to default presence"""
        await self.set_presence(bot)

# Global instance
presence_manager = RichPresenceManager()

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def set_presence(bot):
    """Set the bot's Rich Presence based on current settings"""
    await presence_manager.set_presence(bot)

async def set_custom_activity(bot, text, activity_type=None):
    """Set a custom activity (for commands)"""
    await presence_manager.set_custom_activity(bot, text, activity_type)

async def reset_presence(bot):
    """Reset to default presence"""
    await presence_manager.reset_presence(bot)

# =============================================================================
# CUSTOMIZATION GUIDE
# =============================================================================

"""
🎭 RICH PRESENCE CUSTOMIZATION GUIDE

1. BASIC SETTINGS (edit the values at the top of this file):
   - DEFAULT_BOT_STATUS: Default bot status (online, idle, dnd, invisible)
   - DEFAULT_ACTIVITY_TYPE: Default activity type (playing, listening, watching, streaming, competing)
   - DEFAULT_ACTIVITY_TEXT: Default activity text

2. STREAMING (optional):
   - DEFAULT_ENABLE_STREAMING: Enable streaming by default
   - DEFAULT_STREAMING_TITLE: Default streaming title
   - DEFAULT_STREAMING_URL: Default streaming URL

3. SERVER INFO (optional):
   - DEFAULT_SHOW_SERVER_COUNT: Show server count by default
   - DEFAULT_SHOW_MEMBER_COUNT: Show member count by default

4. IMAGES (optional):
   - DEFAULT_LARGE_IMAGE: Default large image key
   - DEFAULT_LARGE_TEXT: Default large image text
   - DEFAULT_SMALL_IMAGE: Default small image key
   - DEFAULT_SMALL_TEXT: Default small image text

5. COMMANDS:
   - .setstatus <status> - Change bot status
   - .setactivity <text> - Set activity text
   - .settype <type> - Set activity type
   - .setstreaming <true/false> - Enable/disable streaming
   - .setstreamtitle <title> - Set streaming title
   - .setstreamurl <url> - Set streaming URL
   - .setservercount <true/false> - Show/hide server count
   - .setmembercount <true/false> - Show/hide member count
   - .setlargeimage <key> - Set large image
   - .setlargetext <text> - Set large image text
   - .setsmallimage <key> - Set small image
   - .setsmalltext <text> - Set small image text
   - .resetpresence - Reset to default
   - .presenceinfo - Show current settings
   - .presencehelp - Show this guide

6. EXAMPLES:
   - .setactivity "with BrainAllianceFX 🧠"
   - .settype playing
   - .setstatus online
   - .setlargeimage "brainalliance_logo"
   - .setlargetext "BrainAllianceFX Server"
"""