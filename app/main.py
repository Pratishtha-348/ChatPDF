import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import User, Document, Conversation, UserRole
from .schemas import (
    UserCreate, AdminCreate, Token, UserOut, IngestRequest, IngestResponse, 
    QueryRequest, QueryResponse, Source, ConversationMessage, ConversationHistory,
    DocumentInfo
)
from .auth import (
    get_current_user, get_admin_user, hash_password, verify_password, 
    create_access_token, get_user_by_email, ADMIN_SECRET_KEY
)
from fastapi.security import OAuth2PasswordRequestForm
from .rag import ingest_text, retrieve, generate_answer, generate_answer_stream
from dotenv import load_dotenv
load_dotenv()

import io, re, uuid
from pypdf import PdfReader
from typing import List
from fastapi.responses import StreamingResponse
import json
from fastapi.middleware.cors import CORSMiddleware

chat_sessions = {}

app = FastAPI(title="RAG System with Admin Control")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL, e.g., "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------- Auth -------------
@app.post("/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Default role is USER
    user = User(
        email=payload.email, 
        hashed_password=hash_password(payload.password),
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/register-admin", response_model=UserOut)
def register_admin(payload: AdminCreate, db: Session = Depends(get_db)):
    # Verify admin secret key
    if payload.admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=payload.email, 
        hashed_password=hash_password(payload.password),
        role=UserRole.ADMIN
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token, 
        "token_type": "bearer",
        "role": user.role.value
    }

@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value
    }

