"""Events compatibility shim.

Re-exports EventBus/get_event_bus from the production event_bus module and provides
convenience wrappers (publish/subscribe/unsubscribe). Also re-exports
AdversarialResponse for compatibility with code importing from 'events'.
"""

from typing import Any, Callable

from event_bus import EventBus, get_event_bus
from fba_events.adversarial import AdversarialResponse

__all__ = ["EventBus", "get_event_bus", "publish", "subscribe", "unsubscribe", "AdversarialResponse"]


def publish(event_name: str, payload: Any) -> None:
    """Publish an event on the global EventBus.

    Args:
        event_name: The event's name/type.
        payload: The event payload to dispatch to subscribers.
    """
    get_event_bus().publish(event_name, payload)


def subscribe(event_name: str, handler: Callable[[Any], None]) -> None:
    """Subscribe a handler to an event on the global EventBus.

    Args:
        event_name: The event name/type to subscribe to.
        handler: A callable that accepts the event payload.
    """
    get_event_bus().subscribe(event_name, handler)


def unsubscribe(event_name: str, handler: Callable[[Any], None]) -> None:
    """Unsubscribe a handler from an event on the global EventBus.

    Args:
        event_name: The event name/type to unsubscribe from.
        handler: The handler previously registered for this event.
    """
    get_event_bus().unsubscribe(event_name, handler)