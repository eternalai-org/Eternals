from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from eternal_agent.service import AutoServiceProvider
from eternal_agent.models import ChatSession

router = APIRouter()
api_v1_router = APIRouter()

__all__ = [
    "api_v1_router"
]

@router.get("/health")
def health_check():
    return PlainTextResponse("", status_code=200)

@api_v1_router.post("/init-chat")
def init_chat():
    provider = AutoServiceProvider()
    new_session_id = provider.initialize_chat_session(ChatSession())
    return JSONResponse(content={
        "session_id": new_session_id
    }, status_code=200)

@api_v1_router.post("/chat/{session_id}")
def chat(session_id: str, message: str):
    provider = AutoServiceProvider()

    try:
        response = provider.execute_chat_completion(session_id, message)
    except ValueError as err:
        return JSONResponse(content={"error": str(err)}, status_code=400) 

    return JSONResponse(content={
        "response": response
    }, status_code=200)

@api_v1_router.get("/chat/{session_id}/history")
def history(session_id: str):
    provider = AutoServiceProvider()

    try:
        history = provider.get_chat_session(session_id)
    except ValueError as err:
        return JSONResponse(content={"error": str(err)}, status_code=400)

    return JSONResponse(content={
        "history": history.model_dump()
    }, status_code=200)
    
@api_v1_router.get("/deinit-chat/{session_id}")
def deinit_chat(session_id: str):
    provider = AutoServiceProvider()

    try:
        provider.deinitialize_chat_session(session_id)
    except ValueError as err:
        return JSONResponse(content={"error": str(err)}, status_code=400)

    return JSONResponse(content={}, status_code=200)