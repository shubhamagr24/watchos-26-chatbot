import asyncio
import json
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# --- Configuration ---


SOURCES = [

    {

        "url": "https://developer.apple.com/documentation/watchos-release-notes/watchos-26-release-notes",

        "version": "26.0",

        "type": "release_notes"

    },

    {

        "url": "https://developer.apple.com/documentation/watchos-release-notes/watchos-26_1-release-notes",

        "version": "26.1",

        "type": "release_notes"

    },

    {

        "url": "https://developer.apple.com/documentation/watchos-release-notes/watchos-26_2-release-notes",

        "version": "26.2",

        "type": "release_notes"

    },

    {

        "url": "https://developer.apple.com/documentation/watchos-release-notes/watchos-26_3-release-notes",

        "version": "26.3",

        "type": "release_notes"

    }

]



OUTPUT_FILE = "apple_watch_kb/kb_raw_data.json"

async def create_knowledge_base():
    print(f"--- Step 1: Crawling {len(SOURCES)} sources ---")
    
    # 1. Browser Config (Your Config)
    browser_conf = BrowserConfig(
        headless=True,
        # Fake a user agent to avoid bot detection
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # 2. Run Config (Your Config)
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        # CRITICAL: Wait for the main article content to load using CSS selector
        wait_for="main", 
        # Focus extraction ONLY on the main article, ignoring sidebar/footer
        css_selector="main",
        # Remove navigation elements and button text from the output
        excluded_tags=["nav", "footer", "header", "button"],
        # Add a slight delay to allow hydration (text rendering) to finish
        page_timeout=30000, 
        delay_before_return_html=3.0 
    )

    results = []

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        for source in SOURCES:
            print(f"Fetching data from: {source['url']} ...")
            
            # We reuse the same config for each URL in the loop
            result = await crawler.arun(
                url=source["url"],
                config=run_conf
            )

            if result.success:
                print(f"--- Success! Retrieved {len(result.markdown)} chars ---")
                
                # Store raw content + metadata for the RAG pipeline
                entry = {
                    "url": source["url"], 
                    "category": source["type"]+ source["version"],
                    "text": result.markdown,
                    "title": result.metadata.get("title", "Unknown")
                }
                results.append(entry)
            else:
                print(f"Error: {result.error_message}")



    # Save to disk
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved raw knowledge base to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    asyncio.run(create_knowledge_base())