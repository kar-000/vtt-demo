# Verification Matrix

Full traceability from requirement → verification method → specific test/artifact → status.

**Legend**: T=Test, D=Demonstration, I=Inspection, A=Analysis

---

## L0: System Requirements

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| SYS-001 | Real-time multiplayer sessions | T, D | `test_websocket_endpoint.py`, `test_websocket_stress.py`; D: 2-tab test | VERIFIED |
| SYS-002 | Persistent game state | T | `test_campaigns.py`, `test_hp_management.py`, `test_maps.py`, `test_notes.py` | VERIFIED |
| SYS-003 | Role-based access (DM/Player) | T | `test_dm_capabilities.py`, `test_auth.py`, `test_maps.py` (ownership) | VERIFIED |
| SYS-004 | D&D 5e rules compliance | T, I | `test_hp_management.py`, `test_initiative.py`, `test_verification.py`; I: SRD data files | VERIFIED |
| SYS-005 | Web-based accessibility | D | D: Open in Chrome/Firefox, no plugins needed | VERIFIED |
| SYS-006 | Authentication & security | T | `test_auth.py`, `test_jwt.py` | VERIFIED |
| SYS-007 | Visual battle map | T, D | `test_maps.py` (40 tests), `test_verification.py::TestDistanceMeasurement`; D: grid, tokens, fog | VERIFIED |
| SYS-008 | Automated combat tracking | T, D | `test_initiative.py`, `test_dice_coverage.py`, `test_verification.py::TestMovementTracking`; D: full combat round | VERIFIED |
| SYS-009 | SRD content library | I | I: `srd-spells.json`, `srd-weapons.json`, `srd-monsters.json`, `srd-class-data.json` | VERIFIED |
| SYS-010 | Code quality & CI/CD | T, I | `pr-checks.yml` (90% coverage gate), `quality.yml`; I: pre-commit config | VERIFIED |
| SYS-011 | OGL compliance | I | I: LICENSE file in repo | VERIFIED |
| SYS-012 | Session stability (4h, 5 users) | T, D | `test_websocket_stress.py` (50 connections, 1000 events); D: extended session pending | PARTIAL |

---

## L1: Feature Requirements — Authentication & Users (1xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-101 | User registration | T | `test_auth.py::test_register_user`, `test_auth.py::test_register_duplicate_username` | VERIFIED |
| FT-102 | User login with JWT | T | `test_auth.py::test_login_user`, `test_jwt.py` (10 tests) | VERIFIED |
| FT-103 | DM vs Player roles | T | `test_dm_capabilities.py` | VERIFIED |

## L1: Campaign Management (2xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-201 | Campaign CRUD | T | `test_campaigns.py::TestCampaignCreate`, `TestCampaignGet`, `TestCampaignUpdate`, `TestCampaignDelete` | VERIFIED |
| FT-202 | Campaign join | T | `test_campaigns.py::TestCampaignJoin` | VERIFIED |
| FT-203 | Campaign settings persistence | T | `test_initiative.py` (settings survive reconnect) | VERIFIED |

## L1: Character Management (3xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-301 | Character creation | T | `test_auth.py::test_create_character_with_valid_token` | VERIFIED |
| FT-302 | HP management | T | `test_hp_management.py` (15 tests) | VERIFIED |
| FT-303 | Attacks system | T | `test_hp_management.py`, `test_verification.py::TestAttacksSystem` | VERIFIED |
| FT-304 | Spells system | T | `test_hp_management.py`, `test_verification.py::TestSpellsSystem` | VERIFIED |
| FT-305 | Level-up system | T | `test_verification.py::TestLevelUp` (6 tests) | VERIFIED |
| FT-306 | Character export/import | T | `test_campaigns.py` (export/import) | VERIFIED |
| FT-307 | Character portraits | T | `test_verification.py::TestCharacterPortraits` (3 tests) | VERIFIED |
| FT-308 | Ability score details | T | `test_verification.py::TestAbilityScores` (2 tests) | VERIFIED |
| FT-309 | Multiclass support | T | `test_verification.py::TestMulticlass` (2 tests) | VERIFIED |
| FT-310 | DM character management | T | `test_dm_capabilities.py::TestDMAllCharacters`, `TestDMEditCharacters` | VERIFIED |

