"""
Monitor for detecting job changes in LinkedIn profiles
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobChangeMonitor:
    """Detects and tracks job changes in monitored profiles"""
    
    def __init__(self):
        self.db = Database()
    
    def detect_changes(self, scraped_data: Dict) -> Optional[Dict]:
        """
        Compare scraped data with stored data to detect job changes
        
        Returns:
            Dict with change details if change detected, None otherwise
        """
        profile_url = scraped_data.get("url")
        if not profile_url:
            logger.error("Profile URL missing from scraped data")
            return None
        
        # Get existing profile from database
        stored_profile = self.db.get_profile(profile_url)
        
        # If this is a new profile, save it but don't report as change
        if not stored_profile:
            logger.info(f"New profile detected: {scraped_data.get('name')}")
            self.db.save_profile(scraped_data)
            return None
        
        # Check for job changes
        old_position = stored_profile.get("current_position")
        old_company = stored_profile.get("current_company")
        new_position = scraped_data.get("current_position")
        new_company = scraped_data.get("current_company")
        
        # Detect if there's a meaningful change
        position_changed = (
            old_position and new_position and 
            old_position != new_position
        )
        
        company_changed = (
            old_company and new_company and 
            old_company != new_company
        )
        
        if position_changed or company_changed:
            change_data = {
                "profile_url": profile_url,
                "name": scraped_data.get("name"),
                "old_position": old_position,
                "old_company": old_company,
                "new_position": new_position,
                "new_company": new_company,
                "detected_at": datetime.now().isoformat()
            }
            
            # Save the change to database
            self.db.save_job_change(change_data)
            
            # Update the profile with new data
            self.db.save_profile(scraped_data)
            
            logger.info(f"Job change detected for {scraped_data.get('name')}")
            logger.info(f"  Old: {old_position} at {old_company}")
            logger.info(f"  New: {new_position} at {new_company}")
            
            return change_data
        
        else:
            # No change detected, just update last_updated timestamp
            self.db.save_profile(scraped_data)
            logger.info(f"No change detected for {scraped_data.get('name')}")
            return None
    
    def process_scrape_results(self, results: List[Dict]) -> List[Dict]:
        """
        Process multiple scraped profiles and detect all changes
        
        Returns:
            List of detected changes
        """
        changes = []
        
        for profile_data in results:
            # Save scrape history
            self.db.save_scrape_history(
                profile_url=profile_data.get("url"),
                success=True,
                raw_data=profile_data
            )
            
            # Detect changes
            change = self.detect_changes(profile_data)
            if change:
                changes.append(change)
        
        return changes
    
    def get_pending_notifications(self) -> List[Dict]:
        """Get all job changes that haven't been notified"""
        return self.db.get_unnotified_changes()
    
    def mark_notified(self, change_id: int):
        """Mark a change as notified"""
        self.db.mark_change_notified(change_id)
    
    def get_profile_history(self, profile_url: str) -> List[Dict]:
        """Get job change history for a specific profile"""
        return self.db.get_job_changes_history(profile_url)
    
    def get_all_changes(self) -> List[Dict]:
        """Get all job changes"""
        return self.db.get_job_changes_history()
    
    def get_monitored_profiles(self) -> List[str]:
        """Get all active monitored profile URLs"""
        return self.db.get_monitored_profiles()


def format_change_message(change: Dict) -> str:
    """Format a job change into a readable message"""
    name = change.get("name", "Unknown")
    old_pos = change.get("old_position", "Unknown")
    old_comp = change.get("old_company", "Unknown")
    new_pos = change.get("new_position", "Unknown")
    new_comp = change.get("new_company", "Unknown")
    profile_url = change.get("profile_url", "")
    
    message = f"""
🔔 Job Change Detected!

Name: {name}
Profile: {profile_url}

Previous Position:
  • {old_pos}
  • {old_comp}

New Position:
  • {new_pos}
  • {new_comp}

Detected at: {change.get("detected_at", "Unknown")}
"""
    return message.strip()


# Example usage
if __name__ == "__main__":
    monitor = JobChangeMonitor()
    
    # Simulate scraped data
    test_data = {
        "url": "https://www.linkedin.com/in/test-profile/",
        "name": "John Doe",
        "headline": "Senior Software Engineer",
        "current_position": "Staff Engineer",
        "current_company": "New Tech Inc",
        "experience": [
            {"title": "Staff Engineer", "company": "New Tech Inc"}
        ]
    }
    
    change = monitor.detect_changes(test_data)
    if change:
        print(format_change_message(change))
    else:
        print("No changes detected")
