/**
 * Hook pour récupérer les données de marché
 */

import { useEffect, useState } from 'react'
import { Crypto, MarketData } from '@/types/crypto'
import { API_CONFIG, marketDataService } from '@/lib/api'
import * as fixtures from '@/lib/fixtures'

interface UseMarketDataReturn {
  cryptos: Crypto[]
  marketDataMap: Map<string, MarketData>
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useMarketData(): UseMarketDataReturn {
  const [cryptos, setCryptos] = useState<Crypto[]>([])
  const [marketDataMap, setMarketDataMap] = useState<Map<string, MarketData>>(new Map())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      if (API_CONFIG.useMockData) {
        // Utiliser les fixtures
        const mockCryptos = fixtures.getAllCryptos()
        setCryptos(mockCryptos)

        const dataMap = new Map<string, MarketData>()
        mockCryptos.forEach(crypto => {
          const data = fixtures.getMarketData(crypto.symbol)
          if (data) {
            dataMap.set(crypto.symbol, data)
          }
        })
        setMarketDataMap(dataMap)
      } else {
        // Utiliser l'API réelle
        const apiCryptos = await marketDataService.getAllCryptos()
        setCryptos(apiCryptos)

        const dataMap = new Map<string, MarketData>()
        await Promise.all(
          apiCryptos.map(async (crypto) => {
            const data = await marketDataService.getMarketData(crypto.symbol)
            dataMap.set(crypto.symbol, data)
          })
        )
        setMarketDataMap(dataMap)
      }
    } catch (err) {
      setError(err as Error)
      console.error('Erreur lors de la récupération des données:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return {
    cryptos,
    marketDataMap,
    isLoading,
    error,
    refetch: fetchData,
  }
}

