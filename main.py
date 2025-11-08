from fastapi import FastAPI
from backend.routers import normal, celebrity, morph

app = FastAPI(title="AI Lookalike & Morphing Platform")

# Add root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI Lookalike & Morphing Platform. Visit /docs for API endpoints."}

app.include_router(normal.router, prefix="/normal", tags=["Normal Lookalike"])
app.include_router(celebrity.router, prefix="/celebrity", tags=["Celebrity Lookalike"])
app.include_router(morph.router, prefix="/morph", tags=["Morphing Video"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)