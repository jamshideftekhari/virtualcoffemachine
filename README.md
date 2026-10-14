# Virtual Coffee Machine

A software **digital twin** of an automatic coffee machine, designed as a learning and validation vehicle before hardware implementation. Built with **Domain-Driven Design** principles and a **Ports & Adapters** (hexagonal) architecture.

---

## Architecture

```
Driving adapters          Hexagon                    Driven adapters
(inbound)                 (domain + application)     (outbound)

Customer API  ──────────► BrewBeverage          ────► ContainerRepository
Operator API  ──────────► FillContainer         ────► ConfigurationPort
Config API    ──────────► ApplyConfiguration    ────► AlertPort
```

The domain layer has **zero framework dependencies** — plain Python dataclasses, enums, and exceptions. Adapters are swapped without touching the domain.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.12 |
| API | FastAPI + Pydantic v2 |
| Port interfaces | `typing.Protocol` |
| Domain models | `dataclass` |
| Prototype persistence | In-memory |
| Tests | pytest + httpx |

---

## Project Structure

```
virtualcoffeemachine/
├── domain/
│   ├── model/
│   │   ├── value_objects.py      # ContainerId, Quantity, MachineState, …
│   │   ├── container.py          # Container aggregate
│   │   ├── waste_container.py    # WasteContainer aggregate
│   │   ├── recipe.py             # Recipe + RecipeRequirement
│   │   ├── machine.py            # CoffeeMachine FSM
│   │   └── brew_order.py         # BrewOrder lifecycle
│   ├── events.py                 # Domain event dataclasses
│   └── exceptions.py             # Domain exceptions
│
├── application/
│   ├── ports/
│   │   ├── container_repository.py   # Protocol
│   │   ├── configuration_port.py     # Protocol
│   │   └── alert_port.py             # Protocol
│   └── use_cases/
│       ├── results.py                # View / result dataclasses
│       ├── brew_beverage.py
│       ├── fill_container.py
│       ├── empty_waste.py
│       ├── apply_configuration.py
│       ├── get_container_state.py
│       └── get_active_configuration.py
│
├── adapters/                     # (next milestone)
│   ├── inbound/api/              # FastAPI routers
│   └── outbound/                 # In-memory repos, default config, log alerts
│
├── config/
│   └── default_config.json       # Default recipes and thresholds
│
├── docs/
│   ├── requirements-v1.md
│   ├── requirements-v2.md
│   └── system-design-v1.md
│
├── tests/
│   ├── unit/                     # Domain and use case tests (no framework)
│   └── integration/              # Full-stack tests via httpx
│
└── main.py                       # FastAPI app + dependency wiring
```

---

## Getting Started

### Prerequisites
- Python 3.12+

### Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install fastapi uvicorn pydantic
pip install pytest httpx          # for tests
```

### Run (once adapters are wired)

```bash
uvicorn main:app --reload
```

API docs will be available at `http://localhost:8000/docs`.

---

## Key Design Decisions

| Decision | Choice |
|---|---|
| Port interfaces | `typing.Protocol` — no forced inheritance, stubs are plain classes |
| Domain events | Returned as values by aggregates, dispatched by use cases |
| Machine state | `CoffeeMachine` FSM enforces valid transitions via a frozenset |
| Waste tracking | By brew count, not volume (configurable threshold) |
| Config fallback | Default config always present; remote config is additive |
| Mid-brew exhaustion | Brew stops, machine → ERROR, operator must fill to recover |

---

## Domain Concepts

| Term | Meaning |
|---|---|
| **Container** | Holds one ingredient (water, coffee A/B, milk, cacao) |
| **Waste container** | Tracks used grounds/liquids by brew count |
| **Recipe** | Ingredient amounts for one beverage serving |
| **BrewOrder** | Lifecycle of a single brew request |
| **CoffeeMachine** | The state FSM (IDLE → READY → BREWING → READY / ERROR) |

See [`docs/requirements-v2.md`](docs/requirements-v2.md) for full requirements and scenarios.
See [`docs/system-design-v1.md`](docs/system-design-v1.md) for architecture detail and ADRs.
