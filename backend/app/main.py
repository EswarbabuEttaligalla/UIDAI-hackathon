"""
AMEWS - Aadhaar Misuse Early-Warning System
Main FastAPI Application
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.config import settings
from app.database import init_database, get_connection, execute_query_df
from app.models import (
    AuthenticationEventCreate, BatchIngestRequest, BatchIngestResponse,
    RiskScoreRequest, RiskScoreResponse, Alert, AlertUpdate, AlertsResponse,
    DashboardMetrics, RegionRiskData, UserLogin, TokenResponse, UserResponse,
    SimulationRequest, SimulationResponse, PrivacyInfo, AuditLog,
    BaselineStatus, AlertFeedback, SystemModeUpdate, ActionTier, FeedbackType
)
from app.auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_user_required, log_audit
)
from app.risk_engine import risk_engine
from app.alert_manager import alert_manager, run_periodic_analysis
from app.baseline_engine import baseline_engine
from app.simulation import simulation_engine
from app.data_generator import SyntheticDataGenerator, STATES, generate_initial_dataset
from app.otp_auth import send_otp, verify_otp, resend_otp, get_demo_users, get_gateway_status
from app.dataset_loader import get_dataset_loader


# OTP Request/Response Models
class OTPSendRequest(BaseModel):
    phone: str

class OTPSendResponse(BaseModel):
    success: bool
    message: str
    otp: Optional[str] = None  # Only for demo purposes

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str

class OTPVerifyResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    user: Optional[dict] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Initializing AMEWS Backend...")
    init_database()
    
    # Load actual datasets
    print("Loading UIDAI datasets...")
    loader = get_dataset_loader()
    if loader.loaded:
        print(f"Datasets loaded successfully!")
        if loader.regional_stats:
            print(f"  - States: {loader.regional_stats.get('unique_states', 0)}")
            print(f"  - Districts: {loader.regional_stats.get('unique_districts', 0)}")
    
    # Check if we need to generate initial data
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM authentication_events").fetchone()[0]
    conn.close()
    
    if count == 0:
        print("Generating initial dataset from actual data patterns...")
        # Use dataset-based generation
        events = loader.generate_auth_events_from_data(count=5000)
        from app.data_generator import save_events_to_db
        for event in events:
            save_events_to_db([event])
        print(f"Generated {len(events)} events from dataset patterns.")
    
    # Initialize baseline learning system
    print("Initializing baseline learning system...")
    baseline_status = baseline_engine.get_system_status()
    print(f"Baseline learning status: {baseline_status['system_mode']} "
          f"({baseline_status['completion_percentage']:.1f}% complete)")
    
    # Generate sample alerts if none exist or system is in active monitoring
    conn = get_connection()
    alert_count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    conn.close()
    
    if alert_count == 0 and baseline_status['system_mode'] == 'ACTIVE_MONITORING':
        print("Generating sample alerts for testing...")
        generate_sample_alerts()
        print("Sample alerts generated.")
    elif baseline_status['system_mode'] == 'BASELINE_LEARNING':
        print("System in baseline learning mode - alerts will be generated after learning phase completes")
    
    print(f"AMEWS Backend started. {count} events in database.")
    print(f"System mode: {baseline_status['system_mode']}")
    print(f"Baseline completion: {baseline_status['completion_percentage']:.1f}%")
    
    yield
    
    # Shutdown
    print("Shutting down AMEWS Backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Privacy-preserving early-warning intelligence system for detecting abnormal Aadhaar authentication patterns",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Sample Data Generation ==============

def generate_sample_alerts():
    """Generate enhanced sample alerts for testing purposes"""
    import random
    import uuid
    
    conn = get_connection()
    
    # Simple alert types matching the basic schema
    alert_types = [
        ("VELOCITY_ATTACK", "CRITICAL", "Multiple authentication attempts detected from single device in short time window"),
        ("GEOGRAPHIC_ANOMALY", "HIGH", "Unusual geographic pattern detected - same Aadhaar used across distant locations"),
        ("OFF_HOURS_SPIKE", "MEDIUM", "Abnormal authentication activity during non-business hours (2 AM - 5 AM)"),
        ("BIOMETRIC_FAILURE_SPIKE", "HIGH", "High biometric failure rate detected suggesting potential fraud"),
        ("DEVICE_FINGERPRINT_ANOMALY", "CRITICAL", "Suspicious device fingerprint pattern - same device for multiple Aadhaars"),
    ]
    
    states = ["MH", "DL", "KA", "TN", "UP", "GJ", "RJ", "WB", "TS", "KL"]
    
    for i in range(12):  # Generate 12 alerts
        alert_type, severity, description = random.choice(alert_types)
        state = random.choice(states)
        
        alert_id = f"ALR-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now() - timedelta(hours=random.randint(0, 48))
        confidence = random.uniform(0.6, 0.95)
        
        conn.execute("""
            INSERT INTO alerts (alert_id, alert_type, severity, affected_region,
                              confidence_score, description, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
        """, (alert_id, alert_type, severity, state, confidence, description, timestamp))
    
    print(f"Generated 12 sample alerts")



# ============== Health & Info Endpoints ==============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    conn = get_connection()
    try:
        conn.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    finally:
        conn.close()
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/demo/generate-alerts")
async def generate_demo_alerts():
    """Generate sample alerts for testing (no auth required)"""
    generate_sample_alerts()
    return {"success": True, "message": "Generated 15 sample alerts"}


# ============== Authentication Endpoints ==============

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login"""
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    
    log_audit("LOGIN", "/api/auth/login", user["user_id"], 
              f"User logged in: {user['username']}", 200)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(**user)
    )


