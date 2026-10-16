// src/services/webSocketService.js
const logger = require('../utils/logger');

const TRACKED_SYMBOLS = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA'];
const DEFAULT_EXCHANGE = 'okx';
const UPDATE_INTERVAL = 30000; // 30 secondes

class WebSocketService {
    constructor(io, { redis, database, kafka }) {
        this.io = io;
        this.redis = redis;
        this.database = database;
        this.kafka = kafka;

        // Garde trace des abonnements de chaque socket
        this.socketSubscriptions = new Map();
        // Intervalle global pour envoyer les mises à jour
        this.updateInterval = null;
    }

    initialize() {
        this.io.on('connection', (socket) => {
            logger.info(`✅ WebSocket client connected: ${socket.id}`);

            // Initialiser les abonnements pour ce socket
            this.socketSubscriptions.set(socket.id, new Set());

            // Événement: Subscribe à des symboles
            socket.on('subscribe', ({ symbols }) => {
                if (!symbols || !Array.isArray(symbols)) {
                    logger.warn(`Invalid subscribe request from ${socket.id}`);
                    return;
                }

                const subscriptions = this.socketSubscriptions.get(socket.id);
                symbols.forEach(symbol => {
                    subscriptions.add(symbol);
                    logger.info(`Socket ${socket.id} subscribed to ${symbol}`);
                });

                // Envoyer immédiatement les données pour les nouveaux abonnements
                this.sendImmediateUpdate(socket, symbols);
            });

            // Événement: Unsubscribe de symboles
            socket.on('unsubscribe', ({ symbols }) => {
                if (!symbols || !Array.isArray(symbols)) return;

                const subscriptions = this.socketSubscriptions.get(socket.id);
                symbols.forEach(symbol => {
                    subscriptions.delete(symbol);
                    logger.info(`Socket ${socket.id} unsubscribed from ${symbol}`);
                });
            });

            // Événement: Subscribe legacy (compatibilité)
            socket.on('subscribe_market_data', ({ symbol, exchange }) => {
                if (!symbol) return;
                const subscriptions = this.socketSubscriptions.get(socket.id);
                subscriptions.add(symbol);
                logger.info(`Socket ${socket.id} subscribed to ${symbol} (legacy)`);
                this.sendImmediateUpdate(socket, [symbol]);
            });

            // Déconnexion
            socket.on('disconnect', () => {
                logger.info(`❌ WebSocket client disconnected: ${socket.id}`);
                this.socketSubscriptions.delete(socket.id);
            });
        });

        // Démarrer l'intervalle de mise à jour global
        this.startUpdateInterval();
        logger.info('WebSocket update interval started');
    }

    /**
     * Envoie immédiatement les données pour les symboles spécifiés
     */
    async sendImmediateUpdate(socket, symbols) {
        for (const symbol of symbols) {
            await this.sendMarketDataToSocket(socket, symbol);
        }
    }

    /**
     * Démarre l'intervalle de mise à jour global
     */
    startUpdateInterval() {
        this.updateInterval = setInterval(() => {
            this.broadcastUpdates();
        }, UPDATE_INTERVAL);
    }

    /**
     * Diffuse les mises à jour à tous les clients connectés
     */
    async broadcastUpdates() {
        const sockets = await this.io.fetchSockets();

        for (const socket of sockets) {
            const subscriptions = this.socketSubscriptions.get(socket.id);
            if (!subscriptions || subscriptions.size === 0) continue;

            for (const symbol of subscriptions) {
                await this.sendMarketDataToSocket(socket, symbol);
            }
        }
    }

    /**
     * Envoie les données de marché pour un symbole à un socket spécifique
     */
    async sendMarketDataToSocket(socket, symbol, exchange = DEFAULT_EXCHANGE) {
        try {
            // Récupérer depuis Redis
            const redisKey = `market_data:${exchange}:${symbol}/USDT`;
            const realtimeData = await this.redis.getJson(redisKey);

            if (!realtimeData) {
                // Pas de données, on ne fait rien
                return;
            }

            // Récupérer les indicateurs techniques depuis MongoDB
            const db = this.database.getDb();
            const collection = db.collection('processed_data');

            const latestData = await collection
                .find({ symbol: `${symbol}/USDT`, exchange })
                .sort({ timestamp: -1 })
                .limit(1)
                .toArray();

            // Construire la réponse
            const dbData = latestData[0];
            const marketData = {
                symbol,
                currentPrice: realtimeData.close || dbData?.raw_data?.close || dbData?.analytics?.price_analytics?.current_price || 0,
                change24h: realtimeData.percentage || dbData?.raw_data?.percentage || 0,
                volume24h: realtimeData.quote_volume || dbData?.raw_data?.quote_volume || 0,
                high24h: realtimeData.high || dbData?.raw_data?.high || 0,
                low24h: realtimeData.low || dbData?.raw_data?.low || 0,
                lastUpdate: new Date().toISOString(),
                indicators: dbData?.indicators || {},
            };

            // Émettre l'événement 'market-data'
            socket.emit('market-data', marketData);

            // Émettre également 'price-update' pour compatibilité
            socket.emit('price-update', {
                symbol,
                price: marketData.currentPrice,
                change: marketData.change24h,
                timestamp: marketData.lastUpdate,
            });

            // Legacy event (compatibilité)
            socket.emit('market_data_update', {
                key: redisKey,
                data: marketData,
                ts: marketData.lastUpdate,
            });

        } catch (err) {
            logger.error(`Error sending market data for ${symbol}:`, err);
        }
    }

    /**
     * Diffuse une alerte à tous les clients connectés
     */
    broadcastAlert(alert) {
        this.io.emit('alert-triggered', alert);
        logger.info(`Alert broadcasted: ${alert.type} for ${alert.symbol}`);
    }

    async cleanup() {
        // Arrêter l'intervalle de mise à jour
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        // Nettoyer les abonnements
        this.socketSubscriptions.clear();

        logger.info('WebSocket service cleaned up');
    }
}

module.exports = WebSocketService;
