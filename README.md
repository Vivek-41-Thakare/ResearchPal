# 🔬 ResearchPal

### Next-Gen Academic RAG Assistant

ResearchPal is an AI-powered academic research assistant designed to make research paper discovery, analysis, and question answering faster, smarter, and more interactive.

It combines **Retrieval-Augmented Generation (RAG), semantic search, document processing, and AI agents** to help users interact with research papers and extract meaningful information from them.

---

## ✨ What Makes ResearchPal Special?

- 🔍 **Smart Paper Discovery**  
  Search and explore relevant academic research papers through an intuitive interface.

- 📄 **Research Document Analysis**  
  Process and analyze research papers and other academic documents.

- 🤖 **AI Research Assistant**  
  Ask questions directly about research content and receive context-aware answers.

- 🧠 **RAG-Powered Intelligence**  
  Uses Retrieval-Augmented Generation to ground AI responses in relevant research content.

- 🔎 **Semantic Search**  
  Find information based on meaning and context rather than simple keyword matching.

- 📊 **Tables & Figures Retrieval**  
  Retrieve relevant tables and figures from research documents.

- ⚡ **Interactive Experience**  
  Provides a smooth interface for discovering papers and interacting with research content.

- 📈 **Retrieval Evaluation**  
  Includes evaluation pipelines for measuring retrieval quality and system performance.

---

## 🛠️ Built With

**Python • FastAPI • React • Supabase • Google Gemini • RAG • Semantic Search**

---

## 🏗️ Project Structure

```text
ResearchPal/
│
├── evals/
│   ├── data/
│   ├── plots/
│   ├── results/
│   └── evaluation scripts
│
├── server_side/
│   │
│   ├── backend/
│   │   ├── graph/
│   │   │   └── agent.py
│   │   │
│   │   ├── services/
│   │   │   ├── embeddings_service.py
│   │   │   ├── parse_service.py
│   │   │   ├── pwc_service.py
│   │   │   └── supabase_service.py
│   │   │
│   │   ├── test_Scripts/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── schema.sql
│   │
│   └── frontend/
│       ├── public/
│       ├── src/
│       ├── index.html
│       ├── package.json
│       └── vite.config.js
│
└── README.md
