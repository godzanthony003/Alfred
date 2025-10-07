# 🎭 Complete Rich Presence Guide

## Overview
Your Discord bot now has a **completely command-editable** Rich Presence system with full image support! Every aspect of your bot's presence can be controlled through commands, with settings automatically saved and persistent across restarts.

## 🚀 Quick Start

### Basic Commands
- `.setstatus <status>` - Change bot status (online, idle, dnd, invisible)
- `.setactivity <text>` - Set activity text
- `.settype <type>` - Set activity type (playing, listening, watching, streaming, competing)
- `.presenceinfo` - Show current settings
- `.presencehelp` - Show complete command guide

### Example Usage
```
.setstatus online
.setactivity "with BrainAllianceFX 🧠"
.settype playing
.setlargeimage "brainalliance_logo"
.setlargetext "BrainAllianceFX Server"
```

## 🔧 Complete Command List

### Basic Commands
- `.setstatus <status>` → Change bot status
- `.setactivity <text>` → Set activity text
- `.settype <type>` → Set activity type
- `.resetpresence` → Reset to default

### Streaming Commands
- `.setstreaming <true/false>` → Enable/disable streaming
- `.setstreamtitle <title>` → Set streaming title
- `.setstreamurl <url>` → Set streaming URL

### Display Commands
- `.setservercount <true/false>` → Show/hide server count
- `.setmembercount <true/false>` → Show/hide member count

### Image Commands
- `.setlargeimage <key>` → Set large image
- `.setlargetext <text>` → Set large image text
- `.setsmallimage <key>` → Set small image
- `.setsmalltext <text>` → Set small image text

## 🎯 Activity Types

### Playing
- Shows as "Playing [text]"
- Best for general activities
- Example: `.settype playing`

### Listening
- Shows as "Listening to [text]"
- Good for monitoring activities
- Example: `.settype listening`

### Watching
- Shows as "Watching [text]"
- Perfect for observation activities
- Example: `.settype watching`

### Streaming
- Shows as "Streaming [text]"
- Requires streaming to be enabled
- Example: `.settype streaming`

### Competing
- Shows as "Competing in [text]"
- Good for competitive activities
- Example: `.settype competing`

## 📊 Status Options

### Online (Green dot)
- Normal operational status
- Example: `.setstatus online`

### Idle (Yellow dot)
- Bot is online but not actively doing anything
- Example: `.setstatus idle`

### Do Not Disturb (Red dot)
- Bot is busy and shouldn't be interrupted
- Example: `.setstatus dnd`

### Invisible (Gray dot)
- Bot appears offline but is still functional
- Example: `.setstatus invisible`

## 🖼️ Image Support

### Large Image
- Main image displayed in Rich Presence
- Use image keys from Discord's Rich Presence assets
- Example: `.setlargeimage "brainalliance_logo"`

### Large Image Text
- Tooltip text when hovering over large image
- Example: `.setlargetext "BrainAllianceFX Server"`

### Small Image
- Small image displayed next to the large image
- Example: `.setsmallimage "verified_badge"`

### Small Image Text
- Tooltip text when hovering over small image
- Example: `.setsmalltext "Verified Bot"`

## 💡 Complete Examples

### Gaming Theme
```
.setstatus online
.setactivity "in the server arena 🏟️"
.settype competing
.setlargeimage "gaming_logo"
.setlargetext "BrainAllianceFX Gaming"
.setsmallimage "level_badge"
.setsmalltext "Level 100"
```

### Professional Theme
```
.setstatus dnd
.setactivity "managing server infrastructure 🏢"
.settype watching
.setlargeimage "company_logo"
.setlargetext "BrainAllianceFX Management"
.setsmallimage "admin_badge"
.setsmalltext "Administrator"
```

### Streaming Theme
```
.setstatus online
.setstreaming true
.setstreamtitle "BrainAllianceFX Bot Live"
.setstreamurl "https://twitch.tv/yourchannel"
.setlargeimage "stream_logo"
.setlargetext "Live Now!"
```

### Fun Theme
```
.setstatus idle
.setactivity "throwing virtual parties 🎉"
.settype listening
.setlargeimage "party_logo"
.setlargetext "Party Time!"
.setsmallimage "confetti"
.setsmalltext "Celebrating!"
```

