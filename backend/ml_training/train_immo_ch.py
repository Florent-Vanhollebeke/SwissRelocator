# Train Swiss real estate model (ImmoScout24 data)

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib

# ============================================
# CONFIGURATION DES CHEMINS
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # SwissRelocator/
BACKEND_DIR = PROJECT_ROOT / "backend"

# Données d'entrée (CSV nettoyé par post_clean_immoscout.py)
PROCESSED_DATA_DIR = BACKEND_DIR / "data" / "processed"
INPUT_CSV = PROCESSED_DATA_DIR / "immoscout_suisse_clean_final.csv"

# Modèles de sortie
ML_MODELS_DIR = BACKEND_DIR / "ml_models"

# ============================================
# 1. CHARGEMENT DES DONNÉES
# ============================================

print("="*70)
print("🤖 MACHINE LEARNING - PRÉDICTION PRIX LOCATION BUREAUX SUISSE")
print("="*70)

df = pd.read_csv(INPUT_CSV)

print(f"\n📊 Dataset : {len(df)} lignes × {len(df.columns)} colonnes")

# ============================================
# 2. FEATURE ENGINEERING
# ============================================

print("\n" + "="*70)
print("🔧 FEATURE ENGINEERING")
print("="*70)

# Créer une copie
df_ml = df.copy()

# 2.1 Features géographiques enrichies
print("\n1️⃣  Features géographiques...")

# Distance du centre-ville (approximation avec GPS)
city_centers = {
    'Genève': (46.2044, 6.1432),
    'Zürich': (47.3769, 8.5417),
    'Lausanne': (46.5197, 6.6323),
    'Basel': (47.5596, 7.5886)
}

def calculate_distance_from_center(row):
    """Calculer distance euclidienne du centre-ville"""
    if row['city_normalized'] in city_centers:
        center_lat, center_lon = city_centers[row['city_normalized']]
        lat_diff = row['latitude'] - center_lat
        lon_diff = row['longitude'] - center_lon
        return np.sqrt((lat_diff * 111)**2 + (lon_diff * 85)**2)
    return None

df_ml['distance_centre'] = df_ml.apply(calculate_distance_from_center, axis=1)

# 2.2 Features de surface
print("2️⃣  Features de surface...")
df_ml['surface_log'] = np.log1p(df_ml['surface'])
df_ml['surface_squared'] = df_ml['surface'] ** 2

# 2.3 Features catégorielles
print("3️⃣  Encodage features catégorielles...")

# Ville
df_ml['ville_encoded'] = LabelEncoder().fit_transform(df_ml['city_normalized'])

# Type de bien
df_ml['type_bien_encoded'] = LabelEncoder().fit_transform(df_ml['source_bien_type'])

# Parking (gérer les NaN)
df_ml['has_parking_int'] = df_ml['has_parking'].fillna(False).astype(int)

# Ascenseur (gérer les NaN)
df_ml['has_lift_int'] = df_ml['has_lift'].fillna(False).astype(int)

# 2.4 Features d'étage (GÉRER LES NaN)
print("4️⃣  Features d'étage...")
df_ml['etage_filled'] = df_ml['etage'].fillna(-1)  # -1 = inconnu
df_ml['is_ground_floor'] = (df_ml['etage_filled'] == 0).astype(int)
df_ml['is_high_floor'] = (df_ml['etage_filled'] >= 5).astype(int)
df_ml['etage_unknown'] = (df_ml['etage'].isna()).astype(int)

# 2.5 Features de pièces (GÉRER LES NaN)
print("5️⃣  Features pièces...")
# Imputer avec la médiane par ville et taille de surface
df_ml['pieces_filled'] = df_ml.groupby(['city_normalized', 'categorie_taille'])['pieces'].transform(
    lambda x: x.fillna(x.median())
)
# Si toujours NaN, utiliser médiane globale
df_ml['pieces_filled'] = df_ml['pieces_filled'].fillna(df_ml['pieces'].median())
df_ml['pieces_unknown'] = (df_ml['pieces'].isna()).astype(int)

