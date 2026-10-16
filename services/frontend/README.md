# Crypto Viz - Frontend

Application Next.js 14 pour le monitoring en temps réel des cryptomonnaies.

## 🚀 Démarrage rapide

```bash
# Installer les dépendances (si ce n'est pas déjà fait)
npm install

# Créer le fichier de configuration (optionnel pour fixtures)
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=http://localhost:3001
NEXT_PUBLIC_USE_MOCK_DATA=true
EOF

# Lancer en mode développement
npm run dev
```

L'application sera accessible sur `http://localhost:3000`

## 📁 Structure du projet

```
src/
├── app/
│   ├── layout.tsx          # Layout principal de l'application
│   ├── page.tsx             # Page d'accueil avec la grille de graphiques
│   └── globals.css          # Styles globaux Tailwind + shadcn
├── components/
│   ├── CryptoChart.tsx      # Composant de graphique pour une crypto
│   └── ui/
│       └── card.tsx         # Composant Card de shadcn
├── hooks/
│   ├── useMarketData.ts     # Hook pour charger les données
│   ├── useRealtimeUpdates.ts # Hook pour les mises à jour temps réel
│   └── index.ts             # Export centralisé
├── lib/
│   ├── api/
│   │   ├── config.ts        # Configuration API (URLs, endpoints)
│   │   ├── client.ts        # Client HTTP REST (Axios)
│   │   ├── websocket.ts     # Client WebSocket (Socket.IO)
│   │   ├── marketData.service.ts # Service pour les données
│   │   └── index.ts         # Export centralisé
│   ├── fixtures.ts          # Génération de données simulées
│   └── utils.ts             # Utilitaires (cn pour Tailwind)
└── types/
    └── crypto.ts            # Types TypeScript pour les données crypto
```

## 🎯 Fonctionnalités

### ✅ Actuelles
- **Dashboard temps réel** : Affichage de 5 cryptomonnaies principales (BTC, ETH, BNB, SOL, ADA)
- **Graphiques interactifs** : Chart.js avec historique des prix
- **Mises à jour automatiques** : Simulation de données en temps réel toutes les 2 secondes
- **Design moderne** : UI glassmorphism avec Tailwind CSS et shadcn
- **Données logiques** : Fixtures avec variation de prix réaliste (±2% par intervalle)

### 🔄 Données simulées

Les fixtures génèrent :
- **Prix en temps réel** avec variations aléatoires logiques
- **Historique de 100 points** (1 point par minute)
- **Métadonnées** : volume 24h, market cap, high/low 24h
- **Changements en pourcentage** calculés automatiquement

## 🎨 Technologies

- **Next.js 14** : App Router avec Server Components
- **React 18** : Hooks modernes
- **TypeScript** : Typage fort
- **Tailwind CSS** : Styling utility-first
- **shadcn/ui** : Composants UI accessibles
- **Chart.js** : Graphiques interactifs
- **Framer Motion** : Animations fluides

## 📊 Structure des données

### Crypto
```typescript
{
  symbol: string          // Ex: "BTC"
  name: string           // Ex: "Bitcoin"
  price: number          // Prix actuel
  change24h: number      // Changement en $
  changePercent24h: number // Changement en %
  volume24h: number      // Volume 24h
  marketCap: number      // Capitalisation
  high24h: number        // Plus haut 24h
  low24h: number         // Plus bas 24h
  lastUpdate: Date       // Dernière mise à jour
}
```

### PriceHistory
```typescript
{
  timestamp: number      // Timestamp Unix
  open: number          // Prix d'ouverture
  high: number          // Plus haut
  low: number           // Plus bas
  close: number         // Prix de clôture
  volume: number        // Volume
}
```

## 🔌 Intégration avec le backend

L'application est **100% prête** pour l'API réelle ! Il suffit de changer une variable d'environnement.

### Mode Fixtures (Développement)

```bash
# .env.local
NEXT_PUBLIC_USE_MOCK_DATA=true
```

✅ Utilise les fixtures avec données simulées
✅ Pas besoin du backend
✅ Parfait pour le développement

### Mode API Réelle (Production)

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=http://localhost:3001
NEXT_PUBLIC_USE_MOCK_DATA=false
```

✅ Connexion au backend réel
✅ WebSocket pour le temps réel
✅ Authentification JWT prête

### Architecture API

**REST Client** :
- Axios avec intercepteurs
- Gestion automatique des erreurs
- Support JWT tokens

**WebSocket Client** :
- Socket.IO pour le temps réel
- Reconnexion automatique
- Événements typés

**Hooks React** :
- `useMarketData()` : Charge les données initiales
- `useRealtimeUpdates()` : Gère les mises à jour

**Services** :
- `marketDataService` : API REST pour market data
- `wsClient` : Client WebSocket singleton

Voir [API_INTEGRATION.md](./API_INTEGRATION.md) pour la documentation complète.

## 🎨 Personnalisation

### Modifier les cryptos affichées

Éditer `src/lib/fixtures.ts` :

```typescript
const BASE_CRYPTOS = [
  { symbol: 'BTC', name: 'Bitcoin', price: 67234.56, ... },
  // Ajouter d'autres cryptos ici
]
```

### Ajuster la fréquence de mise à jour

Dans `src/hooks/useRealtimeUpdates.ts` :

```typescript
setInterval(() => {
  // Logique de mise à jour
}, 30000) // Changer cette valeur (en ms)
```

### Changer les couleurs du thème

Éditer `src/app/globals.css` :

```css
:root {
  --primary: 221.2 83.2% 53.3%; /* Couleur primaire */
  /* ... autres variables */
}
```

## 🧪 Tests

```bash
# Lancer les tests
npm test

# Tests en mode watch
npm run test:watch

# Tests avec coverage
npm run test:ci
```

## 📦 Build de production

```bash
# Créer le build optimisé
npm run build

# Démarrer en mode production
npm start
```

## 🐳 Docker

```bash
# Build
docker build -t crypto-viz-frontend .

# Run
docker run -p 3000:3000 crypto-viz-frontend
```

## 📝 Notes

- Les données sont 100% simulées pour le développement
- Les graphiques se mettent à jour automatiquement
- La variation des prix est réaliste (±2% max par intervalle)
- L'historique conserve les 100 derniers points
- Design responsive (mobile, tablet, desktop)

## 🚧 Prochaines étapes

1. ✅ Intégration avec le backend réel
2. ✅ Connexion WebSocket pour les données live
3. ✅ Ajout de plus d'indicateurs techniques (RSI, MACD, etc.)
4. ✅ Système d'alertes personnalisables
5. ✅ Authentification utilisateur
6. ✅ Gestion de watchlist personnalisée

