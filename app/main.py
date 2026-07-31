import os
import io
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from pypdf import PdfReader

app = FastAPI(title="Enterprise RAG Core Engine")

# Initialize client SDKs using environment variables
openai_client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.getenv("GITHUB_TOKEN")
)
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"), 
    port=int(os.getenv("QDRANT_PORT", 6333))
)

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "enterprise_knowledge")
VECTOR_SIZE = 1536  # Matches OpenAI text-embedding-ada-002 / text-embedding-3-small

# Life-cycle hook: Ensure vector collection exists before taking traffic
@app.on_event("startup")
def prepare_vector_db():
    try:
        collections = qdrant_client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            print(f"Initialized collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Database connection initialization failed: {e}")

# Data structures for handling API communication
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list[str]

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Slices character streams into sliding windows to preserve semantic context."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

@app.post("/ingest")
async def ingest_document(
    request: Request,
    x_document_name: str = Header(default="document.txt", alias="X-Document-Name")
):
    """Automated ingestion endpoint executed by Apache NiFi."""
    try:
        # 1. Read raw byte stream from incoming HTTP body
        contents = await request.body()
        
        # 2. Extract text based on file type
        if x_document_name.lower().endswith(".pdf"):
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            text_content = "\n".join([page.extract_text() or "" for page in reader.pages])
        else:
            # Treats .md, .txt, etc. as UTF-8 text
            text_content = contents.decode("utf-8", errors="ignore")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Document contains no readable text data.")

        # 3. Document Processing: Structural Chunking
        chunks = chunk_text(text_content)
        
        # 4. Mass Vectorization Loop
        points = []
        for idx, chunk in enumerate(chunks):
            embedding_response = openai_client.embeddings.create(
                input=[chunk],
                model="openai/text-embedding-3-small"
            )
            vector = embedding_response.data[0].embedding
            
            point_id = hash(f"{x_document_name}_{idx}") & 0xffffffffffffffff
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload={"filename": x_document_name, "chunk_index": idx, "page_content": chunk}
            ))
            
        # 5. Atomic Vector Store Upsert
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        return {"status": "success", "chunks_processed": len(chunks), "file": x_document_name}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """The Runtime Retrieval-Augmented Generation Execution Loop."""
    try:
        # Step 1: Vectorize incoming natural language query
        query_vector_res = openai_client.embeddings.create(
            input=[request.query],
            model="openai/text-embedding-3-small"
        )
        query_vector = query_vector_res.data[0].embedding

        # Step 2: Query-to-Store Dot Product Matching (Cosine Similarity Search)
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=3  # Retrieve Top-K nearest neighbors
        )

        # Step 3: Extract payloads and synthesize the context window
        retrieved_chunks = [hit.payload["page_content"] for hit in search_results if hit.payload]
        context_str = "\n---\n".join(retrieved_chunks)

        # Step 4: System Prompt Injection & Context Grounding
        system_prompt = (
            "You are a secure Enterprise AI Assistant. Answer the user's question using ONLY the provided "
            "context blocks below. If the answer cannot be confidently derived from the context, state "
            "explicitly that you do not possess that information. Do not use external knowledge.\n\n"
            f"CONTEXT KNOWLEDGE BASE:\n{context_str}"
        )

        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            temperature=0.0  # Force maximum determinism to control hallucination risks
        )

        return QueryResponse(
            answer=completion.choices[0].message.content,
            retrieved_chunks=retrieved_chunks
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
