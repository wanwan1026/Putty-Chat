import os
from openai import OpenAI
import chromadb

DATA_DIR = "data"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "putty_knowledge"


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def load_documents():
    documents = []

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                documents.append({
                    "id": f"{filename}-{i}",
                    "text": chunk,
                    "source": filename,
                })

    return documents


def create_vector_db(client: OpenAI):
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    existing = collection.count()
    if existing > 0:
        return collection

    docs = load_documents()

    for doc in docs:
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=doc["text"]
        ).data[0].embedding

        collection.add(
            ids=[doc["id"]],
            documents=[doc["text"]],
            embeddings=[embedding],
            metadatas=[{"source": doc["source"]}],
        )

    return collection


def retrieve_context(client: OpenAI, collection, query: str, top_k: int = 3):
    query_embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    retrieved = []
    for doc, meta in zip(docs, metas):
        retrieved.append({
            "text": doc,
            "source": meta["source"]
        })

    return retrieved