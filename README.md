# 🧠✨ BrainAllianceFX Discord Bot

<div align="center">

**A powerful, feature-rich Discord bot for voice channel management and mentorship coordination**

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?style=flat-square&logo=python)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 🌟 What Makes This Bot Special?

BrainAllianceFX is your all-in-one server companion, designed to make Discord server management smooth and effortless. Whether you're running mentorship programs, managing events, or keeping your voice channels organized, this bot has you covered!

### ✨ Key Highlights

🎓 **Smart Mentorship System** → Automate role assignments and private channel creation  
🎵 **Voice Channel Mastery** → Move, mute, and manage users with ease  
🔐 **Secure by Design** → Advanced authorization system keeps your server safe  
⏮️ **Undo Actions** → Made a mistake? Roll back with one command  
📊 **Crystal Clear Logs** → Track everything that happens in your server  
⚡ **Lightning Fast** → Optimized for performance and reliability

---

## 🎮 Command Reference

### 🎓 Mentorship & Events

<table>
<tr>
<td width="30%"><code>.mentor</code></td>
<td>Assigns participation roles to Stage channel members and announces participants</td>
</tr>
<tr>
<td><code>.stopmentor</code></td>
<td>Removes waiting room roles and cleans up channels</td>
</tr>
<tr>
<td><code>.setupwaiting</code></td>
<td>Automatically creates private channels and assigns waiting room roles</td>
</tr>
</table>

### 🔊 Voice Channel Control

<table>
<tr>
<td width="30%"><code>.muteall</code></td>
<td>Mutes everyone in your voice channel (except you!)</td>
</tr>
<tr>
<td><code>.unmuteall</code></td>
<td>Unmutes all members in your voice channel</td>
</tr>
<tr>
<td><code>.nosb</code></td>
<td>Disables soundboard for the entire channel</td>
</tr>
<tr>
<td><code>.dosb</code></td>
<td>Re-enables soundboard usage</td>
</tr>
</table>

### 🚀 Moving Users Around

<table>
<tr>
<td width="30%"><code>.moveall &lt;channel&gt;</code></td>
<td>Move all users in your channel to another channel</td>
</tr>
<tr>
<td><code>.servermoveall &lt;channel&gt;</code></td>
<td>Move <strong>everyone</strong> from <strong>all</strong> voice channels to one destination</td>
</tr>
<tr>
<td><code>.back</code></td>
<td>Undo the last move operation (lifesaver!)</td>
</tr>
</table>

**💡 Pro Tips:**
```
.moveall 123456789012345678    ← Use channel ID
.moveall alobby                 ← Or fuzzy name matching
.servermoveall A | Lobby        ← Works with special characters
.back                           ← Oops? No problem!
```

### 👢 Kick Commands

<table>
<tr>
<td width="30%"><code>.kickall</code></td>
<td>Removes all users from your voice channel</td>
</tr>
<tr>
<td><code>.serverkickall</code></td>
<td>Clears all voice channels server-wide</td>
</tr>
</table>

### 🔨 Moderation Tools

**Mass Ban**
```
.massban <userID> <userID> <userID>...

Examples:
.massban 123456789012345678 987654321098765432
.massban 111111111111111111 222222222222222222 333333333333333333
```

**Nickname Management**
```
.nick <user> <new_nickname>

Examples:
.nick aion Godslayer           ← Set a nickname
.nick @Aion Cool Person        ← Works with mentions
.nick 123456789012345678 -     ← Clear nickname
.nick aion                     ← Also clears nickname
```

### 🔐 Authorization (Bot Owner Only)

<table>
<tr>
<td width="30%"><code>.auth &lt;userID&gt;</code></td>
<td>Grant command access to a user</td>
</tr>
<tr>
<td><code>.deauth &lt;userID&gt;</code></td>
<td>Revoke command access from a user</td>
</tr>
</table>

### 🎭 Rich Presence Management

