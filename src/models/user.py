from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime

class User(Document):
    username: str = Field(unique=True)
    password_hash: str
    company: str = "DeepWatch Security"
    role: str = "operator"
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users" # Nome della collezione in MongoDB
