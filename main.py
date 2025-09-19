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

# Import messages from separate file
from messages import (
    get_error_message, 
    get_success_message, 
    get_status_message, 
    HELP_EMBED
)

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
        else:
            await ctx.send(get_success_message("nickname_changed", member_name=member.display_name, member_id=member.id, new_nick=desired_nick))
            log_command(ctx.author, 'nick', f"success | Changed nickname for {member.name} ({member.id}) to '{desired_nick}'")
    except discord.Forbidden:
        log_command(ctx.author, 'nick', f"failed | Missing permissions to change nick for {member.name}")
        await ctx.send(get_error_message("missing_permissions", action="change nickname for", member_name=member.display_name))
    except discord.HTTPException as e:
        log_command(ctx.author, 'nick', f"failed | HTTP error while changing nick for {member.name}: {e}")
        await ctx.send(get_error_message("http_error", action="changing nickname for", member_name=member.display_name, error=e))

# Remove the default help command first
bot.remove_command('help')

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

# Run the bot
bot.run(TOKEN)