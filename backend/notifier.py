"""
Notification system for job change alerts
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Notifier:
    """Handle notifications for job changes"""
    
    def __init__(self):
        self.email_enabled = bool(
            settings.smtp_username and 
            settings.smtp_password and 
            settings.notification_email
        )
        
        if not self.email_enabled:
            logger.warning("Email notifications not configured. Only console notifications will work.")
    
    def notify_change(self, change: Dict, method: str = "both"):
        """
        Send notification about a job change
        
        Args:
            change: Dict containing change information
            method: "console", "email", or "both"
        """
        message = self._format_change_message(change)
        
        if method in ["console", "both"]:
            self._console_notify(message)
        
        if method in ["email", "both"] and self.email_enabled:
            self._email_notify(change, message)
    
    def notify_multiple_changes(self, changes: List[Dict], method: str = "both"):
        """Send notifications for multiple changes"""
        if not changes:
            logger.info("No changes to notify")
            return
        
        logger.info(f"Sending notifications for {len(changes)} job changes")
        
        # For console, show each individually
        if method in ["console", "both"]:
            for change in changes:
                self._console_notify(self._format_change_message(change))
        
        # For email, can send as digest or individual
        if method in ["email", "both"] and self.email_enabled:
            if len(changes) == 1:
                self._email_notify(changes[0], self._format_change_message(changes[0]))
            else:
                self._email_digest(changes)
    
    def _console_notify(self, message: str):
        """Print notification to console"""
        print("\n" + "="*60)
        print(message)
        print("="*60 + "\n")
    
    def _email_notify(self, change: Dict, message: str):
        """Send email notification"""
        try:
            subject = f"LinkedIn Job Change: {change.get('name', 'Unknown')}"
            self._send_email(subject, message)
            logger.info(f"Email notification sent for {change.get('name')}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    
    def _email_digest(self, changes: List[Dict]):
        """Send digest email with multiple changes"""
        try:
            subject = f"LinkedIn Job Changes Digest - {len(changes)} changes detected"
            
            # Build digest message
            digest = f"Detected {len(changes)} job changes:\n\n"
            digest += "="*60 + "\n\n"
            
            for i, change in enumerate(changes, 1):
                digest += f"Change #{i}:\n"
                digest += self._format_change_message(change)
                digest += "\n" + "-"*60 + "\n\n"
            
            self._send_email(subject, digest)
            logger.info(f"Digest email sent for {len(changes)} changes")
            
        except Exception as e:
            logger.error(f"Failed to send digest email: {str(e)}")
    
    def _send_email(self, subject: str, body: str):
        """Send email via SMTP"""
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_username
        msg['To'] = settings.notification_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    
    def _format_change_message(self, change: Dict) -> str:
        """Format a job change into a readable message"""
        name = change.get("name", "Unknown")
        old_pos = change.get("old_position", "Unknown")
        old_comp = change.get("old_company", "Unknown")
        new_pos = change.get("new_position", "Unknown")
        new_comp = change.get("new_company", "Unknown")
        profile_url = change.get("profile_url", "")
        detected_at = change.get("detected_at", "Unknown")
        
        message = f"""
🔔 JOB CHANGE DETECTED!

Name: {name}
Profile: {profile_url}

PREVIOUS POSITION:
  Title: {old_pos}
  Company: {old_comp}

NEW POSITION:
  Title: {new_pos}
  Company: {new_comp}

Detected: {detected_at}
"""
        return message.strip()
    
    def test_email(self) -> bool:
        """Test email configuration"""
        if not self.email_enabled:
            logger.error("Email not configured")
            return False
        
        try:
            subject = "LinkedIn Monitor - Test Email"
            body = f"""
This is a test email from LinkedIn Job Change Monitor.

Configuration:
- SMTP Server: {settings.smtp_server}:{settings.smtp_port}
- From: {settings.smtp_username}
- To: {settings.notification_email}

Time: {datetime.now().isoformat()}

If you received this email, your notifications are working correctly!
"""
            self._send_email(subject, body)
            logger.info("Test email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Test email failed: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    notifier = Notifier()
    
    # Test notification
    test_change = {
        "profile_url": "https://www.linkedin.com/in/test-profile/",
        "name": "John Doe",
        "old_position": "Senior Software Engineer",
        "old_company": "Old Tech Corp",
        "new_position": "Staff Software Engineer",
        "new_company": "New Tech Inc",
        "detected_at": datetime.now().isoformat()
    }
    
    print("Testing console notification:")
    notifier.notify_change(test_change, method="console")
    
    if notifier.email_enabled:
        print("\nTesting email notification:")
        notifier.test_email()
    else:
        print("\nEmail not configured. Set up .env file to enable email notifications.")
