"""
AMEWS - Simulated OTP Authentication Gateway
============================================
This is a SIMULATED authentication system for demonstration purposes only.

COMPLIANCE NOTICE:
- No real phone numbers or Aadhaar data is used
- All phone numbers are synthetic (9900XXXXXX series reserved for demos)
- OTPs are generated locally - no real SMS gateway integration
- All user data is fictional and for demonstration only
- This system does NOT connect to any real UIDAI/Aadhaar infrastructure

ETHICAL CONSIDERATIONS:
- System clearly labeled as simulation
- No real PII (Personally Identifiable Information) collected
- Synthetic data patterns based on public aggregated statistics
- Designed for hackathon/demo purposes only
"""

import random
import string
import hashlib
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import uuid

# ============================================================================
# SIMULATION CONFIGURATION
# ============================================================================

class GatewayStatus(Enum):
    """Simulated SMS Gateway Status"""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


@dataclass
class SimulationConfig:
    """Configuration for the simulated authentication gateway"""
    # Latency simulation (milliseconds)
    min_latency_ms: int = 100
    max_latency_ms: int = 500
    
    # Failure simulation rates (0.0 to 1.0)
    gateway_failure_rate: float = 0.02  # 2% random gateway failures
    otp_delivery_failure_rate: float = 0.01  # 1% delivery failures
    
    # Rate limiting
    max_otp_per_phone_per_hour: int = 5
    cooldown_seconds: int = 30
    otp_expiry_minutes: int = 5
    max_verify_attempts: int = 3
    
    # Demo mode - shows OTP on screen (would be False in production)
    demo_mode: bool = True
    
    # Gateway status (for simulating outages)
    gateway_status: GatewayStatus = GatewayStatus.AVAILABLE


# Global simulation config
SIM_CONFIG = SimulationConfig()

# File-based OTP store path (persists across restarts)
OTP_STORE_FILE = os.path.join(os.path.dirname(__file__), ".otp_store.json")

def load_otp_store() -> Dict[str, Dict]:
    """Load OTP store from file"""
    if os.path.exists(OTP_STORE_FILE):
        try:
            with open(OTP_STORE_FILE, 'r') as f:
                data = json.load(f)
                # Convert datetime strings back to datetime objects
                for phone, entry in data.items():
                    entry["created_at"] = datetime.fromisoformat(entry["created_at"])
                    entry["expires_at"] = datetime.fromisoformat(entry["expires_at"])
                return data
        except Exception as e:
            print(f"[OTP Store] Error loading: {e}")
    return {}

