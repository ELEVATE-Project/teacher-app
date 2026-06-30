<table>
<tr>
<td width="200px">
<img src="figure/chanak_main.png" alt="Chanakya" width="200px" />
</td>
<td>

# Chanakya

### Real-time AI-powered classroom decision-support system for Indian primary school teachers

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-Educational-orange.svg)](LICENSE)

**Chanakya addresses the "implementation gap" in teacher training by providing just-in-time pedagogical support during live classroom moments. It combines multilingual NLP, RAG-based knowledge retrieval, and AI-powered feedback to help teachers deliver better learning outcomes.**

</td>
</tr>
</table>

## ✨ Key Features

- 🌐 **Multilingual Support** - Hindi, Bengali, Tamil, Telugu, and 12+ Indian languages
- 🤖 **AI-Powered Assistance** - Gemini 2.5 Flash integration for intelligent responses
- 📚 **NCERT RAG System** - Semantic search across NCERT textbooks
- 🎙️ **Voice Support** - Speech-to-text and text-to-speech via Sarvam AI
- 📊 **Teaching Analytics** - Real-time feedback and performance insights
- 👨‍🏫 **Dashboard** - Smart student feedback and classroom management

---

## 🎯 Core Modes & Features

<table>
<tr>
<td width="50%" valign="top">

### 📝 **Module Creator Mode**
#### *AI-Powered Lesson Builder*

Transforms NCERT textbook content into structured, ready-to-teach lessons with automatic assignment generation.

**What it does:**
- Generates fixed 8-slide lesson presentations
- Creates mixed assessments (MCQ, short answer, long answer)
- Validates content alignment with curriculum
- Exports in teacher-friendly formats

</td>
<td width="50%" valign="top">

### 🎤 **Active Listening Mode**
#### *Live Teaching Coach*

Real-time classroom audio analysis that provides actionable feedback on your teaching effectiveness.

**What it does:**
- Records and transcribes classroom audio (Sarvam AI STT)
- Automatic language detection for Indian languages
- AI-powered teaching analysis engine
- Structured feedback on engagement & improvement areas

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🚨 **Crisis Handling Mode**
#### *Instant Classroom Interventions*

Provides immediate, actionable strategies for managing live classroom disruptions without requiring devices or materials.

**What it does:**
- Handles noise, restlessness, low energy, loss of focus
- Designed for large, rural classrooms
- No device or material dependency
- Context-aware intervention suggestions

</td>
<td width="50%" valign="top">

### 🎯 **Personalized Q/A Generator**
#### *Smart Student Engagement*

Dynamically recommends which student to question and what difficulty level to use, based on real-time performance data.

**What it does:**
- Uses student profiles & performance history
- Multi-factor priority scoring algorithm
- Adaptive difficulty recommendations
- Ensures equitable classroom participation

</td>
</tr>
<tr>
<td colspan="2" valign="top">

### <img src="figure/twilio_transp.png" alt="Twilio" width="24px" style="vertical-align: middle;" /> **Offline Mode (Twilio Integration - Disabled)**
#### *Zero-Internet AI Access*

Enables teachers to interact with Chanakya's AI using regular phone calls or SMS—no internet, smartphone, or digital literacy required.

