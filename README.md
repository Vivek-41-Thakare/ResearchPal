# 🔬 ResearchPal

### AI-Powered Multi-Source Research Assistant

> **ResearchPal** is an AI-powered research assistant designed to automate the process of searching, retrieving, parsing, ranking, and synthesizing information from research papers and web sources into structured, evidence-based answers.

---

## 🚀 Overview

ResearchPal helps researchers, students, and developers explore complex topics without manually searching through dozens of papers.

Instead of simply generating an answer from an LLM's internal knowledge, ResearchPal follows a **research-oriented pipeline**:

**Question → Search → Retrieval → Parsing → Ranking → Context Construction → AI Reasoning → Evidence-Based Answer**

The system combines **LLMs, information retrieval, embeddings, reranking, document parsing, and structured evaluation** to produce research-focused responses.

---

## ✨ Key Features

* 🔎 **Research-Oriented Search** — Retrieves relevant research papers and sources.
* 📄 **Document Parsing** — Extracts useful text, figures, and tables from research documents.
* 🧠 **Semantic Retrieval** — Uses embeddings to find contextually relevant information.
* 🎯 **Reranking** — Improves retrieval quality by prioritizing the most relevant chunks.
* 🤖 **LLM-Powered Reasoning** — Synthesizes retrieved evidence into coherent answers.
* 📚 **Evidence-Based Responses** — Answers are grounded in retrieved research content.
* 🖼️ **Figure & Table Retrieval** — Supports research content beyond plain text.
* 📊 **Retrieval Evaluation** — Includes metrics and evaluation pipelines for measuring retrieval performance.
* ⚡ **FastAPI Backend** — Provides APIs for the research pipeline.
* 💻 **Modern Web Frontend** — Interactive interface for submitting research questions.
* 🧪 **Testing Suite** — Includes backend, parser, retrieval, and end-to-end tests.

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────┐
                         │       User           │
                         │  Research Question   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   React Frontend     │
                         │      + Vite          │
                         └──────────┬───────────┘
                                    │
                              HTTP / REST API
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       FastAPI Backend        │
                    │                              │
                    │     ResearchPal Engine       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │   Research Agent     │
                         │   / Agent Graph      │
                         └──────────┬───────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
       ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
       │ Research / PWC │  │ Document Parser│  │  Embeddings    │
       │    Service     │  │    Service     │  │    Service     │
       └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │ Retrieval + Ranking  │
                         │       Pipeline       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Context Construction │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Gemini LLM       │
                         │ Reasoning & Synthesis│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Structured Research  │
                         │       Answer         │
                         └──────────────────────┘
```

---

# 🔄 Research Pipeline

ResearchPal follows a multi-stage research pipeline.

### 1️⃣ Query Understanding

The user submits a natural-language research question.

The system identifies the research intent and determines what information needs to be retrieved.

### 2️⃣ Research Discovery

Relevant papers and research sources are discovered using the configured research services.

### 3️⃣ Document Processing

Retrieved research documents are processed and converted into usable information.

The parser can work with:

* Text
* Figures
* Tables
* Document chunks
* Metadata

### 4️⃣ Semantic Chunking

Large documents are divided into smaller chunks so that relevant passages can be efficiently retrieved.

### 5️⃣ Embedding Generation

Document chunks are converted into vector representations using an embedding model.

This enables semantic similarity search rather than relying only on keyword matching.

### 6️⃣ Retrieval

The system retrieves the most relevant chunks for the user's question.

### 7️⃣ Reranking

Retrieved candidates can be reranked to improve the ordering of relevant evidence.

### 8️⃣ Context Construction

The highest-quality retrieved information is combined into a context package.

### 9️⃣ LLM Reasoning

The retrieved context is passed to the LLM.

The model synthesizes the evidence and generates a research-oriented response.

### 🔟 Final Answer

The user receives a structured answer based on the retrieved research context.

---

# 🧠 Core AI Components

## Large Language Model

ResearchPal uses an LLM for:

* Reasoning
* Context synthesis
* Answer generation
* Research question understanding

## Embeddings

Embeddings convert text into dense vector representations.

This allows the system to perform:

```text
User Query
     ↓
Query Embedding
     ↓
Vector Similarity
     ↓
