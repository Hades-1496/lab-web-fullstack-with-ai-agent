import os
import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

# PASO 1: CORS
ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PASO 2: Auth básica
DEMO_TOKEN = os.getenv("DEMO_TOKEN", "demo-token-12345")
security = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    if creds.credentials != DEMO_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")
    return {"user": "demo"}

class ChatInput(BaseModel):
    message: str
    session_id: str

# AGENTE SIMULADO PARA QUE PUEDAS TERMINAR EL LAB
class MockAgent:
    async def astream(self, input_data, config=None):
        msg = input_data.get("messages", [{}])[0].get("content", "")
        respuesta = f"¡Hola! Soy el agente simulado. He recibido tu mensaje: '{msg}'. Todo funciona perfectamente."
        # Simulamos que la IA "piensa" y envía palabra por palabra
        for word in respuesta.split():
            await asyncio.sleep(0.1)
            yield {"messages": [type("obj", (object,), {"content": word + " "})()]}

agente = MockAgent()

# PASO 5: Endpoint de Streaming
@app.post("/api/chat/stream")
async def chat_stream(body: ChatInput, user=Depends(get_current_user)):
    async def generar():
        async for chunk in agente.astream(
            {"messages": [{"role": "user", "content": body.message}]},
            config={"configurable": {"thread_id": body.session_id}},
        ):
            if "messages" in chunk:
                content = chunk["messages"][-1].content
                if content:
                    safe = content.replace("\n", "\\n")
                    yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generar(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )