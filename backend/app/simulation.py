"""
Simulation Module for AMEWS
Generates synthetic misuse scenarios for testing purposes
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio

from app.data_generator import SyntheticDataGenerator, STATES
from app.database import get_connection
from app.risk_engine import risk_engine
from app.alert_manager import alert_manager

class SimulationEngine:
    """Engine for running misuse simulations"""
    
    def __init__(self):
        self.generator = SyntheticDataGenerator(seed=None)  # Random seed for variety
        self.active_simulations = {}
    
    async def run_simulation(self, scenario: str, intensity: float = 1.0,
                             duration_minutes: int = 5,
                             target_region: str = None) -> Dict:
        """Run a misuse simulation scenario"""
        
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        
        self.active_simulations[simulation_id] = {
            "status": "RUNNING",
            "scenario": scenario,
            "start_time": start_time
        }
        
        # Determine number of events based on intensity
        base_events = int(20 * intensity)
        
        events = []
        
        if scenario == "DEVICE_SPIKE":
            events = self._generate_device_spike(base_events, target_region)
        elif scenario == "REGIONAL_ANOMALY":
            events = self._generate_regional_anomaly(base_events, target_region)
        elif scenario == "OTP_ABUSE":
            events = self._generate_otp_abuse(base_events, target_region)
        elif scenario == "OFF_HOURS_SPIKE":
            events = self._generate_off_hours_spike(base_events, target_region)
        elif scenario == "SERVICE_PROVIDER_ANOMALY":
            events = self._generate_sp_anomaly(base_events, target_region)
        
        # Save events to database
        saved = self.generator.save_to_database(events)
        
        # Analyze and potentially generate alerts
        await self._analyze_simulation_events(events, scenario)
        
        self.active_simulations[simulation_id]["status"] = "COMPLETED"
        self.active_simulations[simulation_id]["events_generated"] = saved
        
        return {
            "simulation_id": simulation_id,
            "scenario": scenario,
            "status": "COMPLETED",
            "events_generated": saved,
            "start_time": start_time
        }
    
    def _generate_device_spike(self, count: int, region: str = None) -> List[Dict]:
        """Generate device spike scenario - many auths from single device"""
        events = []
        
        # Use a single device for all events
        target_device = self.generator.device_pool[0]
        target_region = region or random.choice(list(STATES.keys()))
        
        base_time = datetime.now()
        
        for i in range(count):
            event = self.generator.generate_normal_event(
                timestamp=base_time + timedelta(seconds=random.randint(0, 300))
            )
            event["device_fingerprint_hash"] = target_device
            event["state_code"] = target_region
            event["retry_count"] = random.randint(2, 6)
            events.append(event)
        
        return events
    
    def _generate_regional_anomaly(self, count: int, region: str = None) -> List[Dict]:
        """Generate regional anomaly - unusual patterns in a region"""
        events = []
        
        target_region = region or random.choice(list(STATES.keys()))
        districts = STATES[target_region]["districts"]
        
        base_time = datetime.now()
        
        for i in range(count):
            event = self.generator.generate_normal_event(
                timestamp=base_time + timedelta(seconds=random.randint(0, 600))
            )
            event["state_code"] = target_region
            event["district_code"] = random.choice(districts)
            event["retry_count"] = random.randint(2, 5)
            event["hour_of_day"] = random.choice([2, 3, 4, 23])  # Off hours
            event["is_fallback"] = random.random() < 0.4  # High fallback rate
            events.append(event)
        
        return events
    
    def _generate_otp_abuse(self, count: int, region: str = None) -> List[Dict]:
        """Generate OTP abuse scenario - excessive OTP fallbacks"""
        events = []
        
        # Use a small pool of devices
        target_devices = self.generator.device_pool[:5]
        base_time = datetime.now()
        
        for i in range(count):
            event = self.generator.generate_normal_event(
                timestamp=base_time + timedelta(seconds=random.randint(0, 600))
            )
            event["device_fingerprint_hash"] = random.choice(target_devices)
            event["auth_type"] = "OTP"
            event["is_fallback"] = True
            event["retry_count"] = random.randint(2, 8)
            event["status"] = random.choice(["SUCCESS", "FAILURE", "FAILURE"])
            if event["status"] == "FAILURE":
                event["failure_reason"] = random.choice(["OTP_EXPIRED", "OTP_INVALID"])
            events.append(event)
        
        return events
    
    def _generate_off_hours_spike(self, count: int, region: str = None) -> List[Dict]:
        """Generate off-hours spike - authentications during unusual hours"""
        events = []
        
        target_region = region or random.choice(list(STATES.keys()))
        
        # Set time to off-hours
        base_time = datetime.now().replace(hour=random.choice([2, 3, 4]))
        
        for i in range(count):
            event = self.generator.generate_normal_event(
                timestamp=base_time + timedelta(minutes=random.randint(0, 120))
            )
            event["state_code"] = target_region
            event["hour_of_day"] = random.choice([1, 2, 3, 4, 5])
            events.append(event)
        
        return events
    
    def _generate_sp_anomaly(self, count: int, region: str = None) -> List[Dict]:
        """Generate service provider anomaly"""
        events = []
        
        # Use single service provider
        target_sp = "SP_ANOMALY_TEST_abc123"
        base_time = datetime.now()
        
        for i in range(count):
            event = self.generator.generate_normal_event(
                timestamp=base_time + timedelta(seconds=random.randint(0, 600))
            )
            event["service_provider_id"] = target_sp
            event["retry_count"] = random.randint(3, 10)
            event["session_duration_ms"] = random.randint(10000, 50000)  # Very long sessions
            events.append(event)
        
        return events
    
    async def _analyze_simulation_events(self, events: List[Dict], scenario: str):
        """Analyze simulated events and generate alerts if warranted"""
        if not events:
            return
        
        # Group by entity type based on scenario
        if scenario in ["DEVICE_SPIKE", "OTP_ABUSE"]:
            # Analyze by device
            devices = set(e["device_fingerprint_hash"] for e in events)
            for device in devices:
                assessment = risk_engine.analyze_entity("DEVICE", device, time_window_hours=1)
                if assessment["composite_score"] >= 50:
                    alert_manager.generate_alert(assessment, "DEVICE", device)
        
        elif scenario in ["REGIONAL_ANOMALY", "OFF_HOURS_SPIKE"]:
            # Analyze by region
            regions = set(e["state_code"] for e in events)
            for region in regions:
                assessment = risk_engine.analyze_entity("REGION", region, time_window_hours=1)
                if assessment["composite_score"] >= 50:
                    alert_manager.generate_alert(assessment, "REGION", region)
        
        elif scenario == "SERVICE_PROVIDER_ANOMALY":
            # Analyze by service provider
            sps = set(e["service_provider_id"] for e in events)
            for sp in sps:
                assessment = risk_engine.analyze_entity("SERVICE_PROVIDER", sp, time_window_hours=1)
                if assessment["composite_score"] >= 50:
                    alert_manager.generate_alert(assessment, "SERVICE_PROVIDER", sp)
    
    def get_active_simulations(self) -> Dict:
        """Get list of active simulations"""
        return self.active_simulations


# Singleton instance
simulation_engine = SimulationEngine()
