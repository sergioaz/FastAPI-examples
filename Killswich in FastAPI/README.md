# FastAPI Killswitch Implementation

A production-ready demonstration of **operational killswitches** for critical system functions using FastAPI and Redis.

## 🎯 What are Killswitches?

Killswitches are **real-time feature flags** that allow you to instantly disable critical system functions during emergencies or maintenance without code deployments.

### Key Differences:
- **Killswitches** (Critical): Payment processing, order creation, database writes
- **Feature Toggles** (Secondary): New UI themes, A/B tests, experimental features

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   FastAPI App   │◄──►│  Redis Store    │◄──►│  Admin Control  │
│                 │    │                 │    │                 │
│ • Order API     │    │ • Killswitches  │    │ • Emergency     │
│ • Payment API   │    │ • Error Stats   │    │ • Bulk Actions  │
│ • Health Check  │    │ • Auto-disable  │    │ • Monitoring    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 File Structure

```
Killswich in FastAPI/
├── README.md              # This documentation
├── killswitch.py          # Core killswitch manager 
├── killswitch.http        # HTTP test requests
├── main.py                #  main entry point
└── service.py             # Buliness logic with killswitch checks
```

## 🔧 Core Components

### 1. KillswitchManager Class
```python
class KillswitchManager:
    def is_feature_enabled(feature: str) -> bool    # Check if feature is enabled
    def set_feature_state(feature: str, enabled: bool)  # Enable/disable feature
    def get_all_states() -> Dict                    # Get all killswitch states
    def auto_disable_on_errors(feature: str)       # Auto-disable on error threshold
```

### 2. Protected Business Logic
```python
class EcommerceAPI:
    async def create_order(order_data):
        if not killswitch.is_feature_enabled("order_creation"):
            return {"error": "Order creation temporarily disabled"}
        # ... business logic
```

### 3. Admin Endpoints
- `GET /admin/killswitches` - View all states
- `POST /admin/killswitch/{feature}` - Toggle specific feature
- `POST /admin/emergency-disable` - Emergency bulk disable
- `POST /admin/bulk-enable` - Bulk enable features

## 🚀 How to Start

### Prerequisites

1. **Python Environment**
   ```bash
   cd /mnt/c/Learn/FastAPI-Projects
   source .venv/bin/activate  # Use existing virtual environment
   ```

2. **Redis Server** (Required for killswitch persistence)
   ```bash
   # Install Redis (Ubuntu/Debian)
   sudo apt update && sudo apt install redis-server
   
   # Start Redis
   sudo systemctl start redis-server
   sudo systemctl enable redis-server
   
   # Test Redis connection
   redis-cli ping  # Should return "PONG"
   ```

3. **Install Dependencies**
   ```bash
   uv pip install fastapi uvicorn redis pydantic
   ```

### Start the Application

```bash
cd "Killswich in FastAPI"

# Method 1: Direct uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Python module
python -m uvicorn main:app --reload --port 8000

# Method 3: Run directly
python main.py
```

### Verify Startup
```bash
# Check application health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "redis_available": true,
  "critical_features_disabled": [],
  "total_features": 9
}
```

## 🧪 Testing Guide

### Method 1: HTTP File (Recommended)

Using PyCharm or VS Code with REST Client extension or similar:

1. **Open `killswitch.http`** in VS Code
2. **Install REST Client** extension if not installed
3. **Click "Send Request"** above each HTTP request

### Method 2: cURL Commands

