from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from controllers.session_controller import session_router
from controllers.chatbot_controller import chatbot_router
from controllers.websocket_controller import websocket_router

app = FastAPI(
    title="Smart Scheduler AI Agent",
    description="An AI-powered meeting scheduler with voice capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(session_router)
app.include_router(chatbot_router)
app.include_router(websocket_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Smart Scheduler AI Agent"}

@app.get("/")
def root():
    return {
        "message": "Smart Scheduler AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "message": "/message/",
            "websocket": "/ws/chat/{session_id}",
            "voice_websocket": "/ws/voice/{session_id}"
        }
    }