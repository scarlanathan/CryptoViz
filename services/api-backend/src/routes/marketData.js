const express = require('express');
const router = express.Router();

const TRACKED_SYMBOLS = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA'];
const DEFAULT_EXCHANGE = 'okx';

/**
 * GET /api/market-data/all
 * Récupère toutes les cryptos suivies
 */
router.get('/all', async (req, res, next) => {
  try {
    const cryptos = TRACKED_SYMBOLS.map((symbol, index) => ({
      id: index + 1,
      symbol,
      name: getFullName(symbol),
      logo: getLogoUrl(symbol),
    }));

    res.json(cryptos);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/market-data/:symbol
 * Récupère les données de marché pour un symbole spécifique
 */
router.get('/:symbol', async (req, res, next) => {
  try {
    const { symbol } = req.params;
    const { exchange = DEFAULT_EXCHANGE } = req.query;

    const services = req.app.locals.services;
    const redis = services.redis;
    const database = services.database;

    // Récupérer depuis Redis (données en temps réel)
    const key = `market_data:${exchange}:${symbol}/USDT`;
    const realtimeData = await redis.getJson(key);

    // Récupérer depuis MongoDB (données historiques)
    const db = database.getDb();
    const collection = db.collection('processed_data');

    // Dernières données avec indicateurs techniques
    const latestData = await collection
      .find({ symbol: `${symbol}/USDT`, exchange })
      .sort({ timestamp: -1 })
      .limit(1)
      .toArray();

    // Préparer la réponse
    const dbData = latestData[0];
    const marketData = {
      symbol,
      name: getFullName(symbol),
      currentPrice: realtimeData?.close || dbData?.raw_data?.close || dbData?.analytics?.price_analytics?.current_price || 0,
      change24h: realtimeData?.percentage || dbData?.raw_data?.percentage || 0,
      volume24h: realtimeData?.quote_volume || dbData?.raw_data?.quote_volume || 0,
      high24h: realtimeData?.high || dbData?.raw_data?.high || 0,
      low24h: realtimeData?.low || dbData?.raw_data?.low || 0,
      marketCap: 0, // À calculer si nécessaire
      lastUpdate: new Date().toISOString(),
      indicators: dbData?.indicators || {},
    };

    res.json(marketData);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/market-data/:symbol/history
 * Récupère l'historique des prix
 */
router.get('/:symbol/history', async (req, res, next) => {
  try {
    const { symbol } = req.params;
    const { timeframe = '1h', exchange = DEFAULT_EXCHANGE } = req.query;

    const services = req.app.locals.services;
    const database = services.database;

    const db = database.getDb();
    const collection = db.collection('processed_data');

    // Calculer la limite de temps selon le timeframe
    const now = new Date();
    let startTime = new Date();

    switch (timeframe) {
      case '1h':
        startTime.setHours(now.getHours() - 1);
        break;
      case '24h':
        startTime.setDate(now.getDate() - 1);
        break;
      case '7d':
        startTime.setDate(now.getDate() - 7);
        break;
      case '30d':
        startTime.setDate(now.getDate() - 30);
        break;
      default:
        startTime.setHours(now.getHours() - 1);
    }

    // Récupérer l'historique
    const history = await collection
      .find({
        symbol: `${symbol}/USDT`,
        exchange,
        timestamp: { $gte: startTime },
      })
      .sort({ timestamp: 1 })
      .limit(100)
      .toArray();

    // Formater pour Chart.js
    const formattedHistory = history.map(item => ({
      timestamp: item.timestamp,
      price: item.raw_data?.close || item.analytics?.price_analytics?.current_price || 0,
      volume: item.raw_data?.quote_volume || 0,
      high: item.raw_data?.high || 0,
      low: item.raw_data?.low || 0,
      open: item.raw_data?.open || 0,
    }));

    res.json(formattedHistory);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/market-data (legacy endpoint)
 */
router.get('/', async (req, res, next) => {
  try {
    const { symbol, exchange = DEFAULT_EXCHANGE } = req.query;
    if (!symbol) {
      return res.status(400).json({ error: 'symbol query param is required' });
    }

    const services = req.app.locals.services;
    const redis = services.redis;

    const key = `market_data:${exchange}:${symbol}`;
    const data = await redis.getJson(key);

    if (!data) {
      return res.status(404).json({
        error: 'Market data not found',
        symbol,
        exchange,
      });
    }

    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Helper functions
function getFullName(symbol) {
  const names = {
    BTC: 'Bitcoin',
    ETH: 'Ethereum',
    BNB: 'Binance Coin',
    SOL: 'Solana',
    ADA: 'Cardano',
  };
  return names[symbol] || symbol;
}

function getLogoUrl(symbol) {
  return `https://cryptologos.cc/logos/${symbol.toLowerCase()}-logo.png`;
}

module.exports = router;
