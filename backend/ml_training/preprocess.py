# Data preprocessing and cleaning

import pandas as pd
import json
import os
from pathlib import Path
import re

# ============================================
# CONFIGURATION
# ============================================

# Chemins relatifs au projet
PROJECT_ROOT = Path(__file__).parent.parent.parent  # SwissRelocator/
BACKEND_DIR = PROJECT_ROOT / "backend"

# Données brutes (JSON ImmoScout)
RAW_DATA_DIR = BACKEND_DIR / "data" / "raw" / "immoscout"

# Données nettoyées (CSV)
PROCESSED_DATA_DIR = BACKEND_DIR / "data" / "processed"

# Configuration scraping
VILLES = ["Genève", "Lausanne", "Zurich"]
TYPES_TRANSACTION = ["Location", "Vente"]
TYPES_BIEN = ["Bureau", "Commercial"]

# ============================================
# FONCTION DE CHARGEMENT RÉCURSIF
# ============================================

def load_all_json_files(base_dir, villes, types_transaction, types_bien):
    """
    Charge tous les fichiers JSON depuis l'arborescence complète
    """
    
    all_data = []
    
    print("="*70)
    print("🔍 CHARGEMENT DES DONNÉES IMMOSCOUT24")
    print("="*70)
    print(f"\n📂 Répertoire de base : {base_dir}")
    print(f"🏙️  Villes : {', '.join(villes)}")
    print(f"💼 Types de transaction : {', '.join(types_transaction)}")
    print(f"🏢 Types de bien : {', '.join(types_bien)}")
    
    # Parcourir toute l'arborescence
    for transaction_type in types_transaction:
        for bien_type in types_bien:
            for ville in villes:
                
                # Construire le chemin
                folder_path = base_dir / transaction_type / bien_type / ville
                
                if not folder_path.exists():
                    print(f"\n⚠️  Dossier non trouvé : {folder_path}")
                    continue
                
                print(f"\n📂 {transaction_type}/{bien_type}/{ville}")
                
                # Trouver tous les fichiers JSON
                json_files = list(folder_path.glob("*.json"))
                
                if not json_files:
                    print(f"   ❌ Aucun fichier JSON")
                    continue
                
                print(f"   ✓ {len(json_files)} fichier(s) JSON trouvé(s)")
                
                # Charger chaque fichier
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # Ajouter métadonnées
                            if isinstance(data, list):
                                for item in data:
                                    item['source_ville'] = ville
                                    item['source_transaction'] = transaction_type
                                    item['source_bien_type'] = bien_type
                                    item['source_file'] = json_file.name
                                    all_data.append(item)
                            elif isinstance(data, dict):
                                data['source_ville'] = ville
                                data['source_transaction'] = transaction_type
                                data['source_bien_type'] = bien_type
                                data['source_file'] = json_file.name
                                all_data.append(data)
                                
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Erreur JSON dans {json_file.name}: {e}")
                    except Exception as e:
                        print(f"   ⚠️  Erreur lecture {json_file.name}: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ TOTAL ANNONCES CHARGÉES : {len(all_data):,}")
    print(f"{'='*70}")
    
    return all_data

# ============================================
# FONCTION DE NETTOYAGE
# ============================================

