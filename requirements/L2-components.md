# L2: Component-Level Requirements

Detailed behavioral requirements for individual components. Each traces to an L1 parent.

---

## Authentication Components

### CMP-001: Password Hashing

User passwords shall be hashed using `pbkdf2_sha256` via passlib. Plaintext passwords shall never be stored.

- **Parent**: FT-101
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `backend/app/routes/auth.py` — passlib CryptContext usage

### CMP-002: JWT Token Structure

JWT tokens shall contain a string "sub" claim (`str(user.id)`). Token validation shall parse the sub claim as `int(payload.get("sub"))`.

- **Parent**: FT-102
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_jwt.py`

### CMP-003: Protected Endpoints

All API endpoints (except register and login) shall require a valid JWT bearer token. Requests without valid tokens shall receive 401 Unauthorized.

- **Parent**: FT-102
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_auth.py::test_protected_endpoint_no_token`

---

## Character Components

### CMP-010: HP Bar Color Coding

The HP bar shall display green when HP >= 50% of max, yellow when 25-49%, and red when < 25%.

- **Parent**: FT-302
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Damage character through thresholds, verify color changes

### CMP-011: Death Saving Throws

The system shall track death saving throw successes and failures (3 each). Three successes stabilize; three failures result in death.

- **Parent**: FT-302
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_hp_management.py`

### CMP-012: Temp HP Behavior

Temporary HP shall absorb damage before current HP. Temp HP shall not stack (new temp HP replaces old if higher). Healing shall not restore temp HP.

- **Parent**: FT-302
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_hp_management.py`

### CMP-013: SRD Weapons Modal

The attacks section shall include a modal for browsing and selecting SRD weapons, which populates attack fields automatically.

- **Parent**: FT-303
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Open weapons modal, select weapon, verify fields populated

### CMP-014: Spell Slot Tracking

Spell slots shall track current and max values per spell level. Using a spell slot shall decrement current. Long rest shall restore all slots to max.

- **Parent**: FT-304
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Cast spell, verify slot decrements; rest, verify restoration

### CMP-015: Spell Save DC Calculation

Spell save DC shall be auto-calculated as `8 + proficiency bonus + spellcasting ability modifier`.

- **Parent**: FT-304
- **Verification**: D, I
- **Status**: IMPLEMENTED
- **Inspection**: `frontend/src/components/SpellsSection.jsx`

### CMP-016: Level-Up HP Options

Level-up shall offer both "Roll" (random hit die roll + CON modifier, minimum 1) and "Average" (half hit die + 1 + CON modifier) options.

- **Parent**: FT-305
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Level up, choose each option, verify HP calculation

### CMP-017: ASI at Appropriate Levels

Ability Score Improvements shall be offered at class-appropriate levels per SRD data. Options: +2 to one ability or +1 to two abilities. Scores shall not exceed 20.

- **Parent**: FT-305
- **Verification**: D, I
- **Status**: IMPLEMENTED
- **Inspection**: `frontend/src/data/srd-class-data.json` (asi_levels), `LevelUpModal.jsx`

### CMP-018: Portrait Upload Validation

Portrait upload shall accept JPEG, PNG, GIF, and WebP formats. Images shall be resized to 200x200 pixels. Non-image files shall be rejected.

- **Parent**: FT-307
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Upload valid image → success. Upload PDF → rejected.

### CMP-019: Portrait Display Locations

Character portraits shall display on: (1) the character sheet header, (2) initiative tracker combatant rows, (3) with an initials-based fallback when no portrait is set.

- **Parent**: FT-307
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Set portrait, verify in both locations; remove, verify initials fallback

---

## Initiative & Combat Components

### CMP-030: Initiative Ordering

Combatants shall be sorted by initiative value in descending order. Ties shall maintain insertion order.

- **Parent**: FT-401
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py`

### CMP-031: Turn Advancement

The "Next Turn" action shall advance to the next combatant. When the last combatant finishes, the round counter shall increment and turn resets to the first combatant.

- **Parent**: FT-401
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py`

### CMP-032: Action Economy Reset

On turn start, the current combatant's action economy shall reset: action=true, bonus_action=true, reaction=true, movement=max_movement.

- **Parent**: FT-402
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py`

### CMP-033: Condition Duration Tick

Conditions with round-based duration shall decrement by 1 on the affected combatant's turn start. Conditions reaching 0 duration shall be automatically removed.

- **Parent**: FT-404
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py`

### CMP-034: Condition Badge Display

Active conditions shall be displayed as colored badge pills on combatant rows in the initiative tracker.

- **Parent**: FT-404
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Apply condition, verify badge appears with correct styling

### CMP-035: Advantage Roll Mechanics

Advantage shall roll 2d20 and use the higher result. Disadvantage shall roll 2d20 and use the lower result. The roll log entry shall show both dice values with the dropped one visually dimmed.

- **Parent**: FT-405
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Toggle advantage, roll d20, verify two dice shown with correct selection

### CMP-036: Monster HP Controls

Monster stat blocks shall provide increment/decrement HP buttons for the DM. HP shall be bounded by 0 and max HP.

- **Parent**: FT-403
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Add monster, use +/- HP controls, verify bounds

### CMP-037: Movement Auto-Deduction

When auto-tracking is enabled and a token is dragged, the system shall calculate the distance moved (using D&D 5e diagonal rules) and deduct it from the combatant's remaining movement. Movement shall not go below 0.

