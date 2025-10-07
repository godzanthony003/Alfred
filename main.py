import discord
from discord.ext import commands
import os
import json
import aiofiles
from dotenv import load_dotenv
import time
from urllib.request import urlopen, Request
import re
import difflib
import asyncio

# Import messages from separate file
from messages import (
    get_error_message, 
    get_success_message, 
    get_status_message, 
    HELP_EMBED
)

# Import Rich Presence system
from rich_presence import set_presence, set_custom_activity, reset_presence, presence_manager

# --- Minimal web server for Koyeb health check ---
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web():
    try:
        port = int(os.getenv("PORT", "8000"))
    except Exception:
        port = 8000
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Start the web server in the background
threading.Thread(target=run_web, daemon=True).start()

def self_ping():
    while True:
        try:
            port = os.getenv("PORT", "8000")
            urlopen(f"http://127.0.0.1:{port}/", timeout=5).read()
        except Exception:
            pass
        time.sleep(240)

threading.Thread(target=self_ping, daemon=True).start()

def external_keepalive():
    urls = [
        "https://www.google.com/generate_204",
        "https://cloudflare.com/cdn-cgi/trace"
    ]
    # Optionally include your own public URL so the platform router sees inbound traffic
    keepalive_url = os.getenv("KEEPALIVE_URL")
    if keepalive_url:
        urls.insert(0, keepalive_url.rstrip("/"))
    while True:
        for u in urls:
            try:
                urlopen(Request(u, headers={"User-Agent": "KeepAlive/1.0"}), timeout=10).read()
            except Exception:
                pass
        time.sleep(240)

threading.Thread(target=external_keepalive, daemon=True).start()

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')

# Constants for Waiting Setup workflow
TRIGGER_ROLE_ID = 1424547689772613895
CATEGORY_ID = 1424710355271290950
WAITING_ROLE_ID = 1424710209829605478

# Define bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# Initialize bot with prefix '.' and intents
bot = commands.Bot(command_prefix='.', intents=intents)

# File to store authorized users
AUTH_FILE = 'authorized_users.json'

# Global variable to store the last move action for rollback
last_move_action = None

# --- Global hook: delete the issuer's command message before executing any command ---
@bot.before_invoke
async def _delete_invocation(ctx):
    try:
        if ctx and ctx.message:
            await ctx.message.delete()
    except (discord.Forbidden, discord.HTTPException):
        # If we cannot delete, ignore silently
        pass

# --- Global hook: update Rich Presence when commands are executed ---
# Removed automatic command activity updates - Rich Presence shows only what you set

# --- Console logging helper ---
def log_command(author, command_name, details):
    try:
        author_name = getattr(author, 'name', str(author))
        print(f"! {author_name} triggered .{command_name} | {details}")
    except Exception:
        # Fallback to avoid crashing on logging
        try:
            print(f"! [unknown] triggered .{command_name} | {details}")
        except Exception:
            pass

# --- Discord logging helper ---
async def log_to_discord(bot, author, command_name, args=None, details=None):
    """Send command execution log to Discord log channel"""
    if not LOG_CHANNEL_ID:
        return  # Skip if no log channel configured
    
    try:
        log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
        if not log_channel:
            return  # Skip if channel not found
        
        # Create embed for logging
        embed = discord.Embed(
            title="🤖 Command Executed",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        # Add user information
        embed.add_field(
            name="👤 User",
            value=f"{author.mention} ({author.name}#{author.discriminator})\nID: {author.id}",
            inline=True
        )
        
        # Add command information
        embed.add_field(
            name="⚡ Command",
            value=f"`.{command_name}`",
            inline=True
        )
        
        # Add arguments if provided
        if args is not None:
            args_str = " ".join(str(arg) for arg in args) if isinstance(args, (list, tuple)) else str(args)
            embed.add_field(
                name="📝 Arguments",
                value=f"`{args_str}`" if args_str else "None",
                inline=False
            )
        
        # Add additional details if provided
        if details:
            embed.add_field(
                name="📋 Details",
                value=details[:1024],  # Discord field limit
                inline=False
            )
        
        # Add server information
        if hasattr(author, 'guild') and author.guild:
            embed.add_field(
                name="🏠 Server",
                value=f"{author.guild.name} ({author.guild.id})",
                inline=True
            )
        
        # Add channel information
        if hasattr(author, 'voice') and author.voice and author.voice.channel:
            embed.add_field(
                name="🔊 Voice Channel",
                value=f"{author.voice.channel.name} ({author.voice.channel.id})",
                inline=True
            )
        
        await log_channel.send(embed=embed)
        
    except Exception as e:
        # Don't crash the bot if logging fails
        print(f"Failed to log to Discord: {e}")
        pass

# --- Voice channel resolution helper ---
def _normalize_channel_name(name: str):
    try:
        # Lowercase and strip non-alphanumeric for loose matching
        return re.sub(r"[^a-z0-9]", "", name.lower())
    except Exception:
        return name.lower()

def resolve_voice_channel_by_query(guild: discord.Guild, query: str):
    """Resolve a voice channel by ID or fuzzy name within the given guild.

    Returns a discord.VoiceChannel or raises ValueError if not found/invalid.
    """
    if not query:
        raise ValueError("empty_query")

    # Try numeric ID first
    try:
        channel_id = int(query)
        channel = guild.get_channel(channel_id)
        if isinstance(channel, discord.VoiceChannel):
            return channel
    except Exception:
        pass

    # Fuzzy match by name among voice channels
    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    if not voice_channels:
        raise ValueError("no_voice_channels")

    normalized_query = _normalize_channel_name(query)

    # Calculate scores: exact (case-insensitive), startswith, contains, normalized contains, sequence ratio
    best_channel = None
    best_score = 0.0
    for ch in voice_channels:
        name = ch.name
        name_lower = name.lower()
        norm_name = _normalize_channel_name(name)

        score = 0.0
        if name_lower == query.lower():
            score = 1.0
        elif name_lower.startswith(query.lower()):
            score = 0.95
        elif query.lower() in name_lower:
            score = 0.9
        elif normalized_query and normalized_query in norm_name:
            score = 0.85
        else:
            try:
                score = difflib.SequenceMatcher(a=normalized_query, b=norm_name).ratio() * 0.8
            except Exception:
                score = 0.0

        # Slight tie-breaker: prefer channels with more members when scores close
        if score > best_score or (abs(score - best_score) < 0.02 and best_channel and len(ch.members) > len(best_channel.members)):
            best_score = score
            best_channel = ch

    # Require a minimal threshold to avoid wild mismatches
    if best_channel and best_score >= 0.6:
        return best_channel

    raise ValueError("not_found")

# --- Member resolution helper ---
def _extract_id_from_mention(query: str):
    try:
        match = re.match(r"^<@!?(\d+)>$", query.strip())
        if match:
            return int(match.group(1))
    except Exception:
        return None
    return None

def resolve_member_by_query(guild: discord.Guild, query: str):
    """Resolve a member by mention, ID or fuzzy display/name within the given guild.

    Returns a discord.Member or raises ValueError if not found/invalid.
    """
    if not query:
        raise ValueError("empty_query")

    # Try mention format
    mention_id = _extract_id_from_mention(query)
    if mention_id is not None:
        member = guild.get_member(mention_id)
        if isinstance(member, discord.Member):
            return member

    # Try numeric ID
    try:
        member_id = int(query)
        member = guild.get_member(member_id)
        if isinstance(member, discord.Member):
            return member
    except Exception:
        pass

    # Fuzzy match among members by display name and username
    members = list(guild.members)
    if not members:
        raise ValueError("no_members")

    normalized_query = _normalize_channel_name(query)

    best_member = None
    best_score = 0.0

    for m in members:
        names_to_check = [getattr(m, "display_name", ""), getattr(m, "name", ""), getattr(m, "nick", "") or ""]
        score_for_member = 0.0
        for name in names_to_check:
            if not name:
                continue
            name_lower = name.lower()
            norm_name = _normalize_channel_name(name)

            score = 0.0
            if name_lower == query.lower():
                score = 1.0
            elif name_lower.startswith(query.lower()):
                score = 0.95
            elif query.lower() in name_lower:
                score = 0.9
            elif normalized_query and normalized_query in norm_name:
                score = 0.85
            else:
                try:
                    score = difflib.SequenceMatcher(a=normalized_query, b=norm_name).ratio() * 0.8
                except Exception:
                    score = 0.0

            score_for_member = max(score_for_member, score)

        # Slight tie-breaker: prefer members currently in voice or with roles when close
        if score_for_member > best_score or (
            abs(score_for_member - best_score) < 0.02 and best_member and len(m.roles) > len(best_member.roles)
        ):
            best_score = score_for_member
            best_member = m

    if best_member and best_score >= 0.6:
        return best_member

    raise ValueError("not_found")

# Load authorized users from JSON file or use default
async def load_authorized_users():
    try:
        async with aiofiles.open(AUTH_FILE, 'r') as f:
            data = json.loads(await f.read())
            return data
    except FileNotFoundError:
        return {
            '539464122027343873': 'StaffBotOwner'  # Default: your user ID
        }
    except json.JSONDecodeError:
        print(get_status_message("json_error"))
        return {
            '539464122027343873': 'StaffBotOwner'
        }

# Save authorized users to JSON file
async def save_authorized_users(authorized_users):
    async with aiofiles.open(AUTH_FILE, 'w') as f:
        await f.write(json.dumps(authorized_users, indent=4))

# Global check for all commands except .auth and .deauth
@bot.check
async def check_authorized_user(ctx):
    if ctx.command.name in ['auth', 'deauth']:  # Skip check for .auth and .deauth
        return True
    authorized_users = await load_authorized_users()
    if str(ctx.author.id) not in authorized_users:
        await ctx.send(get_error_message("not_authorized"))
        return False
    return True

# Event: Bot is ready
@bot.event
async def on_ready():
    print(get_status_message("bot_ready", bot_name=bot.user))
    
    # Set Rich Presence
    await set_presence(bot)
    print("🎭 Rich Presence set!")
    
    # Automatic startup scan: ensure setup for all members across guilds
    try:
        for guild in bot.guilds:
            trigger_role = guild.get_role(TRIGGER_ROLE_ID)
            waiting_role = guild.get_role(WAITING_ROLE_ID)
            category = guild.get_channel(CATEGORY_ID)
            if not trigger_role or not waiting_role or not isinstance(category, discord.CategoryChannel):
                continue
            for member in guild.members:
                if getattr(member, 'bot', False):
                    continue
                if trigger_role in getattr(member, 'roles', []):
                    try:
                        await ensure_waiting_setup_for_member(guild, member, trigger_role, waiting_role, category)
                    except Exception:
                        # Avoid crashing on startup; continue best-effort
                        pass
    except Exception:
        # Silent guard to ensure bot stays ready even if scan fails
        pass

async def ensure_waiting_setup_for_member(guild: discord.Guild, member: discord.Member, trigger_role: discord.Role, waiting_role: discord.Role, category: discord.CategoryChannel):
    """Ensure the member with trigger_role has a private text channel under category and has waiting_role.

    Idempotent: re-assigns missing role, creates channel if absent.
    Returns (channel_created: bool, role_assigned: bool).
    """
    channel_created = False
    role_assigned = False

    # Ensure waiting role
    if waiting_role not in getattr(member, 'roles', []):
        await member.add_roles(waiting_role, reason=f"Automatic waiting setup")
        role_assigned = True

    # Ensure private channel
    desired_name = member.name.lower()
    existing = discord.utils.get(category.text_channels, name=desired_name)
    if existing is None:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }
        channel = await guild.create_text_channel(
            name=desired_name,
            category=category,
            overwrites=overwrites,
            reason=f"Private waiting channel for {member} ({member.id})"
        )
        channel_created = True
        # Send welcome message to the newly created channel
        try:
            welcome_message = (
                f"👋 Ciao {member.mention},\n"
                f"questo è il tuo canale privato! ✨\n\n"
                f"📌 Prima dell’orario della tua mentorship, ricordati di entrare nella Sala d’Attesa: lì attenderai qualche minuto finché Anthony (il nostro trader) o un membro dello staff ti sposteranno nel canale vocale per la sessione privata.\n\n"
                f"Qui potrai anche comunicare direttamente con Anthony e, se necessario, con altri membri dello staff. 🚀"
            )
            await channel.send(welcome_message)
        except Exception:
            # Do not block setup if message fails
            pass

    # Try to remove the trigger role after setup completes
    try:
        if trigger_role in getattr(member, 'roles', []):
            await member.remove_roles(trigger_role, reason="Automatic waiting setup completed")
    except discord.Forbidden:
        # Missing permissions or role hierarchy; skip silently
        pass
    except discord.HTTPException:
        # Transient API error; skip silently
        pass

    return channel_created, role_assigned

