from fastapi      import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from urllib.parse import urlparse, ParseResult
from pydantic     import BaseModel
from core         import Grok
from uvicorn      import run
import os


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def read_root():
    return FileResponse("index.html")

class ConversationRequest(BaseModel):
    proxy: str = None
    message: str
    model: str = "grok-3-auto"
    extra_data: dict = None

def format_proxy(proxy: str) -> str:
    
    if not proxy.startswith(("http://", "https://")):
        proxy: str = "http://" + proxy
    
    try:
        parsed: ParseResult = urlparse(proxy)

        if parsed.scheme not in ("http", ""):
            raise ValueError("Not http scheme")

        if not parsed.hostname or not parsed.port:
            raise ValueError("No url and port")

        if parsed.username and parsed.password:
            return f"http://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
        
        else:
            return f"http://{parsed.hostname}:{parsed.port}"
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid proxy format: {str(e)}")

@app.post("/ask")
async def create_conversation(request: ConversationRequest):
    if not request.proxy or not request.message:
        raise HTTPException(status_code=400, detail="Proxy and message are required")
    
    proxy = format_proxy(request.proxy)
    
    try:
        answer: dict = Grok(request.model, proxy).start_convo(request.message, request.extra_data)

        return {
            "status": "success",
            **answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6969))
    run("api_server:app", host="0.0.0.0", port=port)