def clean_immoscout_data(all_data):
    """
    Nettoie et structure les données ImmoscoutCH
    """
    
    if len(all_data) == 0:
        print("\n❌ Aucune donnée à nettoyer !")
        return None
    
    print("\n" + "="*70)
    print("🧹 NETTOYAGE DES DONNÉES")
    print("="*70)
    
    cleaned_records = []
    errors = []
    
    for idx, item in enumerate(all_data):
        try:
            # ============================================
            # EXTRACTION GPS
            # ============================================
            gps = item.get('gps', '').split(',')
            latitude = float(gps[0].strip()) if len(gps) > 0 and gps[0] else None
            longitude = float(gps[1].strip()) if len(gps) > 1 and gps[1] else None
            
            # ============================================
            # EXTRACTION PRIX
            # ============================================
            # Gérer location (priceNet) et vente (totalPrice ou priceNet)
            price_raw = None
            if item.get('source_transaction') == 'Location':
                price_raw = item.get('priceNet', '')
            else:  # Vente
                price_raw = item.get('totalPrice') or item.get('priceNet', '')
            
            price = None
            if price_raw:
                # "CHF 3'750.–" ou "CHF 450'000.–" → 3750 ou 450000
                price_clean = re.sub(r"[^\d]", "", str(price_raw))
                price = float(price_clean) if price_clean else None
            
            # ============================================
            # EXTRACTION SURFACE
            # ============================================
            features = item.get('features', {})
            
            # Essayer différentes clés possibles
            surface_raw = (features.get('Surface habitable') or 
                          features.get('Surface utile') or 
                          features.get('Surface') or 
                          item.get('surface'))
            
            surface = None
            if surface_raw:
                # "187 m2" ou "187m²" ou juste "187" → 187
                if isinstance(surface_raw, (int, float)):
                    surface = float(surface_raw)
                else:
                    surface_match = re.search(r'(\d+(?:\.\d+)?)', str(surface_raw))
                    if surface_match:
                        surface = float(surface_match.group(1))
            
            # ============================================
            # EXTRACTION LOCALISATION
            # ============================================
            address = item.get('address', '')
            
            # Extraire code postal et ville de l'adresse
            # "Avenue Rosemont 12, 1208 Genève" → 1208, Genève
            city_match = re.search(r'(\d{4})\s+([A-Za-zéèêàâûôîäöü\s-]+)$', address)
            postal_code = city_match.group(1) if city_match else None
            city = city_match.group(2).strip() if city_match else item.get('source_ville')
            
            # ============================================
            # EXTRACTION AUTRES FEATURES
            # ============================================
            
            # Nombre de pièces
            pieces = features.get("Nombre de pièce(s)") or features.get("Pièces")
            if pieces:
                pieces_match = re.search(r'(\d+(?:\.\d+)?)', str(pieces))
                pieces = float(pieces_match.group(1)) if pieces_match else None
            
            # Étage
            etage = features.get("Etage") or features.get("Étage")
            if etage:
                etage_match = re.search(r'(\d+)', str(etage))
                etage = int(etage_match.group(1)) if etage_match else None
            
            # Type de bien
            property_type = features.get("Type", item.get('source_bien_type', 'Bureau'))
            
            # Disponibilité
            disponibilite = features.get("Disponibilité") or features.get("Disponible dès")
            
            # Features secondaires
            features_secondary = item.get('featuresSecondary', [])
            has_parking = any('parc' in str(f).lower() for f in features_secondary)
            has_lift = any('ascenseur' in str(f).lower() or 'lift' in str(f).lower() for f in features_secondary)
            
            # ============================================
            # CRÉER LE RECORD NETTOYÉ
            # ============================================
            record = {
                # Identifiants
                'id': item.get('id'),
                'url': item.get('url'),
                
                # Localisation
                'city': city,
                'postal_code': postal_code,
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                
                # Prix et surface
                'price': price,
                'surface': surface,
                'prix_m2': price / surface if (price and surface and surface > 0) else None,
                
                # Caractéristiques
                'pieces': pieces,
                'etage': etage,
                'property_type': property_type,
                'disponibilite': disponibilite,
                
                # Équipements
                'has_parking': has_parking,
                'has_lift': has_lift,
                
                # Métadonnées
                'title': item.get('title', '').strip('"'),
                'scraped_at': item.get('scraped_at'),
                'nb_images': len(item.get('images', [])),
                
                # Sources
                'source_ville': item.get('source_ville'),
                'source_transaction': item.get('source_transaction'),
                'source_bien_type': item.get('source_bien_type'),
                'source_file': item.get('source_file')
            }
            
            cleaned_records.append(record)
            
        except Exception as e:
            error_msg = f"Annonce {item.get('id', idx)}: {str(e)}"
            errors.append(error_msg)
            continue
    
    print(f"\n✅ {len(cleaned_records):,} annonces nettoyées")
    
    if errors:
        print(f"⚠️  {len(errors)} erreurs de nettoyage")
        # Afficher les 5 premières erreurs
        for error in errors[:5]:
            print(f"   - {error}")
        if len(errors) > 5:
            print(f"   ... et {len(errors)-5} autres erreurs")
    
    # Créer DataFrame
    df = pd.DataFrame(cleaned_records)
    
    return df

