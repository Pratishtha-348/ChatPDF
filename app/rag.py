import os, uuid, re
from typing import List, Dict, Any
from datetime import datetime
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv
import google.generativeai as genai
from rank_bm25 import BM25Okapi
import numpy as np

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Embeddings
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="docs", embedding_function=embedding_fn)

def get_current_date_info() -> Dict[str, str]:
    """Get current date information for context"""
    now = datetime.now()
    return {
        "full_date": now.strftime("%B %d, %Y"),  # January 15, 2025
        "day_name": now.strftime("%A"),  # Monday
        "short_date": now.strftime("%Y-%m-%d"),  # 2025-01-15
        "month": now.strftime("%B"),  # January
        "year": now.strftime("%Y"),  # 2025
    }

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Smart chunking that preserves paragraph structure"""
    text = text.strip()
    if not text:
        return []
    
    sections = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        section_size = len(section)
        
        if current_size + section_size > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
            current_size = len(current_chunk[0]) if current_chunk else 0
        
        current_chunk.append(section)
        current_size += section_size
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return [c.strip() for c in chunks if c.strip()]

def ingest_text(user_id: int, text: str, title: str | None = None, doc_id: str | None = None, is_global: bool = False) -> str:
    """Ingest text with global flag for admin uploads"""
    doc_id = doc_id or str(uuid.uuid4())
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No text to ingest")

    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    
    # Store metadata with global flag
    metadatas = [
        {
            "user_id": str(user_id) if not is_global else "global",
            "doc_id": doc_id,
            "title": title or "",
            "is_global": str(is_global),
            "uploaded_by": str(user_id)
        } 
        for _ in chunks
    ]
    
    collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
    return doc_id

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    typo_map = {
        "polocies": "policies", "polcy": "policy", "referal": "referral",
        "bonu": "bonus", "experiance": "experience", "employe": "employee"
    }
    for typo, correct in typo_map.items():
        text = text.replace(typo, correct)
    return text

def expand_query(query: str) -> List[str]:
    base_query = normalize_text(query)
    queries = [base_query, query]
    
    expansions = {
        "pip": ["pip", "performance improvement plan"],
        "referral": ["referral", "refer", "reference", "employee recommendation"],
        "bonus": ["bonus", "incentive", "reward", "compensation"],
        "leave": ["leave", "absence", "time off", "vacation"],
        "policy": ["policy", "policies", "rule", "regulation"],
        "wfh": ["wfh", "work from home", "remote"],
        "holiday": ["holiday", "holidays", "public holiday", "festival", "celebration"],
        "upcoming": ["upcoming", "next", "future", "coming"],
    }
    
    query_lower = base_query.lower()
    for key, terms in expansions.items():
        if key in query_lower:
            queries.extend(terms)
    
    return list(set(queries))

def reciprocal_rank_fusion(results_list: List[List[tuple]], k: int = 60) -> List[tuple]:
    fused_scores = {}
    
    for results in results_list:
        for rank, (doc_id, score) in enumerate(results):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (k + rank + 1)
    
    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

def retrieve(query: str, user_id: int, top_k: int = 8):
    """HYBRID RETRIEVAL: Access both user's own docs and global (admin) docs"""
    try:
        # Build the where clause to get:
        # 1. Documents uploaded by admin (is_global = "True")
        # 2. Documents specific to this user
        where_clause = {
            "$or": [
                {"is_global": "True"},  # Admin documents
                {"user_id": str(user_id)}  # User's own documents (if any)
            ]
        }
        
        # Get documents
        all_results = collection.query(
            query_texts=[""],
            n_results=100,
            where=where_clause
        )
        
        all_docs = all_results.get("documents", [[]])[0]
        all_metas = all_results.get("metadatas", [[]])[0]
        
        if not all_docs:
            return []
        
        # Semantic Search
        query_variations = expand_query(query)
        semantic_query = " ".join(query_variations)
        
        semantic_results = collection.query(
            query_texts=[semantic_query], 
            n_results=top_k * 2,
            where=where_clause
        )
        
        semantic_docs = semantic_results.get("documents", [[]])[0]
        semantic_ids = semantic_results.get("ids", [[]])[0]
        semantic_dists = semantic_results.get("distances", [[]])[0]
        
        semantic_rankings = [
            (doc_id, 1 / (1 + dist)) 
            for doc_id, dist in zip(semantic_ids, semantic_dists)
        ]
        
        # BM25 Search
        tokenized_docs = [normalize_text(doc).split() for doc in all_docs]
        bm25 = BM25Okapi(tokenized_docs)
        
        normalized_query = normalize_text(semantic_query)
        tokenized_query = normalized_query.split()
        bm25_scores = bm25.get_scores(tokenized_query)
        
        all_ids = all_results.get("ids", [[]])[0]
        
        bm25_rankings = [
            (doc_id, score) 
            for doc_id, score in zip(all_ids, bm25_scores)
            if score > 0
        ]
        bm25_rankings.sort(key=lambda x: x[1], reverse=True)
        bm25_rankings = bm25_rankings[:top_k * 2]
        
        # Fusion
        fused_rankings = reciprocal_rank_fusion([semantic_rankings, bm25_rankings])
        
        # Get results
        results = []
        doc_map = {
            doc_id: {"chunk": doc, "meta": meta}
            for doc_id, doc, meta in zip(all_ids, all_docs, all_metas)
        }
        
        for doc_id, fused_score in fused_rankings[:top_k]:
            if doc_id in doc_map:
                results.append({
                    "chunk": doc_map[doc_id]["chunk"],
                    "meta": doc_map[doc_id]["meta"],
                    "score": fused_score
                })
        
        return results
        
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []

