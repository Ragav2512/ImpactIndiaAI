import json
import re

class LocalEnricher:
    """
    Fills missing summaries and categories using local rule-based extraction
    when AI rate limits are hit.
    """
    
    def __init__(self):
        self.input_file = 'enriched_startups_final.json'
        self.about_pages_file = 'startup_about_pages.json'
        self.output_file = 'enriched_startups_complete.json'
        
        # Simple keyword mapping for fallback categorization
        self.category_keywords = {
            "Healthcare & Biotech": ["health", "medical", "patient", "diagnostic", "clinic", "hospital", "pharma", "biotech"],
            "Fintech & Banking": ["finance", "bank", "payment", "fintech", "loan", "credit", "wealth", "insurtech", "invest"],
            "Education & EdTech": ["education", "learning", "student", "school", "training", "edtech", "course", "skill", "university", "academy"],
            "Agriculture & AgriTech": ["farm", "agri", "crop", "harvest", "soil", "cattle", "dairy", "livestock"],
            "Cybersecurity": ["security", "cyber", "protection", "threat", "firewall", "auth", "defense", "secure"],
            "E-commerce & Retail": ["retail", "ecommerce", "shop", "store", "buy", "sell", "marketplace", "consumer"],
            "Robotics & Automation": ["robot", "drone", "automation", "autonomous", "unmanned"],
            "Logistics & Supply Chain": ["logistics", "supply chain", "transport", "delivery", "fleet", "warehouse"],
            "Real Estate & PropTech": ["real estate", "property", "housing", "construction", "building"],
            "HR & Workforce Management": ["hr", "recruitment", "hiring", "talent", "employee", "workforce"],
            "Marketing & Sales Tech": ["marketing", "sales", "adtech", "brand", "customer", "crm"],
            "Climate & Sustainability": ["climate", "sustainable", "carbon", "energy", "solar", "waste", "water", "green"],
            "AI/ML Infrastructure & Tools": ["ai", "machine learning", "ml", "data", "analytics", "cloud", "software", "platform", "algorithm", "model"]
        }
    
    def load_data(self):
        """Load data files."""
        print("📂 Loading data...")
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                self.results = self.data['results']
            
            with open(self.about_pages_file, 'r', encoding='utf-8') as f:
                about_data = json.load(f)
                self.about_map = {item['name']: item.get('about_content', '') for item in about_data['results']}
                
            print(f"   ✅ Loaded {len(self.results)} startups")
            return True
        except Exception as e:
            print(f"   ❌ Error loading data: {e}")
            return False

    def clean_text(self, text):
        """Clean and normalize extraction text."""
        if not text:
            return ""
        # Remove multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove common "About Us" prefixes
        text = re.sub(r'^(About Us|Our Story|Welcome to|Who We Are)[\s\-\:]+', '', text, flags=re.IGNORECASE)
        # Limit length
        return text

    def extract_summary(self, text):
        """Extract first few sentences as summary."""
        if not text or len(text) < 20:
            return None
            
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Take first 3 meaningful sentences
        summary_sentences = []
        char_count = 0
        
        for sent in sentences:
            if len(sent) < 5 or "cookie" in sent.lower() or "copyright" in sent.lower():
                continue
            summary_sentences.append(sent)
            char_count += len(sent)
            if char_count > 350:
                break
        
        if not summary_sentences:
            return None
            
        summary = ' '.join(summary_sentences)
        return summary[:400] + "..." if len(summary) > 400 else summary

    def categorize_by_keywords(self, text):
        """Infer category from keywords."""
        if not text:
            return "Other"
            
        text_lower = text.lower()
        
        # Check each category
        scores = {}
        for cat, keywords in self.category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[cat] = score
        
        if not scores:
            return "Other"
            
        # Return category with highest match count
        return max(scores, key=scores.get)

    def run(self):
        """Process all startups with missing data."""
        print("=" * 60)
        print("🛠️  Running Local Data Enrichment (Fallback)")
        print("=" * 60)
        
        if not self.load_data():
            return
            
        enhanced_count = 0
        
        for startup in self.results:
            # Check if needs enhancement
            needs_summary = (
                startup.get('summary') in [
                    'Failed to process with AI', 
                    'No information available', 
                    None
                ]
            )
            
            needs_category = startup.get('category') in ['Error', 'No Data']
            
            if needs_summary or needs_category:
                name = startup['name']
                about_content = self.about_map.get(name, '')
                cleaned_content = self.clean_text(about_content)
                
                # 1. Fill Summary
                if needs_summary:
                    extracted = self.extract_summary(cleaned_content)
                    if extracted:
                        startup['summary'] = extracted
                        startup['confidence'] = "Low (Extracted)"
                        # Extract rudimentary tags/key offerings from summary words? (Skipping for now to keep it clean)
                    else:
                        startup['summary'] = "Information not available."
                
                # 2. Fill Category
                if needs_category:
                    if cleaned_content:
                        new_cat = self.categorize_by_keywords(cleaned_content)
                        startup['category'] = new_cat
                        if not startup.get('tags'):
                            # Add category as a tag
                            startup['tags'] = [new_cat.split('&')[0].strip()]
                    else:
                        startup['category'] = "Uncategorized"
                
                enhanced_count += 1
        
        print(f"\n✅ Enhanced {enhanced_count} startups locally")
        
        # Save results
        self.save_results()

    def save_results(self):
        """Save final complete json."""
        output_data = {
            "total_enriched": len(self.results),
            "timestamp": self.data.get('timestamp'),
            "model_used": "hybrid (gemini + local)",
            "results": self.results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to {self.output_file}")

if __name__ == "__main__":
    enricher = LocalEnricher()
    enricher.run()
