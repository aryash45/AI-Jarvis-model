# 🚀 Quick Start - Get Your Groq API Key

## Step 1: Get Free API Key (Takes 2 minutes)

1. **Visit**: https://console.groq.com
2. **Sign up**: Use Google or GitHub (no credit card needed!)
3. **Navigate**: Click "API Keys" in left sidebar
4. **Create**: Click "Create API Key" button
5. **Copy**: Copy your key (starts with `gsk_...`)

## Step 2: Set Environment Variable (Windows)

Open PowerShell and run:

```powershell
# Set the API key (replace with your actual key)
[System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', 'gsk_YOUR_KEY_HERE', 'User')
```

⚠️ **Important**: Restart your terminal/IDE after setting the variable!

### Verify it worked:

```powershell
echo $env:GROQ_API_KEY
```

You should see your key starting with `gsk_`

## Step 3: Test the Integration

```bash
# Test the Groq AI module
python jarvis_core/groq_ai.py
```

You should see test commands being routed to different agents!

## Step 4: Run Jarvis

```bash
# Start Jarvis
python main.py
```

Try saying:

- "I want to hear some relaxing music" ← AI understands intent!
- "Can you find information about Python?" ← Smarter routing!

## What Changed?

✅ **Before**: Simple keyword matching  
✅ **After**: Real AI understanding with Groq

**Example**:

```
User: "I'd like to listen to some jazz"
Before: No "play" keyword → Wrong agent
After: AI understands music intent → MediaAgent ✓
```

## Troubleshooting

### "GROQ_API_KEY not found"

- Restart your terminal/IDE after setting the variable
- Use: `[System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', 'your_key', 'User')`

### Still not working?

- Check: `echo $env:GROQ_API_KEY`
- Make sure key starts with `gsk_`
- Don't worry! Jarvis falls back to keyword matching if Groq fails

## Free Tier Limits

🎁 **14,400 requests/day** (more than enough!)  
⚡ **70+ tokens/second** (super fast!)  
💰 **$0 cost forever**

Enjoy your AI-powered Jarvis! 🎉
