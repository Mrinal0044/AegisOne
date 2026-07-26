import asyncio
import logging
from typing import Set, Dict, Any, Optional

logger = logging.getLogger("app.services.sse_manager")


class SSEManager:
    _instance: Optional["SSEManager"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SSEManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._listeners: Set[asyncio.Queue] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def subscribe(self) -> asyncio.Queue:
        """Create a new event queue listener for a client streaming session."""
        q = asyncio.Queue()
        self._listeners.add(q)
        logger.debug(f"New client subscribed to SSE stream. Total subscribers: {len(self._listeners)}")
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """Remove a client queue listener when the streaming session disconnects."""
        self._listeners.discard(q)
        logger.debug(f"Client disconnected from SSE stream. Total subscribers: {len(self._listeners)}")

    def publish(self, event_type: str, data: Any) -> None:
        """Publishes an event payload to all active client queues in a thread-safe manner."""
        if not self._listeners:
            return

        payload = {
            "type": event_type,
            "data": data
        }

        # Check if there is an active event loop running in the current thread
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop.is_running():
            # Current thread has a running loop, put data directly in the queues
            for q in list(self._listeners):
                q.put_nowait(payload)
        else:
            # Synchronous context, schedule the put thread-safely on the main loop
            main_loop = self.loop
            if main_loop and main_loop.is_running():
                for q in list(self._listeners):
                    main_loop.call_soon_threadsafe(q.put_nowait, payload)
            else:
                logger.warning("No running event loop available to publish thread-safe SSE message.")


# Singleton instance
sse_manager = SSEManager()
