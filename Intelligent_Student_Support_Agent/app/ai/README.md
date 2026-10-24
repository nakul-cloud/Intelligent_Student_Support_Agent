# 🧠 AI, Vector RAG & Document Ingestion (`app/ai`)

The **AI Layer** implements the end-to-end Retrieval-Augmented Generation (RAG) pipeline for university handbooks and institutional policy documents. It handles PDF document parsing, structure-preserving chunking, local dense vector embedding, and Qdrant vector database search.

---

## 🏗️ End-to-End RAG Ingestion & Retrieval Pipeline

```
[ University Student Handbook (PDF) ]
                 │
                 ▼
┌───────────────────────────────────────────────┐
│          1. PDF Text & Layout Parser          │  <-- app/ai/ingestion/pdf_parser.py
│  - Page-by-page extraction via PyPDF          │
│  - Structural heading detection & hierarchy   │
│  - Tabular rule & clause reconstruction       │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│        2. Dynamic Semantic Chunker            │  <-- app/ai/ingestion/chunker.py
│  - Target chunk size: ~1800 chars (450 tokens)│
│  - Overlap: 200 chars (clause continuity)     │
│  - Metadata: page, section, category tags     │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│        3. Local HuggingFace Embedder          │  <-- app/ai/ingestion/embedder.py
│  - Model: Orange/orange-nomic-v1.5-1536       │
│  - Produces 1536-dimensional dense vectors    │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│         4. Qdrant Vector Database             │  <-- app/ai/retrieval/vector_store.py
│  - Collection: "student_handbook"             │
│  - Distance: Cosine Similarity                │
│  - Payload: full text, page, section heading  │
└───────────────────────────────────────────────┘
                        ▲
                        │ (Runtime Query: search_student_handbook)
                        │
[ Conversational Agent Inquires: "What is the fee refund policy?" ]
```

---

## 📁 Subpackage Inventory

### A. Ingestion Subsystem (`app/ai/ingestion`)
| File | Component | Description |
|---|---|---|
| [`pdf_parser.py`](./ingestion/pdf_parser.py) | `PDFParser` | Extracts raw text, detect headings (e.g., *Annexures*, *Policy Clauses*), and maps page provenance. |
| [`chunker.py`](./ingestion/chunker.py) | `SemanticChunker` | Splits extracted text into coherent semantic windows with clause preservation and boundary overlap. |
| [`embedder.py`](./ingestion/embedder.py) | `Embedder` | Generates 1536-dimensional dense vector embeddings using local sentence transformers. |

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