# Prefix command: .muteall
@bot.command(name="muteall", description="Mutes all members in the user's voice channel except themselves")
async def muteall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        log_command(ctx.author, 'muteall', 'failed | Reason: caller not in a voice channel')
        await ctx.send(get_error_message("not_in_voice"))
        return

    voice_channel = ctx.author.voice.channel
    members_muted = 0
    muted_names = []

    for member in voice_channel.members:
        if member != ctx.author:
            try:
                await member.edit(mute=True)
                members_muted += 1
                muted_names.append(member.name)
            except discord.Forbidden:
                log_command(ctx.author, 'muteall', f"failed | Missing permissions to mute {member.name}")
                await ctx.send(get_error_message("missing_permissions", action="mute", member_name=member.name))
                return
            except discord.HTTPException as e:
                log_command(ctx.author, 'muteall', f"failed | HTTP error while muting {member.name}: {e}")
                await ctx.send(get_error_message("http_error", action="muting", member_name=member.name, error=e))
                return

    await ctx.send(get_success_message("muted_users", count=members_muted, channel_name=voice_channel.name))
    details = f"Members muted: {members_muted} | " + (", ".join(muted_names) if muted_names else "none") + f" | Channel: {voice_channel.name}"
    log_command(ctx.author, 'muteall', details)
    await log_to_discord(bot, ctx.author, 'muteall', details=details)

# Prefix command: .unmuteall
@bot.command(name="unmuteall", description="Unmutes all members in the user's voice channel except themselves")
async def unmuteall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        log_command(ctx.author, 'unmuteall', 'failed | Reason: caller not in a voice channel')
        await ctx.send(get_error_message("not_in_voice"))
        return

    voice_channel = ctx.author.voice.channel
    members_unmuted = 0
    unmuted_names = []

    for member in voice_channel.members:
        if member != ctx.author:
            try:
                await member.edit(mute=False)
                members_unmuted += 1
                unmuted_names.append(member.name)
            except discord.Forbidden:
                log_command(ctx.author, 'unmuteall', f"failed | Missing permissions to unmute {member.name}")
                await ctx.send(get_error_message("missing_permissions", action="unmute", member_name=member.name))
                return
            except discord.HTTPException as e:
                log_command(ctx.author, 'unmuteall', f"failed | HTTP error while unmuting {member.name}: {e}")
                await ctx.send(get_error_message("http_error", action="unmuting", member_name=member.name, error=e))
                return

    await ctx.send(get_success_message("unmuted_users", count=members_unmuted, channel_name=voice_channel.name))
    details = f"Members unmuted: {members_unmuted} | " + (", ".join(unmuted_names) if unmuted_names else "none") + f" | Channel: {voice_channel.name}"
    log_command(ctx.author, 'unmuteall', details)
    await log_to_discord(bot, ctx.author, 'unmuteall', details=details)

