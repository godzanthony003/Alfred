# messages.py - All bot messages in one place for easy editing

# =============================================================================
# ERROR MESSAGES
# =============================================================================

ERROR_MESSAGES = {
    "not_authorized": "You are not authorized to use this command!",
    "not_in_voice": "You must be in a voice channel to use this command!",
    "invalid_user_id": "Invalid user ID! Please provide a valid numeric user ID.",
    "invalid_channel_id": "Invalid channel ID! Please provide a valid numeric channel ID.",
    "user_not_found": "User with ID {user_id} not found in this server!",
    "user_not_found_global": "User with ID {user_id} not found!",
    "channel_not_found": "Voice channel with ID {channel_id} not found!",
    "channel_not_found_query": "Voice channel not found for query: '{query}'. Try a closer name or the ID.",
    "not_voice_channel": "The specified channel is not a voice channel!",
    "user_not_in_voice": "{member_name} is not in a voice channel!",
    "no_voice_channels": "No voice channels found in this server!",
    "missing_permissions": "Failed to {action} {member_name}: Missing permissions",
    "http_error": "Error {action} {member_name}: {error}",
    "fetch_error": "Error fetching {type}: {error}",
    "bot_owner_only": "Only the bot owner can use this command!",
    "cannot_deauth_owner": "You cannot deauthorize the bot owner!",
    "user_already_authorized": "User {username} (ID: {user_id}) is already authorized!",
    "user_not_authorized": "User with ID {user_id} is not authorized!",
    "no_rollback_data": "No move action to rollback!",
    "rollback_different_server": "The last move action was performed in a different server!",
    "rollback_channel_not_found": "Cannot find the previous destination channel for rollback!",
    "member_not_found_query": "Member not found for query: '{query}'. Try a closer name, mention, or ID.",
    "invalid_nickname": "Invalid nickname. Please provide a non-empty nickname.",
    "cannot_change_own_nick": "You cannot change your own nickname with this command.",
    "no_user_ids_provided": "No user IDs provided! Usage: `.massban USERID USERID USERID...`",
    "massban_failed": "Mass ban failed! {failed_count} user(s) could not be banned: {failed_names}",
    # Mentor command
    "not_in_stage": "You must be connected to a Stage channel to use this command!",
    "role_not_found": "The role required for mentorship could not be found.",
    "no_participants": "No eligible participants found in your Stage channel."
}

# =============================================================================
# SUCCESS MESSAGES
# =============================================================================

SUCCESS_MESSAGES = {
    # Mute/Unmute
    "muted_users": "Successfully muted {count} member(s) in {channel_name}!",
    "unmuted_users": "Successfully unmuted {count} member(s) in {channel_name}!",
    
    # Move commands
    "moved_users_channel": "Moved {count} users from #{source_name} {source_id} to #{dest_name} {dest_id}",
    "moved_user": "Moved @{member_name} {member_id} from #{source_name} {source_id} to #{dest_name} {dest_id}",
    "moved_users_server": "Moved {count} users from {channels_count} voice channels to #{dest_name} {dest_id}",
    
    # Kick commands
    "kicked_user": "Kicked @{member_name} {member_id} from #{channel_name} {channel_id}",
    "kicked_users_channel": "Kicked {count} users from #{channel_name} {channel_id}",
    "kicked_users_server": "Kicked {count} users from {channels_count} voice channels in server {server_name} {server_id}",
    
    # Soundboard controls
    "soundboard_disabled_channel": "Disabled soundboard in #{channel_name} {channel_id} for everyone",
    "soundboard_enabled_channel": "Enabled soundboard in #{channel_name} {channel_id} (restored to default)",
    
    # Authorization
    "user_authorized": "Successfully authorized {username} (ID: {user_id}) to use bot commands!",
    "user_deauthorized": "Successfully deauthorized {username} (ID: {user_id}) from using bot commands!",
    
    # Rollback
    "rollback_success": "Rolled back! Moved {count} users back to {channels_count} original voice channels",
    # Nickname
    "nickname_changed": "Changed nickname for @{member_name} {member_id} to '{new_nick}'",
    "nickname_cleared": "Cleared nickname for @{member_name} {member_id}",
    # Mass ban
    "massban_success": "Successfully banned {count} user(s): {usernames}",
    "massban_partial": "Partially successful! Banned {banned_count} user(s): {banned_names}\nFailed to ban {failed_count} user(s): {failed_names}",
    # Mentor command
    "mentor_congrats": "Congratulazioni! {mentions}\n\nAvete visto la vostra mentorship gratuita!\n\nScrivete in privato ad {anthony_mention} per ulteriori dettagli!"
}

