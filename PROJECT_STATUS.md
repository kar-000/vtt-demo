# D&D 5e VTT - Project Status

**Last Updated**: 2026-02-15

## Current Phase: Phase 4 IN PROGRESS (226 tests passing, 93% coverage)

### Phase 4 Progress: Combat Automation

18. **Conditions & Status Effects** ✅ (2026-02-14)
    - ✅ Apply/remove all 15 D&D 5e conditions (Blinded, Charmed, etc.)
    - ✅ Duration tracking (rounds-based with auto-expiry, or indefinite)
    - ✅ Conditions displayed as badges on combatants in initiative tracker
    - ✅ Condition duration ticks down on next_turn
    - ✅ DM can clear all conditions on a combatant
    - ✅ Conditions persist across WebSocket reconnects

19. **Advantage/Disadvantage** ✅ (2026-02-14)
    - ✅ Toggle button in DiceRoller (ADV/DIS)
    - ✅ Rolls 2d20, takes higher (advantage) or lower (disadvantage)
    - ✅ Roll log shows both dice with used/dropped styling
    - ✅ Labels displayed on roll results

20. **Whisper/Secret Rolls** ✅ (2026-02-15)
    - ✅ WHISPER toggle in DiceRoller (sends to DM only)
    - ✅ Whisper routing for dice rolls and chat messages
    - ✅ `send_to_user()` WebSocket method for targeted messaging
    - ✅ Prominent purple whisper banner with contextual text
    - ✅ DM sees "whispered by [Player]", player sees "whispered to DM"
    - ✅ 8 whisper-specific tests

21. **PC Re-add to Initiative** ✅ (2026-02-15)
    - ✅ "+ PC" button appears when characters are missing from initiative
    - ✅ Backend `add_pc` action with duplicate prevention
    - ✅ Re-sorts initiative if value provided
    - ✅ DM `loadAllCharacters` on Game page mount

22. **Token Status Icons on Map** (Planned)
    - Show condition icons on battle map tokens
    - Visual indicators for HP status

---

## Phase 3 COMPLETE

14. **Character Portraits** ✅ (2026-02-10)
    - ✅ CharacterPortrait component with upload/display
    - ✅ Image upload with validation (JPEG, PNG, GIF, WebP)
    - ✅ Auto-resize to 200x200 with base64 storage
    - ✅ Display on character sheet and initiative tracker
    - ✅ Placeholder/initials fallback

15. **Monster Stat Blocks** ✅ (2026-02-10)
    - ✅ MonsterStatBlock component with expandable details
    - ✅ DM HP controls and attack buttons with dice rolling
    - ✅ SRD monster library (10 common creatures)
    - ✅ Color-coded HP bar

16. **Campaign Notes/Journal** ✅ (2026-02-10)
    - ✅ Note model with CRUD endpoints
    - ✅ Public/private visibility (DM sees all)
    - ✅ Sidebar tabs in Game page

17. **Battle Maps/Grid** ✅ (2026-02-10)
    - ✅ HTML5 Canvas grid with zoom/pan
    - ✅ Drag-and-drop token placement and movement
    - ✅ Fog of war (DM reveals/hides areas)
    - ✅ Real-time sync via WebSocket
    - ✅ Map CRUD with activation system
    - ✅ 40 map-related tests

---

## Phase 2 COMPLETE

1. **HP Management** ✅ - Damage/healing, temp HP, death saves, color-coded HP bar
2. **Character Export/Import** ✅ - JSON export/import with validation
3. **UI Improvements** ✅ - Ability modifiers, proficiency toggles
4. **Custom Weapons/Attacks** ✅ - CRUD attacks, clickable rolls, SRD weapons library
5. **Spells System** ✅ - Full spell management, slots, SRD library (~300 spells)
6. **Initiative Tracker** ✅ - Real-time combat order, turn tracking, round counter
7. **DM Capabilities** ✅ - View/edit all characters, manage combat
8. **UI Polish** ✅ - Polyhedral dice shapes, spell sharing
9. **UI Theming** ✅ - Three themes (Dark Medieval, Pink Pony Club, Boring)
10. **Layout Improvements** ✅ - Side-by-side attacks/spells, responsive
11. **Level-Up System** ✅ - 4-step wizard, multiclass, ASI, auto spell slots
12. **Ability Descriptions** ✅ - Expandable cards, share to log
13. **Action Economy** ✅ - Track action/bonus/reaction/movement per turn

---

## Phase 1 COMPLETE

- Character creation and management with full D&D 5e stats
- Clickable stat rolling, manual dice roller
- Real-time shared dice roll log (WebSocket)
- JWT authentication (DM vs Player)
- SQLite persistence, CI/CD pipelines, pre-commit hooks

---

## Legal Foundation: SRD 5.1

Uses SRD 5.1 content under the Open Gaming License (OGL).
- SRD content as default (spells, monsters, weapons, class data)
- Users can add custom non-SRD content
- OGL license text in repository

## Architecture

### Backend
- FastAPI for REST + WebSocket endpoints
- SQLAlchemy ORM with SQLite (PostgreSQL for production)
- JWT tokens with string "sub" claim
- WebSocket manager with campaign-based rooms
- `flag_modified()` for JSON field mutations

### Frontend
- React with functional components, hooks, and Context API
- Vite build tool
- HTML5 Canvas for battle maps
- WebSocket service with auto-reconnection (max 5 attempts)
- CSS custom properties for theming

### Data Files
- `srd-weapons.json` - All SRD weapons
- `srd-spells.json` - All SRD spells (~300)
- `srd-class-data.json` - Hit dice, spell slots, ASI levels per class
- `srd-monsters.json` - Common SRD monsters (10 creatures)

## Known Issues

- [ ] Memory leak testing (4+ hour sessions not yet tested)
- [ ] WebSocket listeners cleared on reconnect (pre-existing)
- [ ] `loadAllCharacters` not called automatically for DM in all contexts

## Deployment Planning

- Currently local development only
- Future: Backend deployment (Railway, VPS)
- Future: Frontend deployment (Vercel, Netlify)
- Future: PostgreSQL for production
- Future: Redis for WebSocket scaling
