from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.sea_roughness import app as roughness_app
from apis.ocean_news import app as news_app

app = FastAPI(title="Dheu Unified API")
# Allow CORS (adjust allow_origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/roughness", roughness_app)
app.mount("/news", news_app)

@app.get("/")
def root():
    return {"message": "Dheu API running"}
