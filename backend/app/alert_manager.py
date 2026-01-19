"""
Alert Generation Module for AMEWS
Enhanced with confidence scoring, action tiers, and false positive feedback
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.database import get_connection, execute_query_df, execute_write
from app.config import settings
from app.baseline_engine import baseline_engine

# Alert type configurations with enhanced action mappings
ALERT_CONFIGS = {
    "VELOCITY_ATTACK": {
        "title_template": "Velocity Attack Detected",
        "actions": {
            "DEVICE_BLACKLIST": [
                "IMMEDIATE: Block device from further authentications",
                "Notify affected service providers",
                "Generate device abuse report",
                "Escalate to cybercrime team if pattern persists"
            ],
            "ENHANCED_REVIEW": [
                "Flag device for enhanced monitoring",
                "Review authentication patterns over 48 hours",
                "Cross-reference with known fraud patterns"
            ],
            "MONITOR_ONLY": [
                "Continue monitoring device activity",
                "Set alert if frequency increases"
            ]
        }
    },
    "GEOGRAPHIC_ANOMALY": {
        "title_template": "Geographic Anomaly Detected",
        "actions": {
            "ESCALATE_REGIONAL": [
                "Alert regional UIDAI offices in affected states",
                "Coordinate investigation across regions",
                "Review cross-border authentication patterns"
            ],
            "ENHANCED_REVIEW": [
                "Verify travel feasibility between locations",
                "Check for legitimate use cases (family/business)",
                "Monitor for 24-hour patterns"
            ],
            "MONITOR_ONLY": [
                "Track geographic patterns",
                "Set threshold alerts for rapid movement"
            ]
        }
    },
    "BIOMETRIC_FAILURE_SPIKE": {
        "title_template": "Biometric Failure Spike Detected",
        "actions": {
            "ENHANCED_REVIEW": [
                "Investigate biometric quality indicators",
                "Check for device tampering signs",
                "Review OTP fallback patterns"
            ],
            "MONITOR_ONLY": [
                "Monitor biometric success rates",
                "Track fallback usage patterns"
            ]
        }
    },
    "OFF_HOURS_SPIKE": {
        "title_template": "Off-Hours Activity Spike",
        "actions": {
            "ENHANCED_REVIEW": [
                "Verify legitimacy of night-time authentications",
                "Check for automated/scripted patterns",
                "Review service provider operational windows"
            ],
            "MONITOR_ONLY": [
                "Track off-hours patterns",
                "Set alerts for volume spikes"
            ]
        }
    }
}


class AlertManager:
    """Manages alert generation, storage, and retrieval"""
    
    def __init__(self):
        self.alert_configs = ALERT_CONFIGS
    
    def generate_alert(self, risk_assessment: Dict, entity_type: str, 
                       entity_id: str) -> Optional[Dict]:
        """Generate an enhanced alert with confidence scoring and action tiers"""
        
        # Check if system is in baseline learning mode
        system_status = baseline_engine.get_system_status()
        if system_status["system_mode"] == "BASELINE_LEARNING":
            # During baseline learning, don't generate alerts but log for analysis
            print(f"Baseline mode: Would have generated alert for {entity_type}:{entity_id} "
                  f"(score: {risk_assessment['composite_score']:.1f})")
            return None
        
        if risk_assessment["composite_score"] < settings.RISK_MEDIUM_THRESHOLD:
            return None
        
        # Determine alert type based on contributing factors
        alert_type = self._determine_alert_type(risk_assessment["contributing_factors"])
        config = self.alert_configs.get(alert_type, self.alert_configs["VELOCITY_ATTACK"])
        
        # Extract enhanced fields from risk assessment
        confidence_score = risk_assessment.get("confidence_score", 0.0)
        action_tier = risk_assessment.get("action_tier", "MONITOR_ONLY")
        baseline_deviation = risk_assessment.get("baseline_deviation", 0.0)
        
        # Build reason codes
        reason_codes = [f["rule_name"] for f in risk_assessment["contributing_factors"]]
        
        # Determine severity
        if risk_assessment["composite_score"] >= 90:
            severity = "CRITICAL"
        elif risk_assessment["composite_score"] >= settings.RISK_HIGH_THRESHOLD:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        
        # Get action-specific suggestions
        action_suggestions = config["actions"].get(action_tier, config["actions"]["MONITOR_ONLY"])
        
        # Create enhanced alert
        alert = {
            "alert_id": f"ALR-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.now(),
            "severity": severity,
            "alert_type": alert_type,
            "title": config["title_template"],
            "description": self._build_enhanced_description(
                risk_assessment, entity_type, entity_id, confidence_score, baseline_deviation
            ),
            "affected_region": entity_id if entity_type == "REGION" else "Multiple",
            "service_category": None,
            "risk_score": risk_assessment["composite_score"],
            "confidence_score": confidence_score,
            "action_tier": action_tier,
            "baseline_deviation": baseline_deviation,
            "reason_codes": json.dumps(reason_codes),
            "suggested_actions": json.dumps(action_suggestions),
            "status": "ACTIVE"
        }
        
        # Save to database
        self._save_enhanced_alert(alert)
        
        return alert
    
    def _determine_alert_type(self, factors: List[Dict]) -> str:
        """Determine alert type based on contributing factors"""
        rule_names = [f["rule_name"] for f in factors]
        
        if "HIGH_AUTH_FREQUENCY" in rule_names:
            return "VELOCITY_ATTACK"
        elif "GEOGRAPHIC_VELOCITY_ANOMALY" in rule_names:
            return "GEOGRAPHIC_ANOMALY"
        elif "OTP_FALLBACK_ABUSE" in rule_names or "HIGH_FAILURE_RATE" in rule_names:
            return "BIOMETRIC_FAILURE_SPIKE"
        elif "OFF_HOURS_ACTIVITY" in rule_names:
            return "OFF_HOURS_SPIKE"
        else:
            return "VELOCITY_ATTACK"
    
    def _build_enhanced_description(self, risk_assessment: Dict, entity_type: str, 
                                   entity_id: str, confidence_score: float,
                                   baseline_deviation: float) -> str:
        """Build detailed alert description with confidence and baseline info"""
        desc_parts = [
            f"Risk Level: {risk_assessment['risk_level']} (Score: {risk_assessment['composite_score']:.1f})",
            f"Confidence: {confidence_score:.0%} | Action Tier: {risk_assessment.get('action_tier', 'MONITOR_ONLY')}",
            f"Entity: {entity_type} - {entity_id[:16]}...",
        ]
        
        # Add baseline context if available
        if baseline_deviation > 0.1:
            desc_parts.append(f"Baseline Deviation: {baseline_deviation:.0%} from regional norm")
        
        desc_parts.extend(["", "Contributing Factors:"])
        
        for factor in risk_assessment["contributing_factors"]:
            severity_indicator = "🔴" if factor.get("severity") == "HIGH" else "🟡" if factor.get("severity") == "MEDIUM" else "🟢"
            desc_parts.append(f"  {severity_indicator} {factor['rule_name']}: {factor['description']}")
        
        desc_parts.extend([
            "",
            f"Analysis Details:",
            f"  • Rule-based Score: {risk_assessment['rule_score']:.1f}/100",
            f"  • ML Anomaly Score: {risk_assessment['ml_score']:.1f}/100",
            f"  • Composite Score: {risk_assessment['composite_score']:.1f}/100"
        ])
        
        # Add confidence interpretation
        if confidence_score >= 0.8:
            desc_parts.append(f"  • High confidence detection - strong agreement between rule and ML systems")
        elif confidence_score >= 0.6:
            desc_parts.append(f"  • Medium confidence detection - moderate agreement between systems")
        else:
            desc_parts.append(f"  • Lower confidence detection - recommend additional verification")
        
        return "\n".join(desc_parts)
    
    def _save_enhanced_alert(self, alert: Dict):
        """Save enhanced alert to database"""
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO alerts 
                (alert_id, timestamp, severity, alert_type, title, description,
                 affected_region, service_category, risk_score, confidence_score,
                 action_tier, baseline_deviation, reason_codes, suggested_actions, 
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert["alert_id"],
                alert["timestamp"],
                alert["severity"],
                alert["alert_type"],
                alert["title"],
                alert["description"],
                alert["affected_region"],
                alert["service_category"],
                alert["risk_score"],
                alert["confidence_score"],
                alert["action_tier"],
                alert["baseline_deviation"],
                alert["reason_codes"],
                alert["suggested_actions"],
                alert["status"],
                datetime.now()
            ))
        finally:
            conn.close()
    
    def process_feedback(self, alert_id: str, feedback_type: str, 
                        user_id: str, feedback_notes: Optional[str] = None,
                        analyst_confidence: Optional[float] = None) -> bool:
        """Process analyst feedback for false positive learning"""
        conn = get_connection()
        try:
            # Update alert with feedback
            conn.execute("""
                UPDATE alerts 
                SET feedback_type = ?, feedback_by = ?, feedback_at = ?, 
                    feedback_notes = ?
                WHERE alert_id = ?
            """, (feedback_type, user_id, datetime.now(), feedback_notes, alert_id))
            
            # Trigger baseline learning adjustment
            baseline_engine.update_baseline_from_feedback(alert_id, feedback_type)
            
            # Log feedback for analysis
            print(f"Alert feedback processed: {alert_id} marked as {feedback_type} by {user_id}")
            if feedback_notes:
                print(f"  Notes: {feedback_notes}")
            
            return True
            
        except Exception as e:
            print(f"Error processing feedback: {e}")
            return False
        finally:
            conn.close()
    
    def get_alerts(self, status: Optional[str] = None, severity: Optional[str] = None,
                   limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve alerts with optional filters"""
        conditions = ["1=1"]
        params = []
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        
        query = f"""
            SELECT * FROM alerts 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        df = execute_query_df(query, tuple(params) if params else None)
        
        if df.empty:
            return []
        
        alerts = []
        for _, row in df.iterrows():
            alert = {
                "alert_id": row["alert_id"],
                "timestamp": row["timestamp"],
                "severity": row["severity"],
                "alert_type": row["alert_type"],
                "title": row["title"],
                "description": row["description"],
                "affected_region": row["affected_region"],
                "service_category": row["service_category"],
                "risk_score": row["risk_score"],
                "reason_codes": json.loads(row["reason_codes"]) if row["reason_codes"] else [],
                "suggested_actions": json.loads(row["suggested_actions"]) if row["suggested_actions"] else [],
                "status": row["status"],
                "acknowledged_by": row.get("acknowledged_by"),
                "acknowledged_at": row.get("acknowledged_at"),
                "resolved_at": row.get("resolved_at")
            }
            alerts.append(alert)
        
        return alerts
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Dict]:
        """Get a specific alert by ID"""
        query = "SELECT * FROM alerts WHERE alert_id = ?"
        df = execute_query_df(query, (alert_id,))
        
        if df.empty:
            return None
        
        row = df.iloc[0]
        return {
            "alert_id": row["alert_id"],
            "timestamp": row["timestamp"],
            "severity": row["severity"],
            "alert_type": row["alert_type"],
            "title": row["title"],
            "description": row["description"],
            "affected_region": row["affected_region"],
            "service_category": row["service_category"],
            "risk_score": row["risk_score"],
            "reason_codes": json.loads(row["reason_codes"]) if row["reason_codes"] else [],
            "suggested_actions": json.loads(row["suggested_actions"]) if row["suggested_actions"] else [],
            "status": row["status"],
            "acknowledged_by": row.get("acknowledged_by"),
            "acknowledged_at": row.get("acknowledged_at"),
            "resolved_at": row.get("resolved_at")
        }
    
    def update_alert_status(self, alert_id: str, status: str, 
                           user_id: Optional[str] = None) -> bool:
        """Update alert status"""
        conn = get_connection()
        try:
            if status == "ACKNOWLEDGED":
                conn.execute("""
                    UPDATE alerts 
                    SET status = ?, acknowledged_by = ?, acknowledged_at = ?
                    WHERE alert_id = ?
                """, (status, user_id, datetime.now(), alert_id))
            elif status == "RESOLVED":
                conn.execute("""
                    UPDATE alerts 
                    SET status = ?, resolved_at = ?
                    WHERE alert_id = ?
                """, (status, datetime.now(), alert_id))
            else:
                conn.execute("""
                    UPDATE alerts SET status = ? WHERE alert_id = ?
                """, (status, alert_id))
            return True
        except Exception as e:
            print(f"Error updating alert: {e}")
            return False
        finally:
            conn.close()
    
    def get_alert_statistics(self) -> Dict:
        """Get alert statistics for dashboard"""
        conn = get_connection()
        try:
            # Total active alerts
            active_count = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE status = 'ACTIVE'"
            ).fetchone()[0]
            
            # Critical alerts
            critical_count = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE severity = 'CRITICAL' AND status = 'ACTIVE'"
            ).fetchone()[0]
            
            # High severity alerts
            high_count = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE severity = 'HIGH' AND status = 'ACTIVE'"
            ).fetchone()[0]
            
            # Alerts by type
            by_type = conn.execute("""
                SELECT alert_type, COUNT(*) as count 
                FROM alerts WHERE status = 'ACTIVE'
                GROUP BY alert_type
            """).fetchall()
            
            # Alerts trend (last 7 days)
            trend = conn.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM alerts
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
                GROUP BY DATE(timestamp)
                ORDER BY date
            """).fetchall()
            
            return {
                "active_alerts": active_count,
                "critical_alerts": critical_count,
                "high_alerts": high_count,
                "by_type": [{"type": t[0], "count": t[1]} for t in by_type],
                "trend": [{"date": str(t[0]), "count": t[1]} for t in trend]
            }
        finally:
            conn.close()


