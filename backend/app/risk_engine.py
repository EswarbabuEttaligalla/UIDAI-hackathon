"""
Risk Analysis Engine for AMEWS
Combines rule-based checks with ML anomaly detection, confidence scoring, and action tiers
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import pickle
import os

from app.database import get_connection, execute_query_df
from app.config import settings
from app.baseline_engine import baseline_engine

# Risk score weights
RULE_WEIGHT = 0.6
ML_WEIGHT = 0.4

class RuleBasedAnalyzer:
    """Rule-based risk analysis component"""
    
    def __init__(self):
        self.rules = [
            self.check_auth_frequency,
            self.check_geographic_velocity,
            self.check_otp_fallback_abuse,
            self.check_retry_loops,
            self.check_off_hours_activity,
            self.check_failure_rate,
            self.check_session_duration_anomaly,
        ]
    
    def analyze(self, events_df) -> List[Dict]:
        """Run all rules and return risk factors"""
        risk_factors = []
        
        for rule in self.rules:
            try:
                result = rule(events_df)
                if result:
                    risk_factors.append(result)
            except Exception as e:
                print(f"Rule {rule.__name__} failed: {e}")
        
        return risk_factors
    
    def check_auth_frequency(self, df) -> Optional[Dict]:
        """Check for excessive authentication frequency"""
        if df.empty:
            return None
            
        # Group by device and count events per hour
        time_range_hours = max((df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600, 1)
        events_per_hour = len(df) / time_range_hours
        
        # Threshold: More than 20 events per hour from same entity
        if events_per_hour > 20:
            severity = "HIGH" if events_per_hour > 50 else "MEDIUM"
            return {
                "rule_name": "HIGH_AUTH_FREQUENCY",
                "contribution": min(30, events_per_hour),
                "description": f"Excessive authentication rate: {events_per_hour:.1f} events/hour",
                "severity": severity
            }
        return None
    
    def check_geographic_velocity(self, df) -> Optional[Dict]:
        """Check for rapid geographic changes (impossible travel)"""
        if len(df) < 2:
            return None
        
        df_sorted = df.sort_values('timestamp')
        unique_states = df_sorted['state_code'].nunique()
        time_span_hours = max((df_sorted['timestamp'].max() - df_sorted['timestamp'].min()).total_seconds() / 3600, 0.1)
        
        # If accessing from multiple states in short time
        states_per_hour = unique_states / time_span_hours
        
        if states_per_hour > 2:  # More than 2 different states per hour
            return {
                "rule_name": "GEOGRAPHIC_VELOCITY_ANOMALY",
                "contribution": min(25, states_per_hour * 5),
                "description": f"Rapid location changes: {unique_states} states in {time_span_hours:.1f} hours",
                "severity": "HIGH"
            }
        return None
    
    def check_otp_fallback_abuse(self, df) -> Optional[Dict]:
        """Check for excessive OTP fallback usage"""
        if df.empty:
            return None
        
        otp_events = df[df['auth_type'] == 'OTP']
        fallback_events = df[df['is_fallback'] == True]
        
        if len(otp_events) == 0:
            return None
            
        fallback_ratio = len(fallback_events) / len(df)
        
        if fallback_ratio > 0.3:  # More than 30% fallbacks
            severity = "HIGH" if fallback_ratio > 0.5 else "MEDIUM"
            return {
                "rule_name": "OTP_FALLBACK_ABUSE",
                "contribution": min(20, fallback_ratio * 40),
                "description": f"High OTP fallback rate: {fallback_ratio*100:.1f}% of authentications",
                "severity": severity
            }
        return None
    
    def check_retry_loops(self, df) -> Optional[Dict]:
        """Check for abnormal retry patterns"""
        if df.empty:
            return None
        
        avg_retries = df['retry_count'].mean()
        high_retry_events = len(df[df['retry_count'] >= 3])
        
        if avg_retries > 2 or high_retry_events > len(df) * 0.2:
            severity = "MEDIUM" if avg_retries < 4 else "HIGH"
            return {
                "rule_name": "ABNORMAL_RETRY_PATTERN",
                "contribution": min(15, avg_retries * 5),
                "description": f"Excessive retries: avg {avg_retries:.1f}, {high_retry_events} high-retry events",
                "severity": severity
            }
        return None
    
    def check_off_hours_activity(self, df) -> Optional[Dict]:
        """Check for authentication during unusual hours"""
        if df.empty:
            return None
        
        # Off hours: 11 PM to 5 AM
        off_hours_events = df[(df['hour_of_day'] >= 23) | (df['hour_of_day'] <= 5)]
        off_hours_ratio = len(off_hours_events) / len(df)
        
        if off_hours_ratio > 0.4:  # More than 40% off-hours
            return {
                "rule_name": "OFF_HOURS_ACTIVITY",
                "contribution": min(15, off_hours_ratio * 30),
                "description": f"Unusual timing: {off_hours_ratio*100:.1f}% of events during off-hours (11PM-5AM)",
                "severity": "MEDIUM"
            }
        return None
    
    def check_failure_rate(self, df) -> Optional[Dict]:
        """Check for abnormal failure rates"""
        if df.empty:
            return None
        
        failures = df[df['status'] == 'FAILURE']
        failure_rate = len(failures) / len(df)
        
        if failure_rate > 0.3:  # More than 30% failures
            severity = "HIGH" if failure_rate > 0.5 else "MEDIUM"
            return {
                "rule_name": "HIGH_FAILURE_RATE",
                "contribution": min(20, failure_rate * 40),
                "description": f"High failure rate: {failure_rate*100:.1f}% of authentications failed",
                "severity": severity
            }
        return None
    
    def check_session_duration_anomaly(self, df) -> Optional[Dict]:
        """Check for abnormal session durations"""
        if df.empty or 'session_duration_ms' not in df.columns:
            return None
        
        avg_duration = df['session_duration_ms'].mean()
        std_duration = df['session_duration_ms'].std()
        
        # Very short or very long sessions
        if avg_duration < 200 or avg_duration > 30000:
            return {
                "rule_name": "SESSION_DURATION_ANOMALY",
                "contribution": 10,
                "description": f"Unusual session duration: avg {avg_duration:.0f}ms",
                "severity": "LOW"
            }
        return None


class MLAnomalyDetector:
    """Machine Learning based anomaly detection"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = os.path.join(os.path.dirname(__file__), "..", "models", "isolation_forest.pkl")
        self.scaler_path = os.path.join(os.path.dirname(__file__), "..", "models", "scaler.pkl")
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            else:
                self._create_new_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            self._create_new_model()
    
    def _create_new_model(self):
        """Create a new Isolation Forest model"""
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,  # Expected 5% anomalies
            random_state=42,
            n_jobs=-1
        )
    
    def _extract_features(self, df) -> np.ndarray:
        """Extract features for ML model"""
        if df.empty:
            return np.array([])
        
        features = []
        
        # Aggregate features
        features.append(len(df))  # Event count
        features.append(df['retry_count'].mean())
        features.append(df['retry_count'].max())
        features.append(df['is_fallback'].mean())
        features.append(len(df[df['status'] == 'FAILURE']) / max(len(df), 1))
        features.append(df['hour_of_day'].std() if len(df) > 1 else 0)
        features.append(df['state_code'].nunique())
        features.append(df['service_category'].nunique())
        features.append(df['session_duration_ms'].mean())
        features.append(df['session_duration_ms'].std() if len(df) > 1 else 0)
        
        # Off-hours ratio
        off_hours = len(df[(df['hour_of_day'] >= 23) | (df['hour_of_day'] <= 5)])
        features.append(off_hours / max(len(df), 1))
        
        # OTP ratio
        otp_events = len(df[df['auth_type'] == 'OTP'])
        features.append(otp_events / max(len(df), 1))
        
        return np.array(features).reshape(1, -1)
    
    def train(self, training_data_df):
        """Train the model on normal behavior data"""
        if training_data_df.empty:
            return
        
        # Group by device and extract features for each
        feature_list = []
        devices = training_data_df['device_fingerprint_hash'].unique()
        
        for device in devices[:1000]:  # Limit for performance
            device_df = training_data_df[training_data_df['device_fingerprint_hash'] == device]
            features = self._extract_features(device_df)
            if features.size > 0:
                feature_list.append(features.flatten())
        
        if not feature_list:
            return
            
        X = np.array(feature_list)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Fit scaler and transform
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled)
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
    
    def predict_anomaly_score(self, df) -> Tuple[float, float]:
        """
        Predict anomaly score for given events
        Returns: (anomaly_score 0-100, confidence 0-1)
        """
        if df.empty:
            return 0.0, 0.0
        
        features = self._extract_features(df)
        if features.size == 0:
            return 0.0, 0.0
        
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        
        try:
            # Check if scaler is fitted
            if not hasattr(self.scaler, 'mean_') or self.scaler.mean_ is None:
                # Use Z-score fallback if model not trained
                return self._zscore_fallback(df)
            
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly score (-1 for anomaly, 1 for normal)
            raw_score = self.model.decision_function(features_scaled)[0]
            
            # Convert to 0-100 scale (lower decision function = more anomalous)
            # Typical range is -0.5 to 0.5
            anomaly_score = max(0, min(100, 50 - raw_score * 100))
            
            # Confidence based on distance from threshold
            confidence = min(1.0, abs(raw_score) * 2)
            
            return anomaly_score, confidence
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return self._zscore_fallback(df)
    
    def _zscore_fallback(self, df) -> Tuple[float, float]:
        """Fallback to Z-score based anomaly detection"""
        if df.empty:
            return 0.0, 0.0
        
        # Calculate z-scores for key metrics
        z_scores = []
        
        # Retry count
        if df['retry_count'].mean() > 1:
            z_scores.append(min(3, df['retry_count'].mean()))
        
        # Failure rate
        failure_rate = len(df[df['status'] == 'FAILURE']) / len(df)
        if failure_rate > 0.1:
            z_scores.append(min(3, failure_rate * 10))
        
        # Off hours ratio
        off_hours = len(df[(df['hour_of_day'] >= 23) | (df['hour_of_day'] <= 5)]) / len(df)
        if off_hours > 0.2:
            z_scores.append(min(3, off_hours * 5))
        
        if not z_scores:
            return 0.0, 0.5
        
        avg_zscore = np.mean(z_scores)
        anomaly_score = min(100, avg_zscore * 25)
        confidence = 0.6  # Lower confidence for fallback
        
        return anomaly_score, confidence


