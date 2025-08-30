"""
FastAPI Long Polling Demo - Chat System
Demonstrates how to implement push-like behavior using HTTP long polling
"""
import asyncio
import time
from typing import Dict, List, Optional
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Models
class Message(BaseModel):
    id: str
    sender: str
    text: str
    timestamp: float
    room: str = "general"

class SendMessageRequest(BaseModel):
    sender: str
    text: str
    room: str = "general"

class PollResponse(BaseModel):
    messages: List[Message]
    status: str
    timeout: bool = False

# Global state for long polling
class LongPollState:
    def __init__(self):
        # Store client queues: {client_id: asyncio.Queue}
        self.client_queues: Dict[str, asyncio.Queue] = {}
        # Message history for late joiners
        self.message_history: List[Message] = []
        # Room subscriptions: {client_id: room_name}
        self.client_rooms: Dict[str, str] = {}
        self.lock = asyncio.Lock()
    
    async def add_client(self, client_id: str, room: str = "general"):
        """Register a new client for long polling"""
        async with self.lock:
            if client_id not in self.client_queues:
                self.client_queues[client_id] = asyncio.Queue()
            self.client_rooms[client_id] = room
            print(f"Client {client_id} joined room '{room}'. Total clients: {len(self.client_queues)}")
    
    async def remove_client(self, client_id: str):
        """Remove client when they disconnect"""
        async with self.lock:
            if client_id in self.client_queues:
                del self.client_queues[client_id]
                del self.client_rooms[client_id]
                print(f"Client {client_id} disconnected. Remaining: {len(self.client_queues)}")
    
    async def broadcast_message(self, message: Message):
        """Broadcast message to all clients in the same room"""
        # Add to history
        self.message_history.append(message)
        
        # Keep only last 100 messages
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        
        # Send to all clients in the same room
        async with self.lock:
            clients_to_remove = []
            for client_id, queue in self.client_queues.items():
                client_room = self.client_rooms.get(client_id, "general")
                if client_room == message.room:
                    try:
                        # Non-blocking put - if queue is full, skip this client
                        queue.put_nowait(message)
                        print(f"Pushed message to client {client_id} in room {message.room}")
                    except asyncio.QueueFull:
                        print(f"Queue full for client {client_id}, removing...")
                        clients_to_remove.append(client_id)
            
            # Remove clients with full queues
            for client_id in clients_to_remove:
                if client_id in self.client_queues:
                    del self.client_queues[client_id]
                    del self.client_rooms[client_id]
    
    async def wait_for_message(self, client_id: str, last_message_id: Optional[str] = None, timeout: int = 30) -> PollResponse:
        """Long poll for new messages"""
        await self.add_client(client_id)
        
        # First, check if there are recent messages in history
        recent_messages = []
        if last_message_id:
            # Find messages after the last seen ID
            found_last = False
            for msg in self.message_history:
                if found_last:
                    recent_messages.append(msg)
                elif msg.id == last_message_id:
                    found_last = True
        else:
            # No last message ID, get recent messages (last 5)
            recent_messages = self.message_history[-5:] if self.message_history else []
        
        # Filter by room
        client_room = self.client_rooms.get(client_id, "general")
        recent_messages = [msg for msg in recent_messages if msg.room == client_room]
        
        if recent_messages:
            return PollResponse(
                messages=recent_messages,
                status="success",
                timeout=False
            )
        
        # No recent messages, wait for new ones
        queue = self.client_queues[client_id]
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    # Wait for a message with a small timeout to allow periodic checks
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    return PollResponse(
                        messages=[message],
                        status="success",
                        timeout=False
                    )
                except asyncio.TimeoutError:
                    # Continue waiting
                    continue
            
            # Timeout reached
            return PollResponse(
                messages=[],
                status="timeout",
                timeout=True
            )
            
        except Exception as e:
            print(f"Error in long poll for client {client_id}: {e}")
            return PollResponse(
                messages=[],
                status="error",
                timeout=True
            )

