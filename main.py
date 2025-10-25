from fastapi import FastAPI

from controllers.session_controller import session_router

app = FastAPI()

app.include_router(session_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}