# =============================================================================
# HELP COMMAND EMBED DATA
# =============================================================================

HELP_EMBED = {
    "title": "🤖 Bot Commands - User Management",
    "description": "Here are all available commands and their usage:",
    "color": 0x00ff00,
    "footer": "🔹 User Management Bot | All commands use '.' prefix",
    
    "fields": [
        {
            "name": "🎓 Mentorship",
            "value": (
                "`.mentor` - Assegna un ruolo di partecipazione a tutti gli utenti connessi nel tuo Stage attuale e annuncia i partecipanti."
            ),
            "inline": False
        },
        {
            "name": "🔇 Voice Control Commands",
            "value": (
                "`.muteall` - Mutes all members in your voice channel except yourself\n"
                "`.unmuteall` - Unmutes all members in your voice channel except yourself\n"
                "`.nosb` - Disables soundboard usage for everyone in your current voice channel\n"
                "`.dosb` - Re-enables soundboard usage (restore defaults) in your current voice channel"
            ),
            "inline": False
        },
        {
            "name": "🔄 Move Commands",
            "value": (
                "`.moveall <CHANNEL>` - Move ALL users in your voice channel to the given channel (accepts ID or fuzzy name)\n"
                "`.servermoveall <CHANNEL>` - Move ALL users from ALL voice channels to the given channel (accepts ID or fuzzy name)\n"
                "`.back` - Roll back the last move action (moveall/servermoveall)\n"
                "\n**Examples:**\n"
                "`.moveall 123456789012345678`\n"
                "`.moveall alobby`\n"
                "`.servermoveall A | Lobby`\n"
                "`.back`"
            ),
            "inline": False
        },
        {
            "name": "👢 Kick Commands",
            "value": (
                "`.kickall` - Kicks all users from your voice channel except yourself\n"
                "`.serverkickall` - Kicks ALL users from ALL voice channels in the server"
            ),
            "inline": False
        },
        {
            "name": "🔨 Ban Commands",
            "value": (
                "`.massban <USERID> <USERID> <USERID>...` - Bans multiple users from the server by their user IDs\n"
                "\n**Examples:**\n"
                "`.massban 123456789012345678 987654321098765432`\n"
                "`.massban 111111111111111111 222222222222222222 333333333333333333`"
            ),
            "inline": False
        },
        {
            "name": "👤 Nickname Commands",
            "value": (
                "`.nick <USER> <NEW_NICK>` - Change a member's server nickname. `<USER>` can be a mention, ID, or fuzzy display/name. Use `-` or omit `<NEW_NICK>` to clear.\n"
                "\n**Examples:**\n"
                "`.nick aion godslayer`\n"
                "`.nick @Aion Godslayer`\n"
                "`.nick 123456789012345678 -` (clear nick)\n"
                "`.nick aion` (clear nick)"
            ),
            "inline": False
        },
        {
            "name": "🔐 Authorization Commands (Bot Owner Only)",
            "value": (
                "`.auth <USER_ID>` - Authorizes a user to use bot commands\n"
                "`.deauth <USER_ID>` - Removes a user's authorization\n"
                "\n**Examples:**\n"
                "`.auth 987654321098765432`\n"
                "`.deauth 987654321098765432`"
            ),
            "inline": False
        },
        {
            "name": "ℹ️ Information",
            "value": (
                "• All commands (except auth/deauth) require authorization\n"
                "• Only authorized users can use voice management commands\n"
                "• Bot owner can authorize/deauthorize users\n"
                "• Move commands support rollback with `.back`\n"
                "• Commands provide detailed logs of actions performed"
            ),
            "inline": False
        },
        {
            "name": "📝 Tips",
            "value": (
                "• You can use channel IDs or approximate names (e.g., 'alobby' → 'A | Lobby')\n"
                "• For exact matches, prefer using the ID"
            ),
            "inline": False
        }
    ]
}

# =============================================================================
# BOT STATUS MESSAGES
# =============================================================================

STATUS_MESSAGES = {
    "bot_ready": "{bot_name} has connected to Discord!",
    "json_error": "Error: Invalid JSON in authorized_users.json. Using default."
}

# =============================================================================
# UTILITY FUNCTIONS FOR MESSAGE FORMATTING
# =============================================================================

def get_error_message(key, **kwargs):
    """Get formatted error message"""
    return ERROR_MESSAGES.get(key, "Unknown error").format(**kwargs)

def get_success_message(key, **kwargs):
    """Get formatted success message"""
    return SUCCESS_MESSAGES.get(key, "Success").format(**kwargs)

def get_status_message(key, **kwargs):
    """Get formatted status message"""
    return STATUS_MESSAGES.get(key, "Status").format(**kwargs)