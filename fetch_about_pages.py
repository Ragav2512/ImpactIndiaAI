import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class StartupAboutFetcher:
    def __init__(self, startups_file='all_startups.json', output_file='startup_about_pages.json'):
        self.startups_file = startups_file
        self.output_file = output_file
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.results = []
        
    def load_startups(self):
        """Load the list of startups from JSON file."""
        with open(self.startups_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['startups']
    
    def search_company_website(self, company_name):
        """
        Search for company website using DuckDuckGo HTML search.
        Returns the most likely website URL.
        """
        try:
            # Clean up company name for search
            search_query = f"{company_name} official website"
            
            # Use DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the first search result link
                result_links = soup.select('.result__a')
                if result_links:
                    url = result_links[0].get('href')
                    # DuckDuckGo wraps URLs, extract the actual URL
                    if url and 'uddg=' in url:
                        actual_url = url.split('uddg=')[1].split('&')[0]
                        from urllib.parse import unquote
                        return unquote(actual_url)
                    return url
            
            return None
        except Exception as e:
            print(f"   ⚠️  Search error for {company_name}: {str(e)}")
            return None
    
    def find_about_page_url(self, base_url):
        """
        Find the About page URL by checking common patterns.
        """
        if not base_url:
            return None
            
        try:
            # Common about page patterns
            about_patterns = [
                '/about',
                '/about-us',
                '/aboutus',
                '/about/',
                '/about-us/',
                '/company',
                '/company/about',
                '/who-we-are',
            ]
            
            # First, get the homepage to find about links
            response = requests.get(base_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for "About" links in navigation
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().lower().strip()
                href = link['href']
                
                if any(keyword in link_text for keyword in ['about', 'who we are', 'company']):
                    full_url = urljoin(base_url, href)
                    # Verify it's a valid about page pattern
                    if any(pattern in full_url.lower() for pattern in about_patterns):
                        return full_url
            
            # Fallback: Try common about URL patterns
            parsed_url = urlparse(base_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            for pattern in about_patterns:
                potential_url = base_domain + pattern
                try:
                    check_response = requests.head(potential_url, headers=self.headers, timeout=5, allow_redirects=True)
                    if check_response.status_code == 200:
                        return potential_url
                except:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"   ⚠️  Error finding about page: {str(e)}")
            return None
    
    def fetch_page_content(self, url):
        """
        Fetch and extract text content from a webpage.
        """
        if not url:
            return None
            
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Limit to reasonable length (first 2000 chars)
            if len(text) > 2000:
                text = text[:2000] + "..."
                
            return text
            
        except Exception as e:
            print(f"   ⚠️  Error fetching content: {str(e)}")
            return None
    
    def process_startup(self, company_name, index, total):
        """
        Process a single startup: find website, locate about page, extract content.
        """
        print(f"\n[{index}/{total}] Processing: {company_name}")
        
        result = {
            "name": company_name,
            "website": None,
            "about_page_url": None,
            "about_content": None,
            "status": "pending"
        }
        
        # Step 1: Search for company website
        print(f"   🔍 Searching for website...")
        website = self.search_company_website(company_name)
        
        if not website:
            result['status'] = 'website_not_found'
            print(f"   ❌ Website not found")
            return result
            
        result['website'] = website
        print(f"   ✅ Found website: {website}")
        
        # Add delay to be respectful
        time.sleep(1)
        
        # Step 2: Find About page
        print(f"   🔍 Looking for About page...")
        about_url = self.find_about_page_url(website)
        
        if not about_url:
            # If no specific about page, use homepage
            about_url = website
            print(f"   ⚠️  No specific About page found, using homepage")
        else:
            print(f"   ✅ Found About page: {about_url}")
            
        result['about_page_url'] = about_url
        
        # Add delay
        time.sleep(1)
        
        # Step 3: Fetch content
        print(f"   📄 Fetching content...")
        content = self.fetch_page_content(about_url)
        
        if content:
            result['about_content'] = content
            result['status'] = 'success'
            print(f"   ✅ Content extracted ({len(content)} chars)")
        else:
            result['status'] = 'content_fetch_failed'
            print(f"   ❌ Failed to fetch content")
            
        return result
    
    def run(self, limit=None, start_index=0):
        """
        Run the fetcher for all startups.
        
        Args:
            limit: Maximum number of startups to process (None for all)
            start_index: Starting index (useful for resuming)
        """
        print("=" * 60)
        print("🚀 Startup About Page Fetcher")
        print("=" * 60)
        
        # Load startups
        startups = self.load_startups()
        total = len(startups)
        
        print(f"\n📊 Loaded {total} startups from {self.startups_file}")
        
        if limit:
            startups = startups[start_index:start_index + limit]
            print(f"🎯 Processing {len(startups)} startups (from index {start_index})")
        
        # Load existing results if any
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                self.results = existing_data.get('results', [])
                print(f"📂 Loaded {len(self.results)} existing results")
        except FileNotFoundError:
            print("📂 Starting fresh (no existing results)")
            self.results = []
        
        # Process each startup
        for idx, startup in enumerate(startups, start=start_index + 1):
            # Check if already processed
            if any(r['name'] == startup for r in self.results):
                print(f"\n[{idx}/{total}] ⏭️  Skipping {startup} (already processed)")
                continue
                
            result = self.process_startup(startup, idx, total)
            self.results.append(result)
            
            # Save progress after each startup
            self.save_results()
            
            # Be respectful with delays
            time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✅ Processing complete!")
        self.print_summary()
        print("=" * 60)
    
    def save_results(self):
        """Save results to JSON file."""
        output_data = {
            "total_processed": len(self.results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print a summary of results."""
        total = len(self.results)
        success = sum(1 for r in self.results if r['status'] == 'success')
        no_website = sum(1 for r in self.results if r['status'] == 'website_not_found')
        failed = sum(1 for r in self.results if r['status'] == 'content_fetch_failed')
        
        print(f"\n📊 Summary:")
        print(f"   Total processed: {total}")
        print(f"   ✅ Successful: {success}")
        print(f"   ❌ Website not found: {no_website}")
        print(f"   ⚠️  Content fetch failed: {failed}")
        print(f"\n💾 Results saved to: {self.output_file}")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    limit = 5  # Default: process 5 as test
    start_index = 0
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            limit = None
        else:
            try:
                limit = int(sys.argv[1])
            except ValueError:
                print("Usage: python3 fetch_about_pages.py [all|number] [start_index]")
                print("Examples:")
                print("  python3 fetch_about_pages.py          # Process 5 startups (test)")
                print("  python3 fetch_about_pages.py 20       # Process 20 startups")
                print("  python3 fetch_about_pages.py all      # Process all startups")
                print("  python3 fetch_about_pages.py all 50   # Process all, starting from index 50")
                sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print("Error: start_index must be a number")
            sys.exit(1)
    
    fetcher = StartupAboutFetcher()
    fetcher.run(limit=limit, start_index=start_index)
