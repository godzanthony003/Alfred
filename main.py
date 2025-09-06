import discord
from discord.ext import commands
import os
import json
import aiofiles
from dotenv import load_dotenv

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
        print("Error: Invalid JSON in authorized_users.json. Using default.")
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
        await ctx.send("You are not authorized to use this command!")
        return False
    return True

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Prefix command: .muteall
@bot.command(name="muteall", description="Mutes all members in the user's voice channel except themselves")
async def muteall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You must be in a voice channel to use this command!")
        return

    voice_channel = ctx.author.voice.channel
    members_muted = 0

    for member in voice_channel.members:
        if member != ctx.author:
            try:
                await member.edit(mute=True)
                members_muted += 1
            except discord.Forbidden:
                await ctx.send(f"Failed to mute {member.name}: Missing permissions")
                return
            except discord.HTTPException as e:
                await ctx.send(f"Error muting {member.name}: {e}")
                return

    await ctx.send(f"Successfully muted {members_muted} member(s) in {voice_channel.name}!")

# Prefix command: .unmuteall
@bot.command(name="unmuteall", description="Unmutes all members in the user's voice channel except themselves")
async def unmuteall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You must be in a voice channel to use this command!")
        return

    voice_channel = ctx.author.voice.channel
    members_unmuted = 0

    for member in voice_channel.members:
        if member != ctx.author:
            try:
                await member.edit(mute=False)
                members_unmuted += 1
            except discord.Forbidden:
                await ctx.send(f"Failed to unmute {member.name}: Missing permissions")
                return
            except discord.HTTPException as e:
                await ctx.send(f"Error unmuting {member.name}: {e}")
                return

    await ctx.send(f"Successfully unmuted {members_unmuted} member(s) in {voice_channel.name}!")

# Prefix command: .auth USERID
@bot.command(name="auth", description="Authorizes a user to use bot commands (restricted to bot owner)")
async def auth(ctx, user_id: str):
    # Restrict to your user ID
    if ctx.author.id != 539464122027343873:
        await ctx.send("Only the bot owner can use this command!")
        return

    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send("Invalid user ID! Please provide a valid numeric user ID.")
        return

    # Fetch the user to get their username
    try:
        user = await bot.fetch_user(user_id)
        username = user.name
    except discord.NotFound:
        await ctx.send(f"User with ID {user_id} not found!")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching user: {e}")
        return

    # Load current authorized users
    authorized_users = await load_authorized_users()

    # Check if user is already authorized
    if str(user_id) in authorized_users:
        await ctx.send(f"User {username} (ID: {user_id}) is already authorized!")
        return

    # Add user to authorized list
    authorized_users[str(user_id)] = username
    await save_authorized_users(authorized_users)
    await ctx.send(f"Successfully authorized {username} (ID: {user_id}) to use bot commands!")

# Prefix command: .deauth USERID
@bot.command(name="deauth", description="Removes a user's authorization to use bot commands (restricted to bot owner)")
async def deauth(ctx, user_id: str):
    # Restrict to your user ID
    if ctx.author.id != 539464122027343873:
        await ctx.send("Only the bot owner can use this command!")
        return

    # Prevent deauthorizing the bot owner
    if user_id == '539464122027343873':
        await ctx.send("You cannot deauthorize the bot owner!")
        return

    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send("Invalid user ID! Please provide a valid numeric user ID.")
        return

    # Load current authorized users
    authorized_users = await load_authorized_users()

    # Check if user is authorized
    if str(user_id) not in authorized_users:
        await ctx.send(f"User with ID {user_id} is not authorized!")
        return

    # Fetch the user to confirm their username
    try:
        user = await bot.fetch_user(user_id)
        username = user.name
    except discord.NotFound:
        username = authorized_users.get(str(user_id), "Unknown User")
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching user: {e}")
        return

    # Remove user from authorized list
    del authorized_users[str(user_id)]
    await save_authorized_users(authorized_users)
    await ctx.send(f"Successfully deauthorized {username} (ID: {user_id}) from using bot commands!")

# Prefix command: .moveall CHANNELID (UPDATED WITH ROLLBACK SUPPORT)
@bot.command(name="moveall", description="Moves all members from the user's voice channel to the specified channel")
async def moveall(ctx, channel_id: str):
    global last_move_action
    
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You must be in a voice channel to use this command!")
        return

    # Validate channel_id
    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.send("Invalid channel ID! Please provide a valid numeric channel ID.")
        return

    # Get the destination channel
    try:
        destination_channel = bot.get_channel(channel_id)
        if not destination_channel:
            destination_channel = await bot.fetch_channel(channel_id)
        
        if not isinstance(destination_channel, discord.VoiceChannel):
            await ctx.send("The specified channel is not a voice channel!")
            return
    except discord.NotFound:
        await ctx.send(f"Voice channel with ID {channel_id} not found!")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching channel: {e}")
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
            await ctx.send(f"Failed to move {member.name}: Missing permissions")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Error moving {member.name}: {e}")
            return

    # Store the move action for potential rollback
    last_move_action = {
        'type': 'moveall',
        'user_positions': user_positions,
        'destination_channel_id': destination_channel.id,
        'guild_id': ctx.guild.id
    }

    await ctx.send(f"Moved {members_moved} users from #{source_channel.name} {source_channel.id} to #{destination_channel.name} {destination_channel.id}")