class RiskAnalysisEngine:
    """Main risk analysis engine combining rules and ML"""
    
    def __init__(self):
        self.rule_analyzer = RuleBasedAnalyzer()
        self.ml_detector = MLAnomalyDetector()
    
    def analyze_entity(self, entity_type: str, entity_id: str, 
                       time_window_hours: int = 24) -> Dict:
        """
        Analyze risk for a specific entity with confidence scoring and action tiers
        Returns comprehensive risk assessment with baseline deviation
        """
        # Fetch relevant events
        events_df = self._fetch_events(entity_type, entity_id, time_window_hours)
        
        if events_df.empty:
            return {
                "score_id": f"score_{uuid.uuid4().hex[:12]}",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "composite_score": 0.0,
                "risk_level": "LOW",
                "rule_score": 0.0,
                "ml_score": 0.0,
                "confidence_score": 0.0,
                "action_tier": "MONITOR_ONLY",
                "baseline_deviation": 0.0,
                "contributing_factors": [],
                "timestamp": datetime.now()
            }
        
        # Run rule-based analysis
        risk_factors = self.rule_analyzer.analyze(events_df)
        rule_score = sum(f["contribution"] for f in risk_factors)
        
        # Run ML anomaly detection
        ml_score, ml_confidence = self.ml_detector.predict_anomaly_score(events_df)
        
        # Calculate confidence score (agreement between rules and ML)
        confidence_score = self._calculate_confidence_score(risk_factors, ml_score, ml_confidence)
        
        # Equity guardrail: Calculate baseline deviation
        baseline_deviation = self._calculate_baseline_deviation(entity_type, entity_id, events_df)
        
        # Apply equity normalization if needed
        normalized_rule_score = self._apply_equity_normalization(
            rule_score, baseline_deviation, entity_type, entity_id
        )
        
        # Combine scores
        composite_score = (normalized_rule_score * RULE_WEIGHT + ml_score * ML_WEIGHT)
        composite_score = min(100, max(0, composite_score))
        
        # Determine risk level and action tier
        risk_level = self._get_risk_level(composite_score)
        action_tier = self._determine_action_tier(composite_score, confidence_score, risk_factors)
        
        # If ML has low confidence, add a note
        if ml_confidence < 0.5 and ml_score > 30:
            risk_factors.append({
                "rule_name": "ML_ANOMALY_DETECTED",
                "contribution": ml_score * ML_WEIGHT,
                "description": f"ML model detected potential anomaly (confidence: {ml_confidence:.0%})",
                "severity": "MEDIUM" if ml_score < 60 else "HIGH"
            })
        
        # Add baseline context if available
        if baseline_deviation > 0.3:
            risk_factors.append({
                "rule_name": "BASELINE_DEVIATION",
                "contribution": baseline_deviation * 10,
                "description": f"Significant deviation from regional baseline ({baseline_deviation:.0%})",
                "severity": "MEDIUM"
            })
        
        return {
            "score_id": f"score_{uuid.uuid4().hex[:12]}",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "composite_score": round(composite_score, 2),
            "risk_level": risk_level,
            "rule_score": round(normalized_rule_score, 2),
            "ml_score": round(ml_score, 2),
            "confidence_score": round(confidence_score, 3),
            "action_tier": action_tier,
            "baseline_deviation": round(baseline_deviation, 3),
            "contributing_factors": risk_factors,
            "timestamp": datetime.now()
        }
    
    def _calculate_confidence_score(self, risk_factors: List[Dict], 
                                   ml_score: float, ml_confidence: float) -> float:
        """
        Calculate confidence score based on agreement between rules and ML
        Returns: 0.0-1.0 confidence score
        """
        # Rule-based score
        rule_score = sum(f["contribution"] for f in risk_factors)
        
        # Normalize scores to 0-1
        normalized_rule = min(1.0, rule_score / 100.0)
        normalized_ml = min(1.0, ml_score / 100.0)
        
        # Agreement: how close are the normalized scores?
        agreement = 1.0 - abs(normalized_rule - normalized_ml)
        
        # High-confidence scenarios
        if normalized_rule > 0.8 and normalized_ml > 0.8:  # Both high
            return min(1.0, 0.9 + agreement * 0.1)
        if normalized_rule < 0.2 and normalized_ml < 0.2:  # Both low
            return min(1.0, 0.85 + agreement * 0.15)
        
        # Incorporate ML confidence
        base_confidence = (agreement + ml_confidence) / 2.0
        
        # Number of triggered rules adds confidence
        rule_count_bonus = min(0.2, len(risk_factors) * 0.05)
        
        # Severity consistency adds confidence
        severity_bonus = 0.0
        if risk_factors:
            high_severity = sum(1 for f in risk_factors if f.get("severity") in ["HIGH", "CRITICAL"])
            if high_severity > 0:
                severity_bonus = min(0.15, high_severity * 0.05)
        
        final_confidence = min(1.0, base_confidence + rule_count_bonus + severity_bonus)
        
        return final_confidence
    
    def _calculate_baseline_deviation(self, entity_type: str, entity_id: str, events_df) -> float:
        """Calculate deviation from baseline for equity guardrail"""
        try:
            # Get current metrics
            if events_df.empty:
                return 0.0
            
            current_metrics = {
                "failure_rate": len(events_df[events_df['status'] == 'FAILURE']) / len(events_df),
                "auth_frequency": len(events_df) / 24.0,  # events per hour
                "retry_rate": events_df['retry_count'].mean(),
                "off_hours_rate": len(events_df[(events_df['hour_of_day'] >= 23) | 
                                               (events_df['hour_of_day'] <= 5)]) / len(events_df)
            }
            
            return baseline_engine.get_baseline_deviation(entity_type, entity_id, current_metrics)
            
        except Exception as e:
            print(f"Baseline deviation calculation error: {e}")
            return 0.0
    
    def _apply_equity_normalization(self, rule_score: float, baseline_deviation: float,
                                   entity_type: str, entity_id: str) -> float:
        """Apply equity guardrail normalization"""
        if entity_type != "REGION" or baseline_deviation == 0.0:
            return rule_score
        
        # For regions with known baseline patterns, normalize the score
        # If this region historically has higher failure rates due to infrastructure,
        # don't penalize it as heavily
        
        # Get system status to check if baseline is ready
        system_status = baseline_engine.get_system_status()
        if not system_status.get("baseline_ready", False):
            return rule_score  # No normalization during baseline learning
        
        # Apply gentle normalization - reduce score if this is normal for the region
        if baseline_deviation < 0.5:  # Within normal range for this region
            normalization_factor = 0.85  # Slight reduction
        elif baseline_deviation < 0.3:  # Well within normal range
            normalization_factor = 0.75  # More significant reduction
        else:
            normalization_factor = 1.0  # No reduction for truly anomalous behavior
        
        normalized_score = rule_score * normalization_factor
        
        print(f"Equity normalization for {entity_id}: {rule_score:.1f} -> {normalized_score:.1f} "
              f"(deviation: {baseline_deviation:.1f}, factor: {normalization_factor})")
        
        return normalized_score
    
    def _determine_action_tier(self, composite_score: float, confidence_score: float, 
                              risk_factors: List[Dict]) -> str:
        """
        Determine recommended action tier based on risk score, confidence, and factors
        """
        # Critical scenarios requiring immediate response
        if composite_score >= 85 and confidence_score >= 0.8:
            return "IMMEDIATE_RESPONSE"
        
        if composite_score >= 70:
            # Check for specific high-risk patterns
            velocity_attack = any(f.get("rule_name") == "HIGH_AUTH_FREQUENCY" for f in risk_factors)
            geographic_anomaly = any(f.get("rule_name") == "GEOGRAPHIC_VELOCITY_ANOMALY" for f in risk_factors)
            
            if velocity_attack and confidence_score >= 0.7:
                return "DEVICE_BLACKLIST"
            if geographic_anomaly and confidence_score >= 0.6:
                return "ESCALATE_REGIONAL"
            
            return "ENHANCED_REVIEW"
        
        if composite_score >= 50 and confidence_score >= 0.6:
            return "ENHANCED_REVIEW"
        
        if composite_score >= 30:
            return "MONITOR_ONLY"
        
        return "MONITOR_ONLY"
    
    def analyze_batch(self, events_df) -> Dict:
        """Analyze a batch of events for overall risk"""
        if events_df.empty:
            return {
                "composite_score": 0.0,
                "risk_level": "LOW",
                "contributing_factors": []
            }
        
        risk_factors = self.rule_analyzer.analyze(events_df)
        rule_score = sum(f["contribution"] for f in risk_factors)
        
        ml_score, _ = self.ml_detector.predict_anomaly_score(events_df)
        
        composite_score = min(100, (rule_score * RULE_WEIGHT + ml_score * ML_WEIGHT))
        
        return {
            "composite_score": round(composite_score, 2),
            "risk_level": self._get_risk_level(composite_score),
            "rule_score": round(rule_score, 2),
            "ml_score": round(ml_score, 2),
            "contributing_factors": risk_factors
        }
    
    def _fetch_events(self, entity_type: str, entity_id: str, 
                      time_window_hours: int) -> 'pd.DataFrame':
        """Fetch events for analysis"""
        start_time = datetime.now() - timedelta(hours=time_window_hours)
        
        if entity_type == "DEVICE":
            query = """
                SELECT * FROM authentication_events 
                WHERE device_fingerprint_hash = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """
        elif entity_type == "REGION":
            query = """
                SELECT * FROM authentication_events 
                WHERE state_code = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """
        elif entity_type == "SERVICE_PROVIDER":
            query = """
                SELECT * FROM authentication_events 
                WHERE service_provider_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """
        else:
            return execute_query_df("SELECT * FROM authentication_events WHERE 1=0")
        
        return execute_query_df(query, (entity_id, start_time))
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score >= settings.RISK_HIGH_THRESHOLD:
            return "CRITICAL" if score >= 90 else "HIGH"
        elif score >= settings.RISK_MEDIUM_THRESHOLD:
            return "MEDIUM"
        elif score >= settings.RISK_LOW_THRESHOLD:
            return "LOW"
        return "LOW"
    
    def train_ml_model(self):
        """Train the ML model on historical data"""
        # Fetch last 30 days of data for training
        query = """
            SELECT * FROM authentication_events 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
        """
        try:
            df = execute_query_df(query)
            if not df.empty:
                self.ml_detector.train(df)
                return True
        except Exception as e:
            print(f"Training failed: {e}")
        return False


# Singleton instance
risk_engine = RiskAnalysisEngine()
