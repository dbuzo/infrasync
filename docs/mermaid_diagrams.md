# InfraSync — Mermaid Diagrams

Paste each code block into [mermaid.live](https://mermaid.live) to render and export as SVG/PNG.

---

## Diagram 1: System Architecture

```mermaid
graph TD
    subgraph "User Interface"
        CLI[CLI<br/>init | plan | apply | destroy]
    end

    subgraph "Core Engine"
        CFG[Config Parser<br/>YAML → Resources]
        STATE[State Manager<br/>JSON read/write]
        PLAN[Plan Engine<br/>Three-way diff]
        GRAPH[Dependency Graph<br/>Topological sort]
        ENGINE[Reconciliation Engine<br/>Orchestrates full cycle]
    end

    subgraph "Provider Layer"
        REG[Provider Registry<br/>type → provider lookup]
        BASE[Provider Interface<br/>read | create | update | delete | fingerprint]
        FS[Filesystem Provider<br/>fs_file | fs_directory]
        FUTURE[Future Providers<br/>cloud | database | HTTP]
    end

    subgraph "External"
        DISK[Real World<br/>Local Filesystem]
        STATEFILE[State File<br/>infrasync.state.json]
        CONFIGFILE[Config File<br/>infrasync.yaml]
    end

    CLI --> ENGINE
    ENGINE --> CFG
    ENGINE --> STATE
    ENGINE --> PLAN
    ENGINE --> GRAPH
    CFG --> CONFIGFILE
    STATE --> STATEFILE
    PLAN --> REG
    REG --> BASE
    BASE --> FS
    BASE -.-> FUTURE
    FS --> DISK
```

---

## Diagram 2: Three-Way Reconciliation Logic

```mermaid
flowchart TD
    START[For each resource in config] --> CHECK_STATE{Exists in state file?}

    CHECK_STATE -->|No — brand new| CHECK_WORLD_NEW{Exists in real world?}
    CHECK_STATE -->|Yes — previously applied| CHECK_WORLD_EXIST{Exists in real world?}

    CHECK_WORLD_NEW -->|No| CREATE[✚ CREATE<br/>New resource, never seen before]
    CHECK_WORLD_NEW -->|Yes, matches config| ADOPT[NO-OP<br/>Already correct, adopt into state]
    CHECK_WORLD_NEW -->|Yes, differs from config| UPDATE_EXISTING[〜 UPDATE<br/>Exists but wrong content]

    CHECK_WORLD_EXIST -->|No — was deleted externally| RECREATE[✚ CREATE<br/>Disappeared from world, recreate]
    CHECK_WORLD_EXIST -->|Yes| COMPARE{Fingerprint matches desired?}

    COMPARE -->|Yes — all good| NOOP[NO-OP<br/>Everything matches]
    COMPARE -->|No — world changed| DRIFT[〜 UPDATE<br/>Drift detected]
    COMPARE -->|No — config changed| CONFIG_UPDATE[〜 UPDATE<br/>Config changed]

    subgraph "Resources in state but NOT in config"
        ORPHAN[— DESTROY<br/>Removed from config]
    end
```

---

## Diagram 3: Plan → Apply Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant E as Engine
    participant C as Config (YAML)
    participant S as State (JSON)
    participant P as Provider
    participant W as Real World

    U->>CLI: python -m infrasync apply
    CLI->>E: cmd_apply()
    E->>C: load_config()
    C-->>E: resources[]
    E->>S: load_state()
    S-->>E: recorded state{}

    loop For each resource
        E->>P: provider.read(resource)
        P->>W: check file/dir existence
        W-->>P: current content or None
        P-->>E: real-world state
    end

    E->>E: compute_plan()<br/>three-way diff

    loop For each action (sorted by dependencies)
        alt CREATE
            E->>P: provider.create(resource)
            P->>W: write file / mkdir
        else UPDATE
            E->>P: provider.update(resource)
            P->>W: overwrite file
        else DESTROY
            E->>P: provider.delete(resource)
            P->>W: remove file / rmdir
        end
        E->>S: save_state() after EACH operation
    end

    E-->>CLI: summary (created, updated, destroyed)
    CLI-->>U: display results
```

---

## Diagram 4: Dependency Graph & Apply Order

```mermaid
graph LR
    subgraph "Config Resources"
        A[fs_directory.output_dir<br/>./managed/output]
        B[fs_file.readme<br/>./managed/README.md]
        C[fs_file.app_config<br/>./managed/output/config.json]
    end

    C -->|depends_on| A

    subgraph "Apply Order (topological sort)"
        direction TB
        S1["Step 1: fs_directory.output_dir"]
        S2["Step 2: fs_file.readme"]
        S3["Step 3: fs_file.app_config"]
        S1 --> S3
    end

    subgraph "Destroy Order (reversed)"
        direction TB
        D1["Step 1: fs_file.app_config"]
        D2["Step 2: fs_file.readme"]
        D3["Step 3: fs_directory.output_dir"]
        D1 --> D3
    end
```

---

## Diagram 5: Error Handling — Partial Apply

```mermaid
flowchart TD
    START[Apply begins] --> R1[Resource 1: CREATE]
    R1 -->|Success| SAVE1[Save state ✓]
    SAVE1 --> R2[Resource 2: UPDATE]
    R2 -->|Success| SAVE2[Save state ✓]
    SAVE2 --> R3[Resource 3: CREATE]
    R3 -->|FAILS| ERROR[Log error]
    ERROR --> SAVE3[State still saved<br/>reflects Resources 1+2 succeeded]
    SAVE3 --> R4[Resource 4: CREATE]
    R4 -->|Success| SAVE4[Save state ✓]
    SAVE4 --> DONE[Apply complete<br/>3 succeeded, 1 error]

    style R3 fill:#ff6666
    style ERROR fill:#ff6666
```

---

## Diagram 6: State File Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Empty: init
    Empty --> Populated: apply creates resources
    Populated --> Populated: apply updates/creates more
    Populated --> Populated: drift corrected via apply
    Populated --> Empty: destroy removes all
    Empty --> [*]

    state Populated {
        [*] --> InSync
        InSync --> Drifted: external change to managed resource
        Drifted --> InSync: apply corrects drift
        InSync --> ConfigChanged: user edits config
        ConfigChanged --> InSync: apply updates resource
    }
```

---

## Diagram 7: Provider Interface (Class Diagram)

```mermaid
classDiagram
    class Provider {
        <<abstract>>
        +read(resource) Optional~dict~
        +create(resource) dict
        +update(resource) dict
        +delete(resource) None
        +fingerprint(resource) str
    }

    class FilesystemProvider {
        +read(resource) Optional~dict~
        +create(resource) dict
        +update(resource) dict
        +delete(resource) None
        +fingerprint(resource) str
        -_read_file(path) str
        -_read_dir(path) bool
    }

    class ProviderRegistry {
        -_providers: Dict
        +get(resource_type) Provider
        +registered_types() List
    }

    Provider <|-- FilesystemProvider
    ProviderRegistry --> Provider : looks up by type
```
