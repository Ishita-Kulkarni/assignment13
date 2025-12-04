from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import time
from app.operations import calculate, DivisionByZeroError, InvalidOperationError
from app.logger_config import setup_logging, get_logger
from app.database import init_db
from app.users import router as users_router
from app.calculations import router as calculations_router

# Initialize logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown events"""
    # Startup
    logger.info("FastAPI Application starting...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info("FastAPI Application started successfully")
    logger.info("API Documentation available at: /docs")
    logger.info("API Health check available at: /health")
    logger.info("User endpoints available at: /users")
    logger.info("Calculation endpoints available at: /calculations")
    
    yield
    
    # Shutdown
    logger.info("FastAPI Application shutting down...")


app = FastAPI(
    title="FastAPI Application with User Management",
    description="A FastAPI application with calculator and user management features",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(users_router)
app.include_router(calculations_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {process_time:.3f}s"
        )
        
        # Add custom header with process time
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - "
            f"Error: {str(e)} - Duration: {process_time:.3f}s",
            exc_info=True
        )
        raise

class CalculationRequest(BaseModel):
    num1: float
    num2: float
    operation: str

class CalculationResponse(BaseModel):
    result: float
    operation: str
    num1: float
    num2: float

@app.get("/")
async def root():
    """Serve the calculator web interface"""
    logger.info("Root endpoint accessed - serving calculator interface")
    return FileResponse("static/index.html")

@app.get("/api")
async def api_info():
    """API information endpoint"""
    logger.info("API info endpoint accessed")
    return {
        "message": "Welcome to FastAPI Application!",
        "version": "2.0.0",
        "endpoints": {
            "/": "Calculator web interface",
            "/docs": "API documentation",
            "/calculate": "Perform calculations",
            "/users": "User management endpoints",
            "/users/register": "Register new user",
            "/users/login": "User login",
            "/health": "Health check"
        }
    }

@app.post("/calculate", response_model=CalculationResponse)
async def calculate_endpoint(request: CalculationRequest):
    """
    Perform basic arithmetic calculations
    
    Operations supported:
    - add: Addition
    - subtract: Subtraction
    - multiply: Multiplication
    - divide: Division
    """
    logger.info(
        f"Calculate endpoint called with: num1={request.num1}, "
        f"num2={request.num2}, operation={request.operation}"
    )
    
    try:
        result = calculate(request.num1, request.num2, request.operation)
        logger.info(f"Calculation successful, returning result: {result}")
        return CalculationResponse(
            result=result,
            operation=request.operation.lower(),
            num1=request.num1,
            num2=request.num2
        )
    except DivisionByZeroError as e:
        logger.warning(f"Division by zero error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidOperationError as e:
        logger.warning(f"Invalid operation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in calculate endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
