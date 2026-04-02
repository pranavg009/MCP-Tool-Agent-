# 🔧 AI Agent with Tool Use (MCP) using Groq LLM

A production ready AI agent system that integrates multiple real world tools such as web search, webpage extraction, file operations, and text summarization using the Model Context Protocol (MCP) paradigm.

This project demonstrates how modern Large Language Models (LLMs) move beyond static responses and actively interact with external tools to solve complex, multi-step tasks.

---

## 🚀 Live Demo Access Link

👉 https://c3rq9oixqbuwyiwneyvizu.streamlit.app/

---

## 🧠 Key Features

* 🔍 Web Search using DuckDuckGo
* 🌐 Webpage Content Extraction (clean parsing with BeautifulSoup)
* 📖 File Reading with metadata insights
* 📝 File Writing with secure path handling
* ✂️ AI-powered Text Summarization using Groq LLM
* 🔄 Tool Chaining (fetch → summarize workflows)
* ⚡ High-speed inference using Groq LLaMA 3.3 (70B)
* 🧩 Context-aware multi-turn conversation handling
* 🛡️ Robust error handling and retry mechanisms

---

## 🏗️ System Architecture

The system follows an **Agent + Tool Execution Loop**:

1. User Query
2. LLM decides whether to:

   * Respond directly OR
   * Call a tool
3. Tool executes the requested operation
4. Result is returned to the LLM
5. Final response is generated

This architecture enables **dynamic reasoning + action-based intelligence**, similar to real-world AI assistants.

---

## 🛠️ Tech Stack

* **LLM:** Groq (LLaMA 3.3 70B)
* **Frontend:** Streamlit
* **Search Engine:** DuckDuckGo API
* **Web Parsing:** BeautifulSoup
* **Backend:** Python
* **Architecture Concept:** Model Context Protocol (MCP)

---

## 📂 Project Structure

```
├── app.py              # Streamlit UI + agent loop
├── requirements.txt    # Project dependencies
├── .gitignore
└── core logic          # Tools + system prompt + agent execution loop
```

## 💡 Highlights

* Implements a **true agentic workflow**
* Demonstrates **tool-augmented reasoning**
* Handles **real-world constraints** (rate limits, errors, memory limits)
* Built with a **production-oriented architecture**

---


## 👨‍💻 Author
**Pranav Gupta**



