import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

APP_TITLE = "SuggestMe.AI"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("SUGGESTION_MODEL", "gemini-2.5-flash")
YOUTUBE_API_KEY = os.getenv("yt_api")
YOUTUBE_RESULTS_LIMIT = 6
REQUEST_TIMEOUT_SECONDS = 10
MAX_INTEREST_LENGTH = 60

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def clean_interest(raw_value: str) -> str:
    return " ".join(raw_value.split()).strip()[:MAX_INTEREST_LENGTH]


def build_prompt(topic: str) -> str:
    return (
        f"The user wants useful suggestions for: {topic}. "
        "Respond like a sharp AI recommendation assistant. "
        "Give a concise answer with these sections: Best starting point, Tools or resources, "
        "What to search next, and a short action plan. "
        "Keep it practical, specific, and easy to scan."
    )


def fetch_response(topic: str) -> str:
    return fetch_response_with_gemini(topic)


def fetch_response_with_gemini(topic: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required.")

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_MODEL}:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        json={
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a careful study assistant. Recommend concise, "
                            "high-quality English learning resources and avoid filler."
                        )
                    }
                ]
            },
            "contents": [{"parts": [{"text": build_prompt(topic)}]}],
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    candidates = payload.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    return text


def search_youtube(query: str) -> list[dict[str, str]]:
    if not YOUTUBE_API_KEY:
        app.logger.warning("Skipping YouTube search because yt_api is not configured.")
        return []

    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "type": "video",
                "maxResults": YOUTUBE_RESULTS_LIMIT,
                "q": f"{query} tutorial",
                "key": YOUTUBE_API_KEY,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        app.logger.exception("YouTube search failed for query '%s'.", query)
        return []

    videos: list[dict[str, str]] = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue

        videos.append(
            {
                "id": video_id,
                "title": snippet.get("title", "Untitled video"),
                "channel": snippet.get("channelTitle", "Unknown channel"),
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )

    return videos


def build_topic_result(topic: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "query": topic,
        "response": "",
        "videos": [],
        "errors": [],
    }

    try:
        result["response"] = fetch_response(topic)
    except Exception:
        app.logger.exception("AI suggestion request failed for '%s'.", topic)
        result["errors"].append(
            f"AI suggestions are temporarily unavailable for {topic}."
        )

    result["videos"] = search_youtube(topic)
    if not result["videos"]:
        result["errors"].append(f"No YouTube videos were found for {topic}.")

    return result


def render_generator(**context: Any) -> str:
    base_context = {
        "app_title": APP_TITLE,
        "selected_model": DEFAULT_MODEL,
        "user_input": "",
        "result": None,
        "form_error": "",
        "youtube_configured": bool(YOUTUBE_API_KEY),
    }
    base_context.update(context)
    return render_template("generate.html", **base_context)


@app.route("/")
def index() -> str:
    return render_template(
        "index.html",
        app_title=APP_TITLE,
        selected_model=DEFAULT_MODEL,
    )


@app.route("/generate", methods=["GET"])
def generate() -> str:
    return render_generator()


@app.route("/get_suggestions", methods=["POST"])
def get_suggestions() -> str:
    user_input = clean_interest(request.form.get("user_input", ""))

    if not user_input:
        return render_generator(
            user_input=user_input,
            form_error="Enter one interest or question to get suggestions.",
        )

    result = build_topic_result(user_input)
    return render_generator(
        user_input=user_input,
        result=result,
    )


if __name__ == "__main__":
    app.run(debug=True)
