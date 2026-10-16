const { createClient } = require('redis');
const logger = require('../utils/logger');

class RedisService {
  constructor(config) {
    this.config = config;
    this.client = null;
  }

  async connect() {
    const { host, port, password } = this.config;

    this.client = createClient({
      socket: { host, port },
      password: password || undefined,
    });

    this.client.on('error', (err) => {
      logger.error('Redis Client Error:', err);
    });

    logger.info(`Connecting to Redis ${host}:${port}`);
    await this.client.connect();
    logger.info('Redis connected');
  }

  async disconnect() {
    if (this.client) {
      await this.client.quit();
      logger.info('Redis disconnected');
    }
  }

  async get(key) {
    return this.client.get(key);
  }

  async getJson(key) {
    const raw = await this.get(key);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (e) {
      logger.error('Failed to parse JSON from Redis key:', key, e);
      return null;
    }
  }
}

module.exports = RedisService;
