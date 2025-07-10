# 🚀 Deploy Discord Mod Bot to Render.com

## **Step-by-Step Deployment Guide**

### **Step 1: Create GitHub Repository**

1. **Go to [GitHub.com](https://github.com)** and sign in
2. **Click "New repository"**
3. **Name it:** `discord-mod-bot`
4. **Make it Public** (Render.com needs access)
5. **Click "Create repository"**

### **Step 2: Upload Your Code**

1. **In your new repository, click "Add file" → "Upload files"**
2. **Drag and drop ALL files from your `bot` folder:**
   - `bot.py`
   - `requirements.txt`
   - `render.yaml`
   - `README.md`
   - `.gitignore`
3. **Click "Commit changes"**

### **Step 3: Deploy on Render.com**

1. **Go to [Render.com](https://render.com)** and sign up/log in
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub account** (if not already connected)
4. **Select your repository:** `discord-mod-bot`
5. **Configure the service:**
   - **Name:** `discord-mod-bot`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
6. **Click "Create Web Service"**

### **Step 4: Set Environment Variable**

1. **In your Render dashboard, click on your service**
2. **Go to "Environment" tab**
3. **Add environment variable:**
   - **Key:** `DISCORD_TOKEN`
   - **Value:** `YOUR_DISCORD_BOT_TOKEN_HERE`
4. **Click "Save Changes"**

### **Step 5: Deploy**

1. **Click "Manual Deploy" → "Deploy latest commit"**
2. **Wait for deployment to complete** (2-3 minutes)
3. **Check the logs** - you should see:
   ```
   Mod bot logged in as shiftlog
   ✅ Check-in reminder system started!
   ```

---

## **✅ Success Indicators**

- **Bot shows as online** in your Discord server
- **Logs show:** "Logged in as shiftlog"
- **Commands work:** Try `*ping` in Discord
- **No error messages** in Render logs

---

## **🔧 Troubleshooting**

### **If bot doesn't connect:**
1. Check Render logs for errors
2. Verify Discord token is correct
3. Make sure bot has proper permissions

### **If commands don't work:**
1. Check if bot is online in Discord
2. Verify bot has "Use Slash Commands" permission
3. Try `*ping` to test basic functionality

### **If deployment fails:**
1. Check that all files are uploaded to GitHub
2. Verify `requirements.txt` is correct
3. Check Render logs for specific errors

---

## **🎉 Your Bot is Now Live 24/7!**

- **Runs continuously** even when your PC is off
- **Automatic restarts** if it crashes
- **Free hosting** (with limitations)
- **Easy updates** - just push to GitHub

---

## **📝 Next Steps**

1. **Test all commands** in your Discord server
2. **Assign the "shitty mod" role** to your moderators
3. **Share the mod guide** with your team
4. **Monitor the logs** occasionally to ensure it's working

---

**Need help? Check the Render logs or ask for assistance!** 