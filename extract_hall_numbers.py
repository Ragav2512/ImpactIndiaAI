import requests
import re
import json

def extract_exhibitor_details():
    """
    Extracts detailed exhibitor information including hall numbers from the India AI Impact Expo website.
    """
    url = "https://www.impactexpo.indiaai.gov.in/list-of-exhibitors"
    print(f"🔍 Fetching exhibitor details from {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return {}

    # Extract the exhibitors array from JavaScript
    match = re.search(r'const exhibitors\s*=\s*(\[[\s\S]*?\])\s*;', response.text)
    if not match:
        print("❌ Could not find exhibitor data in the page source.")
        return {}
    
    array_content = match.group(1)
    exhibitor_map = {}
    
    # Parse each exhibitor object
    for obj_match in re.finditer(r'\{([\s\S]*?)\}\s*(?=,|\])', array_content):
        obj_text = obj_match.group(1)
        
        # Only process startups
        if not re.search(r'categories\s*:\s*[\'"]Startup[\'"]', obj_text):
            continue
        
        # Extract fields
        name_match = re.search(r'name\s*:\s*[\'"](.*?)[\'"]', obj_text)
        hall_match = re.search(r'hall\s*:\s*[\'"](.*?)[\'"]', obj_text)
        sqm_match = re.search(r'sqm\s*:\s*[\'"](.*?)[\'"]', obj_text)
        logo_match = re.search(r'logo\s*:\s*[\'"](.*?)[\'"]', obj_text)
        
        if name_match:
            name = name_match.group(1).strip()
            exhibitor_map[name] = {
                "hall": hall_match.group(1) if hall_match else "Unknown",
                "space_sqm": sqm_match.group(1) if sqm_match else "Unknown",
                "logo_url": logo_match.group(1) if logo_match else None
            }
    
    return exhibitor_map

if __name__ == "__main__":
    exhibitor_details = extract_exhibitor_details()
    
    print(f"\n✅ Extracted details for {len(exhibitor_details)} startups")
    print("\nSample data:")
    for i, (name, details) in enumerate(list(exhibitor_details.items())[:5]):
        print(f"\n{i+1}. {name}")
        print(f"   Hall: {details['hall']}")
        print(f"   Space: {details['space_sqm']} sqm")
    
    # Save to file
    with open('exhibitor_hall_details.json', 'w', encoding='utf-8') as f:
        json.dump(exhibitor_details, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to exhibitor_hall_details.json")
