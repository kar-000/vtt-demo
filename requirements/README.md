# Requirements Management System

## Overview

This directory contains the formal requirements for the D&D 5e Virtual Tabletop (VTT) project. Requirements are organized in a multi-level hierarchy, mapped to verification methods, and tracked to implementation/verification status.

**A requirement is NOT considered implemented until it passes its defined verification method(s) in a release verification run.**

## Hierarchy

| Level | Prefix | Scope | Example |
|-------|--------|-------|---------|
| L0 | `SYS-` | System-level capabilities | "The system shall support real-time multiplayer sessions" |
| L1 | `FT-` | Feature-level functionality | "The system shall provide an initiative tracker with turn ordering" |
| L2 | `CMP-` | Component-level behavior | "The HP bar shall display red when HP < 25%" |

Each lower level traces upward. Every L2 requirement maps to an L1 parent, every L1 maps to an L0 parent.

## Verification Methods

Each requirement is assigned one or more verification methods:

| Code | Method | Description |
|------|--------|-------------|
| **T** | Test | Automated test (pytest, vitest) that exercises the requirement |
| **D** | Demonstration | Manual walkthrough confirming behavior (documented steps) |
| **I** | Inspection | Code review / static analysis confirming implementation |
| **A** | Analysis | Design document or architecture review |

## Requirement Status

| Status | Meaning |
|--------|---------|
| `VERIFIED` | Code exists AND verification method(s) pass in CI |
| `IMPLEMENTED` | Code exists but not yet verified through release check |
| `PARTIAL` | Some sub-requirements verified, others pending |
| `PLANNED` | In roadmap, no code yet |
| `N/A` | Not applicable to current release |

## Files

| File | Contents |
|------|----------|
| [L0-system.md](L0-system.md) | System-level requirements (SYS-xxx) |
| [L1-features.md](L1-features.md) | Feature-level requirements (FT-xxx) |
| [L2-components.md](L2-components.md) | Component-level requirements (CMP-xxx) |
| [verification-matrix.md](verification-matrix.md) | Full traceability matrix: requirement → method → test/demo → status |

## Release Verification

The GitHub Actions workflow `.github/workflows/release-verification.yml` runs on every release tag and:

1. Executes all automated tests (`pytest`, frontend build)
2. Parses test results to determine which `T`-method requirements pass
3. Cross-references against the verification matrix
4. Generates a **Requirements Coverage Report** as a release artifact
5. Reports percentage of VERIFIED vs total requirements
6. Fails the release if any regression (previously VERIFIED requirement now failing)

### How to Verify a Requirement

1. **For T (Test)**: Add/identify the test file and test name in the verification matrix. The release workflow will check that the test passes.
2. **For D (Demonstration)**: Document the manual steps in the verification matrix. A human must sign off during release review.
3. **For I (Inspection)**: Reference the file and line range. Code review during PR confirms.
4. **For A (Analysis)**: Reference the design document or architectural decision record.

## Adding New Requirements

1. Assign the next available ID in the appropriate level file
2. Write the requirement using "shall" language (testable, unambiguous)
3. Assign verification method(s)
4. Add an entry to the verification matrix
5. Set status to `PLANNED`
6. When code is written, update to `IMPLEMENTED`
7. When verification passes in CI, update to `VERIFIED`

## ID Numbering

- `SYS-001` through `SYS-099`: System requirements
- `FT-1xx`: Authentication & Users
- `FT-2xx`: Campaign Management
- `FT-3xx`: Character Management
- `FT-4xx`: Combat & Initiative
- `FT-5xx`: Dice Rolling & Chat
- `FT-6xx`: Battle Maps
- `FT-7xx`: Notes & Journal
- `FT-8xx`: Real-time Communication
- `FT-9xx`: Data & SRD Content
- `CMP-xxx`: Component requirements (numbered sequentially, grouped by parent FT)