# Global state instance
poll_state = LongPollState()

# Cleanup task to remove inactive clients
async def cleanup_inactive_clients():
    """Background task to clean up inactive clients"""
    while True:
        await asyncio.sleep(60)  # Run every minute
        current_time = time.time()
        
        async with poll_state.lock:
            # Remove clients that haven't polled in 5 minutes
            # (In a real app, you'd track last activity time)
            inactive_clients = []
            for client_id in poll_state.client_queues:
                # This is a simplified cleanup - in production you'd track last activity
                if len(poll_state.client_queues[client_id]._queue) == 0:
                    # Queue is empty, but we'll keep the client for now
                    pass
            
            print(f"Active clients: {len(poll_state.client_queues)}")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FastAPI Long Polling Demo...")
    # Start cleanup task
    cleanup_task = asyncio.create_task(cleanup_inactive_clients())
    
    yield
    
    # Shutdown
    print("Shutting down...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Create FastAPI app
app = FastAPI(
    title="FastAPI Long Polling Demo",
    description="Real-time chat using HTTP long polling",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve the chat HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/poll", response_model=PollResponse)
async def long_poll(
    client_id: str = Query(..., description="Unique client identifier"),
    room: str = Query("general", description="Chat room name"),
    last_message_id: Optional[str] = Query(None, description="Last seen message ID"),
    timeout: int = Query(25, ge=5, le=60, description="Timeout in seconds")
):
    """
    Long polling endpoint - holds request open until message arrives or timeout
    
    This is the core of the long polling mechanism:
    1. Client makes request and waits
    2. Server holds the request open
    3. When new message arrives, server immediately responds
    4. Client processes response and immediately makes new request
    """
    print(f"Long poll request from client {client_id} in room '{room}', timeout={timeout}s")
    
    # Set room for this client
    if client_id in poll_state.client_rooms:
        poll_state.client_rooms[client_id] = room
    
    result = await poll_state.wait_for_message(client_id, last_message_id, timeout)
    print(f"Responding to client {client_id}: {len(result.messages)} messages, timeout={result.timeout}")
    
    return result

@app.post("/api/send", response_model=dict)
async def send_message(message_request: SendMessageRequest):
    """
    Send a message - this triggers push to all waiting clients
    """
    if not message_request.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")
    
    message = Message(
        id=str(uuid.uuid4()),
        sender=message_request.sender,
        text=message_request.text.strip(),
        timestamp=time.time(),
        room=message_request.room
    )
    
    print(f"Broadcasting message from {message.sender} in room '{message.room}': {message.text}")
    
    # Broadcast to all clients - this will immediately respond to waiting long-poll requests
    await poll_state.broadcast_message(message)
    
    return {
        "status": "sent",
        "message_id": message.id,
        "timestamp": message.timestamp
    }

@app.get("/api/history")
async def get_message_history(
    room: str = Query("general", description="Room name"),
    limit: int = Query(20, ge=1, le=100, description="Number of recent messages")
):
    """Get recent message history for a room"""
    room_messages = [msg for msg in poll_state.message_history if msg.room == room]
    recent_messages = room_messages[-limit:] if room_messages else []
    
    return {
        "messages": recent_messages,
        "count": len(recent_messages),
        "room": room
    }

@app.get("/api/stats")
async def get_stats():
    """Get system stats for monitoring"""
    return {
        "active_clients": len(poll_state.client_queues),
        "total_messages": len(poll_state.message_history),
        "rooms": list(set(poll_state.client_rooms.values())) if poll_state.client_rooms else [],
        "timestamp": time.time()
    }

@app.delete("/api/client/{client_id}")
async def disconnect_client(client_id: str):
    """Manually disconnect a client"""
    await poll_state.remove_client(client_id)
    return {"status": "disconnected", "client_id": client_id}

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "active_clients": len(poll_state.client_queues)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