**What it does:**
- Voice and SMS-based AI interaction via Twilio (currently disabled)
- Works on basic feature phones
- Speech and text AI integration
- Delivers guidance in low-connectivity areas

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** | **Node.js 18+** | **MongoDB** (Atlas or local)
- API Keys: [OpenRouter](https://openrouter.ai/), [Sarvam AI](https://www.sarvam.ai/)

---

## ⚡ One-Command Setup (Recommended)

The fastest way to get started is using our setup scripts:

### Windows
```cmd
# Clone repository
git clone https://github.com/Kautilya346/Chanakya.git
cd Chanakya

# Run setup (installs everything)
setup.bat

# Start the application
run.bat
```

### Unix/Linux/Mac
```bash
# Clone repository
git clone https://github.com/Kautilya346/Chanakya.git
cd Chanakya

# Make scripts executable & run setup
chmod +x setup.sh run.sh
./setup.sh

# Start the application
./run.sh
```

**What the scripts do:**
1. ✅ Check for Python and Node.js
2. ✅ Create Python virtual environment (`venv/`)
3. ✅ Install all Python dependencies
4. ✅ Install all npm packages
5. ✅ Verify environment configuration

---

## 🔧 Manual Setup (Alternative)

If you prefer manual control, follow these steps:

### Step 1: Clone & Configure Environment

```bash
git clone https://github.com/Kautilya346/Chanakya.git
cd Chanakya

# Edit .env with your API keys
# Required: OPENROUTER_API_KEY, VITE_SARVAM_API_KEY
```

### Step 2: Backend Setup

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\venv\Scripts\activate.bat

# Activate (Unix/Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r Server/requirements.txt
```

### Step 3: Frontend Setup

```powershell
cd Client_F\front_chanak
npm install
cd ..\..
```

### Step 4: Run the Application

**Terminal 1 - Backend (Port 3000):**
```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Unix

# Run backend
python Server/Web_server/main.py
```

**Terminal 2 - Frontend (Port 5173):**
```powershell
cd Client_F\front_chanak
npm run dev
```

---

## ✅ Verify Setup

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:3000 |
| API Docs | http://localhost:3000/docs |
| Health Check | http://localhost:3000/health |

---

## 🔑 Environment Configuration

All configuration is stored in a single `.env` file in the project root:

```env
# ==================== Required ====================
OPENROUTER_API_KEY=your-openrouter-api-key

# ==================== Sarvam AI (Voice) ====================
VITE_SARVAM_API_KEY=your-sarvam-key
VITE_SARVAM_API_URL=https://api.sarvam.ai/speech-to-text
VITE_SARVAM_TTS_API_URL=https://api.sarvam.ai/text-to-speech

# ==================== API URL ====================
VITE_API_URL=http://localhost:3000

# ==================== MongoDB ====================
MONGODB_URL=your-mongodb-connection-string
DATABASE_NAME=Chanakya
```

---

## 🏗️ Architecture

<div align="center">
  <img src="figure/chanak_AD_fnl.png" alt="Chanakya Architecture Diagram" width="100%" />
</div>

---
## ✨ Special Features 




## 📁 Project Structure

```
Chanakya/
├── setup.bat / setup.sh       # One-command setup scripts
├── run.bat / run.sh           # One-command run scripts
├── .env                       # Unified environment configuration
│
├── Client_F/front_chanak/     # React + Vite Frontend
│   ├── src/                   # React components & pages
│   └── vite.config.js         # Vite configuration
│
├── Server/                    # Python Backend
│   ├── Web_server/            # FastAPI Application (main.py)
│   ├── nlp/                   # NLP Pipeline (Gemini integration)
│   ├── orchestrator/          # LangGraph Orchestration
│   ├── module/                # Lesson Builder (MODULE)
│   └── requirements.txt       # Python dependencies
│
├── embedding/                 # RAG System for NCERT Books
│   ├── generate_embeddings.py # PDF → Embeddings pipeline
│   ├── query_books.py         # Semantic search interface
│   └── ncert_books.db         # SQLite vector database
│
├── Finaldata/                 # NCERT PDF Books
└── main.py                    # Direct RAG query script
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User authentication |
| `/api/auth/register` | POST | User registration |
| `/api/query` | POST | AI-powered query processing |
| `/api/chat/history` | GET | Chat history retrieval |
| `/api/sarvam/stt` | POST | Speech-to-text (Indian languages) |
| `/api/sarvam/tts` | POST | Text-to-speech (Indian languages) |
| `/api/classes` | GET/POST | Class management |
| `/api/students` | GET/POST | Student management |
| `/api/questions` | GET/POST | Question bank |
| `/api/sessions` | GET/POST | Teaching sessions |
| `/api/analytics` | GET | Teaching analytics |
| `/api/reflection` | GET/POST | Teaching reflection analysis |

📚 **Full API documentation:** http://localhost:3000/docs

---

## 🌐 NLP Layer

The NLP layer converts teacher utterances in **any Indian language** to clear **English understanding** using **Gemini 2.5 Flash**.

### Supported Languages
Hindi, Bengali, Marathi, Tamil, Telugu, Kannada, Malayalam, Gujarati, Odia, Punjabi, Assamese, Urdu, and code-mixed speech (Hindi-English, etc.)

### Examples

| Input | Output |
|-------|--------|
| `"Bachche sun nahi rahe hain"` | `"The children are not listening"` |
| `"இந்த பாடம் புரியவில்லை அவர்களுக்கு"` | `"They are not understanding this lesson"` |
| `"Addition ka carry samajh nahi aa raha inko"` | `"They are not understanding the carry concept in addition"` |

---

## 📚 RAG System for NCERT Books

Retrieval-Augmented Generation (RAG) system for semantic search and question-answering over NCERT textbooks.

### Quick Usage

```powershell
# Generate embeddings (first time only)
python embedding/generate_embeddings.py

# Query the books
python main.py "What is photosynthesis?" --db-path embedding/ncert_books.db

# Interactive mode
python embedding/query_books.py --interactive

# With filters
python main.py "Explain cells" --class "Class_7" --subject "Science"
```

---

## 🧪 Testing

```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Unix

# Backend tests
cd Server
pytest

# Frontend lint
cd Client_F\front_chanak
npm run lint
```

---

## 🚢 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment instructions.

### Quick Deploy

```powershell
# Build frontend
cd Client_F\front_chanak
npm run build

# Production server
python Server/Web_server/main.py
# Or use: uvicorn Server.Web_server.main:app --host 0.0.0.0 --port 3000
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **MongoDB connection error** | Ensure MongoDB is running: `mongod` |
| **ModuleNotFoundError** | Activate venv and run `pip install -r Server/requirements.txt` |
| **CORS error** | Check backend is on port 3000, verify frontend is on allowed origins |
| **Invalid API key** | Check `.env` file for correct keys (no quotes/spaces) |
| **Orchestrator not ready** | Check `GEMINI_API_KEY` is set correctly |

### Check API Keys

```powershell
python embedding/check_api_keys.py
```

---

## 📝 Available Scripts

| Script | Description |
|--------|-------------|
| `setup.bat` / `setup.sh` | One-command project setup |
| `run.bat` / `run.sh` | Start both frontend and backend |

### Manual Commands

**Backend:**
```powershell
python Server/Web_server/main.py     # Run server
cd Server && pytest                   # Run tests
python embedding/generate_embeddings.py  # Generate embeddings
python main.py "query"                # Query RAG
```

**Frontend:**
```powershell
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview build
npm run lint     # Lint code
```

---
  
## 📄 License

This project is provided for educational purposes. Please respect NCERT's terms of service and copyright policies when using downloaded materials.

---

<div align="center">

**Made with ❤️ for Indian Teachers**

[Report Bug](https://github.com/Kautilya346/Chanakya/issues) · [Request Feature](https://github.com/Kautilya346/Chanakya/issues)

</div>
