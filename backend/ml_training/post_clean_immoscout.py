import pandas as pd
from pathlib import Path

# ============================================
# CONFIGURATION DES CHEMINS
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # SwissRelocator/
BACKEND_DIR = PROJECT_ROOT / "backend"
PROCESSED_DATA_DIR = BACKEND_DIR / "data" / "processed"

# Charger le CSV
df = pd.read_csv(PROCESSED_DATA_DIR / "immoscout_suisse_location.csv")

print(f"Lignes initiales : {len(df)}")

# ============================================
# 1. NORMALISER LES NOMS DE VILLES
# ============================================

def normalize_city(city):
    """Normaliser les variantes de noms de villes"""
    city_lower = str(city).lower().strip()
    
    # Genève
    if city_lower in ['genève', 'geneva', 'genf', 'geneve', 'ginevra']:
        return 'Genève'
    
    # Zurich
    if city_lower in ['zürich', 'zurich']:
        return 'Zürich'
    
    # Lausanne
    if city_lower == 'lausanne':
        return 'Lausanne'
    
    # Quartiers de Genève à normaliser
    geneva_neighborhoods = ['les acacias', 'cointrin', 'champel', 'plainpalais', 
                            'le grand-saconnex', 'le petit-saconnex', 'eaux-vives-lac']
    if city_lower in geneva_neighborhoods:
        return 'Genève'
    
    # Quartiers de Zürich
    zurich_neighborhoods = ['oerlikon', 'seebach', 'leimbach zh']
    if city_lower in zurich_neighborhoods:
        return 'Zürich'

    # Bâle / Basel
    if city_lower in ['bâle', 'basel', 'basle', 'bale']:
        return 'Basel'

    # Quartiers de Basel
    basel_neighborhoods = ['riehen', 'bettingen', 'birsfelden', 'muttenz', 'pratteln', 'allschwil', 'binningen']
    if city_lower in basel_neighborhoods:
        return 'Basel'

    # Par défaut, capitaliser proprement
    return city.strip().title()

df['city_normalized'] = df['city'].apply(normalize_city)

print(f"\n✅ Villes normalisées :")
print(df['city_normalized'].value_counts())

# ============================================
# 2. SUPPRIMER PRIX/M² ABERRANTS
# ============================================

# Prix/m² réalistes en Suisse : 10-100 CHF/m² pour location bureaux
avant = len(df)
df = df[(df['prix_m2'] >= 5) & (df['prix_m2'] <= 150)]
print(f"\n✅ Prix/m² aberrants supprimés : {avant - len(df)} lignes → {len(df)} restantes")

# ============================================
# 3. SUPPRIMER LIGNES SANS CODE POSTAL
# ============================================

avant = len(df)
df = df[df['postal_code'].notna()]
print(f"✅ Lignes sans postal_code supprimées : {avant - len(df)} → {len(df)} restantes")

# ============================================
# 4. RECRÉER LES CATÉGORIES
# ============================================

# Prix/m²
df['categorie_prix_m2'] = pd.cut(
    df['prix_m2'],
    bins=[0, 15, 25, 40, 60, 200],
    labels=['Très bon marché (<15)', 'Bon marché (15-25)', 'Moyen (25-40)', 
            'Cher (40-60)', 'Très cher (>60)']
)

# ============================================
# 5. STATISTIQUES FINALES
# ============================================

print("\n" + "="*70)
print("📊 DATASET FINAL NETTOYÉ")
print("="*70)

print(f"\n📏 Dimensions : {len(df)} lignes")

print(f"\n🏙️  Villes principales :")
print(df['city_normalized'].value_counts())

print(f"\n💰 Prix médian par ville :")
print(df.groupby('city_normalized')['price'].median().sort_values(ascending=False))

print(f"\n📐 Surface médiane par ville :")
print(df.groupby('city_normalized')['surface'].median().sort_values(ascending=False))

print(f"\n💵 Prix/m² médian par ville :")
prix_m2_ville = df.groupby('city_normalized')['prix_m2'].median().sort_values(ascending=False)
print(prix_m2_ville)

print(f"\n🏢 Distribution tailles :")
print(df['categorie_taille'].value_counts().sort_index())

print(f"\n💰 Distribution prix/m² :")
print(df['categorie_prix_m2'].value_counts().sort_index())

# ============================================
# 6. EXPORT FINAL
# ============================================

output_file = PROCESSED_DATA_DIR / "immoscout_suisse_clean_final.csv"
df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n✅ Dataset final exporté : {output_file}")
print(f"📊 {len(df)} lignes × {len(df.columns)} colonnes")

print("\n🎉 NETTOYAGE TERMINÉ !")