## L1: Combat & Initiative (4xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-401 | Initiative tracker | T | `test_initiative.py` (18+ tests) | VERIFIED |
| FT-402 | Action economy tracking | T | `test_dice_coverage.py::TestActionEconomy` (5 tests) | VERIFIED |
| FT-403 | Monster stat blocks | T | `test_verification.py::TestMonsterStatBlocks` (3 tests), `test_dice_coverage.py` (update_npc) | VERIFIED |
| FT-404 | Conditions & status effects | T | `test_initiative.py::TestConditions`, `test_dice_coverage.py::TestConditions` | VERIFIED |
| FT-405 | Advantage/disadvantage | T | `test_dice_coverage.py::TestAdvantageDisadvantage` (4 tests) | VERIFIED |
| FT-406 | PC re-add to initiative | T | `test_dice_coverage.py::test_add_pc_after_removal`, `test_add_pc_no_duplicate`, `test_add_pc_with_initiative_value`, `test_add_pc_nonexistent_character` | VERIFIED |
| FT-407 | Auto movement tracking | T | `test_verification.py::TestMovementTracking` (4 tests) | VERIFIED |
| FT-408 | Token status icons on map | D | D: conditions display on map tokens | PLANNED |

## L1: Dice Rolling & Chat (5xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-501 | Manual dice roller | T | `test_websocket_endpoint.py::TestDiceRollMessages` | VERIFIED |
| FT-502 | Shared roll log | T | `test_websocket_endpoint.py` | VERIFIED |
| FT-503 | Clickable stat rolls | T | `test_verification.py::TestDiceRollWithModifier` (2 tests) | VERIFIED |
| FT-504 | Whisper/secret rolls | T | `test_whisper.py` (8 tests) | VERIFIED |
| FT-505 | Chat messaging | T | `test_websocket_endpoint.py` (chat messages) | VERIFIED |

## L1: Battle Maps (6xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-601 | Map CRUD | T | `test_maps.py::TestMapCRUD` | VERIFIED |
| FT-602 | Map activation | T | `test_maps.py::TestMapActivation` | VERIFIED |
| FT-603 | Token placement & movement | T | `test_maps.py::TestTokenOperations` (16 tests), `test_player_can_move_own_token` | VERIFIED |
| FT-604 | Fog of war | T | `test_maps.py::TestFogOfWar` (9 tests) | VERIFIED |
| FT-605 | Zoom & pan | D | D: scroll zoom, middle-click pan | IMPLEMENTED |
| FT-606 | Distance measurement | T, A | `test_verification.py::TestDistanceMeasurement`, `TestMapFeetPerCellUpdate`; A: `calculateDistance()` | VERIFIED |
| FT-607 | Token size support | D | D: create Large+ token, verify multi-cell rendering | IMPLEMENTED |
| FT-608 | Custom token creation | D | D: TokenPanel custom form | IMPLEMENTED |
| FT-609 | Token HP ring | D | D: DM sees all HP rings, player sees only own | IMPLEMENTED |

## L1: Notes & Journal (7xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-701 | Note CRUD | T | `test_notes.py` (25+ tests) | VERIFIED |
| FT-702 | Note visibility | T | `test_notes.py::TestNotesVisibility`, `TestNotesAuthorization` | VERIFIED |

## L1: Real-Time Communication (8xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-801 | WebSocket connection | T | `test_websocket_endpoint.py`, `test_websocket_stress.py` | VERIFIED |
| FT-802 | Campaign room broadcasting | T | `test_websocket_endpoint.py`, `test_whisper.py` | VERIFIED |
| FT-803 | Real-time state sync | T | `test_websocket_endpoint.py` (initiative, map, dice sync) | VERIFIED |
| FT-804 | WebSocket stress resilience | T | `test_websocket_stress.py` (50 concurrent, 1000 events) | VERIFIED |

