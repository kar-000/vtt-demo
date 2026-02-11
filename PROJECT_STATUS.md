# D&D 5e VTT - Project Status

**Last Updated**: 2026-02-10

## Current Phase: Phase 3 IN PROGRESS (69 tests passing)

### Phase 3 Progress

14. **Character Portraits** ✅ (2026-02-10)
    - ✅ CharacterPortrait component with upload/display functionality
    - ✅ Image upload with validation (JPEG, PNG, GIF, WebP)
    - ✅ Auto-resize to 200x200 with base64 storage in avatar_url field
    - ✅ Size variants: large (100px), medium (60px), small (36px), tiny (28px)
    - ✅ Display on character sheet header
    - ✅ Display in initiative tracker (tiny size)
    - ✅ Placeholder/initials fallback when no portrait

15. **Monster Stat Blocks** ✅ (2026-02-10)
    - ✅ MonsterStatBlock component with expandable details
    - ✅ Quick stats display (AC + HP bar) collapsed view
    - ✅ DM HP controls (damage/heal buttons)
    - ✅ Attack buttons with integrated dice rolling
    - ✅ SRD monster library (10 common creatures)
    - ✅ Add monsters from SRD dropdown in initiative tracker
    - ✅ Color-coded HP bar (green/yellow/red based on %)

16. **Campaign Notes/Journal** ⏳ (In Progress)
    - Notes model and endpoints
    - Session notes for DM
    - Character journals (private/shared)
    - Markdown support

17. **Battle Maps/Grid** (Planned)
    - Interactive grid-based maps
    - Token placement and movement
    - Real-time sync via WebSocket

---

## Phase 2 COMPLETE! 🎉

## ⚖️ Legal Foundation: SRD 5.1

**Decision**: Use SRD 5.1 (System Reference Document) as the base content library.

**Rationale**:
- Released under Open Gaming License (OGL) - legally safe to implement
- Includes core D&D 5e mechanics, spells, monsters, and equipment
- Avoids copyright issues with non-SRD content from official books
- Allows free distribution and digital implementation

**Implementation Approach**:
- Provide SRD 5.1 content as default (spells, abilities, equipment)
- Design flexible data models that allow manual content entry
- Users can add their own non-SRD content (spells, subclasses, etc.)
- We don't distribute non-SRD content - users input what they own
- Include OGL license text in repository and application

**What This Means**:
- ✅ Fully functional VTT with complete rule system
- ✅ Legally distributable without WotC concerns
- ✅ Users can use any content they personally own (they enter it)
- ✅ Flexible enough to support homebrew and custom content

**Resources**:
- Official SRD 5.1: Available from D&D website
- Open5e.com: API access to SRD content
- License: Must include OGL text (see LICENSE.md)

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

### Completed Features

1. **HP Management** ✅ (2026-02-05)
   - ✅ Edit current HP on character sheet
   - ✅ Apply damage/healing with quick buttons
   - ✅ Temporary HP tracking
   - ✅ Death saves tracker (when HP = 0) with clickable boxes
   - ✅ Color-coded HP bar with visual indicator
   - ✅ Damage precedence (temp HP absorbed first)
   - ✅ Auto-reset death saves on healing
   - ✅ 16 comprehensive tests added (38 total tests passing)

2. **Character Export/Import** ✅ (2026-02-05)
   - ✅ Export character as JSON from character sheet
   - ✅ Import character from JSON on dashboard
   - ✅ Automatic filename sanitization
   - ✅ Export metadata (version, timestamp)
   - ✅ Import validation and error handling

3. **UI Improvements** ✅ (2026-02-05)
   - ✅ Large blue ability modifiers (matching character creation)
   - ✅ Clickable proficiency toggles for skills (○ → ● → ◆)
   - ✅ Clickable proficiency toggles for saves (○ ⇄ ●)
   - ✅ Hover effects on proficiency indicators

