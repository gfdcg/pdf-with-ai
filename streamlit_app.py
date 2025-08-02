import streamlit as st
import os
import tempfile
from datetime import datetime
import requests
import time
from pathlib import Path

# Imports pour le traitement PDF et RAG
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.llms import Ollama
    from langchain.chains import RetrievalQA
    from langchain.document_loaders import PyPDFLoader
    from langchain_community.llms import Ollama as CommunityOllama
except ImportError as e:
    st.error(f"Erreur d'import : {e}")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="RAG AI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS moderne et épuré
st.markdown("""
<style>
/* ===== POLICE ET FOND GLOBAL ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    color: #1f2937; /* Texte très lisible */
    background-color: #f3f4f6;
}

/* ===== ZONE PRINCIPALE ===== */
.stApp {
    background: linear-gradient(to right, #706B75, #706B75);
    padding: 2rem;
}

/* ===== EN-TÊTE ===== */
.header-section {
    text-align: center;
    margin-bottom: 2.5rem;
}
.header-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #4f46e5; /* Violette lisible */
    margin-bottom: 0.5rem;
}
.header-subtitle {
    font-size: 1.1rem;
    color: #4b5563;
}

/* ===== CONTAINER PRINCIPAL ===== */
.main-container {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    margin: auto;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}

/* ===== ZONE DE CHAT ===== */
.chat-area {
    background-color: #f9fafb;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e5e7eb;
}
.response-area {
    background-color: #e0f2fe;
    border-left: 4px solid #0ea5e9;
    padding: 1rem 1.5rem;
    margin-top: 1.5rem;
    border-radius: 12px;
}

/* ===== FORMULAIRE QUESTION ===== */
.question-box {
    background: #f1f5f9;
    border: 2px solid #cbd5e1;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.question-box:focus-within {
    border-color:#426278;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    color : black
}

/* ===== BARRE LATÉRALE ===== */
.sidebar-content {
    background-color: #426278;
    padding: 1.2rem;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    margin-bottom: 1rem;
}

/* ===== INDICATEURS DE STATUT ===== */
.status-indicator {
    font-size: 0.9rem;
    font-weight: 600;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    display: inline-block;
    margin-bottom: 1rem;
}
.status-online {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #bbf7d0;
}
.status-offline {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}
.status-waiting {
    background-color: #fef9c3;
    color: #92400e;
    border: 1px solid #fde68a;
}

/* ===== BOUTONS ===== */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    font-size: 1rem;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    transition: transform 0.15s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

/* ===== UPLOADER ===== */
.stFileUploader > div {
    background-color: #f1f5f9;
    border: 2px dashed #94a3b8;
    padding: 1.5rem;
    border-radius: 12px;
    transition: all 0.3s ease;
    text-align: center;
}
.stFileUploader > div:hover {
    background-color: #e0f2fe;
    border-color: #3b82f6;
}

/* ===== HISTORIQUE ===== */
.history-item {
    background-color: #f9fafb;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    border: 1px solid #e5e7eb;
    font-size: 0.9rem;
    color: #374151;
}

/* ===== MÉTRIQUES ===== */
.metric-card {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    margin-bottom: 1rem;
    transition: transform 0.2s ease;
}
.metric-card:hover {
    transform: scale(1.015);
}
.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
}
.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: #6b7280;
    font-weight: 600;
    margin-top: 0.25rem;
}
/* Fixe la couleur du texte dans les encadrés info/alerte */
.stAlert, .stInfo, .stWarning {
    color: #111827 !important; /* Texte foncé et lisible */
    font-weight: 600;
}

/* Fond plus neutre pour l'encadré info */
.stInfo {
    background: #dbeafe !important; /* Bleu plus foncé */
    border: 1px solid #60a5fa !important;
}

/* Fond plus neutre pour l'encadré warning */
.stWarning {
    background: #fef3c7 !important; /* Jaune */
    border: 1px solid #fbbf24 !important;
}

</style>
""", unsafe_allow_html=True)

