import discord
from discord.ext import commands, tasks
import os
import json
from datetime import datetime, timedelta
import pytz

# Get token from environment variable only (for security)
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ Error: DISCORD_TOKEN environment variable not set!")
    print("Please set your Discord bot token as an environment variable.")
    exit(1)

INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.guilds = True
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix='*', intents=INTENTS)

MOD_ROLE_NAME = 'shitty mod'
SHIFT_LOG_CHANNEL_NAME = 'mod-shift-logs'
MONITORED_CHANNEL_IDS = [1334854378686910475, 1234620156383203482]
DATA_FILE = 'mod_data.json'
PKT = pytz.timezone('Asia/Karachi')

# --- Data Persistence ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

data = load_data()

# --- Helper Functions ---
def get_now():
    return datetime.now(PKT)

def format_time(time_str):
    """Format time string to readable format without seconds"""
    try:
        dt = datetime.fromisoformat(time_str)
        return dt.strftime("%d %B %Y, %I:%M %p PKT")
    except:
        return time_str

def check_mod_activity_in_channels(user_id, minutes=25):
    """Check if mod sent messages in monitored channels in last X minutes"""
    now = get_now()
    user_data = data.get(str(user_id), {})
    recent_messages = user_data.get('recent_messages', [])
    
    # Filter messages from last X minutes
    recent_activity = []
    for msg in recent_messages:
        try:
            msg_time = datetime.fromisoformat(msg['timestamp'])
            if (now - msg_time) <= timedelta(minutes=minutes):
                recent_activity.append(msg)
        except:
            continue
    
    return len(recent_activity) > 0, recent_activity

def can_checkin(user_id):
    """Check if user can check-in (25 minutes since last check-in)"""
    user_data = data.get(str(user_id), {})
    checkins = user_data.get('checkins', [])
    
    if not checkins:
        return True, None
    
    last_checkin = datetime.fromisoformat(checkins[-1])
    now = get_now()
    time_since_last = now - last_checkin
    
    if time_since_last < timedelta(minutes=25):
        remaining = timedelta(minutes=25) - time_since_last
        return False, remaining
    return True, None

