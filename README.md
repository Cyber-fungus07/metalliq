# 🌍 Global Trade of Valuable Metals

Interactive Streamlit analytics dashboard tracking global trade flows, bilateral networks, price volatility, and supply-chain dependencies for precious, critical, and battery metals (Gold, Silver, Platinum, Palladium, Copper, Lithium, Cobalt, and Rare Earth Elements).

## 🛠️ Tech Stack

- **Framework:** [Streamlit](https://streamlit.io/)
- **Data & Computation:** Python, Pandas, NumPy, PyArrow
- **Visualization:** Plotly, PyDeck, PyVis, NetworkX
- **Data Standards:** PyCountry, GeoJSON

---

## 📦 How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Set Up a Virtual Environment
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Fetch or Preprocess Data
The repository includes preprocessed datasets in `data/processed/`. If you want to re-download or regenerate data:

```bash
# Generate synthetic dataset offline (no API key needed)
python scripts/download_data.py --synthetic

# Run ETL pipeline to produce Parquet files
python scripts/preprocess.py
```

### 5. Launch the Dashboard
```bash
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`.
