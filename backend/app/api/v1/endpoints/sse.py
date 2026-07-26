import asyncio
import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.sse_manager import sse_manager

logger = logging.getLogger("app.api.v1.endpoints.sse")
router = APIRouter(prefix="/sse")


@router.get("/stream")
async def sse_event_stream():
    """Server-Sent Events streaming endpoint.
    
    Establishes a persistent client connection to receive real-time behavioral updates.
    """
    queue = sse_manager.subscribe()
    
    async def sse_generator():
        from app.services.metrics_service import metrics_service
        try:
            logger.info("Client connected to SSE event stream.")
            metrics_service.active_sse += 1
            # Send initial keepalive/ping message to confirm registration
            yield f"data: {json.dumps({'type': 'CONNECTED', 'message': 'SSE live link operational'})}\n\n"
            
            while True:
                # Wait for published events
                payload = await queue.get()
                yield f"data: {json.dumps(payload)}\n\n"
                
        except asyncio.CancelledError:
            logger.info("Client disconnected from SSE stream (CancelledError).")
        except Exception as e:
            logger.error(f"Error in SSE generator loop: {e}", exc_info=True)
        finally:
            sse_manager.unsubscribe(queue)
            metrics_service.active_sse = max(0, metrics_service.active_sse - 1)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
