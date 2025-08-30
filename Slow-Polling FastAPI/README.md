# FastAPI Long Polling Demo

A real-time chat application demonstrating HTTP Long Polling with FastAPI. This project shows how to implement push-like behavior using standard HTTP requests instead of WebSockets.

## 🎯 Purpose

Long polling is a technique that makes HTTP requests behave like real-time push notifications:

- **Client makes request** → Server holds it open
- **When data arrives** → Server immediately responds
- **Client gets response** → Immediately makes new request
- **Creates continuous stream** of near real-time updates

### Why Long Polling?

- ✅ **HTTP-compatible**: Works through firewalls, proxies, CDNs
- ✅ **Simpler than WebSockets**: No connection management complexity
- ✅ **Near real-time**: Updates delivered immediately when available
- ✅ **Efficient**: No wasted requests when there's no data

## 🏗️ Architecture

```
┌─────────────────┐    Long Poll Request     ┌─────────────────┐
│                 │ ────────────────────────► │                 │
│     Client      │                          │   FastAPI       │
│   (Browser)     │ ◄──── Response with ──── │   Server        │
│                 │       data (immediate)   │                 │
└─────────────────┘                          └─────────────────┘
        │                                            ▲
        │                                            │
        └──── New Long Poll ────────────────────────┘
             (immediately after response)

Multiple clients can long-poll simultaneously:
Client A ──┐
Client B ──┤──► Server holds all requests open
Client C ──┘    until data arrives, then responds to all
```

## 📋 API Schema

### Core Endpoints

#### `GET /api/poll` - Long Polling Endpoint
**The heart of the system** - holds requests open until data arrives.

**Query Parameters:**
```python
client_id: str      # Unique identifier for the client
room: str = "general"  # Chat room name  
last_message_id: str = None  # Last seen message ID
timeout: int = 25   # How long to wait (5-60 seconds)
```

**Response:**
```json
{
  "messages": [
    {
      "id": "uuid-string",
      "sender": "john_doe", 
      "text": "Hello world!",
      "timestamp": 1693420800.123,
      "room": "general"
    }
  ],
  "status": "success",  // "success", "timeout", "error"
  "timeout": false
}
```

**Behavior:**
- Request **hangs for up to 25 seconds**
- Returns immediately if new messages arrive
- Returns empty array on timeout

#### `POST /api/send` - Send Message
Broadcasts a message to all clients waiting in long-poll requests.

**Request Body:**
```json
{
  "sender": "alice",
  "text": "Hello everyone!",
  "room": "general"
}
```

**Response:**
```json
{
  "status": "sent",
  "message_id": "uuid-string", 
  "timestamp": 1693420800.123
}
```

#### `GET /api/history` - Message History
Get recent messages for late-joining clients.

**Query Parameters:**
```python
room: str = "general"  # Room name
limit: int = 20        # Number of recent messages (1-100)
```

#### `GET /api/stats` - System Stats
Monitor active connections and system health.

**Response:**
```json
{
  "active_clients": 5,
  "total_messages": 147,
  "rooms": ["general", "dev", "random"],
  "timestamp": 1693420800.123
}
```

## 🚀 How to Run

### Prerequisites
```bash
cd /mnt/c/Learn/FastAPI-Projects
source .venv/bin/activate  # Use existing venv
```

### Start the Server
```bash
cd "Slow-Polling FastAPI"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application
- **Web Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing the Long Polling

### Method 1: Manual API Testing

#### Terminal 1: Start Long Poll (simulates waiting client)
```bash
# This request will HANG for 25 seconds waiting for messages
curl -X GET "http://localhost:8000/api/poll?client_id=test_user&room=general&timeout=25"
```

#### Terminal 2: Send Message (triggers the waiting request)
```bash
# This will immediately cause Terminal 1 to receive a response!
curl -X POST "http://localhost:8000/api/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "alice",
    "text": "Hello from terminal!",
    "room": "general"
  }'
```

**Expected Result**: Terminal 1 immediately gets the message response.

### Method 2: Multi-Client Test

#### Terminal 1: Client A waiting
```bash
curl "http://localhost:8000/api/poll?client_id=alice&room=general&timeout=30"
```

#### Terminal 2: Client B waiting  
```bash
curl "http://localhost:8000/api/poll?client_id=bob&room=general&timeout=30"
```

#### Terminal 3: Send broadcast message
```bash
curl -X POST "http://localhost:8000/api/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "charlie",
    "text": "Message to everyone!",
    "room": "general"
  }'