# 2.6 Interaction features (sans data leakage)
df_ml['surface_ville'] = df_ml['surface'] * df_ml['ville_encoded']
df_ml['surface_distance'] = df_ml['surface'] * df_ml['distance_centre']

print(f"   ✓ {len(df_ml.columns)} features créées")

# ============================================
# 3. SÉLECTION DES FEATURES
# ============================================

print("\n" + "="*70)
print("📋 SÉLECTION DES FEATURES")
print("="*70)

# Features à utiliser pour le ML (SANS data leakage - pas de prix_m2)
features_to_use = [
    # Géographiques
    'latitude', 'longitude', 'distance_centre', 'ville_encoded',

    # Surface
    'surface', 'surface_log', 'surface_squared',

    # Caractéristiques (NaN gérés)
    'pieces_filled', 'pieces_unknown',
    'etage_filled', 'etage_unknown', 'is_ground_floor', 'is_high_floor',
    'type_bien_encoded',

    # Équipements
    'has_parking_int', 'has_lift_int',

    # Interactions (sans prix_m2)
    'surface_ville',
    'surface_distance'
]

# Supprimer lignes avec NaN dans les features CRITIQUES uniquement
critical_features = ['latitude', 'longitude', 'surface', 'price', 'distance_centre']
df_ml_clean = df_ml.dropna(subset=critical_features)

print(f"\n✅ Features sélectionnées : {len(features_to_use)}")
print(f"✅ Dataset après nettoyage NaN critiques : {len(df_ml_clean)} lignes")

# Vérifier qu'il n'y a plus de NaN
nan_counts = df_ml_clean[features_to_use].isna().sum()
if nan_counts.sum() > 0:
    print(f"\n⚠️  NaN restants :")
    print(nan_counts[nan_counts > 0])
    # Remplir les derniers NaN avec 0
    df_ml_clean[features_to_use] = df_ml_clean[features_to_use].fillna(0)
    print(f"✅ NaN remplacés par 0")
else:
    print(f"✅ Aucun NaN dans les features")

# Préparer X et y
X = df_ml_clean[features_to_use]
y = df_ml_clean['price']

print(f"\n📊 Distribution target (price) :")
print(y.describe())

# ============================================
# 4. SPLIT TRAIN/TEST
# ============================================

print("\n" + "="*70)
print("✂️  SPLIT TRAIN/TEST")
print("="*70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\n✅ Train : {len(X_train)} lignes")
print(f"✅ Test : {len(X_test)} lignes")

# ============================================
# 5. NORMALISATION
# ============================================

print("\n" + "="*70)
print("📏 NORMALISATION DES FEATURES")
print("="*70)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✅ Features normalisées")

# ============================================
# 6. ENTRAÎNEMENT DE PLUSIEURS MODÈLES
# ============================================

print("\n" + "="*70)
print("🤖 ENTRAÎNEMENT DES MODÈLES")
print("="*70)

models = {
    'Ridge': Ridge(alpha=10.0),
    'Lasso': Lasso(alpha=10.0, max_iter=5000),
    'Random Forest': RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        random_state=42
    ),
    'XGBoost': xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        reg_alpha=1.0,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1
    )
}

results = {}

for name, model in models.items():
    print(f"\n🔄 Entraînement {name}...")
    
    # Entraîner
    if name in ['Ridge', 'Lasso']:
        model.fit(X_train_scaled, y_train)
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
    
    # Métriques
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    results[name] = {
        'model': model,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'y_pred_test': y_pred_test
    }
    
    print(f"   ✓ R² Train: {train_r2:.4f} | R² Test: {test_r2:.4f}")
    print(f"   ✓ MAE Test: {test_mae:.0f} CHF | RMSE Test: {test_rmse:.0f} CHF")

# ============================================
# 7. COMPARAISON DES MODÈLES
# ============================================

print("\n" + "="*70)
print("📊 COMPARAISON DES MODÈLES")
print("="*70)

comparison_df = pd.DataFrame({
    'Modèle': list(results.keys()),
    'R² Train': [results[m]['train_r2'] for m in results],
    'R² Test': [results[m]['test_r2'] for m in results],
    'MAE Test (CHF)': [results[m]['test_mae'] for m in results],
    'RMSE Test (CHF)': [results[m]['test_rmse'] for m in results]
})

