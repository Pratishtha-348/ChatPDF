import streamlit as st
import requests
import time
import os
import json
from datetime import datetime

# API configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- Helper functions ---
def register(email, password, role="user"):
    endpoint = "/auth/register" if role == "user" else "/auth/register-admin"
    payload = {"email": email, "password": password}
    
    if role == "admin":
        admin_key = st.session_state.get("admin_key", "")
        payload["admin_key"] = admin_key
    
    r = requests.post(f"{API_URL}{endpoint}", json=payload)
    if r.status_code == 200:
        return True, "Registration successful! Please login."
    else:
        try:
            return False, r.json().get("detail", "Registration failed")
        except:
            return False, "Registration failed"

def login(email, password):
    r = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
    if r.status_code == 200:
        data = r.json()
        st.session_state["token"] = data["access_token"]
        st.session_state["user_email"] = email
        st.session_state["user_role"] = data.get("role", "user")
        return True, "Login successful!"
    else:
        try:
            return False, r.json().get("detail", "Login failed")
        except:
            return False, "Login failed"

def admin_upload_pdf(file, title=None):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    files = {"file": (file.name, file, "application/pdf")}
    data = {"title": title} if title else {}
    r = requests.post(f"{API_URL}/admin/ingest_pdf", files=files, data=data, headers=headers)
    if r.status_code == 200:
        return True, r.json()
    else:
        return False, None

def get_admin_documents():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        r = requests.get(f"{API_URL}/admin/documents", headers=headers)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def delete_document(doc_id):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        r = requests.delete(f"{API_URL}/admin/document/{doc_id}", headers=headers)
        return r.status_code == 200
    except:
        return False

