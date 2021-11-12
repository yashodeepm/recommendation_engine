from pydantic import BaseModel
from typing import List, Dict, Optional

class RecommendationRequest(BaseModel):
    date: str
    search_categories: List[str] # Take in parameter from user (like relaxing, etc. and provide a list of types from here: ["restaurant", "museum", "zoo", "amusement_park", "aquarium", "art_gallery", "night_club", "bar", "bakery", "book_store", "tourist_attraction", "shopping_mall", "park", "movie_theater"])
    radius: Optional[float] = 5000
    location: Dict[str, float] # Should be a Dict like {'lat': 12.2, 'lon': 12.2}

class RecommendationAcceptRequest(BaseModel):
    place_id: str