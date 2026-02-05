# D&D 5e VTT - Project Status

**Last Updated**: 2026-02-05

## Current Phase: Phase 1 Complete, Ready for Phase 2

## ✅ Completed (Phase 1)

### Core Features
- [x] Character creation and editing UI
- [x] Character sheet display with all 6 stats and modifiers
- [x] Derived stats: AC, HP, Proficiency Bonus, Speed, Saving Throws, Skills
- [x] Clickable stat rolling (d20 + modifier)
- [x] Real-time shared dice roll log (WebSocket-based)
- [x] Manual dice roller (d4, d6, d8, d10, d12, d20, d100)
- [x] JWT-based authentication (DM vs Player roles)
- [x] SQLite database with SQLAlchemy ORM
- [x] Data persistence with proper schema

### Infrastructure
- [x] GitHub repository: https://github.com/kar-000/vtt-demo
- [x] CI/CD pipelines with GitHub Actions
  - [x] Automated tests on push/PR
  - [x] Nightly test runs (2 AM UTC)
  - [x] Code quality checks (3 AM UTC)
- [x] Pre-commit hooks (black, isort, flake8, prettier)
- [x] Comprehensive test suite (22 tests, all passing)
- [x] Development documentation (CONTRIBUTING.md)

### Bug Fixes & Improvements
- [x] Fixed JWT "sub" claim bug (string vs integer)
- [x] Added regression tests for authentication
- [x] Cleaned up debug logging
- [x] Re-enabled WebSocket reconnection
- [x] Fixed deprecated GitHub Actions (upload-artifact v3 → v4)
- [x] Auto-formatted entire codebase

## 🚧 Known Issues

### To Investigate
- [ ] Memory leak testing (4+ hour sessions not yet tested)
- [ ] Performance testing with 5+ concurrent users
- [ ] WebSocket connection stability over extended periods

### Minor Improvements
- [ ] Add avatar upload functionality for characters
- [ ] Improve error messages in UI
- [ ] Add loading states for API calls
- [ ] Consider adding toast notifications

## 📋 Next Steps (Phase 2)

### Immediate Priorities
1. **Attacks System**
   - Display all attacks on character sheet
   - Clickable to roll hit (d20 + modifier)
   - Automatic damage roll on hit
   - Show results in shared log

2. **Spells System**
   - Display spell list organized by level
   - Track spell slots (current/max)
   - Clickable to roll damage/healing
   - Auto-calculate spell save DC
   - Concentration indicator

3. **Initiative Tracker**
   - DM can roll/set initiative for all combatants
   - Turn order display
   - Cycle through turns
   - Highlight current turn

4. **DM Capabilities**
   - View all player character sheets
   - Edit any character sheet
   - Manage combat encounter

### Future (Phase 2 continued)
- [ ] Ability descriptions with expandable details
- [ ] Post abilities to shared log
- [ ] Level-up system with guided workflow
- [ ] Action economy tracking (action/bonus action/reaction/movement)

## 📊 Phase 2 Planning Questions

Before starting Phase 2, decide:

1. **Attacks Data Model**
   - Store attacks in database or calculate from character data?
   - How to handle multiple attack types (melee, ranged, spell attacks)?
   - What fields needed? (name, attack_bonus, damage_dice, damage_type, etc.)

2. **Spells Data Model**
   - Full D&D 5e spell database or manual entry?
   - How to handle spell slot tracking?
   - Upcasting mechanics?
   - Concentration tracking?

3. **Initiative Tracker**
   - Where to display? (sidebar, modal, top of screen?)
   - How to handle ties in initiative?
   - Should it auto-advance turns or require DM input?

4. **DM Interface**
   - Separate DM view or enhanced UI in main view?
   - How to switch between characters as DM?
   - Combat management tools needed?

## 🏗️ Architecture Decisions Made

### Backend
- FastAPI for REST + WebSocket endpoints
- SQLAlchemy ORM for database access
- JWT tokens with string "sub" claim (user_id)
- pbkdf2_sha256 for password hashing (Pydantic v1 compatible)
- WebSocket manager for real-time updates

### Frontend
- React with functional components and hooks
- Context API for auth and game state
- localStorage for token persistence
- WebSocket service with auto-reconnection
- Vite for build tooling

### Database Schema
- Users table (id, username, email, hashed_password, is_dm, is_active)
- Characters table (id, user_id, name, race, class, level, stats, etc.)
- Campaigns table (exists but not fully implemented)
- Future: attacks, spells, abilities tables

### Testing Strategy
- Unit tests for core logic (JWT, password hashing)
- Integration tests for API endpoints
- Test database separation (test.db)
- Pre-commit hooks enforce code quality
- CI/CD runs tests on every push

## 📁 Project Structure

```
VTT/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database, security, dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── websocket/     # WebSocket manager
│   ├── tests/            # pytest tests
│   ├── requirements.txt
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── contexts/     # Context providers
│   │   ├── pages/        # Page components
│   │   └── services/     # API and WebSocket services
│   ├── package.json
│   └── node_modules/
├── .github/
│   └── workflows/        # CI/CD pipelines
├── .pre-commit-config.yaml
├── CONTRIBUTING.md
├── PROJECT_STATUS.md     # This file
└── README.md
```

## 🎯 Success Metrics

### Phase 1 Goals (Current)
- ✅ Real-time multiplayer works
- ✅ Data persists reliably
- ✅ Clean, intuitive UI
- ✅ Code quality maintained
- ⏳ Performance tested (needs 4+ hour test)
- ⏳ Concurrent users tested (needs 5+ users)

### Phase 2 Goals (Next)
- Attacks and spells implemented
- Initiative tracker functional
- DM can manage combat
- Level-up system working
- No performance degradation

### Overall Goals
- Production-ready for remote play with friends
- Stable 4+ hour sessions
- 5+ concurrent users smoothly
- Modern, BG3-inspired UI/UX
- Extensible architecture for Phase 3

## 📝 Notes

### Recent Work (2026-02-05)
- Fixed critical JWT authentication bug
- Added comprehensive test suite (22 tests)
- Set up CI/CD with nightly runs
- Configured pre-commit hooks
- Cleaned up codebase with linting
- All systems operational

### Memory Management Considerations
- WebSocket cleanup implemented but not stress-tested
- Event listeners properly removed
- Database connections pooled
- Image assets not yet relevant (no maps yet)
- Need to profile during long sessions

### Deployment Planning
- Currently local development only
- Future: Deploy backend (Heroku, Railway, or VPS)
- Future: Deploy frontend (Vercel, Netlify, or Cloudflare Pages)
- Future: PostgreSQL for production (currently SQLite)
- Future: Redis for WebSocket scaling (if needed)
