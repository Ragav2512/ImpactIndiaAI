import requests
import re
import json

def fetch_startups():
    """
    Scrapes the list of startups from the India AI Impact Expo website.
    The data is embedded as a JavaScript array in the page source.
    """
    url = "https://www.impactexpo.indiaai.gov.in/list-of-exhibitors"
    print(f"🔍 Fetching exhibitors from {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return []

    # The exhibitors are stored in a JS constant: const exhibitors = [...];
    # We use regex to extract this array block
    match = re.search(r'const exhibitors\s*=\s*(\[[\s\S]*?\])\s*;', response.text)
    if not match:
        print("❌ Could not find exhibitor data in the page source.")
        return []
    
    array_content = match.group(1)
    startups = []
    
    # Each exhibitor is an object: { name: '...', categories: 'Startup', ... }
    # We use regex to find each object and check its category
    # This regex matches content between curly braces { ... }
    for obj_match in re.finditer(r'\{([\s\S]*?)\}\s*(?=,|\])', array_content):
        obj_text = obj_match.group(1)
        
        # Check if 'categories' field contains 'Startup'
        # Matches categories: 'Startup' or categories: "Startup"
        if re.search(r'categories\s*:\s*[\'"]Startup[\'"]', obj_text):
            # Extract the 'name' field
            name_match = re.search(r'name\s*:\s*[\'"](.*?)[\'"]', obj_text)
            if name_match:
                # Clean up the name (unescape, trim)
                name = name_match.group(1).strip()
                # Simple unescape for common JS escapes if any
                name = name.replace("\\'", "'").replace('\\"', '"')
                startups.append(name)
                
    return startups

if __name__ == "__main__":
    startups = fetch_startups()
    
    if startups:
        # Save to file
        output_file = 'all_startups.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "source": "https://www.impactexpo.indiaai.gov.in/list-of-exhibitors",
                "total": len(startups), 
                "startups": startups
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Extracted {len(startups)} startups")
        print(f"📂 Data saved to {output_file}")
        
        # Show a few examples
        print("\nExamples:")
        for s in startups[:5]:
            print(f" - {s}")
    else:
        print("⚠️ No startups were found.")
