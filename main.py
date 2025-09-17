import discord
from discord.ext import commands
import os
import json
import aiofiles
from dotenv import load_dotenv

# Import messages from separate file
from messages import (
    get_error_message, 
    get_success_message, 
    get_status_message, 
    HELP_EMBED
)

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
    if ctx.command.name in ['auth', 'deauth', 'afk']:  # Skip check for .auth, .deauth, and .afk
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
        await ctx.send(get_error_message("not_in_voice"))
        return

    voice_channel = ctx.author.voice.channel
    members_muted = 0

    for member in voice_channel.members:
        if member != ctx.author:
            try:
                await member.edit(mute=True)
                members_muted += 1
            except discord.Forbidden:
                await ctx.send(get_error_message("missing_permissions", action="mute", member_name=member.name))
                return
            except discord.HTTPException as e:
                await ctx.send(get_error_message("http_error", action="muting", member_name=member.name, error=e))
                return

    await ctx.send(get_success_message("muted_users", count=members_muted, channel_name=voice_channel.name))

# Prefix command: .unmuteall
@bot.command(name="unmuteall", description="Unmutes all members in the user's voice channel except themselves")
async def unmuteall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(get_error_message("not_in_voice"))
        return

    voice_channel = ctx.author.voice.channel
    members_unmuted = 0

    for member in voice_channel.members:
        if member != ctx.author:
            try:
                await member.edit(mute=False)
                members_unmuted += 1
            except discord.Forbidden:
                await ctx.send(get_error_message("missing_permissions", action="unmute", member_name=member.name))
                return
            except discord.HTTPException as e:
                await ctx.send(get_error_message("http_error", action="unmuting", member_name=member.name, error=e))
                return

    await ctx.send(get_success_message("unmuted_users", count=members_unmuted, channel_name=voice_channel.name))

# Prefix command: .auth USERID
@bot.command(name="auth", description="Authorizes a user to use bot commands (restricted to bot owner)")
async def auth(ctx, user_id: str):
    # Restrict to your user ID
    if ctx.author.id != 539464122027343873:
        await ctx.send(get_error_message("bot_owner_only"))
        return

    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_user_id"))
        return

    # Fetch the user to get their username
    try:
        user = await bot.fetch_user(user_id)
        username = user.name
    except discord.NotFound:
        await ctx.send(get_error_message("user_not_found_global", user_id=user_id))
        return
    except discord.HTTPException as e:
        await ctx.send(get_error_message("fetch_error", type="user", error=e))
        return

    # Load current authorized users
    authorized_users = await load_authorized_users()

    # Check if user is already authorized
    if str(user_id) in authorized_users:
        await ctx.send(get_error_message("user_already_authorized", username=username, user_id=user_id))
        return

    # Add user to authorized list
    authorized_users[str(user_id)] = username
    await save_authorized_users(authorized_users)
    await ctx.send(get_success_message("user_authorized", username=username, user_id=user_id))

# Prefix command: .deauth USERID
@bot.command(name="deauth", description="Removes a user's authorization to use bot commands (restricted to bot owner)")
async def deauth(ctx, user_id: str):
    # Restrict to your user ID
    if ctx.author.id != 539464122027343873:
        await ctx.send(get_error_message("bot_owner_only"))
        return

    # Prevent deauthorizing the bot owner
    if user_id == '539464122027343873':
        await ctx.send(get_error_message("cannot_deauth_owner"))
        return

    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_user_id"))
        return

    # Load current authorized users
    authorized_users = await load_authorized_users()

    # Check if user is authorized
    if str(user_id) not in authorized_users:
        await ctx.send(get_error_message("user_not_authorized", user_id=user_id))
        return

    # Fetch the user to confirm their username
    try:
        user = await bot.fetch_user(user_id)
        username = user.name
    except discord.NotFound:
        username = authorized_users.get(str(user_id), "Unknown User")
    except discord.HTTPException as e:
        await ctx.send(get_error_message("fetch_error", type="user", error=e))
        return

    # Remove user from authorized list
    del authorized_users[str(user_id)]
    await save_authorized_users(authorized_users)
    await ctx.send(get_success_message("user_deauthorized", username=username, user_id=user_id))

