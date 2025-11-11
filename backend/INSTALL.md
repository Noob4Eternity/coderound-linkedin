# Installation Guide

## Quick Setup (Recommended)

### Option 1: Automated Setup (macOS/Linux)

```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup (All Platforms)

Follow these steps carefully:

#### 1. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

#### 2. Upgrade pip (Important!)

```bash
pip install --upgrade pip
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**If you get version conflicts, try installing individually:**

```bash
# Core packages
pip install playwright>=1.40.0
pip install beautifulsoup4>=4.12.0
pip install lxml>=4.9.0
pip install schedule>=1.2.0

# Configuration
pip install python-dotenv>=1.0.0
pip install pydantic>=2.5.0
pip install pydantic-settings>=2.1.0

# Optional
pip install fake-useragent>=1.4.0
```

#### 4. Install Playwright Browser

```bash
playwright install chromium
```

This downloads the Chromium browser (~300MB). Only needs to be done once.

#### 5. Configure Environment

```bash
# Copy example to create your config
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
code .env
```

**Required settings in .env:**
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_actual_password
```

**Optional email settings:**
```env
NOTIFICATION_EMAIL=alerts@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

#### 6. Add Profiles to Monitor

Edit `config.py` and add LinkedIn profile URLs:

```python
PROFILES_TO_MONITOR = [
    "https://www.linkedin.com/in/example-profile-1/",
    "https://www.linkedin.com/in/example-profile-2/",
]
```

## Verify Installation

Test that everything is installed correctly:

```bash
# Check Python packages
pip list | grep -E "playwright|beautifulsoup|schedule|pydantic"

# Test import
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')"
python -c "from bs4 import BeautifulSoup; print('✅ BeautifulSoup OK')"
python -c "import schedule; print('✅ Schedule OK')"
python -c "from pydantic_settings import BaseSettings; print('✅ Pydantic OK')"

# Test the application
python main.py help
```

## Common Issues

### Issue: "Import pydantic_settings could not be resolved"

**Solution:**
```bash
pip install pydantic-settings
```

### Issue: "playwright._impl._api_types.Error: Executable doesn't exist"

**Solution:**
```bash
playwright install chromium
```

### Issue: Version conflicts with pydantic

**Solution:**
```bash
pip install --upgrade pydantic pydantic-settings
```

### Issue: Permission errors on macOS

**Solution:**
```bash
chmod +x setup.sh
```

### Issue: Can't find module config

**Solution:** Make sure you're running from the project directory:
```bash
cd /Users/veddatar/Desktop/projects/coderound-linkedin
python main.py
```

## Test Your Setup

1. **Test email configuration:**
   ```bash
   python main.py test-email
   ```

2. **Run a single check:**
   ```bash
   python main.py once
   ```

3. **Check status:**
   ```bash
   python main.py status
   ```

## Package Versions (Verified Compatible)

These versions are tested and compatible:

- Python: 3.8+
- playwright: 1.40.0+
- beautifulsoup4: 4.12.0+
- lxml: 4.9.0+
- schedule: 1.2.0+
- python-dotenv: 1.0.0+
- pydantic: 2.5.0+
- pydantic-settings: 2.1.0+
- fake-useragent: 1.4.0+

## Need Help?

If you're still having issues:

1. Check Python version: `python3 --version` (should be 3.8+)
2. Make sure virtual environment is activated (you should see `(venv)` in your prompt)
3. Try reinstalling: `pip uninstall -r requirements.txt -y && pip install -r requirements.txt`
4. Check the logs: `cat linkedin_monitor.log`
