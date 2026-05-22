"""Notes API — FastAPI + Google Cloud Firestore."""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
from pydantic import BaseModel

app = FastAPI(title="Notes API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ORIGINS", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)

COLLECTION = "notes"


def get_db() -> firestore.Client:
    return firestore.Client()


class NoteCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


@app.get("/health")
async def health():
    try:
        db = get_db()
        # Quick connectivity check
        db.collection(COLLECTION).limit(1).get()
        return {"status": "healthy", "database": "firestore", "connected": True}
    except Exception as e:
        return {"status": "degraded", "database": "firestore", "connected": False, "error": str(e)}


@app.post("/api/notes")
async def create_note(note: NoteCreate):
    db = get_db()
    note_id = str(uuid.uuid4())[:8]
    doc = {
        "title": note.title,
        "content": note.content,
        "category": note.category,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    db.collection(COLLECTION).document(note_id).set(doc)
    return {"id": note_id, "status": "created"}


@app.get("/api/notes")
async def list_notes(category: Optional[str] = None):
    db = get_db()
    query = db.collection(COLLECTION)
    if category:
        query = query.where("category", "==", category)
    query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
    docs = query.stream()
    notes = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        notes.append(d)
    return {"notes": notes, "count": len(notes)}


@app.get("/api/notes/{note_id}")
async def get_note(note_id: str):
    db = get_db()
    doc = db.collection(COLLECTION).document(note_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Note not found")
    data = doc.to_dict()
    data["id"] = doc.id
    return data


@app.put("/api/notes/{note_id}")
async def update_note(note_id: str, note: NoteUpdate):
    db = get_db()
    ref = db.collection(COLLECTION).document(note_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Note not found")
    updates = {k: v for k, v in note.dict().items() if v is not None}
    updates["updated_at"] = datetime.utcnow().isoformat()
    ref.update(updates)
    return {"id": note_id, "status": "updated"}


@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: str):
    db = get_db()
    ref = db.collection(COLLECTION).document(note_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Note not found")
    ref.delete()
    return {"id": note_id, "status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
