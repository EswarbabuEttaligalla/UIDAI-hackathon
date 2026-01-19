"""
Synthetic Data Generator for AMEWS
Generates realistic Aadhaar authentication metadata without real identifiers
"""
import random
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np
from app.database import get_connection, execute_write
import json

# Indian States and Districts (Sample)
STATES = {
    "MH": {"name": "Maharashtra", "districts": ["MUM", "PUN", "NAG", "THN", "NSK"]},
    "DL": {"name": "Delhi", "districts": ["NDL", "SDL", "EDL", "WDL", "CDL"]},
    "KA": {"name": "Karnataka", "districts": ["BLR", "MYS", "HUB", "MNG", "BEL"]},
    "TN": {"name": "Tamil Nadu", "districts": ["CHN", "CBE", "MDU", "TRY", "SLM"]},
    "UP": {"name": "Uttar Pradesh", "districts": ["LKO", "KNP", "AGR", "VNS", "ALG"]},
    "GJ": {"name": "Gujarat", "districts": ["AMD", "SUR", "VAD", "RJK", "BHV"]},
    "RJ": {"name": "Rajasthan", "districts": ["JPR", "JDH", "UDR", "KTA", "AJM"]},
    "WB": {"name": "West Bengal", "districts": ["KOL", "HWH", "DRJ", "ASN", "SLG"]},
    "MP": {"name": "Madhya Pradesh", "districts": ["BPL", "IND", "JBP", "GWL", "UJN"]},
    "AP": {"name": "Andhra Pradesh", "districts": ["VIJ", "VSK", "GNT", "NLR", "KDP"]},
    "TS": {"name": "Telangana", "districts": ["HYD", "WRG", "KRM", "NZB", "MHB"]},
    "KL": {"name": "Kerala", "districts": ["TVM", "KCH", "KZD", "EKM", "TSR"]},
}

SERVICE_PROVIDERS = {
    "BANKING": ["SBI", "HDFC", "ICICI", "AXIS", "PNB", "BOB", "KOTAK", "YES", "IDFC", "RBL"],
    "TELECOM": ["JIO", "AIRTEL", "VI", "BSNL", "MTNL"],
    "WELFARE": ["PMJAY", "PMKSY", "MGNREGA", "PDS", "PENSION", "LPG"],
    "HEALTHCARE": ["AYUSH", "ESIC", "CGHS", "PMJAY_H", "NHPS"],
    "GOVERNMENT": ["PASSPORT", "DRIVING", "VOTER", "INCOME_TAX", "GST", "EPF"],
    "INSURANCE": ["LIC", "NIAC", "OICL", "UIIC", "GICL"],
    "EDUCATION": ["UGC", "AICTE", "CBSE", "NEET", "JEE"],
}

FAILURE_REASONS = [
    "BIOMETRIC_MISMATCH",
    "OTP_EXPIRED",
    "OTP_INVALID",
    "DEMOGRAPHIC_MISMATCH",
    "DEVICE_NOT_REGISTERED",
    "SERVICE_TIMEOUT",
    "RATE_LIMIT_EXCEEDED",
    "SESSION_EXPIRED",
]

