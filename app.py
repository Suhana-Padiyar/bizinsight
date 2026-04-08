from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
import json, os, io, traceback
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app      = Flask(__name__)
API_KEY  = os.environ.get("GROQ_API_KEY", "")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = "paste-your-groq-key-here"

# ── Error handler ──────────────────────────────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    return jsonify({"error": f"Server error: {str(e)}"}), 500

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sample_orders.csv")
def serve_sample():
    return send_from_directory(BASE_DIR, "sample_orders.csv", mimetype="text/csv")

@app.route("/health")
def health():
    key_ok = bool(API_KEY) and API_KEY != PLACEHOLDER
    return jsonify({
        "status"          : "ok",
        "api_key_loaded"  : key_ok,
        "sample_csv_found": os.path.exists(os.path.join(BASE_DIR, "sample_orders.csv"))
    })

# ── Main analyze endpoint ──────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # 1. Validate API key
        if not API_KEY or API_KEY == PLACEHOLDER:
            return jsonify({
                "error": "GROQ_API_KEY not configured. Open your .env file, "
                         "replace the placeholder with your real Groq key, then restart."
            }), 500

        # 2. Read uploaded CSV
        file = request.files.get("csv_file")
        if not file:
            return jsonify({"error": "No file received."}), 400

        try:
            content = file.read().decode("utf-8-sig")
            df = pd.read_csv(io.StringIO(content))
            if df.empty:
                return jsonify({"error": "CSV file is empty."}), 400
        except Exception as e:
            return jsonify({"error": f"Could not read CSV: {str(e)}"}), 400

        # 3. Prepare CSV preview for AI (headers + up to 40 rows)
        preview_rows = min(40, len(df))
        csv_preview  = df.head(preview_rows).to_csv(index=False)
        total_rows   = len(df)
        columns      = list(df.columns)

        # 4. Single AI call: understand the data AND give recommendations
        prompt = f"""You are an expert business analyst AI. A restaurant/food business owner has uploaded a CSV file.

CSV details:
- Total rows: {total_rows}
- Columns: {columns}
- First {preview_rows} rows:
{csv_preview}

Your job:
1. Understand what this CSV contains, even if column names are unusual or in another language.
2. Calculate or estimate these metrics from the data (use null if not possible):
   - total_revenue (numeric)
   - total_orders (integer)
   - top_items: dict of up to 5 item/product names → revenue or count (whichever makes sense)
   - category_breakdown: dict of category → revenue or count (skip if no category column)
   - peak_hours: dict of "HH:00" → count of orders (skip if no time column)
   - customer_split: dict of customer type → percentage (skip if no such column)
   - daily_revenue: dict of "YYYY-MM-DD" → revenue (skip if no date column, keep to max 10 entries)
3. Write exactly 5 specific, actionable business recommendations using real numbers from the data.
4. Write a one-line executive summary.

Respond ONLY with a single valid JSON object, no markdown, no explanation:
{{
  "data_description": "brief description of what this CSV contains",
  "summary": {{
    "total_revenue": <number or null>,
    "total_orders": <integer>,
    "top_items": {{}},
    "category_breakdown": {{}},
    "peak_hours": {{}},
    "customer_split": {{}},
    "daily_revenue": {{}}
  }},
  "ai_insights": {{
    "one_line_summary": "...",
    "recommendations": [
      {{"title": "...", "insight": "...", "action": "...", "impact": "..."}}
    ]
  }}
}}"""

        try:
            client  = Groq(api_key=API_KEY)
            message = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.choices[0].message.content.strip()

            # Robustly extract JSON — handles preamble/postamble/markdown fences
            start = raw.find("{")
            end   = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                raw = raw[start:end+1]

            result = json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"[WARN] AI JSON parse failed: {e}\nRaw:\n{raw[:800]}")
            return jsonify({"error": "AI returned an unparseable response. Please try again."}), 500
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"AI error: {str(e)}"}), 500

        # 5. Ensure expected keys exist with safe defaults
        summary = result.get("summary", {})
        summary.setdefault("total_revenue",      0)
        summary.setdefault("total_orders",        total_rows)
        summary.setdefault("top_items",           {})
        summary.setdefault("category_breakdown",  {})
        summary.setdefault("peak_hours",          {})
        summary.setdefault("customer_split",      {})
        summary.setdefault("daily_revenue",       {})

        ai_insights = result.get("ai_insights", {})
        ai_insights.setdefault("one_line_summary", "")
        ai_insights.setdefault("recommendations",  [])

        return jsonify({
            "summary"         : summary,
            "ai_insights"     : ai_insights,
            "data_description": result.get("data_description", "")
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Unexpected server error: {str(e)}"}), 500


if __name__ == "__main__":
    key_ok = bool(API_KEY) and API_KEY != PLACEHOLDER
    print(f"\n  API key loaded : {'YES' if key_ok else 'NO — open .env and replace the placeholder'}")
    print(f"  Sample CSV     : {'FOUND' if os.path.exists(os.path.join(BASE_DIR, 'sample_orders.csv')) else 'MISSING'}")
    print(f"  Open browser   : http://localhost:5000\n")
    if not key_ok:
        print("  ⚠  Set GROQ_API_KEY in your .env file before analyzing data.\n")
    app.run(host="0.0.0.0", port=5000, debug=False)