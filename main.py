from fastapi import FastAPI
from apis.sea_roughness import app as roughness_app
from apis.ocean_news import app as news_app

app = FastAPI(title="Dheu Unified API")
app.mount("/roughness", roughness_app)
app.mount("/news", news_app)

@app.get("/")
def root():
    return {"message": "Dheu API running"}
