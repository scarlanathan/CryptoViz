/**
 * CRYPTO VIZ - API Backend Server
 * Node.js + Express + WebSockets
 */

require("dotenv").config();
require("express-async-errors");

const express = require("express");
const http = require("http");
const socketIo = require("socket.io");
const cors = require("cors");
const helmet = require("helmet");
const compression = require("compression");
const morgan = require("morgan");

const config = require("./src/config");
const logger = require("./src/utils/logger");
const errorHandler = require("./src/middleware/errorHandler");
const rateLimiter = require("./src/middleware/rateLimiter");

// Import services
const KafkaService = require("./src/services/kafkaService");
const DatabaseService = require("./src/services/databaseService");
const RedisService = require("./src/services/redisService");
const WebSocketService = require("./src/services/webSocketService");

// Import routes
const healthRoutes = require("./src/routes/health");
const analyticsRoutes = require("./src/routes/analytics");
const marketDataRoutes = require("./src/routes/marketData");
const alertsRoutes = require("./src/routes/alerts");

class Server {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);

        // -------------------
        // WebSocket Server
        // -------------------
        this.io = socketIo(this.server, {
            cors: {
                origin: config.corsOrigins,
                methods: ["GET", "POST"],
            },
        });

        // Services containers
        this.kafkaService = null;
        this.databaseService = null;
        this.redisService = null;
        this.webSocketService = null;
    }

    async initialize() {
        logger.info("Initializing CRYPTO VIZ API Backend Server");

        try {
            await this.initializeServices();
            this.setupMiddleware();
            this.setupRoutes();
            this.setupErrorHandling();
            this.setupWebSocket();
            this.setupGracefulShutdown();

            logger.info("Server initialized successfully");
        } catch (error) {
            logger.error("Failed to initialize server:", error);
            throw error;
        }
    }

    async initializeServices() {
        // -------------------
        // MongoDB
        // -------------------
        this.databaseService = new DatabaseService(config.mongodb);
        await this.databaseService.connect();

        // -------------------
        // Redis
        // -------------------
        this.redisService = new RedisService(config.redis);
        await this.redisService.connect();

        // -------------------
        // Kafka
        // -------------------
        this.kafkaService = new KafkaService(config.kafka);
        await this.kafkaService.initialize();

        // Make available to all routes
        this.app.locals.services = {
            database: this.databaseService,
            redis: this.redisService,
            kafka: this.kafkaService,
        };
    }

    setupMiddleware() {
        this.app.use(helmet());

        this.app.use(
            cors({
                origin: config.corsOrigins,
                credentials: true,
            })
        );

        this.app.use(compression());

        this.app.use(
            morgan("combined", {
                stream: { write: (msg) => logger.info(msg.trim()) },
            })
        );

        this.app.use(express.json({ limit: "10mb" }));
        this.app.use(express.urlencoded({ extended: true }));

        this.app.use("/api/", rateLimiter);

        this.app.use((req, res, next) => {
            req.id = require("uuid").v4();
            res.setHeader("X-Request-ID", req.id);
            next();
        });
    }

    setupRoutes() {
        this.app.use("/api/health", healthRoutes);
        this.app.use("/api/analytics", analyticsRoutes);
        this.app.use("/api/market-data", marketDataRoutes);
        this.app.use("/api/alerts", alertsRoutes);

        this.app.get("/", (req, res) => {
            res.json({
                service: "CRYPTO VIZ API Backend",
                version: "1.0.0",
                status: "running",
                timestamp: new Date().toISOString(),
            });
        });

        this.app.use("*", (req, res) => {
            res.status(404).json({
                error: "Not Found",
                message: `Route ${req.originalUrl} not found`,
                timestamp: new Date().toISOString(),
            });
        });
    }

    setupErrorHandling() {
        this.app.use(errorHandler);
    }

    // -------------------------
    // WebSocket Real-time Setup
    // -------------------------
    setupWebSocket() {
        this.webSocketService = new WebSocketService(this.io, {
            database: this.databaseService,
            redis: this.redisService,
            kafka: this.kafkaService,
        });

        this.webSocketService.initialize();
        logger.info("WebSocket service started");
    }

    setupGracefulShutdown() {
        const shutdown = async (signal) => {
            logger.info(`Received ${signal}. Starting graceful shutdown...`);

            this.server.close(async () => {
                logger.info("HTTP server closed");

                try {
                    if (this.webSocketService) await this.webSocketService.cleanup();
                    if (this.kafkaService) await this.kafkaService.disconnect();
                    if (this.redisService) await this.redisService.disconnect();
                    if (this.databaseService) await this.databaseService.disconnect();

                    logger.info("Graceful shutdown completed");
                    process.exit(0);
                } catch (error) {
                    logger.error("Error during shutdown:", error);
                    process.exit(1);
                }
            });

            setTimeout(() => {
                logger.error("Forced shutdown after timeout");
                process.exit(1);
            }, 30000);
        };

        process.on("SIGTERM", () => shutdown("SIGTERM"));
        process.on("SIGINT", () => shutdown("SIGINT"));

        process.on("uncaughtException", (err) => {
            logger.error("Uncaught exception:", err);
            process.exit(1);
        });

        process.on("unhandledRejection", (reason, promise) => {
            logger.error("Unhandled rejection:", reason);
            process.exit(1);
        });
    }

    async start() {
        const port = config.port || 3002;

        this.server.listen(port, () => {
            logger.info(`CRYPTO VIZ API Backend listening on port ${port}`);
            logger.info(`Environment: ${config.nodeEnv}`);
        });
    }
}

if (require.main === module) {
    const server = new Server();
    server
        .initialize()
        .then(() => server.start())
        .catch((err) => {
            logger.error("Failed to start server:", err);
            process.exit(1);
        });
}

module.exports = Server;
