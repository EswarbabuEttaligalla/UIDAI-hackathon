"""
Dataset Loader for AMEWS
Loads and processes the actual UIDAI datasets for training and analysis
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib

# Dataset paths
DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")
DEMOGRAPHIC_DIR = os.path.join(DATASETS_DIR, "demographic", "api_data_aadhar_demographic")
ENROLMENT_DIR = os.path.join(DATASETS_DIR, "enrolment", "api_data_aadhar_enrolment")


class DatasetLoader:
    """Load and process UIDAI datasets"""
    
    def __init__(self):
        self.demographic_data = None
        self.enrolment_data = None
        self.regional_stats = None
        self.loaded = False
        
    def load_demographic_data(self) -> pd.DataFrame:
        """Load all demographic data files"""
        if self.demographic_data is not None:
            return self.demographic_data
            
        all_files = []
        if os.path.exists(DEMOGRAPHIC_DIR):
            for file in os.listdir(DEMOGRAPHIC_DIR):
                if file.endswith('.csv'):
                    filepath = os.path.join(DEMOGRAPHIC_DIR, file)
                    try:
                        df = pd.read_csv(filepath)
                        all_files.append(df)
                    except Exception as e:
                        print(f"Error loading {file}: {e}")
        
        if all_files:
            self.demographic_data = pd.concat(all_files, ignore_index=True)
            print(f"Loaded {len(self.demographic_data)} demographic records")
        else:
            self.demographic_data = pd.DataFrame()
            print("No demographic data found")
            
        return self.demographic_data
    
    def load_enrolment_data(self) -> pd.DataFrame:
        """Load all enrolment data files"""
        if self.enrolment_data is not None:
            return self.enrolment_data
            
        all_files = []
        if os.path.exists(ENROLMENT_DIR):
            for file in os.listdir(ENROLMENT_DIR):
                if file.endswith('.csv'):
                    filepath = os.path.join(ENROLMENT_DIR, file)
                    try:
                        df = pd.read_csv(filepath)
                        all_files.append(df)
                    except Exception as e:
                        print(f"Error loading {file}: {e}")
        
        if all_files:
            self.enrolment_data = pd.concat(all_files, ignore_index=True)
            print(f"Loaded {len(self.enrolment_data)} enrolment records")
        else:
            self.enrolment_data = pd.DataFrame()
            print("No enrolment data found")
            
        return self.enrolment_data
    
    def load_all(self) -> bool:
        """Load all datasets"""
        try:
            self.load_demographic_data()
            self.load_enrolment_data()
            self.compute_regional_stats()
            self.loaded = True
            return True
        except Exception as e:
            print(f"Error loading datasets: {e}")
            return False
    
    def compute_regional_stats(self) -> Dict:
        """Compute regional statistics from datasets"""
        stats = {}
        
        # Process demographic data
        if self.demographic_data is not None and not self.demographic_data.empty:
            demo_df = self.demographic_data.copy()
            
            # State-level aggregation
            state_stats = demo_df.groupby('state').agg({
                'pincode': 'count',  # Number of records
            }).reset_index()
            state_stats.columns = ['state', 'record_count']
            
            stats['states'] = state_stats.to_dict('records')
            stats['unique_states'] = demo_df['state'].nunique()
            stats['unique_districts'] = demo_df['district'].nunique()
            stats['total_demographic_records'] = len(demo_df)
        
        # Process enrolment data
        if self.enrolment_data is not None and not self.enrolment_data.empty:
            enrol_df = self.enrolment_data.copy()
            
            # Daily enrolment trends
            if 'date' in enrol_df.columns:
                daily_stats = enrol_df.groupby('date').size().reset_index(name='count')
                stats['daily_enrolments'] = daily_stats.to_dict('records')
            
            stats['total_enrolment_records'] = len(enrol_df)
            
            # Age distribution
            age_cols = [c for c in enrol_df.columns if 'age' in c.lower()]
            if age_cols:
                age_totals = {col: int(enrol_df[col].sum()) for col in age_cols}
                stats['age_distribution'] = age_totals
        
        self.regional_stats = stats
        return stats
    
    def get_state_baseline(self, state: str) -> Dict:
        """Get baseline metrics for a state"""
        baseline = {
            'avg_daily_events': 1000,
            'peak_hours': [9, 10, 11, 14, 15, 16],
            'weekend_multiplier': 0.3,
            'expected_failure_rate': 0.05
        }
        
        if self.demographic_data is not None and not self.demographic_data.empty:
            state_data = self.demographic_data[self.demographic_data['state'] == state]
            if not state_data.empty:
                # Calculate baseline from actual data
                baseline['record_count'] = len(state_data)
                baseline['districts'] = state_data['district'].nunique()
        
        return baseline
    
    def get_district_baseline(self, state: str, district: str) -> Dict:
        """Get baseline metrics for a district"""
        baseline = {
            'avg_daily_events': 100,
            'expected_failure_rate': 0.05
        }
        
        if self.demographic_data is not None and not self.demographic_data.empty:
            district_data = self.demographic_data[
                (self.demographic_data['state'] == state) & 
                (self.demographic_data['district'] == district)
            ]
            if not district_data.empty:
                baseline['record_count'] = len(district_data)
        
        return baseline
    
    def generate_auth_events_from_data(self, count: int = 1000) -> List[Dict]:
        """Generate realistic auth events based on actual dataset patterns"""
        import random
        from datetime import timedelta
        
        events = []
        
        # Get unique state/district combinations from data
        if self.demographic_data is not None and not self.demographic_data.empty:
            locations = self.demographic_data[['state', 'district', 'pincode']].drop_duplicates()
            locations_list = locations.to_dict('records')
        else:
            locations_list = [
                {'state': 'Maharashtra', 'district': 'Mumbai', 'pincode': '400001'},
                {'state': 'Karnataka', 'district': 'Bengaluru Urban', 'pincode': '560001'},
                {'state': 'Delhi', 'district': 'New Delhi', 'pincode': '110001'},
            ]
        
        auth_types = ['OTP', 'BIOMETRIC', 'DEMOGRAPHIC']
        service_categories = ['BANKING', 'TELECOM', 'WELFARE', 'GOVERNMENT', 'HEALTHCARE']
        
        for i in range(count):
            location = random.choice(locations_list)
            timestamp = datetime.now() - timedelta(
                hours=random.randint(0, 168),
                minutes=random.randint(0, 59)
            )
            
            hour = timestamp.hour
            # More activity during business hours
            if 9 <= hour <= 18:
                auth_type_weights = [0.4, 0.4, 0.2]
            else:
                auth_type_weights = [0.6, 0.25, 0.15]
            
            auth_type = random.choices(auth_types, weights=auth_type_weights)[0]
            
            # Generate device hash based on location for realistic patterns
            device_seed = f"{location['state']}_{location['district']}_{random.randint(1, 100)}"
            device_hash = hashlib.sha256(device_seed.encode()).hexdigest()[:32]
            
            # Failure rates vary by auth type
            failure_rates = {'OTP': 0.03, 'BIOMETRIC': 0.08, 'DEMOGRAPHIC': 0.12}
            is_failure = random.random() < failure_rates[auth_type]
            
            event = {
                'event_id': f"evt_{hashlib.md5(f'{i}_{timestamp}'.encode()).hexdigest()[:16]}",
                'timestamp': timestamp,
                'auth_type': auth_type,
                'service_category': random.choice(service_categories),
                'service_provider_id': f"SP_{random.randint(1000, 9999)}",
                'device_fingerprint_hash': device_hash,
                'state_code': location['state'][:2].upper(),
                'district_code': location['district'][:3].upper(),
                'state_name': location['state'],
                'district_name': location['district'],
                'pincode': str(location.get('pincode', '000000')),
                'retry_count': int(random.choices([0, 1, 2, 3], weights=[0.8, 0.12, 0.05, 0.03])[0]),
                'is_fallback': random.random() < 0.08,
                'status': 'FAILURE' if is_failure else 'SUCCESS',
                'failure_reason': random.choice(['OTP_EXPIRED', 'BIOMETRIC_MISMATCH', 'TIMEOUT']) if is_failure else None,
                'hour_of_day': int(hour),
                'day_of_week': int(timestamp.weekday()),
                'session_duration_ms': int(random.expovariate(1/2000) + 500),
            }
            events.append(event)
        
        return events
    
    def get_training_features(self) -> Tuple[np.ndarray, List[str]]:
        """Extract features for ML training from datasets"""
        features = []
        feature_names = []
        
        if self.enrolment_data is not None and not self.enrolment_data.empty:
            enrol_df = self.enrolment_data.copy()
            
            # Aggregate by state
            state_agg = enrol_df.groupby('state').agg({
                'age_0_5': 'sum',
                'age_5_17': 'sum', 
                'age_18_greater': 'sum'
            }).reset_index()
            
            feature_names = ['age_0_5', 'age_5_17', 'age_18_greater']
            features = state_agg[feature_names].values
        
        return np.array(features) if len(features) > 0 else np.array([]), feature_names


# Singleton instance
dataset_loader = DatasetLoader()


def get_dataset_loader() -> DatasetLoader:
    """Get the dataset loader singleton"""
    if not dataset_loader.loaded:
        dataset_loader.load_all()
    return dataset_loader