# --- Check-In Reminder Task ---
@tasks.loop(minutes=1)
async def check_in_reminder():
    now = get_now()
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        if not role:
            continue
        
        for mod in role.members:
            user_data = data.setdefault(str(mod.id), {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
            
            # Check if mod is currently on shift
            on_shift = False
            for shift in reversed(user_data['shifts']):
                if shift['end'] is None:  # Shift is ongoing
                    on_shift = True
                    break
            
            if not on_shift:
                continue  # Skip if not on shift
            
            # Check last check-in time
            last_checkin = None
            if user_data['checkins']:
                last_checkin = datetime.fromisoformat(user_data['checkins'][-1])
            
            # If no check-in or check-in was more than 25 minutes ago
            if not last_checkin or (now - last_checkin) > timedelta(minutes=25):
                # Check if they've been active in monitored channels
                has_activity, recent_messages = check_mod_activity_in_channels(mod.id, 25)
                
                try:
                    if has_activity:
                        # They've been active, remind them to check-in
                        embed = discord.Embed(
                            title="⏰ Check-in Reminder!",
                            description="You've been active in monitored channels. Please check-in now!",
                            color=0xffa500
                        )
                        embed.add_field(name="🕐 Last Check-in", value=format_time(last_checkin.isoformat()) if last_checkin else "None", inline=True)
                        embed.add_field(name="📝 Recent Activity", value=f"{len(recent_messages)} messages in monitored channels", inline=True)
                        embed.add_field(name="✅ Action Required", value="Use `*checkin` to check-in", inline=False)
                        
                        await mod.send(embed=embed)
                    else:
                        # They haven't been active, remind them to be active first
                        embed = discord.Embed(
                            title="⚠️ Activity Required!",
                            description="You need to send messages in monitored channels before checking in!",
                            color=0xff0000
                        )
                        embed.add_field(name="🕐 Last Check-in", value=format_time(last_checkin.isoformat()) if last_checkin else "None", inline=True)
                        embed.add_field(name="📝 Required Action", value="Send at least 1 message in monitored channels", inline=True)
                        embed.add_field(name="📋 Monitored Channels", value=f"<#{MONITORED_CHANNEL_IDS[0]}> and <#{MONITORED_CHANNEL_IDS[1]}>", inline=False)
                        embed.add_field(name="✅ Next Step", value="After sending a message, use `*checkin`", inline=False)
                        
                        await mod.send(embed=embed)
                    
                    # Log missed check-in
                    if not user_data['missed'] or (user_data['missed'] and (now - datetime.fromisoformat(user_data['missed'][-1])) > timedelta(minutes=24)):
                        user_data['missed'].append(now.isoformat())
                        save_data(data)
                        
                except Exception as e:
                    print(f"Error sending reminder to {mod.name}: {e}")

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f'Mod bot logged in as {bot.user.name}')
    print(f'Bot is in {len(bot.guilds)} guild(s)')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
        # Create role and channel if they don't exist
        await create_role_and_channel(guild)
    
    # Start the reminder task
    check_in_reminder.start()
    print("✅ Check-in reminder system started!")

async def create_role_and_channel(guild):
    try:
        # Create mod role if it doesn't exist
        role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        if not role:
            role = await guild.create_role(name=MOD_ROLE_NAME)
            print(f'Created role: {MOD_ROLE_NAME}')
        
        # Create shift log channel if it doesn't exist
        channel = discord.utils.get(guild.text_channels, name=SHIFT_LOG_CHANNEL_NAME)
        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            await guild.create_text_channel(SHIFT_LOG_CHANNEL_NAME, overwrites=overwrites)
            print(f'Created channel: {SHIFT_LOG_CHANNEL_NAME}')
    except Exception as e:
        print(f'Error creating role/channel: {e}')

# --- Message Monitoring ---
@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    
    # Track messages in monitored channels
    if message.channel.id in MONITORED_CHANNEL_IDS:
        user_id = str(message.author.id)
        user_data = data.setdefault(user_id, {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
        
        # Add message to recent messages
        message_data = {
            'channel_id': message.channel.id,
            'content': message.content,
            'timestamp': get_now().isoformat()
        }
        user_data['recent_messages'].append(message_data)
        
        # Keep only last 100 messages per user
        if len(user_data['recent_messages']) > 100:
            user_data['recent_messages'] = user_data['recent_messages'][-100:]
        
        save_data(data)
    
    await bot.process_commands(message)

# --- Commands ---
@bot.command(name='shift_start', help='Start your mod shift')
async def shift_start(ctx):
    user = ctx.author
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
    if role not in user.roles:
        await ctx.send('❌ You are not a mod! You need the "shitty mod" role.')
        return
    now = get_now().isoformat()
    data.setdefault(str(user.id), {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
    data[str(user.id)]['shifts'].append({'start': now, 'end': None})
    save_data(data)
    formatted_time = format_time(now)
    await ctx.send(f'✅ **Shift Started!**\n🕐 {formatted_time}\n\n⚠️ **Remember:** You must send messages in the monitored channels and check-in every 25 minutes!')
    # Log in channel
    channel = discord.utils.get(guild.text_channels, name=SHIFT_LOG_CHANNEL_NAME)
    if channel:
        await channel.send(f'🔵 **{user.display_name}** started their shift at {formatted_time}')

@bot.command(name='shift_end', help='End your mod shift')
async def shift_end(ctx):
    user = ctx.author
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
    if role not in user.roles:
        await ctx.send('❌ You are not a mod! You need the "shitty mod" role.')
        return
    now = get_now().isoformat()
    user_data = data.setdefault(str(user.id), {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
    # Find last open shift
    for shift in reversed(user_data['shifts']):
        if shift['end'] is None:
            shift['end'] = now
            break
    save_data(data)
    formatted_time = format_time(now)
    await ctx.send(f'🔴 **Shift Ended!**\n🕐 {formatted_time}')
    channel = discord.utils.get(guild.text_channels, name=SHIFT_LOG_CHANNEL_NAME)
    if channel:
        await channel.send(f'🔴 **{user.display_name}** ended their shift at {formatted_time}')

@bot.command(name='checkin', help='Check in for your shift (must be active in monitored channels)')
async def checkin(ctx):
    user = ctx.author
    role = discord.utils.get(ctx.guild.roles, name=MOD_ROLE_NAME)
    if role not in user.roles:
        await ctx.send('❌ You are not a mod! You need the "shitty mod" role.')
        return
    
    # Check if user can check-in (25 minutes since last check-in)
    can_check, remaining_time = can_checkin(user.id)
    if not can_check:
        minutes = int(remaining_time.total_seconds() // 60)
        seconds = int(remaining_time.total_seconds() % 60)
        await ctx.send(f'⏰ **Please wait before checking in again!**\n⏳ You can check-in again in **{minutes}m {seconds}s**')
        return
    
    # Check if user has been active in monitored channels in last 25 minutes
    has_activity, recent_messages = check_mod_activity_in_channels(user.id, 25)
    
    if not has_activity:
        await ctx.send(f'❌ **Check-in Failed!**\n\n⚠️ You must send at least one message in the monitored channels within the last 25 minutes before checking in.\n\n📝 **Please send a message in the monitored channels and try again.**')
        return
    
    # Successful check-in
    now = get_now().isoformat()
    user_data = data.setdefault(str(user.id), {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
    user_data['checkins'].append(now)
    save_data(data)
    
    formatted_time = format_time(now)
    activity_count = len(recent_messages)
    
    embed = discord.Embed(title="✅ Check-in Successful!", color=0x00ff00)
    embed.add_field(name="🕐 Time", value=formatted_time, inline=False)
    embed.add_field(name="📝 Recent Activity", value=f"You sent {activity_count} message(s) in monitored channels", inline=False)
    embed.add_field(name="⏰ Next Check-in", value="Available in 25 minutes", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='my_stats', help='See your own mod stats')
async def my_stats(ctx):
    user = ctx.author
    user_data = data.get(str(user.id), {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
    total_shifts = len(user_data['shifts'])
    missed = len(user_data['missed'])
    checkins = len(user_data['checkins'])
    recent_activity = len([msg for msg in user_data.get('recent_messages', []) 
                          if (get_now() - datetime.fromisoformat(msg['timestamp'])) <= timedelta(minutes=25)])
    
    embed = discord.Embed(title=f"📊 Stats for {user.display_name}", color=0x00ff00)
    embed.add_field(name="🔄 Total Shifts", value=str(total_shifts), inline=True)
    embed.add_field(name="✅ Successful Check-ins", value=str(checkins), inline=True)
    embed.add_field(name="❌ Missed Check-ins", value=str(missed), inline=True)
    embed.add_field(name="📝 Recent Activity (25min)", value=f"{recent_activity} messages", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='admin_stats', help='Get detailed stats for varunkumar00 (admin only)')
async def admin_stats(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send('❌ You need administrator permissions to use this command.')
        return
    
    # Find user by username
    target_user = None
    for member in ctx.guild.members:
        if member.name == 'varunkumar00' or member.display_name == 'varunkumar00':
            target_user = member
            break
    
    if not target_user:
        await ctx.send('❌ User varunkumar00 not found in this server.')
        return
    
    user_data = data.get(str(target_user.id), {'shifts': [], 'missed': [], 'checkins': [], 'recent_messages': []})
    
    embed = discord.Embed(title=f"👑 Admin Report: {target_user.display_name}", color=0xff6b6b)
    embed.set_thumbnail(url=target_user.display_avatar.url)
    
    # Overall stats
    total_shifts = len(user_data['shifts'])
    total_checkins = len(user_data['checkins'])
    total_missed = len(user_data['missed'])
    recent_activity = len([msg for msg in user_data.get('recent_messages', []) 
                          if (get_now() - datetime.fromisoformat(msg['timestamp'])) <= timedelta(minutes=25)])
    
    embed.add_field(name="📈 Overall Stats", value=f"🔄 Shifts: {total_shifts}\n✅ Check-ins: {total_checkins}\n❌ Missed: {total_missed}\n📝 Recent Activity: {recent_activity} msgs", inline=False)
    
    # Recent shifts (last 5)
    if user_data['shifts']:
        recent_shifts = user_data['shifts'][-5:]  # Last 5 shifts
        shifts_text = ""
        for i, shift in enumerate(reversed(recent_shifts), 1):
            start_time = format_time(shift['start'])
            end_time = format_time(shift['end']) if shift['end'] else "🔄 **ONGOING**"
            shifts_text += f"**Shift {i}:**\n🟢 Start: {start_time}\n🔴 End: {end_time}\n\n"
        
        embed.add_field(name="📅 Recent Shifts", value=shifts_text, inline=False)
    
    # Recent check-ins (last 10)
    if user_data['checkins']:
        recent_checkins = user_data['checkins'][-10:]  # Last 10 check-ins
        checkins_text = ""
        for checkin in reversed(recent_checkins):
            checkin_time = format_time(checkin)
            checkins_text += f"✅ {checkin_time}\n"
        
        embed.add_field(name="⏰ Recent Check-ins", value=checkins_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='weekly_report', help='Get weekly report for all mods (admin only)')
async def weekly_report(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send('❌ You need administrator permissions to use this command.')
        return
    now = get_now()
    week_ago = now - timedelta(days=7)
    
    embed = discord.Embed(title="📊 Weekly Mod Report", description="Last 7 days", color=0x3498db)
    
    for mod_id, mod_data in data.items():
        user = ctx.guild.get_member(int(mod_id))
        if not user:
            continue
        missed = [m for m in mod_data.get('missed', []) if datetime.fromisoformat(m) > week_ago]
        checkins = [c for c in mod_data.get('checkins', []) if datetime.fromisoformat(c) > week_ago]
        
        embed.add_field(
            name=f"👤 {user.display_name}", 
            value=f"✅ Check-ins: {len(checkins)}\n❌ Missed: {len(missed)}", 
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='help_mod', help='Show all mod commands')
async def help_mod(ctx):
    help_text = """
**🤖 Mod Bot Commands:**

**📋 Basic Commands:**
`*shift_start` - Start your mod shift
`*shift_end` - End your mod shift  
`*checkin` - Check in (must be active in monitored channels)
`*my_stats` - See your own stats

**👑 Admin Commands:**
`*weekly_report` - Get weekly report for all mods
`*admin_stats` - Get detailed stats for varunkumar00

**🔧 Utility:**
`*help_mod` - Show this help message
`*ping` - Test if bot is working

**⚠️ Check-in Rules:**
• Must send messages in monitored channels within 25 minutes
• Can only check-in once every 25 minutes
• Bot tracks your activity automatically
    """
    await ctx.send(help_text)

@bot.command(name='ping', help='Test if bot is working')
async def ping(ctx):
    await ctx.send('🏓 Pong! Mod bot is working!')

if __name__ == '__main__':
    bot.run(TOKEN) 