<table>
<tr>
<td width="30%"><code>.setstatus &lt;status&gt;</code></td>
<td>Change bot status (online, idle, dnd, invisible)</td>
</tr>
<tr>
<td><code>.setactivity &lt;text&gt;</code></td>
<td>Set what your bot shows as doing</td>
</tr>
<tr>
<td><code>.settype &lt;type&gt;</code></td>
<td>Set activity type (playing, listening, watching, streaming, competing)</td>
</tr>
<tr>
<td><code>.setstreaming &lt;true/false&gt;</code></td>
<td>Enable/disable streaming presence</td>
</tr>
<tr>
<td><code>.setlargeimage &lt;key&gt;</code></td>
<td>Set large image for Rich Presence</td>
</tr>
<tr>
<td><code>.setsmallimage &lt;key&gt;</code></td>
<td>Set small image for Rich Presence</td>
</tr>
<tr>
<td><code>.presenceinfo</code></td>
<td>Show current Rich Presence settings</td>
</tr>
<tr>
<td><code>.presencehelp</code></td>
<td>Show complete Rich Presence command guide</td>
</tr>
</table>

**🎨 Rich Presence Features:**
- **Complete Command Control** → Every aspect editable via commands
- **Image Support** → Large and small images with custom tooltips
- **Streaming Support** → Full streaming presence control
- **Settings Persistence** → All changes automatically saved
- **Real-time Updates** → Changes take effect immediately

**💡 Quick Examples:**
```
.setstatus online
.setactivity "with BrainAllianceFX 🧠"
.settype playing
.setlargeimage "brainalliance_logo"
.setlargetext "BrainAllianceFX Server"
```

### ℹ️ Help & Utilities

<table>
<tr>
<td width="30%"><code>.ping</code></td>
<td>Shows bot latency and responds with Pong!</td>
</tr>
<tr>
<td><code>.help</code></td>
<td>Shows all available commands and how to use them</td>
</tr>
</table>

---

## 🎭 Rich Presence System

Your bot features a **completely command-editable** Rich Presence system with full image support! Control every aspect of how your bot appears to users through simple commands.

### 🚀 Quick Start

**Basic Setup:**
```bash
.setstatus online
.setactivity "with BrainAllianceFX 🧠"
.settype playing
```

**With Images:**
```bash
.setlargeimage "brainalliance_logo"
.setlargetext "BrainAllianceFX Server"
.setsmallimage "verified_badge"
.setsmalltext "Verified Bot"
```

**Streaming Mode:**
```bash
.setstreaming true
.setstreamtitle "BrainAllianceFX Bot Live"
.setstreamurl "https://twitch.tv/yourchannel"
.settype streaming
```

### 🎯 Complete Command Reference

| Command | Description | Example |
|:--------|:------------|:--------|
| `.setstatus <status>` | Change bot status | `.setstatus online` |
| `.setactivity <text>` | Set activity text | `.setactivity "managing server"` |
| `.settype <type>` | Set activity type | `.settype playing` |
| `.setstreaming <true/false>` | Enable/disable streaming | `.setstreaming true` |
| `.setstreamtitle <title>` | Set streaming title | `.setstreamtitle "Live Now!"` |
| `.setstreamurl <url>` | Set streaming URL | `.setstreamurl "https://twitch.tv/..."` |
| `.setservercount <true/false>` | Show/hide server count | `.setservercount true` |
| `.setmembercount <true/false>` | Show/hide member count | `.setmembercount true` |
| `.setlargeimage <key>` | Set large image | `.setlargeimage "logo"` |
| `.setlargetext <text>` | Set large image text | `.setlargetext "Server Name"` |
| `.setsmallimage <key>` | Set small image | `.setsmallimage "badge"` |
| `.setsmalltext <text>` | Set small image text | `.setsmalltext "Status"` |
| `.presenceinfo` | Show current settings | `.presenceinfo` |
| `.presencehelp` | Show complete guide | `.presencehelp` |
| `.resetpresence` | Reset to defaults | `.resetpresence` |

### 🎨 Activity Types

- **playing** → "Playing [text]"
- **listening** → "Listening to [text]"
- **watching** → "Watching [text]"
- **streaming** → "Streaming [text]"
- **competing** → "Competing in [text]"

### 📊 Status Options

- **online** → Green dot
- **idle** → Yellow dot
- **dnd** → Red dot (Do Not Disturb)
- **invisible** → Gray dot

### 🖼️ Image Support

- **Large Image** → Main image displayed in Rich Presence
- **Large Text** → Tooltip when hovering over large image
- **Small Image** → Small image next to the large image
- **Small Text** → Tooltip when hovering over small image

### 💡 Theme Examples

**Gaming Theme:**
```bash
.setstatus online
.setactivity "in the server arena 🏟️"
.settype competing
.setlargeimage "gaming_logo"
.setlargetext "BrainAllianceFX Gaming"
```