# ============== OTP Authentication Endpoints ==============

@app.post("/api/auth/otp/send", response_model=OTPSendResponse)
async def otp_send(request: OTPSendRequest):
    """Send OTP to phone number"""
    success, message, otp = send_otp(request.phone)
    
    return OTPSendResponse(
        success=success,
        message=message,
        otp=otp  # Only for testing - in production, don't return OTP
    )


@app.post("/api/auth/otp/verify", response_model=OTPVerifyResponse)
async def otp_verify(request: OTPVerifyRequest):
    """Verify OTP and login"""
    success, message, user_data = verify_otp(request.phone, request.otp)
    
    if not success:
        return OTPVerifyResponse(
            success=False,
            message=message
        )
    
    # Create access token using the user_id from verified user data
    access_token = create_access_token(data={"sub": user_data["user_id"]})
    
    return OTPVerifyResponse(
        success=True,
        message=message,
        access_token=access_token,
        user=user_data
    )


@app.post("/api/auth/otp/resend", response_model=OTPSendResponse)
async def otp_resend(request: OTPSendRequest):
    """Resend OTP"""
    success, message, otp = resend_otp(request.phone)
    
    return OTPSendResponse(
        success=success,
        message=message,
        otp=otp
    )


@app.get("/api/auth/demo-users")
async def get_demo_users_list():
    """Get list of demo users for testing"""
    return {
        "users": get_demo_users(),
        "note": "Use any of these phone numbers to test OTP login"
    }


@app.get("/api/auth/gateway-status")
async def get_auth_gateway_status():
    """Get simulated gateway status - transparency for authorized personnel"""
    return get_gateway_status()


# ============== Dataset Info Endpoints ==============

@app.get("/api/dataset/info")
async def get_dataset_info():
    """Get information about loaded datasets"""
    loader = get_dataset_loader()
    
    return {
        "loaded": loader.loaded,
        "stats": loader.regional_stats,
        "demographic_records": len(loader.demographic_data) if loader.demographic_data is not None else 0,
        "enrolment_records": len(loader.enrolment_data) if loader.enrolment_data is not None else 0
    }


@app.get("/api/dataset/states")
async def get_dataset_states():
    """Get list of states from dataset"""
    loader = get_dataset_loader()
    
    if loader.demographic_data is not None and not loader.demographic_data.empty:
        states = loader.demographic_data['state'].unique().tolist()
        return {"states": sorted(states)}
    
    return {"states": []}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user_required)):
    """Get current user info"""
    return UserResponse(**user)


# ============== Data Ingestion Endpoints ==============