def query_rag_stream(query):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    
    try:
        response = requests.post(
            f"{API_URL}/rag/query_stream",
            json={"query": query, "top_k": 8},
            headers=headers,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if "chunk" in data:
                            yield data["chunk"]
                    except json.JSONDecodeError:
                        continue
        else:
            yield query_rag_fallback(query)
            
    except requests.exceptions.RequestException:
        yield query_rag_fallback(query)

def query_rag_fallback(query):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        r = requests.post(
            f"{API_URL}/rag/query",
            json={"query": query, "top_k": 8},
            headers=headers,
            timeout=30
        )
        if r.status_code == 200:
            return r.json()["answer"]
    except:
        pass
    return "Sorry, I couldn't process your question. Please try again."

def save_message_to_db(role, content):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        requests.post(
            f"{API_URL}/conversations/save",
            json={"role": role, "content": content},
            headers=headers,
            timeout=5
        )
    except:
        pass

def load_conversation_history():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        r = requests.get(f"{API_URL}/conversations/history", headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json()["messages"]
    except:
        pass
    return []

def clear_conversation_history():
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        requests.delete(f"{API_URL}/conversations/clear", headers=headers, timeout=5)
    except:
        pass

def get_user_initials(email):
    """Get initials from email"""
    name = email.split('@')[0]
    parts = name.replace('.', ' ').replace('_', ' ').split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper()

# --- Page Config ---
st.set_page_config(
    page_title="AI Knowledge Base",
    page_icon="🏢",
    layout="wide" if "token" in st.session_state and st.session_state.get("user_role") == "admin" else "centered"
)

# Simple, clean CSS
st.markdown("""
<style>
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* User profile badge */
    .user-badge {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 15px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 16px;
    }
    
    .user-info {
        flex: 1;
    }
    
    .user-email {
        font-weight: 600;
        font-size: 14px;
        margin: 0;
    }
    
    .user-role {
        font-size: 12px;
        color: #666;
        margin: 0;
    }
    
    /* Current date badge */
    .date-badge {
        background: #f0f9ff;
        border: 1px solid #bfdbfe;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
        color: #1e40af;
        margin-bottom: 15px;
        text-align: center;
    }
    
    /* Headers */
    .page-header {
        padding: 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 30px;
    }
    
    .admin-bg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .user-bg {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .page-header h1 {
        margin: 0;
        font-size: 2rem;
    }
    
    .page-header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
    }
    
    /* Document cards */
    .doc-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #667eea;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Cleaner buttons */
    .stButton > button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

# --- User Profile Component ---
def show_user_profile():
    """Simple user profile display"""
    email = st.session_state.get("user_email", "")
    role = st.session_state.get("user_role", "user")
    initials = get_user_initials(email)
    
    st.markdown(f"""
    <div class="user-badge">
        <div class="user-avatar">{initials}</div>
        <div class="user-info">
            <p class="user-email">{email}</p>
            <p class="user-role">{"Administrator" if role == "admin" else "User"}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_current_date():
    """Display current date for context"""
    current_date = datetime.now().strftime("%B %d, %Y")
    current_day = datetime.now().strftime("%A")
    
    st.markdown(f"""
    <div class="date-badge">
        📅 Today: {current_day}, {current_date}
    </div>
    """, unsafe_allow_html=True)

# --- Main App ---
if "token" not in st.session_state:
    # LOGIN/REGISTER SCREEN
    st.title("🏢 AI Knowledge Base")
    st.markdown("---")
    
    login_type = st.radio("Select Login Type", ["User", "Admin"], horizontal=True, label_visibility="collapsed")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader(f"{login_type} Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted and email and password:
                with st.spinner("Logging in..."):
                    success, message = login(email, password)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab2:
        with st.form("register_form"):
            st.subheader(f"Register as {login_type}")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if login_type == "Admin":
                st.session_state["admin_key"] = st.text_input("Admin Secret Key", type="password", key="admin_key_input")
            
            submitted = st.form_submit_button("Register", type="primary", use_container_width=True)
            
            if submitted:
                if not new_email or not new_password:
                    st.error("Please fill all fields")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    with st.spinner("Creating account..."):
                        success, message = register(new_email, new_password, role=login_type.lower())
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

elif st.session_state.get("user_role") == "admin":
    # ADMIN INTERFACE
    
    # Sidebar
    with st.sidebar:
        show_user_profile()
        show_current_date()
        
        st.markdown("### Quick Stats")
        docs = get_admin_documents()
        st.metric("Documents", len(docs))
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Header
    st.markdown('<div class="page-header admin-bg"><h1>🔧 Admin Dashboard</h1><p>Manage documents and test queries</p></div>', unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "📚 Documents", "💬 Test Chat"])
    
    with tab1:
        st.subheader("Upload Document")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        title = st.text_input("Title (optional)")
        
        if uploaded_file:
            if st.button("Upload", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    success, result = admin_upload_pdf(uploaded_file, title)
                    if success:
                        st.success("Document uploaded!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Upload failed")
    
    with tab2:
        st.subheader("Manage Documents")
        docs = get_admin_documents()
        
        if docs:
            for doc in docs:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**📄 {doc['title'] or 'Untitled'}**")
                with col2:
                    created = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
                    st.caption(created.strftime('%Y-%m-%d %H:%M'))
                with col3:
                    if st.button("🗑️", key=f"del_{doc['id']}"):
                        if delete_document(doc['id']):
                            st.success("Deleted")
                            time.sleep(1)
                            st.rerun()
                st.markdown("---")
        else:
            st.info("No documents yet")
    
    with tab3:
        st.subheader("Test Queries")
        
        # Show current date context
        show_current_date()
        
        # Load history
        if not st.session_state.history_loaded:
            st.session_state.messages = load_conversation_history()
            st.session_state.history_loaded = True
        
        # Chat display
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask something..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            save_message_to_db("user", prompt)
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_response = ""
                
                for chunk in query_rag_stream(prompt):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_message_to_db("assistant", full_response)
        
        # Clear button
        if st.button("Clear Chat"):
            clear_conversation_history()
            st.session_state.messages = []
            st.rerun()

else:
    # USER INTERFACE
    
    # Sidebar
    with st.sidebar:
        show_user_profile()
        show_current_date()
        
        st.markdown("---")
        st.markdown("### 💡 Try asking:")
        suggestions = [
            "What are the policies?",
            "Employee benefits?",
            "Upcoming holidays?",
        ]
        for q in suggestions:
            if st.button(q, key=q, use_container_width=True):
                st.session_state.suggested_query = q
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            clear_conversation_history()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Load history
    if not st.session_state.history_loaded:
        st.session_state.messages = load_conversation_history()
        st.session_state.history_loaded = True
    
    # Header
    st.markdown('<div class="page-header user-bg"><h1>💬 AI Assistant</h1><p>Ask questions about company documents</p></div>', unsafe_allow_html=True)
    
    # Welcome message
    if len(st.session_state.messages) == 0:
        st.info("👋 Hi! Ask me anything about company documents.")
    
    # Chat display
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle suggested query or chat input
    prompt = st.session_state.pop("suggested_query", None) or st.chat_input("Ask a question...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message_to_db("user", prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            
            for chunk in query_rag_stream(prompt):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_message_to_db("assistant", full_response)
    
    # Footer
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 New Chat", use_container_width=True):
            clear_conversation_history()
            st.session_state.messages = []
            st.rerun()