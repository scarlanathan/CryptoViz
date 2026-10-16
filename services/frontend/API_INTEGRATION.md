# Guide d'intégration de l'API

Ce document explique comment basculer des fixtures aux données réelles de l'API backend.

## 📁 Structure API

```
src/
├── lib/
│   ├── api/
│   │   ├── config.ts           # Configuration (URLs, endpoints, WebSocket events)
│   │   ├── client.ts           # Client HTTP (Axios)
│   │   ├── websocket.ts        # Client WebSocket (Socket.IO)
│   │   ├── marketData.service.ts # Service pour les données de marché
│   │   └── index.ts            # Export centralisé
│   └── fixtures.ts              # Données simulées
├── hooks/
│   ├── useMarketData.ts        # Hook pour charger les données
│   ├── useRealtimeUpdates.ts  # Hook pour les mises à jour temps réel
│   └── index.ts                # Export centralisé
└── types/
    └── crypto.ts               # Types TypeScript
```

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env.local` à la racine de `services/frontend/` :

```bash
# URL de l'API Backend
NEXT_PUBLIC_API_URL=http://localhost:3001

# URL du WebSocket
NEXT_PUBLIC_WS_URL=http://localhost:3001

# Mode de données : true pour fixtures, false pour API réelle
NEXT_PUBLIC_USE_MOCK_DATA=true
```

### Basculer entre fixtures et API réelle

**Mode fixtures (développement)** :
```bash
NEXT_PUBLIC_USE_MOCK_DATA=true
```

**Mode API réelle (production)** :
```bash
NEXT_PUBLIC_USE_MOCK_DATA=false
```

## 🚀 Utilisation

### Hook useMarketData

Charge les données initiales (fixtures ou API selon la config) :

```typescript
import { useMarketData } from '@/hooks'

function MyComponent() {
  const { cryptos, marketDataMap, isLoading, error } = useMarketData()
  
  if (isLoading) return <div>Chargement...</div>
  if (error) return <div>Erreur: {error.message}</div>
  
  return <div>Données chargées !</div>
}
```

### Hook useRealtimeUpdates

Gère les mises à jour en temps réel (fixtures simulées ou WebSocket) :

```typescript
import { useRealtimeUpdates } from '@/hooks'

function MyComponent() {
  const [cryptos, setCryptos] = useState([])
  
  const { isConnected } = useRealtimeUpdates({
    cryptos,
    onCryptosUpdate: setCryptos,
    onMarketDataUpdate: setMarketDataMap,
  })
  
  return <div>Statut: {isConnected ? 'Connecté' : 'Déconnecté'}</div>
}
```

## 🔌 Intégration WebSocket

### Événements supportés

**Client → Serveur** :
- `subscribe` : Souscrire à des symboles
- `unsubscribe` : Se désabonner

**Serveur → Client** :
- `price-update` : Mise à jour de prix
- `market-data` : Données de marché complètes
- `alert-triggered` : Alerte déclenchée

### Exemple d'utilisation directe

```typescript
import { wsClient, WS_EVENTS } from '@/lib/api'

// Connexion
wsClient.connect()

// Souscrire à des symboles
wsClient.subscribe(['BTC', 'ETH', 'SOL'])

// Écouter les mises à jour
const cleanup = wsClient.onPriceUpdate((data) => {
  console.log('Nouveau prix:', data)
})

// Nettoyage
cleanup()
wsClient.disconnect()
```

## 🎯 API REST

### Endpoints disponibles

```typescript
// Toutes les cryptos
GET /api/market-data/all

// Une crypto spécifique
GET /api/market-data/:symbol

// Historique des prix
GET /api/market-data/:symbol/history?timeframe=1h

// Analytics
GET /api/analytics/:symbol

// Alertes
GET /api/alerts
POST /api/alerts
DELETE /api/alerts/:id

// Santé de l'API
GET /api/health
```

### Exemple d'utilisation

```typescript
import { marketDataService } from '@/lib/api'

// Récupérer toutes les cryptos
const cryptos = await marketDataService.getAllCryptos()

// Récupérer une crypto
const btc = await marketDataService.getCrypto('BTC')

// Récupérer l'historique
const history = await marketDataService.getHistory('BTC', '1h')