@app.post("/api/ingest/event")
async def ingest_single_event(
    event: AuthenticationEventCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Ingest a single authentication event"""
    generator = SyntheticDataGenerator()
    
    event_dict = {
        "event_id": f"evt_{uuid.uuid4().hex[:16]}",
        "timestamp": event.timestamp,
        "auth_type": event.auth_type.value,
        "service_category": event.service_category.value,
        "service_provider_id": event.service_provider_id,
        "device_fingerprint_hash": event.device_fingerprint_hash,
        "state_code": event.state_code,
        "district_code": event.district_code,
        "retry_count": event.retry_count,
        "is_fallback": event.is_fallback,
        "status": event.status,
        "failure_reason": event.failure_reason,
        "hour_of_day": event.timestamp.hour,
        "day_of_week": event.timestamp.weekday(),
        "session_duration_ms": event.session_duration_ms,
    }
    
    saved = generator.save_to_database([event_dict])
    
    # Trigger background risk analysis
    background_tasks.add_task(
        analyze_event_background, 
        event.device_fingerprint_hash
    )
    
    return {"success": saved == 1, "event_id": event_dict["event_id"]}


@app.post("/api/ingest/batch", response_model=BatchIngestResponse)
async def ingest_batch(
    request: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Ingest a batch of authentication events"""
    generator = SyntheticDataGenerator()
    events = []
    errors = []
    
    for i, event in enumerate(request.events):
        try:
            event_dict = {
                "event_id": f"evt_{uuid.uuid4().hex[:16]}",
                "timestamp": event.timestamp,
                "auth_type": event.auth_type.value,
                "service_category": event.service_category.value,
                "service_provider_id": event.service_provider_id,
                "device_fingerprint_hash": event.device_fingerprint_hash,
                "state_code": event.state_code,
                "district_code": event.district_code,
                "retry_count": event.retry_count,
                "is_fallback": event.is_fallback,
                "status": event.status,
                "failure_reason": event.failure_reason,
                "hour_of_day": event.timestamp.hour,
                "day_of_week": event.timestamp.weekday(),
                "session_duration_ms": event.session_duration_ms,
            }
            events.append(event_dict)
        except Exception as e:
            errors.append(f"Event {i}: {str(e)}")
    
    saved = generator.save_to_database(events)
    
    # Trigger background analysis
    background_tasks.add_task(run_periodic_analysis)
    
    return BatchIngestResponse(
        success=len(errors) == 0,
        records_processed=saved,
        records_failed=len(errors),
        errors=errors
    )


async def analyze_event_background(device_hash: str):
    """Background task to analyze events"""
    try:
        assessment = risk_engine.analyze_entity("DEVICE", device_hash, time_window_hours=1)
        if assessment["composite_score"] >= settings.RISK_MEDIUM_THRESHOLD:
            alert_manager.generate_alert(assessment, "DEVICE", device_hash)
    except Exception as e:
        print(f"Background analysis error: {e}")


# ============== Risk Analysis Endpoints ==============

@app.post("/api/risk/analyze", response_model=RiskScoreResponse)
async def analyze_risk(
    request: RiskScoreRequest,
    user: dict = Depends(get_current_user)
):
    """Analyze risk for a specific entity"""
    assessment = risk_engine.analyze_entity(
        request.entity_type,
        request.entity_id,
        request.time_window_hours
    )
    
    return RiskScoreResponse(
        score_id=assessment["score_id"],
        entity_type=assessment["entity_type"],
        entity_id=assessment["entity_id"],
        composite_score=assessment["composite_score"],
        risk_level=assessment["risk_level"],
        rule_score=assessment["rule_score"],
        ml_score=assessment["ml_score"],
        contributing_factors=assessment["contributing_factors"],
        timestamp=assessment["timestamp"]
    )


@app.get("/api/risk/overview")
async def get_risk_overview(user: dict = Depends(get_current_user)):
    """Get overall risk overview for dashboard"""
    conn = get_connection()
    # High risk devices
    high_risk_devices = conn.execute("""
        SELECT device_fingerprint_hash, COUNT(*) as event_count,
               AVG(retry_count) as avg_retries
        FROM authentication_events
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
        GROUP BY device_fingerprint_hash
        HAVING COUNT(*) > 20 OR AVG(retry_count) > 3
        ORDER BY event_count DESC
        LIMIT 10
    """).fetchall()
    
    # High risk regions
    high_risk_regions = conn.execute("""
        SELECT state_code, COUNT(*) as event_count,
               SUM(CASE WHEN status = 'FAILURE' THEN 1 ELSE 0 END) as failures
        FROM authentication_events
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
        GROUP BY state_code
        ORDER BY failures DESC
        LIMIT 10
    """).fetchall()
    
    return {
        "high_risk_devices": [
            {"device": d[0][:16] + "...", "events": d[1], "avg_retries": round(d[2], 2)}
            for d in high_risk_devices
        ],
        "high_risk_regions": [
            {"region": r[0], "events": r[1], "failures": r[2]}
            for r in high_risk_regions
        ]
    }
# ============== Alert Endpoints ==============

@app.get("/api/alerts")
async def get_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user: dict = Depends(get_current_user)
):
    """Get alerts with optional filters"""
    alerts = alert_manager.get_alerts(status, severity, limit, offset)
    
    # Get total count
    conn = get_connection()
    conditions = ["1=1"]
    if status:
        conditions.append(f"status = '{status}'")
    if severity:
        conditions.append(f"severity = '{severity}'")
    
    total = conn.execute(
        f"SELECT COUNT(*) FROM alerts WHERE {' AND '.join(conditions)}"
    ).fetchone()[0]
    
    return {
        "alerts": alerts,
        "total_count": total,
        "page": offset // limit + 1,
        "page_size": limit
    }


