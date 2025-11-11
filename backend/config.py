"""
Configuration management for LinkedIn Job Change Monitor
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LinkedIn Credentials
    linkedin_email: str = ""
    linkedin_password: str = ""
    
    # Supabase Database
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""
    
    # Notification Settings
    notification_email: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Scraper Settings
    headless: bool = False  # Set to False to see the browser
    check_interval_hours: int = 24
    request_delay_min: int = 3
    request_delay_max: int = 8
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Profile URLs to monitor - DEPRECATED
# Profiles are now managed in the 'monitored_profiles' table in Supabase
# Use 'python main.py add-profile <url>' to add profiles
# Use 'python main.py list-profiles' to see monitored profiles
PROFILES_TO_MONITOR = [
    # This list is kept for backward compatibility but is no longer used
    # The scraper now reads from the monitored_profiles table in Supabase
]

# Database configuration
DB_PATH = Path(__file__).parent / "linkedin_monitor.db"

# Browser configuration for anti-detection
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
]

# User agent rotation (realistic, current user agents)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# LinkedIn page selectors (may need updates if LinkedIn changes their HTML)
# These are common selectors as of 2025
SELECTORS = {
    # Login page
    "login_email": "#username",
    "login_password": "#password",
    "login_submit": "button[type='submit']",

    # Profile page - more specific selectors
    "profile_name": "h1.text-heading-xlarge",
    "profile_headline": "div.text-body-medium.break-words",

    # Experience section - more specific targeting
    "experience_section": "section[data-section='experience']",
    "experience_items": "li.SwMyfGYulRUEClwQVbSRKsXKgVQVHDFaUaMqk, li.MzjpHdcObydiKPkALjQSraktPAEXLhIfzk, section[data-section='experience'] li.artdeco-list__item",
    "job_title": "span[aria-hidden='true']",
    "company_name": "span.t-14.t-normal span[aria-hidden='true']",

    # Alternative selectors (fallback) - more specific
    "alt_experience_items": "div#experience div.pv-entity__summary-info",
    "alt_job_title": "h3.t-16.t-black.t-bold",
    "alt_company_name": "p.pv-entity__secondary-title.t-14.t-black.t-normal",

    # Even more specific fallbacks
    "fallback_experience": "div.pvs-entity__sub-components, div.pv-profile-section__card-item",
    "fallback_job_title": "span[aria-hidden='true']",
    "fallback_company": "span.t-14.t-normal span[aria-hidden='true']",
}

# Initialize settings
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Could not load settings from .env file: {e}")
    print("Using default settings. Create a .env file to customize.")
    settings = Settings()