# ------------- Helper functions -------------
def clean_text(text: str) -> str:
    text = re.sub(r"-\s*\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def to_uuid_maybe(doc_id: str):
    try:
        return uuid.UUID(doc_id)
    except Exception:
        return doc_id

# ------------- Admin-only Endpoints -------------
@app.post("/admin/ingest", response_model=IngestResponse)
def admin_ingest(
    req: IngestRequest, 
    admin_user: User = Depends(get_admin_user), 
    db: Session = Depends(get_db)
):
    """Admin-only: Ingest text that will be available to all users"""
    doc_id = ingest_text(
        user_id=admin_user.id, 
        text=req.text, 
        title=req.title,
        is_global=True  # Mark as global
    )
    doc = Document(
        id=to_uuid_maybe(doc_id), 
        user_id=admin_user.id, 
        title=req.title,
        is_global=True
    )
    db.add(doc)
    db.commit()
    return {"doc_id": str(doc_id), "title": req.title}

@app.post("/admin/ingest_pdf", response_model=IngestResponse)
async def admin_ingest_pdf(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin-only: Upload PDF that will be available to all users"""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    
    try:
        reader = PdfReader(io.BytesIO(contents))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        raw_text = "\n\n".join(pages)
        
        pdf_title = None
        if reader.metadata:
            pdf_title = getattr(reader.metadata, "title", None) or reader.metadata.get("/Title")
        final_title = title or pdf_title or file.filename
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
    
    text = clean_text(raw_text)
    if not text:
        raise HTTPException(status_code=400, detail="No extractable text found.")
    
    doc_id = ingest_text(
        user_id=admin_user.id, 
        text=text, 
        title=final_title,
        is_global=True  # Mark as global
    )
    doc = Document(
        id=to_uuid_maybe(doc_id), 
        user_id=admin_user.id, 
        title=final_title,
        is_global=True
    )
    db.add(doc)
    db.commit()
    
    return {"doc_id": str(doc_id), "title": final_title}

@app.get("/admin/documents", response_model=List[DocumentInfo])
def list_admin_documents(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: List all documents uploaded by admins"""
    docs = db.query(Document).filter(Document.is_global == True).all()
    return [
        {
            "id": str(doc.id),
            "title": doc.title,
            "uploaded_by": "Admin",
            "created_at": doc.created_at
        }
        for doc in docs
    ]

@app.delete("/admin/document/{doc_id}")
def delete_document(
    doc_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: Delete a document"""
    doc = db.query(Document).filter(Document.id == to_uuid_maybe(doc_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from ChromaDB
    try:
        from .rag import collection
        # Delete all chunks for this document
        collection.delete(where={"doc_id": doc_id})
    except Exception as e:
        print(f"Error deleting from ChromaDB: {e}")
    
    # Delete from Postgres
    db.delete(doc)
    db.commit()
    
    return {"status": "deleted", "doc_id": doc_id}

# ------------- User Endpoints (Query) -------------
@app.post("/rag/query", response_model=QueryResponse)
def rag_query(req: QueryRequest, current_user: User = Depends(get_current_user)):
    """All users can query admin-uploaded documents"""
    hits = retrieve(query=req.query, user_id=current_user.id, top_k=req.top_k)
    if not hits:
        return {"answer": "I don't know.", "sources": []}
    answer = generate_answer(req.query, hits)
    sources = [Source(doc_id=h["meta"]["doc_id"], score=h["score"], chunk=h["chunk"]) for h in hits]
    return {"answer": answer, "sources": sources}

@app.post("/rag/query_stream")
def rag_query_stream(req: QueryRequest, current_user: User = Depends(get_current_user)):
    """Streaming query for all users"""
    hits = retrieve(query=req.query, user_id=current_user.id, top_k=req.top_k)
    if not hits:
        def empty_stream():
            yield json.dumps({"answer": "I don't know.", "sources": []})
        return StreamingResponse(empty_stream(), media_type="application/json")
    
    def stream_response():
        try:
            for chunk in generate_answer_stream(req.query, hits):
                yield json.dumps({"chunk": chunk}) + "\n"
            
            sources = [{"doc_id": h["meta"]["doc_id"], "score": h["score"], "chunk": h["chunk"]} for h in hits]
            yield json.dumps({"sources": sources, "complete": True}) + "\n"
        except Exception as e:
            answer = generate_answer(req.query, hits)
            yield json.dumps({"chunk": answer}) + "\n"
    
    return StreamingResponse(stream_response(), media_type="application/x-ndjson")

# ------------- Conversations -------------
@app.post("/conversations/save")
def save_conversation(
    message: ConversationMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = Conversation(
        user_id=current_user.id,
        role=message.role,
        content=message.content
    )
    db.add(conv)
    db.commit()
    return {"status": "saved"}

@app.get("/conversations/history", response_model=ConversationHistory)
def get_conversation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).limit(limit).all()
    
    messages = [
        ConversationMessage(role=c.role, content=c.content)
        for c in reversed(conversations)
    ]
    return {"messages": messages}

@app.delete("/conversations/clear")
def clear_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Conversation).filter(Conversation.user_id == current_user.id).delete()
    db.commit()
    return {"status": "cleared"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)



@app.post("/chat/upload")
async def chat_upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF for a temporary chat session.
    Parses, chunks, and stores the text in memory.
    Returns a unique session_id.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    session_id = str(uuid.uuid4())
    
    try:
        contents = await file.read()
        reader = PdfReader(io.BytesIO(contents))
        
        # Extract text
        raw_text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
        cleaned_text = clean_text(raw_text)
        
        if not cleaned_text:
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")
            
        # Chunk the text using your existing RAG function
        from .rag import chunk_text
        chunks = chunk_text(cleaned_text)
        
        # Store in our in-memory session store
        chat_sessions[session_id] = {
            "title": file.filename,
            "chunks": chunks
        }
        
        return {"session_id": session_id, "filename": file.filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")


@app.post("/chat/query")
async def chat_query(
    query: str = Form(...),
    session_id: str = Form(...),
    top_k: int = Form(5)
):
    """
    Query against the document in a specific chat session.
    Uses a temporary, in-memory RAG pipeline.
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Invalid or expired chat session.")

    session_data = chat_sessions[session_id]
    chunks = session_data["chunks"]
    
    # --- Simplified In-Memory RAG Pipeline ---
    from rank_bm25 import BM25Okapi
    from .rag import normalize_text

    tokenized_docs = [normalize_text(doc).split() for doc in chunks]
    bm25 = BM25Okapi(tokenized_docs)
    
    tokenized_query = normalize_text(query).split()
    doc_scores = bm25.get_scores(tokenized_query)
    
    # Get top_k chunks
    top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
    
    # Create hits structure
    hits = [{"chunk": chunks[i], "score": float(doc_scores[i]), "meta": {}} for i in top_indices if doc_scores[i] > 0]

    if not hits:
        def empty_stream():
            yield json.dumps({"answer": "I couldn't find any relevant information in the document for your query.", "sources": []}) + "\n"
        return StreamingResponse(empty_stream(), media_type="application/x-ndjson")

    # Generate Answer (Streaming)
    from .rag import generate_answer_stream
    
    def stream_response():
        try:
            # Stream the answer chunks
            for chunk in generate_answer_stream(query, hits):
                yield json.dumps({"chunk": chunk}) + "\n"
            
            # Finally, yield the sources
            sources = [{"doc_id": "session_doc", "score": h["score"], "chunk": h["chunk"]} for h in hits[:3]]
            yield json.dumps({"sources": sources, "complete": True}) + "\n"
        except Exception as e:
            print(f"Streaming error: {e}")
            yield json.dumps({"chunk": "Sorry, I encountered an error generating the response.", "complete": True}) + "\n"

    return StreamingResponse(stream_response(), media_type="application/x-ndjson")