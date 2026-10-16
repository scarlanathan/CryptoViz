const { MongoClient } = require('mongodb');
const logger = require('../utils/logger');

class DatabaseService {
  constructor(config) {
    this.uri = config.uri;
    this.client = null;
    this.db = null;
  }

  async connect() {
    logger.info('Connecting to MongoDB:', this.uri);
    this.client = new MongoClient(this.uri);
    await this.client.connect();
    this.db = this.client.db(); // 使用 URI 里的数据库名 cryptoviz
    logger.info('MongoDB connected');
  }

  getDb() {
    if (!this.db) {
      throw new Error('MongoDB not connected');
    }
    return this.db;
  }

  collection(name) {
    if (!this.db) {
      throw new Error('MongoDB not connected');
    }
    return this.db.collection(name);
  }

  async disconnect() {
    if (this.client) {
      await this.client.close();
      logger.info('MongoDB disconnected');
    }
  }
}

module.exports = DatabaseService;
