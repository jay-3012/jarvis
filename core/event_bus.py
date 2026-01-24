import asyncio
from typing import Callable, Awaitable, Dict, List, Any
import structlog

logger = structlog.get_logger()

EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]

class EventBus:
    """
    Simple in-memory event bus for decoupling components.
    In production, this could be swapped for Redis Pub/Sub.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}", handler=handler)

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event to all subscribers."""
        if event_type not in self._subscribers:
            return

        handlers = self._subscribers[event_type]
        logger.info(f"Publishing event: {event_type}", subscriber_count=len(handlers))
        
        # Execute all handlers concurrently
        await asyncio.gather(*[handler(payload) for handler in handlers])

# Global instance
internal_bus = EventBus()