# Prefix command: .nosb (disable soundboard in the issuer's current voice channel)
@bot.command(name="nosb", description="Disables soundboard for everyone in your current voice channel")
async def nosb(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        log_command(ctx.author, 'nosb', 'failed | Reason: caller not in a voice channel')
        await ctx.send(get_error_message("not_in_voice"))
        return

    channel = ctx.author.voice.channel
    everyone_role = ctx.guild.default_role

    try:
        overwrite = channel.overwrites_for(everyone_role)
        overwrite.use_soundboard = False
        await channel.set_permissions(everyone_role, overwrite=overwrite)
        await ctx.send(get_success_message("soundboard_disabled_channel", channel_name=channel.name, channel_id=channel.id))
        log_command(ctx.author, 'nosb', f"success | Soundboard disabled in #{channel.name} ({channel.id})")
        await log_to_discord(bot, ctx.author, 'nosb', details=f"Soundboard disabled in #{channel.name} ({channel.id})")
    except discord.Forbidden:
        log_command(ctx.author, 'nosb', 'failed | Missing permissions to update @everyone')
        await ctx.send(get_error_message("missing_permissions", action="update permissions for", member_name="@everyone"))
    except discord.HTTPException as e:
        log_command(ctx.author, 'nosb', f"failed | HTTP error while updating permissions: {e}")
        await ctx.send(get_error_message("http_error", action="updating permissions for", member_name="@everyone", error=e))

# Prefix command: .dosb (enable/restores soundboard in the issuer's current voice channel)
@bot.command(name="dosb", description="Re-enables soundboard (restore defaults) in your current voice channel")
async def dosb(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        log_command(ctx.author, 'dosb', 'failed | Reason: caller not in a voice channel')
        await ctx.send(get_error_message("not_in_voice"))
        return

    channel = ctx.author.voice.channel
    everyone_role = ctx.guild.default_role

    try:
        overwrite = channel.overwrites_for(everyone_role)
        # Set to None to clear explicit deny/allow and restore server default
        overwrite.use_soundboard = None
        await channel.set_permissions(everyone_role, overwrite=overwrite)
        await ctx.send(get_success_message("soundboard_enabled_channel", channel_name=channel.name, channel_id=channel.id))
        log_command(ctx.author, 'dosb', f"success | Soundboard restored in #{channel.name} ({channel.id})")
        await log_to_discord(bot, ctx.author, 'dosb', details=f"Soundboard restored in #{channel.name} ({channel.id})")
    except discord.Forbidden:
        log_command(ctx.author, 'dosb', 'failed | Missing permissions to update @everyone')
        await ctx.send(get_error_message("missing_permissions", action="update permissions for", member_name="@everyone"))
    except discord.HTTPException as e:
        log_command(ctx.author, 'dosb', f"failed | HTTP error while updating permissions: {e}")
        await ctx.send(get_error_message("http_error", action="updating permissions for", member_name="@everyone", error=e))

# Prefix command: .auth USERID
@bot.command(name="auth", description="Authorizes a user to use bot commands (restricted to bot owner)")
async def auth(ctx, user_id: str):
    # Restrict to your user ID
    if ctx.author.id != 539464122027343873:
        log_command(ctx.author, 'auth', 'failed | Reason: not bot owner')
        await ctx.send(get_error_message("bot_owner_only"))
        return

    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        log_command(ctx.author, 'auth', 'failed | Reason: invalid user id')
        await ctx.send(get_error_message("invalid_user_id"))
        return

    # Fetch the user to get their username
    try:
        user = await bot.fetch_user(user_id)
        username = user.name
    except discord.NotFound:
        log_command(ctx.author, 'auth', f"failed | User not found: {user_id}")
        await ctx.send(get_error_message("user_not_found_global", user_id=user_id))
        return
    except discord.HTTPException as e:
        log_command(ctx.author, 'auth', f"failed | HTTP error while fetching user {user_id}: {e}")
        await ctx.send(get_error_message("fetch_error", type="user", error=e))
        return

    # Load current authorized users
    authorized_users = await load_authorized_users()

    # Check if user is already authorized
    if str(user_id) in authorized_users:
        log_command(ctx.author, 'auth', f"failed | User already authorized: {username} ({user_id})")
        await ctx.send(get_error_message("user_already_authorized", username=username, user_id=user_id))
        return

    # Add user to authorized list
    authorized_users[str(user_id)] = username
    await save_authorized_users(authorized_users)
    await ctx.send(get_success_message("user_authorized", username=username, user_id=user_id))
    log_command(ctx.author, 'auth', f"success | Authorized {username} ({user_id})")
    await log_to_discord(bot, ctx.author, 'auth', args=[user_id], details=f"Authorized {username} ({user_id})")

# Prefix command: .deauth USERID
@bot.command(name="deauth", description="Removes a user's authorization to use bot commands (restricted to bot owner)")
async def deauth(ctx, user_id: str):
    # Restrict to your user ID
    if ctx.author.id != 539464122027343873:
        log_command(ctx.author, 'deauth', 'failed | Reason: not bot owner')
        await ctx.send(get_error_message("bot_owner_only"))
        return

    # Prevent deauthorizing the bot owner
    if user_id == '539464122027343873':
        log_command(ctx.author, 'deauth', 'failed | Reason: cannot deauth owner')
        await ctx.send(get_error_message("cannot_deauth_owner"))
        return

    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        log_command(ctx.author, 'deauth', 'failed | Reason: invalid user id')
        await ctx.send(get_error_message("invalid_user_id"))
        return

    # Load current authorized users
    authorized_users = await load_authorized_users()

    # Check if user is authorized
    if str(user_id) not in authorized_users:
        log_command(ctx.author, 'deauth', f"failed | User not authorized: {user_id}")
        await ctx.send(get_error_message("user_not_authorized", user_id=user_id))
        return

    # Fetch the user to confirm their username
    try:
        user = await bot.fetch_user(user_id)
        username = user.name
    except discord.NotFound:
        username = authorized_users.get(str(user_id), "Unknown User")
    except discord.HTTPException as e:
        log_command(ctx.author, 'deauth', f"failed | HTTP error while fetching user {user_id}: {e}")
        await ctx.send(get_error_message("fetch_error", type="user", error=e))
        return

    # Remove user from authorized list
    del authorized_users[str(user_id)]
    await save_authorized_users(authorized_users)
    await ctx.send(get_success_message("user_deauthorized", username=username, user_id=user_id))
    log_command(ctx.author, 'deauth', f"success | Deauthorized {username} ({user_id})")
    await log_to_discord(bot, ctx.author, 'deauth', args=[user_id], details=f"Deauthorized {username} ({user_id})")

# Prefix command: .moveall CHANNELID (UPDATED WITH ROLLBACK SUPPORT)
@bot.command(name="moveall", description="Moves all members from the user's voice channel to the specified channel")
async def moveall(ctx, channel: str):
    global last_move_action
    
    if not ctx.author.voice or not ctx.author.voice.channel:
        log_command(ctx.author, 'moveall', 'failed | Reason: caller not in a voice channel')
        await ctx.send(get_error_message("not_in_voice"))
        return

    # Resolve destination channel by ID or fuzzy name
    try:
        destination_channel = resolve_voice_channel_by_query(ctx.guild, channel)
        if not isinstance(destination_channel, discord.VoiceChannel):
            log_command(ctx.author, 'moveall', 'failed | Reason: destination is not a voice channel')
            await ctx.send(get_error_message("not_voice_channel"))
            return
    except ValueError as ve:
        if str(ve) == "no_voice_channels":
            await ctx.send(get_error_message("no_voice_channels"))
        else:
            await ctx.send(get_error_message("channel_not_found_query", query=channel))
        log_command(ctx.author, 'moveall', f"failed | Channel not found from query: {channel}")
        return
    except discord.HTTPException as e:
        log_command(ctx.author, 'moveall', f"failed | HTTP error while resolving channel '{channel}': {e}")
        await ctx.send(get_error_message("fetch_error", type="channel", error=e))
        return

    source_channel = ctx.author.voice.channel
    members_moved = 0
    
    # Store user positions before moving for rollback
    user_positions = {}
    moved_names = []

    # Move all members including the command issuer
    for member in list(source_channel.members):  # Use list() to avoid iteration issues
        # Store original position for rollback
        user_positions[member.id] = source_channel.id
        
        try:
            await member.move_to(destination_channel)
            members_moved += 1
            moved_names.append(member.name)
        except discord.Forbidden:
            log_command(ctx.author, 'moveall', f"failed | Missing permissions to move {member.name}")
            await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
            return
        except discord.HTTPException as e:
            log_command(ctx.author, 'moveall', f"failed | HTTP error while moving {member.name}: {e}")
            await ctx.send(get_error_message("http_error", action="moving", member_name=member.name, error=e))
            return

    # Store the move action for potential rollback
    last_move_action = {
        'type': 'moveall',
        'user_positions': user_positions,
        'destination_channel_id': destination_channel.id,
        'guild_id': ctx.guild.id
    }

    await ctx.send(get_success_message("moved_users_channel", 
                                     count=members_moved, 
                                     source_name=source_channel.name, 
                                     source_id=source_channel.id,
                                     dest_name=destination_channel.name, 
                                     dest_id=destination_channel.id))
    details = (
        f"Members moved: {members_moved} | " + (", ".join(moved_names) if moved_names else "none") +
        f" | From: {source_channel.name} ({source_channel.id}) -> To: {destination_channel.name} ({destination_channel.id})"
    )
    log_command(ctx.author, 'moveall', details)
    await log_to_discord(bot, ctx.author, 'moveall', args=[channel], details=details)

# Prefix command: .servermoveall CHANNELID (NEW)
@bot.command(name="servermoveall", description="Moves all users from all voice channels in the server to the specified channel")
async def servermoveall(ctx, channel: str):
    global last_move_action
    
    # Resolve destination channel by ID or fuzzy name
    try:
        destination_channel = resolve_voice_channel_by_query(ctx.guild, channel)
        if not isinstance(destination_channel, discord.VoiceChannel):
            log_command(ctx.author, 'servermoveall', 'failed | Reason: destination is not a voice channel')
            await ctx.send(get_error_message("not_voice_channel"))
            return
    except ValueError as ve:
        if str(ve) == "no_voice_channels":
            await ctx.send(get_error_message("no_voice_channels"))
        else:
            await ctx.send(get_error_message("channel_not_found_query", query=channel))
        log_command(ctx.author, 'servermoveall', f"failed | Channel not found from query: {channel}")
        return
    except discord.HTTPException as e:
        log_command(ctx.author, 'servermoveall', f"failed | HTTP error while resolving channel '{channel}': {e}")
        await ctx.send(get_error_message("fetch_error", type="channel", error=e))
        return

    # Get all voice channels in the server
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    
    if not voice_channels:
        await ctx.send(get_error_message("no_voice_channels"))
        return

    # Store user positions before moving for rollback
    user_positions = {}
    members_moved = 0
    channels_affected = 0
    moved_names = []

    # Move all members from all voice channels to destination
    for channel in voice_channels:
        if channel.id == destination_channel.id:  # Skip if it's the destination channel
            continue
            
        if len(channel.members) > 0:
            channels_affected += 1
            for member in list(channel.members):  # Use list() to avoid iteration issues
                # Store original position for rollback
                user_positions[member.id] = channel.id
                
                try:
                    await member.move_to(destination_channel)
                    members_moved += 1
                    moved_names.append(member.name)
                except discord.Forbidden:
                    log_command(ctx.author, 'servermoveall', f"failed | Missing permissions to move {member.name}")
                    await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
                    return
                except discord.HTTPException as e:
                    log_command(ctx.author, 'servermoveall', f"failed | HTTP error while moving {member.name}: {e}")
                    await ctx.send(get_error_message("http_error", action="moving", member_name=member.name, error=e))
                    return

    # Store the move action for potential rollback
    last_move_action = {
        'type': 'servermoveall',
        'user_positions': user_positions,
        'destination_channel_id': destination_channel.id,
        'guild_id': ctx.guild.id
    }

    await ctx.send(get_success_message("moved_users_server",
                                     count=members_moved,
                                     channels_count=channels_affected,
                                     dest_name=destination_channel.name,
                                     dest_id=destination_channel.id))
    details = (
        f"Members moved: {members_moved} | " + (", ".join(moved_names) if moved_names else "none") +
        f" | To: {destination_channel.name} ({destination_channel.id}) | Channels affected: {channels_affected}"
    )
    log_command(ctx.author, 'servermoveall', details)
    await log_to_discord(bot, ctx.author, 'servermoveall', args=[channel], details=details)

# Prefix command: .back (NEW - ROLLBACK SYSTEM)
@bot.command(name="back", description="Rollbacks the last move action, returning users to their original channels")
async def back(ctx):
    global last_move_action
    
    if not last_move_action:
        log_command(ctx.author, 'back', 'failed | Reason: no rollback data')
        await ctx.send(get_error_message("no_rollback_data"))
        return
    
    # Check if the rollback is for the same guild
    if last_move_action['guild_id'] != ctx.guild.id:
        log_command(ctx.author, 'back', 'failed | Reason: rollback from different server')
        await ctx.send(get_error_message("rollback_different_server"))
        return
    
    user_positions = last_move_action['user_positions']
    members_moved_back = 0
    channels_affected = 0
    channels_moved_to = set()
    
    # Get the destination channel from the last action
    try:
        previous_destination = bot.get_channel(last_move_action['destination_channel_id'])
        if not previous_destination:
            previous_destination = await bot.fetch_channel(last_move_action['destination_channel_id'])
    except (discord.NotFound, discord.HTTPException):
        log_command(ctx.author, 'back', 'failed | Reason: previous destination channel not found')
        await ctx.send(get_error_message("rollback_channel_not_found"))
        return
    
    # Move users back to their original channels
    for user_id, original_channel_id in user_positions.items():
        try:
            # Get the member
            member = ctx.guild.get_member(user_id)
            if not member:
                log_command(ctx.author, 'back', f"skip | Member not in guild anymore: {user_id}")
                continue  # Skip if member is no longer in the guild
            
            # Check if member is still in the destination channel
            if not member.voice:
                log_command(ctx.author, 'back', f"skip | Member disconnected: {member.name} ({member.id})")
                continue  # Skip if member disconnected
            if member.voice.channel.id != previous_destination.id:
                log_command(ctx.author, 'back', f"skip | Member not in destination: {member.name} ({member.id})")
                continue  # Skip if member is no longer in the destination channel
            
            # Get the original channel
            original_channel = bot.get_channel(original_channel_id)
            if not original_channel:
                original_channel = await bot.fetch_channel(original_channel_id)
            
            if not isinstance(original_channel, discord.VoiceChannel):
                continue  # Skip if original channel is no longer a voice channel
            
            # Move member back to original channel
            await member.move_to(original_channel)
            members_moved_back += 1
            channels_moved_to.add(original_channel.id)
            
        except discord.Forbidden:
            log_command(ctx.author, 'back', f"failed | Missing permissions to move {member.name}")
            await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
            return
        except discord.HTTPException as e:
            log_command(ctx.author, 'back', f"failed | HTTP error while moving {member.name}: {e}")
            await ctx.send(get_error_message("http_error", action="moving", member_name=member.name, error=e))
            return
        except (discord.NotFound, AttributeError):
            log_command(ctx.author, 'back', f"skip | Channel or member not found for user {user_id}")
            continue  # Skip if channel or member not found
    
    channels_affected = len(channels_moved_to)
    
    # Clear the last move action since we've used it
    last_move_action = None
    
    await ctx.send(get_success_message("rollback_success", count=members_moved_back, channels_count=channels_affected))
    log_command(ctx.author, 'back', f"success | Members moved back: {members_moved_back} | Channels affected: {channels_affected}")
    await log_to_discord(bot, ctx.author, 'back', details=f"Members moved back: {members_moved_back} | Channels affected: {channels_affected}")

# Prefix command: .kickall
@bot.command(name="kickall", description="Kicks all members from the user's voice channel except themselves")
async def kickall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        log_command(ctx.author, 'kickall', 'failed | Reason: caller not in a voice channel')
        await ctx.send(get_error_message("not_in_voice"))
        return

    voice_channel = ctx.author.voice.channel
    members_kicked = 0
    kicked_names = []

    # Kick all members except the command issuer
    for member in list(voice_channel.members):  # Use list() to avoid iteration issues
        if member != ctx.author:
            try:
                await member.move_to(None)  # None disconnects them
                members_kicked += 1
                kicked_names.append(member.name)
            except discord.Forbidden:
                log_command(ctx.author, 'kickall', f"failed | Missing permissions to kick {member.name}")
                await ctx.send(get_error_message("missing_permissions", action="kick", member_name=member.name))
                return
            except discord.HTTPException as e:
                log_command(ctx.author, 'kickall', f"failed | HTTP error while kicking {member.name}: {e}")
                await ctx.send(get_error_message("http_error", action="kicking", member_name=member.name, error=e))
                return

    await ctx.send(get_success_message("kicked_users_channel",
                                     count=members_kicked,
                                     channel_name=voice_channel.name,
                                     channel_id=voice_channel.id))
    details = f"Members kicked: {members_kicked} | " + (", ".join(kicked_names) if kicked_names else "none") + f" | Channel: {voice_channel.name} ({voice_channel.id})"
    log_command(ctx.author, 'kickall', details)
    await log_to_discord(bot, ctx.author, 'kickall', details=details)

# Prefix command: .serverkickall
@bot.command(name="serverkickall", description="Kicks all members from all voice channels in the server")
async def serverkickall(ctx):
    members_kicked = 0
    channels_affected = 0
    kicked_names = []
    
    # Get all voice channels in the server
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    
    if not voice_channels:
        log_command(ctx.author, 'serverkickall', 'failed | Reason: no voice channels')
        await ctx.send(get_error_message("no_voice_channels"))
        return

    # Kick all members from all voice channels
    for channel in voice_channels:
        channel_members = len(channel.members)
        if channel_members > 0:
            channels_affected += 1
            for member in list(channel.members):  # Use list() to avoid iteration issues
                try:
                    await member.move_to(None)  # None disconnects them
                    members_kicked += 1
                    kicked_names.append(member.name)
                except discord.Forbidden:
                    log_command(ctx.author, 'serverkickall', f"failed | Missing permissions to kick {member.name}")
                    await ctx.send(get_error_message("missing_permissions", action="kick", member_name=member.name))
                    return
                except discord.HTTPException as e:
                    log_command(ctx.author, 'serverkickall', f"failed | HTTP error while kicking {member.name}: {e}")
                    await ctx.send(get_error_message("http_error", action="kicking", member_name=member.name, error=e))
                    return

    await ctx.send(get_success_message("kicked_users_server",
                                     count=members_kicked,
                                     channels_count=channels_affected,
                                     server_name=ctx.guild.name,
                                     server_id=ctx.guild.id))
    details = (
        f"Members kicked: {members_kicked} | " + (", ".join(kicked_names) if kicked_names else "none") +
        f" | Channels affected: {channels_affected}"
    )
    log_command(ctx.author, 'serverkickall', details)
    await log_to_discord(bot, ctx.author, 'serverkickall', details=details)

# Prefix command: .nick <USER> <NEW_NICK>
@bot.command(name="nick", description="Change a member's server nickname by mention/ID/fuzzy name")
async def nick(ctx, current_name: str, *, new_nick: str = None):
    # Resolve member by mention, ID, or fuzzy name
    try:
        member = resolve_member_by_query(ctx.guild, current_name)
    except ValueError as ve:
        if str(ve) in ("no_members", "empty_query", "not_found"):
            await ctx.send(get_error_message("member_not_found_query", query=current_name))
        else:
            await ctx.send(get_error_message("member_not_found_query", query=current_name))
        log_command(ctx.author, 'nick', f"failed | Member not found from query: {current_name}")
        return

    # Prevent changing own nick via this command to reduce accidents
    if member.id == ctx.author.id:
        log_command(ctx.author, 'nick', 'failed | Attempted to change own nickname')
        await ctx.send(get_error_message("cannot_change_own_nick"))
        return

    # Interpret missing second arg or '-' as clear/remove nickname
    if new_nick is None:
        desired_nick = None
    else:
        desired_nick = None if new_nick.strip() == '-' else new_nick.strip()
    if desired_nick is not None and len(desired_nick) == 0:
        await ctx.send(get_error_message("invalid_nickname"))
        return

    try:
        await member.edit(nick=desired_nick)
        if desired_nick is None:
            await ctx.send(get_success_message("nickname_cleared", member_name=member.display_name, member_id=member.id))
            log_command(ctx.author, 'nick', f"success | Cleared nickname for {member.name} ({member.id})")
            await log_to_discord(bot, ctx.author, 'nick', args=[current_name, '-'], details=f"Cleared nickname for {member.name} ({member.id})")
        else:
            await ctx.send(get_success_message("nickname_changed", member_name=member.display_name, member_id=member.id, new_nick=desired_nick))
            log_command(ctx.author, 'nick', f"success | Changed nickname for {member.name} ({member.id}) to '{desired_nick}'")
            await log_to_discord(bot, ctx.author, 'nick', args=[current_name, desired_nick], details=f"Changed nickname for {member.name} ({member.id}) to '{desired_nick}'")
    except discord.Forbidden:
        log_command(ctx.author, 'nick', f"failed | Missing permissions to change nick for {member.name}")
        await ctx.send(get_error_message("missing_permissions", action="change nickname for", member_name=member.display_name))
    except discord.HTTPException as e:
        log_command(ctx.author, 'nick', f"failed | HTTP error while changing nick for {member.name}: {e}")
        await ctx.send(get_error_message("http_error", action="changing nickname for", member_name=member.display_name, error=e))

# Remove the default help command first
bot.remove_command('help')

# Prefix command: .massban USERID USERID USERID...
@bot.command(name="massban", description="Bans multiple users from the server by their user IDs")
async def massban(ctx, *user_ids):
    if not user_ids:
        log_command(ctx.author, 'massban', 'failed | Reason: no user IDs provided')
        await ctx.send(get_error_message("no_user_ids_provided"))
        return
    
    banned_count = 0
    failed_count = 0
    banned_names = []
    failed_users = []
    
    for user_id_str in user_ids:
        # Validate user_id
        try:
            user_id = int(user_id_str)
        except ValueError:
            log_command(ctx.author, 'massban', f"failed | Invalid user ID: {user_id_str}")
            failed_count += 1
            failed_users.append(f"{user_id_str} (invalid ID)")
            continue
        
        # Fetch the user to get their username
        try:
            user = await bot.fetch_user(user_id)
            username = user.name
        except discord.NotFound:
            log_command(ctx.author, 'massban', f"failed | User not found: {user_id}")
            failed_count += 1
            failed_users.append(f"{user_id} (not found)")
            continue
        except discord.HTTPException as e:
            log_command(ctx.author, 'massban', f"failed | HTTP error while fetching user {user_id}: {e}")
            failed_count += 1
            failed_users.append(f"{user_id} (fetch error)")
            continue
        
        # Check if user is in the server
        member = ctx.guild.get_member(user_id)
        if not member:
            log_command(ctx.author, 'massban', f"failed | User {username} ({user_id}) not in server")
            failed_count += 1
            failed_users.append(f"{username} ({user_id}) - not in server")
            continue
        
        # Prevent banning the command issuer
        if member.id == ctx.author.id:
            log_command(ctx.author, 'massban', f"failed | Cannot ban self: {username} ({user_id})")
            failed_count += 1
            failed_users.append(f"{username} ({user_id}) - cannot ban self")
            continue
        
        # Prevent banning the bot owner
        if member.id == 539464122027343873:
            log_command(ctx.author, 'massban', f"failed | Cannot ban bot owner: {username} ({user_id})")
            failed_count += 1
            failed_users.append(f"{username} ({user_id}) - cannot ban bot owner")
            continue
        
        # Attempt to ban the user
        try:
            await member.ban(reason=f"Mass ban by {ctx.author.name} ({ctx.author.id})")
            banned_count += 1
            banned_names.append(f"{username} ({user_id})")
            log_command(ctx.author, 'massban', f"success | Banned {username} ({user_id})")
        except discord.Forbidden:
            log_command(ctx.author, 'massban', f"failed | Missing permissions to ban {username} ({user_id})")
            failed_count += 1
            failed_users.append(f"{username} ({user_id}) - missing permissions")
        except discord.HTTPException as e:
            log_command(ctx.author, 'massban', f"failed | HTTP error while banning {username} ({user_id}): {e}")
            failed_count += 1
            failed_users.append(f"{username} ({user_id}) - HTTP error")
    
    # Send result message
    if banned_count > 0 and failed_count == 0:
        await ctx.send(get_success_message("massban_success", count=banned_count, usernames=", ".join(banned_names)))
    elif banned_count > 0 and failed_count > 0:
        await ctx.send(get_success_message("massban_partial", 
                                         banned_count=banned_count, 
                                         failed_count=failed_count,
                                         banned_names=", ".join(banned_names),
                                         failed_names=", ".join(failed_users)))
    else:
        await ctx.send(get_error_message("massban_failed", failed_count=failed_count, failed_names=", ".join(failed_users)))
    
    details = f"Banned: {banned_count} | Failed: {failed_count} | Banned: {', '.join(banned_names) if banned_names else 'none'} | Failed: {', '.join(failed_users) if failed_users else 'none'}"
    log_command(ctx.author, 'massban', details)
    await log_to_discord(bot, ctx.author, 'massban', args=list(user_ids), details=details)

# Prefix command: .setupwaiting
@bot.command(name="setupwaiting", description="Crea canali privati e assegna ruolo Sala d’Attesa per utenti con ruolo trigger")
async def setupwaiting(ctx):
    # Resolve roles and category
    trigger_role = ctx.guild.get_role(TRIGGER_ROLE_ID)
    waiting_role = ctx.guild.get_role(WAITING_ROLE_ID)
    category = ctx.guild.get_channel(CATEGORY_ID)

    if trigger_role is None:
        await ctx.send(get_error_message("trigger_role_not_found", role_id=TRIGGER_ROLE_ID))
        log_command(ctx.author, 'setupwaiting', f"failed | trigger role {TRIGGER_ROLE_ID} not found")
        return
    if waiting_role is None:
        await ctx.send(get_error_message("waiting_role_not_found", role_id=WAITING_ROLE_ID))
        log_command(ctx.author, 'setupwaiting', f"failed | waiting role {WAITING_ROLE_ID} not found")
        return
    if category is None:
        await ctx.send(get_error_message("category_not_found", category_id=CATEGORY_ID))
        log_command(ctx.author, 'setupwaiting', f"failed | category {CATEGORY_ID} not found")
        return
    if not isinstance(category, discord.CategoryChannel):
        await ctx.send(get_error_message("invalid_category", category_id=CATEGORY_ID))
        log_command(ctx.author, 'setupwaiting', f"failed | channel {CATEGORY_ID} is not a category")
        return

    # Collect members with trigger role (exclude bots)
    members = [m for m in ctx.guild.members if (trigger_role in getattr(m, 'roles', [])) and not getattr(m, 'bot', False)]

    channels_created = 0
    roles_assigned = 0

    for member in members:
        try:
            ch_created, role_assg = await ensure_waiting_setup_for_member(ctx.guild, member, trigger_role, waiting_role, category)
            if ch_created:
                channels_created += 1
            if role_assg:
                roles_assigned += 1
        except discord.Forbidden:
            await ctx.send(get_error_message("missing_permissions", action="configurare per", member_name=member.display_name))
            log_command(ctx.author, 'setupwaiting', f"failed | missing permissions for {member.name}")
            return
        except discord.HTTPException as e:
            await ctx.send(get_error_message("http_error", action="configurare per", member_name=member.display_name, error=e))
            log_command(ctx.author, 'setupwaiting', f"failed | HTTP while configuring {member.name}: {e}")
            return

    await ctx.send(get_success_message(
        "setupwaiting_summary",
        members_total=len(members),
        channels_created=channels_created,
        roles_assigned=roles_assigned
    ))
    log_command(ctx.author, 'setupwaiting', f"success | members={len(members)} channels_created={channels_created} roles_assigned={roles_assigned}")
    await log_to_discord(bot, ctx.author, 'setupwaiting', details=f"Members processed: {len(members)} | Channels created: {channels_created} | Roles assigned: {roles_assigned}")

# Prefix command: .stopmentor [USER]
@bot.command(name="stopmentor", description="Rimuove ruolo Sala d’Attesa per gli utenti in questo canale e elimina il canale")
async def stopmentor(ctx):
    guild = ctx.guild
    waiting_role = guild.get_role(WAITING_ROLE_ID)
    category = guild.get_channel(CATEGORY_ID)
    if waiting_role is None or not isinstance(category, discord.CategoryChannel):
        if waiting_role is None:
            await ctx.send(get_error_message("waiting_role_not_found", role_id=WAITING_ROLE_ID))
        if not isinstance(category, discord.CategoryChannel):
            await ctx.send(get_error_message("invalid_category", category_id=CATEGORY_ID))
        return

    # Determine the channel to operate on: current text channel
    current_channel = ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None
    if current_channel is None:
        await ctx.send(get_error_message("invalid_channel_id"))
        return

    # Collect members in this channel with the waiting role
    # Note: For text channels, there is no built-in "members in channel" list with read access; use recent participants via channel.members
    # Discord.py provides TextChannel.members as members who can see the channel; we filter by role
    candidates = [m for m in current_channel.members if waiting_role in getattr(m, 'roles', []) and not getattr(m, 'bot', False)]

    if not candidates:
        await ctx.send(get_error_message("stopmentor_no_waiting_in_channel"))
        return

    updated = 0
    for member in candidates:
        try:
            if waiting_role in getattr(member, 'roles', []):
                await member.remove_roles(waiting_role, reason=f"Stop mentor by {ctx.author} ({ctx.author.id})")
            updated += 1
        except discord.Forbidden:
            await ctx.send(get_error_message("missing_permissions", action="rimuovere il ruolo a", member_name=member.display_name))
            return
        except discord.HTTPException as e:
            await ctx.send(get_error_message("http_error", action="rimuovere ruolo a", member_name=member.display_name, error=e))
            return

    # Delete the channel if it belongs to the configured category
    channel_deleted = False
    if current_channel.category and current_channel.category.id == CATEGORY_ID:
        try:
            await current_channel.delete(reason=f"Stop mentor by {ctx.author} ({ctx.author.id})")
            channel_deleted = True
        except discord.Forbidden:
            await ctx.send(get_error_message("missing_permissions", action="eliminare questo canale", member_name=""))
            return
        except discord.HTTPException as e:
            await ctx.send(get_error_message("http_error", action="eliminare questo canale", member_name="", error=e))
            return

    # If channel deleted, message won't be visible; if not deleted, send summary
    if not channel_deleted:
        await ctx.send(get_success_message("stopmentor_done_channel", updated=updated, channel_deleted=channel_deleted))
    log_command(ctx.author, 'stopmentor', f"success | updated={updated} channel_deleted={channel_deleted}")
    await log_to_discord(bot, ctx.author, 'stopmentor', details=f"Users updated: {updated} | Channel deleted: {channel_deleted}")

# Event: React when roles change (auto apply when trigger role is granted)
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    try:
        if before.guild is None:
            return
        guild = after.guild
        trigger_role = guild.get_role(TRIGGER_ROLE_ID)
        waiting_role = guild.get_role(WAITING_ROLE_ID)
        category = guild.get_channel(CATEGORY_ID)
        if not trigger_role or not waiting_role or not isinstance(category, discord.CategoryChannel):
            return
        before_roles = set(r.id for r in getattr(before, 'roles', []))
        after_roles = set(r.id for r in getattr(after, 'roles', []))
        if TRIGGER_ROLE_ID not in before_roles and TRIGGER_ROLE_ID in after_roles:
            if getattr(after, 'bot', False):
                return
            await ensure_waiting_setup_for_member(guild, after, trigger_role, waiting_role, category)
            log_command(after, 'auto-setupwaiting', f"success | configured {after.name} ({after.id})")
    except Exception:
        # Avoid raising from event handlers
        pass

# Prefix command: .ping
@bot.command(name="ping", description="Shows bot latency and responds with Pong!")
async def ping(ctx):
    # Calculate latency in milliseconds
    latency_ms = round(bot.latency * 1000)
    
    await ctx.send(f"Pong! 🏓 {latency_ms}ms")
    log_command(ctx.author, 'ping', f"success | Latency: {latency_ms}ms")
    await log_to_discord(bot, ctx.author, 'ping', details=f"Latency: {latency_ms}ms")

# Prefix command: .help (UPDATED)
@bot.command(name="help", description="Shows all available commands and their usage")
async def help_command(ctx):
    help_embed = discord.Embed(
        title=HELP_EMBED["title"],
        description=HELP_EMBED["description"],
        color=HELP_EMBED["color"]
    )
    
    # Add all fields from the HELP_EMBED configuration
    for field in HELP_EMBED["fields"]:
        help_embed.add_field(
            name=field["name"],
            value=field["value"],
            inline=field["inline"]
        )
    
    help_embed.set_footer(text=HELP_EMBED["footer"])
    
    await ctx.send(embed=help_embed)
    log_command(ctx.author, 'help', 'success | Help embed sent')
    await log_to_discord(bot, ctx.author, 'help', details="Help embed sent")

# Prefix command: .ca (clear all - delete last 100 messages and send KABOOM)
@bot.command(name="ca", description="Clears the last 100 messages and sends a KABOOM message")
async def ca(ctx):
    try:
        # Get the last 100 messages from the channel
        messages = []
        async for message in ctx.channel.history(limit=100):
            messages.append(message)
        
        if not messages:
            log_command(ctx.author, 'ca', 'failed | No messages to delete')
            await ctx.send(get_error_message("no_messages_to_clear"))
            return
        
        # Delete the messages in batches to avoid rate limits
        deleted_count = 0
        for message in messages:
            try:
                await message.delete()
                deleted_count += 1
            except discord.Forbidden:
                log_command(ctx.author, 'ca', f'failed | Missing permissions to delete message {message.id}')
                continue
            except discord.HTTPException as e:
                log_command(ctx.author, 'ca', f'failed | HTTP error while deleting message {message.id}: {e}')
                continue
        
        # Send KABOOM message
        kaboom_msg = await ctx.send(get_success_message("kaboom_message"))
        
        # Delete the KABOOM message after 3 seconds
        await asyncio.sleep(3)
        try:
            await kaboom_msg.delete()
        except (discord.Forbidden, discord.HTTPException):
            # If we can't delete the KABOOM message, just log it
            log_command(ctx.author, 'ca', 'warning | Could not delete KABOOM message')
        
        log_command(ctx.author, 'ca', f'success | Deleted {deleted_count} messages')
        await log_to_discord(bot, ctx.author, 'ca', details=f"Deleted {deleted_count} messages from #{ctx.channel.name}")
        
    except discord.Forbidden:
        log_command(ctx.author, 'ca', 'failed | Missing permissions to manage messages')
        await ctx.send(get_error_message("missing_permissions", action="manage messages", member_name=""))
    except discord.HTTPException as e:
        log_command(ctx.author, 'ca', f'failed | HTTP error: {e}')
        await ctx.send(get_error_message("http_error", action="clearing messages", member_name="", error=e))

# Prefix command: .mentor (assign role to audience in current Stage channel and announce)
@bot.command(name="mentor", description="Assegna un ruolo a tutti i partecipanti connessi nel tuo Stage e annuncia i partecipanti")
async def mentor(ctx):
    ROLE_ID = 1422365715721224192
    ANTHONY_ID = 769582403093004288

    # Validate user is connected and in a Stage channel
    if not ctx.author.voice or not ctx.author.voice.channel or not isinstance(ctx.author.voice.channel, discord.StageChannel):
        log_command(ctx.author, 'mentor', 'failed | Reason: caller not in a Stage channel')
        await ctx.send(get_error_message("not_in_stage"))
        return

    stage_channel: discord.StageChannel = ctx.author.voice.channel

    # Resolve role
    role = ctx.guild.get_role(ROLE_ID)
    if role is None:
        log_command(ctx.author, 'mentor', f'failed | Role not found: {ROLE_ID}')
        await ctx.send(get_error_message("role_not_found"))
        return

    # Collect eligible participants: connected members in this Stage, excluding issuer and bots
    eligible_members = [m for m in stage_channel.members if m.id != ctx.author.id and not getattr(m, 'bot', False)]

    if not eligible_members:
        log_command(ctx.author, 'mentor', 'failed | No eligible participants')
        await ctx.send(get_error_message("no_participants"))
        return

    # Assign role to each eligible member
    assigned_names = []
    try:
        for member in eligible_members:
            if role not in getattr(member, 'roles', []):
                await member.add_roles(role, reason=f"Mentorship participation via .mentor by {ctx.author} ({ctx.author.id})")
            assigned_names.append(member.name)
    except discord.Forbidden:
        # Missing Manage Roles or role hierarchy issue
        log_command(ctx.author, 'mentor', 'failed | Missing permissions to assign role')
        # Reuse existing error template with action/member_name semantics
        await ctx.send(get_error_message("missing_permissions", action="assign role to", member_name="participants"))
        return
    except discord.HTTPException as e:
        log_command(ctx.author, 'mentor', f"failed | HTTP error while assigning roles: {e}")
        await ctx.send(get_error_message("fetch_error", type="roles", error=e))
        return

    # Build announcement message with mentions
    mentions_text = " ".join(member.mention for member in eligible_members)
    anthony_mention = f"<@{ANTHONY_ID}>"
    announcement = get_success_message("mentor_congrats", mentions=mentions_text, anthony_mention=anthony_mention)

    await ctx.send(announcement)
    details = f"Participants: {len(eligible_members)} | " + (", ".join(assigned_names) if assigned_names else "none") + f" | Stage: {stage_channel.name} ({stage_channel.id}) | Role: {role.name} ({role.id})"
    log_command(ctx.author, 'mentor', details)
    await log_to_discord(bot, ctx.author, 'mentor', details=details)

# =============================================================================
# RICH PRESENCE MANAGEMENT COMMANDS
# =============================================================================

# Prefix command: .setstatus <status>
@bot.command(name="setstatus", description="Set bot status (online, idle, dnd, invisible)")
async def setstatus(ctx, status: str):
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible
    }
    
    if status.lower() not in status_map:
        await ctx.send("❌ Invalid status! Use: `online`, `idle`, `dnd`, or `invisible`")
        return
    
    presence_manager.update_setting('bot_status', status_map[status.lower()])
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Status set to: **{status.lower()}**")
    log_command(ctx.author, 'setstatus', f"success | Set status: {status}")
    await log_to_discord(bot, ctx.author, 'setstatus', args=[status])

# Prefix command: .setactivity <text>
@bot.command(name="setactivity", description="Set Rich Presence activity text")
async def setactivity(ctx, *, activity_text: str):
    if not activity_text.strip():
        await ctx.send("❌ Please provide activity text!")
        return
    
    presence_manager.update_setting('activity_text', activity_text)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Activity set to: **{activity_text}**")
    log_command(ctx.author, 'setactivity', f"success | Set activity: {activity_text}")
    await log_to_discord(bot, ctx.author, 'setactivity', args=[activity_text])

# Prefix command: .settype <type>
@bot.command(name="settype", description="Set activity type (playing, listening, watching, streaming, competing)")
async def settype(ctx, activity_type: str):
    type_map = {
        "playing": discord.ActivityType.playing,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
        "streaming": discord.ActivityType.streaming,
        "competing": discord.ActivityType.competing
    }
    
    if activity_type.lower() not in type_map:
        await ctx.send("❌ Invalid type! Use: `playing`, `listening`, `watching`, `streaming`, or `competing`")
        return
    
    presence_manager.update_setting('activity_type', type_map[activity_type.lower()])
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Activity type set to: **{activity_type.lower()}**")
    log_command(ctx.author, 'settype', f"success | Set type: {activity_type}")
    await log_to_discord(bot, ctx.author, 'settype', args=[activity_type])

# Prefix command: .setstreaming <true/false>
@bot.command(name="setstreaming", description="Enable/disable streaming presence")
async def setstreaming(ctx, enable: str):
    if enable.lower() not in ['true', 'false']:
        await ctx.send("❌ Use `true` or `false`!")
        return
    
    enable_bool = enable.lower() == 'true'
    presence_manager.update_setting('enable_streaming', enable_bool)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Streaming {'enabled' if enable_bool else 'disabled'}!")
    log_command(ctx.author, 'setstreaming', f"success | Set streaming: {enable_bool}")
    await log_to_discord(bot, ctx.author, 'setstreaming', args=[enable])

# Prefix command: .setstreamtitle <title>
@bot.command(name="setstreamtitle", description="Set streaming title")
async def setstreamtitle(ctx, *, title: str):
    if not title.strip():
        await ctx.send("❌ Please provide a title!")
        return
    
    presence_manager.update_setting('streaming_title', title)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Streaming title set to: **{title}**")
    log_command(ctx.author, 'setstreamtitle', f"success | Set title: {title}")
    await log_to_discord(bot, ctx.author, 'setstreamtitle', args=[title])

# Prefix command: .setstreamurl <url>
@bot.command(name="setstreamurl", description="Set streaming URL")
async def setstreamurl(ctx, url: str):
    if not url.strip():
        await ctx.send("❌ Please provide a URL!")
        return
    
    presence_manager.update_setting('streaming_url', url)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Streaming URL set to: **{url}**")
    log_command(ctx.author, 'setstreamurl', f"success | Set URL: {url}")
    await log_to_discord(bot, ctx.author, 'setstreamurl', args=[url])

# Prefix command: .setservercount <true/false>
@bot.command(name="setservercount", description="Show/hide server count in presence")
async def setservercount(ctx, show: str):
    if show.lower() not in ['true', 'false']:
        await ctx.send("❌ Use `true` or `false`!")
        return
    
    show_bool = show.lower() == 'true'
    presence_manager.update_setting('show_server_count', show_bool)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Server count {'shown' if show_bool else 'hidden'}!")
    log_command(ctx.author, 'setservercount', f"success | Set server count: {show_bool}")
    await log_to_discord(bot, ctx.author, 'setservercount', args=[show])

# Prefix command: .setmembercount <true/false>
@bot.command(name="setmembercount", description="Show/hide member count in presence")
async def setmembercount(ctx, show: str):
    if show.lower() not in ['true', 'false']:
        await ctx.send("❌ Use `true` or `false`!")
        return
    
    show_bool = show.lower() == 'true'
    presence_manager.update_setting('show_member_count', show_bool)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Member count {'shown' if show_bool else 'hidden'}!")
    log_command(ctx.author, 'setmembercount', f"success | Set member count: {show_bool}")
    await log_to_discord(bot, ctx.author, 'setmembercount', args=[show])

# Prefix command: .setlargeimage <key>
@bot.command(name="setlargeimage", description="Set large image for Rich Presence")
async def setlargeimage(ctx, image_key: str):
    if not image_key.strip():
        await ctx.send("❌ Please provide an image key!")
        return
    
    presence_manager.update_setting('large_image', image_key)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Large image set to: **{image_key}**")
    log_command(ctx.author, 'setlargeimage', f"success | Set large image: {image_key}")
    await log_to_discord(bot, ctx.author, 'setlargeimage', args=[image_key])

# Prefix command: .setlargetext <text>
@bot.command(name="setlargetext", description="Set large image text for Rich Presence")
async def setlargetext(ctx, *, text: str):
    if not text.strip():
        await ctx.send("❌ Please provide text!")
        return
    
    presence_manager.update_setting('large_text', text)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Large image text set to: **{text}**")
    log_command(ctx.author, 'setlargetext', f"success | Set large text: {text}")
    await log_to_discord(bot, ctx.author, 'setlargetext', args=[text])

# Prefix command: .setsmallimage <key>
@bot.command(name="setsmallimage", description="Set small image for Rich Presence")
async def setsmallimage(ctx, image_key: str):
    if not image_key.strip():
        await ctx.send("❌ Please provide an image key!")
        return
    
    presence_manager.update_setting('small_image', image_key)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Small image set to: **{image_key}**")
    log_command(ctx.author, 'setsmallimage', f"success | Set small image: {image_key}")
    await log_to_discord(bot, ctx.author, 'setsmallimage', args=[image_key])

# Prefix command: .setsmalltext <text>
@bot.command(name="setsmalltext", description="Set small image text for Rich Presence")
async def setsmalltext(ctx, *, text: str):
    if not text.strip():
        await ctx.send("❌ Please provide text!")
        return
    
    presence_manager.update_setting('small_text', text)
    await presence_manager.set_presence(bot)
    await ctx.send(f"✅ Small image text set to: **{text}**")
    log_command(ctx.author, 'setsmalltext', f"success | Set small text: {text}")
    await log_to_discord(bot, ctx.author, 'setsmalltext', args=[text])

# Prefix command: .refreshpresence
@bot.command(name="refreshpresence", description="Refresh Rich Presence with current settings")
async def refreshpresence(ctx):
    await presence_manager.set_presence(bot)
    await ctx.send("✅ Rich Presence refreshed!")
    log_command(ctx.author, 'refreshpresence', 'success | Refreshed presence')
    await log_to_discord(bot, ctx.author, 'refreshpresence')

# Prefix command: .resetpresence
@bot.command(name="resetpresence", description="Reset Rich Presence to default settings")
async def resetpresence(ctx):
    # Reset to default settings
    presence_manager.settings = presence_manager.get_default_settings()
    presence_manager.save_settings()
    await presence_manager.set_presence(bot)
    await ctx.send("✅ Presence reset to default!")
    log_command(ctx.author, 'resetpresence', 'success | Reset to default')
    await log_to_discord(bot, ctx.author, 'resetpresence')

# Prefix command: .presenceinfo
@bot.command(name="presenceinfo", description="Show current Rich Presence settings")
async def presenceinfo(ctx):
    settings = presence_manager.settings
    
    embed = discord.Embed(
        title="🎭 Rich Presence Settings",
        color=0x5865F2,
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name="📊 Basic Settings",
        value=f"**Status:** {settings['bot_status'].name}\n"
              f"**Activity Type:** {settings['activity_type'].name}\n"
              f"**Activity Text:** {settings['activity_text']}",
        inline=False
    )
    
    embed.add_field(
        name="📺 Streaming",
        value=f"**Enabled:** {settings['enable_streaming']}\n"
              f"**Title:** {settings['streaming_title']}\n"
              f"**URL:** {settings['streaming_url']}",
        inline=False
    )
    
    embed.add_field(
        name="📈 Server Info",
        value=f"**Show Server Count:** {settings['show_server_count']}\n"
              f"**Show Member Count:** {settings['show_member_count']}",
        inline=True
    )
    
    embed.add_field(
        name="🖼️ Images",
        value=f"**Large Image:** {settings['large_image'] or 'None'}\n"
              f"**Large Text:** {settings['large_text'] or 'None'}\n"
              f"**Small Image:** {settings['small_image'] or 'None'}\n"
              f"**Small Text:** {settings['small_text'] or 'None'}",
        inline=True
    )
    
    embed.set_footer(text="💡 Use .presencehelp for command guide")
    
    await ctx.send(embed=embed)
    log_command(ctx.author, 'presenceinfo', 'success | Showed settings')
    await log_to_discord(bot, ctx.author, 'presenceinfo')

# Prefix command: .checkimages
@bot.command(name="checkimages", description="Check Rich Presence image settings (Note: Discord bots cannot display images)")
async def checkimages(ctx):
    embed = discord.Embed(
        title="🖼️ Rich Presence Image Information",
        color=0xFF6B6B,
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name="⚠️ Important Notice",
        value=(
            "**Discord bots CANNOT display Rich Presence images!**\n\n"
            "This is a Discord API limitation, not a code issue. "
            "Only user accounts can display Rich Presence images, not bot accounts."
        ),
        inline=False
    )
    
    embed.add_field(
        name="✅ What Works for Bots",
        value=(
            "• Activity text (Playing, Listening, Watching)\n"
            "• Activity types (Playing, Listening, Watching, Streaming)\n"
            "• Online status (Online, Idle, Do Not Disturb)\n"
            "• Streaming URLs (for streaming activities)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="❌ What Doesn't Work for Bots",
        value=(
            "• Rich Presence images\n"
            "• Custom Rich Presence assets\n"
            "• Any visual assets in activities"
        ),
        inline=False
    )
    
    embed.set_footer(text="Your Rich Presence system is working correctly!")
    
    await ctx.send(embed=embed)
    log_command(ctx.author, 'checkimages', 'success | Explained bot image limitations')
    await log_to_discord(bot, ctx.author, 'checkimages')

# Prefix command: .presencehelp
@bot.command(name="presencehelp", description="Show Rich Presence command guide")
async def presencehelp(ctx):
    embed = discord.Embed(
        title="🎭 Rich Presence Command Guide",
        description="Complete guide to customize your bot's Rich Presence!",
        color=0x5865F2,
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name="🔧 Basic Commands",
        value=(
            "`.setstatus <status>` → Change bot status\n"
            "`.setactivity <text>` → Set activity text\n"
            "`.settype <type>` → Set activity type\n"
            "`.refreshpresence` → Refresh Rich Presence\n"
            "`.resetpresence` → Reset to default"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📺 Streaming Commands",
        value=(
            "`.setstreaming <true/false>` → Enable/disable streaming\n"
            "`.setstreamtitle <title>` → Set streaming title\n"
            "`.setstreamurl <url>` → Set streaming URL"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📊 Display Commands",
        value=(
            "`.setservercount <true/false>` → Show/hide server count\n"
            "`.setmembercount <true/false>` → Show/hide member count"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🖼️ Image Commands",
        value=(
            "`.setlargeimage <key>` → Set large image\n"
            "`.setlargetext <text>` → Set large image text\n"
            "`.setsmallimage <key>` → Set small image\n"
            "`.setsmalltext <text>` → Set small image text"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎯 Activity Types",
        value=(
            "• **playing** - Playing [text]\n"
            "• **listening** - Listening to [text]\n"
            "• **watching** - Watching [text]\n"
            "• **streaming** - Streaming [text]\n"
            "• **competing** - Competing in [text]"
        ),
        inline=True
    )
    
    embed.add_field(
        name="📊 Status Options",
        value=(
            "• **online** - Green dot\n"
            "• **idle** - Yellow dot\n"
            "• **dnd** - Red dot (Do Not Disturb)\n"
            "• **invisible** - Gray dot"
        ),
        inline=True
    )
    
    embed.add_field(
        name="💡 Examples",
        value=(
            "`.setactivity \"with BrainAllianceFX 🧠\"`\n"
            "`.settype playing`\n"
            "`.setstatus online`\n"
            "`.setlargeimage \"brainalliance_logo\"`\n"
            "`.setlargetext \"BrainAllianceFX Server\"`"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📚 Documentation",
        value=(
            "• **README.md** → Complete setup and command guide\n"
            "• **RICH_PRESENCE_GUIDE.md** → Detailed Rich Presence guide\n"
            "• **.presenceinfo** → Current Rich Presence settings\n"
            "• **.help** → All bot commands"
        ),
        inline=False
    )
    
    embed.set_footer(text="💜 Made with love for BrainAllianceFX")
    
    await ctx.send(embed=embed)
    log_command(ctx.author, 'presencehelp', 'success | Showed help guide')
    await log_to_discord(bot, ctx.author, 'presencehelp')

# Run the bot
bot.run(TOKEN)