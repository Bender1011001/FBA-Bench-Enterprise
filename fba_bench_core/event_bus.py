"""Compatibility shim for fba_bench_core.event_bus.

Re-exports EventBus and related functions from the production event_bus module.
Provides convenience wrappers for common publish/subscribe patterns.
"""

from typing import Any, Callable, Optional
from event_bus import EventBus, get_event_bus

__all__ = ["EventBus", "get_event_bus", "publish", "subscribe", "unsubscribe"]


def publish(event_type: str, payload: Any, **kwargs: Any) -> None:
    """Publish an event to the event bus.

    Delegates to get_event_bus().publish().

    Args:
        event_type: The type of the event.
        payload: The event payload.
        **kwargs: Additional keyword arguments passed to the underlying publish.
    """
    get_event_bus().publish(event_type=event_type, payload=payload, **kwargs)


def subscribe(event_type: str, callback: Callable[[Any], None], **kwargs: Any) -> Optional[str]:
    """Subscribe to an event type.

    Delegates to get_event_bus().subscribe().

    Args:
        event_type: The type of event to subscribe to.
        callback: The callback function to invoke on event receipt.
        **kwargs: Additional keyword arguments passed to the underlying subscribe.

    Returns:
        The subscription ID if returned by the underlying method, else None.
    """
    return get_event_bus().subscribe(event_type=event_type, callback=callback, **kwargs)


def unsubscribe(subscription_id: Optional[str] = None, event_type: Optional[str] = None, callback: Optional[Callable[[Any], None]] = None) -> None:
    """Unsubscribe from events.

    Delegates to get_event_bus().unsubscribe(). Supports unsubscribing by ID, type+callback, or all.

    Args:
        subscription_id: Specific subscription ID to unsubscribe (if provided).
        event_type: Event type to unsubscribe from (if callback provided).
        callback: Callback to match for unsubscription (if event_type provided).
    """
    get_event_bus().unsubscribe(subscription_id=subscription_id, event_type=event_type, callback=callback)