# Prefix command: .move USERID CHANNELID (UPDATED WITH ROLLBACK SUPPORT)
@bot.command(name="move", description="Moves a specific user to the specified voice channel")
async def move(ctx, user_id: str, channel_id: str):
    global last_move_action
    
    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send("Invalid user ID! Please provide a valid numeric user ID.")
        return

    # Validate channel_id
    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.send("Invalid channel ID! Please provide a valid numeric channel ID.")
        return

    # Get the user
    try:
        member = ctx.guild.get_member(user_id)
        if not member:
            member = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.send(f"User with ID {user_id} not found in this server!")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching user: {e}")
        return

    # Check if user is in a voice channel
    if not member.voice or not member.voice.channel:
        await ctx.send(f"{member.name} is not in a voice channel!")
        return

    # Get the destination channel
    try:
        destination_channel = bot.get_channel(channel_id)
        if not destination_channel:
            destination_channel = await bot.fetch_channel(channel_id)
        
        if not isinstance(destination_channel, discord.VoiceChannel):
            await ctx.send("The specified channel is not a voice channel!")
            return
    except discord.NotFound:
        await ctx.send(f"Voice channel with ID {channel_id} not found!")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching channel: {e}")
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
        await ctx.send(f"Moved @{member.name} {member.id} from #{source_channel.name} {source_channel.id} to #{destination_channel.name} {destination_channel.id}")
    except discord.Forbidden:
        await ctx.send(f"Failed to move {member.name}: Missing permissions")
    except discord.HTTPException as e:
        await ctx.send(f"Error moving {member.name}: {e}")

# Prefix command: .servermoveall CHANNELID (NEW)
@bot.command(name="servermoveall", description="Moves all users from all voice channels in the server to the specified channel")
async def servermoveall(ctx, channel_id: str):
    global last_move_action
    
    # Validate channel_id
    try:
        channel_id = int(channel_id)
    except ValueError:
        await ctx.send("Invalid channel ID! Please provide a valid numeric channel ID.")
        return

    # Get the destination channel
    try:
        destination_channel = bot.get_channel(channel_id)
        if not destination_channel:
            destination_channel = await bot.fetch_channel(channel_id)
        
        if not isinstance(destination_channel, discord.VoiceChannel):
            await ctx.send("The specified channel is not a voice channel!")
            return
    except discord.NotFound:
        await ctx.send(f"Voice channel with ID {channel_id} not found!")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching channel: {e}")
        return

    # Get all voice channels in the server
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    
    if not voice_channels:
        await ctx.send("No voice channels found in this server!")
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
                    await ctx.send(f"Failed to move {member.name} from #{channel.name} {channel.id}: Missing permissions")
                    return
                except discord.HTTPException as e:
                    await ctx.send(f"Error moving {member.name} from #{channel.name} {channel.id}: {e}")
                    return

    # Store the move action for potential rollback
    last_move_action = {
        'type': 'servermoveall',
        'user_positions': user_positions,
        'destination_channel_id': destination_channel.id,
        'guild_id': ctx.guild.id
    }

    await ctx.send(f"Moved {members_moved} users from {channels_affected} voice channels to #{destination_channel.name} {destination_channel.id}")

# Prefix command: .back (NEW - ROLLBACK SYSTEM)
@bot.command(name="back", description="Rollbacks the last move action, returning users to their original channels")
async def back(ctx):
    global last_move_action
    
    if not last_move_action:
        await ctx.send("No move action to rollback!")
        return
    
    # Check if the rollback is for the same guild
    if last_move_action['guild_id'] != ctx.guild.id:
        await ctx.send("The last move action was performed in a different server!")
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
        await ctx.send("Cannot find the previous destination channel for rollback!")
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
            await ctx.send(f"Failed to move {member.name} back: Missing permissions")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Error moving {member.name} back: {e}")
            return
        except (discord.NotFound, AttributeError):
            continue  # Skip if channel or member not found
    
    channels_affected = len(channels_moved_to)
    
    # Clear the last move action since we've used it
    last_move_action = None
    
    await ctx.send(f"Rolled back! Moved {members_moved_back} users back to {channels_affected} original voice channels")

