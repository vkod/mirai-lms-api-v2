from pyee.asyncio import AsyncIOEventEmitter
from typing import Any, Callable, Optional
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventBus:
    _instance: Optional['EventBus'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._emitter = AsyncIOEventEmitter()
        self._event_history = []
        self._max_history = 100
        self._initialized = True
    
    def on(self, event: str, handler: Callable) -> None:
        self._emitter.on(event, handler)
        logger.debug(f"Handler registered for event: {event}")
    
    def once(self, event: str, handler: Callable) -> None:
        self._emitter.once(event, handler)
        logger.debug(f"One-time handler registered for event: {event}")
    
    def off(self, event: str, handler: Callable) -> None:
        self._emitter.remove_listener(event, handler)
        logger.debug(f"Handler removed for event: {event}")
    
    async def emit(self, event: str, *args, **kwargs) -> None:
        self._add_to_history(event, args, kwargs)
        self._emitter.emit(event, *args, **kwargs)
        logger.debug(f"Event emitted: {event}")
    
    def emit_sync(self, event: str, *args, **kwargs) -> None:
        self._add_to_history(event, args, kwargs)
        self._emitter.emit(event, *args, **kwargs)
        logger.debug(f"Event emitted (sync): {event}")
    
    def _add_to_history(self, event: str, args: tuple, kwargs: dict) -> None:
        self._event_history.append({
            'event': event,
            'timestamp': datetime.now(),
            'args': args,
            'kwargs': kwargs
        })
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def get_history(self, event: Optional[str] = None) -> list:
        if event:
            return [e for e in self._event_history if e['event'] == event]
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        self._event_history.clear()
    
    def remove_all_listeners(self, event: Optional[str] = None) -> None:
        if event:
            self._emitter.remove_all_listeners(event)
            logger.debug(f"All handlers removed for event: {event}")
        else:
            self._emitter.remove_all_listeners()
            logger.debug("All event handlers removed")
    
    def listener_count(self, event: str) -> int:
        return len(self._emitter.listeners(event))
    
    def event_names(self) -> list:
        return list(self._emitter._events.keys()) if hasattr(self._emitter, '_events') else []


event_bus = EventBus()