# ============================================
# FONCTION DE FILTRAGE ET VALIDATION
# ============================================

def filter_and_validate(df):
    """
    Filtre et valide les données nettoyées
    """
    
    print("\n" + "="*70)
    print("✅ FILTRAGE ET VALIDATION")
    print("="*70)
    
    lignes_initiales = len(df)
    print(f"\n📊 Lignes initiales : {lignes_initiales:,}")
    
    # 1. Supprimer doublons
    avant = len(df)
    df = df.drop_duplicates(subset=['id'])
    print(f"\n1️⃣  Doublons : {avant - len(df)} supprimés → {len(df):,} lignes")
    
    # 2. Garder seulement lignes avec données essentielles
    avant = len(df)
    df = df.dropna(subset=['price', 'surface', 'city', 'latitude', 'longitude'])
    print(f"2️⃣  Données incomplètes : {avant - len(df)} supprimées → {len(df):,} lignes")
    
    # 3. Filtrer surfaces aberrantes
    avant = len(df)
    df = df[(df['surface'] >= 5) & (df['surface'] <= 5000)]
    print(f"3️⃣  Surfaces aberrantes (<5m² ou >5000m²) : {avant - len(df)} supprimées → {len(df):,} lignes")
    
    # 4. Filtrer prix aberrants (percentiles 0.5% et 99.5%)
    avant = len(df)
    
    # Séparer location et vente pour les outliers
    df_location = df[df['source_transaction'] == 'Location']
    df_vente = df[df['source_transaction'] == 'Vente']
    
    # Filtrer locations
    if len(df_location) > 0:
        q_low = df_location['price'].quantile(0.005)
        q_high = df_location['price'].quantile(0.995)
        df_location = df_location[(df_location['price'] >= q_low) & (df_location['price'] <= q_high)]
    
    # Filtrer ventes
    if len(df_vente) > 0:
        q_low = df_vente['price'].quantile(0.005)
        q_high = df_vente['price'].quantile(0.995)
        df_vente = df_vente[(df_vente['price'] >= q_low) & (df_vente['price'] <= q_high)]
    
    df = pd.concat([df_location, df_vente], ignore_index=True)
    print(f"4️⃣  Outliers prix : {avant - len(df)} supprimés → {len(df):,} lignes")
    
    # 5. Catégoriser les données
    print(f"\n5️⃣  Création des catégories...")
    
    # Catégorie de taille
    df['categorie_taille'] = pd.cut(
        df['surface'],
        bins=[0, 30, 80, 150, 300, 600, 10000],
        labels=['Très petit (<30m²)', 'Petit (30-80m²)', 'Moyen (80-150m²)', 
                'Grand (150-300m²)', 'Très grand (300-600m²)', 'Énorme (>600m²)']
    )
    
    # Catégorie de prix (différente pour location vs vente)
    df['categorie_prix'] = None
    
    # Location
    mask_location = df['source_transaction'] == 'Location'
    df.loc[mask_location, 'categorie_prix'] = pd.cut(
        df.loc[mask_location, 'price'],
        bins=[0, 1000, 2000, 4000, 8000, 1000000],
        labels=['<1000 CHF', '1000-2000 CHF', '2000-4000 CHF', '4000-8000 CHF', '>8000 CHF']
    )
    
    # Vente
    mask_vente = df['source_transaction'] == 'Vente'
    df.loc[mask_vente, 'categorie_prix'] = pd.cut(
        df.loc[mask_vente, 'price'],
        bins=[0, 300000, 600000, 1000000, 2000000, 100000000],
        labels=['<300k CHF', '300-600k CHF', '600k-1M CHF', '1-2M CHF', '>2M CHF']
    )
    
    print(f"   ✓ Catégories créées")
    
    # ============================================
    # STATISTIQUES FINALES
    # ============================================
    
    print("\n" + "="*70)
    print("📊 STATISTIQUES DATASET FINAL")
    print("="*70)
    
    print(f"\n📏 Dimensions : {len(df):,} lignes × {len(df.columns)} colonnes")
    print(f"🎯 Taux de conservation : {len(df)/lignes_initiales*100:.1f}%")
    
    print(f"\n🏙️  RÉPARTITION PAR VILLE :")
    print(df['city'].value_counts())
    
    print(f"\n💼 RÉPARTITION PAR TYPE DE TRANSACTION :")
    print(df['source_transaction'].value_counts())
    
    print(f"\n🏢 RÉPARTITION PAR TYPE DE BIEN :")
    print(df['source_bien_type'].value_counts())
    
    print(f"\n💰 STATISTIQUES PRIX :")
    for transaction in df['source_transaction'].unique():
        df_trans = df[df['source_transaction'] == transaction]
        print(f"\n  {transaction} :")
        print(f"    • Moyenne : {df_trans['price'].mean():,.0f} CHF")
        print(f"    • Médiane : {df_trans['price'].median():,.0f} CHF")
        print(f"    • Min : {df_trans['price'].min():,.0f} CHF")
        print(f"    • Max : {df_trans['price'].max():,.0f} CHF")
    
    print(f"\n📐 STATISTIQUES SURFACE :")
    print(f"  • Moyenne : {df['surface'].mean():.0f}m²")
    print(f"  • Médiane : {df['surface'].median():.0f}m²")
    print(f"  • Min : {df['surface'].min():.0f}m²")
    print(f"  • Max : {df['surface'].max():.0f}m²")
    
    print(f"\n💵 PRIX/M² MÉDIAN PAR VILLE :")
    prix_m2_ville = df.groupby(['city', 'source_transaction'])['prix_m2'].median()
    print(prix_m2_ville)
    
    print(f"\n🏢 DISTRIBUTION PAR TAILLE :")
    print(df['categorie_taille'].value_counts().sort_index())
    
    print("="*70)
    
    return df

