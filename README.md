# LinkedIn Job Change Monitor 🔔

A headless browser-based scraper that monitors LinkedIn profiles for job changes and sends notifications when changes are detected.

## ⚠️ Important Disclaimers

- **LinkedIn Terms of Service**: This tool may violate LinkedIn's Terms of Service. Use at your own risk.
- **Account Risk**: Your LinkedIn account may be temporarily or permanently banned for using automated scrapers.
- **Legal Considerations**: Web scraping laws vary by jurisdiction. Ensure compliance with local laws.
- **Educational Purpose**: This project is for educational purposes only.

## 🚀 Features

- **Stealth Mode Scraping**: Uses Playwright with anti-detection measures
- **Job Change Detection**: Automatically detects when someone changes jobs or companies
- **Web Dashboard**: Modern React dashboard for managing monitored profiles
- **FastAPI Backend**: High-performance REST API for profile management operations
- **Supabase Database**: Cloud PostgreSQL database for tracking changes (or use SQLite locally)
- **Persistent Sessions**: Saves login cookies to avoid repeated logins
- **Email Notifications**: Get alerts via email when changes are detected
- **Scheduled Monitoring**: Run checks on a schedule (hourly, daily, etc.)
- **Human-like Behavior**: Random delays and realistic browsing patterns

## 📋 Requirements