4. **Custom Weapons/Attacks System** ✅ (2026-02-05)
   - ✅ AttacksSection component with full CRUD operations
   - ✅ Add custom weapons with name, attack bonus, damage dice, damage type
   - ✅ Edit and delete existing attacks
   - ✅ Clickable attack rolls (d20 + bonus) integrated with rollDice
   - ✅ Clickable damage rolls with dice parsing
   - ✅ Color-coded roll buttons (green for attack, red for damage)
   - ✅ Results displayed in shared combat log
   - ✅ Attacks stored in character.attacks JSON field

5. **Spells System** ✅ (2026-02-05)
   - ✅ SpellsSection component with full spell management
   - ✅ Spell slots tracking for levels 1-9 (current/max per level)
   - ✅ Custom spell entry with complete D&D fields (school, casting time, range, components, etc.)
   - ✅ Add/edit/delete spells functionality
   - ✅ Organize and display spells by level (cantrips through level 9)
   - ✅ Clickable spell casting for damage/healing rolls
   - ✅ Color-coded cast buttons (green for healing, red for damage)
   - ✅ Spell save DC and spell attack bonus fields
   - ✅ Spells stored in character.spells JSON field
   - 📝 Note: SRD 5.1 spell library integration deferred for future enhancement

### Immediate Priorities

6. **Initiative Tracker** ✅ (2026-02-06)
   - ✅ Real-time initiative tracking via WebSocket
   - ✅ DM can start/end combat
   - ✅ Add NPCs to initiative order
   - ✅ Roll initiative for all combatants or individually
   - ✅ Set custom initiative values
   - ✅ Cycle through turns with next/previous buttons
   - ✅ Highlight current turn with gold styling
   - ✅ Round counter
   - ✅ State persists in campaign.settings JSON
   - ✅ 9 comprehensive tests added

7. **DM Capabilities** ✅ (2026-02-06)
   - ✅ GET /characters/all endpoint (DM only)
   - ✅ "Player Characters" section on Dashboard for DMs
   - ✅ DM can view any player's character sheet
   - ✅ DM can edit any player's character
   - ✅ DM can modify HP on any character
   - ✅ "DM View" badge on character sheet
   - ✅ Golden styling for player character cards
   - ✅ 8 comprehensive tests added

8. **UI Polish** ✅ (2026-02-06)
   - ✅ Dice roller buttons styled as polyhedral dice shapes
   - ✅ Spell sharing to chat functionality

11. **Level-Up System** ✅ (2026-02-07)
    - ✅ SRD class data for all 12 classes (hit dice, spell slots, ASI levels)
    - ✅ LevelUpModal with 4-step workflow (Choose Class → HP → ASI → Summary)
    - ✅ Multiclass support (level in same class or choose new class)
    - ✅ HP increase options (roll hit die or take average + CON mod)
    - ✅ ASI at appropriate levels (+2 to one stat or +1 to two stats)
    - ✅ Automatic spell slot updates for casters
    - ✅ Level Up button in CharacterSheet header
    - ✅ Collapsible spell cards with mini cast button
    - ✅ Auto-calculated Spell Save DC and Spell Attack Bonus
    - ✅ Fixed spell share time bug (UTC timezone)
    - ✅ Fixed spell share text formatting

12. **Ability Descriptions** ✅ (2026-02-07)
    - ✅ Expandable ability cards with descriptions
    - ✅ Shows related skills and common uses per ability
    - ✅ "Share to Log" button posts ability info to chat
    - ✅ Expand/collapse animations
    - ✅ Consistent with existing UI patterns

13. **Action Economy Tracking** ✅ (2026-02-07)
    - ✅ Track action/bonus action/reaction/movement per combatant
    - ✅ Visual tokens show available vs used status
    - ✅ Movement tracker with -5/-10 ft buttons
    - ✅ Auto-reset on turn change
    - ✅ DM can reset any combatant's action economy
    - ✅ Players can only control their own character's turn
    - ✅ Real-time sync via WebSocket

## Phase 2 Complete! 🎉

