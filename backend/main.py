# /backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import StreamingResponse

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發階段先這樣
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.get("/")
def read_root():
    return {"message": "FastAPI working"}


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個友善、簡潔的 AI 助手，請用繁體中文回答。"},
                *[msg.model_dump() for msg in request.messages]
            ]
        )

        return {
            "reply": response.choices[0].message.content
        }
    except Exception as e:
        return {
            "error": str(e)
        }

@app.post("/chat-stream")
def chat_stream(request: ChatRequest):

    def generate():

        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個友善的 AI 助手，請用繁體中文回答。"},
                *[msg.model_dump() for msg in request.messages]
            ],
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(generate(), media_type="text/plain")