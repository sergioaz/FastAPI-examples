from typing import List, Dict
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks

from killswitch import killswitch_manager, KillswitchState, KillswitchStatus, OrderRequest, EmergencyDisableRequest
from service import EcommerceAPI


# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Killswitch FastAPI Demo...")
    print(f"📊 Redis available: {killswitch_manager.redis_available}")
    yield
    # Shutdown
    print("🛑 Shutting down Killswitch Demo")


app = FastAPI(
    title="Killswitch Demo API",
    description="Demonstrates operational killswitches for critical system functions",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize business logic
ecommerce_api = EcommerceAPI()


# ==== BUSINESS ENDPOINTS ====

@app.post("/api/orders", summary="Create Order")
async def create_order(order: OrderRequest):
    """Create a new order (protected by killswitches)"""
    return await ecommerce_api.create_order(order)


@app.get("/api/health")
async def health_check():
    """System health check"""
    states = killswitch_manager.get_all_states()
    critical_features = ["order_creation", "payment_processing"]

    critical_disabled = [f for f in critical_features if not states[f].enabled]

    return {
        "status": "degraded" if critical_disabled else "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis_available": killswitch_manager.redis_available,
        "critical_features_disabled": critical_disabled,
        "total_features": len(states)
    }


# ==== KILLSWITCH MANAGEMENT ENDPOINTS ====

@app.get("/admin/killswitches", response_model=Dict[str, KillswitchStatus])
async def get_all_killswitches():
    """Get all killswitch states"""
    return killswitch_manager.get_all_states()


@app.get("/admin/killswitch/{feature}", response_model=KillswitchStatus)
async def get_killswitch_status(feature: str):
    """Get specific killswitch status"""
    states = killswitch_manager.get_all_states()
    if feature not in states:
        raise HTTPException(status_code=404, detail=f"Killswitch '{feature}' not found")
    return states[feature]


@app.post("/admin/killswitch/{feature}")
async def toggle_killswitch(feature: str, request: KillswitchState):
    """Toggle a specific killswitch"""
    if feature not in killswitch_manager.default_states:
        raise HTTPException(status_code=404, detail=f"Unknown feature: {feature}")

    success = killswitch_manager.set_feature_state(
        feature,
        request.enabled,
        request.reason,
        request.updated_by
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update killswitch")

    return {
        "status": "updated",
        "feature": feature,
        "enabled": request.enabled,
        "reason": request.reason,
        "updated_by": request.updated_by,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/admin/emergency-disable")
async def emergency_disable(request: EmergencyDisableRequest):
    """Emergency disable multiple features"""
    results = []

    for feature in request.features:
        if feature in killswitch_manager.default_states:
            success = killswitch_manager.set_feature_state(
                feature,
                False,
                f"EMERGENCY: {request.reason}",
                "emergency-operator"
            )
            results.append({
                "feature": feature,
                "disabled": success,
                "reason": request.reason
            })

            # Set auto-enable timer if duration specified
            if request.duration_minutes and success:
                # In a real system, you'd use a background task or scheduler
                # For demo, we just log it
                print(f"📅 {feature} will auto-enable in {request.duration_minutes} minutes")
        else:
            results.append({
                "feature": feature,
                "disabled": False,
                "error": "Unknown feature"
            })

    return {
        "status": "emergency_disable_executed",
        "timestamp": datetime.now().isoformat(),
        "results": results
    }


@app.post("/admin/bulk-enable")
async def bulk_enable_features(features: List[str], reason: str = "Bulk enable"):
    """Enable multiple features at once"""
    results = []

    for feature in features:
        if feature in killswitch_manager.default_states:
            success = killswitch_manager.set_feature_state(feature, True, reason, "bulk-operator")
            results.append({"feature": feature, "enabled": success})
        else:
            results.append({"feature": feature, "enabled": False, "error": "Unknown feature"})

    return {"status": "bulk_enable_completed", "results": results}


@app.get("/admin/error-stats")
async def get_error_stats():
    """Get error statistics that trigger auto-disable"""
    if not killswitch_manager.redis_available:
        return {"error": "Redis unavailable - no error stats"}

    stats = {}
    try:
        for feature in killswitch_manager.default_states.keys():
            error_key = f"errors:{feature}:5min"
            error_count = killswitch_manager.redis_client.get(error_key) or "0"
            ttl = killswitch_manager.redis_client.ttl(error_key)

            stats[feature] = {
                "errors_last_5min": int(error_count),
                "ttl_seconds": ttl if ttl > 0 else 0
            }
    except Exception as e:
        return {"error": f"Failed to get error stats: {e}"}

    return stats


# ==== TESTING ENDPOINTS ====

@app.post("/test/simulate-error/{feature}")
async def simulate_feature_error(feature: str, count: int = 1):
    """Simulate errors for testing auto-disable (DO NOT USE IN PRODUCTION)"""
    if feature not in killswitch_manager.default_states:
        raise HTTPException(status_code=404, detail="Unknown feature")

    results = []
    for i in range(count):
        auto_disabled = await killswitch_manager.auto_disable_on_errors(
            feature,
            f"Simulated error #{i + 1} for testing",
            threshold=5  # Lower threshold for testing
        )
        results.append({"error_num": i + 1, "auto_disabled": auto_disabled})

    return {
        "feature": feature,
        "simulated_errors": count,
        "results": results
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)