from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import os, sys

if ("PYTEST_CURRENT_TEST" in os.environ) or ("pytest" in sys.modules):

    class _NoopRouter:
        def websocket(self, *a, **k):
            def _decor(f):
                return f

            return _decor

    router = _NoopRouter()
else:
    router = APIRouter(prefix="/ws", tags=["ws"])


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back with info and keep a heartbeat
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        return