```bash
# Check system health
curl http://localhost:8000/api/health

# View all killswitches
curl http://localhost:8000/admin/killswitches

# Create a test order (should work initially)
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "items": [{"product_id": "laptop", "quantity": 1, "price": 999.99}],
    "payment_method": "credit_card",
    "total_amount": 999.99
  }'

# Disable order creation (KILLSWITCH TEST)
curl -X POST http://localhost:8000/admin/killswitch/order_creation \
  -H "Content-Type: application/json" \
  -d '{
    "feature": "order_creation",
    "enabled": false,
    "reason": "Testing killswitch functionality",
    "updated_by": "test_admin"
  }'

# Try creating order again (should fail with clear message)
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "items": [{"product_id": "laptop", "quantity": 1, "price": 999.99}],
    "payment_method": "credit_card",
    "total_amount": 999.99
  }'

# Re-enable order creation
curl -X POST http://localhost:8000/admin/killswitch/order_creation \
  -H "Content-Type: application/json" \
  -d '{
    "feature": "order_creation",
    "enabled": true,
    "reason": "Test completed - re-enabling orders",
    "updated_by": "test_admin"
  }'
```

### Method 3: Python Test Script

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_killswitch_functionality():
    # 1. Check initial health
    health = requests.get(f"{BASE_URL}/api/health").json()
    print(f"Initial health: {health['status']}")
    
    # 2. Create order (should work)
    order_data = {
        "user_id": "test_user",
        "items": [{"product_id": "test", "quantity": 1, "price": 100.0}],
        "payment_method": "test_card",
        "total_amount": 100.0
    }
    
    response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
    print(f"Order creation: {response.status_code} - {response.json()}")
    
    # 3. Disable order creation
    disable_data = {
        "feature": "order_creation",
        "enabled": False,
        "reason": "Python test script",
        "updated_by": "test_script"
    }
    
    response = requests.post(f"{BASE_URL}/admin/killswitch/order_creation", json=disable_data)
    print(f"Disable killswitch: {response.status_code}")
    
    # 4. Try order again (should fail)
    response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
    print(f"Order after disable: {response.status_code} - {response.json()}")
    
    # 5. Re-enable
    enable_data = {**disable_data, "enabled": True, "reason": "Test completed"}
    response = requests.post(f"{BASE_URL}/admin/killswitch/order_creation", json=enable_data)
    print(f"Re-enable: {response.status_code}")

if __name__ == "__main__":
    test_killswitch_functionality()
```

## 📊 Available Killswitches

| Killswitch | Purpose | Effect When Disabled |
|------------|---------|---------------------|
| `order_creation` | Critical business function | Orders return 503 error |
| `payment_processing` | Payment gateway calls | Orders created as "pending payment" |
| `inventory_service` | Inventory checks | Uses `require_inventory_check` setting |
| `require_inventory_check` | Inventory validation | Orders proceed without inventory check |
| `email_notifications` | Email sending | Notifications skipped or queued |
| `sms_notifications` | SMS sending | SMS notifications skipped |
| `database_writes` | Database operations | Writes queued or skipped |
| `expensive_queries` | Complex DB queries | Queries disabled or simplified |
| `third_party_apis` | External API calls | APIs bypassed or cached responses used |

## 🆘 Emergency Scenarios

### Scenario 1: Payment Gateway Down
```bash
# Emergency disable payments
curl -X POST http://localhost:8000/admin/emergency-disable \
  -H "Content-Type: application/json" \
  -d '{
    "features": ["payment_processing"],
    "reason": "Payment gateway experiencing outages",
    "duration_minutes": 30
  }'

# Result: Orders still work but are created as "pending payment"
```

### Scenario 2: Database Overload
```bash
# Disable expensive operations
curl -X POST http://localhost:8000/admin/emergency-disable \
  -H "Content-Type: application/json" \
  -d '{
    "features": ["expensive_queries", "database_writes"],
    "reason": "Database CPU at 100%"
  }'
```

### Scenario 3: Security Incident
```bash
# Disable all external integrations
curl -X POST http://localhost:8000/admin/emergency-disable \
  -H "Content-Type: application/json" \
  -d '{
    "features": ["third_party_apis", "email_notifications", "sms_notifications"],
    "reason": "Security incident - isolating external communications"
  }'