class SyntheticDataGenerator:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        self.device_pool = self._generate_device_pool(1000)
        
    def _generate_device_pool(self, count: int) -> List[str]:
        """Generate a pool of anonymized device fingerprints"""
        devices = []
        for i in range(count):
            raw = f"device_{i}_{uuid.uuid4().hex[:8]}"
            hashed = hashlib.sha256(raw.encode()).hexdigest()[:32]
            devices.append(hashed)
        return devices
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"evt_{uuid.uuid4().hex[:16]}"
    
    def _get_weighted_auth_type(self, hour: int) -> str:
        """Get auth type with realistic distribution"""
        # OTP more common during business hours
        if 9 <= hour <= 18:
            weights = [0.5, 0.35, 0.15]  # OTP, BIOMETRIC, DEMOGRAPHIC
        else:
            weights = [0.6, 0.25, 0.15]
        return random.choices(["OTP", "BIOMETRIC", "DEMOGRAPHIC"], weights=weights)[0]
    
    def _get_weighted_service_category(self, hour: int, day_of_week: int) -> str:
        """Get service category with realistic distribution"""
        if day_of_week >= 5:  # Weekend
            weights = [0.4, 0.2, 0.15, 0.1, 0.05, 0.05, 0.05]
        elif 9 <= hour <= 17:  # Business hours
            weights = [0.3, 0.15, 0.2, 0.1, 0.15, 0.05, 0.05]
        else:
            weights = [0.35, 0.25, 0.15, 0.1, 0.05, 0.05, 0.05]
        
        categories = list(SERVICE_PROVIDERS.keys())
        return random.choices(categories, weights=weights)[0]
    
    def _should_fail(self, retry_count: int, is_fallback: bool) -> bool:
        """Determine if authentication should fail"""
        base_failure_rate = 0.05
        if retry_count > 0:
            base_failure_rate *= (1 + retry_count * 0.3)
        if is_fallback:
            base_failure_rate *= 1.2
        return random.random() < min(base_failure_rate, 0.3)
    
    def generate_normal_event(self, timestamp: Optional[datetime] = None) -> Dict:
        """Generate a single normal authentication event"""
        if timestamp is None:
            timestamp = datetime.now() - timedelta(hours=random.randint(0, 168))
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        state = random.choice(list(STATES.keys()))
        district = random.choice(STATES[state]["districts"])
        service_category = self._get_weighted_service_category(hour, day_of_week)
        service_provider = random.choice(SERVICE_PROVIDERS[service_category])
        
        # Normal behavior patterns
        retry_count = int(np.random.choice([0, 1, 2], p=[0.85, 0.12, 0.03]))
        is_fallback = random.random() < 0.08  # 8% fallback rate
        
        auth_type = self._get_weighted_auth_type(hour)
        if is_fallback:
            auth_type = "OTP"  # Fallback typically to OTP
        
        status = "FAILURE" if self._should_fail(retry_count, is_fallback) else "SUCCESS"
        failure_reason = random.choice(FAILURE_REASONS) if status == "FAILURE" else None
        
        return {
            "event_id": self._generate_event_id(),
            "timestamp": timestamp,
            "auth_type": auth_type,
            "service_category": service_category,
            "service_provider_id": f"SP_{service_provider}_{hashlib.md5(service_provider.encode()).hexdigest()[:8]}",
            "device_fingerprint_hash": random.choice(self.device_pool),
            "state_code": state,
            "district_code": district,
            "retry_count": int(retry_count),
            "is_fallback": bool(is_fallback),
            "status": status,
            "failure_reason": failure_reason,
            "hour_of_day": int(hour),
            "day_of_week": int(day_of_week),
            "session_duration_ms": int(np.random.exponential(2000) + 500),
        }
    
    def generate_anomalous_event(self, anomaly_type: str, timestamp: Optional[datetime] = None) -> Dict:
        """Generate an anomalous event based on type"""
        event = self.generate_normal_event(timestamp)
        
        if anomaly_type == "DEVICE_SPIKE":
            # Same device with high frequency
            event["device_fingerprint_hash"] = self.device_pool[0]  # Fixed device
            event["retry_count"] = int(random.randint(3, 8))
            
        elif anomaly_type == "REGIONAL_ANOMALY":
            # Unusual regional pattern
            event["hour_of_day"] = int(random.choice([2, 3, 4]))  # Off hours
            event["retry_count"] = int(random.randint(2, 5))
            
        elif anomaly_type == "OTP_ABUSE":
            # Excessive OTP fallback
            event["auth_type"] = "OTP"
            event["is_fallback"] = True
            event["retry_count"] = int(random.randint(2, 6))
            event["status"] = random.choice(["SUCCESS", "FAILURE", "FAILURE"])
            if event["status"] == "FAILURE":
                event["failure_reason"] = random.choice(["OTP_EXPIRED", "OTP_INVALID"])
                
        elif anomaly_type == "OFF_HOURS_SPIKE":
            # Authentication during unusual hours
            event["hour_of_day"] = int(random.choice([1, 2, 3, 4, 5]))
            event["timestamp"] = event["timestamp"].replace(hour=event["hour_of_day"])
            
        elif anomaly_type == "SERVICE_PROVIDER_ANOMALY":
            # Unusual service provider behavior
            event["retry_count"] = int(random.randint(4, 10))
            event["session_duration_ms"] = int(np.random.exponential(10000) + 5000)
        
        return event
    
    def generate_batch(self, count: int, anomaly_ratio: float = 0.05, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[Dict]:
        """Generate a batch of events with specified anomaly ratio"""
        events = []
        
        if start_time is None:
            start_time = datetime.now() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now()
        
        time_range = (end_time - start_time).total_seconds()
        
        anomaly_types = ["DEVICE_SPIKE", "REGIONAL_ANOMALY", "OTP_ABUSE", 
                        "OFF_HOURS_SPIKE", "SERVICE_PROVIDER_ANOMALY"]
        
        for i in range(count):
            # Random timestamp within range
            random_seconds = random.random() * time_range
            timestamp = start_time + timedelta(seconds=random_seconds)
            
            if random.random() < anomaly_ratio:
                anomaly_type = random.choice(anomaly_types)
                event = self.generate_anomalous_event(anomaly_type, timestamp)
            else:
                event = self.generate_normal_event(timestamp)
            
            events.append(event)
        
        return sorted(events, key=lambda x: x["timestamp"])
    
    def save_to_database(self, events: List[Dict]) -> int:
        """Save events to database"""
        conn = get_connection()
        saved_count = 0
        
        for event in events:
            try:
                conn.execute("""
                    INSERT INTO authentication_events 
                    (event_id, timestamp, auth_type, service_category, service_provider_id,
                     device_fingerprint_hash, state_code, district_code, retry_count,
                     is_fallback, status, failure_reason, hour_of_day, day_of_week,
                     session_duration_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event["event_id"],
                    event["timestamp"],
                    event["auth_type"],
                    event["service_category"],
                    event["service_provider_id"],
                    event["device_fingerprint_hash"],
                    event["state_code"],
                    event["district_code"],
                    event["retry_count"],
                    event["is_fallback"],
                    event["status"],
                    event["failure_reason"],
                    event["hour_of_day"],
                    event["day_of_week"],
                    event["session_duration_ms"],
                    datetime.now()
                ))
                saved_count += 1
            except Exception as e:
                print(f"Error saving event: {e}")
        
        conn.close()
        return saved_count


def generate_initial_dataset(days: int = 30, events_per_day: int = 1000):
    """Generate initial dataset for the system"""
    generator = SyntheticDataGenerator()
    total_saved = 0
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Generate in daily batches
    current_date = start_time
    while current_date < end_time:
        next_date = current_date + timedelta(days=1)
        
        # Vary events per day (more on weekdays)
        day_of_week = current_date.weekday()
        daily_events = int(events_per_day * (1.2 if day_of_week < 5 else 0.7))
        
        events = generator.generate_batch(
            count=daily_events,
            anomaly_ratio=0.03,  # 3% anomalies
            start_time=current_date,
            end_time=next_date
        )
        
        saved = generator.save_to_database(events)
        total_saved += saved
        print(f"Generated {saved} events for {current_date.date()}")
        
        current_date = next_date
    
    print(f"Total events generated: {total_saved}")
    return total_saved


if __name__ == "__main__":
    from app.database import init_database
    init_database()
    generate_initial_dataset(days=30, events_per_day=500)
