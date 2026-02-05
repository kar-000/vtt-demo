# Development Guide

## Project Architecture

### Backend (FastAPI + SQLAlchemy)

```
backend/
├── app/
│   ├── core/           # Core configuration and utilities
│   │   ├── config.py   # Settings and environment variables
│   │   ├── database.py # Database connection and session
│   │   ├── security.py # JWT and password hashing
│   │   └── dependencies.py # FastAPI dependencies
│   ├── models/         # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── character.py
│   │   └── campaign.py
│   ├── schemas/        # Pydantic schemas for validation
│   │   ├── user.py
│   │   ├── character.py
│   │   └── dice.py
│   ├── routes/         # API endpoints
│   │   ├── auth.py     # Authentication endpoints
│   │   ├── characters.py # Character CRUD
│   │   └── dice.py     # WebSocket for dice rolls
│   ├── services/       # Business logic (future use)
│   ├── websocket/      # WebSocket connection manager
│   └── main.py         # FastAPI application entry point
```

### Frontend (React + Vite)

```
frontend/
├── src/
│   ├── components/     # Reusable React components
│   │   ├── CharacterSheet.jsx
│   │   ├── DiceRoller.jsx
│   │   └── RollLog.jsx
│   ├── contexts/       # React Context for state management
│   │   ├── AuthContext.jsx
│   │   └── GameContext.jsx
│   ├── pages/          # Page components
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   ├── CharacterForm.jsx
│   │   └── Game.jsx
│   ├── services/       # API and WebSocket services
│   │   ├── api.js
│   │   └── websocket.js
│   └── main.jsx        # React entry point
```

## Development Workflow

### First-Time Setup

1. **Backend:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or: source venv/bin/activate  # Mac/Linux
   pip install -r requirements.txt
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database

### Current Setup
- SQLite database: `dnd_vtt.db` (auto-created on first run)
- Location: `backend/` directory

### Viewing Database
Use any SQLite viewer:
- DB Browser for SQLite: https://sqlitebrowser.org/
- VS Code extension: SQLite Viewer

### Resetting Database
Simply delete `dnd_vtt.db` and restart the backend. Tables will be recreated.

### Switching to PostgreSQL (for production)

Update `backend/app/core/config.py`:
```python
DATABASE_URL: str = "postgresql://user:password@localhost/dnd_vtt"
```

Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

## WebSocket Testing

The WebSocket endpoint is at: `ws://localhost:8000/api/v1/ws/game/{campaign_id}?token={jwt_token}`

For testing outside the frontend:
1. Get a JWT token by logging in via the API
2. Use a WebSocket client (e.g., Postman, wscat)

## Common Development Tasks

### Adding a New API Endpoint

1. Create/update schema in `backend/app/schemas/`
2. Add endpoint in `backend/app/routes/`
3. Include router in `backend/app/main.py`
4. Test at http://localhost:8000/docs

### Adding a New Model Field

1. Update model in `backend/app/models/`
2. Update schema in `backend/app/schemas/`
3. Delete database or use Alembic migrations
4. Restart backend

### Adding a New Frontend Page

1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.jsx`
3. Add navigation link where needed

## Phase 2 Preparation

The codebase is structured to easily add Phase 2 features:

### Attacks System
- Models: Character has `attacks` JSON field ready
- Add UI in CharacterSheet to display attacks
- Add click handler to roll attack + damage

### Spells System
- Models: Character has `spells` JSON field ready
- Create SpellList component
- Auto-calculate spell save DC from character stats

### Initiative Tracker
- Create new CombatTracker component
- Add initiative rolls via WebSocket
- DM controls turn order

## Testing

### Manual Testing Checklist

**Authentication:**
- [ ] Register new user
- [ ] Login with credentials
- [ ] Invalid credentials rejected
- [ ] Token persists on refresh

**Character Management:**
- [ ] Create character
- [ ] Edit character
- [ ] Delete character
- [ ] Multiple characters per user

**Dice Rolling:**
- [ ] Quick roll buttons work
- [ ] Custom roll with modifier
- [ ] Stat rolls (click on stats)
- [ ] Skill rolls (click on skills)
- [ ] Saving throw rolls

**Real-time Features:**
- [ ] Open two browsers
- [ ] Both see each other's rolls
- [ ] Roll log updates in real-time
- [ ] Connection status shows "Connected"

### Automated Testing (Future)

Example test structure:
```
backend/tests/
├── test_auth.py
├── test_characters.py
└── test_dice.py

frontend/src/
├── __tests__/
│   ├── CharacterSheet.test.jsx
│   └── DiceRoller.test.jsx
```

## Troubleshooting

### Backend won't start
- Check Python version (3.10+)
- Verify virtual environment is activated
- Check if port 8000 is already in use

### Frontend won't start
- Check Node version (18+)
- Delete `node_modules` and `package-lock.json`, reinstall
- Check if port 5173 is already in use

### Database errors
- Delete `dnd_vtt.db` and restart
- Check file permissions

### WebSocket not connecting
- Ensure backend is running
- Check browser console for errors
- Verify JWT token is valid

## Performance Considerations

### Current Limitations
- SQLite is single-writer (fine for 3-5 users)
- WebSocket connections are in-memory (lost on restart)
- No message persistence

### Future Optimizations
- Switch to PostgreSQL for production
- Add Redis for WebSocket pub/sub
- Implement database connection pooling
- Add message queue for reliability

## Security Notes

### Current Security Features
- Password hashing with bcrypt
- JWT authentication
- Input validation with Pydantic
- CORS protection

### Before Production
- Change SECRET_KEY in config.py
- Use environment variables for secrets
- Enable HTTPS
- Add rate limiting
- Implement CSRF protection
- Add input sanitization for user content

## Contributing

When adding features:
1. Create a new branch: `git checkout -b feature/your-feature`
2. Make changes and test thoroughly
3. Commit with clear messages
4. Push and create pull request

## Resources

- FastAPI docs: https://fastapi.tiangolo.com/
- React docs: https://react.dev/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- D&D 5e SRD: https://www.dndbeyond.com/sources/basic-rules
