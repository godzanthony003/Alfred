# 🤖 BrainAllianceFX Discord Bot

A comprehensive Discord bot designed for advanced voice channel management, mentorship coordination, and server administration. This bot provides powerful tools for managing voice channels, user permissions, and automated workflows.

## ✨ Features

- **🎓 Mentorship Management**: Automated role assignment and private channel creation for mentorship sessions
- **🔊 Voice Channel Control**: Move, kick, mute, and manage users across voice channels
- **🛡️ Authorization System**: Secure command access with user authorization management
- **🔄 Rollback Functionality**: Undo move operations with a single command
- **📊 Comprehensive Logging**: Detailed command execution logs sent to Discord channels
- **🌐 Server-wide Operations**: Manage users across all voice channels simultaneously
- **🎵 Soundboard Control**: Enable/disable soundboard usage in voice channels
- **👤 User Management**: Change nicknames, ban users, and manage permissions

## 🚀 Commands

### 🎓 Mentorship Commands
- **`.mentor`** - Assigns participation role to all users in your current Stage channel and announces participants
- **`.stopmentor`** - Removes the waiting room role from users in the current channel and deletes the channel
- **`.setupwaiting`** - Automatically detects users with trigger role, creates private text channels, and assigns waiting room role

### 🔇 Voice Control Commands
- **`.muteall`** - Mutes all members in your voice channel except yourself
- **`.unmuteall`** - Unmutes all members in your voice channel except yourself
- **`.nosb`** - Disables soundboard usage for everyone in your current voice channel
- **`.dosb`** - Re-enables soundboard usage (restores defaults) in your current voice channel

### 🔄 Move Commands
- **`.moveall <CHANNEL>`** - Move ALL users in your voice channel to the specified channel (accepts ID or fuzzy name)
- **`.servermoveall <CHANNEL>`** - Move ALL users from ALL voice channels to the specified channel (accepts ID or fuzzy name)
- **`.back`** - Roll back the last move action (moveall/servermoveall)

**Examples:**
```
.moveall 123456789012345678
.moveall alobby
.servermoveall A | Lobby
.back
```

### 👢 Kick Commands
- **`.kickall`** - Kicks all users from your voice channel except yourself
- **`.serverkickall`** - Kicks ALL users from ALL voice channels in the server

### 🔨 Ban Commands
- **`.massban <USERID> <USERID> <USERID>...`** - Bans multiple users from the server by their user IDs

**Examples:**
```
.massban 123456789012345678 987654321098765432
.massban 111111111111111111 222222222222222222 333333333333333333
```

### 👤 Nickname Commands
- **`.nick <USER> <NEW_NICK>`** - Change a member's server nickname. `<USER>` can be a mention, ID, or fuzzy display/name. Use `-` or omit `<NEW_NICK>` to clear.

**Examples:**
```
.nick aion godslayer
.nick @Aion Godslayer
.nick 123456789012345678 - (clear nick)
.nick aion (clear nick)
```

### 🔐 Authorization Commands (Bot Owner Only)
- **`.auth <USER_ID>`** - Authorizes a user to use bot commands
- **`.deauth <USER_ID>`** - Removes a user's authorization

**Examples:**
```
.auth 987654321098765432
.deauth 987654321098765432
```

### ℹ️ Information Commands
- **`.help`** - Shows all available commands and their usage

## 🛠️ Setup & Deployment

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- Discord Server with appropriate permissions

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd BrainAllianceFX
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   KEEPALIVE_URL=your_keepalive_url_here
   LOG_CHANNEL_ID=your_log_channel_id_here
   ```

5. **Run the bot:**
   ```bash
   python main.py
   ```

### 🚀 Deployment on Koyeb

1. **Create a Koyeb account** at [koyeb.com](https://koyeb.com)

2. **Create a new service:**
   - Click "Create Service"
   - Choose "GitHub" as source
   - Connect your GitHub account and select this repository

3. **Configure the service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Run Command:** `python main.py`
   - **Port:** `8000` (automatically detected)

4. **Set Environment Variables:**
   In the Koyeb dashboard, go to your service settings and add:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `KEEPALIVE_URL`: Your Koyeb service URL (optional, for keepalive)
   - `LOG_CHANNEL_ID`: Discord channel ID for command logging

5. **Deploy:**
   - Click "Deploy" to start your service
   - The bot will automatically start and connect to Discord

### 🔧 Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Your Discord bot token from the Discord Developer Portal | ✅ Yes |
| `KEEPALIVE_URL` | URL for keepalive requests (optional, helps prevent sleep) | ❌ No |
| `LOG_CHANNEL_ID` | Discord channel ID where command logs will be sent | ❌ No |

### 🔑 Bot Permissions

Your Discord bot needs the following permissions:
- **Send Messages**
- **Manage Messages** (to delete command messages)
- **Manage Channels** (for channel operations)
- **Manage Roles** (for role assignments)
- **Move Members** (for voice channel operations)
- **Mute Members** (for voice control)
- **Ban Members** (for ban commands)
- **Manage Nicknames** (for nickname changes)
- **Use Slash Commands** (if using slash commands)

### 📊 Logging System

The bot includes a comprehensive logging system that sends detailed command execution logs to a specified Discord channel. Each log includes:
- 👤 User who executed the command
- ⚡ Command name and arguments
- 📋 Detailed execution results
- 🏠 Server and channel information
- 🔊 Voice channel context (if applicable)

To enable logging, set the `LOG_CHANNEL_ID` environment variable to your desired log channel ID.

## 🛡️ Security Features

- **Authorization System**: Only authorized users can execute commands
- **Bot Owner Protection**: Bot owner cannot be deauthorized or banned
- **Permission Validation**: Commands check for required Discord permissions
- **Error Handling**: Comprehensive error handling prevents crashes
- **Command Validation**: Input validation for all user-provided data

## 📝 Tips & Best Practices

- Use channel IDs for exact matches when possible
- The bot supports fuzzy matching for channel and user names
- Move commands support rollback with `.back`
- All commands provide detailed feedback and logging
- The bot automatically handles permission errors gracefully

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the Discord server for community support
- Review the command help with `.help`

---

**Made with ❤️ for the BrainAllianceFX community**