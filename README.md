# Google Photos Meme Cleaner

An AI-powered tool that automatically detects and organizes memes in your Google Photos library, using computer vision and text recognition.

## 🌟 Features

- Automatic meme detection using AI (ResNet50) and text analysis
- Works directly with Google Photos API
- Creates organized albums for memes
- Respects Google Photos API free tier limits
- Safe dry-run mode for testing
- Progress tracking and detailed logging
- Rate limiting and quota management

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Google Account
- Google Cloud Project with Photos Library API enabled

### Google Cloud Setup

1. Create a project at [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Photos Library API
3. Configure OAuth Consent Screen:
   - Choose "External"
   - Add your email as test user
4. Create OAuth 2.0 Client ID:
   - Choose "Desktop Application"
   - Download credentials as `client_secrets.json`

### Installation

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/google-photos-meme-cleaner.git
cd google-photos-meme-cleaner
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Place your `client_secrets.json` in the `auth` directory:

```bash
mkdir -p auth
# Copy client_secrets.json to auth/
```

## 🎮 Usage

### Try it safely first (Dry Run)

```bash
python main.py --dry-run
```

### Run for real

```bash
python main.py
```

## 📝 How It Works

1. **Authentication**:

   - Uses OAuth2 for secure access to your Google Photos
   - Stores tokens securely for future use

2. **Meme Detection**:

   - Uses ResNet50 for image analysis
   - OCR for text detection in images
   - Pattern matching for meme-like text

3. **Organization**:

   - Creates dated albums for detected memes
   - Maintains original photos
   - Provides progress statistics

4. **Rate Limiting**:
   - Respects Google's free tier limits (1GB/day)
   - Automatically pauses when limit reached
   - Resumes from last position next day

## ⚠️ Important Notes

- The program creates albums but doesn't delete original photos (Google Photos API limitation)
- First run requires Google authentication via browser
- Processing large libraries may take multiple days due to API limits
- All operations are non-destructive

## 🔒 Privacy & Security

- Your Google credentials are stored locally
- No data is sent to external servers
- All processing happens on your machine
- Sensitive files are git-ignored

## 🤝 Contributing

Feel free to:

- Open issues
- Submit Pull Requests
- Suggest improvements
- Report bugs

## 📄 License

MIT License - feel free to use and modify for your needs.

## 🙏 Acknowledgments

- Google Photos API
- PyTorch and ResNet50 model
- Tesseract OCR
- All contributors and users
