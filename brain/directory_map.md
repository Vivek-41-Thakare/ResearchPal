# Directory Map

> Full annotated file tree. See [brain.md](brain.md) for the master index.

```
Project_0/
├── .agents/                          # Empty (workspace customization root)
└── ResearchPaL/                      # Main project root
    ├── README.md                     # User-facing documentation with eval results
    ├── RAG Architecture Diagram.svg  # System architecture visual
    ├── System Design.svg             # Detailed system design diagram
    ├── *.png / *.webp                # UI screenshots for README
    │
    ├── brain/                        # ← AI knowledge base (this folder)
    │   ├── brain.md                  # Master index
    │   ├── architecture.md           # System topology + data flows
    │   ├── backend.md                # FastAPI + background tasks
    │   ├── agent.md                  # LangGraph 4-node pipeline
    │   ├── database.md               # Supabase schema + SQL functions
    │   ├── frontend.md               # React SPA + state + streaming
    │   ├── ingestion.md              # PDF parse → chunk → embed pipeline
    │   ├── search.md                 # Hybrid search + RRF + reranking
    │   ├── services.md               # All 4 backend services
    │   ├── api.md                    # HTTP endpoints reference
    │   ├── auth_security.md          # Key handling + CORS + risks
    │   ├── evals.md                  # Evaluation suite + metrics
    │   ├── dependencies.md           # Package manifest
    │   ├── directory_map.md          # This file
    │   └── conventions.md            # Coding patterns + fallbacks
    │
    ├── server_side/
    │   ├── backend/
    │   │   ├── main.py               # FastAPI app: routes, bg tasks, streaming (730 lines)
    │   │   ├── .env                  # Live credentials (gitignored)
    │   │   ├── .env.example          # Template with Adobe sample creds
    │   │   ├── requirements.txt      # Python dependencies (19 packages)
    │   │   ├── schema.sql            # Supabase table definitions + functions
    │   │   ├── graph/
    │   │   │   └── agent.py          # LangGraph StateGraph (318 lines)
    │   │   ├── services/
    │   │   │   ├── supabase_service.py  # DB ops + hybrid search + chat (239 lines)
    │   │   │   ├── embeddings_service.py # Multi-provider embeddings (62 lines)
    │   │   │   ├── parse_service.py      # PyMuPDF + Adobe parser (146 lines)
    │   │   │   └── pwc_service.py        # ArXiv API proxy (158 lines)
    │   │   └── test_*.py              # Ad-hoc backend test scripts (7 files)
    │   │
    │   └── frontend/
    │       ├── src/
    │       │   ├── App.jsx            # Entire React SPA (1363 lines)
    │       │   ├── App.css            # Component styles (874 lines)
    │       │   ├── index.css          # CSS variables + animations (141 lines)
    │       │   └── main.jsx           # ReactDOM entry (9 lines)
    │       ├── index.html             # Vite HTML shell
    │       ├── vite.config.js         # Vite React plugin
    │       ├── package.json           # npm deps (3 runtime, 4 dev)
    │       └── .oxlintrc.json         # Linter config
    │
    ├── evals/
    │   ├── compute_all_metrics.py    # Master eval script (296 lines)
    │   ├── generate_plots.py         # 8 eval plots
    │   ├── generate_all_eval_plots.py
    │   ├── generate_cp_cr_results_default.py
    │   ├── generate_cp_cr_results_advanced.py
    │   ├── generate_figure@1_hitrate_results.py
    │   ├── generate_table@1_hitrate_results.py
    │   ├── generate_question_vs_context_for_relevance_check.py
    │   ├── split_and_save_text.py
    │   ├── calculate_p50_latencies.py
    │   ├── data/                     # Ground truth Q&A per paper
    │   ├── results/                  # Computed metric JSONs
    │   └── plots/                    # Generated PNG charts (8 files)
    │
    └── artifacts/                    # Development docs + screenshots
        ├── *.md                      # Design docs, fix reports, implementation notes
        └── *.png / *.webp            # UI screenshots from development sessions
```

## Key File Sizes
| File | Lines | Role |
|------|-------|------|
| `App.jsx` | 1363 | Entire frontend |
| `main.py` | 730 | Backend entry + all routes |
| `App.css` | 874 | All component styles |
| `agent.py` | 318 | LangGraph pipeline |
| `compute_all_metrics.py` | 296 | Eval suite |
| `supabase_service.py` | 239 | DB operations |
| `pwc_service.py` | 158 | ArXiv proxy |
| `parse_service.py` | 146 | PDF parsing |
| `schema.sql` | 161 | DB schema |
| `index.css` | 141 | CSS variables |
| `embeddings_service.py` | 62 | Multi-provider embeddings |
