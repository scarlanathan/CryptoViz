"""
CRYPTO VIZ - Data Processor Service
Python + pandas for real-time cryptocurrency data processing and analytics
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.processor import DataProcessor
from src.config import Settings
from src.models import ProcessorStatus, HealthResponse
from src.utils.logger import setup_logger

# Initialize settings
settings = Settings()
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting CRYPTO VIZ Data Processor Service")

    # Initialize data processor
    processor = DataProcessor(settings)
    await processor.initialize()

    # Store processor in app state
    app.state.processor = processor

    # Start processing tasks
    processing_task = asyncio.create_task(processor.start_processing())

    try:
        yield
    finally:
        logger.info("Shutting down Data Processor Service")
        processing_task.cancel()
        await processor.cleanup()


# Initialize FastAPI app
app = FastAPI(
    title="CRYPTO VIZ - Data Processor",
    description="Real-time cryptocurrency data processing and analytics using Python + pandas",
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
        processor = app.state.processor
        is_healthy = await processor.health_check()

        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            service="data-processor",
            version="1.0.0",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/status", response_model=ProcessorStatus)
async def get_status():
    """Get processor status"""
    try:
        processor = app.state.processor
        status = await processor.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@app.get("/analytics/current")
async def get_current_analytics():
    """Get current analytics"""
    try:
        processor = app.state.processor
        analytics = await processor.get_current_analytics()
        return {"analytics": analytics}
    except Exception as e:
        logger.error(f"Failed to get current analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current analytics")


@app.get("/analytics/history")
async def get_analytics_history(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 100
):
    """Get analytics history"""
    try:
        processor = app.state.processor
        history = await processor.get_analytics_history(symbol, timeframe, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Failed to get analytics history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics history")


@app.get("/indicators/{symbol}")
async def get_technical_indicators(symbol: str):
    """Get technical indicators for a symbol"""
    try:
        processor = app.state.processor
        indicators = await processor.get_technical_indicators(symbol)
        return {"symbol": symbol, "indicators": indicators}
    except Exception as e:
        logger.error(f"Failed to get indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get indicators for {symbol}")


@app.get("/alerts")
async def get_alerts():
    """Get recent alerts"""
    try:
        processor = app.state.processor
        alerts = await processor.get_recent_alerts()
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )