# ============================================
# SwissRelocator - API Endpoint Prediction Loyers
# backend/app/predict_rent_router.py
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

router = APIRouter(prefix="/api/v1", tags=["ML Predictions"])

# ============================================
# CONFIGURATION
# ============================================

# Chemins des modeles (relatifs au backend)
ML_MODELS_DIR = Path(__file__).parent.parent / "ml_models"
MODEL_PATH = ML_MODELS_DIR / "immo_ch_model.pkl"
SCALER_PATH = ML_MODELS_DIR / "immo_ch_scaler.pkl"
FEATURES_PATH = ML_MODELS_DIR / "immo_ch_features.txt"

# Centres-villes pour calcul de distance
CITY_CENTERS = {
    'Geneve': {'lat': 46.2044, 'lon': 6.1432, 'encoded': 2},
    'Lausanne': {'lat': 46.5197, 'lon': 6.6323, 'encoded': 3},
    'Zurich': {'lat': 47.3769, 'lon': 8.5417, 'encoded': 4},
    'Basel': {'lat': 47.5596, 'lon': 7.5886, 'encoded': 0},
}

# Mapping noms de ville (FR/DE/EN -> normalized)
CITY_NORMALIZATION = {
    'geneve': 'Geneve', 'genève': 'Geneve', 'geneva': 'Geneve', 'genf': 'Geneve',
    'lausanne': 'Lausanne',
    'zurich': 'Zurich', 'zürich': 'Zurich',
    'basel': 'Basel', 'bale': 'Basel', 'bâle': 'Basel', 'basle': 'Basel',
}

# ============================================
# CHARGEMENT DU MODELE (au demarrage)
# ============================================

model = None
scaler = None
features_list = None


def load_model():
    """Charge le modele ML et le scaler au demarrage"""
    global model, scaler, features_list

    try:
        if MODEL_PATH.exists():
            model = joblib.load(MODEL_PATH)
            print(f"[ML] Modele charge: {MODEL_PATH}")
        else:
            print(f"[ML] Modele non trouve: {MODEL_PATH}")

        if SCALER_PATH.exists():
            scaler = joblib.load(SCALER_PATH)
            print(f"[ML] Scaler charge: {SCALER_PATH}")

        if FEATURES_PATH.exists():
            with open(FEATURES_PATH, 'r') as f:
                features_list = f.read().strip().split('\n')
            print(f"[ML] Features chargees: {len(features_list)} features")

    except Exception as e:
        print(f"[ML] Erreur chargement modele: {e}")


# Charger au import du module
load_model()


# ============================================
# SCHEMAS PYDANTIC
# ============================================

class PredictRentRequest(BaseModel):
    """Requete de prediction de loyer"""

    city: str = Field(
        ...,
        description="Ville suisse cible (Geneve, Lausanne, Zurich, Basel)"
    )
    surface: float = Field(
        ...,
        gt=5,
        lt=10000,
        description="Surface en m2"
    )
    latitude: Optional[float] = Field(
        None,
        ge=45.5,
        le=48.0,
        description="Latitude GPS (optionnel, centre-ville par defaut)"
    )
    longitude: Optional[float] = Field(
        None,
        ge=5.5,
        le=10.5,
        description="Longitude GPS (optionnel, centre-ville par defaut)"
    )
    pieces: Optional[float] = Field(
        None,
        ge=1,
        le=50,
        description="Nombre de pieces (optionnel)"
    )
    etage: Optional[int] = Field(
        None,
        ge=-1,
        le=50,
        description="Etage (-1=sous-sol, 0=RDC, optionnel)"
    )
    has_parking: bool = Field(
        False,
        description="Place de parking incluse"
    )
    has_lift: bool = Field(
        False,
        description="Ascenseur dans l'immeuble"
    )
    property_type: Literal['bureau', 'commercial'] = Field(
        'bureau',
        description="Type de bien"
    )

    @field_validator('city')
    @classmethod
    def normalize_city(cls, v):
        """Normalise les noms de ville"""
        v_lower = v.lower().strip()
        normalized = CITY_NORMALIZATION.get(v_lower)
        if normalized is None:
            raise ValueError(f"Ville non supportee: {v}. Villes valides: Geneve, Lausanne, Zurich, Basel")
        return normalized


class PredictRentResponse(BaseModel):
    """Reponse de prediction de loyer"""

    predicted_rent_chf: float = Field(..., description="Loyer predit en CHF/mois")
    predicted_rent_eur: float = Field(..., description="Loyer predit en EUR/mois (taux 0.92)")
    price_per_m2_chf: float = Field(..., description="Prix au m2 en CHF")
    confidence_range: dict = Field(..., description="Fourchette de confiance (+/-MAE)")
    city: str = Field(..., description="Ville")
    surface: float = Field(..., description="Surface en m2")
    model_info: dict = Field(..., description="Informations sur le modele")


