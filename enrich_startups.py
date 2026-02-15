import json
import time
import os
from google import genai

class StartupEnricher:
    """
    Enriches startup data by:
    1. Adding hall/booth numbers
    2. Generating AI-powered summaries using Gemini
    3. Categorizing by industry
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3-flash-preview"
        
        # Input files
        self.about_pages_file = 'startup_about_pages.json'
        self.hall_details_file = 'exhibitor_hall_details.json'
        
        # Output file
        self.output_file = 'enriched_startups.json'
        
        # Load data
        self.startup_data = {}
        self.hall_data = {}
        self.results = []
        
        # Category schema
        self.categories = [
            "AI/ML Infrastructure & Tools",
            "Healthcare & Biotech",
            "Fintech & Banking",
            "Education & EdTech",
            "Agriculture & AgriTech",
            "Cybersecurity",
            "E-commerce & Retail",
            "Manufacturing & Industry 4.0",
            "Media & Entertainment",
            "Climate & Sustainability",
            "Logistics & Supply Chain",
            "Legal & Compliance",
            "HR & Workforce Management",
            "Marketing & Sales Tech",
            "Robotics & Automation",
            "IoT & Smart Devices",
            "Data Analytics & Business Intelligence",
            "Government & Public Sector",
            "Real Estate & PropTech",
            "Other"
        ]
    
    def load_data(self):
        """Load all required data files."""
        print("📂 Loading data files...")
        
        # Load about pages
        try:
            with open(self.about_pages_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.startup_data = {item['name']: item for item in data['results']}
            print(f"   ✅ Loaded {len(self.startup_data)} startups from {self.about_pages_file}")
        except Exception as e:
            print(f"   ❌ Error loading {self.about_pages_file}: {e}")
            return False
        
        # Load hall details
        try:
            with open(self.hall_details_file, 'r', encoding='utf-8') as f:
                self.hall_data = json.load(f)
            print(f"   ✅ Loaded hall details for {len(self.hall_data)} startups")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not load hall details: {e}")
            self.hall_data = {}
        
        return True
    
    def create_enrichment_prompt(self, startup_name, about_content):
        """
        Create a comprehensive prompt for Gemini to categorize AND summarize.
        """
        categories_str = "\n".join([f"- {cat}" for cat in self.categories])
        
        prompt = f"""Analyze the following startup and provide a comprehensive analysis.

Startup Name: {startup_name}

About Content:
{about_content[:1800] if about_content else "No content available"}

Tasks:
1. **Categorize**: Choose the SINGLE most appropriate category from the list below
2. **Summarize**: Create a concise 2-3 sentence summary of what this company does
3. **Key Offerings**: List 2-4 key products/services
4. **Confidence**: Rate your confidence in this categorization (Low/Medium/High)

Available Categories:
{categories_str}

Response must be in this EXACT JSON format:
{{
    "category": "Category Name",
    "summary": "2-3 sentence summary here",
    "key_offerings": ["Product 1", "Product 2", "Product 3"],
    "confidence": "High|Medium|Low",
    "tags": ["tag1", "tag2", "tag3"]
}}

