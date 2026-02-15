# Startup About Page Fetcher

This project retrieves the "About" pages for all startups listed on the India AI Impact Expo website.

## Files

- `ExibhitorRetreival.py` - Scrapes the list of startups from the expo website
- `fetch_about_pages.py` - Fetches company websites and about pages
- `all_startups.json` - List of all 396 startups
- `startup_about_pages.json` - Output with company websites and about page content

## How It Works

### Step 1: Get Startup List
First, we scrape the exhibitor list from the India AI Impact Expo website:
```bash
python3 ExibhitorRetreival.py
```

This creates `all_startups.json` with 396 startup names.

### Step 2: Fetch About Pages
The script performs three tasks for each startup:

1. **Search for Website** - Uses DuckDuckGo to find the company's official website
2. **Find About Page** - Looks for common "About" page patterns (/about, /about-us, etc.)
3. **Extract Content** - Scrapes and saves the about page text content

## Usage

### Test Run (5 startups)
```bash
python3 fetch_about_pages.py
```

### Process All Startups
Edit `fetch_about_pages.py` and change the last line:
```python
# Change this:
fetcher.run(limit=5)

# To this:
fetcher.run(limit=None)  # Process all 396 startups
```

### Resume from Specific Index
If the process is interrupted, you can resume:
```python
fetcher.run(limit=None, start_index=50)  # Resume from startup #50
```

## Output Format

The script saves results to `startup_about_pages.json`:

```json
{
  "total_processed": 396,
  "timestamp": "2026-02-14 21:51:14",
  "results": [
    {
      "name": "Benchmark ESG Pvt Limited India",
      "website": "https://benchmarkgensuite.com/",
      "about_page_url": "https://benchmarkgensuite.com/about-us",
      "about_content": "Our EHS Story | Benchmark Gensuite...",
      "status": "success"
    }
  ]
}
```

### Status Values

- `success` - Successfully retrieved about page content
- `website_not_found` - Could not find company website via search
- `content_fetch_failed` - Found website but couldn't fetch content

## Features

✅ **Progress Saving** - Results are saved after each startup, so you can stop and resume anytime  
✅ **Rate Limiting** - Built-in delays to be respectful to websites  
✅ **Error Handling** - Gracefully handles failures and continues  
✅ **Skip Duplicates** - Automatically skips already processed startups  
✅ **Detailed Logging** - Real-time progress updates

## Timing

- **Test (5 startups)**: ~1-2 minutes
- **All 396 startups**: ~20-30 minutes (with rate limiting)

## Requirements

- Python 3.7+
- beautifulsoup4 (already installed)
- requests (already installed)

## Notes

- The script uses DuckDuckGo for web searches (no API key needed)
- Some websites may block automated access
- Content is limited to first 2000 characters to keep file size manageable
- If a specific "About" page isn't found, the homepage is used instead
