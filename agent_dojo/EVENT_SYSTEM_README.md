# Event System Implementation

## Overview
A lightweight event system using the `pyee` library that provides both synchronous and asynchronous event handling with a singleton EventBus pattern.

## Installation
```bash
pip install pyee
```

## Basic Usage

### Import the Event Bus
```python
from agent_dojo.event_system import event_bus
```

### Register Event Handlers
```python
# Regular handler (will be called every time event is emitted)
def on_user_login(username, timestamp):
    print(f"User {username} logged in at {timestamp}")

event_bus.on('user:login', on_user_login)

# One-time handler (will be called only once)
event_bus.once('first:visit', lambda user: print(f"Welcome {user}!"))
```

### Emit Events
```python
# Asynchronous emission (for async handlers)
await event_bus.emit('user:login', 'john_doe', datetime.now())

# Synchronous emission
event_bus.emit_sync('system:alert', 'HIGH_CPU', 'CPU usage exceeded 90%')
```

### Remove Handlers
```python
# Remove specific handler
event_bus.off('user:login', on_user_login)

# Remove all handlers for an event
event_bus.remove_all_listeners('user:login')

# Remove all handlers for all events
event_bus.remove_all_listeners()
```

## Advanced Features

### Event History
The EventBus maintains a history of the last 100 events:
```python
# Get all history
history = event_bus.get_history()

# Get history for specific event
login_events = event_bus.get_history('user:login')

# Clear history
event_bus.clear_history()
```

### Event Information
```python
# Get all registered event types
events = event_bus.event_names()

# Count listeners for an event
count = event_bus.listener_count('user:login')
```

### Wildcard Handler
Register a handler for all events:
```python
async def audit_logger(event_name, *args, **kwargs):
    print(f"[AUDIT] Event '{event_name}' triggered")

event_bus.on('*', audit_logger)
```

## Example: Microservices Communication

```python
class OrderService:
    def __init__(self):
        event_bus.on('order:created', self.handle_order_created)
    
    async def handle_order_created(self, order_id, customer, amount):
        # Process order
        await event_bus.emit('payment:process', order_id, amount)

class PaymentService:
    def __init__(self):
        event_bus.on('payment:process', self.process_payment)
    
    async def process_payment(self, order_id, amount):
        # Process payment
        if success:
            await event_bus.emit('order:confirmed', order_id)
```

## Integration with FastAPI

```python
from fastapi import FastAPI
from agent_dojo.event_system import event_bus

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Register handlers
    event_bus.on('user:registered', send_welcome_email)
    event_bus.on('order:placed', process_order)

@app.post("/users")
async def create_user(user: User):
    # Create user
    await event_bus.emit('user:registered', user.email, user.name)
    return {"status": "success"}
```

## Best Practices

1. **Event Naming Convention**: Use colon-separated namespaces (e.g., `user:login`, `order:created`)
2. **Error Handling**: Wrap handlers in try-catch blocks for production
3. **Memory Management**: Clear event history periodically if not needed
4. **Singleton Pattern**: The EventBus is a singleton - same instance across entire application
5. **Async vs Sync**: Use `emit()` for async handlers, `emit_sync()` for synchronous ones

## Running the Example
```bash
cd agent_dojo
python event_example.py
```

This will demonstrate all features including event chaining, one-time handlers, history tracking, and listener management.