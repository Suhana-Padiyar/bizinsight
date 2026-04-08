# BizInsight AI
### AI-Powered Business Intelligence for Small Restaurants

---

## What it does
Upload a CSV of your restaurant orders → get AI-generated business recommendations in seconds.
No data analyst. No complicated tools. Just answers.

---

## Setup (one time only)

### Step 1 — Make sure Python is installed
Open your terminal / command prompt and type:
```
python --version
```
You should see Python 3.8 or higher. If not, download from python.org.

### Step 2 — Navigate to this folder
```
cd path/to/bizinsight
```

### Step 3 — Install dependencies
```
pip install -r requirements.txt
```

### Step 4 — Run the app
```
python app.py
```
You will see:
```
 * Running on http://127.0.0.1:5000
```

### Step 5 — Open in browser
Go to: http://localhost:5000

---

## How to use

1. Enter your Anthropic API key (get one from console.anthropic.com)
2. Click **"Load Sample Data"** to test with the included sample CSV
   — OR upload your own orders CSV
3. Click **"Analyze with AI"**
4. View your charts + 5 AI business recommendations

---

## Your CSV format (if using own data)
Required columns:
- order_id
- item_name
- category
- quantity
- price
- order_date (YYYY-MM-DD)
- order_time (HH:MM)
- customer_type (new / returning)

See sample_orders.csv for reference.

---

## Project by
Suhana Padiyar — built as an AI-powered extension of a live restaurant client project.