```

**Expected Result**: Both Terminal 1 and Terminal 2 immediately receive the message.

### Method 3: Different Rooms Test
```bash
# Client in room "dev"
curl "http://localhost:8000/api/poll?client_id=developer&room=dev&timeout=30" &

# Client in room "general" 
curl "http://localhost:8000/api/poll?client_id=user&room=general&timeout=30" &

# Send to "dev" room only
curl -X POST "http://localhost:8000/api/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "admin",
    "text": "Dev team meeting in 5 minutes",
    "room": "dev"
  }'
```

**Expected Result**: Only the "dev" room client receives the message.

### Method 4: Timeout Test
```bash
# Start long poll with 10 second timeout
curl "http://localhost:8000/api/poll?client_id=test&timeout=10"

# Don't send any messages - wait 10 seconds
# Expected Result: Returns {"messages": [], "status": "timeout", "timeout": true}
```

### Method 5: Performance Test
```bash
# Test multiple concurrent long polls
for i in {1..5}; do
  curl "http://localhost:8000/api/poll?client_id=user_$i&timeout=30" &
done

# Send message to trigger all
sleep 2
curl -X POST "http://localhost:8000/api/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "broadcaster",
    "text": "Message to all 5 clients!",
    "room": "general"
  }'

# All 5 background requests should complete immediately
```

## 📊 Monitoring

### Check Active Connections
```bash
curl http://localhost:8000/api/stats
```

### Health Check
```bash
curl http://localhost:8000/health
```

### View Recent Messages
```bash
curl "http://localhost:8000/api/history?room=general&limit=10"
```

## 🔧 How It Works Under the Hood

### 1. Client Connection Flow
```python
# Client side pseudo-code
while True:
    response = requests.get('/api/poll?client_id=alice&timeout=25')
    
    if response.messages:
        print("Got new messages:", response.messages)
        process_messages(response.messages)
    
    # Immediately make next request (no artificial delay)
    # This creates continuous long-polling loop
```

### 2. Server Side Magic
```python
# Server holds request open in async function
async def wait_for_message(client_id, timeout=25):
    start_time = time.time()
    
    # Hold the request open!
    while time.time() - start_time < timeout:
        try:
            # Check queue for new messages
            message = await asyncio.wait_for(queue.get(), timeout=1.0)
            return {"messages": [message]}  # Return immediately!
        except asyncio.TimeoutError:
            continue  # Keep waiting
    
    return {"messages": []}  # Timeout reached
```

### 3. Message Broadcasting
```python
# When message is sent:
async def broadcast_message(message):
    # Push to ALL waiting clients' queues
    for client_id, queue in client_queues.items():
        queue.put_nowait(message)  # This immediately wakes up their long-poll!
```

## 🆚 Comparison with Alternatives

| Method | Latency | Server Load | Complexity | Firewall Issues |
|--------|---------|-------------|------------|-----------------|
| **Traditional Polling** | High (5-30s) | Very High | Low | None |
| **Long Polling** | Very Low (<1s) | Low | Medium | None |
| **WebSockets** | Minimal | Low | High | Some |
| **Server-Sent Events** | Very Low | Low | Low | Some |

## 🐛 Common Issues & Solutions

### Issue: "Connection refused"
```bash
# Solution: Make sure server is running
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: Long poll times out immediately
```bash
# Check if client_id is unique and room exists
curl "http://localhost:8000/api/stats"  # Check active clients
```

### Issue: Messages not received
```bash
# Verify room names match exactly
curl -X POST "http://localhost:8000/api/send" \
  -d '{"sender": "test", "text": "test", "room": "general"}'
```

### Issue: Too many connections
```bash
# Monitor active connections
curl "http://localhost:8000/api/stats"

# Manually disconnect clients if needed
curl -X DELETE "http://localhost:8000/api/client/problematic_client_id"
```

## 📈 Production Considerations

- **Connection Limits**: Monitor concurrent long-poll connections
- **Timeout Tuning**: Balance between responsiveness and server load
- **Client Cleanup**: Remove inactive clients to prevent memory leaks  
- **Room Management**: Implement proper room authentication
- **Message Persistence**: Add database storage for message history
- **Load Balancing**: Use sticky sessions or shared message queues

## 🎓 Learning Outcomes

After testing this application, you'll understand:

1. **How long polling creates push-like behavior** with HTTP
2. **The difference between polling and long polling** efficiency
3. **When to choose long polling vs WebSockets** 
4. **How to implement real-time features** without complex protocols
5. **Server resource management** for concurrent connections

This demonstrates a powerful technique for real-time web applications using standard HTTP!