## L1: Data & SRD Content (9xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-901 | SRD spells library | I | `frontend/src/data/srd-spells.json` (~300 spells) | VERIFIED |
| FT-902 | SRD weapons library | I | `frontend/src/data/srd-weapons.json` | VERIFIED |
| FT-903 | SRD monsters library | I | `frontend/src/data/srd-monsters.json` (10 creatures) | VERIFIED |
| FT-904 | SRD class data | I | `frontend/src/data/srd-class-data.json` (12 classes) | VERIFIED |

## L1: Planned Features

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-410 | Token status icons on map | D | — | PLANNED |
| FT-610 | Area of effect templates | D, T | — | PLANNED |
| FT-611 | Drawing tools | D | — | PLANNED |
| FT-905 | Expanded monster library | I | — | PLANNED |

---

## L2: Component Requirements

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| CMP-001 | Password hashing (pbkdf2_sha256) | I | `backend/app/routes/auth.py` | VERIFIED |
| CMP-002 | JWT token structure (string sub) | T | `test_jwt.py` | VERIFIED |
| CMP-003 | Protected endpoints (401) | T | `test_auth.py::test_protected_endpoint_no_token` | VERIFIED |
| CMP-010 | HP bar color coding | I | I: `HPManager.jsx` (color thresholds in render logic) | VERIFIED |
| CMP-011 | Death saving throws | T | `test_hp_management.py` | VERIFIED |
| CMP-012 | Temp HP behavior | T | `test_hp_management.py` | VERIFIED |
| CMP-013 | SRD weapons modal | T, I | `test_verification.py::TestAttacksSystem`; I: `srd-weapons.json`, `AttacksSection.jsx` | VERIFIED |
| CMP-014 | Spell slot tracking | T | `test_verification.py::TestSpellsSystem::test_spell_slot_consumption` | VERIFIED |
| CMP-015 | Spell save DC calculation | T | `test_verification.py::TestSpellsSystem::test_spell_save_dc_stored` | VERIFIED |
| CMP-016 | Level-up HP options | T | `test_verification.py::TestLevelUp::test_level_up_with_hp_increase` | VERIFIED |
| CMP-017 | ASI at appropriate levels | T | `test_verification.py::TestLevelUp::test_level_up_with_ability_score_increase`, `test_ability_score_cannot_exceed_20_via_update` | VERIFIED |
| CMP-018 | Portrait upload validation | T | `test_verification.py::TestCharacterPortraits` (create, update, remove) | VERIFIED |
| CMP-019 | Portrait display locations | D | D: verify portrait in sheet header + initiative tracker + initials fallback | IMPLEMENTED |
| CMP-030 | Initiative ordering | T | `test_initiative.py` | VERIFIED |
| CMP-031 | Turn advancement | T | `test_initiative.py` | VERIFIED |
| CMP-032 | Action economy reset | T | `test_initiative.py` | VERIFIED |
| CMP-033 | Condition duration tick | T | `test_initiative.py` | VERIFIED |
| CMP-034 | Condition badge display | I | I: `ConditionManager.jsx`, `InitiativeTracker.jsx` (badge rendering) | VERIFIED |
| CMP-035 | Advantage roll mechanics | T | `test_dice_coverage.py::TestAdvantageDisadvantage` (rolls 2d20, selects correct) | VERIFIED |
| CMP-036 | Monster HP controls | T | `test_verification.py::TestMonsterStatBlocks::test_update_monster_hp_damage`, `test_monster_hp_cannot_go_negative` | VERIFIED |
| CMP-037 | Movement auto-deduction | T | `test_verification.py::TestMovementTracking::test_use_movement_deducts`, `test_use_movement_cannot_go_negative` | VERIFIED |
| CMP-038 | Movement undo | T | `test_verification.py::TestMovementTracking::test_restore_movement`, `test_restore_movement_capped_at_max` | VERIFIED |
| CMP-050 | Grid rendering | T | `test_maps.py` (map creation with grid params) | VERIFIED |
| CMP-051 | Token snap-to-grid | D | D: drag token, release between cells, verify snap | IMPLEMENTED |
| CMP-052 | Player token ownership | T | `test_maps.py::test_player_can_move_own_token`, `test_player_cannot_move_other_token` | VERIFIED |
| CMP-053 | Fog cell reveal/hide | T | `test_maps.py::TestFogOfWar` | VERIFIED |
| CMP-054 | Fog player view | D | D: player sees opaque overlay, DM sees translucent | IMPLEMENTED |
| CMP-055 | Zoom bounds (0.25x-3x) | I | I: `BattleMap.jsx` (zoom clamp logic) | VERIFIED |
| CMP-056 | D&D diagonal distance | T, A | `test_verification.py::TestDistanceMeasurement::test_dnd_diagonal_distance_calculation`; A: `calculateDistance()` | VERIFIED |
| CMP-057 | Measurement line rendering | D | D: activate measure mode, click-drag, verify dashed line + label | IMPLEMENTED |
| CMP-058 | Token drag distance display | D | D: drag token, verify trail line + ft label | IMPLEMENTED |
| CMP-070 | Note visibility enforcement | T | `test_notes.py::TestNotesVisibility` | VERIFIED |
| CMP-071 | Notes sidebar tabs | I | I: `Game.jsx` (sidebar tab rendering), `NotesSection.jsx` | VERIFIED |
| CMP-080 | Auto-reconnection (5 attempts) | I | `frontend/src/services/websocket.js` (reconnection logic) | VERIFIED |
| CMP-081 | Listener cleanup | I | `frontend/src/services/websocket.js` (`this.listeners` clearing) | VERIFIED |
| CMP-082 | JSON field mutation safety | I | All routes using `flag_modified()` | VERIFIED |
| CMP-083 | Concurrent connection handling | T | `test_websocket_stress.py` (50 connections) | VERIFIED |
| CMP-090 | Theme support (3 themes) | I | I: `ThemeSwitcher.jsx`, `ThemeContext.jsx`, CSS custom properties | VERIFIED |
| CMP-091 | Responsive layout | D | D: resize browser, verify layout adapts | IMPLEMENTED |
| CMP-092 | Polyhedral dice icons | I | I: `DiceRoller.jsx` (SVG/CSS dice shapes) | VERIFIED |

