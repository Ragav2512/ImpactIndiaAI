import json
import time
import os
from google import genai
import requests
from bs4 import BeautifulSoup

class StartupEnhancer:
    """
    Enhances startup data by:
    1. Generating AI summaries for missing ones using Gemini
    2. Finding LinkedIn profile pages
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3-flash-preview"
        
        self.input_file = 'enriched_startups.json'
        self.about_pages_file = 'startup_about_pages.json'
        self.output_file = 'enriched_startups_final.json'
        
        self.results = []
        self.about_content_map = {}
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def load_data(self):
        """Load enriched data and about content."""
        print("📂 Loading data...")
        
        # Load enriched startups
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.results = data['results']
        
        # Load about pages for content reference
        try:
            with open(self.about_pages_file, 'r', encoding='utf-8') as f:
                about_data = json.load(f)
                for item in about_data['results']:
                    self.about_content_map[item['name']] = item.get('about_content', '')
            print(f"   ✅ Loaded {len(self.results)} startups")
            print(f"   ✅ Loaded {len(self.about_content_map)} about pages")
        except:
            print("   ⚠️  Could not load about pages")
        
        return True
    
    def search_linkedin(self, company_name, website=None):
        """Search for company LinkedIn page - check website first, then search."""
        try:
            # Strategy 1: Check company website for LinkedIn link
            if website:
                try:
                    response = requests.get(website, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for LinkedIn links in the page
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            if 'linkedin.com/company/' in href:
                                # Clean and return
                                linkedin_url = href.split('?')[0].split('#')[0]
                                if linkedin_url.startswith('http'):
                                    return linkedin_url
                                else:
                                    return f"https://www.linkedin.com{linkedin_url}" if linkedin_url.startswith('/') else f"https://{linkedin_url}"
                except:
                    pass  # Website check failed, try search
            
            # Strategy 2: Construct likely LinkedIn URL
            clean_name = company_name.lower()
            clean_name = clean_name.replace('pvt. ltd.', '').replace('private limited', '')
            clean_name = clean_name.replace('pvt ltd', '').replace('ltd', '').replace('llp', '')
            clean_name = clean_name.replace('(', '').replace(')', '').strip()
            
            # Convert to LinkedIn slug format
            slug = clean_name.replace(' ', '-').replace('.', '').replace(',', '')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
            
            # Try common patterns
            possible_urls = [
                f"https://www.linkedin.com/company/{slug}",
                f"https://www.linkedin.com/company/{slug}-india",
                f"https://www.linkedin.com/company/{slug.replace('-', '')}"
            ]
            
            # Verify which URL exists
            for url in possible_urls:
                try:
                    resp = requests.head(url, headers=self.headers, timeout=5, allow_redirects=True)
                    if resp.status_code == 200:
                        return url
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"      LinkedIn search error: {str(e)[:50]}")
            return None
    
    def generate_summary_with_ai(self, startup_name, about_content):
        """Use Gemini to generate summary from about content."""
        if not about_content or len(about_content) < 50:
            return None
        
        try:
            prompt = f"""Generate a concise 2-3 sentence summary for this startup.

Startup Name: {startup_name}

About Content:
{about_content[:1800]}

Instructions:
- Write 2-3 clear, informative sentences
- Focus on what the company does and their key value proposition
- Be specific and factual
- Avoid marketing language

