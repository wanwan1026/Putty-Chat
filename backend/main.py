# /backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastapi.responses import StreamingResponse
from rag import create_vector_db, retrieve_context

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
collection = create_vector_db(client)


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
        latest_user_message = request.messages[-1].content if request.messages else ""

        retrieved_docs = retrieve_context(client, collection, latest_user_message, top_k=3)

        context_text = "\n\n".join([
            f"[來源: {doc['source']}]\n{doc['text']}"
            for doc in retrieved_docs
        ])

        system_prompt = f"""
你是布丁（Putty），一個外向、溫暖、很會開話題的 AI 夥伴。
請根據提供的角色知識庫內容回答。
如果適合，可以自然延伸一句話或追問一個輕鬆的問題，鼓勵使用者多分享。
不要亂編角色設定，若知識庫沒有提到，就誠實說不知道。

以下是角色知識庫內容：
{context_text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *[msg.model_dump() for msg in request.messages]
            ]
        )

        return {
            "reply": response.choices[0].message.content,
            "sources": list({doc["source"] for doc in retrieved_docs})
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/chat-stream")
def chat_stream(request: ChatRequest):

    def generate():
        latest_user_message = request.messages[-1].content if request.messages else ""
        retrieved_docs = retrieve_context(client, collection, latest_user_message, top_k=3)

        context_text = "\n\n".join([
            f"[來源: {doc['source']}]\n{doc['text']}"
            for doc in retrieved_docs
        ])

        system_prompt = f"""
你是布丁（Putty），一個外向、溫暖、很會開話題的 AI 夥伴。
請根據提供的角色知識庫內容回答。
如果適合，可以自然延伸一句話或追問一個輕鬆的問題，鼓勵使用者多分享。
不要亂編角色設定，若知識庫沒有提到，就誠實說不知道。

以下是角色知識庫內容：
{context_text}
"""

        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *[msg.model_dump() for msg in request.messages]
            ],
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(generate(), media_type="text/plain")