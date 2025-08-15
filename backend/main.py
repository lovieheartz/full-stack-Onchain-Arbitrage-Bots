from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import uvicorn

from routes.strategies import router as strategies_router
from routes.spreadsheet import router as spreadsheet_router
from routes.health import router as health_router

load_dotenv()

app = FastAPI(
    title="On-Chain Arbitrage API",
    description="Backend API for managing 7 on-chain arbitrage strategies",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategies_router, prefix="/api/strategies", tags=["strategies"])
app.include_router(spreadsheet_router, prefix="/api/spreadsheet", tags=["spreadsheet"])
app.include_router(health_router, prefix="/api/health", tags=["health"])

@app.get("/")
async def root():
    return {"message": "On-Chain Arbitrage API", "version": "1.0.0", "status": "running"}



if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)