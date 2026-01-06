from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import tableau, artifacts,  layout, te3

# ------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------
app = FastAPI(
    title="Power BI Migration API",
    version="1.0.0"
)

# ------------------------------------------------------------
# CORS MIDDLEWARE  (CRITICAL FIX)
# ------------------------------------------------------------
# This MUST be added before include_router()
# This enables OPTIONS preflight for browsers
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 🔴 tighten in production
    allow_credentials=True,
    allow_methods=["*"],           # allows POST + OPTIONS
    allow_headers=["*"],           # allows Content-Type, Authorization, etc.
)

# ------------------------------------------------------------
# Register routers
# ------------------------------------------------------------
app.include_router(tableau.router,   prefix="/tableau",   tags=["Tableau"])

app.include_router(artifacts.router, prefix="/artifacts", tags=["Artifacts"])
app.include_router(te3.router,       prefix="/te3",       tags=["TE3"])
app.include_router(layout.router,    prefix="/layout",    tags=["Layout"])

# ------------------------------------------------------------
# Health check
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