// Vérifier la santé de l'API
const health = await marketDataService.checkHealth()
```

## 📊 Format des données

### Crypto

```typescript
{
  symbol: string          // "BTC"
  name: string           // "Bitcoin"
  price: number          // 67234.56
  change24h: number      // 1234.56
  changePercent24h: number // 1.87
  volume24h: number      // 28456789000
  marketCap: number      // 1316789000000
  high24h: number        // 68123.45
  low24h: number         // 65890.12
  lastUpdate: Date       // 2024-01-15T10:30:00Z
}
```

### PriceHistory

```typescript
{
  timestamp: number      // 1705317000000
  open: number          // 67000.00
  high: number          // 67500.00
  low: number           // 66800.00
  close: number         // 67234.56
  volume: number        // 1234567890
}
```

### Mise à jour WebSocket

```typescript
{
  symbol: string        // "BTC"
  price: number         // 67500.00
  change24h: number     // 1500.00
  changePercent24h: number // 2.23
  timestamp: number     // 1705317060000
  volume: number        // 1250000000
}
```

## 🔒 Authentification (futur)

Le client API est prêt pour l'authentification via token JWT :

```typescript
// Le token sera automatiquement ajouté aux headers
localStorage.setItem('auth_token', 'votre_token_jwt')

// Toutes les requêtes incluront : Authorization: Bearer <token>
```

## 🐛 Gestion des erreurs

### Client API

```typescript
try {
  const data = await marketDataService.getAllCryptos()
} catch (error) {
  if (error.response?.status === 401) {
    // Non autorisé
  } else if (error.response?.status === 404) {
    // Ressource non trouvée
  } else {
    // Autre erreur
  }
}
```

### WebSocket

```typescript
wsClient.on('error', (error) => {
  console.error('Erreur WebSocket:', error)
})
```

## ⚡ Performance

### Optimisations implémentées

- **Reconnexion automatique** : WebSocket se reconnecte en cas de déconnexion
- **Debouncing** : Les mises à jour sont limitées (1 toutes les 30s)
- **Fenêtre glissante** : Seulement 50 derniers points d'historique conservés
- **Gestion de la mémoire** : Map utilisée pour les données (O(1) access)

## 📝 Checklist de migration

### Avant de basculer en mode API réelle

- [ ] Backend démarré et accessible
- [ ] Variables d'environnement configurées
- [ ] WebSocket fonctionnel (test avec `/api/health`)
- [ ] Vérifier le format des données retournées
- [ ] Tester les endpoints REST
- [ ] Tester la connexion WebSocket
- [ ] Mettre `NEXT_PUBLIC_USE_MOCK_DATA=false`
- [ ] Redémarrer le frontend

### Tests à effectuer

```bash
# Tester l'API REST
curl http://localhost:3001/api/health
curl http://localhost:3001/api/market-data/all

# Tester le WebSocket
# Utiliser un client WebSocket (ex: websocat)
websocat ws://localhost:3001
```

## 🔄 Mise à jour continue

### Configuration actuelle

- **Intervalle de mise à jour** : 30 secondes
- **Points d'historique** : 50 (4 heures avec intervalle de 5min)
- **Volatilité des prix** : ±8% entre points d'historique
- **Variation temps réel** : ±1.5% par mise à jour

### Modifier l'intervalle

Dans `src/hooks/useRealtimeUpdates.ts` :

```typescript
// Ligne 36
setInterval(() => {
  // Logique de mise à jour
}, 30000) // Changer cette valeur (en ms)
```

## 🚨 Troubleshooting

### Le WebSocket ne se connecte pas

1. Vérifier que le backend est démarré
2. Vérifier l'URL dans `.env.local`
3. Vérifier les logs du navigateur (F12)
4. Vérifier les CORS côté backend

### Les données ne se mettent pas à jour

1. Vérifier que `isConnected` est `true`
2. Vérifier les événements WebSocket dans DevTools
3. Vérifier que les symboles sont bien souscris
4. Vérifier l'intervalle de mise à jour (30s)

### Erreur 401/403

1. Vérifier le token d'authentification
2. Vérifier les permissions côté backend
3. Renouveler le token si expiré

## 📚 Ressources

- [Axios Documentation](https://axios-http.com/)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)
- [SWR pour le caching](https://swr.vercel.app/) (future amélioration)
- [React Query](https://tanstack.com/query/latest) (alternative)

