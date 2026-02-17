# L0: System-Level Requirements

These define the top-level capabilities the VTT system shall provide.

## SYS-001: Real-Time Multiplayer Sessions

The system shall support real-time multiplayer sessions where a Dungeon Master (DM) and one or more players interact simultaneously through a shared game state.

- **Verification**: T, D
- **Status**: VERIFIED
- **Traces to**: FT-801, FT-802, FT-803

## SYS-002: Persistent Game State

The system shall persist all game state (characters, campaigns, maps, combat, notes) across sessions so that users can resume play without data loss.

- **Verification**: T
- **Status**: VERIFIED
- **Traces to**: FT-201, FT-301, FT-601, FT-701

## SYS-003: Role-Based Access Control

The system shall enforce two distinct roles — Dungeon Master (DM) and Player — with appropriate permissions for each. The DM shall have elevated privileges over game state.

- **Verification**: T
- **Status**: VERIFIED
- **Traces to**: FT-101, FT-102, FT-103

## SYS-004: D&D 5e Rules Compliance

The system shall implement game mechanics consistent with the D&D 5e SRD 5.1 rules, including ability scores, hit points, armor class, attacks, spells, conditions, and initiative.

- **Verification**: T, I
- **Status**: PARTIAL
- **Traces to**: FT-301 through FT-399, FT-401 through FT-499, FT-901

## SYS-005: Web-Based Accessibility

The system shall be accessible through a modern web browser without requiring installation of additional software or plugins.

- **Verification**: D
- **Status**: VERIFIED
- **Traces to**: (Architecture)

## SYS-006: Authentication & Security

The system shall authenticate users via secure credentials and protect session data with industry-standard token-based authentication.

- **Verification**: T
- **Status**: VERIFIED
- **Traces to**: FT-101, FT-102

## SYS-007: Visual Battle Map

The system shall provide a 2D grid-based battle map for spatial combat, supporting tokens, fog of war, and distance measurement.

- **Verification**: T, D
- **Status**: PARTIAL
- **Traces to**: FT-601 through FT-699

## SYS-008: Automated Combat Tracking

The system shall automate combat bookkeeping including initiative order, turn tracking, action economy, conditions, and advantage/disadvantage.

- **Verification**: T, D
- **Status**: PARTIAL
- **Traces to**: FT-401 through FT-499

## SYS-009: SRD Content Library

The system shall provide built-in SRD 5.1 content (spells, weapons, monsters, class data) that users can reference and use during play.

- **Verification**: I, T
- **Status**: VERIFIED
- **Traces to**: FT-901, FT-902, FT-903, FT-904

## SYS-010: Code Quality & CI/CD

The system shall maintain automated test coverage (90%+ for new code), code formatting standards, and continuous integration pipelines.

- **Verification**: T, I
- **Status**: VERIFIED
- **Traces to**: (Infrastructure)

## SYS-011: Open Game License Compliance

The system shall comply with the Open Gaming License (OGL) for all SRD-derived content and include the required license text.

- **Verification**: I
- **Status**: VERIFIED
- **Traces to**: FT-901

## SYS-012: Session Stability

The system shall support sessions of 4+ hours duration for 5+ concurrent users without degradation, memory leaks, or connection failures.

- **Verification**: T, D
- **Status**: PARTIAL
- **Traces to**: FT-801, FT-804
