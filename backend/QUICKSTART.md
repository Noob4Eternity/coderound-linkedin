# 🚀 Quick Start Guide

## Installation (Choose One Method)

### Method 1: Automated Setup (Recommended)
```bash
./setup.sh
```

### Method 2: Manual Setup
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# 2. Install packages
pip install --upgrade pip
pip install -r requirements.txt

# 3. Install browser
playwright install chromium

# 4. Configure
cp .env.example .env
nano .env  # Add your credentials
```

## Verify Installation
```bash
python verify_setup.py
```

## Configuration

### 1. Edit `.env` file:
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

### 2. Edit `config.py` - Add profiles to monitor:
```python
PROFILES_TO_MONITOR = [
    "https://www.linkedin.com/in/profile-username/",
]
```

## Usage

```bash
# Start continuous monitoring (runs 24/7)
python main.py

# Run single check (test it works)
python main.py once

# Check status
python main.py status

# Test email notifications
python main.py test-email

# Show help
python main.py help
```

## What to Expect

1. **First Run**: Browser will open (if headless=false), login to LinkedIn
2. **Scraping**: Visits each profile, extracts job info (takes ~5-10 sec per profile)
3. **Detection**: Compares with database, detects job changes
4. **Notification**: Alerts you via console/email if changes found
5. **Scheduling**: Repeats every 24 hours (configurable)

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Playwright executable not found"
```bash
playwright install chromium
```

### Login fails / CAPTCHA
- Set `HEADLESS=false` in `.env` to solve CAPTCHA manually
- Wait 24 hours if account is rate-limited
- Use an established LinkedIn account

### No changes detected on first run
- This is normal! Database is being initialized
- Changes will be detected on subsequent runs

## File Structure

```
coderound-linkedin/
├── main.py              # Main entry point
├── scraper.py           # Browser automation
├── monitor.py           # Change detection
├── notifier.py          # Notifications
├── database.py          # Data storage
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── setup.sh            # Setup script
├── verify_setup.py     # Verification script
├── .env.example        # Config template
└── README.md           # Full documentation
```

## Dependencies (Verified Versions)

All packages use compatible versions that work together:
- Python 3.8+
- playwright 1.40.0+
- beautifulsoup4 4.12.0+
- pydantic 2.5.0+
- pydantic-settings 2.1.0+
- schedule 1.2.0+

## Safety Tips

⚠️ **This violates LinkedIn's Terms of Service**

- Start with 3-5 profiles
- Use delays of 3-8 seconds between profiles
- Check once daily, not hourly
- Don't run from VPN/datacenter IPs
- Use an established LinkedIn account
- Monitor logs for errors

## Support

- Full docs: `README.md`
- Installation help: `INSTALL.md`
- Run verification: `python verify_setup.py`

---

**Ready to start? Run:** `python main.py once`
