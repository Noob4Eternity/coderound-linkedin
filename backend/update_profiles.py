#!/usr/bin/env python3
"""
Script to update all existing profiles in the database with the current scraper
"""
import asyncio
import logging
from datetime import datetime
from database import Database
from scraper import scrape_linkedin_profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_all_profiles():
    """Update all monitored profiles with current scraper"""
    logger.info("🔄 Starting database update for all profiles...")

    # Initialize database connection
    db = Database()

    # Get all monitored profile URLs
    profile_urls = db.get_monitored_profiles()
    logger.info(f"📊 Found {len(profile_urls)} monitored profiles to update")

    if not profile_urls:
        logger.warning("No profiles found to update")
        return

    updated_count = 0
    failed_count = 0

    for i, url in enumerate(profile_urls, 1):
        logger.info(f"🔍 Processing profile {i}/{len(profile_urls)}: {url}")

        try:
            # Scrape the profile with current scraper
            scraped_data = await scrape_linkedin_profile(url)

            if scraped_data:
                # Save updated data to database
                success = db.save_profile(scraped_data)

                if success:
                    name = scraped_data.get('name', 'Unknown')
                    current_position = scraped_data.get('current_position', 'Unknown')
                    current_company = scraped_data.get('current_company', 'Unknown')
                    experience_count = len(scraped_data.get('experience', []))

                    logger.info(f"✅ Updated: {name}")
                    logger.info(f"   Current: {current_position} at {current_company}")
                    logger.info(f"   Experience entries: {experience_count}")

                    updated_count += 1
                else:
                    logger.error(f"❌ Failed to save profile: {url}")
                    failed_count += 1
            else:
                logger.error(f"❌ Failed to scrape profile: {url}")
                failed_count += 1

        except Exception as e:
            logger.error(f"❌ Error processing {url}: {str(e)}")
            failed_count += 1

        # Add a small delay between profiles to be respectful
        if i < len(profile_urls):
            await asyncio.sleep(2)

    # Summary
    logger.info("="*60)
    logger.info("📈 UPDATE SUMMARY")
    logger.info("="*60)
    logger.info(f"Total profiles processed: {len(profile_urls)}")
    logger.info(f"Successfully updated: {updated_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Success rate: {(updated_count/len(profile_urls)*100):.1f}%")
    logger.info("="*60)


async def update_specific_profile(url: str):
    """Update a specific profile URL"""
    logger.info(f"🔍 Updating specific profile: {url}")

    db = Database()

    try:
        # Scrape the profile
        scraped_data = await scrape_linkedin_profile(url)

        if scraped_data:
            # Save to database
            success = db.save_profile(scraped_data)

            if success:
                name = scraped_data.get('name', 'Unknown')
                current_position = scraped_data.get('current_position', 'Unknown')
                current_company = scraped_data.get('current_company', 'Unknown')
                experience_count = len(scraped_data.get('experience', []))

                logger.info(f"✅ Successfully updated: {name}")
                logger.info(f"   Current position: {current_position} at {current_company}")
                logger.info(f"   Experience entries: {experience_count}")

                # Show first few experience entries
                experience = scraped_data.get('experience', [])
                if experience:
                    logger.info("   Recent experience:")
                    for i, exp in enumerate(experience[:3], 1):
                        logger.info(f"     {i}. {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}")

                return True
            else:
                logger.error("❌ Failed to save profile to database")
                return False
        else:
            logger.error("❌ Failed to scrape profile")
            return False

    except Exception as e:
        logger.error(f"❌ Error updating profile: {str(e)}")
        return False


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "all":
            logger.info("Starting update of all profiles...")
            asyncio.run(update_all_profiles())

        elif command == "profile" and len(sys.argv) > 2:
            url = sys.argv[2]
            logger.info(f"Starting update of specific profile: {url}")
            success = asyncio.run(update_specific_profile(url))
            sys.exit(0 if success else 1)

        else:
            print("Usage:")
            print("  python update_profiles.py all                    # Update all monitored profiles")
            print("  python update_profiles.py profile <url>         # Update specific profile")
            print()
            print("Examples:")
            print("  python update_profiles.py all")
            print("  python update_profiles.py profile https://www.linkedin.com/in/username")
            sys.exit(1)
    else:
        print("Usage: python update_profiles.py <command>")
        print("Commands: all, profile <url>")
        sys.exit(1)


if __name__ == "__main__":
    main()