# CRYPTO VIZ

Plateforme de suivi des cryptomonnaies en temps réel : collecte continue des cours sur plusieurs exchanges, calcul d'indicateurs techniques et d'alertes, puis affichage sur un tableau de bord web mis à jour en direct.

Projet réalisé dans le cadre du module T-DAT-901 (Big Data). Le compte rendu du projet est disponible dans [`T_DAT_Compte_rendu.pdf`](T_DAT_Compte_rendu.pdf).

## Architecture

```
 Exchanges (Binance, Coinbase, Kraken, OKX)
            │  ccxt
            ▼
 ┌──────────────────┐   crypto-raw-data   ┌──────────────────┐
 │  data-collector  │ ──────── Kafka ───▶ │  data-processor  │
 │ Python · FastAPI │                     │ Python · pandas  │
 └──────────────────┘                     └────────┬─────────┘
                                                   │ indicateurs, alertes
                                                   ▼
                                         MongoDB · Redis · Kafka
                                                   │
                                                   ▼
                                       ┌──────────────────────┐   REST + Socket.IO   ┌──────────────┐
                                       │     api-backend      │ ───────────────────▶ │   frontend   │
                                       │ Node.js · Express    │                      │ Next.js 14   │
                                       └──────────────────────┘                      └──────────────┘
```

| Service | Stack | Port hôte | Rôle |
|---|---|---|---|
| `data-collector` | Python 3.11, FastAPI, asyncio, ccxt, aiokafka | 8001 | Récupère les cours OHLCV et les publie dans Kafka (producteur) |
| `data-processor` | Python 3.11, FastAPI, pandas, numpy, motor | 8002 | Consomme les données brutes, calcule RSI / MACD / Bollinger / moyennes mobiles, détecte les alertes, stocke dans MongoDB |
| `api-backend` | Node.js 18, Express, Socket.IO, kafkajs | 3002 | API REST et diffusion temps réel par WebSocket |
| `frontend` | Next.js 14, React 18, TypeScript, Tailwind, Chart.js | 3000 | Tableau de bord |
| `kafka` + `zookeeper` | Confluent 7.5 | 9092 / 2181 | Bus de messages |
| `mongodb` | MongoDB 6.0 | 27017 | Stockage des données traitées |
| `redis` | Redis 7 | 6379 | Cache |

Les indicateurs techniques sont implémentés à la main avec pandas/numpy (pas de dépendance à TA-Lib).

**Paires suivies par défaut** : BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, ADA/USDT (configurables via `SYMBOLS_TO_COLLECT` et `EXCHANGES_TO_USE`).

## Démarrage

### Prérequis

- Docker et Docker Compose
- Environ 4 Go de RAM alloués à Docker

### Lancement

```bash
git clone <url-du-repo>
cd CryptoViz
cp .env.example .env        # les valeurs par défaut suffisent en local
docker compose up --build -d
```

Les topics Kafka sont créés par le conteneur `kafka-init`. Les services applicatifs démarrent dans l'ordre grâce aux healthchecks (Kafka, MongoDB et Redis d'abord, puis collector → processor → backend → frontend). Compter une à deux minutes au premier lancement.

Un script interactif fait la même chose avec quelques vérifications en plus :

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Accès

| URL | Contenu |
|---|---|
| http://localhost:3000 | Tableau de bord |
| http://localhost:3002/api/health | Santé de l'API |
| http://localhost:8001/status | État du collecteur |
| http://localhost:8002/status | État du processeur |

Pour un aperçu rapide des données dans le terminal (prix courants, dernières alertes, statistiques par paire) :

```bash
./view_data.sh
```

## API

### data-collector (8001)

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Santé du service |
| GET | `/status` | État et métriques de collecte |
| POST | `/start` · `/stop` | Démarre / arrête la collecte |
| GET | `/exchanges` | Exchanges configurés |
| GET | `/symbols/{exchange}` | Paires disponibles sur un exchange |

