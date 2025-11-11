"""
LinkedIn Scraper with stealth mode and anti-detection
"""
import asyncio
import random
import logging
import json
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from config import settings, SELECTORS, USER_AGENTS, BROWSER_ARGS

# Path for storing session cookies
COOKIES_FILE = Path(__file__).parent / "linkedin_cookies.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Headless LinkedIn scraper with anti-detection measures"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logged_in = False
        self.playwright_instance = None
        
    async def save_cookies(self):
        """Save session cookies to file for persistence"""
        try:
            cookies = await self.context.cookies()
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"✅ Session cookies saved to {COOKIES_FILE}")
        except Exception as e:
            logger.warning(f"Could not save cookies: {e}")
    
    async def load_cookies(self) -> bool:
        """Load saved session cookies"""
        try:
            if not COOKIES_FILE.exists():
                logger.info("No saved cookies found")
                return False
            
            with open(COOKIES_FILE, 'r') as f:
                data = json.load(f)
            
            # Handle both formats: array directly or object with 'cookies' key
            if isinstance(data, list):
                cookies = data
            elif isinstance(data, dict) and 'cookies' in data:
                cookies = data['cookies']
            else:
                logger.warning("Invalid cookies format")
                return False
            
            await self.context.add_cookies(cookies)
            logger.info(f"✅ Loaded {len(cookies)} saved cookies")
            return True
        except Exception as e:
            logger.warning(f"Could not load cookies: {e}")
            return False
    
    async def check_if_logged_in(self) -> bool:
        """Check if already logged in using saved session"""
        try:
            logger.info("Checking if already logged in...")
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=10000)
            await self.random_delay(2, 3)
            
            current_url = self.page.url
            
            # If we're still on feed and not redirected to login, we're logged in
            if "feed" in current_url and "login" not in current_url:
                logger.info("✅ Already logged in with saved session!")
                self.logged_in = True
                return True
            
            # Check for navigation bar
            nav_exists = await self.page.query_selector('.global-nav__me') or \
                        await self.page.query_selector('[data-control-name="nav.settings"]')
            
            if nav_exists:
                logger.info("✅ Already logged in (navigation detected)!")
                self.logged_in = True
                return True
            
            logger.info("Not logged in, will need to authenticate")
            return False
            
        except Exception as e:
            logger.debug(f"Login check failed: {e}")
            return False
        
    async def init_browser(self):
        """Initialize browser with stealth settings and persistent session"""
        logger.info("Initializing browser...")
        
        self.playwright_instance = await async_playwright().start()
        
        # Launch browser with persistent profile (keeps cookies, cache, etc.)
        # Create a user data directory for persistent sessions
        user_data_dir = Path(__file__).parent / ".browser_profile"
        user_data_dir.mkdir(exist_ok=True)
        
        # Launch browser with anti-detection settings
        self.browser = await self.playwright_instance.chromium.launch(
            headless=settings.headless,
            args=BROWSER_ARGS
        )
        
        # Create context with random user agent and persistent storage
        user_agent = random.choice(USER_AGENTS)
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            storage_state=str(COOKIES_FILE) if COOKIES_FILE.exists() else None,
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            // Overwrite the `navigator.webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Overwrite the `languages` property to use a custom getter
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Pass the Chrome Test
            window.chrome = {
                runtime: {},
            };
            
            // Pass the Permissions Test
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")
        
        # Try to use existing session first
        cookies_loaded = await self.load_cookies()
        if cookies_loaded:
            is_logged_in = await self.check_if_logged_in()
            if is_logged_in:
                return True
        
        # Not logged in yet
        return False
        
    async def login(self) -> bool:
        """Login to LinkedIn"""
        if not settings.linkedin_email or not settings.linkedin_password:
            logger.error("LinkedIn credentials not configured!")
            return False
            
        try:
            logger.info("Attempting to login to LinkedIn...")
            await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=15000)
            
            await self.random_delay(2, 3)
            
            # Check if we're already redirected to feed (already logged in)
            current_url = self.page.url
            if "feed" in current_url or ("linkedin.com" in current_url and "login" not in current_url and "checkpoint" not in current_url):
                logger.info(f"✅ Already logged in! Redirected to: {current_url}")
                self.logged_in = True
                await self.save_cookies()
                return True
            
            # Check for profile picker (remembered accounts) - updated selectors
            profile_picker_selectors = [
                # Modern selectors for profile picker
                'button[data-test-id="profile-card"]',
                'button[data-control-name="profile_switcher"]',
                'button.sign-in-form__profile-card-btn',
                'div.profile-card button',
                'button:has-text("Continue as")',
                'button:has-text("Continue")',
                # Legacy selectors
                'button[data-litms-control-urn*="session-profile"]',
                'button.sign-in-form__session-profile-btn',
                '[data-id*="sign-in-form__session-profile"]',
                # Generic button with profile-related text
                'button:has-text("profile")',
                'button:has-text("account")',
                # New selector based on inspection - button with user details
                'button.member-profile__details',
                # Fallback: any button containing email-like text
                'button:has-text("@")',
                'button:has-text("gmail.com")',
                'button:has-text("yahoo.com")',
                'button:has-text("hotmail.com")',
                'button:has-text("outlook.com")',
            ]
            
            profile_picked = False
            for selector in profile_picker_selectors:
                try:
                    profile_btn = await self.page.query_selector(selector)
                    if profile_btn:
                        logger.info(f"🔍 Found saved profile button, clicking to continue...")
                        await profile_btn.click()
                        profile_picked = True
                        
                        # Wait for navigation after clicking profile
                        await self.random_delay(3, 5)
                        
                        # Check if we're now logged in
                        current_url = self.page.url
                        if "feed" in current_url or ("login" not in current_url and "checkpoint" not in current_url):
                            logger.info(f"✅ Logged in via saved profile! Redirected to: {current_url}")
                            self.logged_in = True
                            await self.save_cookies()
                            return True
                        
                        break
                except Exception:
                    continue
            
            if not profile_picked:
                # No profile picker, need to fill form manually
                logger.info("No saved profile found, filling credentials manually...")
                
                # Wait for login form to be ready - try multiple selectors
                login_form_selectors = [
                    "#username",
                    "input[name='session_key']",
                    "input[type='email']",
                    "input[placeholder*='email']",
                    "input[placeholder*='Email']",
                ]
                
                email_field = None
                for selector in login_form_selectors:
                    try:
                        email_field = await self.page.wait_for_selector(selector, timeout=3000)
                        if email_field:
                            logger.info(f"Found email field with selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not email_field:
                    logger.error("Could not find email/login field!")
                    # Take screenshot for debugging
                    try:
                        await self.page.screenshot(path="login_error.png")
                        logger.info("Saved screenshot to login_error.png")
                    except:
                        pass
                    return False
                
                # Fill email - use the found field
                await self.random_delay(1, 2)
                await email_field.fill(settings.linkedin_email)
                
                # Find password field
                password_selectors = [
                    "#password",
                    "input[name='session_password']",
                    "input[type='password']",
                ]
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = await self.page.wait_for_selector(selector, timeout=3000)
                        if password_field:
                            logger.info(f"Found password field with selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not password_field:
                    logger.error("Could not find password field!")
                    return False
                
                await self.random_delay(0.5, 1.5)
                await password_field.fill(settings.linkedin_password)
                
                # Find submit button
                submit_selectors = [
                    "button[type='submit']",
                    "button:has-text('Sign in')",
                    "button:has-text('Sign In')",
                    "button[data-litms-control-urn*='login-submit']",
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = await self.page.query_selector(selector)
                        if submit_button:
                            logger.info(f"Found submit button with selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not submit_button:
                    logger.error("Could not find submit button!")
                    return False
                
                # Click submit button
                await self.random_delay(0.5, 1.5)
                await submit_button.click()
            
            # Wait for navigation with longer timeout
            logger.info("Waiting for login to complete...")
            await self.random_delay(3, 5)
            
            # Wait for any of these conditions (login success indicators)
            try:
                # Wait up to 20 seconds for navigation away from login page
                await self.page.wait_for_url(lambda url: "login" not in url, timeout=20000)
                logger.info("✅ Navigated away from login page")
            except Exception as e:
                logger.warning(f"Navigation timeout: {e}, checking current state...")
            
            # Give it more time to settle
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                logger.debug("Network idle timeout, continuing anyway...")
                
            await self.random_delay(2, 3)
            
            # Check if login was successful using multiple methods
            current_url = self.page.url
            logger.info(f"Current URL after login: {current_url}")
            
            # Check for failed login indicators first
            if "login" in current_url and "error" in current_url.lower():
                logger.error("Login failed - credentials may be incorrect")
                return False
            elif "checkpoint" in current_url or "challenge" in current_url:
                logger.error("Login blocked - CAPTCHA or verification required!")
                logger.info("Please solve the CAPTCHA in the browser window...")
                # Wait longer for user to solve CAPTCHA
                await self.random_delay(30, 35)
                current_url = self.page.url
                logger.info(f"URL after waiting: {current_url}")
            
            # Check for success indicators
            # Method 1: Check if we're no longer on login page
            if "login" not in current_url:
                logger.info(f"✅ Login successful! Redirected to: {current_url}")
                self.logged_in = True
                # Save cookies for future sessions
                await self.save_cookies()
                return True
            
            # Method 2: Check for specific LinkedIn navigation elements (more reliable)
            try:
                # Check if nav bar exists (sign of successful login)
                nav_exists = await self.page.query_selector('nav.global-nav') or \
                            await self.page.query_selector('[data-control-name="nav.settings"]') or \
                            await self.page.query_selector('.global-nav__me')
                
                if nav_exists:
                    logger.info("✅ Login successful! (Navigation bar detected)")
                    self.logged_in = True
                    # Save cookies for future sessions
                    await self.save_cookies()
                    return True
            except Exception as e:
                logger.debug(f"Navigation check error: {e}")
            
            # If still uncertain, check cookies
            cookies = await self.context.cookies()
            has_session = any(c['name'] in ['li_at', 'JSESSIONID'] for c in cookies)
            
            if has_session:
                logger.info("✅ Login successful! (Session cookies detected)")
                self.logged_in = True
                # Save cookies for future sessions
                await self.save_cookies()
                return True
            
            logger.error(f"Login status unclear - current URL: {current_url}")
            logger.info("If you're logged in visually, the scraper will continue anyway...")
            # Be more permissive - if we're not explicitly on login page, assume success
            if "login" not in current_url:
                logger.info("Assuming login successful based on URL")
                self.logged_in = True
                # Save cookies for future sessions
                await self.save_cookies()
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    async def scrape_profile(self, profile_url: str) -> Optional[Dict]:
        """Scrape a LinkedIn profile for job information"""
        if not self.logged_in:
            logger.warning("Login flag not set, but attempting to scrape anyway...")
            # Don't immediately return, try to scrape anyway
            
        try:
            logger.info(f"Scraping profile: {profile_url}")
            
            # Navigate to profile
            await self.page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            await self.random_delay(2, 3)
            
            # Check if we're redirected back to login (session expired)
            current_url = self.page.url
            if "login" in current_url or "authwall" in current_url:
                logger.error("Redirected to login page - session may have expired or profile requires login")
                logger.error("Try running again or check if profile is public")
                return None
            
            logger.info(f"Successfully navigated to: {current_url}")
            
            # Scroll to load dynamic content
            await self.scroll_page()
            
            # Get page content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # Extract profile information
            profile_data = {
                "url": profile_url,
                "scraped_at": datetime.now().isoformat(),
                "name": None,
                "headline": None,
                "current_position": None,
                "current_company": None,
                "experience": []
            }
            
            # Extract name - try multiple selectors
            name_selectors = [
                SELECTORS["profile_name"],
                "h1.text-heading-xlarge",
                "h1",
                ".pv-text-details__left-panel h1",
            ]

            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name_text = name_elem.get_text(strip=True)
                    # Skip if it looks like a post or activity
                    if len(name_text) > 3 and not any(skip in name_text.lower() for skip in ['posted', 'shared', 'liked', 'commented']):
                        profile_data["name"] = name_text
                        logger.info(f"  ✓ Name: {profile_data['name']}")
                        break

            if not profile_data["name"]:
                logger.warning("  ✗ Could not find name element")

            # Extract headline - try multiple selectors
            headline_selectors = [
                SELECTORS["profile_headline"],
                "div.text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium",
                ".pv-about__summary-text",
            ]

            for selector in headline_selectors:
                headline_elem = soup.select_one(selector)
                if headline_elem:
                    headline_text = headline_elem.get_text(strip=True)
                    # Skip if it looks like a post or activity
                    if len(headline_text) > 5 and not any(skip in headline_text.lower() for skip in ['posted', 'shared', 'liked', 'commented']):
                        profile_data["headline"] = headline_text
                        logger.info(f"  ✓ Headline: {profile_data['headline']}")
                        break

            if not profile_data["headline"]:
                logger.warning("  ✗ Could not find headline element")
            
            # Extract experience section - try multiple selector strategies
            experience_items = []

            # Debug: Print some HTML content to understand structure
            logger.info(f"🔍 Debug: HTML content length: {len(content)}")
            
            # Save HTML content to file for inspection
            with open('/Users/veddatar/Desktop/debug_linkedin.html', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("🔍 Debug: HTML content saved to /Users/veddatar/Desktop/debug_linkedin.html")
            
            logger.info(f"🔍 Debug: First 1000 chars of HTML: {content[:1000]}")

            # Strategy 1: Modern LinkedIn experience section
            experience_items = soup.select(SELECTORS["experience_items"])
            logger.info(f"  Strategy 1 - Found {len(experience_items)} experience items")

            # Strategy 2: Alternative experience selectors if first fails
            if not experience_items:
                experience_items = soup.select(SELECTORS["alt_experience_items"])
                logger.info(f"  Strategy 2 - Found {len(experience_items)} experience items")

            # Strategy 3: Fallback to broader selectors
            if not experience_items:
                experience_items = soup.select(SELECTORS["fallback_experience"])
                logger.info(f"  Strategy 3 - Found {len(experience_items)} experience items")

            # Filter out items that look like posts or activities
            filtered_items = []
            for item in experience_items:
                item_text = item.get_text().lower()
                # Skip if it contains clear post/activity indicators
                skip_indicators = [
                    'posted', 'shared a post', 'liked this', 'commented on this',
                    'reacted to', 'follow', 'connect', 'endorse', 'recommend',
                    'see all activity', 'recent activity', 'free insight', 'unlock',
                    'sales navigator', 'improve outreach', 'premium', 'upgrade',
                    'try premium', 'see more', 'view all', 'load more'
                ]
                
                if any(skip_word in item_text for skip_word in skip_indicators):
                    continue
                    
                # Skip if it's too short (likely not a job entry)
                if len(item_text.strip()) < 10:
                    continue
                    
                # Skip if it looks like a date/location only
                if any(skip_word in item_text for skip_word in ['months', 'years', 'days']) and len(item_text.strip()) < 20:
                    continue
                    
                # Look for job title patterns (contains common job title words)
                job_indicators = [
                    'president', 'manager', 'director', 'engineer', 'developer', 'analyst',
                    'consultant', 'specialist', 'coordinator', 'assistant', 'executive',
                    'officer', 'representative', 'associate', 'senior', 'junior', 'lead',
                    'head', 'chief', 'vice', 'intern', 'trainee', 'member', 'chair',
                    'committee', 'board', 'team', 'group', 'department', 'sales', 'marketing',
                    'product', 'software', 'data', 'business', 'operations', 'finance',
                    'human resources', 'hr', 'recruitment', 'placement'
                ]
                
                has_job_indicator = any(job_word in item_text for job_word in job_indicators)
                
                # Also check for company-like patterns (contains common company suffixes)
                company_indicators = [
                    'ltd', 'limited', 'inc', 'corp', 'corporation', 'llc', 'llp',
                    'pvt', 'private', 'university', 'college', 'school', 'institute',
                    'academy', 'group', 'solutions', 'systems', 'technologies', 'services',
                    'enterprises', 'industries', 'international', 'global', 'company'
                ]
                
                has_company_indicator = any(company_word in item_text for company_word in company_indicators)
                
                # Skip education-only entries
                education_indicators = ['school', 'university', 'college', 'bachelor', 'master', 'phd', 'degree']
                is_education_only = any(edu_word in item_text for edu_word in education_indicators) and not has_job_indicator
                
                # Include if it has job indicators, company indicators, or is reasonably long with dates
                if (has_job_indicator or has_company_indicator) and not is_education_only:
                    filtered_items.append(item)

            experience_items = filtered_items
            logger.info(f"  Filtered to {len(experience_items)} relevant experience items")

            # Process experience items, handling nested roles
            for i, item in enumerate(experience_items[:10], 1):  # Get first 10 positions
                # Check if this item has nested roles (multiple positions at same company)
                nested_roles = item.select('ul li')
                
                if nested_roles:
                    # This is a company with multiple roles
                    # Extract company name from the main item
                    company_spans = item.select('span[aria-hidden="true"]')
                    company_name = None
                    if company_spans:
                        # Find the span that contains the company name (not dates, not job titles)
                        for span in company_spans:
                            span_text = span.get_text().strip()
                            # Skip if it looks like a duration or date
                            if not any(skip_word in span_text.lower() for skip_word in ['yrs', 'mos', 'years', 'months', 'present', 'current', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may']):
                                # Skip if it looks like a job title (contains job indicators)
                                has_job_words = any(job_word in span_text.lower() for job_word in [
                                    'president', 'manager', 'director', 'head', 'member', 'intern'
                                ])
                                if not has_job_words and len(span_text) > 3:
                                    company_name = span_text
                                    break
                    
                    # Process each nested role
                    for role_item in nested_roles:
                        role_spans = role_item.select('span[aria-hidden="true"]')
                        if role_spans:
                            job_title = role_spans[0].get_text().strip()
                            
                            # Clean up the job title
                            if job_title:
                                job_title = ' '.join(job_title.split())
                                
                            if job_title and company_name:
                                profile_data["experience"].append({
                                    "title": job_title,
                                    "company": company_name
                                })
                                logger.info(f"  ✓ Position {len(profile_data['experience'])}: {job_title} at {company_name}")
                else:
                    # This is a single role entry - use aria-hidden spans
                    aria_spans = item.select('span[aria-hidden="true"]')
                    
                    if len(aria_spans) >= 2:
                        # Span 1: Job title, Span 2: Company name
                        job_title = aria_spans[0].get_text().strip()
                        company = aria_spans[1].get_text().strip()
                        
                        # Clean up the extracted text
                        if job_title:
                            job_title = ' '.join(job_title.split())
                            
                        if company:
                            company = ' '.join(company.split())
                            
                        # Skip if company looks like a date
                        if company and any(skip_word in company.lower() for skip_word in ['months', 'years', 'present', 'current']):
                            company = None
                            
                        if job_title and company:
                            profile_data["experience"].append({
                                "title": job_title,
                                "company": company
                            })
                            logger.info(f"  ✓ Position {len(profile_data['experience'])}: {job_title} at {company}")
                        else:
                            logger.debug(f"  ✗ Could not extract valid job title/company from single role item")
                    else:
                        logger.debug(f"  ✗ Not enough aria-hidden spans for single role item")            # Set current position (first in experience list)
            if profile_data["experience"]:
                profile_data["current_position"] = profile_data["experience"][0]["title"]
                profile_data["current_company"] = profile_data["experience"][0]["company"]
                logger.info(f"✅ Successfully scraped profile for {profile_data['name']}")
                logger.info(f"   Current role: {profile_data['current_position']} at {profile_data['current_company']}")
            else:
                logger.warning(f"⚠️  No experience data found for {profile_data['name'] or 'profile'}")
                logger.info("   This might be due to LinkedIn's HTML structure changing")
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {str(e)}")
            return None
    
    async def scrape_profiles(self, profile_urls: List[str]) -> List[Dict]:
        """Scrape multiple profiles with delays"""
        results = []
        
        for i, url in enumerate(profile_urls):
            logger.info(f"Processing profile {i+1}/{len(profile_urls)}")
            
            profile_data = await self.scrape_profile(url)
            if profile_data:
                results.append(profile_data)
            
            # Random delay between profiles
            if i < len(profile_urls) - 1:
                delay = random.randint(
                    settings.request_delay_min,
                    settings.request_delay_max
                )
                logger.info(f"Waiting {delay} seconds before next profile...")
                await asyncio.sleep(delay)
        
        return results
    
    async def scroll_page(self):
        """Scroll page to load dynamic content"""
        try:
            # Scroll down in chunks (human-like)
            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back to top
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"Error scrolling page: {str(e)}")
    
    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def close(self):
        """Close browser and save session state"""
        try:
            # Save cookies one more time before closing
            if self.context and self.logged_in:
                await self.save_cookies()
                # Also save full storage state (includes localStorage, sessionStorage, cookies)
                await self.context.storage_state(path=str(COOKIES_FILE))
                logger.info("💾 Session state saved for next run")
        except Exception as e:
            logger.debug(f"Could not save final state: {e}")
        
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright_instance:
            await self.playwright_instance.stop()
        logger.info("Browser closed")


# Convenience function for one-off scraping
async def scrape_linkedin_profiles(profile_urls: List[str]) -> List[Dict]:
    """Scrape LinkedIn profiles and return data"""
    scraper = LinkedInScraper()
    
    try:
        # Initialize browser and check for existing session
        already_logged_in = await scraper.init_browser()
        
        # Only login if not already logged in
        if not already_logged_in:
            if not await scraper.login():
                logger.error("Failed to login. Aborting scrape.")
                return []
        
        # Scrape profiles
        results = await scraper.scrape_profiles(profile_urls)
        return results
            
    finally:
        await scraper.close()


async def scrape_linkedin_profile(profile_url: str) -> Optional[Dict]:
    """Scrape a single LinkedIn profile and return data"""
    results = await scrape_linkedin_profiles([profile_url])
    return results[0] if results else None


if __name__ == "__main__":
    # Test the scraper
    from config import PROFILES_TO_MONITOR
    
    async def main():
        results = await scrape_linkedin_profiles(PROFILES_TO_MONITOR)
        
        print("\n=== Scrape Results ===")
        for profile in results:
            print(f"\nName: {profile['name']}")
            print(f"Headline: {profile['headline']}")
            print(f"Current: {profile['current_position']} at {profile['current_company']}")
    
    asyncio.run(main())
