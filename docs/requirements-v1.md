# Virtual Coffee Machine — Requirements v1

> Digital Twin · Domain-Driven Design · Version 1.0 · 2026-10-14

---

## 1. Overview

This document defines the requirements for **Virtual Coffee Machine v1** — a software digital twin of an automatic coffee machine. The twin is used to explore, validate, and communicate the domain model before hardware implementation, applying **Domain-Driven Design (DDD)** principles throughout.

### Goals
- Model the real machine's bounded contexts in software
- Validate container state management and beverage dispensing logic
- Provide a living specification that evolves with the physical design

### Scope — Version 1

| In scope | Out of scope |
|---|---|
| Reading container levels (water, coffee×2, milk, cacao, waste) | Automated/sensor-driven refilling |
| Manual filling and emptying of containers | Connectivity / IoT integration |
| Selecting and brewing a beverage | Payment or user accounts |
| Basic waste tracking | Predictive maintenance |
| Domain model and bounded context map | UI beyond CLI / API |

---

## 2. Context Diagram

```
                        +---------------------------------------------+
                        |           Virtual Coffee Machine            |
                        |                                             |
  +-----------+         |  +--------------------------------------+  |
  |  Operator |--fill-->|  |         Container Management         |  |
  | (person)  |<-read---|  |  Water · Coffee A · Coffee B         |  |
  +-----------+         |  |  Milk  · Cacao   · Waste             |  |
                        |  +----------------+---------------------+  |
                        |                   | levels                  |
  +-----------+         |  +----------------v---------------------+  |
  | Customer  |-select->|  |          Beverage Dispensing         |  |
  | (person)  |<-brew---|  |  Recipe · Ingredient check · Brew    |  |
  +-----------+         |  +--------------------------------------+  |
                        |                                             |
                        |  +--------------------------------------+  |
                        |  |           Machine State              |  |
                        |  |  Idle · Ready · Brewing · Error      |  |
                        |  +--------------------------------------+  |
                        +---------------------------------------------+
```

### Actors

| Actor | Role |
|---|---|
| **Customer** | Selects and receives a beverage |
| **Operator** | Reads container levels; manually fills or empties containers |

### External interfaces (v1)

| Interface | Direction | Notes |
|---|---|---|
| Beverage Selection API | Customer -> Machine | Choose beverage type |
| Container State API | Machine -> Operator | Read current levels |
| Fill/Empty Command API | Operator -> Machine | Update container levels manually |

---

## 3. Containers

| Container | Ingredient | Unit | Min (low alert) | Max capacity |
|---|---|---|---|---|
| Water | Water | mL | 200 mL | 1 500 mL |
| Coffee A | Ground coffee type A | g | 20 g | 250 g |
| Coffee B | Ground coffee type B | g | 20 g | 250 g |
| Milk | Fresh milk | mL | 100 mL | 500 mL |
| Cacao | Cacao powder | g | 20 g | 200 g |
| Waste | Spent grounds + liquids | mL-eq | — | 500 mL-eq |

### Container state model

```
       fill()
         |
  -------v-------
  |    EMPTY    | ---- fill() ---->  +--------------+
  +-------------+                    |    NORMAL    |
                                     +------+-------+
                                            | level drops below min
                                       -----v------
                                       |    LOW   | ---- fill() ----> NORMAL
                                       +-----+----+
                                             | level reaches 0
                                        -----v-----
                                        |  EMPTY  |
                                        +---------+
```

Waste container moves in the opposite direction:

```
  EMPTY ---- brew accumulates ----> NORMAL ---- threshold ----> FULL (blocks brewing)
```

---

## 4. Behaviors

### B-01 — Read container level
The system SHALL expose the current level and status (EMPTY / LOW / NORMAL) for each container.

### B-02 — Fill a container
An operator SHALL be able to set a container to a given level (<= max capacity). The state transitions from the current state to the new state derived from the new level.

### B-03 — Empty waste container
An operator SHALL be able to reset the waste container to 0 (EMPTY).

### B-04 — Select a beverage
A customer SHALL be able to select a beverage from the available menu. The machine SHALL validate that all required ingredients are available before confirming.