# Singleton instance
alert_manager = AlertManager()


def run_periodic_analysis():
    """Run periodic analysis to detect anomalies and generate alerts"""
    # Analyze high-activity devices
    conn = get_connection()
    try:
        # Get devices with high activity in last hour
        high_activity_devices = conn.execute("""
            SELECT device_fingerprint_hash, COUNT(*) as event_count
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
            GROUP BY device_fingerprint_hash
            HAVING COUNT(*) > 10
            ORDER BY event_count DESC
            LIMIT 20
        """).fetchall()
        
        for device, count in high_activity_devices:
            assessment = risk_engine.analyze_entity("DEVICE", device, time_window_hours=1)
            if assessment["composite_score"] >= settings.RISK_MEDIUM_THRESHOLD:
                alert_manager.generate_alert(assessment, "DEVICE", device)
        
        # Analyze regions with anomalies
        high_risk_regions = conn.execute("""
            SELECT state_code, COUNT(*) as event_count,
                   AVG(retry_count) as avg_retries
            FROM authentication_events
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
            GROUP BY state_code
            HAVING AVG(retry_count) > 2 OR COUNT(*) > 100
        """).fetchall()
        
        for region, count, retries in high_risk_regions:
            assessment = risk_engine.analyze_entity("REGION", region, time_window_hours=1)
            if assessment["composite_score"] >= settings.RISK_MEDIUM_THRESHOLD:
                alert_manager.generate_alert(assessment, "REGION", region)
                
    finally:
        conn.close()