Relevant Research Chunks
```

## Retrieval-Augmented Generation

ResearchPal follows an RAG-style architecture:

```text
Question
   ↓
Retrieve Evidence
   ↓
Relevant Context
   ↓
LLM
   ↓
Grounded Answer
```

This reduces dependence on the model's parametric knowledge and helps ground responses in retrieved research material.

---

# 📊 Evaluation Framework

ResearchPal includes an evaluation pipeline for measuring retrieval quality.

The repository contains evaluation scripts and generated results for different retrieval configurations.

### Evaluation areas include:

* Precision / Recall style measurements
* F1 score
* Mean Reciprocal Rank (MRR)
* Normalized Discounted Cumulative Gain (NDCG)
* Hit@K
* Figure retrieval hit rate
* Table retrieval hit rate
* Retrieval latency
* Reranker performance
* Context relevance

Example evaluation flow:

```text
Research Dataset
       │
       ▼
Query Generation
       │
       ▼
Retriever
       │
       ▼
Retrieved Candidates
       │
       ▼
Reranker
       │
       ▼
Top-K Results
       │
       ▼
Evaluation Metrics
       │
       ├── MRR
       ├── NDCG
       ├── Hit@K
       ├── F1
       └── Latency
```

Evaluation artifacts are available inside:

```text
evals/
├── data/
├── plots/
├── results/
└── *.py
```

---

# 🛠️ Tech Stack

### Backend

* Python
* FastAPI
* Pydantic
* LangGraph / Agent Graph Architecture
* REST APIs

### AI / ML

* Large Language Models
* Gemini API
* Embeddings
* Semantic Search
* Retrieval-Augmented Generation
* Reranking

### Data & Storage

* Supabase
* PostgreSQL
* Vector-based retrieval

### Document Processing

* PDF parsing
* Text extraction
* Figure extraction
* Table extraction
* Document chunking

### Frontend

* React
* Vite
* JavaScript
* CSS
* HTML

### Development & Testing

* Git
* GitHub
* Pytest
* End-to-End Testing
* Retrieval Evaluation

---

# 📁 Project Structure

```text
ResearchPal/
│
├── evals/
│   ├── data/
│   ├── plots/
│   ├── results/
│   ├── generate_all_eval_plots.py
│   ├── generate_cp_cr_results_advanced.py
│   ├── generate_cp_cr_results_default.py
│   ├── generate_figure@1_hitrate_results.py
│   ├── generate_plots.py
│   ├── generate_question_vs_context_for_relevance_check.py
│   ├── generate_table@1_hitrate_results.py
│   └── split_and_save_text.py
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
│       │   ├── assets/
│       │   ├── App.jsx
│       │   ├── App.css
│       │   ├── index.css
│       │   └── main.jsx
│       ├── package.json
│       └── vite.config.js
│
├── README.md
└── .gitignore
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Vivek-41-Thakare/ResearchPal.git
cd ResearchPal
```

---

# 🐍 Backend Setup

Navigate to the backend:

```bash
cd server_side/backend
```

Create a virtual environment:

### Windows

```bash
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file inside:

```text
server_side/backend/
```

Add your own API credentials.

Example:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

PDF_SERVICES_CLIENT_ID=your_client_id
PDF_SERVICES_CLIENT_SECRET=your_client_secret

FRONTEND_URL=http://localhost:5173

GEMINI_API_KEY=your_gemini_api_key

JINA_API_KEY=your_jina_api_key

GROQ_API_KEY=your_groq_api_key
```

> ⚠️ **Never commit `.env` or API keys to GitHub.**

Use `.env.example` as the configuration template.

---

# ▶️ Run Backend

From:

```text
server_side/backend
```

run:

```bash
python main.py
```

The backend runs locally on:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

---

# 💻 Frontend Setup

Open another terminal:

```bash
cd server_side/frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

---

# 🔗 Frontend → Backend Communication

The frontend communicates with the FastAPI backend through HTTP requests.

```text
React / Vite
     │
     │ HTTP
     ▼
localhost:8000
     │
     ▼
FastAPI
     │
     ▼
ResearchPal Agent
```

Make sure both servers are running simultaneously.

---

# 🧪 Testing

Backend test scripts are available in:

