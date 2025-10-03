from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, date
from google import genai
from google.genai import types
import os
import json 
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env file") 
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
client = genai.Client()
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

app = FastAPI(title="Ocean News Agentic API")

# Allow CORS on the sub-app (adjust allow_origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_gemini_news(region: Optional[str] = None, max_articles: int = 20):
    """
    Uses Gemini API with Google Search to fetch recent, verified ocean/environment news.
    Returns a list of articles.
    """
    region_text = f"in the region of {region}" if region else "globally"
    current_date = date.today().isoformat()

    prompt = f"""
    You are a news-finding AI. Your task is to use your Google Search tool to find recent, factual, English-language news articles about ocean and marine environmental events.

    Current Date: {current_date}
    Search Region: {region_text}
    Topics: Ocean pollution, oil spills, marine debris, plastic waste, coral bleaching, climate change impacts on oceans, and related environmental disasters.

    Instructions:
    1.  **You MUST use your Google Search tool** to find real articles published within the **last 30 days**. Do not use your internal knowledge.
    2.  Verify that all URLs are active and lead to the correct news article.
    3.  Return a JSON array of objects, where each object represents an article.
    4.  Each object must have these exact keys: "title", "url", "publishedAt" (in "YYYY-MM-DD" format).
    5.  Do not include any text, explanations, or markdown formatting outside of the JSON array.
    6.  Find up to {max_articles} articles. If no relevant articles are found, return an empty JSON array `[]`.

    Example JSON output:
    [
      {{
        "title": "Massive oil spill reported off coast of India",
        "url": "https://example.com/article1",
        "publishedAt": "2025-09-28"
      }}
    ]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )

        raw_text = response.text.strip()
        # Remove markdown code blocks if present
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()

        articles_data = json.loads(raw_text)
        return articles_data

    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}. Raw response: {raw_text}")
        return []
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return []


@app.get("/ocean-news")
def ocean_news(
    region: Optional[str] = Query(None, description="Region name, e.g., 'Indian Ocean' or 'Bangladesh'"),
    limit: int = Query(5, description="Number of articles to return")
):
    print(f"Received request: region={region}, limit={limit}")
    all_articles = fetch_gemini_news(region=region, max_articles=max(20, limit)) 
    print(f"Returning {len(all_articles[:limit])} articles")
    return {
        "region": region,
        "date": date.today().isoformat(),
        "news": all_articles[:limit]
    }

