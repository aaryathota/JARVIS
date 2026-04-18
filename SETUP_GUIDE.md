# JARVIS Voice Assistant - Setup Guide

This guide will help you configure all necessary credentials and dependencies for JARVIS.

## Installation Steps

### 1. Clone or Download the Repository
```bash
git clone https://github.com/yourusername/JARVIS-Voice-Assistant.git
cd JARVIS-Voice-Assistant
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Credentials

Copy or rename `credentials.json` and fill in your API keys and credentials:

```bash
cp credentials.json credentials_backup.json
```

Edit `credentials.json` and add your credentials (see detailed instructions below).

---

## Detailed Credential Setup

### Groq API Key (Required)
1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key to `credentials.json`:
```json
"groq_api_key": "your_key_here"
```

### Instagram Credentials (Required for Instagram features)
1. Use your Instagram username and password
2. Add them to `credentials.json`:
```json
"instagram_username": "your_username",
"instagram_password": "your_password"
```
⚠️ **Note:** Instagram may require app-specific passwords or OTP setup.

### Google OAuth (Required for Gmail, YouTube, Calendar)
1. Visit [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable these APIs:
   - Gmail API
   - YouTube Data API v3
   - Google Calendar API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download as JSON file
6. Copy the contents into the `"installed"` field in `credentials.json`

### Spotify API (Optional - for music features)
1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Get Client ID and Client Secret
4. Add to `credentials.json`:
```json
"spotify_client_id": "your_client_id",
"spotify_client_secret": "your_client_secret"
```

### Weather API (Optional - for weather features)
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free API key
3. Add to `credentials.json`:
```json
"weather_api_key": "your_api_key"
```

### ElevenLabs API (Optional - for premium text-to-speech)
1. Visit [ElevenLabs](https://elevenlabs.io)
2. Sign up and get API key
3. Add to `credentials.json`:
```json
"elevenlabs_api_key": "your_api_key"
```

---

## Running JARVIS

### Start the Voice Assistant
```bash
python main.py
```

The assistant will start listening for voice commands.

### Access the Dashboard
Once the assistant is running, open your browser and go to:
```
http://localhost:5000
```

You'll see a real-time dashboard with:
- System stats (CPU, memory, disk usage)
- Active alerts and reminders
- Recent events
- Workflow status

---

## Voice Commands Examples

### System Commands
- "What are my stats?" - Get CPU/memory/disk usage
- "Show me the dashboard" - Open web dashboard
- "Create workflow" - Build automated command chains

### Productivity Commands
- "Show my calendar" - Display upcoming events
- "What's on my agenda?" - Get today's tasks
- "Send an email" - Compose and send email
- "Set a reminder" - Create a timed reminder

### Content Creation
- "Create video ideas" - Generate video concepts
- "Download video from [URL]" - Save YouTube videos
- "Upload to Instagram" - Share content to Instagram

### Information
- "What's the weather?" - Get weather forecast
- "Search the web for [query]" - Web search
- "Tell me the news" - Get latest news

---

## Troubleshooting

### "ModuleNotFoundError"
Install missing packages:
```bash
pip install -r requirements.txt
```

### "Authentication failed"
- Check credentials in `credentials.json`
- Ensure API keys are valid and not expired
- For Google APIs, regenerate OAuth tokens

### "No module named 'pyttsx3'"
On macOS, you may need to install additional dependencies:
```bash
brew install espeak
```

### "Dashboard not accessible"
- Ensure Flask is running (should auto-start with main.py)
- Check if port 5000 is available
- Try accessing `http://127.0.0.1:5000` instead

### Microphone Issues
- Check system microphone permissions
- On Windows, ensure microphone is the default device
- Test with: `python -c "import speech_recognition; print(speech_recognition.Microphone().name)"`

---

## Project Structure

```
JARVIS-Voice-Assistant/
├── main.py                  # Main voice assistant
├── credentials.json         # Your API keys (edit this)
├── requirements.txt         # Python dependencies
├── README.md               # Project overview
├── workflow_manager.py      # Workflow creation/execution
├── system_stats.py         # System monitoring
├── alerts_manager.py       # Alert management
├── event_tracker.py        # Event logging
├── dashboard_server.py     # Flask API server
├── ui/
│   └── dashboard.html      # Web dashboard
├── workflows.json          # Saved workflows
├── calendar_manager.py     # Calendar integration
├── memory.py              # Conversation memory
├── ai.py                  # AI intent detection
└── ... (45+ more feature modules)
```

---

## Features Overview

JARVIS includes 50+ features:

**Core Features:**
- Voice command recognition and execution
- Natural language understanding via Groq LLM
- Persistent conversation memory
- Multi-modal operation (voice, text, commands)

**Productivity:**
- Calendar management
- Email automation
- Task/Todo management
- Reminder system
- Event tracking

**Content Creation:**
- YouTube video download/upload
- Instagram Reels creation and upload
- Video automation and editing
- Content ideas generation

**System Control:**
- Real-time system monitoring
- Process management
- File operations
- Website automation

**Automation:**
- Workflow creation and execution
- Custom command chains
- Scheduled tasks
- Alert management

**Information:**
- Web search
- News aggregation
- Weather forecasts
- Location services

---

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `credentials.json` to version control
- Use `.gitignore` to prevent accidental commits
- Keep API keys private and rotate them regularly
- Use strong passwords for social media accounts
- Enable 2FA on accounts with sensitive data

---

## Support & Contributing

For issues, suggestions, or contributions:
1. Check existing issues on GitHub
2. Create detailed bug reports with error messages
3. Follow the coding style in existing modules
4. Test your changes before submitting

---

## License

This project is provided as-is for personal use and learning purposes.

---

**Happy automating with JARVIS! 🚀**