class ModelInfoResponse(BaseModel):
    """Informations sur le modele ML"""

    model_type: str
    r2_score: float
    mae_chf: float
    features_count: int
    features: list
    supported_cities: list
    last_trained: str


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def calculate_distance_from_center(lat: float, lon: float, city: str) -> float:
    """Calcule la distance euclidienne du centre-ville en km"""
    if city not in CITY_CENTERS:
        return 0.0

    center = CITY_CENTERS[city]
    lat_diff = lat - center['lat']
    lon_diff = lon - center['lon']

    # Conversion approximative en km
    return np.sqrt((lat_diff * 111)**2 + (lon_diff * 85)**2)


def prepare_features(request: PredictRentRequest) -> pd.DataFrame:
    """
    Prepare le vecteur de features pour la prediction.

    Features (18 au total, SANS data leakage):
    - latitude, longitude, distance_centre, ville_encoded
    - surface, surface_log, surface_squared
    - pieces_filled, pieces_unknown
    - etage_filled, etage_unknown, is_ground_floor, is_high_floor
    - type_bien_encoded
    - has_parking_int, has_lift_int
    - surface_ville, surface_distance
    """

    city = request.city

    # Coordonnees (defaut = centre-ville)
    lat = request.latitude or CITY_CENTERS[city]['lat']
    lon = request.longitude or CITY_CENTERS[city]['lon']

    # Distance du centre
    distance_centre = calculate_distance_from_center(lat, lon, city)

    # Encodage ville (Basel=0, Centre=1, Geneve=2, Lausanne=3, Zurich=4)
    ville_encoded = CITY_CENTERS[city]['encoded']

    # Surface features
    surface = request.surface
    surface_log = np.log1p(surface)
    surface_squared = surface ** 2

    # Pieces (estimation si non fourni: ~25m2 par piece pour bureaux)
    pieces_filled = request.pieces if request.pieces is not None else max(1, surface / 25)
    pieces_unknown = 0 if request.pieces is not None else 1

    # Etage
    etage_filled = request.etage if request.etage is not None else -1
    etage_unknown = 0 if request.etage is not None else 1
    is_ground_floor = 1 if request.etage == 0 else 0
    is_high_floor = 1 if request.etage is not None and request.etage >= 5 else 0

    # Type de bien
    type_bien_encoded = 0 if request.property_type == 'bureau' else 1

    # Equipements
    has_parking_int = 1 if request.has_parking else 0
    has_lift_int = 1 if request.has_lift else 0

    # Interaction features (SANS data leakage - pas de prix_m2)
    surface_ville = surface * ville_encoded
    surface_distance = surface * distance_centre

    # Construire le DataFrame avec les features dans l'ORDRE du modele
    features = {
        'latitude': lat,
        'longitude': lon,
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
        'surface_ville': surface_ville,
        'surface_distance': surface_distance
    }

    return pd.DataFrame([features])


# ============================================
# ENDPOINTS
# ============================================

@router.post("/predict-rent", response_model=PredictRentResponse)
async def predict_rent(request: PredictRentRequest):
    """
    Predit le loyer mensuel d'un bien immobilier commercial en Suisse.

    Le modele est entraine sur des donnees ImmoScout24 (bureaux, commerces).

    **Villes supportees:** Geneve, Lausanne, Zurich, Basel

    **Precision du modele:** R2 = 0.763, MAE = 1425 CHF
    """

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Modele ML non disponible. Veuillez reessayer plus tard."
        )

    try:
        # Preparer les features
        features_df = prepare_features(request)

        # Prediction
        predicted_rent = float(model.predict(features_df)[0])

        # S'assurer que le loyer est positif
        predicted_rent = max(predicted_rent, 0.0)

        # Calculs derives
        price_per_m2 = predicted_rent / request.surface
        predicted_rent_eur = predicted_rent * 0.92  # Taux CHF/EUR approximatif

        # Fourchette de confiance (+/-MAE du modele)
        mae = 1425  # MAE du modele XGBoost sans data leakage

        return PredictRentResponse(
            predicted_rent_chf=round(predicted_rent, 2),
            predicted_rent_eur=round(predicted_rent_eur, 2),
            price_per_m2_chf=round(price_per_m2, 2),
            confidence_range={
                "min_chf": round(max(0, predicted_rent - mae), 2),
                "max_chf": round(predicted_rent + mae, 2),
                "mae_chf": mae
            },
            city=request.city,
            surface=request.surface,
            model_info={
                "model_type": "XGBoost Regressor",
                "r2_score": 0.763,
                "training_data": "ImmoScout24 Suisse",
                "last_updated": "2025-12"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de prediction: {str(e)}"
        )


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Retourne les informations sur le modele ML de prediction de loyers.
    """

    return ModelInfoResponse(
        model_type="XGBoost Regressor",
        r2_score=0.763,
        mae_chf=1425,
        features_count=len(features_list) if features_list else 18,
        features=features_list or [],
        supported_cities=list(CITY_CENTERS.keys()),
        last_trained="2025-12"
    )


@router.get("/health")
async def health_check():
    """Verifie l'etat de l'API ML"""

    return {
        "status": "healthy" if model is not None else "degraded",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "features_loaded": features_list is not None
    }
