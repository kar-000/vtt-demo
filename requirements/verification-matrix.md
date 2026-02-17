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
| SYS-004 | D&D 5e rules compliance | T, I | `test_hp_management.py`, `test_initiative.py`; I: SRD data files | PARTIAL |
| SYS-005 | Web-based accessibility | D | D: Open in Chrome/Firefox, no plugins needed | VERIFIED |
| SYS-006 | Authentication & security | T | `test_auth.py`, `test_jwt.py` | VERIFIED |
| SYS-007 | Visual battle map | T, D | `test_maps.py` (40 tests); D: grid, tokens, fog, measure | PARTIAL |
| SYS-008 | Automated combat tracking | T, D | `test_initiative.py`, `test_dice_coverage.py`; D: full combat round | PARTIAL |
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
| FT-303 | Attacks system | T, D | `test_hp_management.py` (attack data); D: click-to-roll | VERIFIED |
| FT-304 | Spells system | T, D | `test_hp_management.py` (spell data); D: slot tracking | VERIFIED |
| FT-305 | Level-up system | D | D: 4-step LevelUpModal wizard | IMPLEMENTED |
| FT-306 | Character export/import | T | `test_campaigns.py` (export/import) | VERIFIED |
| FT-307 | Character portraits | D, I | D: upload/display; I: `CharacterPortrait.jsx` | IMPLEMENTED |
| FT-308 | Ability score details | D | D: expand ability cards | IMPLEMENTED |
| FT-309 | Multiclass support | D | D: level up into second class | IMPLEMENTED |
| FT-310 | DM character management | T | `test_dm_capabilities.py::TestDMAllCharacters`, `TestDMEditCharacters` | VERIFIED |

## L1: Combat & Initiative (4xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-401 | Initiative tracker | T | `test_initiative.py` (18+ tests) | VERIFIED |
| FT-402 | Action economy tracking | T, D | `test_dice_coverage.py::TestActionEconomy` (5 tests); D: UI toggles | VERIFIED |
| FT-403 | Monster stat blocks | D | D: add SRD monster, use HP/attack controls | IMPLEMENTED |
| FT-404 | Conditions & status effects | T | `test_initiative.py::TestConditions`, `test_dice_coverage.py::TestConditions` | VERIFIED |
| FT-405 | Advantage/disadvantage | T, D | `test_dice_coverage.py::TestAdvantageDisadvantage` (4 tests); D: toggle ADV/DIS | IMPLEMENTED |
| FT-406 | PC re-add to initiative | T | `test_initiative.py` (add_pc action) | IMPLEMENTED |
| FT-407 | Auto movement tracking | D | D: enable auto, drag token, verify deduction and undo | IMPLEMENTED |
| FT-408 | Token status icons on map | D | D: conditions display on map tokens | PLANNED |

## L1: Dice Rolling & Chat (5xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-501 | Manual dice roller | T, D | `test_websocket_endpoint.py::TestDiceRollMessages`; D: all die types | VERIFIED |
| FT-502 | Shared roll log | T | `test_websocket_endpoint.py` | VERIFIED |
| FT-503 | Clickable stat rolls | D | D: click STR → d20+mod in log | IMPLEMENTED |
| FT-504 | Whisper/secret rolls | T | `test_whisper.py` (8 tests) | VERIFIED |
| FT-505 | Chat messaging | T | `test_websocket_endpoint.py` (chat messages) | VERIFIED |

## L1: Battle Maps (6xx)

