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
pantry-pulse-orchestrator/
├── DEMO_SCRIPT_UPDATED.sh
├── deploy.sh
├── Procfile
├── render.yaml
├── runtime.txt
├── vercel.json
├── backend/
│   ├── .env.example
│   ├── .env.production.example
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── biometric.py
│   │   │   ├── community.py
│   │   │   ├── exit_strategy.py
│   │   │   ├── household.py
│   │   │   ├── inventory.py
│   │   │   ├── profile.py
│   │   │   ├── recipe.py
│   │   │   └── waste.py
│   │   ├── modules/
│   │   │   └── waste_engine/
│   │   │       ├── agents/
│   │   │       ├── charities_database.py
│   │   │       ├── food_safety_standards.py
│   │   │       ├── orchestrator.py
│   │   │       ├── rag_retriever.py
│   │   │       ├── rag_retriever_advanced.py
│   │   │       ├── smart_decision_engine.py
│   │   │       └── upcycle_nonfood_uses.py
│   │   ├── routers/
│   │   │   ├── analyze.py
│   │   │   ├── community.py
│   │   │   ├── exit_strategy.py
│   │   │   ├── household.py
│   │   │   ├── inventory.py
│   │   │   ├── meals.py
│   │   │   ├── notifications.py
│   │   │   ├── profile.py
│   │   │   ├── recipes.py
│   │   │   ├── shopping.py
│   │   │   └── waste.py
│   │   ├── services/
│   │   │   ├── barcode_service.py
│   │   │   ├── bayesian_freshness_service.py
│   │   │   ├── clip_freshness_service.py
│   │   │   ├── cv_freshness_service.py
│   │   │   ├── ensemble_freshness_service.py
│   │   │   ├── gemini_service.py
│   │   │   ├── household_service.py
│   │   │   ├── image_crop_service.py
│   │   │   ├── inventory_service.py
│   │   │   ├── llm_reasoning_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── receipt_fallback_service.py
│   │   │   ├── recipe_service.py
│   │   │   ├── vit_anomaly_service.py
│   │   │   └── waste_service.py
│   │   └── utils/
│   ├── requirements.txt
│   └── tests/
│       ├── test_all_food_types_complete.py
│       ├── test_decision_engine_comprehensive.py
│       ├── test_receipt_fallback.py
│       ├── test_upcycle_steps_fix.py
│       ├── test_upcycle_with_steps.py
│       └── test_visual_hazard_safety.py
├── web/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── theme.ts
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
└── README.md
```

## Getting Started

### Prerequisites

| Requirement | Version | Download |
|-------------|---------|----------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Git | any | [git-scm.com](https://git-scm.com/) |
| Gemini API Key | — | [aistudio.google.com](https://aistudio.google.com) |

Tesseract OCR is also required for the receipt fallback parser.

---

### Quick Deploy (For Judges)

**Want to demo the app instantly?** This repository includes deployment-ready files for common free hosts:

- `render.yaml` + `Procfile` for Render
- `vercel.json` for Vercel
- `deploy.sh` for scripted deployment flow
- `DEMO_SCRIPT_UPDATED.sh` for guided demo steps

Live demo will be available at: `https://pantry-pulse-web.onrender.com` (once deployed)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/pantry-pulse-orchestrator.git
cd pantry-pulse-orchestrator
```

---

### 2. Install Tesseract OCR

#### macOS
```bash
brew install tesseract
```

#### Windows
1. Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR\`)
3. Add Tesseract to your PATH:
   - Open **System Properties → Advanced → Environment Variables**
   - Under **System variables**, find `Path` and click **Edit**
   - Add `C:\Program Files\Tesseract-OCR\`
4. Verify: open a new terminal and run `tesseract --version`

---

### 3. Backend Setup

#### macOS / Linux

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Open .env and set your GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

#### Windows (Command Prompt)

```cmd
cd backend

python -m venv .venv
.venv\Scripts\activate.bat

pip install -r requirements.txt

copy .env.example .env
rem Open .env in a text editor and set your GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

#### Windows (PowerShell)

```powershell
cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

Copy-Item .env.example .env
# Open .env and set your GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

> **Windows PowerShell note:** If you get an execution policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

API docs available at: `http://localhost:8000/docs`

---

### 4. Configure Environment Variables

Edit `backend/.env` and fill in your values:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: rotate through multiple keys to avoid rate limits
# GEMINI_API_KEYS=key1,key2,key3

# Database (optional — app works without Supabase in demo mode)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

---

### 5. Web Setup

#### macOS / Linux / Windows

```bash
cd web
npm install
npm run dev
```

Web app: `http://localhost:5173`

`web/vite.config.ts` already proxies `/api` to `http://localhost:8000` for local development — no extra configuration needed.

---

### Production Build (Web)

```bash
cd web
npm run build
npm run preview
```

---

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `ECONNREFUSED` in Vite | Backend is not running — start uvicorn first |
| `ValidationError` on startup | `.env` has unknown keys — ensure `"extra": "ignore"` is in `config.py` |
| `tesseract is not installed` | Install Tesseract and ensure it's on your PATH (see step 2) |
| PowerShell activation error | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `torch` install fails on Windows | Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) first |
| Port 8000 already in use (macOS) | Run `lsof -ti :8000 \| xargs kill -9` |
| Port 8000 already in use (Windows) | Run `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |

## API Endpoints

The backend API is available under `/api/*` and includes inventory, analysis, meals, shopping, waste tracking, profile, community, household, recipes, notifications, and exit strategy routes.

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
