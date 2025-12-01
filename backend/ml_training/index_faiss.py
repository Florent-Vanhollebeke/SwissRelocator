#!/usr/bin/env python3
"""
Swiss Tax RAG - Build FAISS Index
=================================
Construit l'index FAISS a partir des documents fiscaux.

Usage:
    python index_faiss.py
"""

import hashlib
import pickle
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================
# CONFIGURATION DES CHEMINS
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # SwissRelocator/
BACKEND_DIR = PROJECT_ROOT / "backend"

# Donnees sources (TXT fiscaux)
RAG_DATA_DIR = BACKEND_DIR / "data" / "rag" / "fiscal"

# Index de sortie (MEME CHEMIN QUE build_faiss_index.py)
FAISS_INDEX_DIR = BACKEND_DIR / "app" / "data" / "faiss_index"

# Modele d'embedding (MEME QUE build_faiss_index.py)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ============================================
# CLASSE CHUNK (IDENTIQUE A build_faiss_index.py)
# ============================================

@dataclass
class Chunk:
    id: str
    text: str  # IMPORTANT: doit etre 'text' et non 'content'
    metadata: Dict

# ============================================
# METADONNEES DES DOCUMENTS
# ============================================

DOCUMENTS_META = {
    # === SUISSE - FEUILLES CANTONALES ===
    "feuille_cantonale_ge.txt": {
        "canton": "GE",
        "doc_type": "feuille_cantonale",
        "language": "fr",
        "description": "Feuille cantonale Geneve - Fiscalite PP et PM",
    },
    "feuille_cantonale_vd.txt": {
        "canton": "VD",
        "doc_type": "feuille_cantonale",
        "language": "fr",
        "description": "Feuille cantonale Vaud - Fiscalite PP et PM",
    },
    "feuille_cantonale_zh.txt": {
        "canton": "ZH",
        "doc_type": "feuille_cantonale",
        "language": "de",
        "description": "Kantonsblatt Zurich - Fiscalite PP et PM",
    },
    "feuille_cantonale_bs.txt": {
        "canton": "BS",
        "doc_type": "feuille_cantonale",
        "language": "de",
        "description": "Kantonsblatt Basel-Stadt - Fiscalite PP et PM (Pharma Hub)",
    },

    # === FRANCE ===
    "feuille_cantonale_fr_lyon.txt": {
        "canton": "FR",
        "doc_type": "feuille_nationale",
        "language": "fr",
        "description": "Fiscalite France - Region Lyon/ARA",
    },

    # === COMPARATIFS ===
    "droit_mutation_ch.txt": {
        "canton": "CH",
        "doc_type": "comparatif",
        "language": "fr",
        "description": "Droit de mutation - Comparatif tous cantons",
    },
    "charges_sociales_comparatif.txt": {
        "canton": "CH",
        "doc_type": "comparatif",
        "language": "fr",
        "description": "Charges sociales patronales - Comparatif FR/CH",
    },
    "tva_comparatif.txt": {
        "canton": "CH",
        "doc_type": "comparatif",
        "language": "fr",
        "description": "TVA - Comparatif France/Suisse",
    },
}

# Import BOFIP metadata si disponible
try:
    from bofip_meta import BOFIP_DOCUMENTS_META
    DOCUMENTS_META.update(BOFIP_DOCUMENTS_META)
    print(f"[OK] BOFIP metadata importees ({len(BOFIP_DOCUMENTS_META)} docs)")
except ImportError:
    pass  # Pas de BOFIP, pas grave

# ============================================
# FONCTIONS
# ============================================

def create_chunks_from_text(filename: str, text: str, meta: Dict) -> List[Chunk]:
    """Decoupe un texte en chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    text_chunks = splitter.split_text(text)
    chunks = []

    for i, chunk_text in enumerate(text_chunks):
        chunk_id = hashlib.md5(
            f"{filename}_{i}_{chunk_text[:50]}".encode()
        ).hexdigest()[:12]

        chunks.append(Chunk(
            id=chunk_id,
            text=chunk_text,
            metadata={
                "source": filename,
                "chunk_index": i,
                **meta
            }
        ))

    return chunks


def load_and_chunk_all() -> List[Chunk]:
    """Charge tous les fichiers texte et les decoupe."""
    all_chunks = []

    print(f"\n[DIR] Dossier source : {RAG_DATA_DIR}")

    for filename, meta in DOCUMENTS_META.items():
        filepath = RAG_DATA_DIR / filename
        if filepath.exists():
            print(f"[FILE] {filename}...", end=" ")
            text = filepath.read_text(encoding='utf-8')
            chunks = create_chunks_from_text(filename, text, meta)
            all_chunks.extend(chunks)
            print(f"OK {len(chunks)} chunks")
        else:
            print(f"[WARN] Non trouve: {filename}")

    return all_chunks


def build_index(chunks: List[Chunk]) -> None:
    """Construit et sauvegarde l'index FAISS."""

    print(f"\n{'='*60}")
    print(f"[BUILD] Construction de l'index FAISS")
    print(f"{'='*60}")

    # Creer le dossier de sortie
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Charger le modele
    print(f"\n[MODEL] Chargement du modele: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Generer les embeddings
    print(f"[EMB] Generation des embeddings pour {len(chunks)} chunks...")
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    # Creer l'index FAISS
    print(f"[FAISS] Creation de l'index FAISS...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))

    # Sauvegarder l'index
    index_path = FAISS_INDEX_DIR / "index.faiss"
    faiss.write_index(index, str(index_path))
    print(f"[OK] Index sauvegarde: {index_path}")

    # Sauvegarder les metadonnees (format compatible avec build_faiss_index.py)
    meta_path = FAISS_INDEX_DIR / "data.pkl"
    with open(meta_path, "wb") as f:
        pickle.dump({"chunks": chunks}, f)
    print(f"[OK] Metadonnees sauvegardees: {meta_path}")

    # Statistiques
    print(f"\n{'='*60}")
    print(f"[STATS] STATISTIQUES")
    print(f"{'='*60}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Dimension embeddings: {dimension}")

    canton_counts = {}
    for c in chunks:
        canton = c.metadata['canton']
        canton_counts[canton] = canton_counts.get(canton, 0) + 1

    print(f"\nPar canton:")
    for canton, count in sorted(canton_counts.items()):
        print(f"  {canton}: {count} chunks")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("SWISS TAX RAG - Build FAISS Index")
    print("="*60)

    # Charger et decouper les documents
    chunks = load_and_chunk_all()

    if not chunks:
        print("\n[ERROR] Aucun document trouve!")
        print(f"   Placez vos fichiers .txt dans: {RAG_DATA_DIR}")
        exit(1)

    # Construire l'index
    build_index(chunks)

    print("\n[DONE] INDEX FAISS CREE AVEC SUCCES!")
    print(f"   L'app Streamlit (build_faiss_index.py) peut maintenant l'utiliser.")
