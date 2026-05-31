from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks

app = FastAPI()

# Allow the local Next.js frontend to call the API (different origin/port).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(tasks.router)