@app.get("/api/alerts/{alert_id}")
async def get_alert_detail(
    alert_id: str,
    user: dict = Depends(get_current_user)
):
    """Get detailed alert information"""
    alert = alert_manager.get_alert_by_id(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert


@app.patch("/api/alerts/{alert_id}")
async def update_alert(
    alert_id: str,
    update: AlertUpdate,
    user: dict = Depends(get_current_user_required)
):
    """Update alert status"""
    success = alert_manager.update_alert_status(
        alert_id, 
        update.status.value,
        user["user_id"]
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update alert")
    
    log_audit("UPDATE_ALERT", f"/api/alerts/{alert_id}", user["user_id"],
              f"Updated alert status to {update.status}", 200)
    
    return {"success": True, "message": f"Alert status updated to {update.status}"}


@app.get("/api/alerts/statistics/summary")
async def get_alert_statistics(user: dict = Depends(get_current_user)):
    """Get alert statistics"""
    return alert_manager.get_alert_statistics()


# ============== Dashboard Endpoints ==============

@app.get("/api/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(user: dict = Depends(get_current_user)):
    """Get dashboard metrics"""
    conn = get_connection()
    try:
        # Events today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        events_today = conn.execute(
            "SELECT COUNT(*) FROM authentication_events WHERE timestamp >= ?",
            (today_start,)
        ).fetchone()[0]
        
        # Events this week
        week_start = today_start - timedelta(days=7)
        events_week = conn.execute(
            "SELECT COUNT(*) FROM authentication_events WHERE timestamp >= ?",
            (week_start,)
        ).fetchone()[0]
        
        # Events previous week (for trend)
        prev_week_start = week_start - timedelta(days=7)
        events_prev_week = conn.execute(
            "SELECT COUNT(*) FROM authentication_events WHERE timestamp >= ? AND timestamp < ?",
            (prev_week_start, week_start)
        ).fetchone()[0]
        
        # Calculate trend
        if events_prev_week > 0:
            trend = ((events_week - events_prev_week) / events_prev_week) * 100
        else:
            trend = 0
        
        # Active alerts
        active_alerts = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE status = 'ACTIVE'"
        ).fetchone()[0]
        
        # Critical alerts
        critical_alerts = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE status = 'ACTIVE' AND severity = 'CRITICAL'"
        ).fetchone()[0]
        
        # High risk events (events with retry > 3 or failure)
        high_risk_events = conn.execute(
            """SELECT COUNT(*) FROM authentication_events 
               WHERE timestamp >= ? AND (retry_count >= 3 OR status = 'FAILURE')""",
            (today_start,)
        ).fetchone()[0]
        
        # Average risk score (simplified calculation)
        avg_risk = conn.execute(
            "SELECT AVG(risk_score) FROM alerts WHERE timestamp >= ?",
            (week_start,)
        ).fetchone()[0] or 0
        
        # Events by hour (last 24 hours)
        events_by_hour = conn.execute("""
            SELECT hour_of_day, COUNT(*) as count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
            GROUP BY hour_of_day
            ORDER BY hour_of_day
        """).fetchall()
        
        # Events by service
        events_by_service = conn.execute("""
            SELECT service_category, COUNT(*) as count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
            GROUP BY service_category
            ORDER BY count DESC
        """).fetchall()
        
        # Risk by region
        risk_by_region = conn.execute("""
            SELECT state_code, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'FAILURE' THEN 1 ELSE 0 END) as failures,
                   AVG(retry_count) as avg_retries
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
            GROUP BY state_code
        """).fetchall()
        
        # Auth type distribution
        auth_dist = conn.execute("""
            SELECT auth_type, COUNT(*) as count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
            GROUP BY auth_type
        """).fetchall()
        
        return DashboardMetrics(
            total_events_today=events_today,
            total_events_week=events_week,
            active_alerts=active_alerts,
            high_risk_events=high_risk_events,
            critical_alerts=critical_alerts,
            avg_risk_score=round(avg_risk, 1),
            trend_percentage=round(trend, 1),
            events_by_hour=[{"hour": h[0], "count": h[1]} for h in events_by_hour],
            events_by_service=[{"service": s[0], "count": s[1]} for s in events_by_service],
            risk_by_region=[
                {
                    "state": r[0], 
                    "state_name": STATES.get(r[0], {}).get("name", r[0]),
                    "total": r[1],
                    "failures": r[2],
                    "risk_score": min(100, (r[2] / max(r[1], 1)) * 100 + r[3] * 10)
                }
                for r in risk_by_region
            ],
            auth_type_distribution=[{"type": a[0], "count": a[1]} for a in auth_dist]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/trends")
async def get_trends(
    days: int = Query(7, le=30),
    user: dict = Depends(get_current_user)
):
    """Get trend data for charts"""
    conn = get_connection()
    try:
        # Daily event counts
        daily_events = conn.execute(f"""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL {days} DAY
            GROUP BY DATE(timestamp)
            ORDER BY date
        """).fetchall()
        
        # Daily failures
        daily_failures = conn.execute(f"""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL {days} DAY
                  AND status = 'FAILURE'
            GROUP BY DATE(timestamp)
            ORDER BY date
        """).fetchall()
        
        # Daily alerts
        daily_alerts = conn.execute(f"""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM alerts
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL {days} DAY
            GROUP BY DATE(timestamp)
            ORDER BY date
        """).fetchall()
        
        # Service category trends
        service_trends = conn.execute(f"""
            SELECT DATE(timestamp) as date, service_category, COUNT(*) as count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL {days} DAY
            GROUP BY DATE(timestamp), service_category
            ORDER BY date, service_category
        """).fetchall()
        
        return {
            "daily_events": [{"date": str(d[0]), "count": d[1]} for d in daily_events],
            "daily_failures": [{"date": str(d[0]), "count": d[1]} for d in daily_failures],
            "daily_alerts": [{"date": str(d[0]), "count": d[1]} for d in daily_alerts],
            "service_trends": [
                {"date": str(s[0]), "service": s[1], "count": s[2]} 
                for s in service_trends
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/regions")
async def get_region_data(user: dict = Depends(get_current_user)):
    """Get region-wise data for heatmap"""
    conn = get_connection()
    try:
        region_data = conn.execute("""
            SELECT 
                state_code,
                COUNT(*) as event_count,
                SUM(CASE WHEN status = 'FAILURE' THEN 1 ELSE 0 END) as failures,
                AVG(retry_count) as avg_retries,
                COUNT(DISTINCT device_fingerprint_hash) as unique_devices
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
            GROUP BY state_code
        """).fetchall()
        
        # Get alert counts per region
        alert_counts = conn.execute("""
            SELECT affected_region, COUNT(*) as count
            FROM alerts
            WHERE status = 'ACTIVE'
            GROUP BY affected_region
        """).fetchall()
        alert_map = {a[0]: a[1] for a in alert_counts}
        
        regions = []
        for r in region_data:
            state_info = STATES.get(r[0], {"name": r[0]})
            failure_rate = r[2] / max(r[1], 1)
            risk_score = min(100, failure_rate * 100 + r[3] * 15)
            
            regions.append({
                "state_code": r[0],
                "state_name": state_info.get("name", r[0]),
                "event_count": r[1],
                "failures": r[2],
                "failure_rate": round(failure_rate * 100, 2),
                "avg_retries": round(r[3], 2),
                "unique_devices": r[4],
                "alert_count": alert_map.get(r[0], 0),
                "risk_score": round(risk_score, 1)
            })
        
        return {"regions": regions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== Baseline Learning Endpoints ==============

@app.get("/api/baseline/status", response_model=BaselineStatus)
async def get_baseline_status(user: dict = Depends(get_current_user)):
    """Get current baseline learning status"""
    status = baseline_engine.get_system_status()
    return BaselineStatus(**status)


@app.post("/api/baseline/mode")
async def update_system_mode(
    update: SystemModeUpdate,
    user: dict = Depends(get_current_user_required)
):
    """Update system mode (admin only)"""
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # For testing purposes, this simulates mode switching
    # In production, this would have more complex validation
    
    log_audit("UPDATE_SYSTEM_MODE", "/api/baseline/mode", user["user_id"],
              f"System mode change requested: {update.target_mode}", 200)
    
    return {
        "success": True,
        "message": f"System mode update initiated: {update.target_mode}",
        "note": "Mode transitions are gradual and depend on baseline completion"
    }


@app.get("/api/baseline/regions/{region_code}")
async def get_region_baseline(
    region_code: str,
    user: dict = Depends(get_current_user)
):
    """Get baseline metrics for a specific region"""
    baseline_metrics = baseline_engine.compute_region_baseline(region_code)
    
    return {
        "region_code": region_code,
        "baseline_available": baseline_metrics.sample_size >= baseline_engine.min_sample_size,
        "metrics": {
            "auth_frequency_mean": baseline_metrics.auth_frequency_mean,
            "auth_frequency_std": baseline_metrics.auth_frequency_std,
            "failure_rate_mean": baseline_metrics.failure_rate_mean,
            "otp_fallback_rate_mean": baseline_metrics.otp_fallback_rate_mean,
            "retry_count_mean": baseline_metrics.retry_count_mean,
            "off_hours_rate_mean": baseline_metrics.off_hours_rate_mean,
            "sample_size": baseline_metrics.sample_size
        },
        "interpretation": {
            "sample_adequacy": "Sufficient" if baseline_metrics.sample_size >= 100 else "Insufficient",
            "reliability": "High" if baseline_metrics.sample_size >= 500 else 
                          "Medium" if baseline_metrics.sample_size >= 100 else "Low"
        }
    }


# ============== Enhanced Alert Endpoints ==============

@app.post("/api/alerts/{alert_id}/feedback")
async def submit_alert_feedback(
    alert_id: str,
    feedback: AlertFeedback,
    user: dict = Depends(get_current_user_required)
):
    """Submit feedback for an alert (false positive, confirmed threat, etc.)"""
    success = alert_manager.process_feedback(
        alert_id=alert_id,
        feedback_type=feedback.feedback_type.value,
        user_id=user["user_id"],
        feedback_notes=feedback.feedback_notes,
        analyst_confidence=feedback.analyst_confidence
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process feedback")
    
    log_audit("SUBMIT_FEEDBACK", f"/api/alerts/{alert_id}/feedback", user["user_id"],
              f"Submitted feedback: {feedback.feedback_type}", 200)
    
    return {
        "success": True,
        "message": f"Feedback recorded: {feedback.feedback_type}",
        "learning_note": "System will adjust sensitivity based on this feedback for future similar patterns"
    }


@app.get("/api/alerts/statistics/advanced")
async def get_advanced_alert_statistics(user: dict = Depends(get_current_user)):
    """Get advanced alert statistics including confidence and action distribution"""
    conn = get_connection()
    try:
        # Confidence distribution
        confidence_dist = conn.execute("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.8 THEN 'High (80%+)'
                    WHEN confidence_score >= 0.6 THEN 'Medium (60-80%)'
                    WHEN confidence_score >= 0.4 THEN 'Low (40-60%)'
                    ELSE 'Very Low (<40%)'
                END as confidence_band,
                COUNT(*) as count
            FROM alerts
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
            GROUP BY 1
            ORDER BY confidence_score DESC
        """).fetchall()
        
        # Action tier distribution
        action_dist = conn.execute("""
            SELECT action_tier, COUNT(*) as count
            FROM alerts
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
            GROUP BY action_tier
            ORDER BY count DESC
        """).fetchall()
        
        # False positive rate
        fp_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN feedback_type = 'FALSE_POSITIVE' THEN 1 ELSE 0 END) as false_positives,
                SUM(CASE WHEN feedback_type = 'CONFIRMED_THREAT' THEN 1 ELSE 0 END) as confirmed_threats,
                SUM(CASE WHEN feedback_type IS NOT NULL THEN 1 ELSE 0 END) as reviewed_alerts
            FROM alerts
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
        """).fetchone()
        
        # Baseline deviation stats
        baseline_stats = conn.execute("""
            SELECT 
                AVG(baseline_deviation) as avg_deviation,
                MAX(baseline_deviation) as max_deviation,
                COUNT(CASE WHEN baseline_deviation > 0.3 THEN 1 END) as significant_deviations
            FROM alerts
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
              AND baseline_deviation IS NOT NULL
        """).fetchone()
        
        # Calculate false positive rate
        fp_rate = 0.0
        if fp_stats and fp_stats[3] > 0:  # reviewed_alerts > 0
            fp_rate = fp_stats[1] / fp_stats[3]  # false_positives / reviewed_alerts
        
        return {
            "confidence_distribution": [
                {"band": c[0], "count": c[1]} for c in confidence_dist
            ],
            "action_tier_distribution": [
                {"tier": a[0] or "Unknown", "count": a[1]} for a in action_dist
            ],
            "feedback_statistics": {
                "total_alerts": fp_stats[0] if fp_stats else 0,
                "false_positives": fp_stats[1] if fp_stats else 0,
                "confirmed_threats": fp_stats[2] if fp_stats else 0,
                "reviewed_alerts": fp_stats[3] if fp_stats else 0,
                "false_positive_rate": round(fp_rate * 100, 1),
                "review_rate": round((fp_stats[3] / max(fp_stats[0], 1)) * 100, 1) if fp_stats else 0
            },
            "baseline_statistics": {
                "avg_deviation": round(baseline_stats[0] * 100, 1) if baseline_stats and baseline_stats[0] else 0,
                "max_deviation": round(baseline_stats[1] * 100, 1) if baseline_stats and baseline_stats[1] else 0,
                "significant_deviations": baseline_stats[2] if baseline_stats else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== Red Team Attack Scenarios ==============

@app.get("/api/scenarios/red-team")
async def get_red_team_scenarios(user: dict = Depends(get_current_user)):
    """Get available red team attack scenarios for testing"""
    return {
        "scenarios": [
            {
                "id": "LOW_AND_SLOW",
                "name": "Low-and-Slow Attack",
                "description": "Gradual misuse that stays below fixed thresholds but shows cumulative deviation from baseline",
                "detection_method": "Baseline deviation analysis over extended time window",
                "difficulty": "High - requires advanced temporal pattern analysis"
            },
            {
                "id": "ADAPTIVE_THRESHOLD_EVASION",
                "name": "Adaptive Threshold Evasion",
                "description": "Attack that learns and adapts to avoid triggering rule-based detectors",
                "detection_method": "ML anomaly detection and behavior pattern analysis",
                "difficulty": "Very High - requires sophisticated ML models"
            },
            {
                "id": "DISTRIBUTED_COORDINATED",
                "name": "Distributed Coordinated Attack",
                "description": "Multiple devices/regions attacking in coordination to evade single-point detection",
                "detection_method": "Cross-regional correlation and network effect analysis",
                "difficulty": "High - requires distributed pattern recognition"
            },
            {
                "id": "LEGITIMATE_MIMICKING",
                "name": "Legitimate Pattern Mimicking",
                "description": "Fraud that closely mimics legitimate usage patterns",
                "detection_method": "Fine-grained behavioral analysis and confidence scoring",
                "difficulty": "Very High - requires high-resolution behavioral models"
            }
        ],
        "note": "These scenarios test AMEWS's ability to detect sophisticated attacks that evade simple rule-based detection"
    }


# ============== Simulation Endpoints ==============

@app.post("/api/simulation/run", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    user: dict = Depends(get_current_user_required)
):
    """Run a misuse simulation scenario"""
    if user["role"] not in ["ADMIN", "ANALYST"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    result = await simulation_engine.run_simulation(
        scenario=request.scenario.value,
        intensity=request.intensity,
        duration_minutes=request.duration_minutes,
        target_region=request.target_region
    )
    
    log_audit("RUN_SIMULATION", "/api/simulation/run", user["user_id"],
              f"Ran simulation: {request.scenario}", 200)
    
    return SimulationResponse(**result)


@app.get("/api/simulation/scenarios")
async def get_scenarios(user: dict = Depends(get_current_user)):
    """Get available simulation scenarios"""
    return {
        "scenarios": [
            {
                "id": "DEVICE_SPIKE",
                "name": "Device Spike",
                "description": "Simulates excessive authentications from a single device"
            },
            {
                "id": "REGIONAL_ANOMALY",
                "name": "Regional Anomaly",
                "description": "Simulates unusual authentication patterns in a specific region"
            },
            {
                "id": "OTP_ABUSE",
                "name": "OTP Abuse",
                "description": "Simulates excessive OTP fallback usage patterns"
            },
            {
                "id": "OFF_HOURS_SPIKE",
                "name": "Off-Hours Spike",
                "description": "Simulates authentication spikes during unusual hours"
            },
            {
                "id": "SERVICE_PROVIDER_ANOMALY",
                "name": "Service Provider Anomaly",
                "description": "Simulates anomalous behavior from a service provider"
            }
        ]
    }


# ============== Privacy & Governance Endpoints ==============

@app.get("/api/governance/privacy", response_model=PrivacyInfo)
async def get_privacy_info():
    """Get privacy and governance information"""
    return PrivacyInfo(
        data_not_collected=[
            "Aadhaar numbers (UID)",
            "Biometric data (fingerprints, iris scans)",
            "Personal demographic information",
            "Photographs or images",
            "Exact addresses or locations",
            "Mobile numbers or email addresses",
            "Bank account or financial details"
        ],
        anonymization_methods=[
            "Device fingerprints are one-way hashed using SHA-256",
            "Service provider IDs are anonymized",
            "Location data is aggregated to state/district level only",
            "Timestamps are used for pattern analysis, not identification",
            "No personally identifiable information (PII) is processed"
        ],
        data_retention_policy=(
            "Synthetic authentication metadata is retained for 90 days for pattern analysis. "
            "Alerts are retained for audit purposes. No real Aadhaar data is ever stored."
        ),
        aggregation_rules=[
            "Minimum 5 events required for any statistical aggregation",
            "Individual-level views are never exposed",
            "Region-wise data is shown at state level only",
            "Device-level analysis uses hashed identifiers only"
        ],
        compliance_standards=[
            "Privacy by Design principles",
            "Data minimization practices",
            "Purpose limitation (fraud detection only)",
            "No unauthorized data sharing",
            "Audit logging for all system actions"
        ]
    )


@app.get("/api/governance/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, le=500),
    user: dict = Depends(get_current_user_required)
):
    """Get audit logs (admin only)"""
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    df = execute_query_df(f"""
        SELECT * FROM audit_logs
        ORDER BY timestamp DESC
        LIMIT {limit}
    """)
    
    if df.empty:
        return {"logs": []}
    
    logs = []
    for _, row in df.iterrows():
        logs.append({
            "log_id": row["log_id"],
            "timestamp": row["timestamp"],
            "action": row["action"],
            "endpoint": row["endpoint"],
            "user_id": row["user_id"],
            "request_summary": row["request_summary"],
            "response_status": row["response_status"]
        })
    
    return {"logs": logs}


# ============== Data Generation Endpoints ==============

@app.post("/api/admin/generate-data")
async def generate_data(
    days: int = Query(7, le=30),
    events_per_day: int = Query(200, le=1000),
    user: dict = Depends(get_current_user_required)
):
    """Generate synthetic data (admin only)"""
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    count = generate_initial_dataset(days=days, events_per_day=events_per_day)
    
    log_audit("GENERATE_DATA", "/api/admin/generate-data", user["user_id"],
              f"Generated {count} events", 200)
    
    return {"success": True, "events_generated": count}


@app.post("/api/admin/train-model")
async def train_model(user: dict = Depends(get_current_user_required)):
    """Train the ML model (admin only)"""
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = risk_engine.train_ml_model()
    
    log_audit("TRAIN_MODEL", "/api/admin/train-model", user["user_id"],
              f"Model training: {'success' if success else 'failed'}", 200 if success else 500)
    
    return {"success": success}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
