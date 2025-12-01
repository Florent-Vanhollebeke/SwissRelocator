import streamlit as st
import os
import pickle
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
from typing import Dict, List

# ============================================
# CONFIGURATION DES CHEMINS
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # SwissRelocator/
BACKEND_DIR = PROJECT_ROOT / "backend"
FAISS_INDEX_DIR = BACKEND_DIR / "app" / "data" / "faiss_index"

# --- 1. DÉFINITION DE LA CLASSE (Doit matcher index_faiss.py) ---
@dataclass
class Chunk:
    id: str
    text: str        # <--- C'est ici que c'était 'content' avant !
    metadata: Dict

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="Swiss Tax RAG", page_icon="🇨🇭", layout="wide")

# --- 3. CHARGEMENT ---
@st.cache_resource
def load_resources():
    print("--- DÉBUT CHARGEMENT ---")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    index_path = FAISS_INDEX_DIR / "index.faiss"
    meta_path = FAISS_INDEX_DIR / "data.pkl"

    if not index_path.exists():
        return None, None, None

    index = faiss.read_index(str(index_path))
    
    with open(str(meta_path), "rb") as f:
        data_global = pickle.load(f)
        
        # Extraction de la liste depuis le dictionnaire
        if isinstance(data_global, dict) and 'chunks' in data_global:
            chunk_list = data_global['chunks']
            print(f"✅ Liste extraite du dictionnaire. {len(chunk_list)} chunks.")
        else:
            chunk_list = data_global
            print(f"⚠️ Format direct (liste). {len(chunk_list)} chunks.")

    return model, index, chunk_list

# --- 4. RECHERCHE ---
def search(query, model, index, chunk_list, k=4):
    print(f"🔍 Recherche pour: {query}")
    query_vector = model.encode([query])
    distances, indices = index.search(query_vector, k)
    
    results = []
    
    for i in range(k):
        idx = indices[0][i]
        score = distances[0][i]
        
        if idx < len(chunk_list):
            chunk_obj = chunk_list[idx]
            
            try:
                # --- CORRECTION ICI : Utilisation de .text ---
                txt = chunk_obj.text 
                meta = chunk_obj.metadata
                
                src = meta.get('source', 'Inconnu')
                loc = meta.get('canton', 'N/A')
                doc_type = meta.get('doc_type', 'Autre')

                relevance = max(0, (20 - score) / 20 * 100)
                
                results.append({
                    "content": txt,
                    "source": src,
                    "canton": loc,
                    "type": doc_type,
                    "score": score,
                    "relevance": relevance
                })
            except Exception as e:
                print(f"⚠️ Erreur lecture chunk {idx}: {e}")
                
    return results

# --- 5. INTERFACE ---
col1, col2 = st.columns([1, 6])
with col1: st.markdown("## 🇨🇭")
with col2: st.title("Comparateur Fiscal France-Suisse")

# Chargement
with st.spinner('Chargement du cerveau juridique...'):
    model, index, chunk_list = load_resources()

if model is None:
    st.error("⚠️ Erreur : Index introuvable.")
    st.stop()

# Recherche
query = st.text_input("Votre question :", placeholder="Ex: impôt frontalier Genève vs Vaud")

if query:
    results = search(query, model, index, chunk_list)
    
    if not results:
        st.warning("Aucun résultat pertinent trouvé.")
    
    st.markdown("---")
    st.subheader(f"🔍 Résultats pertinents ({len(results)})")

    for i, res in enumerate(results):
        color = "green" if res['relevance'] > 60 else "orange"
        if res['relevance'] < 40: color = "red"
        
        title = f"📄 {res['canton']} | {res['type']} | Pertinence: :{color}[{res['relevance']:.1f}%]"
        
        with st.expander(title, expanded=(i==0)):
            st.markdown(f"**Source:** `{res['source']}`")
            st.info(res['content'])
            st.caption(f"Score FAISS : {res['score']:.4f}")