/**
 * Hook pour gérer les mises à jour en temps réel
 */

import { useEffect, useRef } from 'react'
import { Crypto, MarketData } from '@/types/crypto'
import { API_CONFIG, wsClient } from '@/lib/api'
import * as fixtures from '@/lib/fixtures'

interface UseRealtimeUpdatesProps {
  cryptos: Crypto[]
  onCryptosUpdate: (updater: (prev: Crypto[]) => Crypto[]) => void
  onMarketDataUpdate: (updater: (prev: Map<string, MarketData>) => Map<string, MarketData>) => void
}

export function useRealtimeUpdates({
  cryptos,
  onCryptosUpdate,
  onMarketDataUpdate,
}: UseRealtimeUpdatesProps) {
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const cryptosRef = useRef(cryptos)

  useEffect(() => {
    cryptosRef.current = cryptos
  }, [cryptos])

  useEffect(() => {
    if (API_CONFIG.useMockData) {
      // Mode fixtures : simuler les mises à jour toutes les 30 secondes
      intervalRef.current = setInterval(() => {
        onCryptosUpdate(prevCryptos =>
          prevCryptos.map(crypto => {
            const update = fixtures.generateRealtimeUpdate(crypto.symbol)
            return update ? { ...crypto, ...update } : crypto
          })
        )

        onMarketDataUpdate(prevMap => {
          const newMap = new Map(prevMap)
          prevMap.forEach((data, symbol) => {
            const crypto = cryptosRef.current.find(c => c.symbol === symbol)
            if (crypto) {
              const newPoint = {
                timestamp: Date.now(),
                open: crypto.price,
                high: crypto.high24h,
                low: crypto.low24h,
                close: crypto.price,
                volume: crypto.volume24h,
              }

              const updatedHistory = [...data.history.slice(-49), newPoint]
              newMap.set(symbol, {
                ...data,
                history: updatedHistory,
              })
            }
          })
          return newMap
        })
      }, 30000)

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
      }
    } else {
      // Mode API réelle : utiliser WebSocket
      wsClient.connect()

      // Souscrire à tous les symboles
      const symbols = cryptosRef.current.map(c => c.symbol)
      wsClient.subscribe(symbols)

      // Écouter les mises à jour de prix
      const unsubscribePriceUpdate = wsClient.onPriceUpdate((data) => {
        onCryptosUpdate(prevCryptos =>
          prevCryptos.map(crypto =>
            crypto.symbol === data.symbol
              ? { ...crypto, ...data }
              : crypto
          )
        )

        // Ajouter le point à l'historique
        onMarketDataUpdate(prevMap => {
          const newMap = new Map(prevMap)
          const existingData = prevMap.get(data.symbol)
          
          if (existingData) {
            const newPoint = {
              timestamp: data.timestamp || Date.now(),
              open: data.open || data.price,
              high: data.high || data.price,
              low: data.low || data.price,
              close: data.price,
              volume: data.volume || 0,
            }

            const updatedHistory = [...existingData.history.slice(-49), newPoint]
            newMap.set(data.symbol, {
              ...existingData,
              history: updatedHistory,
            })
          }
          
          return newMap
        })
      })

      return () => {
        unsubscribePriceUpdate()
        if (wsClient.isConnected()) {
             wsClient.unsubscribe(symbols)
             wsClient.disconnect()
        }
      }
    }
  }, [onCryptosUpdate, onMarketDataUpdate])

  return {
    isConnected: API_CONFIG.useMockData ? true : wsClient.isConnected(),
  }
}

