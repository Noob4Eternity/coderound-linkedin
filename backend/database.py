"""
Database models and operations for LinkedIn Job Change Monitor
Using Supabase (PostgreSQL)
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from supabase import create_client, Client

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Supabase database handler for profile and job change tracking"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.init_connection()
    
    def init_connection(self):
        """Initialize Supabase connection"""
        try:
            if not settings.supabase_url or not settings.supabase_key:
                logger.error("Supabase credentials not configured in .env file!")
                logger.error("Please add SUPABASE_URL and SUPABASE_KEY to your .env file")
                raise ValueError("Supabase credentials missing")
            
            # Use service key if available (bypasses RLS), otherwise use anon key
            api_key = settings.supabase_service_key if settings.supabase_service_key else settings.supabase_key
            
            self.client = create_client(settings.supabase_url, api_key)
            logger.info("✅ Connected to Supabase database")
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def save_profile(self, profile_data: Dict) -> bool:
        """Save or update profile information"""
        try:
            data = {
                "url": profile_data["url"],
                "name": profile_data.get("name"),
                "headline": profile_data.get("headline"),
                "current_position": profile_data.get("current_position"),
                "current_company": profile_data.get("current_company"),
                "last_updated": datetime.now().isoformat()
            }
            
            # Upsert: Insert or update if URL already exists
            response = self.client.table("profiles").upsert(
                data,
                on_conflict="url"
            ).execute()
            
            logger.info(f"✅ Saved profile: {profile_data.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False
    
    def get_profile(self, profile_url: str) -> Optional[Dict]:
        """Get profile data from database"""
        try:
            response = self.client.table("profiles").select("*").eq("url", profile_url).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    def save_job_change(self, change_data: Dict) -> bool:
        """Save detected job change"""
        try:
            data = {
                "profile_url": change_data["profile_url"],
                "name": change_data.get("name"),
                "old_position": change_data.get("old_position"),
                "old_company": change_data.get("old_company"),
                "new_position": change_data.get("new_position"),
                "new_company": change_data.get("new_company"),
                "detected_at": datetime.now().isoformat(),
                "notified": False
            }
            
            response = self.client.table("job_changes").insert(data).execute()
            
            logger.info(f"✅ Saved job change for {change_data.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving job change: {e}")
            return False
    
    def get_unnotified_changes(self) -> List[Dict]:
        """Get job changes that haven't been notified"""
        try:
            response = self.client.table("job_changes")\
                .select("*")\
                .eq("notified", False)\
                .order("detected_at", desc=True)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting unnotified changes: {e}")
            return []
    
    def mark_change_notified(self, change_id: int) -> bool:
        """Mark a job change as notified"""
        try:
            response = self.client.table("job_changes")\
                .update({"notified": True})\
                .eq("id", change_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking change as notified: {e}")
            return False
    
    def save_scrape_history(self, profile_url: str, success: bool, 
                           raw_data: Optional[Dict] = None, 
                           error_message: Optional[str] = None):
        """Save scraping attempt history"""
        try:
            import json
            
            data = {
                "profile_url": profile_url,
                "scraped_at": datetime.now().isoformat(),
                "success": success,
                "raw_data": json.dumps(raw_data) if raw_data else None,
                "error_message": error_message
            }
            
            self.client.table("scrape_history").insert(data).execute()
            
        except Exception as e:
            logger.error(f"Error saving scrape history: {e}")
    
    def get_monitored_profiles(self) -> List[str]:
        """Get all active monitored profile URLs"""
        try:
            response = self.client.table("monitored_profiles")\
                .select("url")\
                .eq("active", True)\
                .execute()
            
            return [profile["url"] for profile in response.data] if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting monitored profiles: {e}")
            return []
    
    def add_monitored_profile(self, url: str, name: Optional[str] = None) -> bool:
        """Add a new profile to monitor"""
        try:
            data = {
                "url": url,
                "name": name,
                "active": True,
                "added_at": datetime.now().isoformat()
            }
            
            response = self.client.table("monitored_profiles").insert(data).execute()
            
            logger.info(f"✅ Added profile to monitor: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding monitored profile: {e}")
            return False
    
    def remove_monitored_profile(self, url: str) -> bool:
        """Remove a profile from monitoring"""
        try:
            response = self.client.table("monitored_profiles")\
                .delete()\
                .eq("url", url)\
                .execute()
            
            logger.info(f"✅ Removed profile from monitoring: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing monitored profile: {e}")
            return False
    
    def update_profile_check_time(self, url: str) -> bool:
        """Update the last checked timestamp for a profile"""
        try:
            response = self.client.table("monitored_profiles")\
                .update({"last_checked": datetime.now().isoformat()})\
                .eq("url", url)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating profile check time: {e}")
            return False
    
    def get_job_changes_history(self, profile_url: Optional[str] = None) -> List[Dict]:
        """Get job change history, optionally filtered by profile"""
        try:
            query = self.client.table("job_changes").select("*")
            
            if profile_url:
                query = query.eq("profile_url", profile_url)
            
            response = query.order("detected_at", desc=True).limit(100).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting job changes history: {e}")
            return []


# Example usage
if __name__ == "__main__":
    db = Database()
    
    # Test data
    test_profile = {
        "url": "https://www.linkedin.com/in/test-profile/",
        "name": "Test User",
        "headline": "Software Engineer",
        "current_position": "Senior Software Engineer",
        "current_company": "Tech Corp"
    }
    
    db.save_profile(test_profile)
    
    retrieved = db.get_profile(test_profile["url"])
    print(f"Retrieved profile: {retrieved}")
