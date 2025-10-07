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
    "no_participants": "No eligible participants found in your Stage channel.",
    # Setup Waiting workflow
    "category_not_found": "Categoria con ID {category_id} non trovata!",
    "invalid_category": "Il canale con ID {category_id} non è una categoria valida!",
    "trigger_role_not_found": "Ruolo di trigger non trovato (ID: {role_id})!",
    "waiting_role_not_found": "Ruolo Sala d’Attesa non trovato (ID: {role_id})!",
    "channel_create_failed": "Errore nella creazione del canale per @{member_name} {member_id}: {error}",
    "stopmentor_no_waiting_in_channel": "Nessun utente con il ruolo Sala d'Attesa trovato in questo canale.",
    "no_messages_to_clear": "No messages found to clear in this channel!"
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
    "mentor_congrats": "Congratulazioni! {mentions}\n\nAvete visto la vostra mentorship gratuita!\n\n# Scrivete in privato ad {anthony_mention} per ulteriori dettagli!",
    # Setup Waiting workflow
    "setupwaiting_summary": "Completato: trovati {members_total} utenti con ruolo trigger. Canali creati: {channels_created}. Ruoli assegnati/già presenti: {roles_assigned}.",
    # Stop mentor
    "stopmentor_done": "Sessione terminata per @{member_name}. Canale eliminato: {channel_deleted}. Ruolo Sala d'Attesa rimosso: {role_removed}.",
    "stopmentor_done_channel": "Sessione terminata. Utenti aggiornati: {updated}. Canale eliminato: {channel_deleted}.",
    # Clear all command
    "kaboom_message": "💥 **KABOOM!** 💥\n\n*Channel cleared!*"
}

# =============================================================================
# HELP COMMAND EMBED DATA
# =============================================================================

HELP_EMBED = {
    "title": "🧠✨ BrainAllianceFX Bot Commands",
    "description": "All available commands at your fingertips! Use `.` prefix for everything.",
    "color": 0x5865F2,  # Discord blurple
    "footer": "💜 Made with love for BrainAllianceFX",
    
    "fields": [
        {
            "name": "🎓 Mentorship & Events",
            "value": (
                "`.mentor` → Assign participation roles to Stage members\n"
                "`.stopmentor [USER]` → Remove waiting room role & delete private channel\n"
                "`.setupwaiting` → Auto-create private channels for waiting users"
            ),
            "inline": False
        },
        {
            "name": "🔊 Voice Controls",
            "value": (
                "`.muteall` / `.unmuteall` → Mute/unmute everyone (except you!)\n"
                "`.nosb` / `.dosb` → Disable/enable soundboard"
            ),
            "inline": False
        },
        {
            "name": "🚀 Move Users",
            "value": (
                "`.moveall <channel>` → Move your channel to another\n"
                "`.servermoveall <channel>` → Move EVERYONE to one channel\n"
                "`.back` → Undo last move (lifesaver!)\n"
                "*Tip: Use channel ID or fuzzy names like 'alobby'*"
            ),
            "inline": False
        },
        {
            "name": "👢 Kick & 🔨 Ban",
            "value": (
                "`.kickall` → Clear your voice channel\n"
                "`.serverkickall` → Clear ALL voice channels\n"
                "`.massban <id> <id>...` → Ban multiple users by ID"
            ),
            "inline": False
        },
        {
            "name": "🧹 Channel Management",
            "value": (
                "`.ca` → Clear last 100 messages + KABOOM! 💥\n"
                "*Perfect for cleaning up channels*"
            ),
            "inline": False
        },
        {
            "name": "👤 Nicknames",
            "value": (
                "`.nick <user> <new_nick>` → Change someone's nickname\n"
                "`.nick <user> -` → Clear nickname\n"
                "*Supports mentions, IDs, or fuzzy names*"
            ),
            "inline": False
        },
        {
            "name": "🔐 Authorization (Owner Only)",
            "value": (
                "`.auth <user_id>` → Grant command access\n"
                "`.deauth <user_id>` → Revoke command access"
            ),
            "inline": False
        },
        {
            "name": "🎭 Rich Presence",
            "value": (
                "`.setstatus <status>` → Change bot status\n"
                "`.setactivity <text>` → Set activity text\n"
                "`.settype <type>` → Set activity type\n"
                "`.setstreaming <true/false>` → Enable/disable streaming\n"
                "`.setlargeimage <key>` → Set large image\n"
                "`.setsmallimage <key>` → Set small image\n"
                "`.refreshpresence` → Refresh Rich Presence\n"
                "`.checkimages` → Check image configuration\n"
                "`.presenceinfo` → Show current settings\n"
                "`.presencehelp` → Complete command guide"
            ),
            "inline": False
        },
        {
            "name": "💡 Quick Tips",
            "value": (
                "• Use `.ping` to check bot status\n"
                "• Channel IDs work best for exact matches\n"
                "• All actions are logged automatically\n"
                "• `.back` works for both move commands\n"
                "• Use `.presencehelp` for Rich Presence guide"
            ),
            "inline": False
        },
        {
            "name": "📚 Documentation",
            "value": (
                "• **README.md** → Complete setup and command guide\n"
                "• **RICH_PRESENCE_GUIDE.md** → Detailed Rich Presence guide\n"
                "• **.presencehelp** → Rich Presence command reference\n"
                "• **.presenceinfo** → Current Rich Presence settings"
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