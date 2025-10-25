# Smart Scheduler AI Agent

An intelligent meeting scheduler powered by AI that can understand natural language, handle voice conversations, and integrate with Google Calendar to find and schedule meetings.

## Features

- **Voice-Enabled Conversations**: Natural voice interactions with low latency
- **Smart Time Parsing**: Understands complex time expressions like "sometime next week" or "after my 5 PM meeting"
- **Google Calendar Integration**: Checks availability and creates events
- **Intelligent Conflict Resolution**: Suggests alternatives when requested times are unavailable
- **Real-time WebSocket Support**: For seamless voice conversations
- **Advanced Context Management**: Remembers conversation state and user preferences

## Tech Stack

- **Backend**: FastAPI with Python
- **AI/LLM**: OpenAI GPT-4 for conversation understanding
- **Voice**: OpenAI TTS/STT for speech processing
- **Calendar**: Google Calendar API
- **Real-time**: WebSocket for voice conversations
- **Deployment**: Ready for Vercel, GCP, or other cloud platforms

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Google Calendar API credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd meeting_agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv myvenv
   source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Set up Google Calendar API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials file as `credentials.json`
   - Place it in the project root

6. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### REST API

- `GET /` - API information
- `GET /health` - Health check
- `POST /message/` - Send message to chatbot
- `GET /message/context/{session_id}` - Get conversation context
- `DELETE /message/context/{session_id}` - Clear conversation context

### WebSocket Endpoints

- `WS /ws/chat/{session_id}` - Text and voice chat
- `WS /ws/voice/{session_id}` - Voice-only conversation

## Usage Examples

### Basic Text Conversation

```python
import requests

# Start a conversation
response = requests.post("http://localhost:8000/message/", json={
    "user_query": "I need to schedule a meeting",
    "session_id": "user123",
    "is_voice": False
})

print(response.json()["response"])
```

### Voice Conversation via WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/user123');

// Send text message
ws.send(JSON.stringify({
    type: "text",
    message: "I need to schedule a 1-hour meeting"
}));

// Send voice message (base64 encoded audio)
ws.send(JSON.stringify({
    type: "audio", 
    data: "base64_encoded_audio_data"
}));
```

## Advanced Features

### Smart Time Parsing

The agent understands complex time expressions:

- "sometime next week"
- "after my 5 PM meeting on Friday"
- "an hour before my flight that leaves at 6 PM"
- "the last weekday of this month"

### Conflict Resolution

When requested times are unavailable, the agent:

- Analyzes the conflicts
- Suggests alternative times
- Offers different days or time ranges
- Maintains context for follow-up questions

### Voice Capabilities

- **Speech-to-Text**: Converts user speech to text using OpenAI Whisper
- **Text-to-Speech**: Generates natural speech responses
- **Real-time Processing**: Low-latency voice conversations
- **Audio Quality Analysis**: Monitors and provides feedback on audio quality

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
TIMEZONE=UTC
WORKING_HOURS_START=9
WORKING_HOURS_END=17
DEFAULT_VOICE_ID=alloy
```

### Google Calendar Setup

1. Create a Google Cloud Project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download credentials.json
5. Run the app once to complete OAuth flow

## Deployment

### Vercel Deployment

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel --prod
   ```

3. **Set environment variables in Vercel dashboard**

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing

### Test Cases

The agent handles complex scenarios:

1. **Basic Scheduling**
   - "I need to schedule a meeting"
   - "1 hour"
   - "Tuesday afternoon"

2. **Complex Time Expressions**
   - "sometime late next week"
   - "find a time on the morning of June 20th"
   - "an hour before my 5 PM meeting on Friday"

3. **Conflict Resolution**
   - "Tuesday is fully booked. Would Wednesday morning work instead?"
   - "How about afternoon or evening times?"

4. **Changing Requirements**
   - User changes meeting duration mid-conversation
   - Agent adapts and re-searches availability

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │    │   FastAPI App    │    │  Google Calendar│
│                 │◄──►│                  │◄──►│                 │
│  - Text Input   │    │  - REST API      │    │  - Check Slots  │
│  - Voice Input  │    │  - WebSocket     │    │  - Create Events│
│  - Audio Output │    │  - Conversation  │    │                 │
└─────────────────┘    │    Engine        │    └─────────────────┘
                        │                  │
                        │  ┌─────────────┐ │
                        │  │ OpenAI APIs │ │
                        │  │ - GPT-4      │ │
                        │  │ - Whisper    │ │
                        │  │ - TTS        │ │
                        │  └─────────────┘ │
                        └──────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please open an issue on GitHub or contact the development team.
