# Groq API Setup Guide

## Step 1: Get Your Free API Key (2 minutes)

1. Go to https://console.groq.com
2. Sign up with Google/GitHub (free, no credit card needed)
3. Click "API Keys" in the left sidebar
4. Click "Create API Key"
5. Copy the key (starts with `gsk_...`)

## Step 2: Set Environment Variable

### Windows (PowerShell):

```powershell
# Temporary (current session only)
$env:GROQ_API_KEY="gsk_your_key_here"

# Permanent (recommended)
[System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', 'gsk_your_key_here', 'User')
```

### Windows (Command Prompt):

```cmd
setx GROQ_API_KEY "gsk_your_key_here"
```

### Verify it's set:

```powershell
echo $env:GROQ_API_KEY
```

## Step 3: Install Dependencies

```bash
pip install groq
```

## Step 4: Test Groq Integration

```bash
python jarvis_core/groq_ai.py
```

You should see AI routing results for test commands!

## Step 5: Run Jarvis

```bash
# Terminal mode
python main.py

# Web UI mode
python server.py
# Then: http://localhost:8000
```

## What Changed?

✅ **Before**: Keyword matching (`if "play" in command`)
✅ **After**: AI understanding with Groq

**Example**:

```
User: "I want to listen to some chill music"
Before: No match (no "play" keyword) → WebAgent
After: AI understands intent → MediaAgent ✓
```

## Free Tier Limits

- **Requests**: 14,400 per day (plenty!)
- **Tokens**: Up to 6,000 tokens per request
- **Speed**: 70+ tokens/second (faster than local!)
- **Models**: Llama 3.1, Mixtral, Gemma

## Troubleshooting

### Error: "GROQ_API_KEY not found"

- Make sure you set the environment variable
- Restart your terminal/IDE after setting it
- Check with: `echo $env:GROQ_API_KEY`

### Error: "API key invalid"

- Regenerate key at console.groq.com
- Make sure you copied the full key (starts with `gsk_`)

### Fallback Mode

If Groq fails, Jarvis automatically falls back to keyword matching.
Check `jarvis_security.log` for details.

## Alternative: Use .env File (Optional)

Create a `.env` file in your project root:

```env
GROQ_API_KEY=gsk_your_key_here
```

Install python-dotenv:

```bash
pip install python-dotenv
```

Update `groq_ai.py`:

```python
from dotenv import load_dotenv
load_dotenv()  # Add at top of file
```

## Next Steps

Once Groq is working:

1. Try complex commands: "Help me understand this error"
2. Add a CodeAgent for code explanation
3. Integrate with vision (screenshot debugging)

Enjoy your AI-powered Jarvis! 🚀
