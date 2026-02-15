import json
import time
import os
from google import genai

class StartupCategorizer:
    """
    Categorizes startups using Gemini API based on their about page content.
    """
    
    def __init__(self, api_key, input_file='startup_about_pages.json', output_file='categorized_startups.json'):
        self.api_key = api_key
        self.input_file = input_file
        self.output_file = output_file
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-exp"
        self.results = []
        
        # Define category schema
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
    
    def load_startup_data(self):
        """Load the startup data from JSON file."""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['results']
    
    def create_categorization_prompt(self, startup_name, about_content):
        """
        Create a prompt for the Gemini API to categorize the startup.
        """
        categories_str = "\n".join([f"- {cat}" for cat in self.categories])
        
        prompt = f"""Analyze the following startup and categorize it based on its primary business focus.

Startup Name: {startup_name}

About Content:
{about_content[:1500] if about_content else "No content available"}

Available Categories:
{categories_str}

Instructions:
1. Choose the SINGLE most appropriate primary category from the list above
2. Provide a brief 1-2 sentence explanation of why this category fits
3. List 2-3 key services/products offered by this startup
4. Rate the confidence of this categorization (Low/Medium/High)

Response should be in this EXACT JSON format:
{{
    "primary_category": "Category Name",
    "explanation": "Brief explanation here",
    "key_offerings": ["Service 1", "Service 2", "Service 3"],
    "confidence": "High|Medium|Low"
}}

IMPORTANT: Return ONLY the JSON, no additional text."""
        
        return prompt
    
    def categorize_startup(self, startup_data):
        """
        Use Gemini API to categorize a single startup.
        """
        startup_name = startup_data['name']
        about_content = startup_data.get('about_content', '')
        
        if not about_content:
            return {
                "primary_category": "Unknown",
                "explanation": "No content available for analysis",
                "key_offerings": [],
                "confidence": "Low"
            }
        
        try:
            # Create prompt
            prompt = self.create_categorization_prompt(startup_name, about_content)
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                # Find the actual JSON content
                lines = response_text.split('\n')
                json_lines = [line for line in lines if not line.startswith('```')]
                response_text = '\n'.join(json_lines).strip()
            
            # Parse JSON
            categorization = json.loads(response_text)
            
            return categorization
            
        except Exception as e:
            print(f"   ⚠️  Categorization error: {str(e)}")
            return {
                "primary_category": "Error",
                "explanation": f"Failed to categorize: {str(e)}",
                "key_offerings": [],
                "confidence": "Low"
            }
    
    def process_startup(self, startup_data, index, total):
        """
        Process a single startup: categorize and save results.
        """
        name = startup_data['name']
        print(f"\n[{index}/{total}] Categorizing: {name}")
        
        # Skip if no content
        if startup_data.get('status') != 'success':
            print(f"   ⏭️  Skipping (no content available)")
            result = {
                **startup_data,
                "categorization": {
                    "primary_category": "No Data",
                    "explanation": "Website or content not available",
                    "key_offerings": [],
                    "confidence": "Low"
                }
            }
            return result
        
        # Categorize
        print(f"   🤖 Analyzing with Gemini API...")
        categorization = self.categorize_startup(startup_data)
        
        print(f"   ✅ Category: {categorization['primary_category']} (Confidence: {categorization['confidence']})")
        
        # Combine original data with categorization
        result = {
            **startup_data,
            "categorization": categorization
        }
        
        return result
    
    def run(self, limit=None, start_index=0):
        """
        Run categorization for all startups.
        
        Args:
            limit: Maximum number of startups to process (None for all)
            start_index: Starting index (useful for resuming)
        """
        print("=" * 70)
        print("🤖 AI-Powered Startup Categorization using Gemini API")
        print("=" * 70)
        
        # Load startup data
        startups = self.load_startup_data()
        total = len(startups)
        
        print(f"\n📊 Loaded {total} startups from {self.input_file}")
        
        if limit:
            startups = startups[start_index:start_index + limit]
            print(f"🎯 Processing {len(startups)} startups (from index {start_index})")
        
        # Load existing results if any
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                self.results = existing_data.get('results', [])
                print(f"📂 Loaded {len(self.results)} existing categorizations")
        except FileNotFoundError:
            print("📂 Starting fresh (no existing categorizations)")
            self.results = []
        
        # Process each startup
        for idx, startup in enumerate(startups, start=start_index + 1):
            # Check if already processed
            if any(r['name'] == startup['name'] for r in self.results):
                print(f"\n[{idx}/{total}] ⏭️  Skipping {startup['name']} (already categorized)")
                continue
            
            result = self.process_startup(startup, idx, total)
            self.results.append(result)
            
            # Save progress after each startup
            self.save_results()
            
            # Rate limiting - be respectful to API
            time.sleep(1)
        
        print("\n" + "=" * 70)
        print("✅ Categorization complete!")
        self.print_summary()
        print("=" * 70)
    
    def save_results(self):
        """Save categorized results to JSON file."""
        output_data = {
            "total_categorized": len(self.results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": self.model,
            "results": self.results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print a summary of categorization results."""
        total = len(self.results)
        
        # Count by category
        category_counts = {}
        confidence_counts = {"High": 0, "Medium": 0, "Low": 0}
        
        for result in self.results:
            cat = result.get('categorization', {})
            primary_cat = cat.get('primary_category', 'Unknown')
            confidence = cat.get('confidence', 'Low')
            
            category_counts[primary_cat] = category_counts.get(primary_cat, 0) + 1
            if confidence in confidence_counts:
                confidence_counts[confidence] += 1
        
        print(f"\n📊 Categorization Summary:")
        print(f"   Total categorized: {total}")
        print(f"\n📈 Confidence Distribution:")
        print(f"   High: {confidence_counts['High']}")
        print(f"   Medium: {confidence_counts['Medium']}")
        print(f"   Low: {confidence_counts['Low']}")
        
        print(f"\n🏷️  Top 10 Categories:")
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats[:10]:
            print(f"   {cat}: {count}")
        
        print(f"\n💾 Results saved to: {self.output_file}")


if __name__ == "__main__":
    import sys
    
    # Get API key from environment or command line
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCwTx6-aQnXJ9DFLOm6n2KmKHT7wH6d6NM')
    
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
                print("Usage: python3 categorize_startups.py [all|number] [start_index]")
                print("Examples:")
                print("  python3 categorize_startups.py          # Categorize 5 startups (test)")
                print("  python3 categorize_startups.py 20       # Categorize 20 startups")
                print("  python3 categorize_startups.py all      # Categorize all startups")
                print("  python3 categorize_startups.py all 50   # Categorize all, starting from index 50")
                sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            start_index = int(sys.argv[2])
        except ValueError:
            print("Error: start_index must be a number")
            sys.exit(1)
    
    categorizer = StartupCategorizer(api_key=api_key)
    categorizer.run(limit=limit, start_index=start_index)
