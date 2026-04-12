# pantry-pulse-orchestrator
An AI-driven decision engine for the circular food economy, utilizing Multi-agent Orchestration and Safety Guardrails to automate sustainable food exit strategies.

# FreshSave - AI-Powered Food Waste Reduction

A web app that helps individuals and households reduce food waste through smart inventory tracking, AI-driven freshness monitoring, meal suggestions, and intelligent shopping lists.

## Features

### Smart Food Input (4 Methods)
- **Fridge/Cupboard Photo**: Upload a photo of your open fridge or cupboard. AI identifies visible food items and checks for spoilage (mold, discoloration, wilting).
- **Receipt Scanning**: Upload a grocery receipt image to auto-populate your pantry with purchased items. If Gemini is unavailable, the backend automatically falls back to OCR-based receipt parsing.
- **Barcode Scanning**: Enter a product barcode (EAN/UPC) to look up items via the free Open Food Facts database.
- **Manual Entry**: Add items with category, quantity, storage location, and perishability.

### Freshness Tracking
Every perishable item gets a **freshness score (0-100)** that depreciates daily based on food category and storage method:
- **70-100 (Green - Fresh)**: Safe to use in any meal plan
- **50-70 (Yellow - Use Soon)**: Notification that item should be used in the next few meals
- **Below 50 (Red - Critical)**: AI suggests alternative uses to prevent waste (e.g., overripe bananas -> banana bread)

### Visual Spoilage Detection
When adding items via photo, AI checks for:
- Mold (fuzzy patches, spots)
- Abnormal browning or discoloration
- Wilting, sliminess, or shriveling
- Swollen or damaged packaging

### Freeze Suggestions
When items drop into the 30-70 freshness range, the app suggests freezing them:
- Snowflake indicator appears on freezable items in inventory
- Banner alerts show how many items could be frozen
- Moving to freezer dramatically slows decay (e.g., meat goes from 8/day to 0.3/day)
- Freeze events are tracked in your impact dashboard

### Daily Meal Suggestions (Dietary-Aware)
AI generates meal ideas each day based on your current inventory, prioritizing:
1. **Critical items** (freshness < 50) - must be used immediately
2. **Use-soon items** (freshness 50-70) - should be in the next few meals
3. **Fresh items** - available for any recipe

### Waste Tracking Dashboard
Track your food waste reduction impact over time:
- **Items saved vs. wasted** with save rate percentage
- **Money saved** (estimated from food category averages)
- **CO2 prevented** (2.5 kg per food item saved)
- **Weekly trend** bar chart (saved vs wasted per week)
- **Category breakdown** (which food types you save/waste most)
- **Recent activity feed** with save/waste/freeze/donate events

### Additional Product Areas
- Weekly meal planning with freshness projection
- Dietary profile and allergy preferences
- Community food sharing
- Household pantry sharing
- Saved recipes and favorites
- Nutritional balance analysis
- Freshness notifications

## Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Web | React + TypeScript + Vite | Free |
| Backend | Python + FastAPI | Free |
| AI | Google Gemini 2.5 Flash (Google AI Studio) | Free tier |
| Database | Supabase (PostgreSQL + Auth + Storage) | Free tier |
| Barcode Lookup | Open Food Facts API | Free |
| Hosting | Render | Free tier |

**Total cost: $0**

## Project Structure

```text
freshsave/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── utils/
│   └── requirements.txt
├── web/
│   ├── src/
│   │   ├── pages/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free [Google AI Studio](https://aistudio.google.com) API key
- Tesseract OCR (used as receipt fallback model)

On macOS:
```bash
brew install tesseract
```

### Backend Setup

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Web Setup

```bash
cd web
npm install
npm run dev
```

Web app: `http://localhost:5173`

`web/vite.config.ts` already proxies `/api` to `http://localhost:8000` for local development.

### Production Build (Web)

```bash
cd web
npm run build
npm run preview
```

## API Endpoints

The backend API is available under `/api/*` and includes inventory, analysis, meals, shopping, waste tracking, profile, community, household, recipes, and notifications routes.

For complete endpoint details, see router files in `backend/app/routers/` or open FastAPI docs at `http://localhost:8000/docs`.

## Freshness Decay Model

Each food category has a daily decay rate per storage location:

| Category | Fridge | Freezer | Pantry | Counter |
|----------|--------|---------|--------|---------|
| Dairy | 5.0/day | 0.5/day | 15.0/day | 15.0/day |
| Meat | 8.0/day | 0.3/day | 25.0/day | 25.0/day |
| Seafood | 10.0/day | 0.3/day | 30.0/day | 30.0/day |
| Fruit | 3.5/day | 0.5/day | 5.0/day | 6.0/day |
| Vegetable | 3.0/day | 0.4/day | 5.0/day | 6.0/day |
| Bread | 4.0/day | 0.3/day | 7.0/day | 7.0/day |

`freshness_score = 100 - (days_since_added * decay_rate)`

## License

MIT
