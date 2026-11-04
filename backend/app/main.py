from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.session import engine, get_db
from app.database.base import Base, import_models
from app.routers import auth, public, protests, volunteers, reports, admin, notifications

# 1. Load all models and auto-create tables in Supabase
import_models()
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created successfully!")
except Exception as e:
    print(f"⚠️  Database setup warning: {e}")

# 2. FastAPI App
app = FastAPI(
    title="CivicPulse API",
    description="AI-Powered Civic Event Intelligence & Crowdsourced Monitoring Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Mount all routers
app.include_router(auth.router,          prefix="/api/v1", tags=["Module A — Auth"])
app.include_router(protests.router,      prefix="/api/v1", tags=["Module C — Public Discovery"])
app.include_router(public.router,        prefix="/api/v1", tags=["Module C — Public Stats & Feed"])
app.include_router(volunteers.router,    prefix="/api/v1", tags=["Module D — Volunteer"])
app.include_router(reports.router,       prefix="/api/v1", tags=["Module E — Admin Reports"])
app.include_router(admin.router,         prefix="/api/v1", tags=["Module B & E — Admin"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Module F — Notifications"])

# 5. Root
@app.get("/", tags=["Root"])
def root():
    return {
        "project": "CivicPulse",
        "status": "Online 🚀",
        "docs": "/docs",
        "api_base": "/api/v1"
    }

# 6. Health check
@app.get("/api/v1/health", tags=["Root"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "Connected to Supabase PostgreSQL ✅"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
