# 🇨🇭 SWISS TAX SIMULATOR - Spécification Technique Complète

> **Version** : 3.1  
> **Date** : 30 novembre 2025  
> **Auteur** : Florent Vanhollebeke
> **Statut** : Document de pilotage

---

## 📋 Table des matières

1. [Vision Produit](#1-vision-produit)
2. [Architecture Globale](#2-architecture-globale)
3. [Stack Technique](#3-stack-technique)
4. [Modules Backend](#4-modules-backend)
5. [Module Strategic Advisor (CrewAI)](#5-module-strategic-advisor-crewai)
6. [Modules Frontend](#6-modules-frontend)
7. [Modèles de Données](#7-modèles-de-données)
8. [Flux de Données & Privacy](#8-flux-de-données--privacy)
9. [Internationalisation (i18n)](#9-internationalisation-i18n)
10. [Infrastructure & Déploiement](#10-infrastructure--déploiement)
11. [Sécurité & Garde-fous](#11-sécurité--garde-fous)
12. [Sources de Données](#12-sources-de-données)
13. [Roadmap](#13-roadmap)
14. [KPIs & Métriques](#14-kpis--métriques)
15. [Glossaire](#15-glossaire)

---

## 1. Vision Produit

### 1.1 Objectif

Créer un **simulateur d'implantation d'entreprise Franco-Suisse** permettant aux entrepreneurs et décideurs de comparer objectivement les coûts et avantages d'une implantation à :
- 🇫🇷 **Lyon** (France)
- 🇨🇭 **Genève** (Suisse - Canton GE) - Finance, Luxe, Commodities
- 🇨🇭 **Lausanne** (Suisse - Canton VD) - Tech, EPFL, Startups
- 🇨🇭 **Zurich** (Suisse - Canton ZH) - Finance, Tech, Sièges sociaux
- 🇨🇭 **Bâle** (Suisse - Canton BS) - 💊 Pharma (Novartis, Roche)

### 1.2 Proposition de valeur

| Problème | Solution |
|----------|----------|
| Comparaisons fiscales complexes et opaques | Simulation automatisée avec sources officielles |
| Données éparpillées (loyers, salaires, impôts) | Agrégation intelligente multi-sources |
| Outils existants = simples calculateurs | Approche "Business Plan" avec cash-flow |
| Craintes sur la confidentialité des données | Architecture Privacy-First (nLPD/RGPD) |

### 1.3 Cibles utilisateurs

| Persona | Besoin | Fréquence d'usage |
|---------|--------|-------------------|
| **Entrepreneur français** | Évaluer une implantation en Suisse | Ponctuel (décision stratégique) |
| **Fiduciaire/Expert-comptable** | Conseiller ses clients | Récurrent (outil métier) |
| **Startup internationale** | Choisir entre plusieurs localisations | Ponctuel |
| **Recruteur tech suisse** | Évaluer les compétences du candidat (Florent) | Démo unique 😉 |

### 1.4 Philosophie technique

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRINCIPES DIRECTEURS                         │
├─────────────────────────────────────────────────────────────────┤
│  🔒 Privacy-First    : Données perso jamais envoyées au cloud  │
│  📊 Data-Driven      : ML + RAG, pas de valeurs hardcodées     │
│  🏦 Rigueur Bancaire : Audit logs, traçabilité, sources citées │
│  🌍 Multi-juridique  : Conforme RGPD (FR/UE) et nLPD (Suisse)  │
│  🚀 Production-Ready : Pas un POC, un vrai produit déployable  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Globale

### 2.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              UTILISATEUR                                    │
│                    (Entrepreneur, Expert-comptable)                         │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 14)                               │
│                         Hébergé sur Vercel                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Landing   │  │   Wizard    │  │  Dashboard  │  │  Auth/User  │       │
│  │    Page     │  │ Simulation  │  │  Résultats  │  │   Profile   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    Internationalisation                         │       │
│  │                   (FR 🇫🇷 | DE 🇩🇪 | EN 🇬🇧)                      │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ API REST (JSON)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                                  │
│                         Hébergé sur Railway                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      API GATEWAY & RATE LIMITING                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│         ┌────────────────────────────┼────────────────────────────┐        │
│         ▼                            ▼                            ▼        │
│  ┌─────────────┐          ┌─────────────────┐          ┌─────────────┐    │
│  │  Privacy    │          │    Business     │          │    Data     │    │
│  │Orchestrator │          │   Simulator     │          │  Services   │    │
│  │             │          │                 │          │             │    │
│  │ • Anonymize │          │ • Cash Flow     │          │ • RAG Fiscal│    │
│  │ • PII Detect│          │ • Projections   │          │ • ML Immo   │    │
│  │ • Audit Log │          │ • Comparaisons  │          │ • Salaires  │    │
│  └─────────────┘          └─────────────────┘          └─────────────┘    │
│                                                                             │
└───────────┬─────────────────────┬─────────────────────┬─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────────┐
│   LLM LOCAL       │  │   LLM CLOUD       │  │      DATABASES                │
│   (Ollama)        │  │   (Claude API)    │  │                               │
├───────────────────┤  ├───────────────────┤  ├───────────────────────────────┤
│                   │  │                   │  │                               │
│  Mistral 7B       │  │  Claude Sonnet    │  │  Supabase (PostgreSQL)       │
│                   │  │                   │  │  ├── users                    │
│  Rôles :          │  │  Rôles :          │  │  ├── simulations              │
│  • Anonymisation  │  │  • Données live   │  │  ├── quotas                   │
│  • Synthèse PII   │  │  • Calculs        │  │  └── feedback                 │
│  • Magic Fill     │  │  • Web search     │  │                               │
│                   │  │  • Jurisprudence  │  │  FAISS Index (Vector DB)      │
│                   │  │                   │  │  └── fiscal_knowledge         │
│                   │  │                   │  │                               │
│                   │  │                   │  │  ML Models (Pickle/ONNX)      │
│                   │  │                   │  │  ├── immo_ch_model.pkl        │
│                   │  │                   │  │  └── immo_fr_model.pkl        │
└───────────────────┘  └───────────────────┘  └───────────────────────────────┘
```

### 2.2 Flux de simulation complet

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUX DE SIMULATION                                   │
└─────────────────────────────────────────────────────────────────────────────┘

     ÉTAPE 1                ÉTAPE 2                ÉTAPE 3              ÉTAPE 4
    [INPUT]              [ENRICHMENT]            [COMPUTE]             [OUTPUT]
       │                      │                      │                     │
       ▼                      ▼                      ▼                     ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐      ┌─────────────┐
│  Wizard     │        │  Privacy    │        │  Business   │      │  Dashboard  │
│  Formulaire │───────▶│Orchestrator │───────▶│  Simulator  │─────▶│  + PDF      │
│             │        │             │        │             │      │             │
│ • Identité  │        │ • Anonymise │        │ • Cash Flow │      │ • Graphiques│
│ • Finance   │        │ • Enrichit  │        │ • Compare   │      │ • Tableaux  │
│ • Immo      │        │   (ML/RAG)  │        │ • Projette  │      │ • Export    │
│ • RH        │        │ • Valide    │        │             │      │             │
└─────────────┘        └─────────────┘        └─────────────┘      └─────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │ ML Immo     │   │ RAG Fiscal  │   │ Benchmark   │
     │             │   │             │   │ Salaires    │
     │ Prédit      │   │ Récupère    │   │             │
     │ loyer/m²    │   │ taux IS,    │   │ Estime      │
     │             │   │ charges,    │   │ masse       │
     │             │   │ conventions │   │ salariale   │
     └─────────────┘   └─────────────┘   └─────────────┘
```

---

## 3. Stack Technique

### 3.1 Frontend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Next.js** | 14.x (App Router) | Framework React SSR/SSG |
| **TypeScript** | 5.x | Typage statique |
| **Tailwind CSS** | 3.x | Styling utility-first |
| **shadcn/ui** | Latest | Composants UI accessibles |
| **React Hook Form** | 7.x | Gestion formulaires |
| **Zod** | 3.x | Validation schemas |
| **next-intl** | 3.x | Internationalisation |
| **Recharts** | 2.x | Graphiques interactifs |
| **Lucide React** | Latest | Icônes |

### 3.2 Backend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.11+ | Langage principal |
| **FastAPI** | 0.100+ | Framework API REST |
| **Pydantic** | 2.x | Validation données |
| **SQLAlchemy** | 2.x | ORM (si besoin) |
| **Pandas** | 2.x | Manipulation données |
| **NumPy** | 1.24+ | Calculs numériques |
| **Scikit-learn** | 1.3+ | Modèles ML |
| **FAISS** | 1.7+ | Vector search (RAG) |
| **Sentence-Transformers** | 2.x | Embeddings |
| **Ollama** | Latest | LLM local |
| **Anthropic SDK** | Latest | Claude API |
| **CrewAI** | 0.30+ | Orchestration agents IA |
| **LangChain** | 0.1+ | Tools & integrations LLM |
| **WeasyPrint** | 60+ | Génération PDF |

### 3.3 Infrastructure

| Service | Rôle | Tier |
|---------|------|------|
| **Vercel** | Hosting frontend | Gratuit |
| **Railway** | Hosting backend | ~5-10€/mois |
| **Supabase** | Auth + PostgreSQL + Storage | Gratuit |
| **Claude API** | LLM Cloud | ~10-20€/mois (usage) |
| **GitHub** | Repo + CI/CD | Gratuit |
| **Sentry** | Error tracking | Gratuit (tier dev) |

### 3.4 Outils de développement

| Outil | Rôle |
|-------|------|
| **UV** | Package manager Python (rapide) |
| **pnpm** | Package manager Node.js |
| **Pytest** | Tests unitaires Python |
| **Vitest** | Tests unitaires JS/TS |
| **Ruff** | Linter Python |
| **ESLint** | Linter TypeScript |
| **Prettier** | Formatter |
| **Husky** | Git hooks |

---

## 4. Modules Backend

### 4.1 Vue d'ensemble des modules

```
/backend
├── /app
│   ├── main.py                      # Point d'entrée FastAPI
│   ├── config.py                    # Configuration (env vars)
│   │
│   ├── /api                         # Routes API
│   │   ├── __init__.py
│   │   ├── simulate.py              # POST /api/simulate
│   │   ├── compare.py               # POST /api/compare
│   │   ├── magic_fill.py            # POST /api/extract
│   │   └── health.py                # GET /api/health
│   │
│   ├── /services                    # Logique métier
│   │   ├── __init__.py
│   │   ├── privacy_orchestrator.py  # Anonymisation & flux
│   │   ├── business_simulator.py    # Calculs cash-flow
│   │   ├── rag_fiscal.py            # Recherche vectorielle
│   │   ├── real_estate_predictor.py # ML prédiction loyers
│   │   ├── salary_benchmark.py      # Grilles salaires
│   │   ├── strategic_advisor.py     # 🆕 CrewAI agents (async)
│   │   ├── email_service.py         # 🆕 Envoi PDF par email
│   │   └── pdf_generator.py         # Export rapports
│   │
│   ├── /agents                      # 🆕 Définition agents CrewAI
│   │   ├── __init__.py
│   │   ├── market_scout.py          # Agent analyse marché
│   │   ├── legal_watchdog.py        # Agent veille juridique
│   │   └── chief_editor.py          # Agent rédaction synthèse
│   │
│   ├── /models                      # Schémas Pydantic
│   │   ├── __init__.py
│   │   ├── simulation.py            # Input/Output simulation
│   │   ├── fiscal.py                # Taux, règles fiscales
│   │   └── user.py                  # Utilisateur, quotas
│   │
│   ├── /core                        # Utilitaires
│   │   ├── __init__.py
│   │   ├── pii_detector.py          # Détection données perso
│   │   ├── audit_logger.py          # Logs compliance
│   │   ├── rate_limiter.py          # Quotas API
│   │   └── exceptions.py            # Erreurs custom
│   │
│   └── /data                        # Données statiques
│       ├── fiscal_rates.json        # Taux IS, charges (backup)
│       ├── salary_grids.json        # Grilles salaires
│       └── /faiss_index             # Index vectoriel
│
├── /tests                           # Tests unitaires
│   ├── test_fiscal_engine.py
│   ├── test_pii_detector.py
│   ├── test_cash_flow.py
│   └── test_strategic_advisor.py    # 🆕 Tests agents
│
├── /ml_models                       # Modèles entraînés
│   ├── immo_ch_model.pkl
│   └── immo_fr_model.pkl
│
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### 4.2 Module : Privacy Orchestrator

**Fichier** : `services/privacy_orchestrator.py`

**Responsabilité** : Orchestrer le flux de données en garantissant que les PII (données personnelles) ne quittent jamais l'environnement local.

**Sous-composants** :

| Composant | Rôle |
|-----------|------|
| `PIIDetector` | Détecte emails, téléphones, IBAN, AVS, NIR, etc. (FR + CH) |
| `Anonymizer` | Appelle LLM local pour nettoyer les requêtes |
| `SecureVault` | Stockage RAM temporaire des PII |
| `AuditLogger` | Logs JSON sans PII pour compliance |

**Flux** :
```
Input User → PIIDetector → Vault (RAM) → Anonymizer (Mistral) 
    → Services (RAG/ML/Cloud) → Synthesizer (Mistral) → Output
```

**Patterns PII détectés** :

| Juridiction | Types |
|-------------|-------|
| 🇫🇷 France | NIR (Sécu), Téléphone, IBAN FR, SIREN/SIRET, TVA FR, RCS |
| 🇨🇭 Suisse | AVS/AHV, Téléphone, IBAN CH, IDE/UID, TVA CH, RC |
| 🌍 International | Email, LEI, DUNS, BIC/SWIFT, EORI |

---

### 4.3 Module : Business Simulator

**Fichier** : `services/business_simulator.py`

**Responsabilité** : Calculer les projections financières et comparer les localisations.

**Méthodes principales** :

| Méthode | Description |
|---------|-------------|
| `simulate(params)` | Simulation complète pour une ville |
| `compare(params, villes[])` | Comparaison multi-villes |
| `project_cash_flow(params, horizon)` | Projection sur N années |
| `calculate_break_even(params)` | CA minimum pour rentabilité |

**Formule Cash-Flow** :

```
Net Cash Flow Annuel = 
    Chiffre d'Affaires
  - Masse Salariale Brute
  - Charges Patronales
  - Loyer Annuel
  - Charges Locatives (~15-20% du loyer)
  - Impôt Société
  - Frais Fixes (comptabilité, assurances, banque)
```

**Détail des calculs** :

| Poste | France (Lyon) | Suisse (Genève) | Source |
|-------|---------------|-----------------|--------|
| Charges patronales | ~43-45% du brut | ~15-17% du brut | RAG |
| IS / Impôt bénéfice | 25% (15% PME) | ~14% effectif | RAG |
| Charges locatives | ~15% du loyer | ~18-20% du loyer | Estimation |
| Frais fixes annuels | ~5-8k€ | ~8-12k CHF | Estimation |

---

### 4.4 Module : RAG Fiscal

**Fichier** : `services/rag_fiscal.py`

**Responsabilité** : Recherche sémantique dans la base de connaissances fiscales.

**Architecture** :

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG FISCAL                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Embedding  │    │   FAISS     │    │   Chunks    │        │
│  │   Model     │───▶│   Index     │───▶│   Store     │        │
│  │             │    │             │    │             │        │
│  │ MiniLM-L12  │    │ ~200 vecs   │    │ ~200 texts  │        │
│  │ (384 dims)  │    │             │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Contenu indexé** :

| Source | Type | Chunks |
|--------|------|--------|
| `fiscalite_france_synthese.txt` | Synthèse FR (CGI) | ~30 |
| `feuille_cantonale_ge.txt` | Canton Genève | ~15 |
| `feuille_cantonale_vd.txt` | Canton Vaud | ~15 |
| `feuille_cantonale_zh.txt` | Canton Zurich | ~15 |
| `feuille_cantonale_bs.txt` | Canton Bâle-Ville | ~15 |
| `convention_france_suisse.txt` | Convention bilatérale | ~20 |
| `charges_sociales_comparatif.txt` | Charges FR vs CH | ~10 |

**Paramètres chunking** :
- `chunk_size` : 500 caractères
- `chunk_overlap` : 100 caractères
- `separators` : `["---SECTION:", "\n\n", ". "]`

---

### 4.5 Module : Real Estate Predictor

**Fichier** : `services/real_estate_predictor.py`

**Responsabilité** : Prédire le loyer commercial au m² pour une ville donnée.

**Modèles** :

| Modèle | Pays | Source données | Algorithme | Performance |
|--------|------|----------------|------------|-------------|
| `immo_ch_model.pkl` | 🇨🇭 Suisse | ImmoScout24 (~1200 annonces) | XGBoost/RandomForest | R² = 0.864 |
| `immo_fr_model.pkl` | 🇫🇷 France | BureauxLocaux (à scraper) | XGBoost/RandomForest | R² = TBD |

**Features du modèle** :

| Feature | Type | Description |
|---------|------|-------------|
| `city` | Categorical | Ville (encodée) |
| `district` | Categorical | Quartier/Arrondissement |
| `surface_m2` | Numeric | Surface en m² |
| `property_type` | Categorical | Bureau/Commercial/Mixte |
| `floor` | Numeric | Étage |
| `has_parking` | Boolean | Parking inclus |
| `renovation_year` | Numeric | Année rénovation |

**Output** : `rent_per_m2_monthly` (CHF ou EUR)

---

### 4.6 Module : Salary Benchmark

**Fichier** : `services/salary_benchmark.py`

**Responsabilité** : Estimer les salaires par métier/région si non fournis par l'utilisateur.

**Sources de données** :

| Pays | Source | Granularité |
|------|--------|-------------|
| 🇨🇭 Suisse | OFS (Office Fédéral Statistique) | Canton × Branche × Niveau |
| 🇫🇷 France | INSEE / APEC | Région × Branche × Niveau |

**Structure grille** :

```json
{
  "IT": {
    "developer_junior": {
      "lyon": 38000,
      "geneve": 85000,
      "lausanne": 82000,
      "zurich": 95000,
      "basel": 90000
    },
    "developer_senior": {
      "lyon": 55000,
      "geneve": 110000,
      "lausanne": 105000,
      "zurich": 130000,
      "basel": 120000
    },
    "project_manager": {
      "lyon": 50000,
      "geneve": 100000,
      "lausanne": 95000,
      "zurich": 115000,
      "basel": 110000
    }
  },
  "pharma": {
    "research_scientist": {
      "lyon": 45000,
      "geneve": 95000,
      "lausanne": 90000,
      "zurich": 100000,
      "basel": 110000
    },
    "regulatory_affairs": {
      "lyon": 50000,
      "geneve": 100000,
      "lausanne": 95000,
      "zurich": 105000,
      "basel": 115000
    },
    "quality_manager": {
      "lyon": 55000,
      "geneve": 105000,
      "lausanne": 100000,
      "zurich": 110000,
      "basel": 120000
    }
  },
  "finance": {
    // ...
  }
}
```

**Méthode principale** :

```
estimate_salary(role, city, experience_level) → annual_gross_salary
```

---

### 4.7 Module : PDF Generator

**Fichier** : `services/pdf_generator.py`

**Responsabilité** : Générer un rapport PDF professionnel avec les résultats de simulation.

**Technologie** : WeasyPrint (HTML → PDF)

**Sections du rapport** :

1. **Page de garde** : Logo, titre, date, disclaimer
2. **Résumé exécutif** : KPIs clés, recommandation
3. **Détail des coûts** : Tableau comparatif par poste
4. **Projections cash-flow** : Graphique 5 ans
5. **Hypothèses** : Paramètres utilisés, sources
6. **Annexes** : Détail calculs, références légales
7. **Analyse Stratégique** : Section générée par CrewAI (si activé)

---

## 5. Module Strategic Advisor (CrewAI)

### 5.1 Philosophie : Hybride Synchrone/Asynchrone

**Principe fondamental** : Ne jamais mélanger calculs déterministes et agents IA.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE HYBRIDE                                     │
└─────────────────────────────────────────────────────────────────────────────┘

     SYNCHRONE (200ms)                      ASYNCHRONE (2-3 min)
     ════════════════                       ═══════════════════
     Moteur Python                          CrewAI "Virtual Board"
           │                                        │
           │                                        │
           ▼                                        ▼
    ┌─────────────┐                         ┌─────────────────┐
    │  CALCULS    │                         │   AGENTS IA     │
    │ DÉTERMINISTES│                         │   AUTONOMES     │
    │             │                         │                 │
    │ • Cash-flow │                         │ 🔍 Market Scout │
    │ • Impôts    │                         │ ⚖️ Legal Watch  │
    │ • Loyers ML │                         │ ✍️ Chief Editor │
    │ • Charges   │                         │                 │
    └──────┬──────┘                         └────────┬────────┘
           │                                         │
           │ Immédiat                                │ Background Task
           ▼                                         ▼
    ┌─────────────┐                         ┌─────────────────┐
    │  DASHBOARD  │                         │   PDF ENRICHI   │
    │   (Web UI)  │                         │   (par email)   │
    │             │                         │                 │
    │ L'user voit │                         │ Contient :      │
    │ ses chiffres│                         │ • Tendances     │
    │ tout de     │                         │ • Risques       │
    │ suite       │                         │ • Opportunités  │
    └─────────────┘                         └─────────────────┘
```

### 5.2 Pourquoi cette séparation ?

| Approche | Problème | Conséquence |
|----------|----------|-------------|
| ❌ Agents pour calculs fiscaux | Latence 30-60s, hallucinations possibles | UX catastrophique, crédibilité = 0 |
| ✅ Python pour calculs | Déterministe, 200ms, sources citées | "Rigueur Bancaire" préservée |
| ✅ Agents pour conseil | Valeur ajoutée qualitative | Différenciation concurrentielle |

### 5.3 La Team CrewAI : "Virtual Board"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CREWAI VIRTUAL BOARD                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
    │   🔍 AGENT 1      │    │   ⚖️ AGENT 2      │    │   ✍️ AGENT 3      │
    │   Market Scout    │    │   Legal Watchdog  │    │   Chief Editor    │
    ├───────────────────┤    ├───────────────────┤    ├───────────────────┤
    │                   │    │                   │    │                   │
    │ LLM: Claude API   │    │ LLM: Claude API   │    │ LLM: Mistral 7B   │
    │ + Search Tool     │    │ + Search Tool     │    │ (Local)           │
    │                   │    │                   │    │                   │
    │ Mission:          │    │ Mission:          │    │ Mission:          │
    │ Analyser les      │    │ Surveiller les    │    │ Synthétiser les   │
    │ tendances marché  │    │ évolutions        │    │ rapports en       │
    │ du secteur dans   │    │ légales/fiscales  │    │ "Executive        │
    │ la ville cible    │    │ récentes          │    │ Summary"          │
    │                   │    │                   │    │                   │
    │ Output:           │    │ Output:           │    │ Output:           │
    │ • 3 opportunités  │    │ • Réformes en     │    │ • Texte 200 mots  │
    │ • 2 risques       │    │   cours           │    │ • Ton pro         │
    │ • Concurrence     │    │ • Votations       │    │ • Encourageant    │
    │                   │    │ • Jurisprudence   │    │                   │
    └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘
              │                        │                        │
              └────────────────────────┴────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  PDF GENERATOR  │
                              │                 │
                              │ Ajoute section  │
                              │ "Analyse        │
                              │  Stratégique"   │
                              └─────────────────┘
```

### 5.4 Détail des Agents

#### Agent 1 : Market Scout

| Attribut | Valeur |
|----------|--------|
| **Role** | Senior Market Analyst |
| **LLM** | Claude Sonnet (via API) |
| **Tools** | DuckDuckGo Search, Web Fetch |
| **Goal** | Analyser les tendances du secteur {sector} à {city} en 2025 |

**Prompt Template** :

```
Tu es un analyste de marché senior spécialisé en implantation d'entreprise.

CONTEXTE:
- Secteur: {sector}
- Ville: {city}
- Canton: {canton}

MISSION:
Recherche et analyse les tendances actuelles pour ce secteur dans cette ville.

OUTPUT REQUIS (JSON):
{
  "opportunities": [
    {"title": "...", "description": "...", "source": "..."},
    // 3 opportunités
  ],
  "risks": [
    {"title": "...", "description": "...", "source": "..."},
    // 2 risques
  ],
  "competition_level": "low|medium|high",
  "talent_availability": "scarce|moderate|abundant"
}
```

#### Agent 2 : Legal Watchdog

| Attribut | Valeur |
|----------|--------|
| **Role** | Swiss Legal Expert |
| **LLM** | Claude Sonnet (via API) |
| **Tools** | DuckDuckGo Search, Web Fetch |
| **Goal** | Identifier les évolutions légales/fiscales récentes à {canton} |

**Prompt Template** :

```
Tu es un juriste expert en droit fiscal suisse et européen.

CONTEXTE:
- Canton: {canton}
- Type d'entreprise: {company_type}

MISSION:
Recherche les évolutions récentes qui pourraient impacter une implantation:
- Réformes fiscales (cantonales, fédérales, OCDE)
- Votations en cours ou récentes
- Jurisprudence importante

OUTPUT REQUIS (JSON):
{
  "reforms": [
    {"title": "...", "status": "enacted|pending|proposed", "impact": "positive|negative|neutral", "source": "..."}
  ],
  "votations": [
    {"title": "...", "date": "...", "relevance": "..."}
  ],
  "legal_stability_score": 1-10,
  "key_warning": "..." // ou null
}
```

#### Agent 3 : Chief Editor

| Attribut | Valeur |
|----------|--------|
| **Role** | Executive Report Writer |
| **LLM** | Mistral 7B (Local via Ollama) |
| **Tools** | Aucun (synthèse pure) |
| **Goal** | Rédiger une synthèse exécutive de 200 mots |

**Prompt Template** :

```
Tu es un rédacteur de rapports exécutifs pour conseils d'administration.

INPUTS:
- Résultats financiers: {financial_results_json}
- Analyse marché: {market_analysis_json}
- Analyse légale: {legal_analysis_json}

MISSION:
Rédige une "Synthèse Exécutive" de 200 mots maximum pour le PDF final.

CONTRAINTES:
- Ton professionnel mais encourageant
- Commence par le verdict principal
- Mentionne 1-2 opportunités clés
- Mentionne 1 risque à surveiller
- Termine par une recommandation actionnable

FORMAT:
Texte brut en paragraphes (pas de JSON, pas de bullet points).
```

### 5.5 Intégration FastAPI

**Fichier** : `services/strategic_advisor.py`

**Architecture** :

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX D'INTÉGRATION                           │
└─────────────────────────────────────────────────────────────────┘

POST /api/simulate
      │
      ├──────────────────────────────────────────┐
      │                                          │
      ▼                                          ▼
┌─────────────┐                         ┌─────────────────────┐
│  SYNCHRONE  │                         │    ASYNCHRONE       │
│             │                         │  (BackgroundTasks)  │
│ tax_engine  │                         │                     │
│ .calculate()│                         │ strategic_advisor   │
│             │                         │ .run_analysis()     │
└──────┬──────┘                         └──────────┬──────────┘
       │                                           │
       │ 200ms                                     │ 2-3 min
       ▼                                           ▼
┌─────────────┐                         ┌─────────────────────┐
│   Response  │                         │  generate_pdf()     │
│   JSON      │                         │  send_email()       │
│             │                         │                     │
│ "Vos        │                         │ "Votre rapport      │
│  résultats  │                         │  complet est prêt"  │
│  financiers"│                         │                     │
└─────────────┘                         └─────────────────────┘
```

### 5.6 Gestion des erreurs

| Scénario | Comportement |
|----------|--------------|
| Agent timeout (> 3min) | Envoyer PDF sans section stratégique |
| Erreur API Claude | Fallback sur Mistral local pour tous les agents |
| Recherche web échoue | Utiliser connaissances LLM uniquement |
| Email échoue | Stocker PDF dans Supabase + notifier dashboard |

### 5.7 Coûts estimés

| Agent | Tokens/requête | Coût/requête |
|-------|----------------|--------------|
| Market Scout | ~2000 input + 500 output | ~$0.02 |
| Legal Watchdog | ~2000 input + 500 output | ~$0.02 |
| Chief Editor | ~1500 input + 300 output | ~$0.00 (local) |
| **Total** | | **~$0.04/simulation** |

Avec 100 simulations/jour = ~$4/jour = ~$120/mois (acceptable).

### 5.8 Valeur ajoutée pour le recruteur

| Sans Strategic Advisor | Avec Strategic Advisor |
|------------------------|------------------------|
| "Il sait utiliser des APIs LLM" | "Il sait **orchestrer** des agents autonomes" |
| Calculs statiques | Analyse dynamique du marché |
| Rapport générique | Rapport **contextualisé** (tendances, risques) |
| Dev IA classique | **Architecte solutions IA avancées** |

"Pour les calculs fiscaux, j'utilise un moteur Python strict car on ne joue pas avec l'argent. Pour l'analyse de marché, j'utilise une équipe d'agents autonomes CrewAI qui scannent le web en temps réel. J'ai géré la latence via des BackgroundTasks FastAPI pour ne pas dégrader l'UX."

### 5.9 Stratégie de Fallback

**Principe** : L'échec des agents ne doit jamais bloquer l'utilisateur.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ARBRE DE DÉCISION FALLBACK                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    CrewAI lancé (BackgroundTask)
                              │
                              ▼
                    ┌─────────────────┐
                    │  Timeout 3 min  │
                    │    atteint ?    │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ NON                         │ OUI
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────────┐
    │ Agents OK ?     │           │ FALLBACK TIMEOUT    │
    └────────┬────────┘           │                     │
             │                    │ • PDF sans section  │
    ┌────────┴────────┐           │   stratégique       │
    │ OUI             │ NON       │ • Email : "Analyse  │
    ▼                 ▼           │   en cours..."      │
┌────────┐    ┌─────────────┐     │ • Retry async       │
│ PDF    │    │ FALLBACK    │     │   (max 2x)          │
│ COMPLET│    │ ERREUR      │     └─────────────────────┘
└────────┘    │             │
              │ • Log erreur│
              │ • PDF sans  │
              │   section   │
              │ • Note :    │
              │  "Analyse   │
              │  indispo."  │
              └─────────────┘
```

**Comportements par scénario** :

| Scénario | Comportement | Message utilisateur |
|----------|--------------|---------------------|
| ✅ Succès complet | PDF avec "Analyse Stratégique" | "Votre rapport complet est prêt" |
| ⏱️ Timeout (>3min) | PDF sans section + retry async | "Rapport envoyé. Analyse stratégique en cours, complément à suivre." |
| ❌ Erreur Agent 1 ou 2 | Continuer avec agents restants | Section partielle dans PDF |
| ❌ Erreur Claude API | Fallback tous agents sur Mistral | Section générée (qualité moindre) |
| ❌ Erreur totale CrewAI | PDF financier uniquement | "Analyse stratégique temporairement indisponible" |
| ❌ Erreur envoi email | Stocker PDF Supabase + notif dashboard | "PDF disponible dans votre espace" |

**Implémentation** :

```
try:
    result = await asyncio.wait_for(crew.kickoff(), timeout=180)
    pdf = generate_full_pdf(financial_data, result)
except asyncio.TimeoutError:
    pdf = generate_partial_pdf(financial_data, note="pending")
    schedule_retry(simulation_id)
except CrewAIError as e:
    log_error(e)
    pdf = generate_partial_pdf(financial_data, note="unavailable")
finally:
    try:
        send_email(user_email, pdf)
    except EmailError:
        store_pdf_supabase(user_id, pdf)
        notify_dashboard(user_id, "pdf_ready")
```

**Métriques de monitoring** :

| Métrique | Seuil alerte | Action |
|----------|--------------|--------|
| Taux timeout | > 10% | Augmenter timeout ou optimiser prompts |
| Taux erreur agents | > 5% | Vérifier API keys, quotas |
| Taux fallback Mistral | > 20% | Investiguer Claude API |
| Temps moyen agents | > 2min | Optimiser prompts, réduire scope |

---

## 6. Modules Frontend

### 6.1 Landing Page "Hook" (Priorité P0)

**Objectif** : Capturer l'attention du recruteur en moins de 5 secondes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANDING PAGE STRUCTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo]                              [FR] [DE] [EN]    [Se connecter]       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    🇫🇷 Lyon  vs  🇨🇭 Genève                                  │
│                                                                             │
│              ┌─────────────────────────────────────────┐                   │
│              │                                         │                   │
│              │    ÉCONOMIE ANNUELLE ESTIMÉE            │                   │
│              │                                         │                   │
│              │         ████████████████                │                   │
│              │              +127,000 €                 │  ← Animation      │
│              │                                         │    compteur       │
│              │    (basé sur CA 500k€, 5 employés)     │                   │
│              │                                         │                   │
│              └─────────────────────────────────────────┘                   │
│                                                                             │
│                  [ 🚀 Simuler mon implantation ]                           │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│     🔒 Privacy-First       🤖 IA Agentique        🌍 Trilingue             │
│     Vos données restent    Analyse de marché      FR • DE • EN             │
│     sur votre appareil     en temps réel          Interface native         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    COMMENT ÇA MARCHE ?                                     │
│                                                                             │
│     ┌─────────┐        ┌─────────┐        ┌─────────┐        ┌─────────┐  │
│     │    1    │   →    │    2    │   →    │    3    │   →    │    4    │  │
│     │ 📝      │        │ ⚙️      │        │ 📊      │        │ 📄      │  │
│     │Formulaire│       │ Calcul  │        │Résultats│        │  PDF    │  │
│     │ 2 min   │        │ IA      │        │ live    │        │ complet │  │
│     └─────────┘        └─────────┘        └─────────┘        └─────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    VILLES COMPARÉES                                        │
│                                                                             │
│     🇫🇷 Lyon        🇨🇭 Genève      🇨🇭 Lausanne     🇨🇭 Zurich      🇨🇭 Bâle   │
│     Référence      Finance        Tech/EPFL      Finance       Pharma      │
│     France         Canton GE      Canton VD      Canton ZH     Canton BS   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    TECHNOLOGIES                                            │
│                                                                             │
│     [Next.js]  [FastAPI]  [CrewAI]  [Claude]  [Supabase]                  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│     Projet portfolio par Florent VANHOLLEBEKE            [GitHub] [LinkedIn]│
│     Chef de projet IA                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Composants clés** :

| Composant | Fichier | Description |
|-----------|---------|-------------|
| `HeroSection` | `components/landing/HeroSection.tsx` | Animation compteur + CTA principal |
| `ValueProps` | `components/landing/ValueProps.tsx` | 3 badges (Privacy, IA, Trilingue) |
| `HowItWorks` | `components/landing/HowItWorks.tsx` | 4 étapes illustrées |
| `CityCards` | `components/landing/CityCards.tsx` | 5 cartes villes avec spécialités |
| `TechStack` | `components/landing/TechStack.tsx` | Logos technologies |
| `Footer` | `components/landing/Footer.tsx` | Bio + liens sociaux |

**Animation compteur (HeroSection)** :

```
Effet : Compteur qui défile de 0 à 127,000 en 2 secondes
Librairie : framer-motion ou react-countup
Trigger : Au scroll into view (Intersection Observer)

États :
1. Initial : "Calculez votre économie potentielle"
2. Animation : Compteur 0 → 127,000
3. Final : "+127,000 €" avec particules/confetti subtils
```

**Responsive** :

| Breakpoint | Adaptation |
|------------|------------|
| Desktop (>1024px) | Layout complet comme schéma |
| Tablet (768-1024px) | 2 colonnes pour ValueProps |
| Mobile (<768px) | Stack vertical, CTA sticky bottom |

**Performance** :

| Métrique | Cible | Comment |
|----------|-------|---------|
| LCP | < 1.5s | Images optimisées (next/image), fonts préchargées |
| FID | < 100ms | Pas de JS bloquant, lazy load animations |
| CLS | < 0.1 | Dimensions réservées pour tous éléments |

### 6.2 Structure du projet

```
/frontend
├── /app
│   ├── /[locale]                    # Routes internationalisées
│   │   ├── layout.tsx               # Layout avec providers
│   │   ├── page.tsx                 # Landing page
│   │   │
│   │   ├── /simulator
│   │   │   ├── page.tsx             # Container Wizard
│   │   │   └── /results
│   │   │       └── page.tsx         # Dashboard résultats
│   │   │
│   │   ├── /auth
│   │   │   ├── /login
│   │   │   │   └── page.tsx
│   │   │   └── /register
│   │   │       └── page.tsx
│   │   │
│   │   └── /account
│   │       └── page.tsx             # Profil, historique
│   │
│   └── /api                         # Route handlers (proxy)
│       └── /[...proxy]
│           └── route.ts
│
├── /components
│   ├── /ui                          # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── ...
│   │
│   ├── /landing                     # 🆕 Composants landing page
│   │   ├── HeroSection.tsx          # Animation compteur + CTA
│   │   ├── ValueProps.tsx           # 3 badges valeur
│   │   ├── HowItWorks.tsx           # 4 étapes
│   │   ├── CityCards.tsx            # 5 cartes villes
│   │   ├── TechStack.tsx            # Logos technos
│   │   └── AnimatedCounter.tsx      # Compteur animé réutilisable
│   │
│   ├── /simulator                   # Composants métier
│   │   ├── SimulationWizard.tsx     # Orchestrateur wizard
│   │   ├── StepIndicator.tsx        # Indicateur progression
│   │   ├── /steps
│   │   │   ├── IdentityStep.tsx     # Step 0 : Identité
│   │   │   ├── LocationStep.tsx     # Step 1 : Localisation
│   │   │   ├── FinanceStep.tsx      # Step 2 : Finance/RH
│   │   │   ├── RealEstateStep.tsx   # Step 3 : Immobilier
│   │   │   └── LegalStep.tsx        # Step 4 : Juridique
│   │   └── MagicFillButton.tsx      # Bouton IA pré-remplissage
│   │
│   ├── /results                     # Composants résultats
│   │   ├── ResultsDashboard.tsx     # Dashboard principal
│   │   ├── CashFlowChart.tsx        # Graphique cash-flow
│   │   ├── ComparisonTable.tsx      # Tableau comparatif
│   │   ├── KPICards.tsx             # Cartes KPIs
│   │   └── DownloadPDFButton.tsx    # Export PDF
│   │
│   └── /layout                      # Composants layout
│       ├── Header.tsx
│       ├── Footer.tsx
│       ├── LanguageSwitcher.tsx
│       └── AuthButton.tsx
│
├── /lib
│   ├── api.ts                       # Client API (fetch wrapper)
│   ├── auth.ts                      # Helpers auth Supabase
│   ├── schemas.ts                   # Schémas Zod
│   └── utils.ts                     # Utilitaires
│
├── /messages                        # Traductions i18n
│   ├── fr.json
│   ├── de.json
│   └── en.json
│
├── /hooks                           # Custom hooks
│   ├── useSimulation.ts
│   ├── useAuth.ts
│   └── useQuota.ts
│
├── /styles
│   └── globals.css                  # Tailwind + custom
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### 6.2 Composant : Simulation Wizard

**Fichier** : `components/simulator/SimulationWizard.tsx`

**Type** : Client Component (`"use client"`)

**État** :

```typescript
interface WizardState {
  currentStep: number;  // 0-4
  data: SimulationInput;
  errors: Record<string, string>;
  isSubmitting: boolean;
}
```

**Steps** :

| Step | Nom | Champs | Obligatoire |
|------|-----|--------|-------------|
| 0 | Identité | Nom entreprise, Email, Téléphone | Non (PDF only) |
| 1 | Localisation | Pays, Ville/Canton | Oui |
| 2 | Finance & RH | CA, Bénéfice, Effectif, Secteur, Salaire moyen | Oui (sauf salaire) |
| 3 | Immobilier | Surface m², Type bien, Loyer (optionnel) | Oui (sauf loyer) |
| 4 | Juridique | Forme juridique, Horizon projection | Oui |

### 5.3 Feature : Magic Fill

**Principe** : L'utilisateur colle un texte libre décrivant son projet, le LLM extrait les entités et pré-remplit le formulaire.

**Exemple** :

```
Input: "Je veux créer une SAS de conseil IT avec 5 développeurs, 
        300k€ de CA prévu, dans des bureaux de 100m² à Genève"

Output JSON:
{
  "forme_juridique": "SAS",
  "secteur": "IT",
  "nb_employees": 5,
  "chiffre_affaires": 300000,
  "surface_m2": 100,
  "ville": "geneve"
}
```

**Flow** :

```
Texte libre → POST /api/extract → LLM Local (Mistral) → JSON → Pré-remplissage form
```

### 5.4 Composant : Results Dashboard

**Fichier** : `components/results/ResultsDashboard.tsx`

**Sections** :

```
┌─────────────────────────────────────────────────────────────────┐
│                     RÉSULTATS SIMULATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ TCO     │  │ Marge   │  │ Break   │  │ Gain    │           │
│  │ Annuel  │  │ Nette   │  │ Even    │  │ vs Lyon │           │
│  │ 450k CHF│  │  18%    │  │ 380k CA │  │ +125k€  │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PROJECTION CASH-FLOW 5 ANS                  │  │
│  │                                                          │  │
│  │  💰│                                          ╱──────    │  │
│  │    │                               ╱─────────╱           │  │
│  │    │                    ╱─────────╱                      │  │
│  │    │         ╱─────────╱                                 │  │
│  │    │╱───────╱                                            │  │
│  │    └──────────────────────────────────────────────────   │  │
│  │        Y1      Y2      Y3      Y4      Y5                │  │
│  │                                                          │  │
│  │    ── Lyon    ── Genève    ── Zurich                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              COMPARAISON DÉTAILLÉE                       │  │
│  │                                                          │  │
│  │  Poste          │ Lyon    │ Genève  │ Zurich  │ Delta   │  │
│  │  ─────────────────────────────────────────────────────   │  │
│  │  Masse salar.   │ 250k€   │ 450k CHF│ 520k CHF│ +80%    │  │
│  │  Charges patr.  │ 108k€   │ 68k CHF │ 78k CHF │ -37%    │  │
│  │  Loyer annuel   │ 36k€    │ 72k CHF │ 96k CHF │ +100%   │  │
│  │  Impôt société  │ 75k€    │ 42k CHF │ 36k CHF │ -44%    │  │
│  │  ─────────────────────────────────────────────────────   │  │
│  │  TOTAL          │ 469k€   │ 632k CHF│ 730k CHF│         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  📥 Télécharger le rapport PDF                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Modèles de Données

### 6.1 Input Simulation

```
SimulationInput
├── identity (optionnel - PII)
│   ├── company_name: string
│   ├── contact_email: string
│   └── contact_phone: string
│
├── location
│   ├── country: "FR" | "CH"
│   ├── city: "lyon" | "geneve" | "lausanne" | "zurich"
│   └── district: string (optionnel)
│
├── finance
│   ├── chiffre_affaires: number (EUR)
│   ├── benefice_previsionnel: number (EUR)
│   ├── nb_employees: number
│   ├── secteur: "IT" | "Finance" | "Industrie" | "Services" | "Commerce"
│   └── salaire_moyen_brut: number | null (si null → benchmark)
│
├── real_estate
│   ├── surface_m2: number
│   ├── property_type: "bureau" | "commercial" | "mixte"
│   └── loyer_mensuel: number | null (si null → ML prediction)
│
├── legal
│   ├── forme_juridique: "SAS" | "SARL" | "SA" | "GmbH" | "AG" | "Sàrl"
│   └── horizon_ans: 1 | 3 | 5 | 10
│
└── options
    ├── include_comparison: boolean
    └── comparison_cities: string[]
```

### 6.2 Output Simulation

```
SimulationResult
├── metadata
│   ├── simulation_id: UUID
│   ├── generated_at: ISO datetime
│   ├── version: string
│   └── disclaimer: string
│
├── input_summary
│   └── (copie anonymisée des inputs)
│
├── location_result
│   ├── city: string
│   ├── currency: "EUR" | "CHF"
│   │
│   ├── annual_costs
│   │   ├── masse_salariale_brute: number
│   │   ├── charges_patronales: number
│   │   ├── cout_salarial_total: number
│   │   ├── loyer_annuel: number
│   │   ├── charges_locatives: number
│   │   ├── cout_immobilier_total: number
│   │   ├── impot_societe: number
│   │   ├── frais_fixes: number
│   │   └── total_charges: number
│   │
│   ├── kpis
│   │   ├── tco_annuel: number
│   │   ├── marge_nette_pct: number
│   │   ├── break_even_ca: number
│   │   └── benefice_net_annuel: number
│   │
│   └── projections: CashFlowProjection[]
│       ├── annee: number
│       ├── ca: number
│       ├── charges: number
│       ├── benefice_net: number
│       └── cumul: number
│
├── comparison (si demandé)
│   ├── baseline: string (ex: "lyon")
│   ├── results: Record<city, location_result>
│   └── deltas: Record<city, DeltaAnalysis>
│       ├── delta_total_5ans: number
│       ├── delta_impots: number
│       ├── delta_salaires: number
│       └── delta_immobilier: number
│
└── sources
    ├── fiscal: string[] (ex: ["CGI Art. 219", "ESTV 2024"])
    ├── immobilier: string (ex: "ML Model ImmoScout24")
    └── salaires: string (ex: "OFS 2024")
```

### 6.3 Schéma base de données (Supabase)

```sql
-- Utilisateurs (géré par Supabase Auth)
-- Table: auth.users (built-in)

-- Profils utilisateurs
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    company_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Historique des simulations
CREATE TABLE simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    input_hash TEXT,  -- Hash des paramètres (pour déduplication)
    input_data JSONB,  -- Paramètres (sans PII)
    result_data JSONB,  -- Résultats complets
    cities TEXT[],  -- Villes comparées
    created_at TIMESTAMP DEFAULT NOW()
);

-- Quotas d'utilisation
CREATE TABLE usage_quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    date DATE DEFAULT CURRENT_DATE,
    api_calls INTEGER DEFAULT 0,
    llm_tokens INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

-- Feedback utilisateurs
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    simulation_id UUID REFERENCES simulations(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_simulations_user ON simulations(user_id);
CREATE INDEX idx_simulations_created ON simulations(created_at DESC);
CREATE INDEX idx_quotas_user_date ON usage_quotas(user_id, date);
```

---

## 8. Flux de Données & Privacy

### 7.1 Classification des données

| Catégorie | Exemples | Stockage | Envoi Cloud |
|-----------|----------|----------|-------------|
| **PII Identité** | Nom, Email, Téléphone | RAM uniquement | ❌ JAMAIS |
| **PII Entreprise** | SIREN, IDE, IBAN | RAM uniquement | ❌ JAMAIS |
| **Données métier** | CA, Effectif, Surface | Supabase (chiffré) | ✅ Anonymisé |
| **Résultats** | Cash-flow, Comparaisons | Supabase | ✅ Générique |

### 7.2 Flux détaillé

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUX PRIVACY-FIRST                                │
└─────────────────────────────────────────────────────────────────────────────┘

ÉTAPE 1: COLLECTE
─────────────────
    User Input (Formulaire)
           │
           ▼
    ┌─────────────────────────────────────────────────┐
    │  {                                              │
    │    "company_name": "Music Consulting",   ← PII │
    │    "email": "florent@music.dev",         ← PII │
    │    "ca": 500000,                                │
    │    "ville": "geneve",                           │
    │    "surface_m2": 150                            │
    │  }                                              │
    └─────────────────────────────────────────────────┘

ÉTAPE 2: SÉPARATION
───────────────────
           │
           ▼
    ┌─────────────┐         ┌─────────────────────────┐
    │ PII VAULT   │         │ DONNÉES MÉTIER          │
    │ (RAM only)  │         │ (Processable)           │
    ├─────────────┤         ├─────────────────────────┤
    │ company_name│         │ ca: 500000              │
    │ email       │         │ ville: "geneve"         │
    │ phone       │         │ surface_m2: 150         │
    │ siret       │         │ nb_employees: 10        │
    └─────────────┘         └─────────────────────────┘
           │                           │
           │                           ▼
           │                 ┌─────────────────────────┐
           │                 │ SERVICES                │
           │                 │ • RAG Fiscal            │
           │                 │ • ML Immo               │
           │                 │ • Claude API (anonyme)  │
           │                 └─────────────────────────┘
           │                           │
           │                           ▼
           │                 ┌─────────────────────────┐
           │                 │ RÉSULTATS GÉNÉRIQUES    │
           │                 │ • cash_flow: [...]      │
           │                 │ • tco: 450000           │
           │                 │ • recommandation: "..." │
           │                 └─────────────────────────┘
           │                           │
           ▼                           ▼
    ┌─────────────────────────────────────────────────┐
    │              ÉTAPE 3: RÉASSEMBLAGE              │
    │                   (LLM Local)                   │
    │                                                 │
    │  PII + Résultats → Rapport Personnalisé        │
    └─────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────┐
    │              ÉTAPE 4: NETTOYAGE                 │
    │                                                 │
    │  • Suppression PII Vault                        │
    │  • Log audit (sans PII)                         │
    │  • Stockage résultats (Supabase, sans PII)     │
    └─────────────────────────────────────────────────┘
```

### 7.3 Audit Logging

**Format des logs** (JSON Lines) :

```json
{"ts": "2025-11-29T23:15:00Z", "session": "a3f2b1c4", "action": "SESSION_START", "status": "OK"}
{"ts": "2025-11-29T23:15:01Z", "session": "a3f2b1c4", "action": "PII_DETECTED", "types": ["email", "phone_fr"]}
{"ts": "2025-11-29T23:15:02Z", "session": "a3f2b1c4", "action": "ANONYMIZATION", "status": "OK"}
{"ts": "2025-11-29T23:15:03Z", "session": "a3f2b1c4", "action": "RAG_SEARCH", "chunks": 3}
{"ts": "2025-11-29T23:15:05Z", "session": "a3f2b1c4", "action": "CLOUD_API", "tokens": 1250}
{"ts": "2025-11-29T23:15:08Z", "session": "a3f2b1c4", "action": "SESSION_COMPLETE", "status": "OK"}
{"ts": "2025-11-29T23:15:08Z", "session": "a3f2b1c4", "action": "VAULT_CLEARED", "status": "OK"}
```

**Règle absolue** : Aucune donnée personnelle dans les logs.

---

## 9. Internationalisation (i18n)

### 8.1 Langues supportées

| Code | Langue | Marché cible | Priorité |
|------|--------|--------------|----------|
| `fr` | Français | Romandie, France | 🥇 P0 |
| `de` | Allemand | Zurich, Berne, Bâle | 🥈 P1 |
| `en` | Anglais | International, Expats | 🥉 P2 |

### 8.2 Configuration next-intl

**Routing** : `/[locale]/...`

| URL | Langue | Page |
|-----|--------|------|
| `/fr` | Français | Landing |
| `/de/simulator` | Allemand | Wizard |
| `/en/simulator/results` | Anglais | Résultats |

### 8.3 Éléments traduits

| Élément | Clé i18n | Exemple FR | Exemple DE |
|---------|----------|------------|------------|
| UI Labels | `simulator.step1` | "Localisation" | "Standort" |
| Boutons | `common.next` | "Suivant" | "Weiter" |
| Erreurs | `errors.required` | "Champ requis" | "Pflichtfeld" |
| Villes | `cities.geneve` | "Genève" | "Genf" |
| Monnaies | `currency.chf` | "CHF" | "CHF" |
| Rapports PDF | `pdf.title` | "Rapport de simulation" | "Simulationsbericht" |

### 8.4 Détection automatique

```
1. URL path (/de/...) → Priorité 1
2. Cookie (NEXT_LOCALE) → Priorité 2
3. Accept-Language header → Priorité 3
4. Défaut → fr
```

---

## 10. Infrastructure & Déploiement

### 9.1 Environnements

| Env | URL | Usage |
|-----|-----|-------|
| **Local** | localhost:3000 / :8000 | Développement |
| **Preview** | *.vercel.app | PR reviews |
| **Production** | swisstax.app (ou similaire) | Public |

### 9.2 Architecture déploiement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │   Cloudflare    │
                         │   (DNS + CDN)   │
                         └────────┬────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
    ┌─────────────────┐                     ┌─────────────────┐
    │     Vercel      │                     │    Railway      │
    │   (Frontend)    │                     │   (Backend)     │
    ├─────────────────┤                     ├─────────────────┤
    │                 │     API calls       │                 │
    │  Next.js 14     │◄───────────────────►│  FastAPI        │
    │  Static + SSR   │                     │  Python 3.11    │
    │                 │                     │                 │
    └─────────────────┘                     └────────┬────────┘
                                                     │
              ┌──────────────────────────────────────┤
              │                   │                  │
              ▼                   ▼                  ▼
    ┌─────────────────┐  ┌─────────────┐   ┌─────────────────┐
    │    Supabase     │  │   Claude    │   │  Ollama Cloud   │
    │                 │  │    API      │   │  (ou self-host) │
    ├─────────────────┤  └─────────────┘   └─────────────────┘
    │ • Auth          │
    │ • PostgreSQL    │
    │ • Storage (PDF) │
    └─────────────────┘
```

### 9.3 CI/CD Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Push     │────►│   Tests     │────►│   Build     │────►│   Deploy    │
│   (GitHub)  │     │  (pytest,   │     │  (Docker,   │     │  (Vercel,   │
│             │     │   vitest)   │     │   Next.js)  │     │   Railway)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Linting   │
                    │ (ruff, eslint)
                    └─────────────┘
```

### 9.4 Variables d'environnement

**Frontend (.env.local)** :

```env
NEXT_PUBLIC_API_URL=https://api.swisstax.app
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
```

**Backend (.env)** :

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["https://swisstax.app"]

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx

# LLM
ANTHROPIC_API_KEY=sk-ant-xxx
OLLAMA_HOST=http://localhost:11434

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## 11. Sécurité & Garde-fous

### 10.1 Rate Limiting

| Utilisateur | Limite | Période | Action si dépassé |
|-------------|--------|---------|-------------------|
| Non authentifié | 3 simulations | /jour | Bloquer + inciter inscription |
| Authentifié (gratuit) | 10 simulations | /jour | Bloquer + proposer upgrade |
| Authentifié (premium) | 100 simulations | /jour | Soft limit + alerte |

### 10.2 Protection API Claude

| Mesure | Implémentation |
|--------|----------------|
| **Quota tokens** | Max 2000 tokens/requête |
| **Cache** | Redis/Supabase cache sur requêtes identiques |
| **Fallback** | Si quota dépassé → LLM local (Mistral) |
| **Monitoring** | Alerte si coût > 50€/jour |

### 10.3 Validation des entrées

| Champ | Validation |
|-------|------------|
| `chiffre_affaires` | > 0, < 1 milliard |
| `nb_employees` | >= 1, <= 10000 |
| `surface_m2` | >= 10, <= 100000 |
| `email` | Format email valide |
| `ville` | Enum whitelist |

### 10.4 Headers de sécurité

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## 12. Sources de Données

### 12.1 Données fiscales (RAG)

| Source | Contenu | Mise à jour |
|--------|---------|-------------|
| **CGI (Légifrance)** | IS, IFI, DMTO, TVA France | Annuelle (LF) |
| **ESTV** | Impôt bénéfice par canton | Annuelle |
| **Fiches cantonales** | Barèmes GE, VD, ZH, BS | Annuelle |
| **Convention FR-CH 1966** | Double imposition | Stable |
| **Code Sécu Sociale** | Charges patronales FR | Annuelle |

### 12.2 Données immobilières (ML)

| Source | Pays | Méthode | Volume |
|--------|------|---------|--------|
| **ImmoScout24** | 🇨🇭 Suisse | Scraping (existant) | ~1200 annonces |
| **BureauxLocaux** | 🇫🇷 France | Scraping (à faire) | ~500-1000 annonces |

### 12.3 Données salaires (Benchmark)

| Source | Pays | Granularité |
|--------|------|-------------|
| **OFS (ESS)** | 🇨🇭 Suisse | Canton × Branche × Niveau |
| **INSEE/DADS** | 🇫🇷 France | Région × Branche × CSP |
| **APEC** | 🇫🇷 France | Métiers cadres |

### 12.4 Données temps réel (Claude API)

| Donnée | Source | Fréquence |
|--------|--------|-----------|
| Taux EUR/CHF | Web search | Chaque requête |
| Actualités fiscales | Web search | Chaque requête |
| Jurisprudence récente | Web search | Si pertinent |

---

## 13. Roadmap

### 13.1 Phase 1 : MVP (Semaines 1-8)

| Semaine | Backend | Frontend | Livrable |
|---------|---------|----------|----------|
| **S1** | FastAPI setup, Pydantic schemas | Next.js 14 setup, i18n | Squelette |
| **S2** | Privacy Orchestrator (existant) | Auth Supabase | Flux sécurisé |
| **S3** | Business Simulator (TDD) | Wizard Steps 1-2 | Calculs base |
| **S4** | RAG Fiscal integration | Wizard Steps 3-4 | Formulaire complet |
| **S5** | ML Immo CH integration | Results Dashboard | Prédictions |
| **S6** | Salary Benchmark | Graphiques (Recharts) | Comparaisons |
| **S7** | Rate limiting, quotas | Landing page | Anti-abus |
| **S8** | PDF Generator, tests | Polish, SEO | **MVP LIVE** 🚀 |

### 13.2 Phase 2 : Enrichissement (Mois 3-6)

| Mois | Features |
|------|----------|
| **M3** | Scraping Lyon (BureauxLocaux), Modèle ML FR |
| **M4** | 26 cantons suisses (pas juste GE/VD/ZH) |
| **M5** | Historique simulations, compte utilisateur |
| **M6** | Beta testeurs (fiduciaires), feedback loop |

### 13.3 Phase 3 : Scale (Mois 7-15)

| Mois | Objectif |
|------|----------|
| **M7-9** | API publique, documentation, pricing |
| **M10-12** | Intégrations (Zapier, n8n), partenariats |
| **M13-15** | Expansion (IT, DE, autres métropoles), revenus |

---

## 14. KPIs & Métriques

### 14.1 Métriques techniques

| Métrique | Cible | Outil |
|----------|-------|-------|
| Uptime | > 99.5% | Railway metrics |
| Temps réponse API | < 3s (P95) | Sentry |
| Erreurs 5xx | < 0.1% | Sentry |
| Couverture tests | > 80% | Pytest/Vitest |

### 14.2 Métriques produit

| Métrique | Cible MVP | Outil |
|----------|-----------|-------|
| Inscriptions | 100 en 2 mois | Supabase |
| Simulations/jour | 50 | Analytics custom |
| Taux complétion wizard | > 60% | Posthog/Mixpanel |
| NPS (feedback) | > 40 | Formulaire custom |

### 14.3 Métriques business

| Métrique | Cible M12 | Commentaire |
|----------|-----------|-------------|
| Utilisateurs actifs | 500 | MAU |
| Contacts recruteurs | 5+ | 
| Revenus (si SaaS) | 1k€/mois | Nice to have |

---

## 15. Glossaire

| Terme | Définition |
|-------|------------|
| **AVS** | Assurance-Vieillesse et Survivants (numéro Sécu suisse) |
| **CGI** | Code Général des Impôts (France) |
| **CrewAI** | Framework Python pour orchestrer des agents IA autonomes |
| **ESTV** | Administration Fédérale des Contributions (Suisse) |
| **IDE** | Identifiant des Entreprises (Suisse) |
| **IS** | Impôt sur les Sociétés |
| **LLM** | Large Language Model |
| **nLPD** | Nouvelle Loi sur la Protection des Données (Suisse, sept. 2023) |
| **NIR** | Numéro d'Inscription au Répertoire (Sécu sociale France) |
| **OFS** | Office Fédéral de la Statistique (Suisse) |
| **PII** | Personally Identifiable Information |
| **RAG** | Retrieval-Augmented Generation |
| **RGPD** | Règlement Général sur la Protection des Données (UE) |
| **SIREN** | Système d'Identification du Répertoire des Entreprises |
| **TCO** | Total Cost of Ownership |

---

## 📎 Annexes

### A. Liens utiles

| Ressource | URL |
|-----------|-----|
| Légifrance (CGI) | https://www.legifrance.gouv.fr |
| ESTV Statistiques | https://www.estv.admin.ch |
| OFS Salaires | https://www.bfs.admin.ch |
| Convention FR-CH | https://www.impots.gouv.fr/conventions |
| ImmoScout24 | https://www.immoscout24.ch |
| BureauxLocaux | https://www.bureauxlocaux.com |

### B. Contacts projet

| Rôle | Nom | Contact |
|------|-----|---------|
| Lead Dev / PM | Florent Vanhollebeke |  
| Assistant IA | Claude (Anthropic) | - |
| Assistant IA | Gemini (Google) | - |

---

*Document généré le 30 novembre 2025 - Version 3.1*
