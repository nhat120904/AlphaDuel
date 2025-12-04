# 🐂 AlphaDuel 🐻

**The On-Chain AI Debate Arena with "Skin in the Game"**

AlphaDuel is a multi-agent analytical platform that gamifies cryptocurrency market analysis. It deploys competing AI agents—a "Bull" and a "Bear"—to debate market trends in real-time, with predictions recorded on the Hedera blockchain.

![AlphaDuel Demo](docs/demo.gif)

## ✨ Features

- **Multi-Agent Debate**: Bull and Bear AI agents argue opposing market views
- **Referee Agent**: Impartial judge evaluates arguments and determines winner
- **Hedera Integration** (via [Hiero SDK](https://github.com/hiero-ledger/hiero-sdk-python)): 
  - HCS (Hedera Consensus Service) for immutable prediction logs
  - HBAR transfers for "skin in the game" wagers
- **Real-time Streaming**: Watch the debate unfold live
- **Beautiful UI**: Modern, animated interface with distinct agent personalities

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                          │
│              (Vercel AI SDK + React + Tailwind)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ SSE Streaming
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LangGraph Workflow                     │   │
│  │                                                           │   │
│  │    ┌──────────┐    ┌──────────┐    ┌──────────┐        │   │
│  │    │   Bull   │◄──►│   Bear   │◄──►│ Referee  │        │   │
│  │    │  Agent   │    │  Agent   │    │  Agent   │        │   │
│  │    └──────────┘    └──────────┘    └──────────┘        │   │
│  │         │               │               │               │   │
│  │         └───────────────┴───────────────┘               │   │
│  │                         │                               │   │
│  └─────────────────────────┼───────────────────────────────┘   │
│                            ▼                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Hedera Service (HCS + Crypto)              │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Hedera Testnet                               │
│           (Consensus Service + Cryptocurrency Service)           │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API Key
- (Optional) Hedera Testnet Account

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=sk-...
# HEDERA_ACCOUNT_ID=0.0.xxxxx (optional)
# HEDERA_PRIVATE_KEY=... (optional)

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🔧 Configuration

### Environment Variables

#### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Yes |
| `HEDERA_ACCOUNT_ID` | Hedera Testnet account ID | No* |
| `HEDERA_PRIVATE_KEY` | Hedera Testnet private key | No* |
| `HEDERA_ESCROW_ACCOUNT_ID` | Escrow account for wagers | No* |
| `TAVILY_API_KEY` | Tavily API for news search | No |
| `COINGECKO_API_KEY` | CoinGecko API key | No |

*Without Hedera credentials, the app runs in simulation mode

#### Frontend (.env.local)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## 📖 API Endpoints

### Start Debate (Non-streaming)
```bash
POST /api/debate/start
Content-Type: application/json

{
  "query": "What is the outlook for HBAR today?",
  "symbol": "HBAR",
  "max_rounds": 2
}
```

### Stream Debate (SSE)
```bash
POST /api/debate/stream
Content-Type: application/json

{
  "query": "Is Bitcoin a good buy right now?",
  "symbol": "BTC"
}
```

### Get Supported Symbols
```bash
GET /api/debate/symbols
```

## 🎨 UI Components

- **BullBubble**: Green-themed message bubble for bullish arguments
- **BearBubble**: Red-themed message bubble for bearish arguments
- **RefereeCard**: Verdict display with Hedera transaction links
- **DebateArena**: Main chat container with auto-scroll
- **ChatInput**: Input with symbol selector and quick prompts

## 🔗 Hedera Integration

### Consensus Service (HCS)
Every debate prediction is logged to a Hedera Consensus Service topic, creating an immutable audit trail:

```json
{
  "type": "AlphaDuel_Prediction",
  "symbol": "HBAR",
  "winner": "Bull",
  "confidence": 75,
  "wager_amount": 7.5,
  "market_snapshot": {
    "price": 0.0725,
    "rsi": 45.2
  }
}
```

### Cryptocurrency Service
The wager amount (based on confidence) is transferred from the agent's wallet to an escrow account, proving "skin in the game."

View transactions on [HashScan Testnet](https://hashscan.io/testnet).

## 🛠️ Development

### Project Structure

```
AlphaDuel/
├── backend/
│   ├── app/
│   │   ├── agents/          # Bull, Bear, Referee agents
│   │   ├── models/          # Pydantic models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Hedera, Market Data services
│   │   └── main.py          # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── lib/             # Utilities
│   └── package.json
└── README.md
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🏆 Hackathon Highlights

1. **LangGraph Multi-Agent System**: Advanced AI agent orchestration with debate loops
2. **Hedera Native Integration**: Real blockchain transactions, not just demos
3. **Streaming UX**: Watch agents "think" in real-time
4. **Accountability**: AI predictions with financial consequences

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

Built with ❤️

