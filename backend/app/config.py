"""
Configuration settings for AMEWS Backend
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "AMEWS - Aadhaar Misuse Early-Warning System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database Settings
    DATABASE_URL: str = "duckdb:///./amews_data.duckdb"
    
    # Security Settings
    SECRET_KEY: str = "amews-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Risk Thresholds
    RISK_LOW_THRESHOLD: int = 30
    RISK_MEDIUM_THRESHOLD: int = 60
    RISK_HIGH_THRESHOLD: int = 80
    
    # Alert Settings
    ALERT_RETENTION_DAYS: int = 90
    
    # Privacy Settings
    MIN_AGGREGATION_COUNT: int = 5  # Minimum records to aggregate for privacy
    
    class Config:
        env_file = ".env"

settings = Settings()