### data-processor (8002)

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` · `/status` | Santé et état du traitement |
| GET | `/analytics/current` | Analyses courantes |
| GET | `/analytics/history` | Historique des analyses |
| GET | `/indicators/{symbol}` | Indicateurs techniques d'une paire |
| GET | `/alerts` | Alertes récentes |

### api-backend (3002)

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | Santé du service et de ses dépendances |
| GET | `/api/market-data` | Données de marché |
| GET | `/api/market-data/all` | Dernières données de toutes les paires |
| GET | `/api/market-data/:symbol` | Dernières données d'une paire |
| GET | `/api/market-data/:symbol/history` | Historique d'une paire |
| GET | `/api/analytics` | Analyses |
| GET | `/api/alerts` | Alertes |

**WebSocket (Socket.IO)** — le client émet `subscribe` / `unsubscribe` (`{ symbols: [...] }`) ou `subscribe_market_data` (`{ symbol, exchange }`) ; le serveur pousse `market-data`, `price-update`, `market_data_update` et `alert-triggered`.

## Données (MongoDB, base `cryptoviz`)

- **`processed_data`** : données OHLCV brutes + indicateurs techniques, tendance et marqueurs d'alerte, par paire et par exchange.
- **`analytics`** : analyses agrégées (tendances, volatilité, volume, score de confiance).
- **`alerts`** : alertes générées (RSI suracheté/survendu, croisement MACD, cassure de Bollinger, pic de volume, variation de prix).

Connexion depuis l'hôte (MongoDB Compass ou `mongosh`), avec les identifiants par défaut :

```
mongodb://cryptovizuser:cryptovizpass@localhost:27017/cryptoviz?authSource=admin
```

## Structure du dépôt

```
.
├── services/
│   ├── data-collector/    # main.py (FastAPI) + src/collector.py, config.py, models.py
│   ├── data-processor/    # main.py (FastAPI) + src/processor.py, indicators.py
│   ├── api-backend/       # server.js + src/routes, services, middleware
│   └── frontend/          # Next.js (src/app, components, hooks, lib/api)
├── shared/                # monté en lecture seule dans les conteneurs
├── scripts/setup.sh       # installation guidée
├── view_data.sh           # aperçu des données en terminal
├── docker-compose.yml
├── .env.example
└── T_DAT_Compte_rendu.pdf
```

## Développement local (hors Docker)

Kafka, MongoDB et Redis doivent tourner (`docker compose up -d zookeeper kafka mongodb redis`). Depuis l'hôte, Kafka est joignable sur `localhost:9092`.

```bash
# Services Python
cd services/data-collector        # ou data-processor
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000   # 8002 pour le processor

# API backend
cd services/api-backend
npm install
npm run dev

# Frontend
cd services/frontend
npm install
npm run dev
```

Les variables d'environnement du frontend sont décrites dans [`services/frontend/ENV_SETUP.md`](services/frontend/ENV_SETUP.md) et l'intégration avec l'API dans [`services/frontend/API_INTEGRATION.md`](services/frontend/API_INTEGRATION.md).

## Commandes utiles

```bash
docker compose ps                          # état des conteneurs
docker compose logs -f data-processor      # logs d'un service
docker compose up -d --build api-backend   # reconstruire un service
docker compose down                        # tout arrêter
docker compose down -v                     # tout arrêter et supprimer les données

# Kafka
docker exec crypto-kafka kafka-topics --list --bootstrap-server localhost:9092
docker exec crypto-kafka kafka-console-consumer --topic crypto-raw-data --bootstrap-server localhost:9092

# Redis
docker exec -it crypto-redis redis-cli -a redis_password
```

## Dépannage

- **Les services applicatifs ne démarrent pas** : Kafka met parfois plus de 30 s à devenir healthy ; vérifier avec `docker compose ps` puis relancer `docker compose up -d`.
- **Conflit de ports** : 3000, 3002, 8001, 8002, 9092, 2181, 27017 et 6379 doivent être libres.
- **Erreur d'authentification MongoDB** : les identifiants sont fixés à la création du volume. Après avoir changé `MONGODB_USER` / `MONGODB_PASSWORD`, supprimer le volume (`docker compose down -v`).
- **Limites de requêtes des exchanges** : augmenter `COLLECTION_INTERVAL` (en secondes, 30 par défaut).
