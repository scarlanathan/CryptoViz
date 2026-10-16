"""
CRYPTO VIZ - Data Collector Service
Python + asyncio + ccxt for real-time cryptocurrency data collection
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.collector import DataCollector
from src.config import Settings
from src.models import CollectorStatus, HealthResponse
from src.utils.logger import setup_logger

# Initialize settings
settings = Settings()
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting CRYPTO VIZ Data Collector Service")

    # Initialize data collector
    collector = DataCollector(settings)
    await collector.initialize()

    # Store collector in app state
    app.state.collector = collector

    # Start collection tasks
    collection_task = asyncio.create_task(collector.start_collection())

    try:
        yield
    finally:
        logger.info("Shutting down Data Collector Service")
        collection_task.cancel()
        await collector.cleanup()


# Initialize FastAPI app
app = FastAPI(
    title="CRYPTO VIZ - Data Collector",
    description="Real-time cryptocurrency data collection service using Python + asyncio + ccxt",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        collector = app.state.collector
        is_healthy = await collector.health_check()

        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            service="data-collector",
            version="1.0.0",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/status", response_model=CollectorStatus)
async def get_status():
    """Get collector status"""
    try:
        collector = app.state.collector
        status = await collector.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@app.post("/start")
async def start_collection():
    """Start data collection"""
    try:
        collector = app.state.collector
        await collector.start_collection()
        return {"message": "Collection started"}
    except Exception as e:
        logger.error(f"Failed to start collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to start collection")


@app.post("/stop")
async def stop_collection():
    """Stop data collection"""
    try:
        collector = app.state.collector
        await collector.stop_collection()
        return {"message": "Collection stopped"}
    except Exception as e:
        logger.error(f"Failed to stop collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop collection")


@app.get("/exchanges")
async def get_exchanges():
    """Get available exchanges"""
    try:
        collector = app.state.collector
        exchanges = await collector.get_exchanges()
        return {"exchanges": exchanges}
    except Exception as e:
        logger.error(f"Failed to get exchanges: {e}")
        raise HTTPException(status_code=500, detail="Failed to get exchanges")


@app.get("/symbols/{exchange}")
async def get_symbols(exchange: str):
    """Get available symbols for an exchange"""
    try:
        collector = app.state.collector
        symbols = await collector.get_symbols(exchange)
        return {"exchange": exchange, "symbols": symbols}
    except Exception as e:
        logger.error(f"Failed to get symbols for {exchange}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get symbols for {exchange}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )