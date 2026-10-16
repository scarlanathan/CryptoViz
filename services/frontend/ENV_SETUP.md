# Configuration des variables d'environnement

## 📝 Fichier `.env.local`

Créez un fichier `.env.local` à la racine du dossier `services/frontend/` avec le contenu suivant :

### Mode Développement (avec fixtures)

```bash
# URL de l'API Backend
NEXT_PUBLIC_API_URL=http://localhost:3001

# URL du WebSocket
NEXT_PUBLIC_WS_URL=http://localhost:3001

# Mode fixtures (pas besoin du backend)
NEXT_PUBLIC_USE_MOCK_DATA=true
```

### Mode Production (avec API réelle)

```bash
# URL de l'API Backend
NEXT_PUBLIC_API_URL=http://localhost:3001

# URL du WebSocket
NEXT_PUBLIC_WS_URL=http://localhost:3001

# Mode API réelle (nécessite le backend)
NEXT_PUBLIC_USE_MOCK_DATA=false
```

## 🚀 Commande rapide

### Créer le fichier automatiquement (fixtures)

```bash
cd services/frontend

cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=http://localhost:3001
NEXT_PUBLIC_USE_MOCK_DATA=true
EOF
```

### Créer le fichier automatiquement (API réelle)

```bash
cd services/frontend

cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=http://localhost:3001
NEXT_PUBLIC_USE_MOCK_DATA=false
EOF
```

## 📋 Variables disponibles

| Variable | Description | Valeur par défaut | Requis |
|----------|-------------|-------------------|--------|
| `NEXT_PUBLIC_API_URL` | URL de l'API REST | `http://localhost:3001` | Non* |
| `NEXT_PUBLIC_WS_URL` | URL du WebSocket | `http://localhost:3001` | Non* |
| `NEXT_PUBLIC_USE_MOCK_DATA` | Mode fixtures ou API | `true` | Non* |

\* *Si non défini, utilise les fixtures par défaut*

## ⚙️ Fonctionnement

### Sans fichier `.env.local`

Si vous ne créez pas de fichier `.env.local`, l'application fonctionne quand même avec les valeurs par défaut définies dans `src/lib/api/config.ts` :

```typescript
export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
  wsURL: process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:3001',
  useMockData: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true' || true,
}
```

### Avec `NEXT_PUBLIC_USE_MOCK_DATA=true`

✅ Utilise les fixtures (données simulées)  
✅ Pas besoin du backend  
✅ Mises à jour toutes les 30 secondes  
✅ Parfait pour le développement frontend  

### Avec `NEXT_PUBLIC_USE_MOCK_DATA=false`

✅ Connexion au backend réel  
✅ WebSocket pour temps réel  
✅ Données depuis MongoDB via l'API  
❗ Nécessite que le backend soit démarré  

## 🔄 Changer de mode

Pour basculer entre fixtures et API réelle :

1. **Modifier `.env.local`** : Changer `NEXT_PUBLIC_USE_MOCK_DATA`
2. **Redémarrer Next.js** : `npm run dev` (les variables d'env nécessitent un restart)

## 🚫 Fichiers à ne pas committer

Ajoutez à votre `.gitignore` (déjà fait) :

```
.env.local
.env*.local
.env
```

## 📚 Plus d'informations

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [API Integration Guide](./API_INTEGRATION.md)
- [README](./README.md)

