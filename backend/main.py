"""
LinkedIn Job Change Monitor - Main Application
"""
import asyncio
import schedule
import time
import logging
from datetime import datetime
from typing import List

from config import PROFILES_TO_MONITOR, settings
from scraper import scrape_linkedin_profiles
from monitor import JobChangeMonitor
from notifier import Notifier
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInMonitor:
    """Main orchestrator for LinkedIn job change monitoring"""
    
    def __init__(self):
        self.monitor = JobChangeMonitor()
        self.notifier = Notifier()
        # Get profiles from database instead of config
        self.profiles = self.monitor.get_monitored_profiles()
        
    async def run_check(self):
        """Run a single check of all monitored profiles"""
        logger.info("="*60)
        logger.info("Starting profile check...")
        logger.info(f"Monitoring {len(self.profiles)} profiles")
        logger.info("="*60)
        
        if not self.profiles:
            logger.warning("No profiles configured to monitor!")
            logger.info("Add profile URLs using the database management functions")
            return
        
        try:
            # Scrape all profiles
            logger.info("Scraping LinkedIn profiles...")
            scraped_data = await scrape_linkedin_profiles(self.profiles)
            
            if not scraped_data:
                logger.error("No data scraped. Check your credentials and network.")
                return
            
            logger.info(f"Successfully scraped {len(scraped_data)} profiles")
            
            # Detect changes
            logger.info("Analyzing for job changes...")
            changes = self.monitor.process_scrape_results(scraped_data)
            
            if changes:
                logger.info(f"🔔 Detected {len(changes)} job change(s)!")
                
                # Send notifications
                self.notifier.notify_multiple_changes(changes, method="both")
                
                # Mark as notified
                for change in changes:
                    if 'id' in change:
                        self.monitor.mark_notified(change['id'])
            else:
                logger.info("No job changes detected")
            
            logger.info("Check completed successfully")
            
        except Exception as e:
            logger.error(f"Error during check: {str(e)}", exc_info=True)
    
    def run_once(self):
        """Run a single check (synchronous wrapper)"""
        asyncio.run(self.run_check())
    
    def start_scheduler(self):
        """Start scheduled monitoring"""
        interval_hours = settings.check_interval_hours
        
        logger.info("="*60)
        logger.info("LinkedIn Job Change Monitor Started")
        logger.info("="*60)
        logger.info(f"Monitoring {len(self.profiles)} profiles")
        logger.info(f"Check interval: Every {interval_hours} hours")
        logger.info(f"Next check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        # Run immediately on start
        self.run_once()
        
        # Schedule future runs
        schedule.every(interval_hours).hours.do(self.run_once)
        
        # Keep running
        logger.info("\nMonitor running... Press Ctrl+C to stop")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\nMonitor stopped by user")
    
    def show_status(self):
        """Display current monitoring status"""
        print("\n" + "="*60)
        print("LINKEDIN JOB CHANGE MONITOR - STATUS")
        print("="*60)
        
        # Monitored profiles
        profile_urls = self.monitor.get_monitored_profiles()
        print(f"\n📊 Monitored Profiles: {len(profile_urls)}")
        
        # Get profile data for each URL
        for i, url in enumerate(profile_urls, 1):
            profile_data = self.monitor.db.get_profile(url)
            if profile_data:
                name = profile_data.get('name', 'Unknown')
                position = profile_data.get('current_position', 'Unknown')
                company = profile_data.get('current_company', 'Unknown')
                last_updated = profile_data.get('last_updated', 'Never')
                print(f"  {i}. {name} - {position} at {company}")
                print(f"     Last updated: {last_updated}")
            else:
                print(f"  {i}. {url} (No data yet)")
        
        # Recent changes
        changes = self.monitor.get_all_changes()
        print(f"\n🔔 Recent Job Changes: {len(changes)}")
        for i, change in enumerate(changes[:5], 1):  # Show last 5
            print(f"  {i}. {change['name']}")
            print(f"     {change['old_position']} → {change['new_position']}")
            print(f"     Detected: {change['detected_at']}")
        
        # Configuration
        print(f"\n⚙️  Configuration:")
        print(f"  Check interval: {settings.check_interval_hours} hours")
        print(f"  Headless mode: {settings.headless}")
        print(f"  Email notifications: {'Enabled' if self.notifier.email_enabled else 'Disabled'}")
        
        print("\n" + "="*60 + "\n")


def main():
    """Main entry point"""
    import sys
    
    app = LinkedInMonitor()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "once":
            logger.info("Running single check...")
            app.run_once()
            
        elif command == "status":
            app.show_status()
            
        elif command == "add-profile":
            if len(sys.argv) < 3:
                print("Usage: python main.py add-profile <linkedin-url> [name]")
                return
            
            url = sys.argv[2]
            name = sys.argv[3] if len(sys.argv) > 3 else None
            
            db = Database()
            if db.add_monitored_profile(url, name):
                print(f"✅ Added profile to monitor: {url}")
            else:
                print(f"❌ Failed to add profile: {url}")
                
        elif command == "remove-profile":
            if len(sys.argv) < 3:
                print("Usage: python main.py remove-profile <linkedin-url>")
                return
            
            url = sys.argv[2]
            
            db = Database()
            if db.remove_monitored_profile(url):
                print(f"✅ Removed profile from monitoring: {url}")
            else:
                print(f"❌ Failed to remove profile: {url}")
                
        elif command == "migrate-profiles":
            logger.info("Migrating profiles from config to database...")
            
            # Import here to avoid circular imports
            from config import PROFILES_TO_MONITOR
            
            db = Database()
            migrated = 0
            
            for url in PROFILES_TO_MONITOR:
                if url and url.startswith('http'):
                    # Try to get existing profile data
                    profile_data = db.get_profile(url)
                    name = profile_data.get('name') if profile_data else None
                    
                    if db.add_monitored_profile(url, name):
                        migrated += 1
                        print(f"✅ Migrated: {url}")
                    else:
                        print(f"❌ Failed to migrate: {url}")
            
            print(f"\nMigration complete! Migrated {migrated} profiles.")
                
        elif command == "help":
            print("""
LinkedIn Job Change Monitor

Usage:
  python main.py              Start continuous monitoring
  python main.py once         Run a single check
  python main.py status       Show current status
  python main.py test-email   Test email notifications
  python main.py add-profile <url> [name]    Add profile to monitor
  python main.py remove-profile <url>        Remove profile from monitoring
  python main.py list-profiles               List monitored profiles
  python main.py migrate-profiles            Migrate profiles from config to database
  python main.py help         Show this help

Configuration:
  1. Copy .env.example to .env
  2. Add your LinkedIn credentials
  3. Add profile URLs to the monitored_profiles table in Supabase
  4. Configure email settings (optional)

For more information, see README.md
""")
        else:
            print(f"Unknown command: {command}")
            print("Use 'python main.py help' for usage information")
    else:
        # Default: start scheduler
        app.start_scheduler()


if __name__ == "__main__":
    main()
