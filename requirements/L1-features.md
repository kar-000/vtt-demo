# L1: Feature-Level Requirements

Feature requirements grouped by domain. Each traces to a parent SYS requirement.

---

## 1xx: Authentication & Users

### FT-101: User Registration

The system shall allow new users to register with a username and password. Usernames shall be unique.

- **Parent**: SYS-003, SYS-006
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_auth.py::test_register_user`

### FT-102: User Login with JWT

The system shall authenticate users via username/password and issue JWT tokens for subsequent API requests. Tokens shall contain a string "sub" claim with the user ID.

- **Parent**: SYS-006
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_auth.py::test_login_user`, `test_jwt.py`

### FT-103: DM vs Player Roles

The system shall distinguish DM and Player roles. The first user to create a campaign shall be the DM. The DM shall have elevated permissions to manage all game state.

- **Parent**: SYS-003
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_dm_capabilities.py`

---

## 2xx: Campaign Management

### FT-201: Campaign CRUD

The system shall allow the DM to create, read, update, and delete campaigns. Each campaign shall have a name and associated settings.

- **Parent**: SYS-002
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_campaigns.py`

### FT-202: Campaign Join

The system shall allow players to join existing campaigns and associate their characters with that campaign.

- **Parent**: SYS-001
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_campaigns.py`

### FT-203: Campaign Settings Persistence

The system shall persist campaign settings (including initiative state) as a JSON field that survives server restarts.

- **Parent**: SYS-002
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py`

---

## 3xx: Character Management

### FT-301: Character Creation

The system shall allow players to create characters with D&D 5e attributes: name, race, class, level, and six ability scores (STR, DEX, CON, INT, WIS, CHA).

- **Parent**: SYS-004
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_campaigns.py` (character creation within campaigns)

### FT-302: HP Management

The system shall track current HP, max HP, and temporary HP. It shall support damage, healing, temp HP application, and death saving throws with a color-coded HP bar.

- **Parent**: SYS-004
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_hp_management.py`

### FT-303: Attacks System

The system shall allow characters to have custom attacks with attack bonus, damage dice, and damage type. Attacks shall be clickable to trigger dice rolls. An SRD weapons library shall be available.

- **Parent**: SYS-004, SYS-009
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_hp_management.py` (attack data), D: manual click-to-roll

### FT-304: Spells System

The system shall support full spell management including spell slots (per level), spells known, spell save DC, and spell attack bonus. An SRD spell library (~300 spells) shall be available for selection.

- **Parent**: SYS-004, SYS-009
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_hp_management.py` (spell data), D: spell slot tracking

### FT-305: Level-Up System

The system shall provide a guided level-up workflow: class selection (including multiclass), HP gain (roll or average), Ability Score Improvement at appropriate levels, and automatic spell slot updates.

- **Parent**: SYS-004
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: 4-step LevelUpModal wizard

### FT-306: Character Export/Import

The system shall allow characters to be exported as JSON and imported from JSON with validation.

- **Parent**: SYS-002
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_campaigns.py` (export/import endpoints)

### FT-307: Character Portraits

The system shall allow character portrait upload (JPEG, PNG, GIF, WebP), auto-resize to 200x200, store as base64, and display on character sheet and initiative tracker.

- **Parent**: SYS-004
- **Verification**: D, I
- **Status**: IMPLEMENTED
- **Demo**: Upload portrait, verify display in sheet and initiative

### FT-308: Ability Score Details

The system shall display ability modifiers, proficiency toggles, saving throw proficiencies, and expandable ability descriptions with common uses and associated skills.

- **Parent**: SYS-004
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Expand ability cards, verify descriptions and skill links

### FT-309: Multiclass Support

The system shall track multiclass levels (e.g., `{Fighter: 5, Wizard: 3}`) and calculate total level, hit dice, and spell slots according to SRD multiclassing rules.

- **Parent**: SYS-004
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Level up into a second class, verify slot calculation

### FT-310: DM Character Management

The DM shall be able to view and edit all player characters in the campaign, not just their own.

- **Parent**: SYS-003
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_dm_capabilities.py`

---

## 4xx: Combat & Initiative

### FT-401: Initiative Tracker

The system shall provide an initiative tracker that orders combatants by initiative value, tracks the current turn, advances turns, and counts rounds.

- **Parent**: SYS-008
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py`

### FT-402: Action Economy Tracking

The system shall track per-combatant action economy: action, bonus action, reaction, and movement (with max movement). These shall reset on turn start.

- **Parent**: SYS-008
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_initiative.py` (action economy fields)

### FT-403: Monster Stat Blocks

The system shall display monster stat blocks with HP, AC, attacks, and speed. The DM shall have HP controls and attack buttons that trigger dice rolls.