---

## Coverage Summary

| Status | L0 | L1 | L2 | Total |
|--------|----|----|-----|-------|
| VERIFIED | 10 | 39 | 37 | **86** |
| IMPLEMENTED | 0 | 3 | 5 | **8** |
| PARTIAL | 1 | 0 | 0 | **1** |
| PLANNED | 0 | 4 | 0 | **4** |
| **Total** | **11** | **46** | **42** | **99** |

**Verification Rate**: 86/95 active requirements = **91%** (excluding PLANNED)

### Remaining IMPLEMENTED (8 requirements needing verification)

These are purely frontend rendering behaviors with no backend-testable aspect:

| Req ID | Description | Path to Verification |
|--------|-------------|---------------------|
| FT-605 | Zoom & pan | Integration test (Playwright) |
| FT-607 | Token size support (multi-cell render) | Integration test (Playwright) |
| FT-608 | Custom token creation form | Integration test (Playwright) |
| FT-609 | Token HP ring (DM vs player view) | Integration test (Playwright) |
| CMP-019 | Portrait display in sheet + initiative | Integration test (Playwright) |
| CMP-051 | Token snap-to-grid | Integration test (Playwright) |
| CMP-054 | Fog player view (opaque vs translucent) | Integration test (Playwright) |
| CMP-091 | Responsive layout | Integration test (Playwright) |

### Remaining PARTIAL (1 requirement)

| Req ID | Description | Gap |
|--------|-------------|-----|
| SYS-012 | Session stability (4h, 5 users) | Stress tests pass but no real-world 4+ hour session test |
