# InfraSync — Lucidchart Drawing Guide

Use this to manually build the architecture diagram in Lucidchart (or import the Mermaid exports as images).

---

## Option A: Import Mermaid Exports

1. Go to [mermaid.live](https://mermaid.live)
2. Paste diagram code from `mermaid_diagrams.md`
3. Click the download icon → export as **SVG** (best quality) or PNG
4. In Lucidchart: **File → Import Data → Image** → upload the SVG/PNG
5. Position and resize as needed

---

## Option B: Build Manually in Lucidchart

### Components & Shapes

| Component | Shape | Color | Label |
|-----------|-------|-------|-------|
| CLI | Rounded rectangle | Gray (#E0E0E0) | `CLI: init \| plan \| apply \| destroy` |
| Config File | Document shape (paper icon) | Light blue (#BBDEFB) | `infrasync.yaml` |
| State File | Cylinder (database) | Light green (#C8E6C9) | `infrasync.state.json` |
| Engine | Large rectangle (container) | Blue (#42A5F5) | `Reconciliation Engine` |
| Config Parser | Small rectangle inside Engine | Light blue | `Config Parser (YAML)` |
| State Manager | Small rectangle inside Engine | Light green | `State Manager (JSON)` |
| Plan Engine | Small rectangle inside Engine | Orange (#FFB74D) | `Plan Engine (3-way diff)` |
| Dependency Graph | Small rectangle inside Engine | Orange | `Topological Sort` |
| Provider Interface | Rectangle with dashed border | Purple (#CE93D8) | `Provider Interface (abstract)` |
| Filesystem Provider | Rectangle solid | Purple (#7B1FA2 text white) | `Filesystem Provider` |
| Future Provider | Rectangle dashed | Purple dashed (#CE93D8) | `Cloud / DB / HTTP (future)` |
| Real World | Cloud shape or folder icon | Yellow (#FFF9C4) | `Local Filesystem` |

---

### Layout (top to bottom)

```
Row 1:  [CLI]
         |
Row 2:  [Config File]  [Engine (large box)]  [State File]
                        contains:
                        - Config Parser
                        - State Manager  
                        - Plan Engine
                        - Dependency Graph
         |
Row 3:  [Provider Interface]
         |
Row 4:  [Filesystem Provider]  ···  [Future Providers]
         |
Row 5:  [Real World / Filesystem]
```

---

### Arrows & Labels

| From | To | Label | Style |
|------|----|-------|-------|
| CLI | Engine | `commands` | Solid, black |
| Config File | Engine (Config Parser) | `parse YAML` | Solid, blue |
| Engine (State Manager) | State File | `read/write JSON` | Solid, green |
| Engine (Plan Engine) | Provider Interface | `lookup provider` | Solid, purple |
| Provider Interface | Filesystem Provider | `fs_file, fs_directory` | Solid, purple |
| Provider Interface | Future Providers | `extensible` | Dashed, purple |
| Filesystem Provider | Real World | `create / read / update / delete` | Solid, yellow |
| Engine | Engine (Plan Engine) | `three-way diff` | Internal arrow |

---

### The Three-Way Diff Box (key visual)

Draw this as a standalone callout or annotation:

```
┌────────────────────────────────────────────┐
│         THREE-WAY RECONCILIATION           │
├────────────────────────────────────────────┤
│                                            │
│  Config    vs    State    vs    World      │
│  (want)         (last did)     (actual)   │
│                                            │
│  If all match         → NO-OP             │
│  If config changed    → UPDATE            │
│  If world changed     → UPDATE (drift)    │
│  If new in config     → CREATE            │
│  If gone from config  → DESTROY           │
│  If gone from world   → CREATE (recreate) │
│                                            │
└────────────────────────────────────────────┘
```

---

### Plan Output Symbols (for slides)

| Symbol | Color | Meaning |
|--------|-------|---------|
| `+` | Green | Create — resource will be added |
| `~` | Yellow/Orange | Update — resource will be modified |
| `-` | Red | Destroy — resource will be removed |
| (blank) | Gray | No-op — already in sync |

---

## Slide Suggestions (for PowerPoint)

**Slide 1: Problem Statement**
- "Desired state vs actual state — and the gap between them"
- One sentence: "InfraSync closes that gap automatically"

**Slide 2: Architecture Diagram**
- Use the top-to-bottom layout above
- The Engine box is the hero — largest element

**Slide 3: Three-Way Reconciliation**
- The callout box above as the main visual
- This IS the intellectual core of the project

**Slide 4: Demo Screenshots**
- Terminal output of plan (with colors)
- Show: create → drift → detect → correct

**Slide 5: Provider Extensibility**
- Show the interface (5 methods)
- "Adding AWS means implementing these 5 methods. Engine never changes."

**Slide 6: Trade-offs & What's Next**
- Table of decisions + rationale
- List of improvements with more time