def save_otp_store():
    """Save OTP store to file"""
    try:
        # Convert datetime objects to strings for JSON serialization
        data = {}
        for phone, entry in otp_store.items():
            data[phone] = {
                **entry,
                "created_at": entry["created_at"].isoformat(),
                "expires_at": entry["expires_at"].isoformat()
            }
        with open(OTP_STORE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[OTP Store] Error saving: {e}")

# Load existing OTPs on module import (survives restarts!)
otp_store: Dict[str, Dict] = load_otp_store()
rate_limit_store: Dict[str, List[datetime]] = {}
gateway_logs: List[Dict] = []


# ============================================================================
# SYNTHETIC USER DATABASE
# ============================================================================
# These are FICTIONAL users with SYNTHETIC phone numbers
# Phone numbers use 9900XXXXXX series which is reserved for demos/testing

SYNTHETIC_USERS = [
    {
        "phone": "9900000001",  # Synthetic demo number
        "name": "Demo Administrator",
        "masked_aadhaar": "XXXX-XXXX-0001",  # Only last 4 shown, rest masked
        "state": "Delhi",
        "district": "New Delhi",
        "role": "ADMIN",
        "department": "UIDAI - Technology Division"
    },
    {
        "phone": "9900000002",
        "name": "Priya Sharma (Demo)",
        "masked_aadhaar": "XXXX-XXXX-0002",
        "state": "Maharashtra",
        "district": "Mumbai",
        "role": "ANALYST",
        "department": "Regional Office - West"
    },
    {
        "phone": "9900000003",
        "name": "Rahul Kumar (Demo)",
        "masked_aadhaar": "XXXX-XXXX-0003",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "role": "ANALYST",
        "department": "Regional Office - South"
    },
    {
        "phone": "9900000004",
        "name": "Anjali Patel (Demo)",
        "masked_aadhaar": "XXXX-XXXX-0004",
        "state": "Gujarat",
        "district": "Ahmedabad",
        "role": "VIEWER",
        "department": "Compliance Team"
    },
    {
        "phone": "9900000005",
        "name": "Vikram Singh (Demo)",
        "masked_aadhaar": "XXXX-XXXX-0005",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "role": "VIEWER",
        "department": "Audit Division"
    },
    # Easy demo number for testing
    {
        "phone": "1234567890",  
        "name": "UIDAI Security Officer",
        "masked_aadhaar": "XXXX-XXXX-0000",
        "state": "Delhi",
        "district": "New Delhi",
        "role": "ADMIN",
        "department": "Security Operations"
    },
]


# ============================================================================
# SIMULATED SMS GATEWAY
# ============================================================================

class SimulatedSMSGateway:
    """
    Simulated SMS Gateway for OTP delivery
    
    This class simulates a real SMS gateway with:
    - Realistic latency
    - Random failures (for testing error handling)
    - Retry logic
    - Delivery status tracking
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.delivery_log: List[Dict] = []
    
    def simulate_latency(self) -> int:
        """Simulate network latency (synchronous)"""
        latency = random.randint(
            self.config.min_latency_ms, 
            self.config.max_latency_ms
        )
        time.sleep(latency / 1000)  # Convert to seconds
        return latency
    
    def check_gateway_health(self) -> Tuple[bool, str]:
        """Check if gateway is available"""
        if self.config.gateway_status == GatewayStatus.MAINTENANCE:
            return False, "SMS Gateway under maintenance. Please try again later."
        
        if self.config.gateway_status == GatewayStatus.DEGRADED:
            # 50% chance of failure when degraded
            if random.random() < 0.5:
                return False, "SMS Gateway experiencing issues. Please retry."
        
        # Random failure simulation
        if random.random() < self.config.gateway_failure_rate:
            return False, "Temporary gateway error. Please retry."
        
        return True, "Gateway available"
    
    def simulate_delivery(self, phone: str, otp: str) -> Dict:
        """Simulate OTP delivery via SMS"""
        delivery_id = f"del_{uuid.uuid4().hex[:10]}"
        
        # Simulate latency
        latency = self.simulate_latency()
        
        # Check for delivery failure
        if random.random() < self.config.otp_delivery_failure_rate:
            result = {
                "delivery_id": delivery_id,
                "status": "FAILED",
                "phone": f"XXXXXX{phone[-4:]}",
                "timestamp": datetime.now().isoformat(),
                "latency_ms": latency,
                "error": "Carrier delivery failed - simulated"
            }
        else:
            result = {
                "delivery_id": delivery_id,
                "status": "DELIVERED",
                "phone": f"XXXXXX{phone[-4:]}",
                "timestamp": datetime.now().isoformat(),
                "latency_ms": latency
            }
        
        self.delivery_log.append(result)
        return result
    
    def send_otp(self, phone: str, otp: str, retry_count: int = 0) -> Tuple[bool, str, Dict]:
        """
        Send OTP with retry logic
        Returns: (success, message, delivery_info)
        """
        max_retries = 2
        
        # Check gateway health
        healthy, health_msg = self.check_gateway_health()
        if not healthy:
            if retry_count < max_retries:
                # Automatic retry with backoff
                time.sleep(0.1 * (retry_count + 1))
                return self.send_otp(phone, otp, retry_count + 1)
            return False, health_msg, {"retries": retry_count, "status": "GATEWAY_ERROR"}
        
        # Simulate delivery
        delivery = self.simulate_delivery(phone, otp)
        
        if delivery["status"] == "FAILED":
            if retry_count < max_retries:
                return self.send_otp(phone, otp, retry_count + 1)
            return False, "SMS delivery failed after retries", delivery
        
        delivery["retries"] = retry_count
        return True, "OTP sent successfully", delivery


# Global gateway instance
sms_gateway = SimulatedSMSGateway(SIM_CONFIG)


# ============================================================================
# OTP AUTHENTICATION FUNCTIONS
# ============================================================================

def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


def clean_phone(phone: str) -> str:
    """Normalize phone number format"""
    return phone.replace(" ", "").replace("-", "").replace("+91", "").strip()


def find_user_by_phone(phone: str) -> Optional[Dict]:
    """Find a synthetic user by phone number"""
    phone_clean = clean_phone(phone)
    
    for user in SYNTHETIC_USERS:
        if user["phone"] == phone_clean:
            return user.copy()  # Return a copy to prevent modification
    return None


def check_rate_limit(phone: str) -> Tuple[bool, str]:
    """Check if phone has exceeded rate limit"""
    phone_clean = clean_phone(phone)
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Get requests in last hour
    if phone_clean in rate_limit_store:
        recent = [t for t in rate_limit_store[phone_clean] if t > hour_ago]
        rate_limit_store[phone_clean] = recent
        
        if len(recent) >= SIM_CONFIG.max_otp_per_phone_per_hour:
            return False, f"Rate limit exceeded. Maximum {SIM_CONFIG.max_otp_per_phone_per_hour} OTPs per hour."
    
    return True, "OK"


def send_otp(phone: str) -> Tuple[bool, str, Optional[str]]:
    """
    Send OTP to phone number via simulated gateway
    
    Returns: (success, message, otp_for_demo)
    
    Note: In demo mode, OTP is returned for display. In production,
    this would NEVER return the OTP - it would only be sent via SMS.
    """
    phone_clean = clean_phone(phone)
    
    # Validate phone number format
    if not phone_clean.isdigit() or len(phone_clean) != 10:
        return False, "Invalid phone number. Please enter 10 digits.", None
    
    # Check if user exists in synthetic database
    user = find_user_by_phone(phone_clean)
    if not user:
        return False, "📱 Phone not registered in demo. Try: 9900000001 or 1234567890", None
    
    # Check rate limiting
    rate_ok, rate_msg = check_rate_limit(phone_clean)
    if not rate_ok:
        return False, rate_msg, None
    
    # Check cooldown
    if phone_clean in otp_store:
        stored = otp_store[phone_clean]
        time_since = (datetime.now() - stored["created_at"]).seconds
        if time_since < SIM_CONFIG.cooldown_seconds:
            wait = SIM_CONFIG.cooldown_seconds - time_since
            return False, f"⏱️ Please wait {wait} seconds before requesting a new OTP.", None
    
    # Generate OTP
    otp = generate_otp()
    
    # Send via simulated gateway
    success, msg, delivery_info = sms_gateway.send_otp(phone_clean, otp)
    
    if not success:
        return False, f"❌ {msg}", None
    
    # Store OTP
    otp_store[phone_clean] = {
        "otp": otp,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=SIM_CONFIG.otp_expiry_minutes),
        "attempts": 0,
        "verified": False,
        "delivery_id": delivery_info.get("delivery_id")
    }
    
    # Persist to file (survives server restarts)
    save_otp_store()
    
    # Update rate limit
    if phone_clean not in rate_limit_store:
        rate_limit_store[phone_clean] = []
    rate_limit_store[phone_clean].append(datetime.now())
    
    # Log for debugging
    masked_phone = f"XXXXXX{phone_clean[-4:]}"
    latency = delivery_info.get("latency_ms", 0)
    retries = delivery_info.get("retries", 0)
    print(f"[SIMULATED SMS] To: {masked_phone} | OTP: {otp} | Latency: {latency}ms | Retries: {retries}")
    
    # In demo mode, return OTP for display
    demo_otp = otp if SIM_CONFIG.demo_mode else None
    
    return True, f"✅ OTP sent to {masked_phone}. Valid for {SIM_CONFIG.otp_expiry_minutes} minutes.", demo_otp


def verify_otp(phone: str, otp: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Verify OTP for phone number
    
    Returns: (success, message, user_data)
    """
    phone_clean = clean_phone(phone)
    
    # Debug logging
    print(f"[DEBUG] Verifying OTP for phone: {phone_clean}")
    print(f"[DEBUG] Current OTP store keys: {list(otp_store.keys())}")
    
    # Check if OTP request exists
    if phone_clean not in otp_store:
        print(f"[DEBUG] Phone {phone_clean} NOT found in store!")
        return False, "❌ No OTP found. Please request a new OTP.", None
    
    stored = otp_store[phone_clean]
    print(f"[DEBUG] Found OTP entry, expires_at: {stored['expires_at']}")
    
    # Check expiry
    if datetime.now() > stored["expires_at"]:
        del otp_store[phone_clean]
        save_otp_store()
        return False, "⏰ OTP has expired. Please request a new OTP.", None
    
    # Check attempt limit
    if stored["attempts"] >= SIM_CONFIG.max_verify_attempts:
        del otp_store[phone_clean]
        save_otp_store()
        return False, "🚫 Too many failed attempts. Please request a new OTP.", None
    
    # Verify OTP
    if stored["otp"] != otp.strip():
        stored["attempts"] += 1
        save_otp_store()
        remaining = SIM_CONFIG.max_verify_attempts - stored["attempts"]
        return False, f"❌ Invalid OTP. {remaining} attempt(s) remaining.", None
    
    # Success! Get user data
    user = find_user_by_phone(phone_clean)
    if not user:
        return False, "User not found in system.", None
    
    # Cleanup OTP
    del otp_store[phone_clean]
    save_otp_store()
    
    # Create session data (no sensitive info)
    session_id = hashlib.sha256(f"{phone_clean}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    user_data = {
        "user_id": f"usr_{hashlib.md5(phone_clean.encode()).hexdigest()[:12]}",
        "session_id": f"sess_{session_id}",
        "phone_masked": f"XXXXXX{phone_clean[-4:]}",
        "full_name": user["name"],
        "role": user["role"],
        "state": user["state"],
        "district": user["district"],
        "department": user.get("department", "AMEWS"),
        "login_time": datetime.now().isoformat(),
        "is_demo_user": True  # Always true in this simulation
    }
    
    # Log authentication
    log_auth_event(phone_clean, True, user["state"])
    
    return True, "✅ OTP verified successfully! Redirecting to dashboard...", user_data


def resend_otp(phone: str) -> Tuple[bool, str, Optional[str]]:
    """Resend OTP with rate limiting"""
    return send_otp(phone)


def log_auth_event(phone: str, success: bool, state: str):
    """Log authentication event for audit"""
    event = {
        "timestamp": datetime.now().isoformat(),
        "phone_masked": f"XXXXXX{phone[-4:]}",
        "success": success,
        "state": state,
        "event_type": "OTP_LOGIN"
    }
    gateway_logs.append(event)
    
    # Keep only last 1000 logs in memory
    if len(gateway_logs) > 1000:
        gateway_logs.pop(0)


def get_demo_users() -> List[Dict]:
    """
    Get list of demo users for testing
    
    Returns only non-sensitive information suitable for display
    """
    return [
        {
            "phone": user["phone"],
            "name": user["name"],
            "state": user["state"],
            "role": user["role"],
            "is_synthetic": True
        }
        for user in SYNTHETIC_USERS
    ]


def get_gateway_status() -> Dict:
    """Get current simulated gateway status"""
    return {
        "status": SIM_CONFIG.gateway_status.value,
        "demo_mode": SIM_CONFIG.demo_mode,
        "rate_limit": f"{SIM_CONFIG.max_otp_per_phone_per_hour}/hour",
        "otp_expiry": f"{SIM_CONFIG.otp_expiry_minutes} minutes",
        "is_simulation": True,
        "disclaimer": "This is a SIMULATED gateway for demonstration purposes only."
    }
