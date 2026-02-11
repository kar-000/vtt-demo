# D&D 5e Virtual Tabletop

A real-time web application for remote D&D 5e sessions with character management, dice rolling, combat tracking, and shared game logs.

## Current Status: Phase 3 In Progress

**Phase 2 Complete** - 69 tests passing

### Core Features (Phase 1)
- Character creation and management with full D&D 5e stats
- Clickable stat rolling (d20 + modifier)
- Manual dice roller (d4, d6, d8, d10, d12, d20, d100) with polyhedral styling
- Real-time shared log for all players (WebSocket)
- JWT-based authentication (DM vs Player roles)
- SQLite persistence

### Combat Features (Phase 2)
- **HP Management**: Damage/healing, temp HP, death saves, color-coded HP bar
- **Custom Attacks**: Add weapons with attack bonus and damage dice, clickable rolls
- **Spells System**: Full spell management with slots, SRD spell library (~300 spells)
- **Initiative Tracker**: Real-time combat order, turn tracking, round counter
- **Action Economy**: Track actions, bonus actions, reactions, movement per turn
- **DM Tools**: View/edit all player characters, manage combat
- **Level-Up System**: Multi-step wizard with multiclass support, ASI handling
- **UI Theming**: Three themes (Dark Medieval, Pink Pony Club, Boring)

### Phase 3 Features (In Progress)
- **Character Portraits**: Upload avatars, display on sheet and initiative tracker
- **Monster Stat Blocks**: HP/AC/attacks tracking, SRD monster library, DM combat tools
- Campaign Notes/Journal (planned)
- Battle Maps/Grid (planned)

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- WebSockets (real-time communication)
- SQLite (database, PostgreSQL for production)
- JWT (authentication)

**Frontend:**
- React with hooks and Context API
- Vite (build tool)
- WebSocket client with auto-reconnection
- CSS custom properties for theming

## Prerequisites

- Python 3.10+
- Node.js 18+
- Git

## Local Setup

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Start both backend and frontend servers
2. Open multiple browser windows to `http://localhost:5173`
3. Register/login as DM or Player
4. Create or join a campaign
5. Create characters and start playing
6. All rolls appear in real-time for all connected users

## Project Structure

```
vtt/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database, security, dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── websocket/     # WebSocket handlers
│   ├── tests/             # pytest tests (69+ tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # Context providers (Auth, Game, Theme)
│   │   ├── pages/         # Page components
│   │   ├── data/          # SRD data files (spells, weapons, monsters)
│   │   └── services/      # API and WebSocket services
│   └── package.json
├── .github/
│   └── workflows/         # CI/CD pipelines
├── .pre-commit-config.yaml
├── CONTRIBUTING.md
├── PROJECT_STATUS.md
└── README.md
```

## Testing

```bash
# Run backend tests
cd backend
pytest -v

# Run with coverage
pytest --cov=app
```

## Legal

Uses SRD 5.1 content under the Open Gaming License (OGL). See LICENSE.md for details.

## Contributing

This is a personal project, but suggestions and bug reports are welcome!

## License

MIT