### B-05 — Brew a beverage
When a beverage is confirmed, the machine SHALL:
1. Transition to BREWING state
2. Deduct ingredient amounts from the relevant containers
3. Accumulate waste in the waste container
4. Return to READY (or ERROR if a container transitions to EMPTY mid-brew)

### B-06 — Reject when ingredients insufficient
If any required ingredient level is insufficient to fulfil a recipe, the machine SHALL reject the order and return the reason (which ingredient is low or empty).

### B-07 — Machine state gate
The machine SHALL only accept beverage orders when in READY state. Any other state (BREWING, ERROR, IDLE) causes the request to be refused.

---

## 5. Scenarios

### S-01 — Successful espresso (happy path)

```
Customer                    Machine                     Containers
   |                           |                             |
   |-- selectBeverage(Espresso)>|                             |
   |                           |-- checkIngredients() ------>|
   |                           |<-- ok: water=800mL, coffeeA=50g
   |<-- confirmed -------------|                             |
   |                           |-- BREWING ------------------|
   |                           |-- deduct(water:30mL, coffeeA:7g) -->
   |                           |-- addWaste(35mL-eq) ------->|
   |<-- beverageReady ----------|                             |
   |                           |-- READY --------------------|
```

### S-02 — Rejection due to empty coffee

```
Customer                    Machine
   |                           |
   |-- selectBeverage(CoffeeBEspresso) -->|
   |                           |-- checkIngredients()
   |                           |   coffeeB.level = 0 -> EMPTY
   |<-- rejected(reason: coffeeB EMPTY) --|
```

### S-03 — Operator fills water container

```
Operator                    Machine
   |                           |
   |-- getContainerState(Water)>|
   |<-- {level:180mL, state:LOW}|
   |-- fillContainer(Water, 1500mL) -->|
   |                           |-- validate: 1500 <= maxCapacity(1500) OK
   |                           |-- Water.level = 1500, state = NORMAL
   |<-- {level:1500mL, state:NORMAL} --|
```

### S-04 — Waste container full, brewing blocked

```
Customer                    Machine
   |                           |
   |-- selectBeverage(Cappuccino) -->|
   |                           |-- checkIngredients() -> all ok
   |                           |-- checkWaste() -> Waste FULL
   |<-- rejected(reason: waste container full, please empty) --|

Operator                    Machine
   |-- emptyWasteContainer() -->|
   |                           |-- Waste.level = 0, state = EMPTY
   |<-- ok ---------------------|
```

### S-05 — Machine in ERROR state

```
Customer                    Machine
   |-- selectBeverage(Espresso) -->|
   |                           |-- state = ERROR
   |<-- rejected(reason: machine not ready, state=ERROR) --|
```

---

## 6. Beverage Menu (v1 examples)

| Beverage | Water (mL) | Coffee A (g) | Coffee B (g) | Milk (mL) | Cacao (g) | Waste (mL-eq) |
|---|---|---|---|---|---|---|
| Espresso | 30 | 7 | — | — | — | 10 |
| Americano | 120 | 7 | — | — | — | 10 |
| Cappuccino | 30 | 7 | — | 100 | — | 15 |
| Latte | 30 | 7 | — | 150 | — | 15 |
| Coffee B Espresso | 30 | — | 7 | — | — | 10 |
| Hot Chocolate | 150 | — | — | 100 | 20 | 20 |
| Mocha | 30 | 7 | — | 100 | 10 | 20 |

---

## 7. Domain Model — DDD Suggestions

### 7.1 Context Map

```
  +--------------------------+      +--------------------------+
  |   CORE: Brewing          |----->|  CORE: Container         |
  |   (Beverage Dispensing)  | uses |  Management              |
  +--------------------------+      +--------------------------+
             |                                  |
             | notifies                         | notifies
             v                                  v
  +--------------------------+      +--------------------------+
  |  SUPPORTING: Machine     |      |  SUPPORTING: Alerting    |
  |  Lifecycle               |      |  (low-level warnings)    |
  +--------------------------+      +--------------------------+
             |
             v
  +--------------------------+
  |  GENERIC: Configuration  |
  |  (capacities, thresholds)|
  +--------------------------+
```

