<table>
  <tr>
    <td width="200px">
      <img src="../../Chanakya-Backend/Server/figure/chanak_main.png" alt="Chanakya Logo" width="200px" />
    </td>
    <td>
      <h1>Chanakya - Frontend Client</h1>
      <h3>Responsive React & Vite web interface for the Chanakya Teacher Assistant ecosystem</h3>
      <p>
        <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-19.0-61DAFB.svg?style=flat-square&logo=react" alt="React" /></a>
        <a href="https://vite.dev/"><img src="https://img.shields.io/badge/Vite-7.2-646CFF.svg?style=flat-square&logo=vite" alt="Vite" /></a>
        <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg?style=flat-square&logo=tailwind-css" alt="Tailwind CSS" /></a>
        <a href="https://lucide.dev/"><img src="https://img.shields.io/badge/Lucide_React-0.562-F43F5E.svg?style=flat-square&logo=lucide" alt="Lucide" /></a>
      </p>
      <p>
        The frontend client of Chanakya provides primary school teachers with a real-time, interactive, and beautifully responsive dashboard. It empowers them with lesson plan creators, active listening teaching coaches, crisis interventions, and personalized student query helpers.
      </p>
    </td>
  </tr>
</table>

---

## 🎨 Key Features & Interfaces

The frontend is divided into several modules corresponding to the teacher's workflow:

### 1. 📊 Teacher Dashboard
* **Route:** `/dashboard`
* **Features:**
  * **Classroom Selection & Management:** Easy selection and overview of classes.
  * **Cold Start Setup (`/dashboard/setup`):** Simple onboarding flow to establish new classes and student profiles.
  * **Student Profiles (`/dashboard/student/:id`):** Shows detailed analytics, attendance, performance trends, and learning recommendations for each child.
  * **Class Session Summary (`/dashboard/summary/:id`):** Reviews classroom interactions, engagement indexes, and topics covered.

### 2. 🎙️ Active Listening Mode (ALM)
* **Route:** `/alm`
* **Features:**
  * **Real-Time Coaching:** Records microphone audio directly in the classroom.
  * **Multilingual Transcription:** Translates and transcribes regional Indian languages in real-time utilizing **Sarvam AI APIs**.
  * **Voice Feedback:** Text-to-speech feedback using custom regional voices (Bulbul v2).
  * **Live Analytics:** Dynamic visual representations of speech metrics, sentiment analysis, and pacing.

### 3. 🚨 Crisis Handling Mode
* **Route:** `/discuss` & Dynamic overlays
* **Features:**
  * **Zero-Resource Interventions:** Access to immediate suggestions for classroom disruptions (e.g., noise, restlessness, low participation) tailored for Indian classrooms.
  * **Interactive Guidance:** Steps and action strategies that do not require any classroom materials.

### 4. 📝 Module Creator Mode
* **Route:** `/module`
* **Features:**
  * **NCERT-Based Lesson Builder:** Input chapters to dynamically generate structured 8-slide lessons.
  * **Assessment Generator:** Automatically generates assessment slides (MCQs, short answer, and long answer questions) based on textbook context.

### 5. 💬 Discuss Forum
* **Route:** `/discuss`
* **Features:**
  * **Teacher Community:** Threaded discussion boards where educators can share resources, post questions, and offer advice.
  * **Rich Post Creator (`/discuss/new`):** Clean and intuitive post creator supporting custom markdown or text inputs.

---

## 🛠️ Tech Stack & Dependencies

* **Framework:** React 19 (Single Page Application)
* **Build Tool:** Vite 7 (using Fast Refresh and optimized asset bundling)
* **Routing:** React Router v7 (`react-router-dom`)
* **Styling:** Vanilla CSS & Tailwind CSS 3 (harmonious colors, dark modes, premium typography)
* **Icons:** Lucide React & React Lineicons
* **Animations:** Framer Motion (`motion` package for fluid micro-animations)
* **API Client:** Axios for backend network communications
* **Notifications:** React Hot Toast & React Toastify

---

## ⚡ Setup & Installation

### Option 1: One-Command Setup (Recommended)

From the `Frontend/front_chanak` directory, run the setup helper script matching your operating system:

#### Windows (CMD / PowerShell):
```cmd
setup.bat
```

#### macOS / Linux / Git Bash:
```bash
chmod +x setup.sh
./setup.sh
```

**What the scripts do:**
1. Verifies that **Node.js** (v18+) and **npm** are installed.
2. Checks for a `.env` file at the workspace root (`../../.env`). If missing, copies `.env.example` or creates a default one.
3. Installs all packages and devDependencies via `npm install`.

---

### Option 2: Manual Setup

If you prefer to run setup steps manually:

1. **Verify Prerequisites:**
   * Node.js (v18 or higher)
   * npm (v9 or higher)

2. **Configure Environment Variables:**
   * Ensure there is a `.env` file at the workspace root directory (two directories up from `Frontend/front_chanak/`).
   * The file should contain:
     ```env
     # Backend Service URL
     VITE_API_URL=http://localhost:3000
     
     # AI Service URL
     VITE_AI_URL=http://localhost:5001
     
     # Sarvam AI API Key (Required for live transcription/TTS)
     VITE_SARVAM_API_KEY=your_sarvam_api_key_here
     ```

3. **Install Dependencies:**
   ```bash
   npm install
   ```

---

## 🚀 Running the Frontend

Run the following commands within the `Frontend/front_chanak` directory:

| Command | Description |
| :--- | :--- |
| `npm run dev` | Starts the local development server at `http://localhost:5173`. |
| `npm run build` | Builds the optimized production bundle in the `dist/` directory. |
| `npm run preview` | Runs a local web server to preview the production build locally. |
| `npm run lint` | Runs ESLint to inspect and analyze codebase quality. |

---

## 🔗 Architecture & API Proxies

To bypass Cross-Origin Resource Sharing (CORS) issues during development, the frontend configuration in [vite.config.js](./vite.config.js) utilizes local proxy rules:

* `/api` requests are automatically proxied to the FastAPI server running on `http://localhost:3000`.
* `/api/dashboard` queries are mapped and routed to the corresponding dashboard API server.
* `/health` requests are proxied directly to the backend health endpoint.

This is loaded from the environment variables configured at the workspace root, as resolved by `envDir: path.resolve(__dirname, '../../')` in Vite's configuration.

---

## 📁 Directory Structure

```
Frontend/front_chanak/
├── public/                 # Static assets (images, logos, SVGs)
├── src/
│   ├── api/                # Base API clients and interceptors
│   ├── components/         # Reusable UI components (Headers, Footers, Cards)
│   │   └── dashboard/      # Specific layout & components for the dashboard
│   ├── config/             # App configs (API routes, endpoints)
│   ├── context/            # Global state (Auth, Context providers)
│   ├── pages/              # Main view screens (Landing, ActiveListeningMode, etc.)
│   │   └── dashboard/      # Sub-screens inside the dashboard panel
│   ├── services/           # Services interacting with outer backends
│   ├── styles/             # Modular and custom CSS files
│   ├── utils/              # API utilities (Sarvam voice, classroom math algorithms)
│   ├── App.jsx             # Main app routes and component assembly
│   ├── main.jsx            # DOM mounting entrypoint
│   └── index.css           # Global Tailwind and styling entrypoint
├── eslint.config.js        # Linter rules
├── package.json            # Scripts, dependencies, and configuration
├── tailwind.config.js      # Tailwind theme extensions
└── vite.config.js          # Vite configuration & dev proxy definitions
```

---
<div align="center">
  <sub>Made with ❤️ for Indian Teachers</sub>
</div>