```

## 🔄 Auto-Disable Feature

The system automatically disables features when error rates exceed thresholds:

```python
# Automatic disable when 10 errors in 5 minutes
await killswitch.auto_disable_on_errors("payment_processing", error_message)
```

### Test Auto-Disable
```bash
# Simulate errors to trigger auto-disable
curl -X POST "http://localhost:8000/test/simulate-error/payment_processing?count=5"

# Check if feature was auto-disabled
curl http://localhost:8000/admin/killswitch/payment_processing

# Check error statistics
curl http://localhost:8000/admin/error-stats
```

## 📈 Monitoring & Observability

### Health Checks
```bash
# System health
curl http://localhost:8000/api/health

# Killswitch states
curl http://localhost:8000/admin/killswitches

# Error statistics
curl http://localhost:8000/admin/error-stats
```

### Redis Monitoring
```bash
# Check Redis killswitch keys
redis-cli KEYS "killswitch:*"

# View specific killswitch
redis-cli GET "killswitch:order_creation"

# View error counters
redis-cli KEYS "errors:*"
```

### Logs to Watch
```bash
# Application logs show killswitch changes
tail -f /var/log/fastapi-killswitch.log

# Look for these log patterns:
# ✅ KILLSWITCH ENABLED: feature by user - reason
# ❌ KILLSWITCH DISABLED: feature by user - reason
# 🚨 Auto-disabled: feature due to high error rate
```

## 🔧 Configuration

### Environment Variables
```bash
# Fallback killswitch states (when Redis unavailable)
export KILLSWITCH_ORDER_CREATION=true
export KILLSWITCH_PAYMENT_PROCESSING=true
export KILLSWITCH_INVENTORY_SERVICE=true

# Redis configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

### Redis Configuration
```bash
# /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 🚨 Troubleshooting

### Problem: "Redis connection failed"
**Solution:**
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Start Redis if stopped
sudo systemctl start redis-server

# Test connection
redis-cli ping
```

### Problem: "Killswitch not persisting"
**Solution:**
```bash
# Check Redis permissions
sudo chown redis:redis /var/lib/redis
sudo chmod 750 /var/lib/redis

# Check Redis logs
sudo journalctl -u redis-server
```

### Problem: "Auto-disable not working"
**Solution:**
```bash
# Check error counters in Redis
redis-cli KEYS "errors:*"
redis-cli GET "errors:payment_processing:5min"

# Verify error threshold logic in logs
```

### Problem: "Orders failing unexpectedly"
**Solution:**
```bash
# Check killswitch states
curl http://localhost:8000/admin/killswitches

# Look for auto-disabled features
curl http://localhost:8000/admin/error-stats
```

## 📝 Development Notes

### Adding New Killswitches
1. **Add to default_states** in `KillswitchManager.__init__`
2. **Use in business logic**: `if not killswitch.is_feature_enabled("new_feature"):`
3. **Add to documentation** and test cases

### Best Practices
- **Critical features**: Always have killswitches (payments, orders, auth)
- **Clear error messages**: Tell users what's disabled and why
- **Graceful degradation**: Provide alternatives when possible
- **Audit trail**: Log all killswitch changes
- **Test regularly**: Ensure killswitches work before you need them

## 🎓 Learning Outcomes

After running these tests, you'll understand:

1. **How killswitches provide operational safety** for critical systems
2. **The difference between killswitches and feature toggles**
3. **How to implement graceful degradation** in microservices
4. **Real-time operational control** without code deployments
5. **Auto-disable mechanisms** for proactive system protection
6. **Emergency response procedures** for production incidents

## 🔗 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🎯 Next Steps

1. **Run the basic tests** to understand functionality
2. **Simulate emergency scenarios** to see graceful degradation
3. **Test auto-disable feature** with error simulation
4. **Monitor Redis** to see real-time state changes
5. **Extend with your own business logic** and killswitches

This implementation demonstrates **production-ready killswitches** that can save your system during real emergencies! 🚨
