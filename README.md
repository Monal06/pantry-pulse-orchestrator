# FreshSave: AI-Powered Circular Food Economy
### Atlantec AI Challenge 2026 Submission

**Repository:** `pantry-pulse-orchestrator`

**FreshSave** is an AI-driven decision engine for the circular food economy, utilizing Multi-agent Orchestration and Safety Guardrails to automate sustainable food exit strategies.

---

## 🚀 Live Demo & Links

**[👉 View FreshSave Live](https://pantry-pulse-orchestrator-web.onrender.com)** — Open here to see the app in action!

**[API Documentation](https://pantry-pulse-orchestrator.onrender.com/docs)** — FastAPI interactive endpoint explorer

FreshSave helps individuals and households reduce food waste through:
- Smart inventory tracking powered by AI vision analysis
- Real-time freshness monitoring with decay prediction
- Intelligent meal suggestions based on available items
- Sustainable exit strategies (upcycle, share, dispose) with multi-gate safety validation
- Community food sharing and waste tracking dashboard

### Judging Criteria Alignment

| Criterion | How FreshSave Addresses It |
|-----------|---------------------------|
| **Innovation** | Multi-agent orchestration with 4-gate safety validation; dual-path freshness detection (Bayesian + Visual); RAG-powered food safety standards; non-food creative upcycling database; smart decision engine works at ANY freshness score |
| **Societal Impact** | Reduces household food waste; connects donors with 15+ Galway charities; educates on environmental impact (2.5kg CO2 saved per item); democratizes waste management with free-tier architecture |
| **Technical Depth** | FastAPI backend with async agents; React TypeScript frontend with expandable action cards; Gemini 2.5 Flash + Groq hybrid LLM routing; computer vision for spoilage detection; USDA FoodKeeper + Bayesian freshness modeling; RAG retrieval for food safety standards |
| **Ethical Compliance** | **100% free-tier architecture** (Render, Supabase free tier, Google AI Studio, Open Food Facts); transparent 3-gate safety validation prevents unsafe recommendations; explicit consent flows; no data exploitation; environmental benefit quantified and displayed |

---

## 💡 Key Features & Innovation

### Dual-Gate Freshness Detection
- **Bayesian Model**: Predicts decay based on EFSA/FDA standards for 100+ food items across all storage types
- **Visual Analysis**: AI detects mold, discoloration, wilting, and spoilage via photo analysis
- **Age Verification**: Compares stored age against official safety limits
- **USDA FoodKeeper Integration**: Uses item-level shelf-life data (661 products) before falling back to category decay rates

### Multi-Agent Orchestration
Three specialized agents handle different exit paths:
1. **Upcycle Agent** — Suggests creative non-food uses (composting, face masks, natural dyes, crafts)
2. **Charity Finder Agent** — Identifies local charities, community fridges, and drop-off instructions
3. **Disposal Guide Agent** — Provides Galway-specific waste bin guidance with environmental impact

### Smart Decision Engine
- Evaluates **all three exit paths** (upcycle, share, dispose) at any freshness score
- **4-gate safety validation** prevents dangerous recommendations:
  - Gate 1: Freshness Score (0-100 scale)
  - Gate 2: Visual Spoilage Detection (mold, etc.)
  - Gate 3: Age Verification (vs. EFSA limits)
  - Gate 4: Category-specific rules
- Ranks recommendations by user context (has garden? in office? environmental priority?)

## Features

### Smart Food Input (3 Methods)
- **Fridge/Cupboard Photo**: Upload a photo of your open fridge or cupboard. AI identifies visible food items and checks for spoilage (mold, discoloration, wilting).
- **Receipt Scanning**: Upload a grocery receipt image to auto-populate your pantry with purchased items. If Gemini is unavailable, the backend automatically falls back to OCR-based receipt parsing.
- **Voice Input**: Speak your items naturally (e.g., "I just bought 2 avocados and milk"). AI transcribes and adds them to your inventory.
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

**Weekly Meal Planning**: Plan out your entire week with freshness projections to minimize waste across the week

### Waste Tracking Dashboard
Track your food waste reduction impact over time:
- **Items saved vs. wasted** with save rate percentage
- **Money saved** (estimated from food category averages)
- **CO2 prevented** (2.5 kg per food item saved)
- **Weekly trend** bar chart (saved vs wasted per week)
- **Category breakdown** (which food types you save/waste most)
- **Recent activity feed** with save/waste/freeze/donate events

### Additional Product Areas
- **Saved Recipes**: Store and organize your favorite recipes for quick reference
- **Dietary Profile**: Define your dietary preferences, allergies, and cuisine preferences
- **Nutritional Balance**: Analyze the nutritional content of your current inventory
- **Freshness Notifications**: Real-time alerts when items are approaching critical freshness

## Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Web | React + TypeScript + Vite | Free |
| Backend | Python + FastAPI | Free |
| AI | Google Gemini 2.5 Flash (Google AI Studio) | Free tier |
| Database | Supabase (PostgreSQL + Auth + Storage) | Free tier |
| Hosting | Render | Free tier |

**Total cost: $0**

## 🌱 Ethical AI & Free-Tier Infrastructure

### Why Free Tier?
FreshSave is built entirely on free-tier services to ensure **equitable access** and demonstrate that impactful AI applications don't require expensive infrastructure. This aligns with our mission to democratize food waste reduction.

### All Services Are Free
- **Google Gemini 2.5 Flash**: Free tier via Google AI Studio (15 requests/minute + 60 requests/hour)
- **Groq API**: Free tier for fallback LLM routing (improves reliability)
- **Supabase**: Free PostgreSQL database + Auth + Storage (suitable for MVP/demo)
- **Render**: Free tier web hosting with automatic deployments from GitHub
- **UptimeRobot**: Free tier monitoring with 50+ check intervals per month

### Keeping Free Tier Alive: UptimeRobot Integration
Render's free tier spins down applications after 15 minutes of inactivity. To keep FreshSave running 24/7, we use **UptimeRobot** (free tier):

1. **UptimeRobot Monitor**: Pings our `/health` endpoint every 10 minutes
2. **Keeps Render Alive**: Prevents the app from being hibernated
3. **Uptime Reports**: Tracks 99.9% availability (no cost)
4. **Alerts**: Notifies if the app goes down (via email, Slack, webhooks)

**Setup:**
```bash
# UptimeRobot monitors: https://pantry-pulse-orchestrator.onrender.com/health
# Ping frequency: 10 minutes
# Free tier allows unlimited monitors with 10-minute checks
```

This approach ensures the live demo stays accessible for judges without incurring any costs.

---

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
│   │   ├── data/
│   │   │   └── foodkeeper_data.json
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
│   │   │   ├── foodkeeper_service.py
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
│       ├── test_foodkeeper_integration.py
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
| Groq API Key (Optional Backup) | — | [console.groq.com/keys](https://console.groq.com/keys) |

Tesseract OCR is also required for the receipt fallback parser.

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/Monal06/pantry-pulse-orchestrator.git
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
# Optional: set GROQ_API_KEY for backup text model

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
rem Optional: set GROQ_API_KEY for backup text model

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
# Optional: set GROQ_API_KEY for backup text model

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

# Optional: backup model for text-only fallback when Gemini is unavailable/rate-limited
GROQ_API_KEY=your_groq_api_key_here

# Optional: rotate through multiple keys to avoid rate limits
# GEMINI_API_KEYS=key1,key2,key3

# Database (optional — app works without Supabase in demo mode)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).
Get an optional Groq API key at [console.groq.com/keys](https://console.groq.com/keys).

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

## Deployment

#### How We Deploy to Render (Free Tier)

1. **Connect GitHub Repository**: Link your GitHub repo to Render
2. **Create Web Service**: Set up auto-deploy from `main` branch
3. **Configure Environment**: Add `GEMINI_API_KEY` and optionally `GROQ_API_KEY` in Render environment variables
4. **Deploy**: Render automatically builds and deploys from `render.yaml`
5. **Keep Alive**: UptimeRobot pings `/health` endpoint every 10 minutes to prevent hibernation

#### Configuration Files

- **`render.yaml`**: Specifies build and start commands for Render
- **`Procfile`**: Defines how to start the FastAPI backend (`web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- **`vite.config.ts`**: Web app already proxies `/api` to backend

This entire setup costs **$0** and maintains 99.9% uptime.

## API Endpoints

The backend API is available under `/api/*` and includes inventory, analysis, meals, shopping, waste tracking, profile, community, household, recipes, notifications, and exit strategy routes.

For complete endpoint details, see router files in `backend/app/routers/` or open FastAPI docs at `http://localhost:8000/docs`.

## Freshness Decay Model

Freshness uses USDA-backed defaults with item-level FoodKeeper overrides where available.

Default category decay rates (points/day):

| Category | Fridge | Freezer | Pantry | Counter |
|----------|--------|---------|--------|---------|
| Dairy | 14.3/day | 1.1/day | 50.0/day | 50.0/day |
| Meat | 25.0/day | 0.42/day | 100.0/day | 100.0/day |
| Seafood | 50.0/day | 0.83/day | 100.0/day | 100.0/day |
| Fruit | 7.1/day | 0.83/day | 10.0/day | 14.3/day |
| Vegetable | 10.0/day | 0.83/day | 14.3/day | 20.0/day |
| Bread | 7.1/day | 1.1/day | 14.3/day | 14.3/day |

`freshness_score = 100 - (days_since_added * decay_rate)`

## License

MIT
