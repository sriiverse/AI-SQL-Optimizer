# 🚀 AI-Powered SQL Query Optimizer & Generator

![System Architecture](./assets/system_architecture.png)

[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)]()
[![Stack](https://img.shields.io/badge/Stack-React_|_FastAPI_|_Gemini-blueviolet?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)]()

A professional-grade database engineering tool that leverages **Google Gemini** and **Groq Llama-3** to analyze execution plans and generate highly optimized, enterprise-level queries for **PostgreSQL**, **MySQL**, **SQLite**, and **MongoDB**.

---

## ✨ Enterprise Features

### 🛡️ Multi-Provider API Resilience
*   **Primary Engine:** Google Gemini (`gemini-flash-latest`) for rapid static analysis and generation.
*   **Auto-Failover:** Automatically cascades to Groq's flagship `llama-3.3-70b-versatile` if Gemini rate limits are hit, ensuring 100% uptime without user intervention.
*   **Deterministic Fallback:** Degrades seamlessly to a simulated heuristic engine if no API keys are available.

### 🧠 Elite Analytics Guardrails
The system isn't a basic text-to-SQL wrapper. It enforces **34+ strict architectural rules** during generation:
*   **Advanced SQL:** Forces strict CTE scoping, `GENERATE_SERIES()` for sparse time-series forecasting, and mathematically flawless rolling averages.
*   **MongoDB Mastery:** Safely handles recursive `$graphLookup` trees with `maxDepth` limits, `$setWindowFields` time-decay scoring, and faceted analytics without crashing.

### 🔍 Intelligent Optimization
*   **Static Analysis:** Identify full table scans, missing indexes, and `SELECT *` anti-patterns.
*   **Dialect Aware:** Generates optimization advice specific to your database engine.

### ✍️ Schema-Aware Generator
*   **Natural Language to Pipeline:** Translates "Find viral contagion risk" into 250+ line MongoDB aggregation pipelines or 10+ chained Postges CTEs.
*   **Context Injection:** Injects user table definitions into the AI context to prevent hallucinations and invent secure joins.

---

## 🚀 Quick Start

### Prerequisites
*   Node.js (v18+)
*   Python (v3.9+)
*   Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### 1. Clone & Install
```bash
git clone https://github.com/sriiverse/AI-SQL-Optimizer.git
cd AI-SQL-Optimizer
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Create .env file (See .env.example)
echo "GEMINI_API_KEY=your_key_here" > .env
python main.py
```
*Server runs at `http://localhost:8000`*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*App runs at `http://localhost:5173`*

---

## 💡 Example Workflows

### Scenario 1: Optimizing a Slow Query
**Input:**
```sql
SELECT * FROM orders WHERE DATE(created_at) = '2023-01-01'
```
**AI Analysis:**
> *"Using a function like `DATE()` on a column prevents index usage (SARGable violation). This causes a Full Table Scan."*

**Optimized Output (PostgreSQL):**
```sql
SELECT * FROM orders 
WHERE created_at >= '2023-01-01 00:00:00' 
  AND created_at < '2023-01-02 00:00:00';
```

### Scenario 2: Generating Reports
**Question:** *"Show me top 5 customers by speed of payment"*
**Schema Context:** `payments (amount, date, customer_id)`, `customers (id, name)`
**AI Output:**
```sql
SELECT c.name, AVG(p.date - o.order_date) as avg_payment_speed
FROM customers c
JOIN payments p ON c.id = p.customer_id
GROUP BY c.id
ORDER BY avg_payment_speed ASC
LIMIT 5;
```

---

## 🔒 Privacy & Data Safety

This application sends data to **Google's Generative AI API**.
*   **What is sent:** The SQL Query, Table Schema, and Natural Language Question you provide.
*   **What is NOT sent:** Database credentials, connection strings, or actual row data (unless you paste row data into the schema box).
*   **Recommendation:** Use randomized/anonymized table names (e.g., `table_a`) if your schema contains highly sensitive trade secrets.

---

## 🏗️ System Architecture
The application follows a **Hybrid Cloud Architecture**:
*   **Frontend:** React (Vite) + Tailwind CSS + Framer Motion. Hosted on **Netlify**.
*   **Backend:** FastAPI (Python) running on **Render**.
*   **AI Engine:** **Google Gemini Flash**.

---

## 🛠️ Deployment
## 🛠️ Tech Stack

*   **Frontend:** React, TypeScript, Vite, Tailwind CSS, Framer Motion (for smooth UI/UX).
*   **Backend:** Python, FastAPI, Uvicorn, Google Generative AI (`google-generativeai`), Groq (`groq`).
*   **Deployment:** Designed for Render (Backend) and Netlify (Frontend).

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
