require('dotenv').config();

const parseCorsOrigins = () => {
  if (!process.env.CORS_ORIGINS) return ['http://localhost:3000'];
  return process.env.CORS_ORIGINS.split(',').map(o => o.trim());
};

module.exports = {
  port: process.env.PORT || 3002,
  nodeEnv: process.env.NODE_ENV || 'development',
  corsOrigins: parseCorsOrigins(),

  mongodb: {
    uri:
      process.env.MONGODB_URI ||
      'mongodb://cryptovizuser:cryptovizpass@127.0.0.1:27017/cryptoviz?authSource=admin',
  },

  redis: {
    host: process.env.REDIS_HOST || '127.0.0.1',
    port: Number(process.env.REDIS_PORT || 6379),
    password: process.env.REDIS_PASSWORD || "redis_password",
  },

  kafka: {
    clientId: process.env.KAFKA_CLIENT_ID || 'crypto-viz-backend',
    brokers: (process.env.KAFKA_BROKERS || '127.0.0.1:9092')
      .split(',')
      .map(b => b.trim()),
  },
};
