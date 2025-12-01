import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================
# CONFIGURATION DES CHEMINS
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # SwissRelocator/
BACKEND_DIR = PROJECT_ROOT / "backend"
ML_MODELS_DIR = BACKEND_DIR / "ml_models"

# ============================================
# FONCTION DE PRÉDICTION COMPLÈTE
# ============================================

def predire_prix_bureau(ville, surface, latitude, longitude,
                        pieces=None, etage=None,
                        has_parking=False, has_lift=False,
                        type_bien='Bureau'):
    """
    Prédire le prix de location d'un bureau en Suisse

    Paramètres:
    -----------
    ville : str
        'Genève', 'Zürich' ou 'Lausanne'
    surface : float
        Surface en m²
    latitude : float
        Latitude GPS
    longitude : float
        Longitude GPS
    pieces : int, optional
        Nombre de pièces (si None, valeur par défaut = 4)
    etage : int, optional
        Numéro d'étage (0 = RDC, si None = inconnu)
    has_parking : bool
        Place de parking incluse
    has_lift : bool
        Ascenseur présent
    type_bien : str
        'Bureau' ou 'Commercial'

    Returns:
    --------
    float : Prix estimé en CHF/mois
    """

    # Charger le modèle
    model = joblib.load(ML_MODELS_DIR / "immo_ch_model.pkl")
    
    # Calculer distance du centre
    city_centers = {
        'Genève': (46.2044, 6.1432),
        'Zürich': (47.3769, 8.5417),
        'Lausanne': (46.5197, 6.6323)
    }
    center_lat, center_lon = city_centers[ville]
    lat_diff = latitude - center_lat
    lon_diff = longitude - center_lon
    distance_centre = np.sqrt((lat_diff * 111)**2 + (lon_diff * 85)**2)
    
    # Surface transformée
    surface_log = np.log1p(surface)
    surface_squared = surface ** 2
    
    # Encodages
    ville_mapping = {'Centre': 0, 'Genève': 1, 'Lausanne': 2, 'Zürich': 3}
    ville_encoded = ville_mapping[ville]
    type_bien_encoded = 0 if type_bien == 'Bureau' else 1
    
    # Features pièces
    pieces_filled = pieces if pieces is not None else 4.0
    pieces_unknown = 0 if pieces is not None else 1
    
    # Features étage
    etage_filled = etage if etage is not None else -1
    is_ground_floor = 1 if etage == 0 else 0
    is_high_floor = 1 if etage >= 5 else 0
    etage_unknown = 0 if etage is not None else 1
    
    # Équipements
    has_parking_int = 1 if has_parking else 0
    has_lift_int = 1 if has_lift else 0
    
    # Premium (approximation par défaut)
    is_premium_area = 0
    
    # Interactions
    surface_ville = surface * ville_encoded
    prix_m2_distance = 30 * distance_centre  # Approximation
    
    # Créer le vecteur de features (ORDRE IMPORTANT !)
    features = {
        'latitude': latitude,
        'longitude': longitude,
        'distance_centre': distance_centre,
        'ville_encoded': ville_encoded,
        'surface': surface,
        'surface_log': surface_log,
        'surface_squared': surface_squared,
        'pieces_filled': pieces_filled,
        'pieces_unknown': pieces_unknown,
        'etage_filled': etage_filled,
        'etage_unknown': etage_unknown,
        'is_ground_floor': is_ground_floor,
        'is_high_floor': is_high_floor,
        'type_bien_encoded': type_bien_encoded,
        'has_parking_int': has_parking_int,
        'has_lift_int': has_lift_int,
        'is_premium_area': is_premium_area,
        'surface_ville': surface_ville,
        'prix_m2_distance': prix_m2_distance
    }
    
    df_pred = pd.DataFrame([features])
    prix = model.predict(df_pred)[0]
    
    return prix

# ============================================
# EXEMPLES D'UTILISATION
# ============================================

if __name__ == "__main__":
    
    print("="*70)
    print("🏢 PRÉDICTIONS DE PRIX - BUREAUX SUISSE")
    print("="*70)
    
    # Exemple 1 : Bureau Genève centre
    print("\n1️⃣  Bureau Genève centre")
    print("   📐 100m², 4 pièces, 3e étage, parking, ascenseur")
    prix1 = predire_prix_bureau(
        ville='Genève',
        surface=100,
        latitude=46.2044,
        longitude=6.1432,
        pieces=4,
        etage=3,
        has_parking=True,
        has_lift=True
    )
    print(f"   💰 Prix estimé : {prix1:.0f} CHF/mois ({prix1/100:.2f} CHF/m²)")
    
    # Exemple 2 : Petit bureau Zürich périphérie
    print("\n2️⃣  Bureau Zürich périphérie")
    print("   📐 50m², 2 pièces, 1er étage, sans parking")
    prix2 = predire_prix_bureau(
        ville='Zürich',
        surface=50,
        latitude=47.40,  # Plus au nord
        longitude=8.55,
        pieces=2,
        etage=1,
        has_parking=False,
        has_lift=False
    )
    print(f"   💰 Prix estimé : {prix2:.0f} CHF/mois ({prix2/50:.2f} CHF/m²)")
    
    # Exemple 3 : Local commercial Lausanne
    print("\n3️⃣  Local commercial Lausanne centre")
    print("   📐 200m², 8 pièces, RDC, parking")
    prix3 = predire_prix_bureau(
        ville='Lausanne',
        surface=200,
        latitude=46.5197,
        longitude=6.6323,
        pieces=8,
        etage=0,
        has_parking=True,
        has_lift=False,
        type_bien='Commercial'
    )
    print(f"   💰 Prix estimé : {prix3:.0f} CHF/mois ({prix3/200:.2f} CHF/m²)")
    
    # Exemple 4 : Grand bureau Zürich centre
    print("\n4️⃣  Grand bureau Zürich centre")
    print("   📐 250m², 10 pièces, 7e étage, parking, ascenseur")
    prix4 = predire_prix_bureau(
        ville='Zürich',
        surface=250,
        latitude=47.3769,
        longitude=8.5417,
        pieces=10,
        etage=7,
        has_parking=True,
        has_lift=True
    )
    print(f"   💰 Prix estimé : {prix4:.0f} CHF/mois ({prix4/250:.2f} CHF/m²)")
    
    # Exemple 5 : Petit bureau sans infos (valeurs par défaut)
    print("\n5️⃣  Petit bureau Genève (infos minimales)")
    print("   📐 30m², infos manquantes")
    prix5 = predire_prix_bureau(
        ville='Genève',
        surface=30,
        latitude=46.20,
        longitude=6.15
        # pieces, etage non fournis → valeurs par défaut
    )
    print(f"   💰 Prix estimé : {prix5:.0f} CHF/mois ({prix5/30:.2f} CHF/m²)")
    
    print("\n" + "="*70)