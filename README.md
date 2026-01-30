# 🚀 AI-Powered SQL Optimizer & Generator

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Tech Stack](https://img.shields.io/badge/Stack-React_|_FastAPI_|_Gemini_Pro-blueviolet)
![License](https://img.shields.io/badge/License-MIT-blue)

**A hybrid, intelligent SQL engineering tool that combines static analysis with the power of Google's Gemini Pro LLM.**

This application serves as a comprehensive "SQL Companion" for developers and data analysts, offering real-time query optimization suggestions and natural language to SQL generation.

## 🌟 Key Features

### 🧠 Hybrid AI Engine
The core of this project is its **resilient, fail-safe architecture**:
*   **Real AI Mode:** When a valid `GEMINI_API_KEY` is present, the system leverages **Google Gemini Pro** to perform deep, context-aware analysis of arbitrary queries and schemas.
*   **Demo Mode (Fail-Safe):** If the API key is missing or quota is exceeded, the system seamlessly degrades to a **Simulated Heuristic Engine**. This ensures the application *never* breaks and is always available for demonstration purposes.

### ⚡ Performance Optimizer
*   **Execution Plan Analysis:** Simulates/Retrieves `EXPLAIN ANALYZE` metrics (Cost, Rows, Node Types).
*   **Smart Suggestions:** Identifies common anti-patterns (e.g., `SELECT *`, Unbounded queries, Leading wildcards).
*   **Auto-Fix:** Generates optimized SQL rewrites instantly.

### 🗣️ Text-to-SQL Generator
*   **Natural Language Processing:** Translates plain English questions (e.g., *"Find top users by sales"*) into syntactically correct SQL.
*   **Schema-Aware:** Understands custom table definitions provided on the fly.

---

## 🛠️ Tech Stack

*   **Frontend:** React, TypeScript, Vite, Tailwind CSS, Framer Motion (for smooth UI/UX).
*   **Backend:** Python, FastAPI, Uvicorn, Google Generative AI (`google-generativeai`).
*   **Deployment:** designed for Render (Backend) and Netlify (Frontend).

---

## 🚀 Getting Started

### Prerequisites
*   Node.js & npm
*   Python 3.10+
*   Google Gemini API Key (Optional, for Real AI features)

### Local Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/sriiverse/AI-SQL-Optimizer.git
    cd AI-SQL-Optimizer
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    pip install -r requirements.txt
    
    # Optional: Enable Real AI
    # Create a .env file and add: GEMINI_API_KEY=your_key_here
    
    uvicorn main:app --reload
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## ☁️ Deployment

### Backend (Render)
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
*   **Environment Variables:** `GEMINI_API_KEY` (Required for Real AI)

### Frontend (Netlify/Vercel)
*   **Build Command:** `npm run build`
*   **Output Directory:** `dist`
*   **Environment Variables:** `VITE_API_BASE_URL` (Point to your Render Backend URL)

---

## 📸 Screenshots
*(Add your screenshots here)*