- Python 3.8+
- Node.js 18+ (for web dashboard)
- LinkedIn account (for authentication)
- Supabase account (free tier works - [sign up here](https://supabase.com))
- SMTP credentials (optional, for email notifications)

## 🛠️ Installation

### 1. Clone or Download

```bash
cd coderound-linkedin
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

### 5. Set Up Supabase Database

**Option A: Use Supabase (Recommended - Cloud Database)**
1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Run the SQL in `supabase_schema.sql` in your Supabase SQL Editor
4. Get your credentials from Settings → API

See detailed instructions in [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

**Option B: Use SQLite (Local Database)**
- No setup needed, but not recommended for production
- Contact me if you prefer SQLite

### 6. Configure Environment

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# LinkedIn Credentials (REQUIRED)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Supabase Database (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Notification Settings (OPTIONAL)
NOTIFICATION_EMAIL=alerts@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Scraper Settings
HEADLESS=true
CHECK_INTERVAL_HOURS=24
REQUEST_DELAY_MIN=3
REQUEST_DELAY_MAX=8
```

**For Gmail:** Generate an [App Password](https://support.google.com/accounts/answer/185833) instead of using your regular password.

### 6. Configure Profiles to Monitor

**Option A: Web Dashboard (Recommended)**
1. Start the backend API: `python api.py`
2. Navigate to the frontend directory: `cd frontend`
3. Install dependencies: `npm install`
4. Configure API URL in `frontend/.env.local`: `NEXT_PUBLIC_API_BASE=http://localhost:5000`
5. Start the dashboard: `npm run dev`
6. Open [http://localhost:3000](http://localhost:3000) to manage profiles

**Option B: Manual Configuration (Legacy)**
Edit `config.py` and add LinkedIn profile URLs:

```python
PROFILES_TO_MONITOR = [
    "https://www.linkedin.com/in/example-profile-1/",
    "https://www.linkedin.com/in/example-profile-2/",
    "https://www.linkedin.com/in/example-profile-3/",
]
```

## 🎯 Usage

### Start the Web Dashboard

1. **Configure Frontend**:
```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Supabase credentials
```

2. **Start Frontend**:
```bash
cd frontend
npm install
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

**Note**: The frontend now queries Supabase directly. No backend API server required for the dashboard.

### Run Continuous Monitoring

Start the scheduler to check profiles at regular intervals:

```bash
python main.py
```

This will:
- Run an immediate check
- Schedule future checks based on `CHECK_INTERVAL_HOURS`
- Send notifications when changes are detected

### Run Single Check

Run one check and exit:

```bash
python main.py once
```

### Check Status

View current monitoring status:

```bash
python main.py status
```

### Test Email Notifications

Verify your email configuration:

```bash
python main.py test-email
```

### Get Help

```bash
python main.py help
```

## 📁 Project Structure

```
coderound-linkedin/
├── main.py              # Main application entry point
├── api.py               # FastAPI REST API for profile management
├── scraper.py           # LinkedIn scraper with Playwright
├── monitor.py           # Job change detection logic
├── notifier.py          # Notification system (email, console)
├── database.py          # Supabase database operations
├── config.py            # Configuration and settings
├── requirements.txt     # Python dependencies
├── supabase_schema.sql  # Database schema for Supabase
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Example environment configuration
├── frontend/            # Next.js web dashboard
│   ├── app/
│   │   ├── layout.tsx   # Root layout
│   │   ├── page.tsx     # Dashboard page
│   │   └── globals.css  # Global styles
│   ├── .env.local       # Frontend environment variables
│   ├── package.json     # Node.js dependencies
│   └── README.md        # Frontend documentation
├── linkedin_monitor.db  # SQLite database (created automatically)
└── linkedin_monitor.log # Application logs (created automatically)
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LINKEDIN_EMAIL` | LinkedIn login email | Required |
| `LINKEDIN_PASSWORD` | LinkedIn password | Required |
| `NOTIFICATION_EMAIL` | Email to receive alerts | Optional |
| `SMTP_SERVER` | SMTP server address | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port | 587 |
| `SMTP_USERNAME` | SMTP login username | Optional |
| `SMTP_PASSWORD` | SMTP login password | Optional |
| `HEADLESS` | Run browser in headless mode | true |
| `CHECK_INTERVAL_HOURS` | Hours between checks | 24 |
| `REQUEST_DELAY_MIN` | Min seconds between profiles | 3 |
| `REQUEST_DELAY_MAX` | Max seconds between profiles | 8 |

### Profiles to Monitor

Edit `PROFILES_TO_MONITOR` in `config.py`:

```python
PROFILES_TO_MONITOR = [
    "https://www.linkedin.com/in/username1/",
    "https://www.linkedin.com/in/username2/",
]
```

## 🛡️ Anti-Detection Features

This scraper includes several anti-detection measures:

1. **Stealth Mode**: Removes browser automation indicators
2. **Random User Agents**: Rotates between realistic user agents
3. **Human-like Delays**: Random delays between actions
4. **Realistic Scrolling**: Mimics human scrolling behavior
5. **Session Management**: Maintains login session
6. **Rate Limiting**: Configurable delays between profiles

## 📊 Database Schema

The scraper maintains several tables:

- **monitored_profiles**: Stores profiles to monitor (managed via web dashboard)
- **profiles**: Stores current profile information
- **job_history**: Tracks all detected positions
- **job_changes**: Records detected job changes
- **scrape_history**: Logs all scraping attempts

## 🚨 Troubleshooting

### Login Fails / CAPTCHA Required

- LinkedIn may show CAPTCHA if it detects automation
- Try running with `HEADLESS=false` to solve CAPTCHA manually
- Use a LinkedIn account with established history
- Reduce scraping frequency

### No Profiles Scraped

- Verify your credentials in `.env`
- Check that profile URLs are correct and public
- Ensure you're connected to the profiles (for private profiles)
- Check `linkedin_monitor.log` for errors

### Email Notifications Not Working

- Verify SMTP credentials
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Run `python main.py test-email` to test configuration
- Check firewall/network settings

### LinkedIn Account Blocked

- Wait 24-48 hours before trying again
- Reduce scraping frequency
- Use longer delays between requests
- Consider using LinkedIn's official API instead

## 🔄 How It Works

1. **Web Dashboard**: Manage monitored profiles through the React dashboard
2. **API Integration**: FastAPI serves profile data to the frontend
3. **Scraping**: Playwright browser logs into LinkedIn and visits profile pages
4. **Extraction**: BeautifulSoup parses HTML to extract job titles and companies
5. **Storage**: Supabase database stores profile snapshots
6. **Comparison**: New data is compared with stored data
7. **Detection**: Changes in position/company trigger alerts
8. **Notification**: Email and/or console notifications are sent

## 🌐 Web Dashboard

The web dashboard provides an easy-to-use interface for managing monitored profiles:

### Features
- **Profile Management**: Add, view, and remove LinkedIn profiles to monitor
- **Real-time Stats**: Dashboard showing total profiles and monitoring status
- **Direct Database Access**: Queries Supabase database directly (no API server needed)
- **Responsive Design**: Works on desktop and mobile devices
- **Type Safety**: Full TypeScript support with Supabase client

### Database Tables
The dashboard queries these Supabase tables directly:
- `monitored_profiles` - Stores profiles to monitor
- `profiles` - Stores current profile information
- `job_changes` - Records detected job changes

### Security Considerations
- **⚠️ Credentials Exposed**: Supabase keys are visible in client-side code
- **Row Level Security**: Enable RLS policies in Supabase to restrict access
- **Environment Variables**: Never commit `.env.local` to version control

### Running the Dashboard
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the dashboard.

**Note**: No backend API server required - the frontend queries Supabase directly.

## 📈 Best Practices

1. **Start Small**: Monitor 5-10 profiles initially
2. **Use Realistic Delays**: 3-8 seconds between profiles
3. **Check Infrequently**: Daily or weekly checks are safer
4. **Monitor Logs**: Review `linkedin_monitor.log` regularly
5. **Respect Rate Limits**: Don't scrape too aggressively
6. **Use Established Account**: Avoid new LinkedIn accounts

## 🔐 Security

- Never commit `.env` file to version control
- Use environment variables for sensitive data
- Store database files securely
- Consider encrypting stored credentials
- Review logs for sensitive information

## 🤝 Contributing

This is an educational project. Improvements welcome:

- Better anti-detection techniques
- More robust error handling
- Additional notification channels (Slack, Discord)
- Proxy rotation support
- Better HTML parsing

## 📝 License

This project is provided as-is for educational purposes only. Use responsibly and at your own risk.

## ⚖️ Legal Notice

This tool is intended for educational purposes only. The authors are not responsible for any misuse or violations of LinkedIn's Terms of Service. Always ensure you have proper authorization before scraping any website.

---

**Made for educational purposes only. Use responsibly! 🚀**
