# Deployment Guide

## Prerequisites
- Node.js 18+
- Python 3.9+
- Google Sheets API credentials

## Environment Setup

### Backend (.env)
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

### Frontend (.env.local)
```bash
cp frontend/.env.local.example frontend/.env.local
# Edit frontend/.env.local with your values
```

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

### Backend Options

#### 1. Render
1. Connect GitHub repo
2. Select `backend` folder
3. Environment: Python
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### 2. Railway
```bash
cd backend
railway login
railway init
railway up
```

### Frontend Options

#### 1. Vercel (Recommended)
1. Connect GitHub repo
2. Root directory: `frontend`
3. Build: `npm run build`
4. Auto-deploy on push

#### 2. Netlify
1. Connect GitHub repo
2. Build directory: `frontend`
3. Build command: `npm run build`
4. Publish directory: `.next`

## Environment Variables

### Required for Backend
- `ETHEREUM_RPC`: Ethereum RPC endpoint
- `ARBITRUM_RPC`: Arbitrum RPC endpoint  
- `POLYGON_RPC`: Polygon RPC endpoint
- `GOOGLE_CREDENTIALS_FILE`: Path to Google credentials

### Required for Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Google Sheets Setup
1. Create Google Cloud Project
2. Enable Sheets API
3. Create Service Account
4. Download credentials.json
5. Share sheets with service account email

## Health Checks
- Backend: `/api/health`
- Frontend: Automatic Next.js health check