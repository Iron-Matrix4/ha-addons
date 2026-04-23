# Getting Google Custom Search API Keys

To use web search in Jarvis, you need two things from Google:

## 1. Get API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **API Key**
5. Copy the API key
6. (Optional) Click **Restrict Key** → Under **API restrictions**, select "Custom Search API"

## 2. Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create)
2. **What to search**: Select "Search the entire web"
3. **Name of search engine**: "Jarvis Search" (or anything)
4. Click **Create**
5. On the next page, copy the **Search engine ID** (looks like: `a1b2c3d4e5f6g7h8i`)

## 3. Enable Custom Search API

1. Go to [Custom Search API Page](https://console.cloud.google.com/apis/library/customsearch.googleapis.com)
2. Click **Enable**

## 4. Add to Jarvis Configuration

In Home Assistant:
**Settings** → **Add-ons** → **Jarvis AI** → **Configuration**

```yaml
google_search_api_key: "YOUR_API_KEY_HERE"
google_search_engine_id: "YOUR_SEARCH_ENGINE_ID_HERE"
```

## Free Tier Limits

- **100 queries per day** (free)
- Above that: $5 per 1000 queries

For a personal voice assistant, 100/day is usually plenty!

## Test

After configuration, try:

```
"Jarvis, what's the population of Japan?"
```

Jarvis should search Google and respond with the answer.
