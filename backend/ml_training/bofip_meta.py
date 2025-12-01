"""
Métadonnées BOFIP pour index_faiss.py
=====================================
Ajoute ces entrées à DOCUMENTS_META dans index_faiss.py
pour que les fichiers BOFIP soient correctement indexés.

USAGE:
    1. Copie ce contenu dans index_faiss.py
    2. Ou importe ce fichier et merge les dictionnaires
"""

BOFIP_DOCUMENTS_META = {
    # === IMPÔT SUR LES SOCIÉTÉS ===
    "bofip_boi_is_base.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - IS Base d'imposition (assiette, charges)",
    },
    "bofip_boi_is_liq.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - IS Liquidation (taux 25%, calcul)",
    },
    
    # === TVA ===
    "bofip_boi_tva_imm.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - TVA Immobilière (livraisons immeubles)",
    },
    "bofip_boi_tva_liq.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - TVA Taux et liquidation (20%, 10%, 5.5%)",
    },
    
    # === PLUS-VALUES IMMOBILIÈRES ===
    "bofip_boi_rfpi_pvi.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - Plus-values immobilières particuliers",
    },
    "bofip_boi_rfpi_pvinr.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - Plus-values immobilières non-résidents",
    },
    
    # === DROITS DE MUTATION ===
    "bofip_boi_enr_dmtoi.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - Droits de mutation immeubles (~5.8%)",
    },
    
    # === CONVENTION FRANCE-SUISSE ===
    "bofip_boi_int_cvb_che.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - Convention fiscale France-Suisse",
    },
    
    # === BIC ===
    "bofip_boi_bic_base.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - BIC Base d'imposition (SCI)",
    },
    
    # === IFI ===
    "bofip_boi_pat_ifi.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - Impôt Fortune Immobilière (seuil 1.3M€)",
    },
    
    # === CHARGES SOCIALES ===
    "bofip_boi_rsa_champ.txt": {
        "canton": "FR",
        "doc_type": "bofip",
        "language": "fr",
        "description": "BOFIP - Traitements et salaires, charges sociales",
    },
}


# Code pour merger avec DOCUMENTS_META existant
def get_merged_meta():
    """
    Retourne les métadonnées mergées (existantes + BOFIP).
    
    Usage dans index_faiss.py:
        from bofip_meta import get_merged_meta
        DOCUMENTS_META = get_merged_meta()
    """
    from index_faiss import DOCUMENTS_META
    merged = DOCUMENTS_META.copy()
    merged.update(BOFIP_DOCUMENTS_META)
    return merged


# Affiche les instructions si exécuté directement
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║          BOFIP Metadata pour Swiss Tax RAG                  ║
╚══════════════════════════════════════════════════════════════╝

Pour intégrer les fichiers BOFIP à ton indexeur FAISS:

OPTION 1: Copier-coller dans index_faiss.py
-------------------------------------------
Ouvre index_faiss.py et ajoute ces entrées dans DOCUMENTS_META:

""")
    
    for filename, meta in BOFIP_DOCUMENTS_META.items():
        print(f'    "{filename}": {{')
        print(f'        "canton": "{meta["canton"]}",')
        print(f'        "doc_type": "{meta["doc_type"]}",')
        print(f'        "language": "{meta["language"]}",')
        print(f'        "description": "{meta["description"]}",')
        print(f'    }},')
    
    print("""

OPTION 2: Import automatique
----------------------------
Modifie index_faiss.py pour charger dynamiquement les métadonnées:

    # Au début de index_faiss.py, après les imports:
    from bofip_meta import BOFIP_DOCUMENTS_META
    
    # Puis merge les dictionnaires:
    DOCUMENTS_META.update(BOFIP_DOCUMENTS_META)

C'est tout ! Après ça, lance:
    python index_faiss.py --index
""")