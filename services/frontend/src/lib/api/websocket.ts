/**
 * Client WebSocket pour les données en temps réel
 */

import { io, Socket } from 'socket.io-client'
import { API_CONFIG, WS_EVENTS } from './config'

type EventCallback = (data: any) => void

class WebSocketClient {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 2000

  connect(): void {
    if (this.socket?.connected) {
      console.log('WebSocket déjà connecté')
      return
    }

    this.socket = io(API_CONFIG.wsURL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.setupEventHandlers()
  }

  private setupEventHandlers(): void {
    if (!this.socket) return

    this.socket.on(WS_EVENTS.CONNECT, () => {
      console.log('✅ WebSocket connecté')
      this.reconnectAttempts = 0
    })

    this.socket.on(WS_EVENTS.DISCONNECT, (reason) => {
      console.log('❌ WebSocket déconnecté:', reason)
      this.handleReconnect()
    })

    this.socket.on(WS_EVENTS.ERROR, (error) => {
      console.error('❌ Erreur WebSocket:', error)
    })
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
    } else {
      console.error('❌ Nombre maximum de tentatives de reconnexion atteint')
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      console.log('WebSocket déconnecté')
    }
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false
  }

  // Souscrire à un symbole
  subscribe(symbol: string | string[]): void {
    if (!this.socket?.connected) {
      console.warn('WebSocket non connecté, impossible de souscrire')
      return
    }
    this.socket.emit(WS_EVENTS.SUBSCRIBE, { symbols: Array.isArray(symbol) ? symbol : [symbol] })
  }

  // Se désabonner d'un symbole
  unsubscribe(symbol: string | string[]): void {
    if (!this.socket?.connected) return
    this.socket.emit(WS_EVENTS.UNSUBSCRIBE, { symbols: Array.isArray(symbol) ? symbol : [symbol] })
  }

  // Écouter les mises à jour de prix
  onPriceUpdate(callback: EventCallback): () => void {
    if (!this.socket) return () => {}
    this.socket.on(WS_EVENTS.PRICE_UPDATE, callback)
    return () => this.socket?.off(WS_EVENTS.PRICE_UPDATE, callback)
  }

  // Écouter les données de marché
  onMarketData(callback: EventCallback): () => void {
    if (!this.socket) return () => {}
    this.socket.on(WS_EVENTS.MARKET_DATA, callback)
    return () => this.socket?.off(WS_EVENTS.MARKET_DATA, callback)
  }

  // Écouter les alertes
  onAlert(callback: EventCallback): () => void {
    if (!this.socket) return () => {}
    this.socket.on(WS_EVENTS.ALERT_TRIGGERED, callback)
    return () => this.socket?.off(WS_EVENTS.ALERT_TRIGGERED, callback)
  }

  // Écouter un événement personnalisé
  on(event: string, callback: EventCallback): () => void {
    if (!this.socket) return () => {}
    this.socket.on(event, callback)
    return () => this.socket?.off(event, callback)
  }

  // Émettre un événement
  emit(event: string, data?: any): void {
    if (!this.socket?.connected) {
      console.warn('WebSocket non connecté, impossible d\'émettre')
      return
    }
    this.socket.emit(event, data)
  }
}

// Instance singleton
export const wsClient = new WebSocketClient()

