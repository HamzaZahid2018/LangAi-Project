# LangAI - AI-Powered Smart Document Editor

LangAI is a full-stack Django application that provides intelligent writing assistance through NLP and AI technologies. It helps users improve their writing with real-time grammar checking, multi-language translation, plagiarism detection, text summarization, and speech-to-text conversion.

## Features

- **Grammar Checking**: Real-time error detection with auto-correction suggestions
- **Multi-Language Translation**: Support for 11 languages with online/offline modes
- **Plagiarism Detection**: TF-IDF similarity matching + AI-generated content detection + web search
- **Text Summarization**: LSA algorithm with configurable compression
- **Speech-to-Text**: Live transcription via Groq Whisper API with fallbacks
- **Document Management**: Save, export (PDF/TXT), search, and manage user documents
- **User Authentication**: Email-based OTP verification system
- **Dashboard**: Statistics and activity feed for user analytics
- **Dark/Light Theme**: Persistent theme preference with localStorage

## Tech Stack

**Backend:**
- Django 6.0.3
- Python 3.14+
- SQLite (development) / PostgreSQL (production)
- spaCy, NLTK, scikit-learn for NLP
- sumy for text summarization
- language-tool-python for grammar checking
- deep-translator for multi-language support
- PyMuPDF for PDF generation

**Frontend:**
- HTML5, Bootstrap 5.3
- Vanilla JavaScript
- Web Speech API for audio capture
- Bootstrap Icons

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/HamzaZahid2018/LangAi.git
cd LangAi/LangAIProject/langai
```

### 2. Create Environment File

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
SECRET_KEY=your-django-secret-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
GROQ_API_KEY=your-groq-api-key
```

**Note:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional - for Django Admin)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

1. **Landing Page**: Visit `http://127.0.0.1:8000/` to see the marketing page
2. **Register**: Create a new account at `/accounts/register/` - OTP will be sent to your email (printed to console in dev mode)
3. **Login**: Access your account at `/accounts/login/`
4. **Editor**: Use the main editor at `/editor/` to:
   - Check grammar
   - Translate text (11 languages)
   - Detect plagiarism
   - Summarize documents
   - Transcribe speech
5. **Dashboard**: View your statistics and activity at `/editor/dashboard/`
6. **Documents**: Manage saved documents at `/editor/documents/`

## Project Structure

```
LangAIProject/
├── langai/                      # Main Django project
│   ├── accounts/               # User authentication app
│   │   ├── models.py          # UserProfile, OTPVerification
│   │   ├── views.py           # Auth views
│   │   ├── forms.py           # Auth forms
│   │   └── urls.py            # Routing
│   │
│   ├── editor/                # Document editor app
│   │   ├── models.py          # Document, EditHistory, PlagiarismResult
│   │   ├── views.py           # Editor, dashboard, file processing
│   │   ├── ai_engine.py       # Core AI/NLP logic
│   │   ├── forms.py           # Document forms
│   │   └── urls.py            # Routing
│   │
│   ├── langai/                # Django config
│   │   ├── settings.py        # Configuration
│   │   ├── urls.py            # Root URL router
│   │   └── wsgi.py            # Production WSGI
│   │
│   ├── templates/             # HTML templates
│   ├── static/                # CSS, JavaScript
│   ├── manage.py              # Django CLI
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment template
```

## API Operations

### Grammar Check
POST to `/editor/` with:
- `text`: Input text
- `operation`: 'grammar'

### Translation
POST to `/editor/` with:
- `text`: Input text
- `operation`: 'translate'
- `target_language`: Language code (e.g., 'es', 'fr', 'ur')

### Plagiarism Detection
POST to `/editor/` with:
- `text`: Input text
- `operation`: 'plagiarism'

### Text Summarization
POST to `/editor/` with:
- `text`: Input text
- `operation`: 'summarize'
- `sentences`: Number of sentences (1-8)

### Speech-to-Text
POST to `/editor/speech/transcribe/` with audio blob

## Configuration

### Supported Languages (Translation)
- English, Urdu, Arabic, French, Spanish
- German, Chinese, Hindi, Portuguese, Russian, Turkish

### AI Engine Fallback Chain
**Grammar**: LanguageTool API → Local Server → Offline Rules
**Translation**: Google Translate API → Argostranslate (Offline)
**Speech-to-Text**: Groq Whisper → OpenAI Whisper Local → Google Speech Recognition

## Security Notes

- Never commit `.env` file (added to `.gitignore`)
- Use environment variables for all sensitive data
- Enable HTTPS in production
- Set `DEBUG=False` in production
- Use a production-grade database (PostgreSQL)
- Configure ALLOWED_HOSTS for your domain
- Use a production WSGI server (Gunicorn, uWSGI)

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL instead of SQLite
3. Configure a production WSGI server (Gunicorn)
4. Set up proper ALLOWED_HOSTS
5. Use HTTPS/SSL certificates
6. Configure static file serving (Nginx/Apache)
7. Set up a reverse proxy

Example deployment with Gunicorn:
```bash
gunicorn langai.wsgi:application --bind 0.0.0.0:8000
```

## Troubleshooting

### Email Not Sending
- Verify Gmail App Password is correct
- Check if "Less secure app access" is enabled
- Check console output for OTP codes in dev mode

### Grammar Check Not Working
- Ensure Java is installed (LanguageTool requires it)
- Check internet connection (tries online first)
- Falls back to offline rules automatically

### Audio Transcription Fails
- Verify Groq API key is set
- Check internet connection
- Falls back to local Whisper or Google Speech Recognition

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, bugs, or feature requests, please open an issue on GitHub.

## Author

Created with ❤️ by the LangAI team

---

**Note:** This is a development version. For production use, ensure all security best practices are implemented.
