from typing import Any, Callable
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable[[Any], None]]] = {}
        self._lock = Lock()

    def subscribe(self, event_name: str, handler: Callable[[Any], None]) -> None:
        with self._lock:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
            logger.debug(f"Subscribed handler to event '{event_name}'")

    def publish(self, event_name: str, payload: Any) -> None:
        with self._lock:
            if event_name in self._handlers:
                for handler in self._handlers[event_name]:
                    try:
                        handler(payload)
                    except Exception as e:
                        logger.error(f"Handler failed for event '{event_name}': {e}")
            else:
                logger.debug(f"No handlers for event '{event_name}'")

    def unsubscribe(self, event_name: str, handler: Callable[[Any], None]) -> None:
        with self._lock:
            if event_name in self._handlers:
                self._handlers[event_name] = [h for h in self._handlers[event_name] if h != handler]
                if not self._handlers[event_name]:
                    del self._handlers[event_name]
                logger.debug(f"Unsubscribed handler from event '{event_name}'")

# Global singleton instance
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    return _event_bus