Return ONLY the summary text, no JSON or additional formatting."""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            summary = response.text.strip()
            return summary
            
        except Exception as e:
            print(f"      AI summary error: {str(e)[:80]}")
            return None
    
    def needs_enhancement(self, startup):
        """Check if startup needs summary or LinkedIn."""
        needs_summary = (
            startup.get('category') in ['Error', 'No Data'] or
            startup.get('summary') in [
                'No information available',
                'Failed to process with AI',
                'No information available for this startup.',
                None
            ]
        )
        
        needs_linkedin = not startup.get('linkedin_url')
        
        return needs_summary or needs_linkedin
    
    def enhance_startup(self, startup, index, total):
        """Enhance a single startup with missing data."""
        name = startup['name']
        print(f"\n[{index}/{total}] Enhancing: {name}")
        
        enhanced = startup.copy()
        changes_made = []
        
        # Check if needs summary
        needs_summary = (
            startup.get('category') in ['Error', 'No Data'] or
            startup.get('summary') in [
                'No information available',
                'Failed to process with AI',
                'No information available for this startup.',
                None
            ]
        )
        
        if needs_summary:
            about_content = self.about_content_map.get(name, '')
            if about_content:
                print(f"   🤖 Generating AI summary...")
                summary = self.generate_summary_with_ai(name, about_content)
                if summary:
                    enhanced['summary'] = summary
                    enhanced['confidence'] = 'Medium'
                    changes_made.append('summary')
                    print(f"   ✅ Generated summary")
                time.sleep(1)  # Rate limiting
        
        # Find LinkedIn
        if not startup.get('linkedin_url'):
            print(f"   🔍 Searching for LinkedIn...")
            linkedin_url = self.search_linkedin(name, startup.get('website'))
            if linkedin_url:
                enhanced['linkedin_url'] = linkedin_url
                changes_made.append('LinkedIn')
                print(f"   ✅ Found LinkedIn: {linkedin_url}")
            else:
                enhanced['linkedin_url'] = None
                print(f"   ⚠️  LinkedIn not found")
            time.sleep(1)  # Rate limiting for search
        
        if changes_made:
            print(f"   📝 Enhanced: {', '.join(changes_made)}")
        else:
            print(f"   ⏭️  No enhancements needed")
        
        return enhanced
    
    def run(self, limit=None, start_index=0):
        """Run enhancement for all or subset of startups."""
        print("=" * 70)
        print("🚀 Startup Data Enhancement Pipeline")
        print("=" * 70)
        
        if not self.load_data():
            print("❌ Failed to load data")
            return
        
        # Filter startups that need enhancement
        startups_to_process = [
            (i, s) for i, s in enumerate(self.results)
            if self.needs_enhancement(s)
        ]
        
        total = len(startups_to_process)
        print(f"\n📊 Found {total} startups needing enhancement")
        
        if limit:
            startups_to_process = startups_to_process[start_index:start_index + limit]
            print(f"🎯 Processing {len(startups_to_process)} startups (from index {start_index})")
        
        # Process each startup
        for orig_idx, startup in startups_to_process:
            enhanced = self.enhance_startup(startup, orig_idx + 1, len(self.results))
            self.results[orig_idx] = enhanced
            
            # Save progress after each
            self.save_results()
        
        print("\n" + "=" * 70)
        print("✅ Enhancement complete!")
        self.print_summary()
        print("=" * 70)
    
    def save_results(self):
        """Save enhanced results."""
        output_data = {
            "total_enriched": len(self.results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": self.model,
            "results": self.results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print summary statistics."""
        total = len(self.results)
        
        with_linkedin = sum(1 for s in self.results if s.get('linkedin_url'))
        with_summary = sum(1 for s in self.results 
                          if s.get('summary') and s['summary'] not in [
                              'No information available',
                              'Failed to process with AI',
                              'No information available for this startup.'
                          ])
        
        print(f"\n📊 Enhancement Summary:")
        print(f"   Total startups: {total}")
        print(f"   With LinkedIn: {with_linkedin} ({with_linkedin/total*100:.1f}%)")
        print(f"   With summaries: {with_summary} ({with_summary/total*100:.1f}%)")
        print(f"\n💾 Results saved to: {self.output_file}")


if __name__ == "__main__":
    import sys
    
    # API key
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCwTx6-aQnXJ9DFLOm6n2KmKHT7wH6d6NM')
    
    # Parse arguments
    limit = 10  # Default: test with 10
    start_index = 0
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            limit = None
        else:
            try:
                limit = int(sys.argv[1])
            except ValueError:
                print("Usage: python3 enhance_missing_data.py [all|number] [start_index]")
                print("Examples:")
                print("  python3 enhance_missing_data.py          # Process 10 startups (test)")
                print("  python3 enhance_missing_data.py 50       # Process 50 startups")
                print("  python3 enhance_missing_data.py all      # Process all missing data")
                print("  python3 enhance_missing_data.py all 100  # Process all, starting from #100")
                sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print("Error: start_index must be a number")
            sys.exit(1)
    
    enhancer = StartupEnhancer(api_key=api_key)
    enhancer.run(limit=limit, start_index=start_index)