comparison_df = comparison_df.sort_values('R² Test', ascending=False)
print("\n" + comparison_df.to_string(index=False))

# Meilleur modèle
best_model_name = comparison_df.iloc[0]['Modèle']
best_model = results[best_model_name]['model']

print(f"\n🏆 MEILLEUR MODÈLE : {best_model_name}")
print(f"   • R² Test : {results[best_model_name]['test_r2']:.4f}")
print(f"   • MAE Test : {results[best_model_name]['test_mae']:.0f} CHF")

# ============================================
# 8. FEATURE IMPORTANCE (pour modèles tree-based)
# ============================================

if best_model_name in ['Random Forest', 'Gradient Boosting', 'XGBoost']:
    print("\n" + "="*70)
    print("🎯 IMPORTANCE DES FEATURES")
    print("="*70)
    
    importances = best_model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'Feature': features_to_use,
        'Importance': importances
    }).sort_values('Importance', ascending=False)
    
    print("\nTop 10 features :")
    print(feature_importance_df.head(10).to_string(index=False))

# ============================================
# 9. ANALYSE DES ERREURS
# ============================================

print("\n" + "="*70)
print("🔍 ANALYSE DES ERREURS")
print("="*70)

y_pred_best = results[best_model_name]['y_pred_test']
errors = y_test - y_pred_best
errors_pct = (errors / y_test) * 100

print(f"\n📊 Distribution des erreurs :")
print(f"   • Erreur moyenne : {errors.mean():.0f} CHF ({errors_pct.mean():.1f}%)")
print(f"   • Erreur médiane : {errors.median():.0f} CHF ({errors_pct.median():.1f}%)")
print(f"   • Erreur absolue médiane : {np.abs(errors).median():.0f} CHF")

# Erreurs par ville
print(f"\n🏙️  Erreurs par ville (MAE) :")
test_df = df_ml_clean.loc[y_test.index].copy()
test_df['error_abs'] = np.abs(errors)
errors_by_city = test_df.groupby('city_normalized')['error_abs'].mean().sort_values(ascending=False)
print(errors_by_city)

# ============================================
# 10. PRÉDICTIONS D'EXEMPLE
# ============================================

print("\n" + "="*70)
print("🎯 EXEMPLES DE PRÉDICTIONS")
print("="*70)

# Prendre 10 exemples aléatoires du test set
sample_indices = np.random.choice(len(y_test), min(10, len(y_test)), replace=False)

print(f"\n{'Ville':<15} {'Surface':<10} {'Réel':<12} {'Prédit':<12} {'Erreur':<10}")
print("-" * 70)

for idx in sample_indices:
    original_idx = y_test.index[idx]
    ville = df_ml_clean.loc[original_idx, 'city_normalized']
    surface = df_ml_clean.loc[original_idx, 'surface']
    reel = y_test.iloc[idx]
    predit = y_pred_best[idx]
    erreur = predit - reel
    
    print(f"{ville:<15} {surface:<10.0f} {reel:<12.0f} {predit:<12.0f} {erreur:+10.0f}")

# ============================================
# 11. SAUVEGARDER LE MEILLEUR MODÈLE
# ============================================

print("\n" + "="*70)
print("💾 SAUVEGARDE DU MODÈLE")
print("="*70)

# Créer le dossier ml_models s'il n'existe pas
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Sauvegarder le modèle et le scaler
model_path = ML_MODELS_DIR / "immo_ch_model.pkl"
scaler_path = ML_MODELS_DIR / "immo_ch_scaler.pkl"

joblib.dump(best_model, model_path)
joblib.dump(scaler, scaler_path)

print(f"\n✅ Modèle sauvegardé : {model_path}")
print(f"✅ Scaler sauvegardé : {scaler_path}")

# Sauvegarder les features utilisées
features_path = ML_MODELS_DIR / "immo_ch_features.txt"
with open(features_path, 'w') as f:
    f.write('\n'.join(features_to_use))
print(f"✅ Features sauvegardées : {features_path}")

print("\n🎉 ENTRAÎNEMENT TERMINÉ !")