# Discord Mod Team Bot

## Features
- Shift logging for mods
- 25-minute check-in system
- Monitors user messages in specified channels
- Weekly admin reports
- Self-stats for mods
- Auto-creates the 'shitty mod' role and 'mod-shift-logs' channel if missing
- Persists data in `mod_data.json` (excluded from git)

## Setup
1. **Clone this repo**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your Discord bot and get the token:**
   - Go to https://discord.com/developers/applications
   - Create a new application and bot
   - Copy the bot token

4. **Set environment variable:**
   - On your local machine: `export DISCORD_TOKEN=your_token_here`
   - On Render.com: Add `DISCORD_TOKEN` in the environment variables section

## Deployment (Render.com)
1. Go to https://render.com
2. Click "New +" > "Web Service"
3. Connect your GitHub repo or upload the code
4. Set the build command to `pip install -r requirements.txt`
5. Set the start command to `python bot.py`
6. Add environment variable: `DISCORD_TOKEN`
7. Deploy!

## Configuration
- The bot will create necessary channels and roles if missing.
- Make sure the bot has permission to manage roles, channels, and read/send messages.

## Data Persistence
- All mod activity is logged in `mod_data.json` (auto-created, excluded from git).

## Next Steps
- Use `/shift_start` and `/shift_end` to log shifts.
- Mods will receive check-in reminders every 25 minutes during their shift.
- Admins can use `/weekly_report` for stats.
- Mods can use `/my_stats` for personal stats. 