## 🔄 How It Works

### Settings Persistence
- All settings are automatically saved to `rich_presence_settings.json`
- Settings persist across bot restarts
- No need to reconfigure after restarting

### Real-time Updates
- Changes take effect immediately
- No need to restart the bot
- All commands update the presence instantly

### Default Settings
- Default values are set in `rich_presence.py`
- Use `.resetpresence` to return to defaults
- Defaults are used when settings file doesn't exist

## 🎨 Creative Ideas

### Seasonal Themes
- Update activities for holidays and seasons
- Use seasonal emojis and language
- Create special activities for events

### Server Milestones
- Celebrate member count milestones
- Acknowledge server anniversaries
- Highlight special achievements

### Interactive Activities
- Use activities to communicate with members
- Show current server events
- Display helpful information

### Image Combinations
- Use large image for main branding
- Use small image for status indicators
- Combine images with descriptive text

## 🚨 Troubleshooting

### Rich Presence Not Updating
1. Check if the bot has proper permissions
2. Use `.presenceinfo` to see current settings
3. Check console for error messages
4. Try `.resetpresence` to reset to defaults

### Commands Not Working
1. Make sure you're using the correct command syntax
2. Check if the bot is online and responding
3. Verify you have permission to use the commands
4. Use `.presencehelp` for command reference

### Images Not Showing
1. Make sure image keys are valid Discord Rich Presence assets
2. Check if images are properly uploaded to Discord
3. Verify image keys are spelled correctly
4. Use `.presenceinfo` to see current image settings

### Streaming Not Working
1. Set `.setstreaming true` first
2. Provide a valid streaming URL
3. Set a streaming title
4. Ensure the URL is accessible

## 📝 Best Practices

### 1. Use Emojis
- Emojis make activities more visually appealing
- Choose emojis that match your server's theme
- Don't overuse emojis (1-2 per activity is enough)

### 2. Keep Messages Short
- Discord has character limits for activities
- Keep messages under 50 characters when possible
- Test your messages to ensure they display properly

### 3. Match Your Brand
- Use language that matches your server's personality
- Include your server name or theme in activities
- Make activities relevant to your bot's purpose

### 4. Use Images Effectively
- Large image should represent your main brand
- Small image can show status or additional info
- Use descriptive text for both images
- Keep image keys simple and memorable

### 5. Test Before Deploying
- Use `.presenceinfo` to verify settings
- Test different combinations of settings
- Make sure everything works before finalizing

## 🔄 Updating Your Configuration

### Method 1: Commands (Recommended)
1. Use the various `.set*` commands
2. Settings are automatically saved
3. Changes take effect immediately

### Method 2: Code (Advanced)
1. Edit `rich_presence.py` to change defaults
2. Use `.resetpresence` to apply new defaults
3. Or restart the bot to load new defaults

## 📞 Support

If you need help with Rich Presence customization:
1. Check this guide first
2. Use `.presencehelp` for quick reference
3. Use `.presenceinfo` to see current settings
4. Check the console for error messages

## 🎉 Conclusion

Your Rich Presence system is now **completely command-editable** with full image support! You can control every aspect of your bot's presence through simple commands, with all settings automatically saved and persistent. The system is designed to be intuitive and powerful, giving you complete control over how your bot appears to users.

Remember: The best Rich Presence is one that reflects your server's personality and provides useful information to your members. Have fun customizing! 🚀

## 🎯 Quick Reference

### Most Used Commands
- `.setactivity "your text here"` - Set what your bot is doing
- `.settype playing` - Set activity type
- `.setstatus online` - Set bot status
- `.setlargeimage "your_image_key"` - Set main image
- `.presenceinfo` - See current settings
- `.presencehelp` - Get help

### Image Setup
1. Upload images to Discord Rich Presence assets
2. Use `.setlargeimage "key"` to set main image
3. Use `.setlargetext "text"` to set image tooltip
4. Use `.setsmallimage "key"` for small image
5. Use `.setsmalltext "text"` for small image tooltip

### Streaming Setup
1. Use `.setstreaming true` to enable
2. Use `.setstreamtitle "title"` to set title
3. Use `.setstreamurl "url"` to set URL
4. Use `.settype streaming` for streaming type