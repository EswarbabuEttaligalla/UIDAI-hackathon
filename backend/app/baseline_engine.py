"""
Baseline Learning Engine for AMEWS
Manages the system's learning phase before active monitoring
Using DuckDB for fast analytical queries
"""
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.config import settings
from app.database import get_connection


@dataclass
class BaselineMetrics:
    """Baseline metrics for a specific context (region, service, time)"""
    auth_frequency_mean: float = 0.0
    auth_frequency_std: float = 0.0
    failure_rate_mean: float = 0.0
    failure_rate_std: float = 0.0
    otp_fallback_rate_mean: float = 0.0
    retry_count_mean: float = 0.0
    off_hours_rate_mean: float = 0.0
    sample_size: int = 0


class BaselineLearningEngine:
    """Manages baseline learning and adaptation"""
    
    def __init__(self):
        self.baseline_window_days = 14
        self.min_sample_size = 100
        self.confidence_threshold = 0.7
    
    def get_system_status(self) -> Dict:
        """Get current system baseline status"""
        conn = get_connection()
        try:
            # Check if baseline record exists
            baseline = conn.execute("""
                SELECT * FROM system_baseline 
                ORDER BY created_at DESC 
                LIMIT 1
            """).fetchone()
            
            if not baseline:
                # Initialize baseline if doesn't exist
                self._initialize_baseline()
                baseline = conn.execute("""
                    SELECT * FROM system_baseline 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """).fetchone()
            
            # Calculate completion percentage
            completion = self._calculate_baseline_completion()
            
            # Update completion in database
            conn.execute("""
                UPDATE system_baseline 
                SET completion_percentage = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE baseline_id = ?
            """, (completion, baseline[0]))
            
            # Determine system mode
            mode = "BASELINE_LEARNING"
            if completion >= 80.0:  # 80% completion threshold
                mode = "ACTIVE_MONITORING"
                # Update mode in database
                conn.execute("""
                    UPDATE system_baseline 
                    SET system_mode = ? 
                    WHERE baseline_id = ?
                """, (mode, baseline[0]))
            
            return {
                "system_mode": mode,
                "baseline_start_date": baseline[2],
                "baseline_window_days": baseline[3],
                "completion_percentage": completion,
                "next_retrain_at": baseline[5],
                "regions_covered": self._get_covered_regions(),
                "baseline_ready": completion >= 80.0
            }
        finally:
            conn.close()
    
    def _initialize_baseline(self):
        """Initialize baseline learning phase"""
        conn = get_connection()
        try:
            baseline_id = f"baseline_{uuid.uuid4().hex[:16]}"
            start_date = datetime.now() - timedelta(days=self.baseline_window_days)
            next_retrain = datetime.now() + timedelta(days=1)  # Daily retraining
            
            conn.execute("""
                INSERT INTO system_baseline (
                    baseline_id, system_mode, baseline_start_date, 
                    baseline_window_days, next_retrain_at
                ) VALUES (?, 'BASELINE_LEARNING', ?, ?, ?)
            """, (baseline_id, start_date, self.baseline_window_days, next_retrain))
        except Exception as e:
            raise
        finally:
            conn.close()
    
    def _calculate_baseline_completion(self) -> float:
        """Calculate baseline learning completion percentage"""
        conn = get_connection()
        try:
            # Count unique combinations of region, time_band, and service
            total_contexts = conn.execute("""
                SELECT COUNT(DISTINCT 
                    CONCAT(state_code, '|', hour_of_day, '|', service_category)
                ) as count 
                FROM authentication_events 
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 14 DAY
            """).fetchone()[0]
            
            # Count contexts with sufficient data
            sufficient_contexts = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT 
                        state_code, hour_of_day, service_category,
                        COUNT(*) as sample_size 
                    FROM authentication_events 
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 14 DAY 
                    GROUP BY state_code, hour_of_day, service_category 
                    HAVING COUNT(*) >= ?
                ) contexts
            """, (self.min_sample_size,)).fetchone()[0]
            
            if total_contexts == 0:
                return 0.0
            
            return min(100.0, (sufficient_contexts / total_contexts) * 100.0)
        except Exception as e:
            raise
        finally:
            conn.close()
    
    def _get_covered_regions(self) -> List[str]:
        """Get list of regions with sufficient baseline data"""
        conn = get_connection()
        try:
            regions = conn.execute("""
                SELECT DISTINCT state_code 
                FROM authentication_events 
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 14 DAY 
                GROUP BY state_code 
                HAVING COUNT(*) >= ?
            """, (self.min_sample_size,)).fetchall()
            
            return [r[0] for r in regions]
        except Exception as e:
            raise
        finally:
            conn.close()
    
    def compute_region_baseline(self, region_code: str, 
                               time_band: str = "all",
                               service_category: str = "all") -> BaselineMetrics:
        """Compute baseline metrics for a specific region/context"""
        conn = get_connection()
        try:
            conditions = ["timestamp >= CURRENT_TIMESTAMP - INTERVAL 14 DAY"]
            params = []
            
            if region_code != "all":
                conditions.append("state_code = ?")
                params.append(region_code)
            
            if service_category != "all":
                conditions.append("service_category = ?")
                params.append(service_category)
            
            if time_band != "all":
                if time_band.startswith("hour_"):
                    hour = int(time_band.split("_")[1])
                    conditions.append("hour_of_day = ?")
                    params.append(hour)
                elif time_band.startswith("dow_"):
                    dow = int(time_band.split("_")[1])
                    conditions.append("day_of_week = ?")
                    params.append(dow)
            
            where_clause = " AND ".join(conditions)
            
            # Get aggregated metrics
            metrics_query = f"""
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT device_fingerprint_hash) as unique_devices,
                    AVG(CASE WHEN status = 'FAILURE' THEN 1.0 ELSE 0.0 END) as failure_rate,
                    AVG(CASE WHEN is_fallback THEN 1.0 ELSE 0.0 END) as otp_fallback_rate,
                    AVG(retry_count) as avg_retries,
                    AVG(CASE WHEN hour_of_day BETWEEN 23 AND 5 THEN 1.0 ELSE 0.0 END) as off_hours_rate,
                    STDDEV(retry_count) as retry_std 
                FROM authentication_events 
                WHERE {where_clause}
            """
            
            result = conn.execute(metrics_query, params).fetchone()
            
            if not result or result[0] == 0:
                return BaselineMetrics()
            
            # Calculate frequency metrics by device
            freq_query = f"""
                SELECT 
                    device_fingerprint_hash,
                    COUNT(*) as event_count,
                    COUNT(*) * 24.0 / (EXTRACT(EPOCH FROM 
                    (MAX(timestamp) - MIN(timestamp))) / 3600.0 + 0.1) as events_per_hour 
                FROM authentication_events 
                WHERE {where_clause} 
                GROUP BY device_fingerprint_hash 
                HAVING COUNT(*) >= 5
            """
            
            freq_results = conn.execute(freq_query, params).fetchall()
            
            if freq_results:
                freq_values = [r[2] for r in freq_results]
                auth_freq_mean = sum(freq_values) / len(freq_values)
                auth_freq_std = (sum((x - auth_freq_mean) ** 2 for x in freq_values) / 
                               len(freq_values)) ** 0.5 if len(freq_values) > 1 else 0.0
            else:
                auth_freq_mean = 0.0
                auth_freq_std = 0.0
            
            return BaselineMetrics(
                auth_frequency_mean=auth_freq_mean,
                auth_frequency_std=auth_freq_std,
                failure_rate_mean=result[2] or 0.0,
                failure_rate_std=0.05,  # Estimated variance
                otp_fallback_rate_mean=result[3] or 0.0,
                retry_count_mean=result[4] or 0.0,
                off_hours_rate_mean=result[5] or 0.0,
                sample_size=result[0]
            )
        except Exception as e:
            raise
        finally:
            conn.close()
    
    def store_baseline(self, region_code: str, time_band: str,
                      service_category: str, metrics: BaselineMetrics):
        """Store computed baseline metrics"""
        conn = get_connection()
        try:
            baseline_id = f"reg_{uuid.uuid4().hex[:16]}"
            
            conn.execute("""
                INSERT OR REPLACE INTO region_baselines (
                    baseline_id, region_code, time_band, service_category,
                    auth_frequency_mean, auth_frequency_std,
                    failure_rate_mean, failure_rate_std,
                    otp_fallback_rate_mean, retry_count_mean,
                    off_hours_rate_mean, sample_size, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                baseline_id, region_code, time_band, service_category,
                metrics.auth_frequency_mean, metrics.auth_frequency_std,
                metrics.failure_rate_mean, metrics.failure_rate_std,
                metrics.otp_fallback_rate_mean, metrics.retry_count_mean,
                metrics.off_hours_rate_mean, metrics.sample_size
            ))
        except Exception as e:
            raise
        finally:
            conn.close()
    
    def get_baseline_deviation(self, entity_type: str, entity_id: str,
                              current_metrics: Dict) -> float:
        """Calculate deviation from baseline for equity guardrail"""
        if entity_type == "REGION":
            region_baseline = self.compute_region_baseline(entity_id)
            
            if region_baseline.sample_size < self.min_sample_size:
                return 0.0  # No baseline available
            
            # Calculate normalized deviation
            failure_dev = 0.0
            if region_baseline.failure_rate_mean > 0:
                failure_dev = abs(current_metrics.get("failure_rate", 0) - 
                                region_baseline.failure_rate_mean) / region_baseline.failure_rate_mean
            
            freq_dev = 0.0
            if region_baseline.auth_frequency_mean > 0:
                freq_dev = abs(current_metrics.get("auth_frequency", 0) - 
                             region_baseline.auth_frequency_mean) / region_baseline.auth_frequency_mean
            
            # Weighted average deviation
            return min(1.0, (failure_dev * 0.6 + freq_dev * 0.4))
        
        return 0.0
    
    def update_baseline_from_feedback(self, alert_id: str, feedback_type: str):
        """Update baseline sensitivity based on analyst feedback (simulated)"""
        conn = get_connection()
        try:
            # Get alert details
            alert = conn.execute("""
                SELECT affected_region, alert_type, confidence_score 
                FROM alerts WHERE alert_id = ?
            """, (alert_id,)).fetchone()
            
            if not alert:
                return
            
            region_code = alert[0]
            alert_type = alert[1]
            confidence = alert[2]
            
            # Log feedback adjustment (simulation only)
            adjustment_factor = 0.95 if feedback_type == "FALSE_POSITIVE" else 1.05
            
            # For testing, we log the simulated adjustment
            # In production, this would update model weights or thresholds
            print(f"Simulated baseline adjustment for {region_code}:")
            print(f"  Alert type: {alert_type}")
            print(f"  Feedback: {feedback_type}")
            print(f"  Confidence factor adjusted by: {adjustment_factor}")
            print(f"  Future similar alerts in {region_code} will have adjusted sensitivity")
        except Exception as e:
            raise
        finally:
            conn.close()


# Global baseline engine instance
baseline_engine = BaselineLearningEngine()