# Prefix command: .kick USERID
@bot.command(name="kick", description="Kicks a specific user from their voice channel")
async def kick(ctx, user_id: str):
    # Validate user_id
    try:
        user_id = int(user_id)
    except ValueError:
        await ctx.send("Invalid user ID! Please provide a valid numeric user ID.")
        return

    # Get the user
    try:
        member = ctx.guild.get_member(user_id)
        if not member:
            member = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.send(f"User with ID {user_id} not found in this server!")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Error fetching user: {e}")
        return

    # Check if user is in a voice channel
    if not member.voice or not member.voice.channel:
        await ctx.send(f"{member.name} is not in a voice channel!")
        return

    # Kick the user from voice channel
    try:
        source_channel = member.voice.channel
        await member.move_to(None)  # None disconnects them
        await ctx.send(f"Kicked @{member.name} {member.id} from #{source_channel.name} {source_channel.id}")
    except discord.Forbidden:
        await ctx.send(f"Failed to kick {member.name}: Missing permissions")
    except discord.HTTPException as e:
        await ctx.send(f"Error kicking {member.name}: {e}")

# Prefix command: .kickall
@bot.command(name="kickall", description="Kicks all members from the user's voice channel except themselves")
async def kickall(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You must be in a voice channel to use this command!")
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
                await ctx.send(f"Failed to kick {member.name}: Missing permissions")
                return
            except discord.HTTPException as e:
                await ctx.send(f"Error kicking {member.name}: {e}")
                return

    await ctx.send(f"Kicked {members_kicked} users from #{voice_channel.name} {voice_channel.id}")

# Prefix command: .serverkickall
@bot.command(name="serverkickall", description="Kicks all members from all voice channels in the server")
async def serverkickall(ctx):
    members_kicked = 0
    channels_affected = 0
    
    # Get all voice channels in the server
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    
    if not voice_channels:
        await ctx.send("No voice channels found in this server!")
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
                    await ctx.send(f"Failed to kick {member.name} from #{channel.name} {channel.id}: Missing permissions")
                    return
                except discord.HTTPException as e:
                    await ctx.send(f"Error kicking {member.name} from #{channel.name} {channel.id}: {e}")
                    return

    await ctx.send(f"Kicked {members_kicked} users from {channels_affected} voice channels in server {ctx.guild.name} {ctx.guild.id}")

# Remove the default help command first
bot.remove_command('help')

# Prefix command: .help (UPDATED)
@bot.command(name="help", description="Shows all available commands and their usage")
async def help_command(ctx):
    help_embed = discord.Embed(
        title="🤖 Bot Commands - User Management",
        description="Here are all available commands and their usage:",
        color=0x00ff00
    )
    
    # Voice Control Commands
    help_embed.add_field(
        name="🔇 Voice Control Commands",
        value=(
            "`.muteall` - Mutes all members in your voice channel except yourself\n"
            "`.unmuteall` - Unmutes all members in your voice channel except yourself"
        ),
        inline=False
    )
    
    # Move Commands
    help_embed.add_field(
        name="🔄 Move Commands",
        value=(
            "`.moveall <CHANNEL_ID>` - Moves ALL users (including yourself) from your voice channel to specified channel\n"
            "`.move <USER_ID> <CHANNEL_ID>` - Moves a specific user to specified voice channel\n"
            "`.servermoveall <CHANNEL_ID>` - Moves ALL users from ALL voice channels to specified channel\n"
            "`.back` - Rolls back the last move action (move/moveall/servermoveall)\n"
            "\n**Examples:**\n"
            "`.moveall 123456789012345678`\n"
            "`.move 987654321098765432 123456789012345678`\n"
            "`.servermoveall 123456789012345678`\n"
            "`.back`"
        ),
        inline=False
    )
    
    # Kick Commands
    help_embed.add_field(
        name="👢 Kick Commands",
        value=(
            "`.kick <USER_ID>` - Kicks a specific user from their voice channel\n"
            "`.kickall` - Kicks all users from your voice channel except yourself\n"
            "`.serverkickall` - Kicks ALL users from ALL voice channels in the server\n"
            "\n**Example:**\n"
            "`.kick 987654321098765432`"
        ),
        inline=False
    )
    
    # Authorization Commands
    help_embed.add_field(
        name="🔐 Authorization Commands (Bot Owner Only)",
        value=(
            "`.auth <USER_ID>` - Authorizes a user to use bot commands\n"
            "`.deauth <USER_ID>` - Removes a user's authorization\n"
            "\n**Examples:**\n"
            "`.auth 987654321098765432`\n"
            "`.deauth 987654321098765432`"
        ),
        inline=False
    )
    
    # Information
    help_embed.add_field(
        name="ℹ️ Information",
        value=(
            "• All commands (except auth/deauth) require authorization\n"
            "• Only authorized users can use voice management commands\n"
            "• Bot owner can authorize/deauthorize users\n"
            "• Move commands support rollback with `.back`\n"
            "• Commands provide detailed logs of actions performed"
        ),
        inline=False
    )
    
    help_embed.add_field(
        name="📝 How to get IDs",
        value=(
            "**User ID:** Right-click user → Copy User ID\n"
            "**Channel ID:** Right-click voice channel → Copy Channel ID\n"
            "*(Developer Mode must be enabled in Discord settings)*"
        ),
        inline=False
    )
    
    help_embed.set_footer(text="🔹 User Management Bot | All commands use '.' prefix")
    
    await ctx.send(embed=help_embed)

# Run the bot
bot.run(TOKEN)