- **Parent**: SYS-004, SYS-008
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Add SRD monster to initiative, use HP controls and attack buttons

### FT-404: Conditions & Status Effects

The system shall support all 15 D&D 5e conditions (Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious) plus pseudo-conditions (Concentrating, Dodging, Raging). Conditions shall have duration tracking (rounds-based with auto-expiry or indefinite), display as badges on combatants, and persist across WebSocket reconnects.

- **Parent**: SYS-008
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_initiative.py` (condition add/remove/duration)

### FT-405: Advantage/Disadvantage

The system shall support advantage and disadvantage on d20 rolls. Advantage rolls 2d20 and takes the higher; disadvantage takes the lower. The roll log shall show both dice with used/dropped styling.

- **Parent**: SYS-008
- **Verification**: T, D
- **Status**: IMPLEMENTED
- **Test**: `test_dice_coverage.py`, D: toggle ADV/DIS in dice roller

### FT-406: PC Re-add to Initiative

The system shall allow the DM to re-add player characters to an active initiative if they were removed, with duplicate prevention.

- **Parent**: SYS-008
- **Verification**: T
- **Status**: IMPLEMENTED
- **Test**: `test_initiative.py` (add_pc action)

### FT-407: Auto Movement Tracking

When auto-tracking is enabled, the system shall automatically deduct movement (in feet) when a token is dragged on the battle map. An undo button shall revert the token to its previous position and restore the movement. Undo shall only be available until initiative advances to the next turn.

- **Parent**: SYS-008, SYS-007
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Enable auto-tracking, drag token, verify movement deduction and undo

### FT-408: Token Status Icons on Map

The system shall display condition abbreviation badges on tokens on the battle map, linked to the combatant's conditions from initiative.

- **Parent**: SYS-007, SYS-008
- **Verification**: D
- **Status**: PLANNED

---

## 5xx: Dice Rolling & Chat

### FT-501: Manual Dice Roller

The system shall provide a dice roller supporting standard D&D dice (d4, d6, d8, d10, d12, d20, d100) with polyhedral dice shape icons.

- **Parent**: SYS-004
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_websocket_endpoint.py` (dice roll messages)

### FT-502: Shared Roll Log

The system shall broadcast dice roll results to all players in the campaign in real-time via WebSocket, displaying in a shared roll log.

- **Parent**: SYS-001
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_websocket_endpoint.py`

### FT-503: Clickable Stat Rolls

The system shall allow clicking on ability scores, saving throws, skills, attacks, and spell attacks to trigger appropriately-modified dice rolls.

- **Parent**: SYS-004
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Click STR score → d20 + STR modifier roll appears in log

### FT-504: Whisper/Secret Rolls

The system shall support whisper rolls that are visible only to the DM and the rolling player. Whispered messages shall display with a distinct visual treatment (purple banner). Chat messages shall also support whisper mode.

- **Parent**: SYS-001, SYS-003
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_whisper.py`

### FT-505: Chat Messaging

The system shall support real-time text chat within a campaign session, broadcast via WebSocket.

- **Parent**: SYS-001
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_websocket_endpoint.py` (chat messages)

---

## 6xx: Battle Maps

### FT-601: Map CRUD

The system shall allow the DM to create, read, update, and delete battle maps with configurable grid dimensions, grid size, and optional background image.

- **Parent**: SYS-007
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_maps.py`

### FT-602: Map Activation

The system shall support activating one map at a time per campaign, visible to all players. Only the DM shall be able to activate/deactivate maps.

- **Parent**: SYS-007, SYS-003
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_maps.py`

### FT-603: Token Placement & Movement

The system shall allow placing tokens on the map grid and moving them via drag-and-drop. Tokens shall snap to grid cells. The DM can move any token; players can move only their own character's token.

- **Parent**: SYS-007
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_maps.py::test_player_can_move_own_token`, `test_maps.py::test_player_cannot_move_other_token`

### FT-604: Fog of War

The system shall provide a fog of war system where the DM can reveal and hide grid cells. Players shall only see revealed areas. Fog state shall be persisted and synchronized in real-time.

