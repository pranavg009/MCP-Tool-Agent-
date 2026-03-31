import streamlit as st
from groq import Groq, RateLimitError
import os, json, requests, time
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────
client = Groq(api_key=os.environ["GROQ_API_KEY"])

st.set_page_config(
    page_title="MCP Tools Server",
    page_icon="🔧",
    layout="centered"
)
st.title("🔧 MCP Tools Server")
st.caption("AI agent with live web search, file I/O, and webpage reading — powered by Groq")

# ── Tool functions ─────────────────────────────────────────────
def search_web(query):
    if not query or not query.strip():
        return "Error: Query cannot be empty."
    try:
        with DDGS() as d:
            results = list(d.text(query, max_results=5))
        if not results:
            return "No results found."
        return "\n".join(
            f"{i+1}. {r['title']}\n   {r['href']}\n   {r['body'][:200]}"
            for i, r in enumerate(results)
        )
    except Exception as e:
        return f"Search error: {e}"

def fetch_webpage(url):
    if not url or not url.strip().startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer", "header", "aside"]):
            t.decompose()
        lines = [
            l for l in soup.get_text(separator="\n", strip=True).splitlines()
            if len(l.strip()) > 40
        ]
        return "\n".join(lines[:80])
    except Exception as e:
        return f"Error fetching page: {e}"

def read_file(filepath):
    if not filepath or not filepath.strip():
        return "Error: Filepath cannot be empty."
    for bad in ["../", "..\\", ";", "|", "&", "$", "`"]:
        if bad in filepath:
            return "Error: Invalid characters in filepath."
    try:
        with open(filepath.strip(), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{filepath}' does not exist."
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filepath, content):
    if not filepath or not filepath.strip():
        return "Error: Filepath cannot be empty."
    for bad in ["../", "..\\", ";", "|", "&", "$", "`"]:
        if bad in filepath:
            return "Error: Invalid characters in filepath."
    if content is None:
        return "Error: Content cannot be None."
    try:
        with open(filepath.strip(), "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully written {len(content)} characters to '{filepath}'"
    except Exception as e:
        return f"Error writing file: {e}"

TOOL_MAP = {
    "search_web":    search_web,
    "fetch_webpage": fetch_webpage,
    "read_file":     read_file,
    "write_file":    write_file
}

TOOL_ICONS = {
    "search_web":    "🔍",
    "fetch_webpage": "🌐",
    "read_file":     "📖",
    "write_file":    "📝"
}

TOOLS = [
    {"type": "function", "function": {
        "name": "search_web",
        "description": "Search the internet using DuckDuckGo for current, live information. Use this when the user asks about recent events, news, or anything requiring up to date web data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to look up"}
            },
            "required": ["query"]
        }
    }},
    {"type": "function", "function": {
        "name": "fetch_webpage",
        "description": "Fetch and read the text content of any webpage from a URL. Use when the user provides a URL or wants content from a specific website.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL starting with http:// or https://"}
            },
            "required": ["url"]
        }
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read and return the contents of a local file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["filepath"]
        }
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write text content to a local file. Creates the file if it does not exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path where the file should be written"},
                "content":  {"type": "string", "description": "Text content to write to the file"}
            },
            "required": ["filepath", "content"]
        }
    }}
]

SYSTEM_PROMPT = """You are a helpful AI assistant with access to 4 tools:
- search_web: search the internet for current information
- fetch_webpage: read content from any URL
- read_file: read local files
- write_file: write content to local files

IMPORTANT RULES:
- Always call tools using the proper function calling interface only
- Never write tool calls as plain text, XML tags, or any other format
- Use tools whenever they would help answer the user question better
- Always be accurate, helpful, and concise."""

# ── Session State ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []      # display messages for UI
if "history" not in st.session_state:
    st.session_state.history  = []      # real Groq message history for memory

# Render existing chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat Input ─────────────────────────────────────────────────
if prompt := st.chat_input("Ask anything — I can search web, read files, fetch URLs..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        # Three separate placeholders so each updates independently
        status       = st.empty()   # spinning status line
        tools_display = st.empty()  # tool chain summary
        answer       = st.empty()   # final reply

        status.markdown("*🤔 Thinking...*")

        # Build full message list with history for real memory
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + st.session_state.history
            + [{"role": "user", "content": prompt}]
        )

        tools_used     = []
        reply          = "No response generated."
        MAX_TOOL_ROUNDS = 6
        tool_round      = 0

        while tool_round < MAX_TOOL_ROUNDS:

            # ── Call Groq ──────────────────────────────────
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=4096
                )
            except RateLimitError:
                status.markdown("*⏳ Rate limit — waiting 30s then retrying...*")
                time.sleep(30)
                continue
            except Exception as e:
                reply = f"❌ API error: {str(e)}"
                break

            assistant_message = response.choices[0].message

            # Append assistant turn to message history
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in (assistant_message.tool_calls or [])
                ] or None
            })

            # ── No tool calls → final answer ───────────────
            if not assistant_message.tool_calls:
                reply = assistant_message.content or "No response generated."
                break

            # ── Execute tool calls ─────────────────────────
            for tc in assistant_message.tool_calls:
                tool_name = tc.function.name

                try:
                    tool_args = json.loads(tc.function.arguments)
                except Exception:
                    tool_args = {}

                tools_used.append(tool_name)

                icon = TOOL_ICONS.get(tool_name, "🔧")
                hint = (
                    tool_args.get("query") or
                    tool_args.get("url") or
                    tool_args.get("filepath") or ""
                )
                status.markdown(f"*{icon} Running `{tool_name}`: `{hint[:60]}`...*")

                try:
                    tool_result = (
                        TOOL_MAP[tool_name](**tool_args)
                        if tool_name in TOOL_MAP
                        else f"Tool {tool_name} not found."
                    )
                except Exception as e:
                    tool_result = f"Tool execution error in {tool_name}: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(tool_result)
                })

            tool_round += 1

        # ── Render final output ────────────────────────────
        status.empty()  # clear the spinning status

        if tools_used:
            chain = " → ".join(
                f"{TOOL_ICONS.get(t, '🔧')} {t}" for t in tools_used
            )
            tools_display.caption(f"Tools used: {chain}")

        # st.markdown instead of st.write_stream
        # write_stream was causing the UI to hang — markdown renders immediately
        answer.markdown(reply)

    # Save to history for memory across turns
    st.session_state.history.append({"role": "user",      "content": prompt})
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.session_state.messages.append({"role": "assistant", "content": reply})
