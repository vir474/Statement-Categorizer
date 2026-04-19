# Statement Categorizer

Bank and credit card statement analyzer with automatic categorization and monthly budget summaries.

## Features
- Upload PDF, CSV, OFX, and QFX statements
- Automatic transaction categorization (rule engine + optional Ollama/Claude AI)
- Edit categories inline, define custom categories and rules
- Monthly budget summary with charts
- Fully offline-first (no internet required unless using Claude API)
- Windows, Mac, and Linux compatible

---

## Quick Start (Local — No Docker)

### 1. Backend

**Requirements:** Python 3.11+

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Mac/Linux)
source .venv/bin/activate
# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install fastapi uvicorn sqlmodel alembic aiosqlite asyncpg greenlet \
    pydantic-settings python-dotenv python-multipart aiofiles \
    pdfplumber pandas ofxparse anthropic httpx boto3 python-dateutil

# Copy env file (Mac/Linux)
cp .env.example .env
# Copy env file (Windows)
copy .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000
API docs (interactive) at http://localhost:8000/docs

### 2. Frontend

**Requirements:** Node.js 18+

```bash
cd frontend
npm install

# Copy env file (Mac/Linux)
cp .env.example .env
# Copy env file (Windows)
copy .env.example .env

npm run dev
```

Frontend runs at http://localhost:5173

---

## Starting and Stopping

### Starting

Open two terminal windows. Run one command in each:

**Terminal 1 — Backend:**
```bash
cd backend

# Mac/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

### Stopping

In each terminal press `Ctrl + C` to stop the server.

### Restarting after a crash

If the backend stops responding but the process is still running (port 8000 stuck):

**Mac/Linux:**
```bash
pkill -f "uvicorn app.main"
# then start again normally
```

**Windows PowerShell:**
```powershell
# Find and kill the Python process holding port 8000
netstat -ano | findstr :8000
# Note the PID in the last column, then:
taskkill /PID <pid> /F
# then start again normally
```

---

## Offline LLM Categorization (Optional)

For AI-powered categorization without internet:

1. Install [Ollama](https://ollama.com) — has a Windows `.exe` installer
2. Pull a model: `ollama pull llama3.2`
3. Ensure `backend/.env` has `LLM_BACKEND=ollama`

Ollama runs as a background service automatically after install. If you don't want any LLM, set `LLM_BACKEND=none` to use the rule engine only.

---

## Network Access (Other Devices on Same Network)

To access from other devices on the same Wi-Fi (phone, tablet, another PC):

1. Find your machine's local IP
   - Windows: run `ipconfig` → look for IPv4 Address
   - Mac: run `ipconfig getifaddr en0`
2. In `backend/.env`: set `CORS_ORIGINS=http://192.168.x.x:5173`
3. In `frontend/.env`: set `VITE_API_URL=http://192.168.x.x:8000`
4. Windows only: allow ports 8000 and 5173 through Windows Firewall
5. Restart both servers
6. Other devices open `http://192.168.x.x:5173`

---

## Server Deployment (Docker)

```bash
# Edit the env file — set POSTGRES_PASSWORD and VITE_API_URL at minimum
cp .env.example .env

docker compose -f docker-compose.prod.yml up -d

# Stop
docker compose -f docker-compose.prod.yml down

# Stop and wipe all data (irreversible)
docker compose -f docker-compose.prod.yml down -v
```

Runs on port 80. Switches to PostgreSQL automatically via `DATABASE_URL`.

---

## Supported Statement Formats

| Format | How to Export |
|--------|--------------|
| **CSV** | Most banks: Download Transactions → CSV |
| **OFX / QFX** | Chase, Bank of America, Wells Fargo: Download → OFX |
| **PDF** | Any bank statement PDF |

For the most reliable results use OFX/QFX when your bank offers it. PDF parsing is best-effort and may miss transactions on unusual layouts.

---

## Troubleshooting

### Page keeps loading / spinner never stops

The frontend lost connection to the backend.

1. Check the backend terminal — look for error output
2. Confirm the backend is actually running: open http://localhost:8000/health in your browser — it should return `{"status":"ok"}`
3. If the health check times out, the port is stuck. Follow the **Restarting after a crash** steps above
4. After restarting the backend, refresh the browser

### Transactions don't appear after uploading a statement

The statement is parsed in the background after upload. The status badge on the Statements page shows the progress:

- **Pending** → queued, not started yet
- **Parsing** → actively processing
- **Imported** → done, transactions are available
- **Error** → parsing failed (error message shown below the filename)

If the status stays on **Pending** for more than a few seconds, the background task may have failed silently. Restart the backend and re-upload the file.

If status shows **Imported** but the Transactions page is empty, try:
1. Go to Transactions and clear any active filters (month, search, uncategorized toggle)
2. Hard-refresh the browser (`Cmd+Shift+R` on Mac, `Ctrl+Shift+R` on Windows)

### PDF transactions not found or wrong dates

PDF parsing is bank-specific. The parser handles common formats (Chase, Amex, etc.) but some banks use unusual layouts.

- Try exporting as CSV or OFX from your bank's website instead — these are more reliable
- If dates appear with the wrong year, check that the statement's "Opening/Closing Date" line is on the first page of the PDF

### "Address already in use" error on startup

Another process is already using port 8000. Either:
- Stop the existing backend process (see **Restarting after a crash** above)
- Or start on a different port: `uvicorn app.main:app --reload --port 8001` and update `frontend/.env` to match: `VITE_API_URL=http://localhost:8001`

### Data disappears after restarting

On startup the backend prints the database path it is using, e.g.:

```
INFO:     Database: sqlite:////Users/you/statement_categorizer/backend/data/app.db
```

If this path changes between restarts, you are connecting to a different database file. This happens when uvicorn is started from different directories. Always start the backend from inside the `backend/` folder:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The path fix is already in the code, but verifying this log line is the fastest way to confirm you are looking at the right file.

### Categories not saving / API errors

Check the backend terminal for error output. Most API errors are printed there with a full traceback.

You can also view all API endpoints and test them interactively at http://localhost:8000/docs.

### Windows: `Activate.ps1 cannot be loaded` error

PowerShell execution policy is blocking scripts. Run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then activate the venv again.

### Windows: `python` not found

Use `python3` instead of `python`, or install Python from https://python.org and ensure "Add to PATH" is checked during install.

---

## Project Structure

```
backend/app/
  core/          # Config, database engine
  api/routes/    # FastAPI endpoints
  models/        # SQLModel DB models
  schemas/       # Pydantic request/response shapes
  crud/          # Database operations
  services/
    parser/      # PDF, CSV, OFX parsers
    categorizer/ # Rule engine + Ollama + Claude
    storage/     # Local filesystem + S3

frontend/src/
  features/      # statements | transactions | categories | budgets
  components/    # Shared UI components
  lib/           # API client, utilities
  types/         # TypeScript type definitions
```
