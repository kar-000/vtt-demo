# D&D 5e Virtual Tabletop

A real-time web application for remote D&D 5e sessions with character management, dice rolling, and shared game logs.

## Current Status: Phase 1

Phase 1 includes:
- Character creation and management
- Full character sheet with D&D 5e stats and modifiers
- Clickable stat rolling (d20 + modifier)
- Manual dice roller (d4, d6, d8, d10, d12, d20, d100)
- Real-time shared log for all players
- Basic authentication (DM vs Player roles)
- SQLite persistence

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- WebSockets (real-time communication)
- SQLite (database)
- JWT (authentication)

**Frontend:**
- React
- Vite (build tool)
- WebSocket client
- Modern CSS

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
4. Create characters and start rolling dice
5. All rolls appear in real-time for all connected users

## Project Structure

```
vtt/
├── backend/
│   ├── app/
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── websocket/     # WebSocket handlers
│   │   └── main.py        # FastAPI app
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API and WebSocket services
│   │   ├── hooks/         # Custom React hooks
│   │   └── App.jsx
│   ├── package.json
│   └── README.md
├── .gitignore
└── README.md
```

## Roadmap

### Phase 2 - Combat & Abilities (Coming Next)
- Attack rolls with damage
- Spell system with auto-calculated DC
- Initiative tracking
- DM character sheet editing
- Level-up system

### Phase 3 - Maps & Tokens (Future)
- Interactive maps with fog of war
- Movable player and NPC tokens
- Campaign management
- Map-based character access

## Contributing

This is a personal project, but suggestions and bug reports are welcome!

## License

MIT
