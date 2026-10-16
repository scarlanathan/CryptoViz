const express = require('express');
const router = express.Router();

/**
 * GET /api/analytics?symbol=BTC/USDT
 */
router.get('/', async (req, res, next) => {
  try {
    const { symbol } = req.query;
    if (!symbol) {
      return res.status(400).json({ error: 'symbol query param is required' });
    }

    const services = req.app.locals.services;
    const redis = services.redis;

    const key = `analytics:${symbol}`;
    const data = await redis.getJson(key);

    if (!data) {
      return res.status(404).json({ error: 'Analytics not found for symbol', symbol });
    }

    res.json(data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