def generate_answer(query: str, contexts: List[Dict[str, Any]]) -> str:
    if not contexts:
        return "I couldn't find any relevant information in the documents."
    
    # Get current date info
    date_info = get_current_date_info()
    
    contexts = sorted(contexts, key=lambda x: x['score'], reverse=True)[:6]
    context_text = "\n\n---\n\n".join([c['chunk'] for c in contexts])
    
    prompt = f"""You are a helpful assistant answering questions about company policies and documents.

TODAY'S DATE: {date_info['full_date']} ({date_info['day_name']})
CURRENT YEAR: {date_info['year']}

DOCUMENT CONTEXT:
{context_text}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS FOR DATE-RELATED QUESTIONS:
1. **Always consider today's date** when answering about "upcoming", "next", or future events
2. **Compare dates in the document with today's date** ({date_info['short_date']})
3. **For holiday questions**: Find holidays that come AFTER today's date
4. **Show your reasoning**: Explain which date is upcoming based on today
5. If multiple dates are listed, identify which ones are in the future

GENERAL RULES:
• Quote specific rules, dates, or numbers from the context
• Use bullet points (•) or numbered lists (1., 2., 3.)
• If you need to calculate something, show your steps
• If the answer is NOT in the context, say: "I don't have this specific information in the provided document."
• Be comprehensive - include ALL relevant details from the context
• Reference specific policy sections when applicable

FORMAT YOUR ANSWER:
• Use bullet points for clarity
• For date comparisons, explain: "Today is [date], so the next/upcoming [event] is..."
• Show calculations step-by-step if needed
• Quote exact text from context when relevant

ANSWER:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Slightly increased for better reasoning
                max_output_tokens=700,
                top_p=0.9,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Sorry, I couldn't generate a response. Please try again."

def generate_answer_stream(query: str, contexts: List[Dict[str, Any]]):
    if not contexts:
        yield "I couldn't find any relevant information in the documents."
        return
    
    # Get current date info
    date_info = get_current_date_info()
    
    contexts = sorted(contexts, key=lambda x: x['score'], reverse=True)[:6]
    context_text = "\n\n---\n\n".join([c['chunk'] for c in contexts])
    
    prompt = f"""You are a helpful assistant answering questions about company policies and documents.

TODAY'S DATE: {date_info['full_date']} ({date_info['day_name']})
CURRENT YEAR: {date_info['year']}

DOCUMENT CONTEXT:
{context_text}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS FOR DATE-RELATED QUESTIONS:
1. **Always consider today's date** when answering about "upcoming", "next", or future events
2. **Compare dates in the document with today's date** ({date_info['short_date']})
3. **For holiday questions**: Find holidays that come AFTER today's date
4. **Show your reasoning**: Explain which date is upcoming based on today
5. If multiple dates are listed, identify which ones are in the future

GENERAL RULES:
• Provide a clear, complete answer with all relevant details
• For dates: explain "Today is [date], so the next [event] is..."
• Quote specific information from the context
• Use bullet points for clarity
• If information is not in context, say so clearly

ANSWER:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=700,
                top_p=0.9,
            ),
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        print(f"Gemini streaming error: {e}")
        yield generate_answer(query, contexts)