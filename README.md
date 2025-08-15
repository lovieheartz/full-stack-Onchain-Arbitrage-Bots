# Full Stack On-Chain Arbitrage Dashboard

A production-ready full-stack application showcasing 7 Python-based on-chain arbitrage strategies with 3D visualizations and real-time data management.

## 🚀 Live Demo
- **Frontend**: [Deploy on Vercel](https://vercel.com)
- **Backend API**: [Deploy on Render](https://render.com)

## 🏗️ Architecture

```
/
├── frontend/          # Next.js + TailwindCSS + Three.js
├── backend/           # FastAPI + Python strategies
├── .github/           # CI/CD workflows
└── README.md
```

## ⚡ Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Git

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/full-stack-onchain-arbitrage-dashboard.git
cd full-stack-onchain-arbitrage-dashboard
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with backend URL
npm run dev
```

### 4. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📦 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy

#### Backend (Render)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

#### Frontend (Vercel)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/full-stack-onchain-arbitrage-dashboard&project-name=arbitrage-dashboard&repository-name=arbitrage-dashboard)

## 🔧 Environment Variables

### Backend (.env)
```
ETHEREUM_RPC=your_ethereum_rpc
ARBITRUM_RPC=your_arbitrum_rpc
POLYGON_RPC=your_polygon_rpc
GOOGLE_CREDENTIALS_FILE=credentials.json
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

## 📊 Features

- **3D Blockchain Visualization** - Interactive Three.js nodes
- **7 Arbitrage Strategies** - Cross-chain, triangular, sandwich, etc.
- **Real-time Data** - Google Sheets integration
- **Dark/Light Mode** - Persistent theme switching
- **Responsive Design** - Mobile-first approach
- **Zero Database** - File-based strategy management

## 🛠️ Tech Stack

**Frontend:**
- Next.js 14
- React 18
- TailwindCSS
- Framer Motion
- Three.js
- Recharts

**Backend:**
- FastAPI
- Python 3.9+
- Web3.py
- Google Sheets API
- Pydantic

## 📁 Project Structure

```
frontend/
├── pages/
│   ├── index.js           # Home with 3D visualization
│   ├── strategies/        # Strategy pages
│   ├── spreadsheet.js     # Data viewer
│   └── settings.js        # Configuration
├── components/
│   ├── Layout.js          # Main layout
│   ├── ThreeScene.js      # 3D blockchain
│   └── StrategyCard.js    # Strategy components
└── lib/
    └── api.js             # API client

backend/
├── strategies/            # 7 Python strategy files
├── routes/               # FastAPI endpoints
├── services/             # Business logic
├── models/               # Pydantic models
└── main.py               # FastAPI app
```

## 🔄 API Endpoints

- `GET /strategies` - List all strategies
- `GET /strategies/{id}` - Strategy details
- `POST /strategies/{id}/run` - Execute strategy
- `GET /spreadsheet/view` - View data
- `GET /spreadsheet/download/{type}` - Export data

## 🚨 Production Notes

- CORS configured for production domains
- Environment-specific builds
- Docker containers included
- Health checks implemented
- Error boundaries in React
- API rate limiting ready

## 📈 Monitoring

- Strategy execution logs
- Performance metrics
- Error tracking
- Real-time status updates

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

---

**⚠️ Disclaimer**: This is for educational purposes. Trading cryptocurrencies involves risk.