import asyncio
from event_system import event_bus
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_user_login(username: str, timestamp: datetime):
    logger.info(f"User {username} logged in at {timestamp}")
    await asyncio.sleep(0.5)
    logger.info(f"Welcome email sent to {username}")


async def on_user_action(action: str, user: str, **metadata):
    logger.info(f"User {user} performed action: {action}")
    if metadata:
        logger.info(f"Metadata: {metadata}")


def on_system_alert(alert_type: str, message: str):
    logger.warning(f"SYSTEM ALERT [{alert_type}]: {message}")


async def audit_logger(event_name: str, *args, **kwargs):
    logger.info(f"[AUDIT] Event '{event_name}' triggered with args={args}, kwargs={kwargs}")


class OrderService:
    def __init__(self):
        event_bus.on('order:created', self.handle_order_created)
        event_bus.on('order:cancelled', self.handle_order_cancelled)
    
    async def handle_order_created(self, order_id: str, customer: str, amount: float):
        logger.info(f"Processing new order #{order_id} from {customer} for ${amount}")
        await event_bus.emit('payment:process', order_id, amount)
    
    async def handle_order_cancelled(self, order_id: str, reason: str):
        logger.info(f"Order #{order_id} cancelled. Reason: {reason}")
        await event_bus.emit('inventory:restore', order_id)


class PaymentService:
    def __init__(self):
        event_bus.on('payment:process', self.process_payment)
    
    async def process_payment(self, order_id: str, amount: float):
        logger.info(f"Processing payment for order #{order_id}: ${amount}")
        await asyncio.sleep(1)
        success = amount < 1000
        
        if success:
            logger.info(f"Payment successful for order #{order_id}")
            await event_bus.emit('order:confirmed', order_id)
        else:
            logger.error(f"Payment failed for order #{order_id}")
            await event_bus.emit('order:failed', order_id, "Payment declined")


async def main():
    logger.info("=== Event System Example ===\n")
    
    event_bus.on('user:login', on_user_login)
    event_bus.on('user:action', on_user_action)
    event_bus.on('system:alert', on_system_alert)
    
    event_bus.on('*', audit_logger)
    
    order_service = OrderService()
    payment_service = PaymentService()
    
    logger.info("1. User Login Event")
    await event_bus.emit('user:login', 'john_doe', datetime.now())
    await asyncio.sleep(1)
    
    logger.info("\n2. User Action Events")
    await event_bus.emit('user:action', 'view_product', 'john_doe', product_id='ABC123', category='Electronics')
    await asyncio.sleep(0.5)
    
    logger.info("\n3. System Alert (Synchronous)")
    event_bus.emit_sync('system:alert', 'HIGH_CPU', 'CPU usage exceeded 90%')
    
    logger.info("\n4. Order Processing Chain")
    await event_bus.emit('order:created', 'ORD-001', 'john_doe', 599.99)
    await asyncio.sleep(2)
    
    logger.info("\n5. One-time Event Handler")
    async def special_offer_handler(user: str, discount: float):
        logger.info(f"Special offer: {discount}% off for {user}! (This handler will only run once)")
    
    event_bus.once('special:offer', special_offer_handler)
    await event_bus.emit('special:offer', 'john_doe', 25)
    await event_bus.emit('special:offer', 'jane_doe', 30)
    
    logger.info("\n6. Event History")
    history = event_bus.get_history()
    logger.info(f"Total events in history: {len(history)}")
    
    user_events = event_bus.get_history('user:login')
    logger.info(f"User login events: {len(user_events)}")
    
    logger.info("\n7. Event Listeners Info")
    logger.info(f"Active event types: {event_bus.event_names()}")
    logger.info(f"Listeners for 'user:login': {event_bus.listener_count('user:login')}")
    
    logger.info("\n8. Removing Listeners")
    event_bus.off('user:action', on_user_action)
    logger.info("Removed user:action handler")
    await event_bus.emit('user:action', 'logout', 'john_doe')
    
    logger.info("\n=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())