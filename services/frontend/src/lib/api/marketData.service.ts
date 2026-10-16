/**
 * Service pour les données de marché
 */

import { apiClient } from './client'
import { API_ENDPOINTS } from './config'
import { Crypto, PriceHistory, MarketData, ApiCrypto, ApiMarketData } from '@/types/crypto'

export class MarketDataService {
  /**
   * Récupérer toutes les cryptos
   */
  async getAllCryptos(): Promise<Crypto[]> {
    const apiCryptos = await apiClient.get<ApiCrypto[]>(API_ENDPOINTS.getAllCryptos)

    // Convertir les données de l'API vers le format Crypto
    return apiCryptos.map(apiCrypto => ({
      id: apiCrypto.id,
      symbol: apiCrypto.symbol,
      name: apiCrypto.name,
      logo: apiCrypto.logo,
      price: 0,
      changePercent24h: 0,
      volume24h: 0,
      marketCap: 0,
      high24h: 0,
      low24h: 0,
      lastUpdate: new Date(),
    }))
  }

  /**
   * Récupérer une crypto spécifique avec ses données de marché
   */
  async getCrypto(symbol: string): Promise<Crypto> {
    const apiData = await apiClient.get<ApiMarketData>(API_ENDPOINTS.getCrypto(symbol))

    // Convertir les données de l'API vers le format Crypto
    return {
      symbol: apiData.symbol,
      name: apiData.name,
      price: apiData.currentPrice,
      changePercent24h: apiData.change24h,
      volume24h: apiData.volume24h,
      marketCap: apiData.marketCap,
      high24h: apiData.high24h,
      low24h: apiData.low24h,
      lastUpdate: new Date(apiData.lastUpdate),
      indicators: apiData.indicators,
    }
  }

  /**
   * Récupérer l'historique des prix
   */
  async getHistory(symbol: string, timeframe: string = '1h'): Promise<PriceHistory[]> {
    const history = await apiClient.get<PriceHistory[]>(API_ENDPOINTS.getHistory(symbol, timeframe))

    // Convertir les timestamps en nombres si nécessaire
    return history.map(item => ({
      ...item,
      timestamp: typeof item.timestamp === 'string'
        ? new Date(item.timestamp).getTime()
        : item.timestamp,
      close: item.price || item.close,
    }))
  }

  /**
   * Récupérer les données complètes de marché
   */
  async getMarketData(symbol: string): Promise<MarketData> {
    const [crypto, history] = await Promise.all([
      this.getCrypto(symbol),
      this.getHistory(symbol),
    ])

    return {
      crypto,
      history,
    }
  }

  /**
   * Vérifier la santé de l'API
   */
  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    return apiClient.get(API_ENDPOINTS.health)
  }
}

export const marketDataService = new MarketDataService()

