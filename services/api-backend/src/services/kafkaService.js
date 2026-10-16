const { Kafka } = require('kafkajs');
const logger = require('../utils/logger');

class KafkaService {
  constructor(config) {
    this.config = config;
    this.kafka = null;
    this.producer = null;
    this.consumer = null; // 以后需要再加
  }

  async initialize() {
    this.kafka = new Kafka({
      clientId: this.config.clientId,
      brokers: this.config.brokers,
    });

    this.producer = this.kafka.producer();
    await this.producer.connect();
    logger.info('Kafka producer connected');

    // 如果以后要消费消息，可以在这里初始化 consumer
  }

  async disconnect() {
    if (this.producer) {
      await this.producer.disconnect();
      logger.info('Kafka producer disconnected');
    }
    // consumer 同理
  }
}

module.exports = KafkaService;