| Req ID | Requirement | Method | Verification Artifact | Status |
|--------|-------------|--------|----------------------|--------|
| FT-601 | Map CRUD | T | `test_maps.py::TestMapCRUD` | VERIFIED |
| FT-602 | Map activation | T | `test_maps.py::TestMapActivation` | VERIFIED |
| FT-603 | Token placement & movement | T | `test_maps.py::TestTokenOperations` (16 tests), `test_player_can_move_own_token` | VERIFIED |
| FT-604 | Fog of war | T, D | `test_maps.py::TestFogOfWar` (9 tests); D: real-time fog sync | VERIFIED |
| FT-605 | Zoom & pan | D | D: scroll zoom, middle-click pan | IMPLEMENTED |
| FT-606 | Distance measurement | D, A | D: measure mode; A: `calculateDistance()` in BattleMap.jsx | IMPLEMENTED |
| FT-607 | Token size support | D | D: create Large+ token | IMPLEMENTED |
| FT-608 | Custom token creation | D | D: TokenPanel custom form | IMPLEMENTED |
| FT-609 | Token HP ring | D | D: DM sees all, player sees own | IMPLEMENTED |

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
| FT-803 | Real-time state sync | T, D | `test_websocket_endpoint.py`; D: multi-tab test | VERIFIED |
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
| CMP-010 | HP bar color coding | D | D: damage through thresholds | IMPLEMENTED |
| CMP-011 | Death saving throws | T | `test_hp_management.py` | VERIFIED |
| CMP-012 | Temp HP behavior | T | `test_hp_management.py` | VERIFIED |
| CMP-013 | SRD weapons modal | D | D: open modal, select weapon | IMPLEMENTED |
| CMP-014 | Spell slot tracking | D | D: cast spell, verify decrement | IMPLEMENTED |
| CMP-015 | Spell save DC calculation | D, I | I: `SpellsSection.jsx` | IMPLEMENTED |
| CMP-016 | Level-up HP options | D | D: roll vs average | IMPLEMENTED |
| CMP-017 | ASI at appropriate levels | D, I | I: `srd-class-data.json`, `LevelUpModal.jsx` | IMPLEMENTED |
| CMP-018 | Portrait upload validation | D | D: valid image → ok, PDF → reject | IMPLEMENTED |
| CMP-019 | Portrait display locations | D | D: sheet + initiative + fallback | IMPLEMENTED |
| CMP-030 | Initiative ordering | T | `test_initiative.py` | VERIFIED |
| CMP-031 | Turn advancement | T | `test_initiative.py` | VERIFIED |
| CMP-032 | Action economy reset | T | `test_initiative.py` | VERIFIED |
| CMP-033 | Condition duration tick | T | `test_initiative.py` | VERIFIED |
| CMP-034 | Condition badge display | D | D: apply condition, verify badge | IMPLEMENTED |
| CMP-035 | Advantage roll mechanics | D | D: toggle ADV, verify 2d20 | IMPLEMENTED |
| CMP-036 | Monster HP controls | D | D: +/- buttons, verify bounds | IMPLEMENTED |
| CMP-037 | Movement auto-deduction | D | D: drag 3 cells, verify 15ft deducted | IMPLEMENTED |
| CMP-038 | Movement undo | D | D: undo restores position + movement | IMPLEMENTED |
| CMP-050 | Grid rendering | T, D | `test_maps.py`; D: visible grid lines | VERIFIED |
| CMP-051 | Token snap-to-grid | D | D: drag and release between cells | IMPLEMENTED |
| CMP-052 | Player token ownership | T | `test_maps.py::test_player_can_move_own_token`, `test_player_cannot_move_other_token` | VERIFIED |
| CMP-053 | Fog cell reveal/hide | T, D | `test_maps.py::TestFogOfWar`; D: real-time sync | VERIFIED |
| CMP-054 | Fog player view | D | D: player sees opaque, DM sees translucent | IMPLEMENTED |
| CMP-055 | Zoom bounds (0.25x–3x) | D | D: zoom to limits | IMPLEMENTED |
| CMP-056 | D&D diagonal distance | D, A | D: 2 diag = 15ft; A: `calculateDistance()` | IMPLEMENTED |
| CMP-057 | Measurement line rendering | D | D: dashed line + label | IMPLEMENTED |
| CMP-058 | Token drag distance display | D | D: trail line + ft label | IMPLEMENTED |
| CMP-070 | Note visibility enforcement | T | `test_notes.py::TestNotesVisibility` | VERIFIED |
| CMP-071 | Notes sidebar tabs | D | D: click tab, verify CRUD | IMPLEMENTED |
| CMP-080 | Auto-reconnection (5 attempts) | I | `frontend/src/services/websocket.js` | VERIFIED |
| CMP-081 | Listener cleanup | I | `frontend/src/services/websocket.js` | VERIFIED |
| CMP-082 | JSON field mutation safety | I | All routes using `flag_modified()` | VERIFIED |
| CMP-083 | Concurrent connection handling | T | `test_websocket_stress.py` (50 connections) | VERIFIED |
| CMP-090 | Theme support (3 themes) | D | D: switch themes, verify visuals | IMPLEMENTED |
| CMP-091 | Responsive layout | D | D: resize browser window | IMPLEMENTED |
| CMP-092 | Polyhedral dice icons | D | D: open dice roller, verify icons | IMPLEMENTED |

---

## Coverage Summary

| Status | L0 | L1 | L2 | Total |
|--------|----|----|-----|-------|
| VERIFIED | 7 | 28 | 22 | **57** |
| IMPLEMENTED | 0 | 11 | 20 | **31** |
| PARTIAL | 4 | 0 | 0 | **4** |
| PLANNED | 0 | 4 | 0 | **4** |
| **Total** | **11** | **43** | **42** | **96** |

**Verification Rate**: 57/92 active requirements = **62%** (excluding PLANNED)

### Path to 100% Verification

Requirements with status `IMPLEMENTED` need automated tests (`T` method) or documented demonstration procedures (`D` method) run during a release check. The primary gap is frontend-only features verified by `D` (demonstration) that lack automated tests. Options:

1. **Add integration tests** (e.g., Playwright/Cypress) for D-method requirements
2. **Formalize demo scripts** as checklist items in release process
3. **Promote key D requirements to T** by adding backend test coverage where possible