**Professional Theme:**
```bash
.setstatus dnd
.setactivity "managing server infrastructure 🏢"
.settype watching
.setlargeimage "company_logo"
.setlargetext "BrainAllianceFX Management"
```

**Streaming Theme:**
```bash
.setstatus online
.setstreaming true
.setstreamtitle "BrainAllianceFX Bot Live"
.setstreamurl "https://twitch.tv/yourchannel"
.setlargeimage "stream_logo"
.setlargetext "Live Now!"
```

### 🔄 How It Works

- **Settings Persistence** → All changes automatically saved to `rich_presence_settings.json`
- **Real-time Updates** → Changes take effect immediately, no restart needed
- **Command Control** → Every aspect controllable via commands
- **Image Support** → Full Discord Rich Presence image support
- **Streaming Support** → Complete streaming presence control

For the complete guide with troubleshooting and advanced tips, see [RICH_PRESENCE_GUIDE.md](RICH_PRESENCE_GUIDE.md).

---

## 🚀 Getting Started

### 📋 What You'll Need

- Python 3.8 or newer
- A Discord bot token
- A Discord server with proper permissions

### 💻 Local Development

**1. Clone and enter the project**
```bash
git clone <repository-url>
cd BrainAllianceFX
```

**2. Set up your environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure your bot**

Create a `.env` file:
```env
DISCORD_TOKEN=your_bot_token_here
KEEPALIVE_URL=your_keepalive_url_here
LOG_CHANNEL_ID=your_log_channel_id_here
```

**4. Launch!**
```bash
python main.py
```

### ☁️ Deploy to Koyeb

**Step 1:** Create a free account at [koyeb.com](https://koyeb.com)

**Step 2:** Create a new service
- Select GitHub as your source
- Connect your repository

**Step 3:** Configure deployment
```yaml
Build Command: pip install -r requirements.txt
Run Command: python main.py
Port: 8000
```

**Step 4:** Add environment variables
- `DISCORD_TOKEN` → Your bot token (required)
- `KEEPALIVE_URL` → Your service URL (optional)
- `LOG_CHANNEL_ID` → Log channel ID (optional)

**Step 5:** Hit deploy and watch the magic happen! ✨

---

## 🔧 Configuration

### Environment Variables

| Variable | Purpose | Required |
|:---------|:--------|:--------:|
| `DISCORD_TOKEN` | Your Discord bot token | ✅ |
| `KEEPALIVE_URL` | Keeps your bot awake (helpful for free hosting) | ❌ |
| `LOG_CHANNEL_ID` | Where command logs are sent | ❌ |

### Required Bot Permissions

Make sure your bot has these permissions enabled:

✅ Send Messages  
✅ Manage Messages  
✅ Manage Channels  
✅ Manage Roles  
✅ Move Members  
✅ Mute Members  
✅ Ban Members  
✅ Manage Nicknames  
✅ Use Slash Commands

---

## 📊 Logging System

Every action is tracked with beautiful, detailed logs that include:

- 👤 Who ran the command
- ⚡ What command was executed
- 📋 Complete execution details
- 🏠 Server and channel context
- 🔊 Voice channel information

Just set your `LOG_CHANNEL_ID` and you're all set!

---

## 🛡️ Security First

Your server's safety is our priority:

- 🔒 **Authorization System** → Only approved users can run commands
- 👑 **Owner Protection** → Bot owner always has access
- ✅ **Permission Checks** → Validates Discord permissions before acting
- 🛠️ **Error Handling** → Graceful error recovery prevents crashes
- 🔍 **Input Validation** → All user input is thoroughly validated

---

## 💡 Pro Tips

- Use channel IDs for exact matches when moving users
- Fuzzy matching works great for channel and user names
- The `.back` command is your best friend for move operations
- Check logs regularly to monitor bot activity
- Commands provide instant feedback so you always know what's happening

---

## 🤝 Contributing

We love contributions! Here's how to get involved:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ✨ Make your awesome changes
4. 🧪 Test everything thoroughly
5. 📮 Submit a pull request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 💬 Need Help?

We're here for you!

- 🐛 Found a bug? [Create an issue](https://github.com/your-repo/issues)
- 💭 Have questions? Join our Discord community
- 📖 Check the built-in help with `.help`

---

<div align="center">

**Built with 💜 for the BrainAllianceFX community**

⭐ Star this repo if you find it helpful!

</div>