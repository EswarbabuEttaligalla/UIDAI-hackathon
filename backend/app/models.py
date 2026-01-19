"""
Pydantic Models for AMEWS API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class AuthType(str, Enum):
    OTP = "OTP"
    BIOMETRIC = "BIOMETRIC"
    DEMOGRAPHIC = "DEMOGRAPHIC"

class ServiceCategory(str, Enum):
    BANKING = "BANKING"
    TELECOM = "TELECOM"
    WELFARE = "WELFARE"
    HEALTHCARE = "HEALTHCARE"
    GOVERNMENT = "GOVERNMENT"
    INSURANCE = "INSURANCE"
    EDUCATION = "EDUCATION"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

class SystemMode(str, Enum):
    BASELINE_LEARNING = "BASELINE_LEARNING"
    ACTIVE_MONITORING = "ACTIVE_MONITORING"
    
class ActionTier(str, Enum):
    MONITOR_ONLY = "MONITOR_ONLY"
    ENHANCED_REVIEW = "ENHANCED_REVIEW"
    DEVICE_BLACKLIST = "DEVICE_BLACKLIST"
    ESCALATE_REGIONAL = "ESCALATE_REGIONAL"
    IMMEDIATE_RESPONSE = "IMMEDIATE_RESPONSE"
    
class FeedbackType(str, Enum):
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CONFIRMED_THREAT = "CONFIRMED_THREAT"
    PARTIALLY_RELEVANT = "PARTIALLY_RELEVANT"

# Authentication Event Models
class AuthenticationEventCreate(BaseModel):
    timestamp: datetime
    auth_type: AuthType
    service_category: ServiceCategory
    service_provider_id: str
    device_fingerprint_hash: str
    state_code: str
    district_code: str
    retry_count: int = 0
    is_fallback: bool = False
    status: str = "SUCCESS"
    failure_reason: Optional[str] = None
    session_duration_ms: int = 0

class AuthenticationEvent(AuthenticationEventCreate):
    event_id: str
    hour_of_day: int
    day_of_week: int
    created_at: datetime

class BatchIngestRequest(BaseModel):
    events: List[AuthenticationEventCreate]

class BatchIngestResponse(BaseModel):
    success: bool
    records_processed: int
    records_failed: int
    errors: List[str] = []

# Risk Score Models
class RiskFactor(BaseModel):
    rule_name: str
    contribution: float
    description: str
    severity: str

class RiskScoreResponse(BaseModel):
    score_id: str
    entity_type: str
    entity_id: str
    composite_score: float
    risk_level: RiskLevel
    rule_score: float
    ml_score: float
    contributing_factors: List[RiskFactor]
    timestamp: datetime

class RiskScoreRequest(BaseModel):
    entity_type: str  # DEVICE, REGION, SERVICE_PROVIDER
    entity_id: str
    time_window_hours: int = 24

# Alert Models
class AlertCreate(BaseModel):
    severity: RiskLevel
    alert_type: str
    title: str
    description: str
    affected_region: str
    service_category: Optional[str] = None
    risk_score: float
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    action_tier: ActionTier
    baseline_deviation: Optional[float] = None
    reason_codes: List[str]
    suggested_actions: List[str]

class Alert(AlertCreate):
    alert_id: str
    timestamp: datetime
    status: AlertStatus
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    feedback_type: Optional[FeedbackType] = None
    feedback_by: Optional[str] = None
    feedback_at: Optional[datetime] = None
    feedback_notes: Optional[str] = None

class AlertUpdate(BaseModel):
    status: AlertStatus
    acknowledged_by: Optional[str] = None

class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total_count: int
    page: int
    page_size: int

# Dashboard Models
class DashboardMetrics(BaseModel):
    total_events_today: int
    total_events_week: int
    active_alerts: int
    high_risk_events: int
    critical_alerts: int
    avg_risk_score: float
    trend_percentage: float  # Compared to previous period
    events_by_hour: List[Dict[str, Any]]
    events_by_service: List[Dict[str, Any]]
    risk_by_region: List[Dict[str, Any]]
    auth_type_distribution: List[Dict[str, Any]]

class RegionRiskData(BaseModel):
    state_code: str
    state_name: str
    risk_score: float
    event_count: int
    alert_count: int

class TrendData(BaseModel):
    timestamp: datetime
    value: float
    metric_type: str

# User Models
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    full_name: str
    role: UserRole
    department: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Simulation Models
class SimulationScenario(str, Enum):
    DEVICE_SPIKE = "DEVICE_SPIKE"
    REGIONAL_ANOMALY = "REGIONAL_ANOMALY"
    OTP_ABUSE = "OTP_ABUSE"
    OFF_HOURS_SPIKE = "OFF_HOURS_SPIKE"
    SERVICE_PROVIDER_ANOMALY = "SERVICE_PROVIDER_ANOMALY"

class SimulationRequest(BaseModel):
    scenario: SimulationScenario
    intensity: float = 1.0  # 0.5 to 2.0
    duration_minutes: int = 5
    target_region: Optional[str] = None

class SimulationResponse(BaseModel):
    simulation_id: str
    scenario: str
    status: str
    events_generated: int
    start_time: datetime

# Audit Models
class AuditLog(BaseModel):
    log_id: str
    timestamp: datetime
    action: str
    endpoint: str
    user_id: str
    request_summary: str
    response_status: int

# Privacy Info Model
class PrivacyInfo(BaseModel):
    data_not_collected: List[str]
    anonymization_methods: List[str]
    data_retention_policy: str
    aggregation_rules: List[str]
    compliance_standards: List[str]

class BaselineStatus(BaseModel):
    system_mode: SystemMode
    baseline_start_date: Optional[datetime] = None
    baseline_window_days: int = 14
    regions_covered: List[str]
    completion_percentage: float
    next_retrain_at: Optional[datetime] = None
    
class RegionBaseline(BaseModel):
    region_code: str
    auth_frequency_mean: float
    auth_frequency_std: float
    failure_rate_mean: float
    failure_rate_std: float
    otp_fallback_rate_mean: float
    retry_count_mean: float
    off_hours_rate_mean: float
    sample_size: int
    last_updated: datetime
    
class AlertFeedback(BaseModel):
    alert_id: str
    feedback_type: FeedbackType
    feedback_notes: Optional[str] = None
    analyst_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
class SystemModeUpdate(BaseModel):
    target_mode: SystemMode
    force_transition: bool = False
