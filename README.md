# JARVIS - AI Voice Assistant

A sophisticated, voice-controlled AI assistant that combines speech recognition, advanced NLP, and 50+ integrated features for productivity, entertainment, media automation, and content creation.

## 🎯 What is JARVIS?

JARVIS is an intelligent personal assistant that responds to voice commands and executes complex tasks. It uses **Groq LLM (llama-3.3-70b)** for AI reasoning, maintains conversation memory for context-aware responses, and integrates with popular APIs (YouTube, Instagram, Gmail, Spotify, etc.) to automate workflows.

Simply speak your command and JARVIS handles the rest!

## ✨ Key Features

### 📊 Productivity (7)
- Todo/task management with priorities
- Calendar events & scheduling
- Expense tracking
- Smart reminders with time parsing
- Background email monitoring
- Daily routine automation

### 🎬 Media & Content (8)
- YouTube video download & upload
- Instagram Reels creation & upload
- YouTube Shorts automation
- Video trimming & editing
- Audio extraction & conversion
- QR code generation/scanning
- Media file processing
- Video idea generation

### 💬 Communication (4)
- Send/receive emails (Gmail)
- SMS messaging
- Smart message composition
- Email dictation support

### 🎮 Entertainment (5)
- Joke telling
- Trivia games with scoring
- 20 questions game
- Guided meditation
- Music control (Spotify)

### 💻 Developer Tools (5)
- Code explanation & analysis
- API endpoint testing
- Git command execution
- Code formatting
- Syntax error detection

### 🤖 Advanced AI (5+)
- AGI agent for task decomposition
- Persistent conversation memory
- Multi-mode operation (Work, Study, Creative, Developer)
- Context-aware intelligent routing
- Autonomous task execution

### 🌍 Utilities
- Real-time weather information
- Web browser automation
- System info & monitoring
- And more...

## 🛠 Tech Stack

- **Language**: Python 3
- **AI/LLM**: Groq API (llama-3.3-70b)
- **Speech**: SpeechRecognition, pyttsx3
- **Video**: MoviePy, yt-dlp, Pillow
- **APIs**: Google APIs, YouTube, Instagram, Spotify, WeatherAPI
- **Web**: Flask, Flask-CORS
- **Database**: SQLite, JSON

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Microphone for voice input
- Internet connection

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jarvis-voice-assistant.git
cd jarvis-voice-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `credentials.json` in the root directory with your API keys and credentials (see below)

4. Run the assistant:
```bash
python main.py
```

## 🔐 Required Credentials

Create a `credentials.json` file in the project root with the following structure. **Never commit this file to GitHub** - add it to `.gitignore`:

```json
{
  "groq_api_key": "your_groq_api_key_here",
  "instagram_username": "your_instagram_username",
  "instagram_password": "your_instagram_password",
  "installed": {
    "client_id": "your_google_client_id",
    "project_id": "your_google_project_id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your_google_client_secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

### How to Get Each Credential:

**Groq API Key**
- Visit: https://console.groq.com/keys
- Create an API key and paste it here

**Instagram Credentials**
- Use your Instagram username and password
- Note: Two-factor authentication may require additional setup

**Google OAuth (Gmail, YouTube, Calendar)**
- Go to: https://console.cloud.google.com/
- Create a project
- Enable Gmail, YouTube Data, and Google Calendar APIs
- Create OAuth 2.0 credentials (Desktop app)
- Download JSON and fill in the values above

**Optional Credentials** (add as needed):
- `spotify_client_id` & `spotify_client_secret` - For music control
- `weather_api_key` - From WeatherAPI.com (free tier available)
- `elevenlabs_api_key` - For advanced text-to-speech

## 💬 Usage Examples

Simply run the assistant and speak commands:

```bash
python main.py
```

**Voice Commands:**
- "What's the weather today?"
- "Send an email to John with subject hello"
- "Create a todo: buy groceries"
- "Upload Instagram Reels from [YouTube URL]"
- "Tell me a joke"
- "What's the latest news?"
- "Schedule a meeting tomorrow at 2 PM"

## 📁 Project Structure

```
├── main.py                 # Main entry point
├── voice.py               # Speech recognition & TTS
├── ai.py                  # AI intent detection (Groq)
├── actions.py             # Command handlers
├── conversation_memory.py # Context & history tracking
├── instagram_uploader.py  # Instagram automation
├── youtube_uploader.py    # YouTube automation
├── calendar_manager.py    # Calendar management
├── todo_manager.py        # Task management
├── weather_config.py      # Weather integration
├── requirements.txt       # Python dependencies
└── ui/                    # Web interface (optional)
```

## ⚙️ Configuration

Edit `config.py` to customize:
- Voice speed & pitch
- Default microphone device
- Language preferences
- API timeout values
- Log levels

## 🐛 Troubleshooting

**Microphone not detected:**
```bash
python -m sounddevice
```

**API authentication failed:**
- Verify credentials in `credentials.json`
- Ensure API keys have correct permissions

**Video upload fails:**
- Check internet connection
- Verify YouTube/Instagram credentials
- Ensure videos meet platform requirements

## 📝 License

MIT License - Feel free to use and modify

## 🤝 Contributing

Contributions welcome! Feel free to fork and submit pull requests.

## 📧 Support

For issues or feature requests, open a GitHub issue.

---

**Made with ❤️ - JARVIS Voice Assistant**
