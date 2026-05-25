from beanie import Document
from pydantic import Field
from typing import List, Dict
from datetime import datetime

class Detection(Document):
    client_id: str
    camera: str
    objects: List[Dict] 
    object_count: int
    image: str = "" # Base64 string della cattura
    timestamp: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "detections"
