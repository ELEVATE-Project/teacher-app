# Chanakya — Teacher Assistant Platform

Chanakya is a real-time, AI-powered classroom decision-support system for primary school teachers. It combines multilingual NLP, NCERT textbook RAG retrieval, speech integration, teaching feedback, and classroom management.

## 📁 Repository Structure

* **[Chanakya-Backend/Server](./Chanakya-Backend/Server/)**: Python FastAPI web server.
* **[Frontend/front_chanak](./Frontend/front_chanak/)**: React + Vite client dashboard.
* **[RagFlow_Backend/ai-personalization](./RagFlow_Backend/ai-personalization/)**: Python service for AI personalization and RAGFlow integration.

---

## 🔑 Environment Configuration

Chanakya utilizes a single, unified environment configuration file at the workspace root directory:

* **File Location:** `./.env` (at the root of this repository)
* **Setup:** Copy [`.env.example`](./.env.example) to `.env` and fill in the required variables (OpenRouter keys, Supabase URLs, Sarvam AI voice credentials, etc.).

All components (FastAPI backend, React frontend client, and AI personalization service) resolve and load configuration variables dynamically from this single root environment file.
