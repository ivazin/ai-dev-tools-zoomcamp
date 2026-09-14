from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import events, expenses, settlements, rates, health, websockets

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend REST API for Tavli Collaborative Expense Splitter",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )


# Register modular routers
app.include_router(events.router)
app.include_router(expenses.router)
app.include_router(settlements.router)
app.include_router(rates.router)
app.include_router(health.router)
app.include_router(websockets.router)
