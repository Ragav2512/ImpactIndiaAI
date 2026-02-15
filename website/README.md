# India AI Impact Expo - Startup Directory Website

## 📊 Overview

An interactive, modern static website showcasing **395+ startups** from the India AI Impact Expo 2026.

## ✨ Features

- **🔍 Real-time Search**: Search by startup name, category, technology, or keywords
- **🎯 Smart Filtering**: Filter by industry category or hall number
- **📱 Responsive Design**: Works beautifully on desktop, tablet, and mobile
- **💫 Modern UI**: Glassmorphism effects, smooth animations, gradient accents
- **📋 Detailed View**: Click any startup for comprehensive information
- **🏢 Hall Information**: See booth locations and sizes

## 🚀 Quick Start

### Option 1: Simple HTTP Server (Python)
```bash
cd website
python3 -m http.server 8000
```
Then open: http://localhost:8000

### Option 2: Using npx
```bash
cd website
npx serve
```

### Option 3: Direct File
Simply double-click `index.html` to open in your browser

## 📁 Files

- `index.html` - Main webpage structure
- `style.css` - Modern styling with animations
- `app.js` - Interactive functionality
- `enriched_startups.json` - Startup data (395 entries)

## 📊 Data Included

For each startup:
- ✅ Company name
- ✅ Hall & booth number
- ✅ Booth size (sqm)
- ✅ Website link
- ✅ Category (AI/ML, Healthcare, FinTech, etc.)
- ✅ 2-3 sentence summary
- ✅ Key offerings/products
- ✅ Technology tags
- ✅ Logo (when available)

## 🎨 Design Features

- **Glassmorphism UI**: Frosted glass effects
- **Gradient Accents**: Purple-blue-pink color scheme
- **Smooth Animations**: Fade-in, slide-in transitions
- **Hover Effects**: Interactive card transformations
- **Sticky Filters**: Search bar stays visible while scrolling

## 📝 Note

**Key Person/Presenter Data**: Currently being collected and will be added to the dataset soon. Each startup card will be updated to include:
- Presenter name
- Role/title
- Contact information (if available)

## 🛠️ Technologies Used

- HTML5
- CSS3 (Custom Properties, Flexbox, Grid)
- Vanilla JavaScript (ES6+)
- Google Fonts (Inter)

## 📈 Stats

- **395 Startups** showcased
- **20 Categories** (AI/ML, Healthcare, AgriTech, etc.)
- **15 Halls** at the expo venue
- **343 Detailed Profiles** (with AI-generated summaries)

## 🤝 Contributing

To add or update startup information:
1. Edit `enriched_startups.json`
2. Refresh the webpage
3. Changes will appear immediately

## 📧 Contact

For questions or data updates, please contact the India AI Impact Expo team at:
aiimpactexpo@stpi.in

---

**Powered by**: AI-driven web scraping and data enrichment using Gemini API
