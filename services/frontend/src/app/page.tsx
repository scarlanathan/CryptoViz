'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { CryptoChart } from '@/components/CryptoChart'
import { useMarketData } from '@/hooks/useMarketData'
import { wsClient, API_CONFIG } from '@/lib/api'
import { Crypto } from '@/types/crypto'

export default function HomePage() {
  const { cryptos: initialCryptos, marketDataMap: initialMarketDataMap, isLoading, error } = useMarketData()
  const [cryptos, setCryptos] = useState<Crypto[]>([])
  const [marketDataMap, setMarketDataMap] = useState(initialMarketDataMap)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [mounted, setMounted] = useState(false)
  const [isConnected, setIsConnected] = useState(false)

  // Éviter l'erreur d'hydratation
  useEffect(() => {
    setMounted(true)
    setLastUpdate(new Date())
  }, [])

  // Initialiser les cryptos et marketDataMap
  useEffect(() => {
    if (initialCryptos.length > 0) {
      setCryptos(initialCryptos)
    }
  }, [initialCryptos])

  useEffect(() => {
    setMarketDataMap(initialMarketDataMap)
  }, [initialMarketDataMap])

  // Configurer la connexion WebSocket
  useEffect(() => {
    if (API_CONFIG.useMockData) {
      console.log('📦 Mode mock data activé - pas de WebSocket')
      return
    }

    console.log('🔌 Connexion au WebSocket...')

    // Se connecter au WebSocket
    wsClient.connect()

    // Vérifier la connexion
    const checkConnection = setInterval(() => {
      setIsConnected(wsClient.isConnected())
    }, 1000)

    // Souscrire aux symboles une fois connecté
    setTimeout(() => {
      if (wsClient.isConnected()) {
        const symbols = initialCryptos.map(c => c.symbol)
        console.log('📡 Souscription aux symboles:', symbols)
        wsClient.subscribe(symbols)
      }
    }, 1000)

    // Écouter les mises à jour de prix
    const unsubscribePrice = wsClient.onPriceUpdate((data) => {
      console.log('💰 Mise à jour de prix reçue:', data)

      const crypto = cryptos.find(c => c.symbol === data.symbol)

      setCryptos(prev =>
        prev.map(c =>
          c.symbol === data.symbol
            ? {
                ...c,
                price: data.price,
                changePercent24h: data.change || c.changePercent24h
              }
            : c
        )
      )

      // Ajouter un nouveau point à l'historique
      if (crypto) {
        setMarketDataMap(prev => {
          const newMap = new Map(prev)
          const existingData = newMap.get(data.symbol)

          if (existingData) {
            const newPoint = {
              timestamp: Date.now(),
              price: data.price,
              open: data.price,
              high: crypto.high24h,
              low: crypto.low24h,
              close: data.price,
              volume: crypto.volume24h,
            }

            // Garder seulement les 100 derniers points
            const updatedHistory = [...existingData.history.slice(-99), newPoint]

            newMap.set(data.symbol, {
              ...existingData,
              history: updatedHistory,
            })
          }

          return newMap
        })
      }

      setLastUpdate(new Date())
    })

    // Écouter les données de marché
    const unsubscribeMarket = wsClient.onMarketData((data) => {
      console.log('📊 Données de marché reçues:', data)
      setCryptos(prev =>
        prev.map(crypto =>
          crypto.symbol === data.symbol
            ? {
                ...crypto,
                price: data.currentPrice,
                changePercent24h: data.change24h,
                volume24h: data.volume24h,
                high24h: data.high24h,
                low24h: data.low24h,
              }
            : crypto
        )
      )

      // Ajouter un nouveau point à l'historique du graphique
      setMarketDataMap(prev => {
        const newMap = new Map(prev)
        const existingData = newMap.get(data.symbol)

        if (existingData) {
          const newPoint = {
            timestamp: Date.now(),
            price: data.currentPrice,
            open: data.currentPrice,
            high: data.high24h,
            low: data.low24h,
            close: data.currentPrice,
            volume: data.volume24h,
          }

          // Garder seulement les 100 derniers points
          const updatedHistory = [...existingData.history.slice(-99), newPoint]

          newMap.set(data.symbol, {
            ...existingData,
            history: updatedHistory,
          })
        }

        return newMap
      })

      setLastUpdate(new Date())
    })

    // Cleanup à la déconnexion
    return () => {
      clearInterval(checkConnection)
      unsubscribePrice()
      unsubscribeMarket()
      wsClient.disconnect()
    }
  }, [initialCryptos, API_CONFIG.useMockData])

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          Crypto Viz
        </h1>
        <p className="text-xl text-gray-300">
          Monitoring des cryptomonnaies en temps réel
        </p>
        <div className="mt-4 flex items-center justify-center space-x-2">
          <div className={`w-2 h-2 rounded-full animate-pulse ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-400">
            {isConnected 
              ? mounted && lastUpdate 
                ? `Données en temps réel - Dernière mise à jour: ${lastUpdate.toLocaleTimeString()}` 
                : 'Données en temps réel'
              : 'Connexion en cours...'}
          </span>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center text-gray-400">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
          <p>Chargement des données...</p>
        </div>
      )}

      {/* Market Overview */}
      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {cryptos.map((crypto) => {
          const isPositive = crypto.changePercent24h >= 0
          return (
            <motion.div
              key={crypto.symbol}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
              className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20 hover:border-white/30 transition-all duration-300"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400 font-medium">{crypto.symbol}</span>
                <motion.span
                  key={crypto.changePercent24h}
                  initial={{ scale: 1.2 }}
                  animate={{ scale: 1 }}
                  className={`text-xs font-medium px-2 py-1 rounded ${
                    isPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}
                >
                  {isPositive ? '+' : ''}{crypto.changePercent24h.toFixed(2)}%
                </motion.span>
              </div>
              <motion.div
                key={crypto.price}
                initial={{ scale: 1.1, color: isPositive ? '#22c55e' : '#ef4444' }}
                animate={{ scale: 1, color: '#ffffff' }}
                transition={{ duration: 0.3 }}
                className="text-xl font-mono font-bold"
              >
                ${crypto.price.toLocaleString('en-US', { 
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2 
                })}
              </motion.div>
              <div className="text-xs text-gray-400 mt-1">
                Vol: ${(crypto.volume24h / 1e9).toFixed(2)}B
              </div>
            </motion.div>
          )
        })}
      </div>
      )}

      {/* Charts Grid */}
      {!isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {cryptos.map((crypto) => {
          const marketData = marketDataMap.get(crypto.symbol)
          if (!marketData) return null

          return (
            <CryptoChart
              key={crypto.symbol}
              symbol={crypto.symbol}
              name={crypto.name}
              currentPrice={crypto.price}
              changePercent={crypto.changePercent24h}
              history={marketData.history}
            />
          )
        })}
      </div>
      )}

      {/* Footer Info */}
      <div className="mt-12 text-center text-sm text-gray-500">
        <p>
          {process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true' 
            ? 'Les données affichées sont des simulations à des fins de démonstration'
            : 'Données en temps réel depuis l\'API'}
        </p>
        <p className="mt-1">Mise à jour automatique toutes les 30 secondes</p>
      </div>
    </div>
  )
}

