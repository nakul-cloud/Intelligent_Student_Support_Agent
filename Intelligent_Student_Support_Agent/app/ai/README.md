# 🧠 AI, Vector RAG & Document Ingestion (`app/ai`)

The **AI Layer** implements the end-to-end Retrieval-Augmented Generation (RAG) pipeline for university handbooks and institutional policy documents. It handles PDF document parsing, structure-preserving chunking, local dense vector embedding, and Qdrant vector database search.

---

## 🏗️ End-to-End RAG Ingestion & Retrieval Pipeline

```mermaid
flowchart TD
    subgraph Ingestion["1. Document Ingestion Pipeline (app/ai/ingestion/)"]
        PDF["📄 University Student Handbook (PDF)<br/>data/student_handbook.pdf"] --> Parser["PDFParser (pdf_parser.py)<br/>• Structural heading detection<br/>• Tabular clause reconstruction"]
        Parser --> Chunker["SemanticChunker (chunker.py)<br/>• Window: ~1800 chars (450 tokens)<br/>• Overlap: 200 chars for clause cohesion"]
        Chunker --> Embedder["LocalEmbedder (embedder.py)<br/>• Model: Orange/orange-nomic-v1.5-1536<br/>• 1536-dim Dense Embedding Vectors<br/>• Thread-safe Singleton & LRU Cache"]
    end

    Embedder --> VectorDB[("Qdrant Vector DB<br/>• Collection: student_handbook<br/>• Distance: Cosine Similarity<br/>• Payload: text, page, section_filter")]
    Embedder --> PostgresDocs[("PostgreSQL 'documents' Table<br/>• Ingestion Tracking & Checksum Status")]

    subgraph Retrieval["2. Runtime RAG Retrieval Pipeline (app/ai/retrieval/)"]
        AgentQuery["Agent Query via rag_tool.py<br/>'What is the late fee policy?'"] --> CacheCheck{"Redis RAG Cache<br/>(24h SHA256 Key)"}
        CacheCheck -- "Cache Hit (2.3 ms)" --> CachedResult["Return Cached Citations"]
        CacheCheck -- "Cache Miss" --> VectorSearch["QdrantVectorStore (vector_store.py)<br/>• Cosine similarity search (top_k=3)<br/>• Score threshold >= 0.45"]
        VectorDB -.-> VectorSearch
        VectorSearch --> PopulateCache["Write to Redis Cache"]
        PopulateCache --> FinalCitations["Assemble Policy Citations & Page Provenance<br/>[Handbook Section 4.2 | Page 12]"]
        CachedResult --> FinalCitations
    end
```

---

## 📁 Subpackage Inventory

### A. Ingestion Subsystem (`app/ai/ingestion`)
| File | Component | Description |
|---|---|---|
| [`pdf_parser.py`](./ingestion/pdf_parser.py) | `PDFParser` | Extracts raw text, detect headings (e.g., *Annexures*, *Policy Clauses*), and maps page provenance. |
| [`chunker.py`](./ingestion/chunker.py) | `SemanticChunker` | Splits extracted text into coherent semantic windows with clause preservation and boundary overlap. |
| [`embedder.py`](./ingestion/embedder.py) | `LocalEmbedder` | Generates 1536-dimensional dense vector embeddings using local sentence transformers with thread-safe singleton caching, LRU query caching (<0.01ms), and `torch.inference_mode()`. |

### B. Retrieval Subsystem (`app/ai/retrieval`)
| File | Component | Description |
|---|---|---|
| [`vector_store.py`](./retrieval/vector_store.py) | `QdrantVectorStore` | Manages collection creation, payload indexing, dense vector search, and similarity scoring against Qdrant. |

---

## 📊 Chunking & Ingestion Fidelity Benchmark

The ingestion pipeline is audited across 5 dimensions using `just audit-chunks`:
- **Text Coverage**: **100.0%** (all tokens preserved)
- **Metadata Accuracy**: **100.0%** (accurate page number provenance)
- **Boundary Quality**: **95.31%** (clauses remain unbroken across splits)
- **Text Integrity**: **100.0%** (zero unicode artifacts or malformed ligatures)
- **Table Integrity**: **100.0%** (key-value relationships retained)
