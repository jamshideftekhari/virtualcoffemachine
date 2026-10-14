# Bounded Contexts — Discussion & Decision

> DDD Architecture · 2026-10-14

---

## Question

> Is there only one bounded context in this design?

---

## Current State

The codebase is effectively **one bounded context**. Everything lives in a single `domain/` package. All aggregates share the same events, exceptions, and ubiquitous language — there are no explicit context boundaries.

The core / supporting / generic classification in the requirements documents describes **investment priority and team ownership**, not bounded context separation. Those are different concepts in DDD.

---

## Natural Seams

Three candidate bounded contexts emerge from the aggregate structure:

| Bounded Context | Aggregates / concepts | Language owner |
|---|---|---|
| **Machine Operation** | `Container`, `WasteContainer`, `CoffeeMachine`, `BrewOrder` | Machine / ops team |
| **Beverage & Recipe** | `Recipe`, `RecipeRequirement`, beverage menu | Product / barista |
| **Configuration** | Thresholds, remote config lifecycle | Platform / infra |

### Strongest seam: Configuration

`Configuration` has the clearest separation from the rest:
- Different lifecycle — pushed remotely, versioned externally
- Different owner — platform / infrastructure team
- Its own failure mode — fallback to default when unreachable
- The existing `ConfigurationPort` is already an **anti-corruption layer (ACL) in disguise**

### Weakest seam: Brewing vs. Container Management

`BrewBeverage` reads container levels and deducts from them directly. Splitting these two into separate contexts forces either a synchronous cross-context call or eventual consistency — real complexity with no gain at this scale.

---

## What a Two-Context Structure Would Look Like

```
virtualcoffeemachine/
├── contexts/
│   ├── machine/              ← Bounded Context 1
│   │   ├── domain/
│   │   │   ├── model/        # Container, WasteContainer, CoffeeMachine, BrewOrder
│   │   │   ├── events.py
│   │   │   └── exceptions.py
│   │   └── application/
│   │       ├── ports/
│   │       └── use_cases/
│   │
│   └── configuration/        ← Bounded Context 2
│       ├── domain/
│       │   ├── model/        # MachineConfiguration, Recipe, Threshold
│       │   ├── events.py
│       │   └── exceptions.py
│       └── application/
│           ├── ports/
│           └── use_cases/
│
└── adapters/                 ← shared, talks to both contexts
```

The `machine` context would consume recipes via a **read-only port (ACL)** backed by the `configuration` context — not by importing its domain model directly.

---

## Decision: Keep One Bounded Context (for now)

**Rationale:**
- The machine is small and the ubiquitous language is uniform across all aggregates
- The aggregates are tightly coupled by nature (brewing requires containers, containers require thresholds)
- Splitting prematurely introduces translation layers (ACL, shared kernel, or cross-context events) without a real problem to solve
- The current port-and-adapter structure already enforces the right separation of concerns within the single context

---

## When to Revisit

Split into multiple bounded contexts if any of the following occur:

| Trigger | Suggested split |
|---|---|
| A separate team owns recipe management | `machine` context + `configuration` context |
| Configuration needs its own deployment / database | `configuration` as an independent service |
| Analytics or reporting requirements emerge | New `reporting` context (read model / projections) |
| Customer loyalty or accounts are introduced | New `customer` context with its own identity model |
| Maintenance scheduling is added | New `maintenance` context with its own language |

---

## Migration Path (when the time comes)

The current structure makes a future split low-risk:

1. Move aggregates into `contexts/machine/domain/` and `contexts/configuration/domain/`
2. Replace the direct import of `Recipe` inside `BrewBeverage` with a read-only port interface
3. Implement the port with an in-process adapter (same process) or an HTTP adapter (separate service)
4. No changes to the domain logic itself — only the wiring changes

The `ConfigurationPort` already exists as the boundary; formalising it into a full bounded context is an extension of work already done.
