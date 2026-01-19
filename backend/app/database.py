"""
Database Models and Connection for AMEWS
"""
import duckdb
import pandas as pd
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from app.config import settings

def get_connection():
    """Get a new DuckDB connection for each request"""
    # Extract file path from database URL (remove duckdb:/// prefix)
    db_path = settings.DATABASE_URL.replace("duckdb:///", "")
    return duckdb.connect(db_path)

def execute_query_df(query: str, params=None) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame"""
    conn = get_connection()
    try:
        if params:
            result = conn.execute(query, params).fetchdf()
        else:
            result = conn.execute(query).fetchdf()
        return result
    except Exception as e:
        print(f"Query error: {e}")
        raise
    finally:
        conn.close()

def execute_write(query: str, params=None):
    """Execute a write query (INSERT, UPDATE, DELETE)"""
    conn = get_connection()
    try:
        if params:
            conn.execute(query, params)
        else:
            conn.execute(query)
        conn.commit()
    except Exception as e:
        print(f"Write error: {e}")
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database schema and create tables"""
    conn = get_connection()
    
    # Create authentication_events table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS authentication_events (
            event_id VARCHAR PRIMARY KEY,
            aadhaar_id VARCHAR,
            timestamp TIMESTAMP,
            service_type VARCHAR,
            service_category VARCHAR,
            device_type VARCHAR,
            device_fingerprint_hash VARCHAR,
            location_city VARCHAR,
            location_state VARCHAR,
            state_code VARCHAR,
            ip_address VARCHAR,
            status VARCHAR,
            is_fallback BOOLEAN,
            hour_of_day INTEGER,
            day_of_week INTEGER,
            retry_count INTEGER,
            session_duration DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create alerts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id VARCHAR PRIMARY KEY,
            alert_type VARCHAR,
            severity VARCHAR,
            affected_region VARCHAR,
            confidence_score DOUBLE,
            description TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR DEFAULT 'OPEN',
            assigned_to VARCHAR,
            resolved_at TIMESTAMP
        )
    """)
    
    # Create region_baselines table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS region_baselines (
            baseline_id VARCHAR PRIMARY KEY,
            region_code VARCHAR,
            time_band VARCHAR,
            service_category VARCHAR,
            auth_frequency_mean DOUBLE,
            auth_frequency_std DOUBLE,
            failure_rate_mean DOUBLE,
            failure_rate_std DOUBLE,
            otp_fallback_rate_mean DOUBLE,
            retry_count_mean DOUBLE,
            off_hours_rate_mean DOUBLE,
            sample_size INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create system_baseline table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_baseline (
            baseline_id VARCHAR PRIMARY KEY,
            system_mode VARCHAR,
            baseline_start_date TIMESTAMP,
            baseline_window_days INTEGER,
            completion_percentage DOUBLE DEFAULT 0.0,
            next_retrain_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create demographic_data table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS demographic_data (
            aadhaar_id VARCHAR PRIMARY KEY,
            state_code VARCHAR,
            district VARCHAR,
            age INTEGER,
            gender VARCHAR,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("Database schema initialized successfully")
























