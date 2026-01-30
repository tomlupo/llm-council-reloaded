"""FastAPI application for LLM Council Reloaded."""

import json
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.settings import (
    Settings,
    get_settings,
    load_settings,
    save_settings,
)
from backend.storage import (
    add_assistant_message,
    add_user_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)
from backend.council import get_enabled_models
from backend.model_catalog import get_catalog

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="LLM Council Reloaded")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_settings()


# --- Request/Response Models ---

class SendMessageRequest(BaseModel):
    content: str
    web_search: bool = False
    execution_mode: str = "full"  # "full", "chat_only", "chat_ranking"
    deliberation_mode: str = "ask"  # "ask", "debate", "decide", "minmax", "brainstorm"
    mode_config: Optional[dict] = None


class CreateConversationResponse(BaseModel):
    id: str


# --- SSE helper ---

def _sse_encode(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# --- Pipeline factory ---

def _get_pipeline(mode: str, mode_config: dict | None):
    if mode == "debate":
        from backend.pipelines.debate import DebatePipeline
        return DebatePipeline()
    elif mode == "decide":
        from backend.pipelines.decide import DecidePipeline
        return DecidePipeline()
    elif mode == "minmax":
        from backend.pipelines.minmax import MinmaxPipeline
        return MinmaxPipeline()
    elif mode == "brainstorm":
        from backend.pipelines.brainstorm import BrainstormPipeline
        return BrainstormPipeline()
    elif mode == "ask":
        from backend.pipelines.ask import AskPipeline
        return AskPipeline()
    else:
        raise ValueError(f"Unknown deliberation mode: {mode}")


# --- API Endpoints ---

@app.post("/api/conversations", response_model=CreateConversationResponse)
async def create_conv():
    conv_id = create_conversation()
    return CreateConversationResponse(id=conv_id)


@app.get("/api/conversations")
async def list_convs():
    return list_conversations()


@app.get("/api/conversations/{conv_id}")
async def get_conv(conv_id: str):
    try:
        return get_conversation(conv_id)
    except FileNotFoundError:
        raise HTTPException(404, "Conversation not found")


@app.delete("/api/conversations/{conv_id}")
async def delete_conv(conv_id: str):
    if not delete_conversation(conv_id):
        raise HTTPException(404, "Conversation not found")
    return {"ok": True}


@app.post("/api/conversations/{conv_id}/messages")
async def send_message_stream(conv_id: str, req: SendMessageRequest):
    # Store user message
    add_user_message(conv_id, req.content, metadata={
        "deliberation_mode": req.deliberation_mode,
        "execution_mode": req.execution_mode,
    })

    async def generate():
        try:
            pipeline = _get_pipeline(req.deliberation_mode, req.mode_config)
        except ValueError as e:
            yield _sse_encode("error", {"message": str(e)})
            return

        collected_data: dict = {}
        final_content = ""

        try:
            async for evt in pipeline.execute(req.content, req.mode_config):
                event_name = evt.get("event", "unknown")
                event_data = evt.get("data", {})
                yield _sse_encode(event_name, event_data)

                # Collect data for storage
                if event_name.endswith("_complete"):
                    collected_data[event_name] = event_data
                if "content" in event_data:
                    final_content = event_data["content"]

            yield _sse_encode("done", {"status": "complete"})
        except Exception as e:
            yield _sse_encode("error", {"message": str(e)})
            return

        # Store assistant response
        add_assistant_message(
            conv_id,
            content=final_content or json.dumps(collected_data),
            metadata={
                "deliberation_mode": req.deliberation_mode,
                "execution_mode": req.execution_mode,
                "mode_config": req.mode_config,
            },
            mode_data=collected_data,
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Settings endpoints ---

@app.get("/api/settings")
async def get_settings_endpoint():
    return get_settings().model_dump()


@app.put("/api/settings")
async def update_settings_endpoint(settings: Settings):
    save_settings(settings)
    return {"ok": True}


@app.get("/api/models")
async def list_models():
    return [m.model_dump() for m in get_enabled_models()]


@app.get("/api/model-catalog")
async def model_catalog():
    """Full model lists per provider for searchable dropdowns."""
    return get_catalog()
