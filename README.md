# 🛤️ MargMitra — Street Sign Transliterator
> AICTE – Indian Knowledge Systems (IKS) Project

---

## 📁 Project Structure

```
margmitra/
│
├── frontend/
│   ├── index.html        ← Main app UI (your teammate's work)
│   ├── style.css         ← Styles (your teammate's work)
│   └── script.js         ← Frontend logic + API calls (updated)
│
├── backend/
│   ├── ocr/
│   │   └── main.py       ← OCR Service        → runs on port 8001
│   ├── translit/
│   │   └── main.py       ← Transliteration    → runs on port 8002
│   ├── main.py           ← YOUR Main API      → runs on port 8000
│   ├── database.py       ← YOUR Database layer
│   └── requirements.txt  ← All Python packages
│
└── README.md             ← This file
```

---

## 🚀 How to Run the Full Project

### Step 1 — Install Python dependencies (one time only)
Open a terminal in the `backend/` folder:
```bash
pip install -r requirements.txt
```

### Step 2 — Install Tesseract OCR (one time only)
**Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
During install, check "Hindi" and "English" language data.

**Linux/Mac:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-hin   # Linux
brew install tesseract                               # Mac
```

### Step 3 — Start all 3 backend services
Open **3 separate terminal windows**:

**Terminal 1 — OCR Service**
```bash
cd backend/ocr
uvicorn main:app --port 8001
```

**Terminal 2 — Transliteration Service**
```bash
cd backend/translit
uvicorn main:app --port 8002
```

**Terminal 3 — YOUR Main API**
```bash
cd backend
uvicorn main:app --port 8000 --reload
```

### Step 4 — Open the frontend
Simply open `frontend/index.html` in Chrome.
That's it — the full app is running!

---

## 🔌 API Endpoints (Your Service — Port 8000)

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | Health check |
| GET | `/health` | Check all 3 services are online |
| POST | `/scan` | **Main endpoint** — image → OCR → transliterate → save |
| GET | `/history` | All past scan results |
| GET | `/history/{id}` | One scan by ID |
| DELETE | `/history/{id}` | Delete a scan |
| GET | `/stats` | Total scans & languages used |

Interactive docs: **http://localhost:8000/docs**

---

## 👥 Team Contributions

| Member | Role | Files |
|--------|------|-------|
| Jashwin Sharma | Main API + Database | `backend/main.py`, `backend/database.py` |
| Atharva | Transliteration Service | `backend/translit/main.py` |
| Harshita Suchak | Frontend UI | `frontend/index.html`, `frontend/style.css` |
| Sneha | Frontend Logic | `frontend/script.js` |
| Keshav | OCR Service | `backend/ocr/main.py` |


---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| OCR | Tesseract 5 (open source, offline) |
| Transliteration | Google Input Tools API |
| Main API | FastAPI (Python) |
| Database | SQLite (local, no setup needed) |
| Communication | REST APIs over localhost |

---

## 📊 How the Pipeline Works

```
User takes photo
      ↓
Frontend (index.html)
      ↓  POST /scan (image + target_lang)
Main API — YOUR SERVICE (port 8000)
      ↓  POST /ocr
OCR Service (port 8001)  →  "Railway Station"
      ↓  POST /transliterate
Transliteration (port 8002)  →  "रेलवे स्टेशन"
      ↓  save_scan()
SQLite Database (margmitra.db)
      ↓  return JSON result
Frontend shows result + plays audio
```