- **Parent**: FT-407
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Enable auto, drag token 3 cells, verify 15ft deducted

### CMP-038: Movement Undo

The undo move button shall: (1) move the token back to its pre-drag position, (2) restore the deducted movement, (3) be available only until the next turn advancement.

- **Parent**: FT-407
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Drag token, click undo, verify position and movement restored

---

## Battle Map Components

### CMP-050: Grid Rendering

The battle map shall render a configurable grid with visible grid lines on an HTML5 Canvas element.

- **Parent**: FT-601
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_maps.py` (map creation with grid params)

### CMP-051: Token Snap-to-Grid

Tokens shall snap to the nearest grid cell when placed or moved. Token position shall be stored as grid coordinates (x, y).

- **Parent**: FT-603
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Drag token, release between cells, verify snap to nearest cell

### CMP-052: Player Token Ownership

Players shall only be able to drag tokens that have a `character_id` matching their character's ID. The backend shall verify ownership via the Character model's `owner_id` field.

- **Parent**: FT-603, SYS-003
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_maps.py::test_player_can_move_own_token`, `test_maps.py::test_player_cannot_move_other_token`

### CMP-053: Fog Cell Reveal/Hide

The DM shall be able to paint fog cells as revealed or hidden. Fog state shall be stored as a JSON array of revealed cell coordinates. The fog painting shall broadcast in real-time via WebSocket.

- **Parent**: FT-604
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_maps.py` (fog endpoints), D: real-time fog sync

### CMP-054: Fog Player View

Players shall see a dark overlay on unrevealed cells. Tokens on unrevealed cells shall not be visible to players. The DM shall see the full map with fog cells semi-transparent.

- **Parent**: FT-604
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: As player, verify hidden cells are opaque; as DM, verify translucent overlay

### CMP-055: Zoom Bounds

Zoom shall be bounded between 0.25x and 3x. Mouse wheel up shall zoom in; wheel down shall zoom out.

- **Parent**: FT-605
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Zoom to min/max, verify bounds enforced

### CMP-056: D&D Diagonal Distance

Distance measurement shall use the D&D 5e alternating diagonal rule: each pair of diagonal moves costs 15ft (5ft + 10ft), an odd remaining diagonal costs 5ft, and straight moves cost `feet_per_cell` each.

- **Parent**: FT-606
- **Verification**: D, A
- **Status**: IMPLEMENTED
- **Demo**: Measure 2 diagonal cells → 15ft, 3 → 20ft, 1 straight + 1 diagonal → 10ft
- **Analysis**: `calculateDistance()` in BattleMap.jsx

### CMP-057: Measurement Line Rendering

When in measure mode, a dashed line shall be drawn from start to end point with a distance label (e.g., "30 ft") at the midpoint. Start and end cells shall be highlighted.

- **Parent**: FT-606
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Activate measure mode, click-drag, verify dashed line and label

### CMP-058: Token Drag Distance Display

When dragging a token, a distance label shall display showing feet from the token's original position to the current drag position, with a yellow dashed trail line.

- **Parent**: FT-606
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Drag token, verify trail line and distance label follow

---

## Notes Components

### CMP-070: Note Visibility Enforcement

Private notes shall be visible only to their author. The DM shall see all notes regardless of visibility. Public notes shall be visible to all campaign members.

- **Parent**: FT-702
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_notes.py`

### CMP-071: Notes Sidebar Tabs

Notes shall be accessible via sidebar tabs in the Game page, allowing switching between notes and other sidebar content.

- **Parent**: FT-701
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Click Notes tab, verify notes list and CRUD controls

---

## WebSocket Components

### CMP-080: Auto-Reconnection

The WebSocket client shall attempt reconnection up to 5 times with increasing backoff on disconnection.

- **Parent**: FT-801
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `frontend/src/services/websocket.js` — reconnection logic

### CMP-081: Listener Cleanup

WebSocket listeners shall be cleared on connect/disconnect to prevent duplicate event handlers from accumulating.

- **Parent**: FT-801
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `frontend/src/services/websocket.js` — `this.listeners` clearing

### CMP-082: JSON Field Mutation Safety

Backend code modifying JSON fields (e.g., `campaign.settings`) shall call `flag_modified()` before committing to ensure SQLAlchemy detects the change.

- **Parent**: FT-203, FT-803
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: All routes that modify JSON fields

### CMP-083: Concurrent Connection Handling

The WebSocket manager shall support at least 50 concurrent connections without connection failures.

- **Parent**: FT-804
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_websocket_stress.py`

---

## UI Components

### CMP-090: Theme Support

The system shall support multiple UI themes (Dark Medieval, Pink Pony Club, Boring) switchable at runtime via CSS custom properties.

- **Parent**: SYS-005
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Switch themes, verify visual changes

### CMP-091: Responsive Layout

The Game page shall arrange character sheet, initiative tracker, dice roller, roll log, and map in a responsive layout suitable for desktop browsers.

- **Parent**: SYS-005
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Resize browser window, verify layout adapts

### CMP-092: Polyhedral Dice Icons

The dice roller shall display polyhedral shape icons (d4 triangle, d6 cube, d8 diamond, d10, d12 pentagon, d20 icosahedron) for each die type.

- **Parent**: FT-501
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Open dice roller, verify each die has a distinct polyhedral icon