# Créer les dossiers nécessaires
def create_directories():
    directories = ['data/uploads', 'faiss_index']
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

create_directories()

# Variables de session
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None
if 'pdf_processed' not in st.session_state:
    st.session_state.pdf_processed = False
if 'question_history' not in st.session_state:
    st.session_state.question_history = []
if 'current_pdf' not in st.session_state:
    st.session_state.current_pdf = None

# Configuration Ollama
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')

def check_ollama_connection():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        return response.status_code == 200
    except:
        return False

def get_available_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            clean_models = []
            for model in models:
                model_name = model['name']
                if model_name.endswith(':latest'):
                    model_name = model_name.replace(':latest', '')
                clean_models.append(model_name)
            return clean_models
        return []
    except:
        return []

def pull_model(model_name):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/pull", 
            json={"name": model_name},
            timeout=300
        )
        return response.status_code == 200
    except:
        return False

def extract_text_from_pdf(pdf_file):
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=upload_dir) as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_file_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_file_path)
        documents = loader.load()
        st.session_state.current_pdf = tmp_file_path
        
        return documents
    except Exception as e:
        st.error(f"❌ Erreur extraction PDF : {e}")
        return None

@st.cache_resource
def get_embeddings():
    try:
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
    except Exception as e:
        st.error(f"❌ Erreur embeddings : {e}")
        return None

def create_vector_store(documents):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_documents(documents)
        
        embeddings = get_embeddings()
        if not embeddings:
            return None
        
        with st.spinner("Création de l'index vectoriel..."):
            vector_store = FAISS.from_documents(texts, embeddings)
        
        return vector_store
    except Exception as e:
        st.error(f"❌ Erreur vector store : {e}")
        return None

def create_qa_chain(vector_store, model_name="llama2"):
    try:
        llm = CommunityOllama(
            model=model_name,
            base_url=OLLAMA_URL,
            temperature=0.1
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            ),
            return_source_documents=True
        )
        
        return qa_chain
    except Exception as e:
        st.error(f"❌ Erreur QA chain : {e}")
        return None

