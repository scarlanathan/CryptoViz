import { Crypto, PriceHistory, MarketData } from '@/types/crypto'

// Données de base pour les principales cryptos
const BASE_CRYPTOS: Array<Omit<Crypto, 'lastUpdate'>> = [
  {
    symbol: 'BTC',
    name: 'Bitcoin',
    price: 67234.56,
    change24h: 1234.56,
    changePercent24h: 1.87,
    volume24h: 28456789000,
    marketCap: 1316789000000,
    high24h: 68123.45,
    low24h: 65890.12,
  },
  {
    symbol: 'ETH',
    name: 'Ethereum',
    price: 3456.78,
    change24h: -45.23,
    changePercent24h: -1.29,
    volume24h: 15678234000,
    marketCap: 415678234000,
    high24h: 3512.34,
    low24h: 3398.45,
  },
  {
    symbol: 'BNB',
    name: 'Binance Coin',
    price: 612.34,
    change24h: 8.56,
    changePercent24h: 1.42,
    volume24h: 1234567000,
    marketCap: 94567890000,
    high24h: 621.45,
    low24h: 598.23,
  },
  {
    symbol: 'SOL',
    name: 'Solana',
    price: 178.92,
    change24h: 12.34,
    changePercent24h: 7.41,
    volume24h: 3456789000,
    marketCap: 84567890000,
    high24h: 182.45,
    low24h: 165.23,
  },
  {
    symbol: 'ADA',
    name: 'Cardano',
    price: 0.6789,
    change24h: 0.0234,
    changePercent24h: 3.57,
    volume24h: 567890000,
    marketCap: 23456789000,
    high24h: 0.6934,
    low24h: 0.6512,
  },
]

/**
 * Génère un historique de prix avec variation aléatoire logique
 */
export function generatePriceHistory(
  basePrice: number,
  points: number = 50
): PriceHistory[] {
  const history: PriceHistory[] = []
  const now = Date.now()
  const intervalMs = 30 * 1000 // 30 secondes entre chaque point

  let currentPrice = basePrice

  for (let i = points; i >= 0; i--) {
    const timestamp = now - i * intervalMs
    
    // Variation aléatoire entre -8% et +8% (plus visible)
    const variation = (Math.random() - 0.5) * 0.16
    currentPrice = currentPrice * (1 + variation)
    
    const open = currentPrice
    // Variation intra-chandelier plus importante
    const close = currentPrice * (1 + (Math.random() - 0.5) * 0.03)
    const high = Math.max(open, close) * (1 + Math.random() * 0.02)
    const low = Math.min(open, close) * (1 - Math.random() * 0.02)
    const volume = basePrice * 1000000 * (0.5 + Math.random())

    history.push({
      timestamp,
      open,
      high,
      low,
      close,
      volume,
    })

    currentPrice = close
  }

  return history
}

/**
 * Simule une mise à jour de prix en temps réel
 */
export function simulatePriceUpdate(currentPrice: number, volatility: number = 0.01): number {
  // Volatilité par défaut : ±1%
  const change = (Math.random() - 0.5) * 2 * volatility
  return currentPrice * (1 + change)
}

/**
 * Récupère toutes les cryptos avec des données à jour
 */
export function getAllCryptos(): Crypto[] {
  return BASE_CRYPTOS.map(crypto => ({
    ...crypto,
    lastUpdate: new Date(),
  }))
}

/**
 * Récupère une crypto par son symbole
 */
export function getCryptoBySymbol(symbol: string): Crypto | null {
  const crypto = BASE_CRYPTOS.find(c => c.symbol === symbol)
  if (!crypto) return null
  
  return {
    ...crypto,
    lastUpdate: new Date(),
  }
}

/**
 * Récupère les données de marché (crypto + historique)
 */
export function getMarketData(symbol: string): MarketData | null {
  const crypto = getCryptoBySymbol(symbol)
  if (!crypto) return null

  return {
    crypto,
    history: generatePriceHistory(crypto.price, 50), // 50 points = 4 heures d'historique
  }
}

/**
 * Simule une mise à jour WebSocket
 */
export function generateRealtimeUpdate(symbol: string): Partial<Crypto> | null {
  const crypto = getCryptoBySymbol(symbol)
  if (!crypto) return null

  // Volatilité plus importante pour des changements visuels
  const newPrice = simulatePriceUpdate(crypto.price, 0.015) // ±1.5% par mise à jour
  const change = newPrice - crypto.price
  const changePercent = (change / crypto.price) * 100

  return {
    symbol,
    price: newPrice,
    change24h: (crypto.change24h ?? 0) + change,
    changePercent24h: crypto.changePercent24h + changePercent,
    lastUpdate: new Date(),
  }
}