### 7.2 Core Domains

These encode the machine's primary competitive differentiation.

#### Brewing Domain
Responsible for the beverage lifecycle from selection to delivery.

- **Aggregates:** `BrewOrder` (root), `Recipe`
- **Entities:** `BeverageSelection`, `BrewStep`
- **Value Objects:** `Ingredient`, `Quantity`, `RecipeRequirement`
- **Domain Events:** `BeverageOrdered`, `BrewStarted`, `BrewCompleted`, `BrewRejected`
- **Invariants:**
  - Cannot brew if any required ingredient is insufficient
  - Cannot brew unless machine is in READY state

#### Container Management Domain
Manages the state of all physical ingredient and waste containers.

- **Aggregates:** `Container` (one per physical container)
- **Value Objects:** `ContainerLevel`, `ContainerState` (EMPTY / LOW / NORMAL / FULL)
- **Domain Events:** `ContainerFilled`, `ContainerLevelChanged`, `ContainerLow`, `ContainerEmpty`, `WasteContainerFull`
- **Invariants:**
  - Level cannot exceed max capacity
  - Level cannot be negative

### 7.3 Supporting Domains

Important to the machine, but not the primary differentiator.

#### Machine Lifecycle Domain
Tracks and enforces machine operational states.

- **Aggregate:** `CoffeeMachine`
- **Value Object:** `MachineState` (IDLE / READY / BREWING / ERROR)
- **Domain Events:** `MachineReady`, `MachineBrewing`, `MachineError`
- **Invariants:** State transitions follow a defined finite state machine (FSM)

```
  IDLE ---[power on]---> READY ---[brew start]---> BREWING ---[brew done]---> READY
                           ^                           |
                           |                      [error]
                           |                           v
                           +-------[resolve]--------- ERROR
```

#### Alerting Domain
Notifies operators when action is needed (low ingredient, waste full).

- **Service:** `AlertService`
- **Value Objects:** `Alert`, `AlertSeverity` (INFO / WARNING / CRITICAL)
- **Listens to:** `ContainerLow`, `ContainerEmpty`, `WasteContainerFull`

### 7.4 Generic Domains

Commodity concerns — implement with standard patterns or off-the-shelf libraries.

| Domain | Responsibility | Candidate approach |
|---|---|---|
| Configuration | Container capacities, low-level thresholds, recipe definitions | Static config / seeded data store |
| Logging / Audit | Record all state changes and commands | Standard logging framework |
| Persistence | Store and retrieve aggregate state | In-memory store for v1 |

---

## 8. Ubiquitous Language (Glossary)

| Term | Definition |
|---|---|
| **Container** | A storage unit (physical or virtual) holding one ingredient or waste |
| **Level** | The current amount in a container, in its natural unit (mL or g) |
| **State** | Derived status of a container: EMPTY, LOW, NORMAL, or FULL (waste only) |
| **Fill** | Operator action to add ingredient to a container up to a target level |
| **Empty** | Operator action to drain the waste container to zero |
| **Recipe** | The set of ingredients and quantities required to produce one serving of a beverage |
| **BrewOrder** | A customer's intent to brew a specific beverage; transitions through the Brewing domain |
| **Brew** | The process of consuming ingredients per a recipe and producing a beverage + waste |
| **Waste** | Spent grounds, rinsing water, and other by-products accumulated in the waste container |
| **Operator** | A human who maintains the machine (fills containers, empties waste) |
| **Customer** | A human who uses the machine to get a beverage |

---

## 9. Open Questions

| # | Question | Owner |
|---|---|---|
| OQ-1 | What are the exact recipe ingredient amounts for each beverage? | Domain expert |
| OQ-2 | Should LOW threshold be a fixed value or configurable per container? | Design team |
| OQ-3 | What happens if the machine runs out of an ingredient mid-brew? (partial brew?) | Domain expert |
| OQ-4 | Will v2 add temperature as a dimension (e.g. hot water vs cold water tank)? | Architecture |
| OQ-5 | Is the waste container tracked by volume or by brew count? | Hardware team |
