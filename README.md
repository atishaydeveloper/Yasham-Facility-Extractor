# ♻️ Recycling Facility Extractor using Google Gemini

This project uses Google's Gemini 2.5 Flash LLM and Python to automate the extraction of structured recycling center data from semi-structured websites such as Earth911. It scrapes relevant web pages, filters out useful links, and classifies facilities with detailed material categorization.

---

## 🚀 Features

- Scrapes any provided URL to extract page content and links.
- Filters relevant recycling center links using prompt-engineered classification.
- Extracts structured information including:
  - Business name
  - Last update date
  - Street address
  - Accepted materials and categories
- Uses OpenAI-compatible Google Gemini (`gemini-2.5-flash`) for natural language understanding.

---

## 🧠 Prompting Strategy

### 🧭 Classification of Materials & Facilities
- **System Prompts** define role and context (e.g., extract only recycling-related links or structured facility info).
- **User Prompts** guide the LLM to:
  - Filter out irrelevant links (e.g., nav menus, legal pages).
  - Convert relative URLs to absolute ones.
  - Structure facility details using fixed schemas and predefined material categories.

---

## 🏗️ Pipeline Architecture

### Tech Stack:
- **BeautifulSoup**: Web scraping and DOM cleaning.
- **Requests**: HTTP fetching.
- **LangChain not used** but a custom **prompt-chaining** approach is implemented via `system + user` design.
- **Gemini 2.5 Flash API**: Chat completions for classification and extraction.

### Processing Flow:
1. **Web Scraping** using `Website` class.
2. **Link Filtering**:
   - Uses a structured JSON-based prompt for Gemini to filter valid recycling center URLs.
3. **Content Aggregation**:
   - Scrapes selected links and compiles content for next stage.
4. **Facility Extraction**:
   - Gemini processes combined content to return structured JSON output.

---

## ⚠️ Edge Case Handling

- **Nested HTML / Scripts**: Removed using `decompose()` for `<script>`, `<style>`, `<img>`, and `<input>` tags.
- **Map-only or vague listings**: Links leading to maps, logins, or navigational pages are ignored via LLM prompting.
- **Inconsistent Labeling**: Model is prompted to infer specific accepted materials when only general terms like "electronics" are mentioned.
- **Relative URLs**: Instructions in prompts ask the LLM to convert relative URLs to absolute format using the page's domain.

---

## 💡 Proposed Plan (If Incomplete)

If full deployment isn't completed, the plan includes:

### 📦 Libraries:
- **LangChain**: For managing prompt templates and agents (optional).
- **FastAPI/Flask**: For converting into a deployable API service.
- **Streamlit**: For simple user-facing interaction interface.

### ✅ Strengths:
- Model-agnostic prompting works with any OpenAI-compatible LLM.
- Scalable to different categories (e.g., e-waste, batteries, etc.).
- High-level control over data structure and filtering.

### ⚠️ Limitations:
- Web scraping depends on static HTML — dynamic content (e.g., React/JS-rendered pages) is not supported.
- LLM output quality may degrade for noisy or non-standard sites.
- Latency from multiple API calls per URL.

---

## ▶️ Example

```bash
python script.py

[
  {
    "business_name": "Green Earth Recyclers",
    "last_update_date": "2023-11-04",
    "street_address": "123 5th Ave, New York, NY 10001",
    "materials_category": ["Electronics", "Batteries"],
    "materials_accepted": ["Computers, Laptops, Tablets", "Lithium-ion Batteries"]
  }
]
```

---

## Author
[Atishay Jain](https://github.com/atishaydeveloper)

