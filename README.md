# SuggestMe.AI

Small Flask app that takes one prompt at a time and generates AI-powered suggestions for it. When `yt_api` is configured, it also embeds matching YouTube videos.

## What changed

- Better request validation and cleaner prompt construction
- Gemini API support with `requests`
- Graceful fallback when AI or YouTube requests fail
- Improved layout, input persistence, and visible error messages
- Basic setup files for local development

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file from `.env.example`.
4. Start the app:

```bash
python main.py
```

5. Open `http://127.0.0.1:5000`.

## Environment variables

- `GEMINI_API_KEY`: Gemini API key
- `yt_api`: YouTube Data API key for video search
- `SUGGESTION_MODEL`: Gemini model name
- `LOG_LEVEL`: optional Flask/app logging level

## Recommendation

Gemini is a good fit here because the REST API is official, easy to call without extra SDKs, and the free tier works well for lightweight suggestion prompts.