```text
server_side/backend/test_Scripts/
```

Examples include:

```text
test_e2e_backend.py
test_e2e_local.py
test_e2e_real_title.py
test_e2e_small.py
test_only_chat.py
test_parser.py
test_pwc.py
test_supabase.py
```

Run tests with:

```bash
pytest
```

---

# 📈 Performance & Evaluation

The `evals/` directory contains scripts and generated artifacts for evaluating the research retrieval pipeline.

The evaluation framework can be used to analyze:

* Retrieval accuracy
* Ranking quality
* Context relevance
* Figure retrieval
* Table retrieval
* Latency
* Reranker improvements

Generated plots are stored under:

```text
evals/plots/
```

Generated metrics are stored under:

```text
evals/results/
```

---

# 🖥️ Application Screenshots

## ResearchPal Interface

> Add your application screenshot here.

```text
docs/screenshots/researchpal-home.png
```

## Research Result

> Add your result screenshot here.

```text
docs/screenshots/researchpal-result.png
```

---

# 🎯 Example Research Query

Example:

```text
What are the major applications, benefits, limitations,
and future scope of Generative AI in healthcare?
```

ResearchPal processes the question through the retrieval and reasoning pipeline before generating the final response.

---

# 🔒 Security

API credentials are intentionally excluded from the repository.

Sensitive configuration should always be stored using environment variables:

```text
.env
```

Never hard-code credentials inside:

* Python files
* JavaScript files
* JSON files
* README files
* Git commits

---

# 🐛 Troubleshooting

### Backend is not reachable

Verify that FastAPI is running:

```bash
python main.py
```

Then check:

```text
http://localhost:8000/health
```

### Frontend cannot connect to backend

Make sure:

```text
Frontend → localhost:5173
Backend  → localhost:8000
```

are both running.

Also verify the API base URL configured in the frontend.

### API quota errors

If the LLM returns a quota or `RESOURCE_EXHAUSTED` error, check the API provider's quota and rate limits.

### Environment variable errors

Verify that `.env` exists inside:

```text
server_side/backend/
```

and contains the required credentials.

---

# 🧩 Design Principles

ResearchPal is designed around several engineering principles:

### Modularity

Services are separated by responsibility:

```text
Research
Parsing
Embeddings
Storage
Agent
API
Frontend
```

### Separation of Concerns

The frontend handles presentation and user interaction while the backend handles research orchestration and AI processing.

### Evidence-Driven Generation

The LLM receives retrieved research context rather than relying solely on its internal knowledge.

### Evaluability

The retrieval pipeline includes measurable evaluation metrics instead of treating answer quality as a purely subjective result.

---

# 🚧 Future Improvements

Potential improvements include:

* [ ] Multi-agent research planning
* [ ] Citation-aware answer generation
* [ ] Improved hybrid search
* [ ] Advanced reranking models
* [ ] Streaming responses
* [ ] Persistent research sessions
* [ ] User authentication
* [ ] Research history
* [ ] Export reports to PDF / Markdown
* [ ] Cloud deployment
* [ ] Automated evaluation pipelines
* [ ] Better figure and table understanding
* [ ] Multimodal research reasoning

---

# 🌐 Deployment

The project is currently designed to run locally.

A production deployment can be structured as:

```text
                   ┌───────────────┐
                   │   End User    │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │    Frontend   │
                   │ React + Vite  │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │    Backend    │
                   │    FastAPI    │
                   └───────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │   LLM   │   │Supabase │   │Research │
        │   API   │   │Database │   │Sources  │
        └─────────┘   └─────────┘   └─────────┘
```

---

# 👨‍💻 Author

### Vivek Thakare

B.Tech — Artificial Intelligence & Machine Learning

GitHub:
https://github.com/Vivek-41-Thakare

LinkedIn:
https://linkedin.com/in/vivekthakare

---

# ⭐ Support

If you find ResearchPal useful, consider giving the repository a ⭐ on GitHub.

---

## 📜 License

This project is intended for educational, research, and development purposes.

---

## 💡 Project Vision

> **Research should be about discovering insights—not spending hours searching for them.**

ResearchPal aims to make research exploration faster, more structured, and more accessible by combining modern information retrieval techniques with LLM-powered reasoning.
