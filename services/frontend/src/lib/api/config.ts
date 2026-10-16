/**
 * Configuration de l'API
 */

export const API_CONFIG = {
  // URL de base de l'API REST
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3002',

  // URL du WebSocket
  wsURL: process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:3002',

  // Timeout pour les requêtes (en ms)
  timeout: 30000,

  // Mode de développement (fixtures vs API réelle)
  useMockData: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true',
}

export const API_ENDPOINTS = {
  // Market data
  getAllCryptos: '/api/market-data/all',
  getCrypto: (symbol: string) => `/api/market-data/${symbol}`,
  getHistory: (symbol: string, timeframe: string) => `/api/market-data/${symbol}/history?timeframe=${timeframe}`,
  
  // Analytics
  getAnalytics: (symbol: string) => `/api/analytics/${symbol}`,
  
  // Alerts
  getAlerts: '/api/alerts',
  createAlert: '/api/alerts',
  deleteAlert: (id: string) => `/api/alerts/${id}`,
  
  // Health
  health: '/api/health',
}

export const WS_EVENTS = {
  // Client -> Server
  SUBSCRIBE: 'subscribe',
  UNSUBSCRIBE: 'unsubscribe',
  
  // Server -> Client
  PRICE_UPDATE: 'price-update',
  MARKET_DATA: 'market-data',
  ALERT_TRIGGERED: 'alert-triggered',
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
}