IMPORTANT: 
- Return ONLY valid JSON, no markdown formatting, no additional text
- Make the summary actionable and clear
- Tags should be relevant technology/domain keywords (3-5 tags)"""
        
        return prompt
    
    def enrich_with_ai(self, startup_name, about_content):
        """Use Gemini API to categorize and summarize the startup."""
        if not about_content:
            return {
                "category": "No Data",
                "summary": "No information available for this startup.",
                "key_offerings": [],
                "confidence": "Low",
                "tags": []
            }
        
        try:
            prompt = self.create_enrichment_prompt(startup_name, about_content)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            response_text = response.text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                json_lines = [line for line in lines if not line.startswith('```') and 'json' not in line.lower()]
                response_text = '\n'.join(json_lines).strip()
            
            enrichment = json.loads(response_text)
            return enrichment
            
        except Exception as e:
            print(f"      ⚠️  AI enrichment error: {str(e)[:100]}")
            return {
                "category": "Error",
                "summary": "Failed to process with AI",
                "key_offerings": [],
                "confidence": "Low",
                "tags": []
            }
    
    def enrich_startup(self, name, index, total):
        """Process a single startup: merge all data sources."""
        print(f"\n[{index}/{total}] Enriching: {name}")
        
        # Get startup data
        startup_info = self.startup_data.get(name, {})
        about_content = startup_info.get('about_content', '')
        
        # Get hall data
        hall_info = self.hall_data.get(name, {})
        
        # Skip if no content
        if startup_info.get('status') != 'success':
            print(f"   ⏭️  Skipping (no content available)")
            return {
                "name": name,
                "hall": hall_info.get('hall', 'Unknown'),
                "space_sqm": hall_info.get('space_sqm', 'Unknown'),
                "website": startup_info.get('website'),
                "category": "No Data",
                "summary": "No information available",
                "key_offerings": [],
                "confidence": "Low",
                "tags": []
            }
        
        # AI enrichment
        print(f"   🤖 Processing with Gemini API...")
        ai_data = self.enrich_with_ai(name, about_content)
        
        print(f"   ✅ Category: {ai_data['category']} | Confidence: {ai_data['confidence']}")
        print(f"   📝 Summary: {ai_data['summary'][:80]}...")
        
        # Merge all data
        enriched = {
            "name": name,
            "hall": hall_info.get('hall', 'Unknown'),
            "space_sqm": hall_info.get('space_sqm', 'Unknown'),
            "website": startup_info.get('website'),
            "about_page_url": startup_info.get('about_page_url'),
            "logo_url": hall_info.get('logo_url'),
            "category": ai_data['category'],
            "summary": ai_data['summary'],
            "key_offerings": ai_data['key_offerings'],
            "tags": ai_data['tags'],
            "confidence": ai_data['confidence']
        }
        
        return enriched
    
    def run(self, limit=None, start_index=0):
        """Run enrichment for all startups."""
        print("=" * 70)
        print("🚀 Startup Data Enrichment Pipeline")
        print("=" * 70)
        
        # Load data
        if not self.load_data():
            print("❌ Failed to load required data files")
            return
        
        startup_names = list(self.startup_data.keys())
        total = len(startup_names)
        
        if limit:
            startup_names = startup_names[start_index:start_index + limit]
            print(f"\n🎯 Processing {len(startup_names)} startups (from index {start_index})")
        else:
            print(f"\n🎯 Processing all {total} startups")
        
        # Load existing results if any
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                self.results = existing_data.get('results', [])
                print(f"📂 Loaded {len(self.results)} existing results")
        except FileNotFoundError:
            print("📂 Starting fresh")
            self.results = []
        
        # Process each startup
        for idx, name in enumerate(startup_names, start=start_index + 1):
            # Skip if already processed
            if any(r['name'] == name for r in self.results):
                print(f"\n[{idx}/{total}] ⏭️  Skipping {name} (already enriched)")
                continue
            
            result = self.enrich_startup(name, idx, total)
            self.results.append(result)
            
            # Save progress
            self.save_results()
            
            # Rate limiting
            time.sleep(1)
        
        print("\n" + "=" * 70)
        print("✅ Enrichment complete!")
        self.print_summary()
        print("=" * 70)
    
    def save_results(self):
        """Save enriched results to JSON file."""
        output_data = {
            "total_enriched": len(self.results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": self.model,
            "results": self.results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print enrichment summary."""
        total = len(self.results)
        
        # Category distribution
        category_counts = {}
        confidence_counts = {"High": 0, "Medium": 0, "Low": 0}
        hall_distribution = {}
        
        for result in self.results:
            cat = result.get('category', 'Unknown')
            conf = result.get('confidence', 'Low')
            hall = result.get('hall', 'Unknown')
            
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if conf in confidence_counts:
                confidence_counts[conf] += 1
            hall_distribution[hall] = hall_distribution.get(hall, 0) + 1
        
        print(f"\n📊 Enrichment Summary:")
        print(f"   Total enriched: {total}")
        
        print(f"\n📈 AI Confidence:")
        for conf, count in sorted(confidence_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {conf}: {count}")
        
        print(f"\n🏷️  Top 10 Categories:")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {cat}: {count}")
        
        print(f"\n🏢 Hall Distribution (Top 10):")
        for hall, count in sorted(hall_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   Hall {hall}: {count} startups")
        
        print(f"\n💾 Results saved to: {self.output_file}")


if __name__ == "__main__":
    import sys
    
    # API key
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCwTx6-aQnXJ9DFLOm6n2KmKHT7wH6d6NM')
    
    # Parse arguments
    limit = 5  # Default: test with 5
    start_index = 0
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            limit = None
        else:
            try:
                limit = int(sys.argv[1])
            except ValueError:
                print("Usage: python3 enrich_startups.py [all|number] [start_index]")
                print("Examples:")
                print("  python3 enrich_startups.py          # Process 5 startups (test)")
                print("  python3 enrich_startups.py 20       # Process 20 startups")
                print("  python3 enrich_startups.py all      # Process all startups")
                print("  python3 enrich_startups.py all 50   # Process all, starting from #50")
                sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print("Error: start_index must be a number")
            sys.exit(1)
    
    enricher = StartupEnricher(api_key=api_key)
    enricher.run(limit=limit, start_index=start_index)