# Prefix command: .moveall CHANNELID (UPDATED WITH ROLLBACK SUPPORT)
@bot.command(name="moveall", description="Moves all members from the user's voice channel to the specified channel")
async def moveall(ctx, channel_id: str):
    global last_move_action
    
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(get_error_message("not_in_voice"))
        return

    # Validate channel_id
    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_channel_id"))
        return

    # Get the destination channel
    try:
        destination_channel = bot.get_channel(channel_id)
        if not destination_channel:
            destination_channel = await bot.fetch_channel(channel_id)
        
        if not isinstance(destination_channel, discord.VoiceChannel):
            await ctx.send(get_error_message("not_voice_channel"))
            return
    except discord.NotFound:
        await ctx.send(get_error_message("channel_not_found", channel_id=channel_id))
        return
    except discord.HTTPException as e:
        await ctx.send(get_error_message("fetch_error", type="channel", error=e))
        return

    source_channel = ctx.author.voice.channel
    members_moved = 0
    
    # Store user positions before moving for rollback
    user_positions = {}

    # Move all members including the command issuer
    for member in list(source_channel.members):  # Use list() to avoid iteration issues
        # Store original position for rollback
        user_positions[member.id] = source_channel.id
        
        try:
            await member.move_to(destination_channel)
            members_moved += 1
        except discord.Forbidden:
            await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
            return
        except discord.HTTPException as e:
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

# Prefix command: .move USERID CHANNELID (UPDATED WITH ROLLBACK SUPPORT)
@bot.command(name="move", description="Moves a specific user to the specified voice channel")
async def move(ctx, user_id: str, channel_id: str):
    global last_move_action
    
    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_user_id"))
        return

    # Validate channel_id
    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_channel_id"))
        return

    # Get the user
    try:
        member = ctx.guild.get_member(user_id)
        if not member:
            member = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.send(get_error_message("user_not_found", user_id=user_id))
        return
    except discord.HTTPException as e:
        await ctx.send(get_error_message("fetch_error", type="user", error=e))
        return

    # Check if user is in a voice channel
    if not member.voice or not member.voice.channel:
        await ctx.send(get_error_message("user_not_in_voice", member_name=member.name))
        return

    # Get the destination channel
    try:
        destination_channel = bot.get_channel(channel_id)
        if not destination_channel:
            destination_channel = await bot.fetch_channel(channel_id)
        
        if not isinstance(destination_channel, discord.VoiceChannel):
            await ctx.send(get_error_message("not_voice_channel"))
            return
    except discord.NotFound:
        await ctx.send(get_error_message("channel_not_found", channel_id=channel_id))
        return
    except discord.HTTPException as e:
        await ctx.send(get_error_message("fetch_error", type="channel", error=e))
        return

    # Move the user
    try:
        source_channel = member.voice.channel
        
        # Store the move action for potential rollback
        last_move_action = {
            'type': 'move',
            'user_positions': {member.id: source_channel.id},
            'destination_channel_id': destination_channel.id,
            'guild_id': ctx.guild.id
        }
        
        await member.move_to(destination_channel)
        await ctx.send(get_success_message("moved_user",
                                         member_name=member.name,
                                         member_id=member.id,
                                         source_name=source_channel.name,
                                         source_id=source_channel.id,
                                         dest_name=destination_channel.name,
                                         dest_id=destination_channel.id))
    except discord.Forbidden:
        await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
    except discord.HTTPException as e:
        await ctx.send(get_error_message("http_error", action="moving", member_name=member.name, error=e))

# Prefix command: .servermoveall CHANNELID (NEW)
@bot.command(name="servermoveall", description="Moves all users from all voice channels in the server to the specified channel")
async def servermoveall(ctx, channel_id: str):
    global last_move_action
    
    # Validate channel_id
    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_channel_id"))
        return

    # Get the destination channel
    try:
        destination_channel = bot.get_channel(channel_id)
        if not destination_channel:
            destination_channel = await bot.fetch_channel(channel_id)
        
        if not isinstance(destination_channel, discord.VoiceChannel):
            await ctx.send(get_error_message("not_voice_channel"))
            return
    except discord.NotFound:
        await ctx.send(get_error_message("channel_not_found", channel_id=channel_id))
        return
    except discord.HTTPException as e:
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
                except discord.Forbidden:
                    await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
                    return
                except discord.HTTPException as e:
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