# ============================================
# FONCTION PRINCIPALE
# ============================================

def process_immoscout_data():
    """
    Pipeline complet de traitement
    """

    # Créer le dossier processed s'il n'existe pas
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Charger toutes les données
    all_data = load_all_json_files(RAW_DATA_DIR, VILLES, TYPES_TRANSACTION, TYPES_BIEN)

    if not all_data:
        return None

    # 2. Nettoyer
    df = clean_immoscout_data(all_data)

    if df is None or len(df) == 0:
        return None

    # 3. Filtrer et valider
    df_final = filter_and_validate(df)

    # 4. Export
    print("\n" + "="*70)
    print("💾 EXPORT")
    print("="*70)

    output_file = PROCESSED_DATA_DIR / "immoscout_suisse_final.csv"
    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Dataset exporté : {output_file}")
    print(f"📊 {len(df_final):,} lignes × {len(df_final.columns)} colonnes")

    # Export séparé location vs vente
    df_location = df_final[df_final['source_transaction'] == 'Location']
    df_vente = df_final[df_final['source_transaction'] == 'Vente']

    if len(df_location) > 0:
        output_location = PROCESSED_DATA_DIR / "immoscout_suisse_location.csv"
        df_location.to_csv(output_location, index=False, encoding='utf-8-sig')
        print(f"✅ Location exporté : {output_location} ({len(df_location):,} lignes)")

    if len(df_vente) > 0:
        output_vente = PROCESSED_DATA_DIR / "immoscout_suisse_vente.csv"
        df_vente.to_csv(output_vente, index=False, encoding='utf-8-sig')
        print(f"✅ Vente exporté : {output_vente} ({len(df_vente):,} lignes)")

    print("\n🎉 TRAITEMENT TERMINÉ !")

    return df_final

# ============================================
# EXÉCUTION
# ============================================

if __name__ == "__main__":
    df = process_immoscout_data()
    
    if df is not None:
        print("\n📋 APERÇU DES DONNÉES (10 premières lignes) :")
        print(df[['city', 'postal_code', 'price', 'surface', 'prix_m2', 
                  'source_transaction', 'source_bien_type']].head(10))