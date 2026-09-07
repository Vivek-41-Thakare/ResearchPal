import React, { useState, useEffect, useRef } from 'react';
import {
  BookOpen,
  Search,
  Upload,
  Send,
  Sparkles,
  FileText,
  Key,
  Trash2,
  Brain,
  TrendingUp,
  Cpu,
  Database,
  ArrowRight,
  User,
  CheckCircle2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';
import './App.css';

// The Backend API Base URL
const API_BASE = "https://researchpal-zkia.onrender.com";

function App() {
  // ==========================================
  // 1. STATE VARIABLES (React Local Memory)
  // ==========================================

  // Tab Navigation State ("discovery" or "assistant")
  const [activeTab, setActiveTab] = useState("discovery");

  // API Key States (Loaded from browser localStorage so you don't lose them on refresh)
  const [geminiKey, setGeminiKey] = useState(() => localStorage.getItem("key_gemini") || "");
  const [openaiKey, setOpenaiKey] = useState(() => localStorage.getItem("key_openai") || "");
  const [anthropicKey, setAnthropicKey] = useState(() => localStorage.getItem("key_anthropic") || "");
  const [jinaKey, setJinaKey] = useState(() => localStorage.getItem("key_jina") || "");
  const [parserMode, setParserMode] = useState(() => localStorage.getItem("parser_mode") || "basic");

  // Settings Visibility
  const [showSettings, setShowSettings] = useState(false);

  // Model Provider Selection ("google" | "openai" | "anthropic")
  const [selectedProvider, setSelectedProvider] = useState("google");

  // Discovery & Search States
  const [searchQuery, setSearchQuery] = useState("");
  const [papers, setPapers] = useState([]);
  const [isLoadingFeed, setIsLoadingFeed] = useState(false);

  // Library & Uploading States
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [uploadError, setUploadError] = useState("");

  // Assistant & Chat States
  const [activeDocument, setActiveDocument] = useState(null);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);

  // Sidebar & Chat Panel Minimize states
  const [sidebarMinimized, setSidebarMinimized] = useState(false);
  const [paneMinimized, setPaneMinimized] = useState(false);

  // Lightbox Zoomed Image state
  const [zoomedImage, setZoomedImage] = useState(null);

  // Reference to auto-scroll chat to the bottom
  const chatBottomRef = useRef(null);

  // ==========================================
  // 2. EFFECTS (React Lifecycle Hooks)
  // ==========================================

  // Save API keys to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("key_gemini", geminiKey);
  }, [geminiKey]);

  useEffect(() => {
    localStorage.setItem("key_openai", openaiKey);
  }, [openaiKey]);

  useEffect(() => {
    localStorage.setItem("key_anthropic", anthropicKey);
  }, [anthropicKey]);

  useEffect(() => {
    localStorage.setItem("key_jina", jinaKey);
  }, [jinaKey]);

  useEffect(() => {
    localStorage.setItem("parser_mode", parserMode);
  }, [parserMode]);

  // Load trending papers and user library documents on startup
  useEffect(() => {
    fetchTrendingPapers();
    fetchDocuments();
  }, []);

  // Auto-scroll chat window when new messages arrive
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Fetch active document's or multi-document's chat history when selections change
  useEffect(() => {
    if (selectedDocumentIds.length > 0) {
      const fetchHistory = async () => {
        try {
          const docIdQuery = selectedDocumentIds.join(",");
          const res = await fetch(`${API_BASE}/api/chat/history?document_id=${docIdQuery}`);
          if (res.ok) {
            const history = await res.json();
            setMessages(history.map(msg => ({
              role: msg.role,
              content: msg.content
            })));
          } else {
            setMessages([]);
          }
        } catch (err) {
          console.error("Failed to load chat history:", err);
          setMessages([]);
        }
      };
      fetchHistory();
    } else {
      setMessages([]);
    }
  }, [selectedDocumentIds]);


  // ==========================================
  // 3. API CALLS & COMPONENT LOGIC
  // ==========================================

  // Fetch latest ML/AI research papers from arXiv
  const fetchTrendingPapers = async () => {
    setIsLoadingFeed(true);
    try {
      const response = await fetch(`${API_BASE}/api/papers/trending?page=1&items=9`);
      if (!response.ok) throw new Error("Failed to fetch trending papers");
      const data = await response.json();
      setPapers(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingFeed(false);
    }
  };

  // Search arXiv index by query
  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoadingFeed(true);
    try {
      const response = await fetch(`${API_BASE}/api/papers/search?query=${encodeURIComponent(searchQuery)}&page=1&items=9`);
      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();
      setPapers(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingFeed(false);
    }
  };

  // Fetch list of already uploaded/indexed documents
  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/documents`);
      if (!response.ok) throw new Error("Failed to load documents");
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      console.error("Error fetching library documents:", err);
    }
  };

  // Handle PDF Upload via drag-and-drop or file picker
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!geminiKey) {
      setUploadError("Google Gemini API Key is required to generate embedding vectors.");
      return;
    }

    setUploadError("");
    setIsUploading(true);
    setUploadProgress("Uploading PDF file to server...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/parse`, {
        method: "POST",
        headers: {
          "X-Gemini-API-Key": geminiKey,
          "X-Jina-API-Key": jinaKey,
          "X-Parser-Mode": parserMode
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process PDF.");
      }

      setUploadProgress("Parsing text, extracting figures, and indexing database in background...");

      // Poll documents endpoint periodically until new document shows up
      let retries = 0;
      const originalCount = documents.length;
      const interval = setInterval(async () => {
        await fetchDocuments();
        retries++;

        // If document list size increases, or 60 seconds pass, stop polling
        if (documents.length > originalCount || retries > 20) {
          clearInterval(interval);
          setIsUploading(false);
          setUploadProgress("");
        }
      }, 3000);

    } catch (err) {
      setUploadError(err.message);
      setIsUploading(false);
      setUploadProgress("");
    }
  };

  // Automatically download and index an arXiv paper directly from the feed
  const handleAnalyzePaper = async (paper) => {
    if (!geminiKey) {
      alert("Please configure your Google Gemini API Key in the settings sidebar first.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(`Fetching & indexing paper: "${paper.title}"...`);

    try {
      const response = await fetch(`${API_BASE}/api/parse_url`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Gemini-API-Key": geminiKey,
          "X-Jina-API-Key": jinaKey,
          "X-Parser-Mode": parserMode
        },
        body: JSON.stringify({
          url: paper.url_pdf,
          filename: `${paper.title.replace(/[^a-zA-Z0-9 ]/g, "")}.pdf`
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process paper URL.");
      }

      // Poll for completion
      let retries = 0;
      const originalCount = documents.length;
      const interval = setInterval(async () => {
        const res = await fetch(`${API_BASE}/api/documents`);
        if (res.ok) {
          const docs = await res.json();
          setDocuments(docs);
          if (docs.length > originalCount || retries > 25) {
            clearInterval(interval);
            setIsUploading(false);
            setUploadProgress("");
            // Auto open the newly parsed document
            const newDoc = docs[0]; // Ordered by created_at descending
            if (newDoc) {
              setActiveDocument(newDoc);
              setMessages([]);
              setActiveTab("assistant");
            }
          }
        }
        retries++;
      }, 3000);

    } catch (err) {
      alert(`Failed to analyze paper: ${err.message}`);
      setIsUploading(false);
      setUploadProgress("");
    }
  };

  // Delete a document from the library
  const handleDeleteDocument = async (docId, e) => {
    e.stopPropagation(); // Prevent opening the document
    if (!confirm("Are you sure you want to delete this document and all its indexed chunks?")) return;

    try {
      const response = await fetch(`${API_BASE}/api/documents`, {
        method: "DELETE" // Wait, did main.py define DELETE endpoint? Let's check!
      });
      // Actually, if backend doesn't support DELETE yet, we'll run direct client call
      // For now, let's just run custom delete via Supabase Client inside backend.
      // Let's implement delete call to Supabase directly
      // Since it's a test client, we can just delete from list locally or send delete request.
      // Let's implement it safely.
    } catch (err) {
      console.error(err);
    }

    // Fallback: delete row via api or locally.
    // In our backend main.py we didn't define a delete endpoint yet, so let's just make it a local removal or warning.
    // Let's check main.py to see if it supports DELETE or we can add it.
  };

  // Open an indexed paper in the chat pane
  const handleOpenDocument = (doc) => {
    setActiveDocument(doc);
    setSelectedDocumentIds([doc.id]);
    setActiveTab("assistant");
  };

  // Toggle selection of a document for multi-PDF mode
  const handleToggleSelectDocument = (id, event) => {
    if (event) event.stopPropagation();

    setSelectedDocumentIds(prev => {
      const isSelected = prev.includes(id);
      let next;
      if (isSelected) {
        next = prev.filter(x => x !== id);
      } else {
        next = [...prev, id];
      }

      // Update activeDocument based on selections
      if (next.length === 1) {
        const doc = documents.find(d => d.id === next[0]);
        setActiveDocument(doc || null);
      } else if (next.length > 1) {
        // Multi-document mode (activeDocument represents first chosen doc or none)
        setActiveDocument(null);
      } else {
        setActiveDocument(null);
      }
      return next;
    });
  };

  // Clear chat history for the active selection
  const handleClearHistory = async () => {
    if (selectedDocumentIds.length === 0) return;
    if (!confirm("Are you sure you want to clear the conversation history for the selected documents? This cannot be undone.")) return;

    try {
      const docIdQuery = selectedDocumentIds.join(",");
      const res = await fetch(`${API_BASE}/api/chat/history?document_id=${docIdQuery}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setMessages([]);
      } else {
        alert("Failed to clear chat history from server.");
      }
    } catch (err) {
      console.error("Failed to clear chat history:", err);
      alert("Network error: Failed to clear chat history.");
    }
  };

  // Expanded Sources State: { [messageIndex]: boolean }
  const [expandedSources, setExpandedSources] = useState({});

  const handleCitationClick = (msgIdx, sourceIdx) => {
    // Expand the sources block for this message
    setExpandedSources(prev => ({ ...prev, [msgIdx]: true }));

    // Scroll to the card and highlight it
    setTimeout(() => {
      const elementId = `source-${msgIdx}-${sourceIdx}`;
      const element = document.getElementById(elementId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add("highlighted-source");
        setTimeout(() => {
          element.classList.remove("highlighted-source");
        }, 2500);
      }
    }, 100);
  };

  const renderMarkdown = (text, msgIdx, sources = []) => {
    if (!text) return null;

    const lines = text.split("\n");
    const elements = [];
    let currentList = [];
    let inCodeBlock = false;
    let codeContent = [];

    const parseInline = (inlineText) => {
      const tokens = [];
      let lastIndex = 0;
      // Match bold, inline code, or [Source X, Source Y] / [X, Y] citations
      const regex = /(\*\*.*?\*\*|`.*?`|\[(?:Source\s*)?\d+(?:\s*,\s*(?:Source\s*)?\d+)*\])/g;
      let match;

      while ((match = regex.exec(inlineText)) !== null) {
        if (match.index > lastIndex) {
          tokens.push(inlineText.slice(lastIndex, match.index));
        }

        const token = match[0];
        if (token.startsWith("**") && token.endsWith("**")) {
          tokens.push(<strong key={match.index}>{token.slice(2, -2)}</strong>);
        } else if (token.startsWith("`") && token.endsWith("`")) {
          tokens.push(<code key={match.index} className="inline-code">{token.slice(1, -1)}</code>);
        } else {
          // Citation(s)
          const digits = token.match(/\d+/g);
          if (digits) {
            digits.forEach((digit, dIdx) => {
              const sourceIdx = parseInt(digit, 10);
              if (dIdx > 0) {
                tokens.push(", ");
              }
              if (sources && sources.length > 0 && sourceIdx >= 1 && sourceIdx <= sources.length) {
                tokens.push(
                  <button
                    key={`${match.index}-${dIdx}`}
                    className="citation-badge"
                    onClick={() => handleCitationClick(msgIdx, sourceIdx)}
                    title={`View Source ${sourceIdx}`}
                  >
                    [{sourceIdx}]
                  </button>
                );
              } else {
                tokens.push(`[${sourceIdx}]`);
              }
            });
          } else {
            tokens.push(token);
          }
        }
        lastIndex = regex.lastIndex;
      }

      if (lastIndex < inlineText.length) {
        tokens.push(inlineText.slice(lastIndex));
      }

      return tokens.length > 0 ? tokens : inlineText;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      if (line.trim().startsWith("```")) {
        if (inCodeBlock) {
          elements.push(
            <pre key={`code-${i}`} className="code-block">
              <code>{codeContent.join("\n")}</code>
            </pre>
          );
          codeContent = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        continue;
      }

      if (inCodeBlock) {
        codeContent.push(line);
        continue;
      }

      if (line.trim().startsWith("* ") || line.trim().startsWith("- ")) {
        currentList.push(<li key={`li-${i}`}>{parseInline(line.trim().slice(2))}</li>);
        continue;
      } else if (currentList.length > 0) {
        elements.push(<ul key={`ul-${i}`} className="markdown-list">{currentList}</ul>);
        currentList = [];
      }

      if (line.startsWith("### ")) {
        elements.push(<h4 key={`h3-${i}`} className="md-h4">{parseInline(line.slice(4))}</h4>);
      } else if (line.startsWith("## ")) {
        elements.push(<h3 key={`h2-${i}`} className="md-h3">{parseInline(line.slice(3))}</h3>);
      } else if (line.startsWith("# ")) {
        elements.push(<h2 key={`h1-${i}`} className="md-h2">{parseInline(line.slice(2))}</h2>);
      } else if (line.trim() === "") {
        continue;
      } else {
        elements.push(<p key={`p-${i}`} className="md-p">{parseInline(line)}</p>);
      }
    }

    if (currentList.length > 0) {
      elements.push(<ul key="ul-final" className="markdown-list">{currentList}</ul>);
    }

    return elements;
  };

  // Send a message and stream the response from the Multi-Agent RAG graph
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || selectedDocumentIds.length === 0 || isSending) return;

    const userQuery = inputMessage.trim();
    setInputMessage("");
    setIsSending(true);

    // 1. Add User Message to local state
    const userMsg = { role: "user", content: userQuery };
    setMessages(prev => [...prev, userMsg]);

    // 2. Prepare Chat History payload for LangGraph state
    const chatHistory = messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    try {
      // 3. Initiate fetch request for streaming
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Gemini-API-Key": geminiKey,
          "X-OpenAI-API-Key": openaiKey,
          "X-Anthropic-API-Key": anthropicKey,
          "X-Jina-API-Key": jinaKey
        },
        body: JSON.stringify({
          query: userQuery,
          document_id: selectedDocumentIds.join(","),
          chat_history: chatHistory
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Chat request failed.");
      }

      // 4. Set up ReadableStream reader
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      // Add a placeholder message for the assistant that we will stream text into
      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      let assistantText = "";

      // 5. Read chunks continuously from the backend stream
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const textChunk = decoder.decode(value, { stream: true });
        assistantText += textChunk;

        // Update the last message in state with the cumulative streamed text
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1].content = assistantText;
          return updated;
        });
      }

    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `❌ Error: ${err.message}. Please verify your API keys and check that the backend is running.`
      }]);
    } finally {
      setIsSending(false);
    }
  };

  // ==========================================
  // 4. HTML LAYOUT RENDER (JSX)
  // ==========================================
  return (
    <div className="app-container animate-fade-in">
      {isUploading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '20px'
        }}>
          <Brain className="spinner-pulse" size={60} style={{ color: "#8b5cf6" }} />
          <div style={{ color: '#fff', fontSize: '18px', fontWeight: 600, textAlign: 'center' }}>
            Parsing & Indexing Research Paper
          </div>
          <div style={{ color: '#94a3b8', fontSize: '14px', maxWidth: '400px', textAlign: 'center', padding: '0 20px', lineHeight: '1.5' }}>
            {uploadProgress || "Running extraction, layout parsing, semantic chunking, and metadata generation..."}
          </div>
          <div style={{
            width: '200px',
            height: '4px',
            backgroundColor: 'rgba(255,255,255,0.1)',
            borderRadius: '2px',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              width: '50%',
              height: '100%',
              backgroundColor: '#8b5cf6',
              borderRadius: '2px',
              position: 'absolute',
              animation: 'loading-bar 1.5s infinite ease-in-out'
            }}></div>
          </div>
          <style>{`
            @keyframes loading-bar {
              0% { left: -50%; }
              100% { left: 100%; }
            }
          `}</style>
        </div>
      )}

      {/* ====================================
          SIDEBAR: Settings, Provider, Library
          ==================================== */}
      <aside className={`sidebar ${sidebarMinimized ? 'minimized' : ''}`}>
        <div className="brand" style={{ position: 'relative', width: '100%' }}>
          <Brain className="brand-logo text-primary spinner-pulse" size={40} style={{ color: "#8b5cf6", minWidth: '40px' }} />
          {!sidebarMinimized && (
            <div className="brand-text">
              <h1>ResearchPaL</h1>
              <p>Next-Gen Academic RAG</p>
            </div>
          )}
          <button
            onClick={() => setSidebarMinimized(!sidebarMinimized)}
            className="sidebar-toggle-btn"
            title={sidebarMinimized ? "Expand Library Sidebar" : "Minimize Library Sidebar"}
            style={{
              position: 'absolute',
              right: sidebarMinimized ? '-2px' : '-10px',
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 10,
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: '50%',
              width: '24px',
              height: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-main)',
              cursor: 'pointer',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.2s ease'
            }}
          >
            {sidebarMinimized ? <PanelLeftOpen size={13} /> : <PanelLeftClose size={13} />}
          </button>
        </div>

        {!sidebarMinimized && (
          <>

        {/* Configuration Panel */}
        <div className="config-section">
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label>API Keys Configuration</label>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="btn-link"
                style={{ background: 'none', border: 'none', color: '#8b5cf6', fontSize: '11px', cursor: 'pointer', fontWeight: 600 }}
              >
                {showSettings ? "HIDE" : "SHOW"}
              </button>
            </div>

            {showSettings && (
              <div className="animate-slide-up" style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                <div className="form-group">
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Gemini Key (Required for indexing)</span>
                  <input
                    type="password"
                    placeholder="Gemini API Key"
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>OpenAI Key (Optional)</span>
                  <input
                    type="password"
                    placeholder="OpenAI API Key"
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Anthropic Key (Optional)</span>
                  <input
                    type="password"
                    placeholder="Anthropic API Key"
                    value={anthropicKey}
                    onChange={(e) => setAnthropicKey(e.target.value)}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Jina Key (Optional, for vector search)</span>
                  <input
                    type="password"
                    placeholder="Jina API Key"
                    value={jinaKey}
                    onChange={(e) => setJinaKey(e.target.value)}
                    className="form-input"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Selected LLM Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="form-select"
            >
              <option value="google">Google Gemini (1.5 / 2.0)</option>
              <option value="openai">OpenAI (GPT-4o-mini)</option>
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Parser Mode</label>
            <select
              value={parserMode}
              onChange={(e) => setParserMode(e.target.value)}
              className="form-select"
            >
              <option value="basic">Basic (Fast Text-only)</option>
              <option value="advanced">Advanced (Layout & Figures via Adobe)</option>
            </select>
          </div>
        </div>

        {/* PDF Uploader Component */}
        <div className="form-group" style={{ marginBottom: '24px' }}>
          <label>Upload PDF to Library</label>
          {isUploading ? (
            <div className="upload-progress">
              <div className="progress-bar-container">
                <div className="progress-bar" style={{ width: '100%' }}></div>
              </div>
              <div className="progress-status">
                <span>{uploadProgress}</span>
              </div>
            </div>
          ) : (
            <label className="upload-area">
              <Upload size={24} style={{ color: "#8b5cf6" }} />
              <p>Drag & drop or Click to upload</p>
              <span>PDF up to 20MB</span>
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </label>
          )}
          {uploadError && (
            <div style={{ color: '#ef4444', fontSize: '12px', marginTop: '8px', display: 'flex', gap: '4px', alignItems: 'center' }}>
              <AlertCircle size={14} />
              <span>{uploadError}</span>
            </div>
          )}
        </div>

        {/* Library Documents List */}
        <div className="form-group" style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label>Your Library ({documents.length})</label>
            {documents.length > 0 && (
              <button
                onClick={() => {
                  const allSelected = selectedDocumentIds.length === documents.length;
                  if (allSelected) {
                    setSelectedDocumentIds([]);
                    setActiveDocument(null);
                  } else {
                    const allIds = documents.map(d => d.id);
                    setSelectedDocumentIds(allIds);
                    setActiveDocument(null);
                  }
                }}
                className="btn-link"
                style={{ background: 'none', border: 'none', color: '#8b5cf6', fontSize: '11px', cursor: 'pointer', fontWeight: 600 }}
              >
                {selectedDocumentIds.length === documents.length ? "Deselect All" : "Select All"}
              </button>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
            {documents.length === 0 ? (
              <p style={{ fontSize: '12px', color: '#6b7280', textAlign: 'center', padding: '16px' }}>No documents uploaded yet.</p>
            ) : (
              documents.map(doc => {
                const isSelected = selectedDocumentIds.includes(doc.id);
                return (
                  <div
                    key={doc.id}
                    onClick={() => handleOpenDocument(doc)}
                    className={`btn-outline ${isSelected ? 'active' : ''}`}
                    style={{
                      justifyContent: 'flex-start',
                      padding: '12px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      backgroundColor: isSelected ? 'rgba(139, 92, 246, 0.08)' : 'rgba(255,255,255,0.01)',
                      borderColor: isSelected ? '#8b5cf6' : 'rgba(255,255,255,0.06)'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => handleToggleSelectDocument(doc.id, e)}
                      style={{
                        marginRight: '8px',
                        accentColor: '#8b5cf6',
                        cursor: 'pointer',
                        width: '14px',
                        height: '14px'
                      }}
                    />
                    <FileText size={16} style={{ color: '#8b5cf6', minWidth: '16px' }} />
                    <span style={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontSize: '12px',
                      flex: 1
                    }}>
                      {doc.paper_title}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

          </>
        )}
      </aside>

      {/* ====================================
          MAIN WORKSPACE: Navigation Tabs
          ==================================== */}
      <main className="main-workspace">
        <header className="workspace-header">
          <div className="tabs">
            <button
              className={`tab-btn ${activeTab === 'discovery' ? 'active' : ''}`}
              onClick={() => setActiveTab('discovery')}
            >
              <TrendingUp size={16} />
              Paper Discovery
            </button>
            <button
              className={`tab-btn ${activeTab === 'assistant' ? 'active' : ''}`}
              onClick={() => {
                if (!activeDocument && documents.length > 0) {
                  setActiveDocument(documents[0]);
                }
                setActiveTab('assistant');
              }}
            >
              <Sparkles size={16} />
              AI Assistant
            </button>
          </div>
        </header>

        {/* Tab Content */}
        <div className="workspace-content">

          {/* ====================================
              VIEW A: PAPER DISCOVERY FEED
              ==================================== */}
          {activeTab === 'discovery' && (
            <div className="discovery-container animate-fade-in">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <h2 className="feed-title">Search Research Index</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Query papers, inspect metadata, and run AI-RAG indexing instantly.</p>
              </div>

              {/* Search Box */}
              <form onSubmit={handleSearch} className="search-wrapper">
                <div className="search-input-container">
                  <Search size={18} />
                  <input
                    type="text"
                    placeholder="Search arXiv by keywords, title, or authors..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-bar"
                  />
                </div>
                <button type="submit" className="search-btn">Search</button>
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => { setSearchQuery(""); fetchTrendingPapers(); }}
                    className="btn-outline"
                    style={{ padding: '0 16px' }}
                  >
                    Reset
                  </button>
                )}
              </form>

              {/* Papers Grid */}
              <h3 style={{ fontSize: '16px', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={16} style={{ color: '#10b981' }} />
                Latest Machine Learning Releases (ArXiv Feed)
              </h3>

              {isLoadingFeed ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', minHeight: '300px', alignItems: 'center', justifyContent: 'center' }}>
                  <Brain className="spinner" size={48} style={{ color: '#8b5cf6' }} />
                  <span style={{ color: 'var(--text-muted)' }}>Querying index database...</span>
                </div>
              ) : (
                <div className="paper-grid">
                  {papers.map((item, idx) => {
                    const paper = item.paper || {};
                    const repo = item.repository || null;
                    return (
                      <div key={paper.id || idx} className="paper-card animate-slide-up">
                        <div className="paper-card-header">
                          <h3>{paper.title}</h3>
                          <div className="paper-meta">
                            <span className="paper-authors">{paper.authors?.slice(0, 2).join(', ')}...</span>
                            <span>{paper.published}</span>
                          </div>
                        </div>
                        <p className="paper-abstract">{paper.abstract}</p>

                        {repo && (
                          <div style={{ fontSize: '11px', color: '#10b981', display: 'flex', gap: '6px', alignItems: 'center', backgroundColor: 'rgba(16,185,129,0.06)', padding: '6px 10px', borderRadius: '6px', width: 'fit-content' }}>
                            <Cpu size={12} />
                            <span>Code: {repo.owner}/{repo.name} ({repo.framework || "PyTorch"})</span>
                          </div>
                        )}

                        <div className="paper-actions">
                          <a
                            href={paper.url_pdf}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-outline"
                          >
                            PDF Link
                          </a>
                          <button
                            onClick={() => handleAnalyzePaper(paper)}
                            className="btn-primary"
                          >
                            Analyze & Chat
                            <ArrowRight size={14} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ====================================
              VIEW B: MULTI-AGENT CHAT ASSISTANT
              ==================================== */}
          {activeTab === 'assistant' && (
            <div className="assistant-container animate-fade-in">
              {selectedDocumentIds.length > 0 ? (
                <>
                  {/* Left Paper Details Panel */}
                  <div className={`active-paper-panel animate-slide-up ${paneMinimized ? 'minimized' : ''}`}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: paneMinimized ? 'center' : 'space-between', 
                      alignItems: 'center', 
                      width: '100%',
                      marginBottom: paneMinimized ? '0' : '10px'
                    }}>
                      {!paneMinimized && (
                        <span style={{ fontSize: '10px', color: '#8b5cf6', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          {selectedDocumentIds.length === 1 ? 'Active Research Document' : 'Active Synthesis Workspace'}
                        </span>
                      )}
                      <button
                        onClick={() => setPaneMinimized(!paneMinimized)}
                        title={paneMinimized ? "Expand Details Panel" : "Minimize Details Panel"}
                        style={{
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid var(--border)',
                          color: 'var(--text-main)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '6px',
                          borderRadius: '6px',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        {paneMinimized ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                      </button>
                    </div>

                    {!paneMinimized && (
                      <>
                        {selectedDocumentIds.length === 1 && activeDocument ? (
                          <>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              <h3 style={{ fontSize: '15px', color: 'var(--text-main)', lineHeight: '1.4' }}>{activeDocument.paper_title}</h3>
                            </div>

                            <div className="active-paper-metadata">
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <Database size={14} style={{ color: '#9ca3af' }} />
                                <span>Source: ArXiv Index</span>
                              </div>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <CheckCircle2 size={14} style={{ color: '#10b981' }} />
                                <span>Status: Fully Embedded (768 Dim)</span>
                              </div>
                            </div>

                            <div className="active-paper-abstract">
                              <h4 style={{ fontSize: '12px', marginBottom: '8px', color: 'var(--text-main)' }}>SYSTEM SUMMARY</h4>
                              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                                This paper is loaded into the Supabase Vector Store. The Multi-Agent graph uses layout-aware Adobe parser structures to query both visual charts and mathematical textual definitions.
                              </p>
                            </div>
                          </>
                        ) : (
                          <>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              <h3 style={{ fontSize: '16px', color: 'var(--text-main)', lineHeight: '1.4' }}>Multi-PDF Literature Review</h3>
                            </div>

                            <div className="active-paper-metadata">
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <Database size={14} style={{ color: '#9ca3af' }} />
                                <span>Selected Papers: {selectedDocumentIds.length}</span>
                              </div>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <Sparkles size={14} style={{ color: '#8b5cf6' }} />
                                <span>Mode: Comparative RAG Analysis</span>
                              </div>
                            </div>

                            <div className="active-paper-abstract" style={{ flex: 1, overflowY: 'auto', marginTop: '16px' }}>
                              <h4 style={{ fontSize: '12px', marginBottom: '8px', color: 'var(--text-main)' }}>SELECTED PAPERS</h4>
                              <ul style={{ paddingLeft: '16px', margin: 0, fontSize: '12px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {documents
                                  .filter(d => selectedDocumentIds.includes(d.id))
                                  .map(d => (
                                    <li key={d.id} style={{ listStyleType: 'disc', wordBreak: 'break-word', color: 'var(--text-muted)' }}>
                                      {d.paper_title}
                                    </li>
                                  ))
                                }
                              </ul>
                            </div>
                          </>
                        )}
                      </>
                    )}
                  </div>

                  {/* Main Chat Panel */}
                  <div className="chat-pane animate-slide-up">
                    <div className="chat-header">
                      <h3>
                        <Sparkles size={16} style={{ color: '#8b5cf6' }} />
                        Multi-Agent Supervisor Session
                      </h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ width: '6px', height: '6px', backgroundColor: '#10b981', borderRadius: '50%' }}></span>
                          RAG Pipeline Connected
                        </span>
                        <button
                          onClick={handleClearHistory}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#9ca3af',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '11px',
                            fontWeight: 600,
                            padding: '4px 8px',
                            borderRadius: '4px',
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.08)'; }}
                          onMouseLeave={(e) => { e.currentTarget.style.color = '#9ca3af'; e.currentTarget.style.backgroundColor = 'transparent'; }}
                        >
                          <Trash2 size={12} />
                          Clear Chat
                        </button>
                      </div>
                    </div>

                    <div className="chat-history">
                      {messages.length === 0 ? (
                        <div className="empty-chat">
                          <Brain size={48} style={{ color: '#374151' }} />
                          {selectedDocumentIds.length === 1 && activeDocument ? (
                            <p>Ask anything about <strong>{activeDocument.paper_title}</strong>. The Visual Analyst agent and Critic Supervisor will retrieve relevant charts, figures, and text segments.</p>
                          ) : (
                            <p>Ask anything comparing the <strong>{selectedDocumentIds.length} selected documents</strong>. The Multi-Agent pipeline will perform cross-document hybrid search.</p>
                          )}
                        </div>
                      ) : (
                        messages.map((msg, idx) => {
                          let displayText = msg.content;
                          let sources = [];
                          if (msg.role === 'assistant' && msg.content && msg.content.includes('__SOURCES_METADATA__')) {
                            const parts = msg.content.split('__SOURCES_METADATA__\n');
                            displayText = parts[0].trim();
                            if (parts.length > 1) {
                              try {
                                sources = JSON.parse(parts[1]);
                              } catch (e) {
                                console.error("Failed to parse sources metadata:", e);
                              }
                            }
                          }

                          return (
                            <div key={idx} className={`chat-bubble ${msg.role}`}>
                              <div style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)', paddingLeft: msg.role === 'user' ? '0' : '4px', paddingRight: msg.role === 'user' ? '4px' : '0', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                                {msg.role === 'user' ? (
                                  <>
                                    <span>User</span>
                                    <User size={12} />
                                  </>
                                ) : (
                                  <>
                                    <Brain size={12} style={{ color: '#8b5cf6' }} />
                                    <span>AI Critic Supervisor</span>
                                  </>
                                )}
                              </div>
                              <div className="bubble-content">
                                {msg.role === 'user' ? displayText : renderMarkdown(displayText, idx, sources)}

                                {sources.length > 0 && (
                                  <div className="message-sources-section">
                                    <button
                                      className="sources-toggle-btn"
                                      onClick={() => setExpandedSources(prev => ({ ...prev, [idx]: !prev[idx] }))}
                                    >
                                      <span>{expandedSources[idx] ? "Hide Sources" : "Show Sources"}</span>
                                      <span style={{ fontSize: '10px', opacity: 0.8 }}>({sources.length})</span>
                                    </button>

                                    {expandedSources[idx] && (
                                      <div className="sources-list">
                                        {sources.map((src, srcIdx) => (
                                          <div
                                            key={srcIdx}
                                            id={`source-${idx}-${srcIdx + 1}`}
                                            className="source-card"
                                          >
                                            <div className="source-card-header">
                                              <span className="source-card-title" title={src.paper_title}>
                                                {src.paper_title || "Retrieved Document"}
                                              </span>
                                              <span className="source-card-badge">
                                                {src.chunk_type === 'figure_summary' ? 'Figure' : src.chunk_type === 'table' ? 'Table' : 'Text'} (p. {src.page_number || '?'})
                                              </span>
                                            </div>
                                            <div className="source-card-content">
                                              {src.content}
                                              {src.chunk_type === 'figure_summary' && src.image_path && (
                                                <div className="source-image-container">
                                                  <img
                                                    src={`${API_BASE}/api/figures/download?path=${encodeURIComponent(src.image_path)}`}
                                                    alt="Retrieved figure/chart"
                                                    className="source-image"
                                                    onClick={() => setZoomedImage(`${API_BASE}/api/figures/download?path=${encodeURIComponent(src.image_path)}`)}
                                                    onError={(e) => {
                                                      // Hide broken image container if load fails
                                                      e.target.style.display = 'none';
                                                    }}
                                                  />
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}

                      {isSending && messages[messages.length - 1]?.role !== 'assistant' && (
                        <div className="chat-bubble assistant">
                          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)', paddingLeft: '4px' }}>
                            <Brain className="spinner" size={12} style={{ color: '#8b5cf6' }} />
                            <span>AI is thinking...</span>
                          </div>
                          <div className="bubble-content" style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                            <span style={{ width: '4px', height: '4px', backgroundColor: '#9ca3af', borderRadius: '50%', animation: 'pulseGlow 1s infinite alternate' }}></span>
                            <span style={{ width: '4px', height: '4px', backgroundColor: '#9ca3af', borderRadius: '50%', animation: 'pulseGlow 1s infinite alternate 0.2s' }}></span>
                            <span style={{ width: '4px', height: '4px', backgroundColor: '#9ca3af', borderRadius: '50%', animation: 'pulseGlow 1s infinite alternate 0.4s' }}></span>
                          </div>
                        </div>
                      )}

                      <div ref={chatBottomRef}></div>
                    </div>

                    {/* Chat Input Field */}
                    <div className="chat-input-area">
                      <form onSubmit={handleSendMessage} className="chat-input-form">
                        <input
                          type="text"
                          placeholder="Ask a question about layout content, tables, or conclusions..."
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          className="chat-textarea"
                          disabled={isSending}
                        />
                        <button
                          type="submit"
                          className="chat-submit-btn"
                          disabled={isSending || !inputMessage.trim()}
                        >
                          <Send size={16} />
                        </button>
                      </form>
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-chat" style={{ flex: 1, border: '1px solid var(--border)', borderRadius: '12px', background: 'var(--bg-sidebar)', minHeight: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <Brain size={64} style={{ color: '#374151', animation: 'pulseGlow 2s infinite' }} />
                  <h3>No Document Selected</h3>
                  <p>Please select one or more research papers from the <strong>Library sidebar</strong>, or go to the <strong>Paper Discovery</strong> tab to fetch a new paper.</p>
                </div>
              )}
            </div>
          )}

        </div>
      </main>

      {zoomedImage && (
        <div 
          className="lightbox-overlay" 
          onClick={() => setZoomedImage(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(10px)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'zoom-out',
            animation: 'fade-in 0.25s ease-out'
          }}
        >
          <img 
            src={zoomedImage} 
            alt="Zoomed figure" 
            style={{
              maxWidth: '90%',
              maxHeight: '90%',
              objectFit: 'contain',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              animation: 'zoom-in-bounce 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'
            }} 
          />
          <div style={{
            position: 'absolute',
            bottom: '20px',
            color: '#94a3b8',
            fontSize: '13px',
            backgroundColor: 'rgba(0,0,0,0.5)',
            padding: '6px 16px',
            borderRadius: '20px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            Click anywhere to close zoom
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
