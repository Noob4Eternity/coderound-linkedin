"""
LinkedIn Monitor API - FastAPI for managing monitored profiles
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import logging
from urllib.parse import unquote
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LinkedIn Monitor API",
    description="REST API for managing LinkedIn profile monitoring",
    version="1.0.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()

# Pydantic models
class ProfileResponse(BaseModel):
    url: str
    name: str
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    last_updated: Optional[str] = None
    active: bool = True

class AddProfileRequest(BaseModel):
    url: HttpUrl
    name: Optional[str] = None

class ApiResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    profiles: Optional[List[ProfileResponse]] = None
    stats: Optional[dict] = None

class StatsResponse(BaseModel):
    total_profiles: int
    total_changes: int
    last_updated: Optional[str] = None

@app.get("/api/profiles", response_model=List[ProfileResponse])
async def get_monitored_profiles():
    """Get all monitored profiles"""
    try:
        profiles = db.get_monitored_profiles()
        result = []

        for url in profiles:
            profile_data = db.get_profile(url)
            if profile_data:
                result.append(ProfileResponse(
                    url=url,
                    name=profile_data.get('name', 'Unknown'),
                    current_position=profile_data.get('current_position'),
                    current_company=profile_data.get('current_company'),
                    last_updated=profile_data.get('last_updated'),
                    active=True
                ))
            else:
                result.append(ProfileResponse(
                    url=url,
                    name='Not scraped yet',
                    active=True
                ))

        return result

    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles", response_model=dict)
async def add_monitored_profile(profile: AddProfileRequest):
    """Add a new profile to monitor"""
    try:
        url_str = str(profile.url)

        if not url_str.startswith('https://www.linkedin.com/in/'):
            raise HTTPException(status_code=400, detail='Invalid LinkedIn profile URL')

        success = db.add_monitored_profile(url_str, profile.name)
        if success:
            return {"success": True, "message": "Profile added successfully"}
        else:
            raise HTTPException(status_code=500, detail='Failed to add profile')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/profiles/{url:path}", response_model=dict)
async def remove_monitored_profile(url: str):
    """Remove a profile from monitoring"""
    try:
        # URL decode the path parameter
        decoded_url = unquote(url)

        success = db.remove_monitored_profile(decoded_url)
        if success:
            return {"success": True, "message": "Profile removed successfully"}
        else:
            raise HTTPException(status_code=500, detail='Failed to remove profile')

    except Exception as e:
        logger.error(f"Error removing profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get monitoring statistics"""
    try:
        # Get counts from database
        profiles = db.get_monitored_profiles()
        total_profiles = len(profiles)

        # Get recent changes
        changes = db.get_job_changes_history()
        total_changes = len(changes)

        return StatsResponse(
            total_profiles=total_profiles,
            total_changes=total_changes,
            last_updated=None  # Could be implemented later
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/{url:path}", response_model=dict)
async def scrape_specific_profile(url: str):
    """Scrape a specific LinkedIn profile immediately"""
    try:
        # URL decode the path parameter
        from urllib.parse import unquote
        decoded_url = unquote(url)

        logger.info(f"🔍 Immediate scrape requested for: {decoded_url}")

        # Import scraper functions
        from scraper import scrape_linkedin_profile
        import asyncio

        # Scrape the specific profile
        scraped_data = await scrape_linkedin_profile(decoded_url)

        if scraped_data:
            # Save to database
            db.save_profile(scraped_data)

            logger.info(f"✅ Successfully scraped and saved: {scraped_data.get('name')}")

            return {
                "success": True,
                "message": "Profile scraped successfully",
                "data": {
                    "name": scraped_data.get("name"),
                    "current_position": scraped_data.get("current_position"),
                    "current_company": scraped_data.get("current_company"),
                    "last_updated": scraped_data.get("last_updated"),
                    "experience_count": len(scraped_data.get("experience", [])),
                    "experience": scraped_data.get("experience", [])[:2]  # Show first 2 experiences
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to scrape profile")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping profile {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)