- **Parent**: SYS-007, SYS-003
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_maps.py` (fog endpoints), D: real-time fog sync between DM and player

### FT-605: Zoom & Pan

The system shall support zoom (mouse wheel) and pan (middle-click drag) on the battle map canvas.

- **Parent**: SYS-007
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Scroll to zoom, middle-click to pan

### FT-606: Distance Measurement

The system shall provide a measurement mode where click-drag draws a line showing distance in feet using D&D 5e diagonal rules (alternating 5ft/10ft). Each map shall have a configurable `feet_per_cell` (default 5).

- **Parent**: SYS-007
- **Verification**: D, T
- **Status**: IMPLEMENTED
- **Demo**: Toggle measure mode, click-drag to see distance

### FT-607: Token Size Support

The system shall render tokens at appropriate sizes: Medium (1x1), Large (2x2), Huge (3x3), Gargantuan (4x4).

- **Parent**: SYS-007
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Create Large+ token via custom token panel, verify multi-cell rendering

### FT-608: Custom Token Creation

The system shall allow the DM to create custom tokens with a name, color, and size for monsters/NPCs not in initiative.

- **Parent**: SYS-007
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Use TokenPanel to add custom token

### FT-609: Token HP Ring

The system shall display an HP ring around tokens that have associated combatant data. The DM shall see HP rings on all tokens; players shall see HP rings only on their own character's token.

- **Parent**: SYS-007, SYS-003
- **Verification**: D
- **Status**: IMPLEMENTED
- **Demo**: Verify DM sees all HP rings, player sees only their own

---

## 7xx: Notes & Journal

### FT-701: Note CRUD

The system shall allow creating, reading, updating, and deleting campaign notes with title and content.

- **Parent**: SYS-002
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_notes.py`

### FT-702: Note Visibility

Notes shall support public and private visibility. Public notes are visible to all campaign members. Private notes are visible only to the author, except the DM who can see all notes.

- **Parent**: SYS-003
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_notes.py`

---

## 8xx: Real-Time Communication

### FT-801: WebSocket Connection

The system shall establish WebSocket connections per campaign session with auto-reconnection (max 5 attempts).

- **Parent**: SYS-001, SYS-012
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_websocket_endpoint.py`, `test_websocket_stress.py`

### FT-802: Campaign Room Broadcasting

The system shall broadcast messages to all connected users in a campaign room, with support for targeted messages (whisper to specific user/DM).

- **Parent**: SYS-001
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_websocket_endpoint.py`, `test_whisper.py`

### FT-803: Real-Time State Sync

The system shall synchronize initiative changes, map updates (token moves, fog changes), and dice rolls across all connected clients in real-time.

- **Parent**: SYS-001
- **Verification**: T, D
- **Status**: VERIFIED
- **Test**: `test_websocket_endpoint.py`, D: multi-tab testing

### FT-804: WebSocket Stress Resilience

The system shall handle 50 concurrent WebSocket connections and 1000-event sessions without connection failures or memory leaks.

- **Parent**: SYS-012
- **Verification**: T
- **Status**: VERIFIED
- **Test**: `test_websocket_stress.py`

---

## 9xx: Data & SRD Content

### FT-901: SRD Spells Library

The system shall provide a searchable library of ~300 SRD 5.1 spells with name, level, school, casting time, range, components, duration, and description.

- **Parent**: SYS-009, SYS-011
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `frontend/src/data/srd-spells.json`

### FT-902: SRD Weapons Library

The system shall provide SRD weapons data including name, damage dice, damage type, properties, and weight.

- **Parent**: SYS-009, SYS-011
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `frontend/src/data/srd-weapons.json`

### FT-903: SRD Monsters Library

The system shall provide SRD monster data including name, size, type, AC, HP, speed, abilities, CR, and attacks for at least 10 common creatures.

- **Parent**: SYS-009, SYS-011
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `frontend/src/data/srd-monsters.json`

### FT-904: SRD Class Data

The system shall provide class data including hit dice, spell slots per level, ASI levels, and spellcaster status for all SRD classes.

- **Parent**: SYS-009, SYS-011
- **Verification**: I
- **Status**: VERIFIED
- **Inspection**: `frontend/src/data/srd-class-data.json`

---

## Planned Features (Status: PLANNED)

### FT-410: Token Status Icons on Map (Phase 4.5)

The system shall display condition icons on battle map tokens, linked to the combatant's conditions from initiative.

- **Parent**: SYS-007, SYS-008
- **Verification**: D
- **Status**: PLANNED

### FT-610: Area of Effect Templates (Phase 6.1)

The system shall provide AoE templates (circle, cone, line, cube) that overlay affected grid cells and auto-detect tokens within the area.

- **Parent**: SYS-007
- **Verification**: D, T
- **Status**: PLANNED

### FT-611: Drawing Tools (Phase 6.2)

The system shall provide DM drawing tools (freehand, line, rectangle, circle, text) on a layer between the background and tokens.

- **Parent**: SYS-007
- **Verification**: D
- **Status**: PLANNED

### FT-905: Expanded Monster Library (Phase 5.1)

The system shall expand the SRD monster library to 50-80 creatures covering CR 0-20 with special abilities.

- **Parent**: SYS-009
- **Verification**: I
- **Status**: PLANNED