# Prefix command: .back (NEW - ROLLBACK SYSTEM)
@bot.command(name="back", description="Rollbacks the last move action, returning users to their original channels")
async def back(ctx):
    global last_move_action
    
    if not last_move_action:
        await ctx.send(get_error_message("no_rollback_data"))
        return
    
    # Check if the rollback is for the same guild
    if last_move_action['guild_id'] != ctx.guild.id:
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
        await ctx.send(get_error_message("rollback_channel_not_found"))
        return
    
    # Move users back to their original channels
    for user_id, original_channel_id in user_positions.items():
        try:
            # Get the member
            member = ctx.guild.get_member(user_id)
            if not member:
                continue  # Skip if member is no longer in the guild
            
            # Check if member is still in the destination channel
            if not member.voice or member.voice.channel.id != previous_destination.id:
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
            await ctx.send(get_error_message("missing_permissions", action="move", member_name=member.name))
            return
        except discord.HTTPException as e:
            await ctx.send(get_error_message("http_error", action="moving", member_name=member.name, error=e))
            return
        except (discord.NotFound, AttributeError):
            continue  # Skip if channel or member not found
    
    channels_affected = len(channels_moved_to)
    
    # Clear the last move action since we've used it
    last_move_action = None
    
    await ctx.send(get_success_message("rollback_success", count=members_moved_back, channels_count=channels_affected))

# Prefix command: .kick USERID
@bot.command(name="kick", description="Kicks a specific user from their voice channel")
async def kick(ctx, user_id: str):
    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send(get_error_message("invalid_user_id"))
        return

    # Get the user
    try:
        member = ctx.guild.get_member(user_id)
        if not member:
            member = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.send(get_error_message("user_not_found", user_id=user_id))
        return
    except discord.HTTPException as e:
        await ctx.send(get_error_message("fetch_error", type="user", error=e))
        return

    # Check if user is in a voice channel
    if not member.voice or not member.voice.channel:
        await ctx.send(get_error_message("user_not_in_voice", member_name=member.name))
        return

    # Kick the user from voice channel
    try:
        source_channel = member.voice.channel
        await member.move_to(None)  # None disconnects them
        await ctx.send(get_success_message("kicked_user",
                                         member_name=member.name,
                                         member_id=member.id,
                                         channel_name=source_channel.name,
                                         channel_id=source_channel.id))
    except discord.Forbidden:
        await ctx.send(get_error_message("missing_permissions", action="kick", member_name=member.name))
    except discord.HTTPException as e:
        await ctx.send(get_error_message("http_error", action="kicking", member_name=member.name, error=e))

# Prefix command: .kickall
@bot.command(name="kickall", description="Kicks all members from the user's voice channel except themselves")
async def kickall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(get_error_message("not_in_voice"))
        return

    voice_channel = ctx.author.voice.channel
    members_kicked = 0

    # Kick all members except the command issuer
    for member in list(voice_channel.members):  # Use list() to avoid iteration issues
        if member != ctx.author:
            try:
                await member.move_to(None)  # None disconnects them
                members_kicked += 1
            except discord.Forbidden:
                await ctx.send(get_error_message("missing_permissions", action="kick", member_name=member.name))
                return
            except discord.HTTPException as e:
                await ctx.send(get_error_message("http_error", action="kicking", member_name=member.name, error=e))
                return

    await ctx.send(get_success_message("kicked_users_channel",
                                     count=members_kicked,
                                     channel_name=voice_channel.name,
                                     channel_id=voice_channel.id))

# Prefix command: .serverkickall
@bot.command(name="serverkickall", description="Kicks all members from all voice channels in the server")
async def serverkickall(ctx):
    members_kicked = 0
    channels_affected = 0
    
    # Get all voice channels in the server
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    
    if not voice_channels:
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
                except discord.Forbidden:
                    await ctx.send(get_error_message("missing_permissions", action="kick", member_name=member.name))
                    return
                except discord.HTTPException as e:
                    await ctx.send(get_error_message("http_error", action="kicking", member_name=member.name, error=e))
                    return

    await ctx.send(get_success_message("kicked_users_server",
                                     count=members_kicked,
                                     channels_count=channels_affected,
                                     server_name=ctx.guild.name,
                                     server_id=ctx.guild.id))

# Prefix command: .afk (PUBLIC) - Adds [AFK] prefix to caller's nickname
@bot.command(name="afk", description="Adds [AFK] to the front of your nickname (everyone can use)")
async def afk(ctx):
    # Ensure used in a server
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    prefix = "[AFK] "

    # Determine the base name to apply prefix to
    current_display = ctx.author.display_name or ctx.author.name

    # If already prefixed, acknowledge and exit
    if current_display.startswith(prefix):
        await ctx.send(f"You're already marked as AFK, {ctx.author.mention}.")
        return

    base_name = ctx.author.nick or ctx.author.name
    new_nick = prefix + base_name

    # Discord nickname max length is 32 characters
    if len(new_nick) > 32:
        new_nick = new_nick[:32]

    try:
        await ctx.author.edit(nick=new_nick)
        await ctx.send(f"Set your nickname to '{new_nick}'.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to change your nickname.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to set nickname: {e}")

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

# Run the bot
bot.run(TOKEN)