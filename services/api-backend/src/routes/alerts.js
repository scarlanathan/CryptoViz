const express = require('express');
const router = express.Router();

/**
 * GET /api/alerts?symbol=BTC/USDT
 * 从 MongoDB alerts 集合读取
 */
router.get('/', async (req, res, next) => {
  try {
    const { symbol } = req.query;

    const services = req.app.locals.services;
    const db = services.database;

    const collection = db.collection('alerts');

    const query = symbol ? { symbol } : {};
    const alerts = await collection.find(query).sort({ timestamp: -1 }).limit(100).toArray();

    res.json(alerts);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
