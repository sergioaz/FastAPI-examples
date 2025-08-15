"""
FastAPI Feature Flag Demo Application

This demo showcases different types of feature flags and their use cases:
1. Simple on/off toggles
2. Percentage-based rollouts
3. User-specific flags
4. A/B testing flags
5. Emergency disable functionality
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import json
import json
import json
import hashlib
import time
import logging
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # 🚀 Startup events
    logger.info("🚀 FastAPI Feature Flag Demo starting up...")
    
    # Initialize application state
    app.state.startup_time = time.time()
    app.state.total_requests = 0
    app.state.feature_flag_checks = 0
    
    # Create demo feature flags
    await create_demo_flags()
    
    logger.info("✅ Application startup complete!")
    
    yield  # Application runs here
    
    # 🛑 Shutdown events
    logger.info("🛑 FastAPI Feature Flag Demo shutting down...")
    
    # Log final statistics
    uptime = time.time() - app.state.startup_time
    logger.info(f"📊 Application statistics:")
    logger.info(f"   ⏱️  Total uptime: {uptime:.2f} seconds")
    logger.info(f"   🌐 Total requests: {getattr(app.state, 'total_requests', 0)}")
    logger.info(f"   🎯 Feature flag checks: {getattr(app.state, 'feature_flag_checks', 0)}")
    
    # Save feature flag statistics to file (in production, save to database)
    stats_summary = {
        "uptime_seconds": uptime,
        "total_requests": getattr(app.state, 'total_requests', 0),
        "feature_flag_checks": getattr(app.state, 'feature_flag_checks', 0),
        "shutdown_time": datetime.utcnow().isoformat(),
        "feature_flags": feature_service.get_stats()
    }
    
    try:
        with open("feature_flag_stats.json", "w") as f:
            json.dump(stats_summary, f, indent=2)
        logger.info("📁 Statistics saved to feature_flag_stats.json")
    except Exception as e:
        logger.error(f"❌ Failed to save statistics: {e}")
    
    logger.info("✅ Application shutdown complete!")


app = FastAPI(title="Feature Flag Demo", version="1.0.0", lifespan=lifespan)

# In-memory storage for demo (use Redis/database in production)
feature_flags_storage: Dict[str, Dict] = {}
feature_flag_usage_stats: Dict[str, Dict] = {}


class FlagType(str, Enum):
    SIMPLE = "simple"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    AB_TEST = "ab_test"


class FeatureFlagConfig(BaseModel):
    name: str
    enabled: bool = True
    flag_type: FlagType = FlagType.SIMPLE
    percentage: Optional[int] = None  # 0-100 for percentage rollouts
    allowed_users: Optional[List[str]] = None
    blocked_users: Optional[List[str]] = None
    experiment_groups: Optional[Dict[str, int]] = None  # For A/B testing
    description: Optional[str] = None
    created_at: Optional[str] = None
    emergency_disabled: bool = False


class FeatureFlagService:
    def __init__(self):
        self.storage = feature_flags_storage
        self.stats = feature_flag_usage_stats
    
    def create_flag(self, config: FeatureFlagConfig) -> bool:
        """Create or update a feature flag"""
        flag_data = config.dict()
        flag_data["created_at"] = datetime.utcnow().isoformat()
        
        self.storage[config.name] = flag_data
        
        # Initialize stats
        if config.name not in self.stats:
            self.stats[config.name] = {
                "total_checks": 0,
                "enabled_count": 0,
                "disabled_count": 0,
                "last_checked": None
            }
        
        logger.info(f"Feature flag '{config.name}' created/updated")
        return True
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None, context: Optional[Dict] = None) -> bool:
        """Check if a feature flag is enabled for a given user/context"""
        # Update stats
        self._update_stats(flag_name)
        
        # Get flag configuration
        flag_config = self.storage.get(flag_name)
        if not flag_config:
            logger.warning(f"Feature flag '{flag_name}' not found, defaulting to False")
            return False
        
        # Check if emergency disabled
        if flag_config.get("emergency_disabled", False):
            self._update_stats(flag_name, enabled=False)
            return False
        
        # Check if flag is disabled globally
        if not flag_config.get("enabled", False):
            self._update_stats(flag_name, enabled=False)
            return False
        
        flag_type = flag_config.get("flag_type", FlagType.SIMPLE)
        result = self._evaluate_flag(flag_config, flag_type, user_id, context)
        
        self._update_stats(flag_name, enabled=result)
        return result
    
    def _evaluate_flag(self, flag_config: Dict, flag_type: str, user_id: Optional[str], context: Optional[Dict]) -> bool:
        """Evaluate flag based on its type"""
        
        if flag_type == FlagType.SIMPLE:
            return True  # Already checked enabled status above
        
        elif flag_type == FlagType.USER_LIST:
            if not user_id:
                return False
            
            # Check blocked users first
            blocked_users = flag_config.get("blocked_users", [])
            if user_id in blocked_users:
                return False
            
            # Check allowed users
            allowed_users = flag_config.get("allowed_users", [])
            if allowed_users:
                return user_id in allowed_users
            return True
        
        elif flag_type == FlagType.PERCENTAGE:
            if not user_id:
                return False
            
            percentage = flag_config.get("percentage", 0)
            if percentage <= 0:
                return False
            if percentage >= 100:
                return True
            
            # Use consistent hashing based on user_id and flag name
            hash_input = f"{flag_config['name']}:{user_id}"
            user_hash = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100
            return user_hash < percentage
        
        elif flag_type == FlagType.AB_TEST:
            if not user_id:
                return False
            
            experiment_groups = flag_config.get("experiment_groups", {})
            if not experiment_groups:
                return False
            
            # Assign user to experiment group based on hash
            hash_input = f"{flag_config['name']}:experiment:{user_id}"
            user_hash = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100
            
            cumulative_percentage = 0
            for group, percentage in experiment_groups.items():
                if user_hash < cumulative_percentage + percentage:
                    # Store the assigned group in context if provided
                    if context is not None:
                        context["experiment_group"] = group
                    # Return True for treatment groups (not control)
                    return group != "control"
                cumulative_percentage += percentage
            
            return False
        
        return False
    
    def _update_stats(self, flag_name: str, enabled: Optional[bool] = None):
        """Update usage statistics for a feature flag"""
        if flag_name not in self.stats:
            self.stats[flag_name] = {
                "total_checks": 0,
                "enabled_count": 0,
                "disabled_count": 0,
                "last_checked": None
            }
        
        stats = self.stats[flag_name]
        stats["total_checks"] += 1
        stats["last_checked"] = datetime.utcnow().isoformat()
        
        if enabled is not None:
            if enabled:
                stats["enabled_count"] += 1
            else:
                stats["disabled_count"] += 1
    
    def get_flag(self, flag_name: str) -> Optional[Dict]:
        """Get feature flag configuration"""
        return self.storage.get(flag_name)
    
    def list_flags(self) -> Dict[str, Dict]:
        """List all feature flags"""
        return self.storage
    
    def delete_flag(self, flag_name: str) -> bool:
        """Delete a feature flag"""
        if flag_name in self.storage:
            del self.storage[flag_name]
            logger.info(f"Feature flag '{flag_name}' deleted")
            return True
        return False
    
    def emergency_disable(self, flag_name: str) -> bool:
        """Emergency disable a feature flag"""
        if flag_name in self.storage:
            self.storage[flag_name]["emergency_disabled"] = True
            self.storage[flag_name]["emergency_disabled_at"] = datetime.utcnow().isoformat()
            logger.warning(f"Feature flag '{flag_name}' emergency disabled!")
            return True
        return False
    
    def get_stats(self, flag_name: Optional[str] = None) -> Dict:
        """Get usage statistics"""
        if flag_name:
            return self.stats.get(flag_name, {})
        return self.stats


# Initialize feature flag service
feature_service = FeatureFlagService()


# Middleware to add feature flag context to requests
class FeatureFlagMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, feature_service):
        super().__init__(app)
        self.feature_service = feature_service
    
    async def dispatch(self, request, call_next):
        # Add feature flag service and user context to request state
        request.state.feature_flags = self.feature_service
        request.state.user_id = request.headers.get("X-User-ID")
        request.state.flag_context = {}
        
        response = await call_next(request)
        
        # Add experiment group info to response headers if available
        if hasattr(request.state, 'flag_context') and request.state.flag_context:
            for key, value in request.state.flag_context.items():
                response.headers[f"X-Experiment-{key.replace('_', '-').title()}"] = str(value)
        
        return response


app.add_middleware(FeatureFlagMiddleware, feature_service=feature_service)


# Helper function to get feature flag service from request
def get_feature_service(request: Request) -> FeatureFlagService:
    return request.state.feature_flags


def get_user_id(request: Request) -> Optional[str]:
    return request.state.user_id


# =============================================================================
# FEATURE FLAG MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/admin/feature-flags")
async def create_feature_flag(config: FeatureFlagConfig, feature_service: FeatureFlagService = Depends(get_feature_service)):
    """Create or update a feature flag"""
    try:
        success = feature_service.create_flag(config)
        if success:
            return {"message": f"Feature flag '{config.name}' created/updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create feature flag")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/feature-flags")
async def list_feature_flags(feature_service: FeatureFlagService = Depends(get_feature_service)):
    """List all feature flags"""
    return feature_service.list_flags()


@app.get("/admin/feature-flags/{flag_name}")
async def get_feature_flag(flag_name: str, feature_service: FeatureFlagService = Depends(get_feature_service)):
    """Get a specific feature flag"""
    flag = feature_service.get_flag(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag


@app.delete("/admin/feature-flags/{flag_name}")
async def delete_feature_flag(flag_name: str, feature_service: FeatureFlagService = Depends(get_feature_service)):
    """Delete a feature flag"""
    success = feature_service.delete_flag(flag_name)
    if success:
        return {"message": f"Feature flag '{flag_name}' deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Feature flag not found")


@app.post("/admin/feature-flags/{flag_name}/emergency-disable")
async def emergency_disable_flag(flag_name: str, feature_service: FeatureFlagService = Depends(get_feature_service)):
    """Emergency disable a feature flag"""
    success = feature_service.emergency_disable(flag_name)
    if success:
        return {"message": f"Feature flag '{flag_name}' emergency disabled!"}
    else:
        raise HTTPException(status_code=404, detail="Feature flag not found")


@app.get("/admin/feature-flags/{flag_name}/stats")
async def get_flag_stats(flag_name: str, feature_service: FeatureFlagService = Depends(get_feature_service)):
    """Get usage statistics for a feature flag"""
    stats = feature_service.get_stats(flag_name)
    if not stats:
        raise HTTPException(status_code=404, detail="No statistics found for this feature flag")
    return stats


@app.get("/admin/stats")
async def get_all_stats(feature_service: FeatureFlagService = Depends(get_feature_service)):
    """Get usage statistics for all feature flags"""
    return feature_service.get_stats()


# =============================================================================
# DEMO ENDPOINTS - SHOWCASING FEATURE FLAGS IN ACTION
# =============================================================================

@app.get("/")
async def root():
    """API information and available demo endpoints"""
    return {
        "message": "Feature Flag Demo API",
        "version": "1.0.0",
        "demo_endpoints": {
            "simple_flag": "/demo/simple-feature",
            "percentage_rollout": "/demo/percentage-feature",
            "user_specific": "/demo/user-feature",
            "ab_test": "/demo/ab-test-feature",
            "payment_processor": "/demo/payment",
            "recommendation_engine": "/demo/recommendations"
        },
        "admin_endpoints": {
            "create_flag": "POST /admin/feature-flags",
            "list_flags": "GET /admin/feature-flags",
            "emergency_disable": "POST /admin/feature-flags/{name}/emergency-disable"
        }
    }


@app.get("/demo/simple-feature")
async def demo_simple_feature(request: Request, 
                             feature_service: FeatureFlagService = Depends(get_feature_service),
                             user_id: Optional[str] = Depends(get_user_id)):
    """Demo of a simple on/off feature flag"""
    
    if feature_service.is_enabled("simple_demo_feature", user_id):
        return {
            "message": "🎉 New feature is enabled!",
            "feature": "simple_demo_feature",
            "status": "enabled",
            "user_id": user_id
        }
    else:
        return {
            "message": "Standard feature response",
            "feature": "simple_demo_feature", 
            "status": "disabled",
            "user_id": user_id
        }


@app.get("/demo/percentage-feature")
async def demo_percentage_feature(request: Request,
                                 feature_service: FeatureFlagService = Depends(get_feature_service),
                                 user_id: Optional[str] = Depends(get_user_id)):
    """Demo of percentage-based feature rollout"""
    
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required for percentage rollout demo")
    
    if feature_service.is_enabled("percentage_demo_feature", user_id):
        return {
            "message": "🎯 You're in the percentage rollout!",
            "feature": "percentage_demo_feature",
            "status": "enabled",
            "user_id": user_id,
            "note": "This feature is gradually rolling out to users"
        }
    else:
        return {
            "message": "Standard feature - not in rollout yet",
            "feature": "percentage_demo_feature",
            "status": "disabled", 
            "user_id": user_id
        }


@app.get("/demo/user-feature")
async def demo_user_specific_feature(request: Request,
                                   feature_service: FeatureFlagService = Depends(get_feature_service),
                                   user_id: Optional[str] = Depends(get_user_id)):
    """Demo of user-specific feature flags"""
    
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required for user-specific demo")
    
    if feature_service.is_enabled("user_specific_demo_feature", user_id):
        return {
            "message": f"🌟 Special feature unlocked for user {user_id}!",
            "feature": "user_specific_demo_feature",
            "status": "enabled",
            "user_id": user_id,
            "note": "This feature is only available to specific users"
        }
    else:
        return {
            "message": "Standard user experience",
            "feature": "user_specific_demo_feature",
            "status": "disabled",
            "user_id": user_id
        }


@app.get("/demo/ab-test-feature")
async def demo_ab_test_feature(request: Request,
                              feature_service: FeatureFlagService = Depends(get_feature_service),
                              user_id: Optional[str] = Depends(get_user_id)):
    """Demo of A/B testing with feature flags"""
    
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required for A/B test demo")
    
    context = {}
    is_treatment = feature_service.is_enabled("ab_test_demo_feature", user_id, context)
    
    # Store experiment group in request state for middleware
    if context.get("experiment_group"):
        request.state.flag_context["experiment_group"] = context["experiment_group"]
    
    if is_treatment:
        return {
            "message": "🧪 Treatment group - new algorithm active!",
            "feature": "ab_test_demo_feature",
            "status": "enabled",
            "experiment_group": context.get("experiment_group", "unknown"),
            "user_id": user_id,
            "algorithm": "new_recommendation_v2"
        }
    else:
        return {
            "message": "Control group - standard algorithm",
            "feature": "ab_test_demo_feature",
            "status": "disabled",
            "experiment_group": context.get("experiment_group", "control"),
            "user_id": user_id,
            "algorithm": "legacy_recommendation"
        }


@app.post("/demo/payment")
async def demo_payment_processor(request: Request,
                               payment_data: Dict[str, Any],
                               feature_service: FeatureFlagService = Depends(get_feature_service),
                               user_id: Optional[str] = Depends(get_user_id)):
    """Demo of feature flags for risky payment processor changes"""
    
    if feature_service.is_enabled("new_payment_processor", user_id):
        # Simulate new payment processor with potential issues
        return {
            "message": "Payment processed with NEW payment system",
            "processor": "stripe_v2",
            "transaction_id": f"txn_new_{int(time.time())}",
            "status": "success",
            "features": ["fraud_detection_ml", "instant_settlement", "multi_currency"],
            "user_id": user_id
        }
    else:
        # Safe legacy payment processor
        return {
            "message": "Payment processed with legacy payment system",
            "processor": "legacy_processor",
            "transaction_id": f"txn_legacy_{int(time.time())}",
            "status": "success",
            "features": ["basic_fraud_check"],
            "user_id": user_id
        }


@app.get("/demo/recommendations")
async def demo_recommendation_engine(request: Request,
                                   feature_service: FeatureFlagService = Depends(get_feature_service),
                                   user_id: Optional[str] = Depends(get_user_id)):
    """Demo of ML recommendations with feature flag fallback"""
    
    try:
        if feature_service.is_enabled("ml_recommendations", user_id):
            # Simulate ML recommendation system (potentially risky)
            recommendations = [
                {"id": 1, "title": "AI-Powered Product A", "score": 0.95, "type": "ml_generated"},
                {"id": 2, "title": "Smart Recommendation B", "score": 0.89, "type": "ml_generated"},
                {"id": 3, "title": "Personalized Item C", "score": 0.84, "type": "ml_generated"}
            ]
            
            return {
                "message": "Recommendations from ML engine",
                "engine": "neural_collaborative_filtering",
                "recommendations": recommendations,
                "user_id": user_id,
                "features": ["deep_learning", "real_time_personalization"]
            }
        else:
            # Safe rule-based recommendations
            recommendations = [
                {"id": 101, "title": "Popular Product X", "score": 0.8, "type": "rule_based"},
                {"id": 102, "title": "Trending Item Y", "score": 0.75, "type": "rule_based"},
                {"id": 103, "title": "Category Bestseller Z", "score": 0.7, "type": "rule_based"}
            ]
            
            return {
                "message": "Recommendations from rule-based engine",
                "engine": "rule_based_collaborative",
                "recommendations": recommendations,
                "user_id": user_id,
                "features": ["popularity_based", "category_filtering"]
            }
            
    except Exception as e:
        # Fallback to safe recommendations if ML system fails
        logger.error(f"Recommendation system error: {e}")
        return {
            "message": "Fallback recommendations due to system error",
            "engine": "fallback_static",
            "recommendations": [
                {"id": 999, "title": "Safe Fallback Product", "score": 0.5, "type": "fallback"}
            ],
            "user_id": user_id,
            "error": "ML system temporarily unavailable"
        }


# =============================================================================
# INITIALIZATION - CREATE DEMO FEATURE FLAGS
# =============================================================================

@app.on_event("startup")
async def create_demo_flags():
    """Initialize demo feature flags on startup"""
    
    demo_flags = [
        FeatureFlagConfig(
            name="simple_demo_feature",
            enabled=True,
            flag_type=FlagType.SIMPLE,
            description="Simple on/off toggle demo"
        ),
        FeatureFlagConfig(
            name="percentage_demo_feature", 
            enabled=True,
            flag_type=FlagType.PERCENTAGE,
            percentage=25,  # 25% of users
            description="Percentage rollout demo - 25% of users"
        ),
        FeatureFlagConfig(
            name="user_specific_demo_feature",
            enabled=True,
            flag_type=FlagType.USER_LIST,
            allowed_users=["admin", "beta_user", "test_user_123"],
            description="User-specific feature demo"
        ),
        FeatureFlagConfig(
            name="ab_test_demo_feature",
            enabled=True,
            flag_type=FlagType.AB_TEST,
            experiment_groups={"control": 50, "treatment_a": 30, "treatment_b": 20},
            description="A/B test demo with control and treatment groups"
        ),
        FeatureFlagConfig(
            name="new_payment_processor",
            enabled=True,
            flag_type=FlagType.PERCENTAGE,
            percentage=10,  # Start with 10% for risky payment changes
            description="New payment processor rollout - start small!"
        ),
        FeatureFlagConfig(
            name="ml_recommendations",
            enabled=True,
            flag_type=FlagType.PERCENTAGE,
            percentage=50,  # 50% get ML recommendations
            description="ML recommendation engine vs rule-based"
        )
    ]
    
    for flag in demo_flags:
        feature_service.create_flag(flag)
    
    logger.info("Demo feature flags initialized!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("feature_flag_demo:app", host="0.0.0.0", port=8000, reload=True)
