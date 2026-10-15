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
                                                ────► DisplayPort (Sense HAT LEDs / log)
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
│   │   ├── alert_port.py             # Protocol
│   │   └── display_port.py           # Protocol
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
│   └── outbound/                 # In-memory repos, default config, log alerts, Sense HAT display
│
├── config/
│   └── default_config.json       # Default recipes and thresholds
│
├── docs/
│   ├── requirements-v1.md
│   ├── requirements-v2.md
│   ├── system-design-v1.md
│   └── sensehat-display-design.md
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

### Run

```bash
uvicorn main:app --reload
```

The UI will be available at `http://localhost:8000/` and the API docs at `http://localhost:8000/docs`.

### Run on a local network

By default uvicorn listens on `127.0.0.1`, so only this computer can reach it. To access the machine from other computers on the same network:

1. Start the server on all network interfaces:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. Find this computer's LAN IP address (`ipconfig` on Windows, `ip addr` on Linux or `ipconfig getifaddr en0` on macOS), e.g. `192.168.1.42`.

3. On Windows, allow inbound traffic on port 8000. Run once in an admin PowerShell:

   ```powershell
   New-NetFirewallRule -DisplayName "Virtual Coffee Machine 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
   ```

   If your network is set to the **Public** profile, switch it to Private or add `Public` to `-Profile`.

4. From another computer, open `http://192.168.1.42:8000/` (UI) or `http://192.168.1.42:8000/docs` (API docs).

### Raspberry Pi Sense HAT display

On a Raspberry Pi with a Sense HAT, the 8x8 LED matrix shows the machine status:

| Situation | Icon | Text |
|---|---|---|
| Ready (waiting for an order) | Coffee machine with blinking power LED | `Welcome` |
| Brewing (about 10 s) | Steaming coffee cup | Beverage name, e.g. `Cappuccino` |
| Order refused | Yellow `!` | e.g. `Refill milk`, `Empty waste`, `Not ready` |
| Error (until an operator fills a container or empties the waste) | Blinking red `X` | e.g. `Out of milk` |

See [docs/sensehat-display-design.md](docs/sensehat-display-design.md) for the design. The Sense HAT is detected automatically at startup. Without one (e.g. on a laptop), display output is logged instead.

Install the Sense HAT library from Raspberry Pi OS, and create the virtual environment with access to system packages so it can be imported:

```bash
sudo apt install sense-hat
python -m venv --system-site-packages .venv
```

If the Pi is mounted so the display appears upside down or sideways, set the rotation (0, 90, 180 or 270):

```bash
SENSE_HAT_ROTATION=180 uvicorn main:app --host 0.0.0.0 --port 8000
```

> **Note:** The API has no authentication, so anyone on the network can brew, refill or reconfigure the machine. Only use this on a trusted network and never expose it to the internet. State is held in memory and shared by all clients, so it resets when the server restarts.

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
