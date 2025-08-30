"""
FastAPI Killswitch Implementation
Demonstrates operational killswitches for critical system functions
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import redis

# Pydantic Models
class KillswitchState(BaseModel):
    feature: str
    enabled: bool
    reason: str = ""
    updated_by: str = "system"

class KillswitchStatus(BaseModel):
    feature: str
    enabled: bool
    last_updated: Optional[datetime] = None
    reason: str = ""
    auto_disabled: bool = False

class OrderRequest(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    payment_method: str
    total_amount: float

class EmergencyDisableRequest(BaseModel):
    features: List[str]
    reason: str
    duration_minutes: Optional[int] = None

# Killswitch Manager
class KillswitchManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            print("✅ Redis connected for killswitches")
        except Exception as e:
            print(f"⚠️ Redis unavailable, using environment fallback: {e}")
            self.redis_client = None
            self.redis_available = False
        
        # Default killswitch states
        self.default_states = {
            "order_creation": True,
            "payment_processing": True,
            "inventory_service": True,
            "require_inventory_check": True,
            "email_notifications": True,
            "sms_notifications": True,
            "database_writes": True,
            "expensive_queries": True,
            "third_party_apis": True
        }
        
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize default killswitch states if they don't exist"""
        if not self.redis_available:
            return
            
        for feature, default_state in self.default_states.items():
            key = f"killswitch:{feature}"
            if not self.redis_client.exists(key):
                self.redis_client.set(key, "true" if default_state else "false")
                self.redis_client.set(f"{key}:updated", time.time())
                self.redis_client.set(f"{key}:reason", "Default initialization")
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled via killswitch"""
        if self.redis_available:
            try:
                value = self.redis_client.get(f"killswitch:{feature}")
                if value is not None:
                    return value.lower() == "true"
            except Exception as e:
                print(f"Redis error for feature {feature}: {e}")
        
        # Fallback to environment variable
        env_value = os.getenv(f"KILLSWITCH_{feature.upper()}", 
                             "true" if self.default_states.get(feature, False) else "false")
        return env_value.lower() == "true"
    
    def set_feature_state(self, feature: str, enabled: bool, reason: str = "", updated_by: str = "system"):
        """Set killswitch state for a feature"""
        if not self.redis_available:
            print(f"Cannot set {feature}: Redis unavailable")
            return False
        
        try:
            key = f"killswitch:{feature}"
            self.redis_client.set(key, "true" if enabled else "false")
            self.redis_client.set(f"{key}:updated", time.time())
            self.redis_client.set(f"{key}:reason", reason)
            self.redis_client.set(f"{key}:updated_by", updated_by)
            
            # Log the change
            action = "ENABLED" if enabled else "DISABLED"
            print(f"🔧 KILLSWITCH {action}: {feature} by {updated_by} - {reason}")
            return True
        except Exception as e:
            print(f"Failed to set killswitch {feature}: {e}")
            return False
    
    def get_all_states(self) -> Dict[str, KillswitchStatus]:
        """Get all killswitch states"""
        states = {}
        
        if self.redis_available:
            try:
                for feature in self.default_states.keys():
                    key = f"killswitch:{feature}"
                    enabled = self.redis_client.get(key) == "true"
                    updated_time = self.redis_client.get(f"{key}:updated")
                    reason = self.redis_client.get(f"{key}:reason") or ""
                    
                    last_updated = None
                    if updated_time:
                        try:
                            last_updated = datetime.fromtimestamp(float(updated_time))
                        except (ValueError, TypeError):
                            pass
                    
                    states[feature] = KillswitchStatus(
                        feature=feature,
                        enabled=enabled,
                        last_updated=last_updated,
                        reason=reason
                    )
            except Exception as e:
                print(f"Error getting killswitch states: {e}")
        
        # Fill in any missing features with defaults
        for feature, default_state in self.default_states.items():
            if feature not in states:
                states[feature] = KillswitchStatus(
                    feature=feature,
                    enabled=default_state,
                    reason="Default state (Redis unavailable)"
                )
        
        return states
    
    async def auto_disable_on_errors(self, feature: str, error_msg: str, threshold: int = 10):
        """Auto-disable feature if error count exceeds threshold"""
        if not self.redis_available:
            return
        
        error_key = f"errors:{feature}:5min"
        try:
            current_errors = self.redis_client.incr(error_key)
            self.redis_client.expire(error_key, 300)  # 5 minute window
            
            if current_errors >= threshold:
                self.set_feature_state(
                    feature, 
                    False, 
                    f"Auto-disabled: {current_errors} errors in 5min. Last error: {error_msg}",
                    "auto-system"
                )
                return True
        except Exception as e:
            print(f"Error in auto-disable for {feature}: {e}")
        
        return False

# Global killswitch manager instance
killswitch_manager = KillswitchManager()

