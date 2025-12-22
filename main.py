
from fastapi import FastAPI
from app.routers import tableau,artifacts,source

app = FastAPI(
    title="Power BI Migration API",
    version="1.0.0"
)

# Register routers

app.include_router(tableau.router, prefix="/tableau", tags=["Tableau"])
app.include_router(source.router, prefix="/source", tags=["Source"])
app.include_router(artifacts.router, prefix="/artifacts", tags=["Artifacts"])
app.include_router(te3.router,   prefix="/te3",      tags=["TE3"])
app.include_router(layout.router,   prefix="/layout",   tags=["Layout"])

@app.get("/health")
def health():
    return {"status": "ok"}