9. **UI Theming** ✅ (2026-02-07)
   - ✅ Three complete themes with CSS custom properties
     - **Dark Medieval (Default)** - Dark fantasy aesthetic, gold accents
     - **Pink Pony Club** - Sparkly pink and playful
     - **Boring** - Minimal, neutral, no-frills
   - ✅ ThemeContext for React state management
   - ✅ Theme persistence via localStorage
   - ✅ CSS variables for all colors, shadows, borders
   - ✅ Smooth theme transitions
   - ✅ ThemeSwitcher component (dropdown + compact icon mode)
   - ✅ All CSS files migrated to use theme variables
   - ✅ Theme switcher in Dashboard header and Game header

10. **Layout Improvements** ✅ (2026-02-07)
    - ✅ Attacks and Spells sections side-by-side on desktop
    - ✅ Compact attack/damage roll buttons
    - ✅ Responsive stacking on smaller screens (< 1200px)

## 📊 Phase 2 Planning Questions

Before starting Phase 2, decide:

1. **Attacks Data Model**
   - Store attacks in database or calculate from character data?
   - How to handle multiple attack types (melee, ranged, spell attacks)?
   - What fields needed? (name, attack_bonus, damage_dice, damage_type, etc.)

2. **Spells Data Model**
   - Start with SRD 5.1 spell list (~300 spells)
   - Allow manual entry for non-SRD spells (user responsibility)
   - How to handle spell slot tracking?
   - Upcasting mechanics?
   - Concentration tracking?
   - Consider using Open5e API vs seeding local database

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

### Recent Work (2026-02-06)

**DM Capabilities Complete** ✅
- Backend: Added GET /characters/all endpoint for DM to fetch all characters
- Backend: Updated PUT /characters/{id} to allow DM to edit any character
- Frontend: "Player Characters" section on Dashboard (golden styling)
- Frontend: "DM View" badge when viewing player's character sheet
- Frontend: allCharacters state in GameContext for DM view
- Added 8 comprehensive tests for DM capabilities

**Dice Roller Styling** ✅
- Buttons now shaped like traditional polyhedral dice
- d4=triangle, d6=square, d8=diamond, d10=kite, d12=pentagon, d20=red triangle, d100=orange circle
- Uses CSS clip-path for unique shapes

**Initiative Tracker Complete** ✅
- Fixed bugs: All characters now appear (not just DM's)
- Fixed bugs: Initiative values persist correctly (flag_modified fix)
- Fixed bugs: Duplicate dice rolls resolved (listener cleanup)
- Added spell sharing to chat
- 9 comprehensive tests for initiative tracker

### Earlier (2026-02-05)

**Spells System Complete** ✅
- Created SpellsSection component with comprehensive spell management
- Spell slots tracking for all levels (1-9) with current/max per level
- Custom spell entry with complete D&D 5e fields (name, level, school, casting time, range, components, duration, description)
- Damage/healing spells with dice notation, damage types, and saving throw support
- Spell save DC and spell attack bonus fields
- Add/edit/delete spells with full CRUD operations
- Spells organized and displayed by level (cantrips through level 9)
- Clickable spell casting integrated with rollDice system
- Color-coded cast buttons (green for healing, red for damage)
- Spells stored in character.spells JSON field (no backend changes needed)
- All code committed and pushed to GitHub (commit: 1901a3a)

**Custom Weapons/Attacks System Complete** ✅
- Created AttacksSection component with full CRUD functionality
- Add/edit/delete attacks with name, attack bonus, damage dice, damage type
- Clickable attack rolls (d20 + bonus) and damage rolls integrated with existing rollDice system
- Color-coded roll buttons for better UX (green for attacks, red for damage)
- Attacks stored in character.attacks JSON field (no backend changes needed)
- All code committed and pushed to GitHub (commit: 04d4ad5)

**Phase 2 Kickoff: HP Management + Character Export/Import Complete** ✅
- Implemented comprehensive HP management system
- Backend: death_saves field, HP update endpoints, damage/healing logic
- Frontend: HPManager component with color-coded HP bar, damage/healing controls, death saves tracker
- Added 16 comprehensive HP management tests (38 total tests passing)
- Integrated HPManager into CharacterSheet component
- Character export/import for JSON backups
- Ability score styling and proficiency toggles improved
- All tests passing, code committed and pushed to GitHub

**Earlier (2026-02-05)**
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
