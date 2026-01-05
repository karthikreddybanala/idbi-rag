import streamlit as st
import os
import json
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from vector_store import get_vector_store

# ----------------- Constants -----------------
CHAT_HISTORY_FILE = "chat_history.json"

# ----------------- Utility Functions -----------------
def load_chat_history():
    """Load chat history from JSON file."""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_chat_history(chat_history):
    """Save chat history to JSON file."""
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4, ensure_ascii=False)

# ----------------- Streamlit Page Config -----------------
st.set_page_config(page_title="Accounts RAG", layout="wide")
st.title("💬 AI Assistant")

# ----------------- Initialize Session State -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # Current chat messages
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()
if "current_chat_name" not in st.session_state:
    st.session_state.current_chat_name = "New Chat"
if "show_menu" not in st.session_state:
    st.session_state.show_menu = None  # Which chat's menu is open
if "rename_target" not in st.session_state:
    st.session_state.rename_target = None  # Which chat is being renamed

# ----------------- Sidebar -----------------
st.sidebar.header("🔍 Setup & History")

# Build / Refresh Vector DB
if st.sidebar.button("Build Vector DB"):
    with st.spinner("Building vector database... Please wait ⏳"):
        loader = DirectoryLoader("data", glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        vectordb = get_vector_store()
        vectordb.add_documents(chunks)
        vectordb.persist()
    st.sidebar.success("✅ Vector DB created successfully!")

# New Chat button
if st.sidebar.button("➕ New Chat"):
    # Save old chat if not empty
    if st.session_state.messages:
        first_msg = st.session_state.messages[0]["text"][:30] if st.session_state.messages else "Chat"
        chat_name = first_msg or "Chat"
        counter = 1
        while chat_name in st.session_state.chat_history:
            chat_name = f"{first_msg}_{counter}"
            counter += 1
        st.session_state.chat_history[chat_name] = st.session_state.messages.copy()
        save_chat_history(st.session_state.chat_history)
    st.session_state.messages = []
    st.session_state.current_chat_name = "New Chat"

# ----------------- Chat History (Sidebar) -----------------
st.sidebar.subheader("💾 Chat History")

# Custom CSS
st.sidebar.markdown("""
<style>
.chat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    border-radius: 6px;
    margin-bottom: 4px;
    cursor: pointer;
}
.chat-row:hover {
    background-color: #ececec;
}
.menu-btn {
    font-weight: 900;
    color: #000;
    background: none;
    border: none;
    font-size: 18px;
    visibility: hidden;
    cursor: pointer;
}
.chat-row:hover .menu-btn {
    visibility: visible;
}
.menu-popup {
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 6px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
    padding: 4px 0;
    margin-left: 20px;
}
.menu-item {
    padding: 6px 12px;
    cursor: pointer;
}
.menu-item:hover {
    background: #f2f2f2;
}
</style>
""", unsafe_allow_html=True)

for chat_name in list(st.session_state.chat_history.keys()):
    col1, col2 = st.sidebar.columns([0.8, 0.2])
    with col1:
        if st.button(chat_name, key=f"load_{chat_name}"):
            st.session_state.messages = st.session_state.chat_history[chat_name].copy()
            st.session_state.current_chat_name = chat_name
            st.session_state.show_menu = None
    with col2:
        if st.button("⋮", key=f"menu_{chat_name}", help="Options", use_container_width=False):
            st.session_state.show_menu = chat_name if st.session_state.show_menu != chat_name else None

    # Show rename/delete menu when menu is open
    if st.session_state.show_menu == chat_name:
        with st.sidebar.container():
            st.markdown('<div class="menu-popup">', unsafe_allow_html=True)
            if st.button("✏️ Rename", key=f"rename_{chat_name}", use_container_width=True):
                st.session_state.rename_target = chat_name
                st.session_state.show_menu = None
            if st.button("🗑️ Delete", key=f"delete_{chat_name}", use_container_width=True):
                del st.session_state.chat_history[chat_name]
                save_chat_history(st.session_state.chat_history)
                st.session_state.show_menu = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# Rename chat form
if st.session_state.rename_target:
    with st.sidebar.form("rename_form", clear_on_submit=True):
        new_name = st.text_input("Rename chat:", value=st.session_state.rename_target)
        rename_submit = st.form_submit_button("Save")
        if rename_submit:
            if new_name.strip() and new_name != st.session_state.rename_target:
                st.session_state.chat_history[new_name] = st.session_state.chat_history.pop(st.session_state.rename_target)
                if st.session_state.current_chat_name == st.session_state.rename_target:
                    st.session_state.current_chat_name = new_name
                st.session_state.rename_target = None
                save_chat_history(st.session_state.chat_history)
                st.rerun()
            else:
                st.session_state.rename_target = None

# ----------------- Main Chat Window -----------------
chat_placeholder = st.empty()

def render_chat():
    """Render chat messages with auto-scroll"""
    chat_html = ""
    for msg in st.session_state.messages:
        if msg["sender"] == "user":
            chat_html += f"<div style='text-align:right; background:#DCF8C6; padding:8px; border-radius:10px; margin:5px'>{msg['text']}</div>"
        else:
            chat_html += f"<div style='text-align:left; background:#F1F0F0; padding:8px; border-radius:10px; margin:5px'>{msg['text']}</div>"
    chat_html += "<div id='scroll-anchor'></div>"
    chat_placeholder.markdown(chat_html, unsafe_allow_html=True)
    st.components.v1.html("""
    <script>
    var el=document.getElementById('scroll-anchor');
    if(el){el.scrollIntoView({behavior:'smooth'});}
    </script>
    """, height=0)

# ----------------- Chat Input -----------------
with st.form(key="chat_form", clear_on_submit=True):
    query = st.text_input("Type your question here:", placeholder="Ask me anything...")
    send = st.form_submit_button("Send")
    if send and query.strip():
        st.session_state.messages.append({"sender": "user", "text": query})
        render_chat()
        with st.spinner("Generating response..."):
            try:
                vectordb = get_vector_store()
                retriever = vectordb.as_retriever(search_kwargs={"k": 1})
                llm = Ollama(model="gpt-oss:latest", temperature=0.1, verbose=False)
                qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
                response = qa_chain.run(query)
                st.session_state.messages.append({"sender": "assistant", "text": response})
                render_chat()

                # Save to persistent storage
                current_chat = st.session_state.current_chat_name
                if current_chat == "New Chat":
                    first_msg = st.session_state.messages[0]["text"][:30]
                    chat_name = first_msg or "Chat"
                    counter = 1
                    while chat_name in st.session_state.chat_history:
                        chat_name = f"{chat_name}_{counter}"
                        counter += 1
                    st.session_state.current_chat_name = chat_name
                    current_chat = chat_name
                st.session_state.chat_history[current_chat] = st.session_state.messages.copy()
                save_chat_history(st.session_state.chat_history)
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

render_chat()