def main():
    # Container principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # En-tête
    st.markdown("""
    <div class="header-section">
        <div class="header-title">🧠 RAG AI Assistant</div>
        <div class="header-subtitle">Intelligence artificielle pour l'analyse de documents PDF</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # Status Ollama
        ollama_connected = check_ollama_connection()
        status_class = "status-online" if ollama_connected else "status-offline"
        status_text = "🟢 Ollama en ligne" if ollama_connected else "🔴 Ollama hors ligne"
        
        st.markdown(f'<div class="{status_class} status-indicator">{status_text}</div>', unsafe_allow_html=True)
        
        if ollama_connected:
            st.markdown('<div class="section-title">🤖 Modèle IA</div>', unsafe_allow_html=True)
            
            available_models = get_available_models()
            
            if available_models:
                selected_model = st.selectbox(
                    "Sélectionner un modèle",
                    available_models,
                    label_visibility="collapsed"
                )
            else:
                st.warning("Aucun modèle disponible")
                model_options = ["llama3.2", "llama2", "mistral", "codellama"]
                model_to_pull = st.selectbox("Télécharger un modèle:", model_options)
                
                if st.button("📥 Télécharger"):
                    with st.spinner(f"Téléchargement {model_to_pull}..."):
                        if pull_model(model_to_pull):
                            st.success("✅ Téléchargé!")
                            st.rerun()
                        else:
                            st.error("❌ Échec")
                
                selected_model = "llama3.2"
        else:
            st.error("Vérifiez que Ollama est démarré")
            if st.button("🔄 Réessayer"):
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Upload PDF
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📄 Document PDF</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Glissez votre PDF ici",
            type="pdf",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            st.success(f"📁 {uploaded_file.name}")
            st.info(f"📊 {uploaded_file.size / (1024*1024):.1f} MB")
            
            if st.button("🚀 Analyser", type="primary"):
                with st.spinner("Analyse en cours..."):
                    documents = extract_text_from_pdf(uploaded_file)
                    
                    if documents:
                        st.success(f"✅ {len(documents)} pages")
                        
                        vector_store = create_vector_store(documents)
                        if vector_store:
                            qa_chain = create_qa_chain(vector_store, selected_model)
                            
                            if qa_chain:
                                st.session_state.vector_store = vector_store
                                st.session_state.qa_chain = qa_chain
                                st.session_state.pdf_processed = True
                                st.session_state.current_model = selected_model
                                st.session_state.pdf_name = uploaded_file.name
                                
                                st.success("🎉 Prêt!")
                                st.balloons()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 État</div>', unsafe_allow_html=True)
        
        if st.session_state.pdf_processed:
            st.markdown('<div class="status-online status-indicator">✅ Document prêt</div>', unsafe_allow_html=True)
            if hasattr(st.session_state, 'current_model'):
                st.info(f"🤖 {st.session_state.current_model}")
        else:
            st.markdown('<div class="status-waiting status-indicator">⏳ En attente</div>', unsafe_allow_html=True)
        
        if st.button("🗑️ Reset"):
            for key in ['vector_store', 'qa_chain', 'pdf_processed', 'question_history']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Zone principale
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="chat-area">', unsafe_allow_html=True)
        
        if st.session_state.pdf_processed:
            st.markdown("### 💬 Poser une question")
            
            question = st.text_area(
                "Question:",
                placeholder="Que contient ce document ?",
                height=100,
                label_visibility="collapsed"
            )
            
            if st.button("🔍 Analyser", type="primary"):
                if question.strip():
                    with st.spinner("Génération de la réponse..."):
                        try:
                            st.session_state.question_history.append({
                                'question': question,
                                'timestamp': datetime.now().strftime("%H:%M")
                            })
                            
                            result = st.session_state.qa_chain({"query": question})
                            
                            st.markdown('<div class="response-area">', unsafe_allow_html=True)
                            st.markdown("**🎯 Réponse:**")
                            st.write(result["result"])
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            if "source_documents" in result and result["source_documents"]:
                                with st.expander("📚 Sources", expanded=False):
                                    for i, doc in enumerate(result["source_documents"]):
                                        st.markdown(f"**Source {i+1}:**")
                                        st.write(doc.page_content[:300] + "...")
                                        st.markdown("---")
                        
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
                else:
                    st.warning("⚠️ Saisissez une question")
        
        else:
            st.markdown("### 🚀 Commencer")
            st.info("Téléchargez un PDF dans la barre latérale pour commencer")
            
            st.markdown('<div class="example-questions">', unsafe_allow_html=True)
            st.markdown("**💡 Exemples de questions:**")
            
            examples = [
                "Résumez ce document en 3 points",
                "Quelles sont les conclusions principales ?",
                "Y a-t-il des chiffres importants ?",
                "Qui sont les auteurs mentionnés ?",
                "Quel est le contexte de ce document ?"
            ]
            
            for example in examples:
                st.markdown(f'<div class="example-item">• {example}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Métriques
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{"🟢" if check_ollama_connection() else "🔴"}</div>
            <div class="metric-label">Ollama</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{"📄" if st.session_state.pdf_processed else "⏳"}</div>
            <div class="metric-label">Document</div>
        </div>
        ''', unsafe_allow_html=True)
        
        models_count = len(get_available_models())
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{models_count}</div>
            <div class="metric-label">Modèles</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Historique
        if st.session_state.question_history:
            st.markdown("### 📝 Historique")
            for item in reversed(st.session_state.question_history[-3:]):
                st.markdown(f'''
                <div class="history-item">
                    <small>{item['timestamp']}</small><br>
                    <em>{item['question'][:50]}...</em>
                </div>
                ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()