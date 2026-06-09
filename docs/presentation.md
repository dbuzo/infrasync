# InfraSync — Presentation Slides

---

## SLIDE 1 — Title

# InfraSync
### A Declarative Infrastructure Reconciliation Engine

**David Uwakwe**

> You write what you want to exist. InfraSync figures out what needs to change and does it.

---

## SLIDE 2 — The Problem

# The Gap Between Intent and Reality

Every infrastructure tool solves the same core problem:

**What you want to exist** is rarely the same as **what actually exists.**

Files get edited by hand. Directories get deleted by accident. Another script overwrites your config. A deployment changes something you were managing. Over time, your system drifts away from your declared intent — silently.

The question is: **how do you detect that drift and fix it automatically?**

That is the problem InfraSync is built to solve.

```
You declare:     README.md with content "Hello World"
Reality:         README.md now says "someone changed this"
InfraSync:       ~ fs_file.readme  (drift detected — update needed)
```

---

## SLIDE 3 — System Architecture

# How InfraSync Is Structured

![System Architecture](diagrams/system-architecture.png)

The user writes a YAML config file and runs a single command. The CLI passes that command to the Reconciliation Engine. The engine loads the config, reads the state file (its memory of what it last did), and queries the Provider to inspect what actually exists on disk. From those three sources it produces a plan — a list of creates, updates, and destroys — and executes them in dependency order. After each successful operation, state is written to disk immediately.

The Provider Registry sits between the engine and the real world. The engine never calls the Filesystem Provider directly — it calls `get_provider("fs_file")` and gets back whatever implementation is registered for that type. Swapping the backend requires zero changes to the engine.

---

## SLIDE 4 — The Three-Way Reconciliation

# The Core Logic: Three-Way Comparison

![Reconciliation Logic](diagrams/reconciliation-logic.png)

On every `plan` or `apply`, the engine asks one question per resource:

> Does what you **WANT** match what you **LAST DID** match what **ACTUALLY EXISTS**?

| Config | State | World | Action |
|--------|-------|-------|--------|
| ✓ new  | —     | —     | CREATE |
| ✓      | ✓     | ✓ matches | NO-OP |
| ✓      | ✓     | ✗ changed | UPDATE (drift) |
| ✓      | ✓     | — gone | CREATE (recreate) |
| —      | ✓     | ✓     | DESTROY |

**What makes this powerful:** it handles new resources, config edits, external drift, external deletion, and removal from config — all from the same comparison logic, every run.

---

## SLIDE 5 — Live Demo

# What It Looks Like in Practice

**Step 1 — Declare your resources** (`infrasync.yaml`)

```yaml
resources:
  - type: fs_directory
    name: output_dir
    path: ./managed/output

  - type: fs_file
    name: readme
    path: ./managed/README.md
    content: |
      Hello World
      Managed by InfraSync.

  - type: fs_file
    name: app_config
    path: ./managed/output/config.json
    content: '{"log_level": "info", "format": "json"}'
    depends_on:
      - fs_directory.output_dir
```

**Step 2 — Run `plan` to see what will happen**

```
$ python -m infrasync plan

InfraSync Plan:

  + fs_directory.output_dir (new resource)
      path: ./managed/output

  + fs_file.readme (new resource)
      path: ./managed/README.md

  + fs_file.app_config (new resource)
      path: ./managed/output/config.json

Plan: 3 to create, 0 to update, 0 to destroy.
```

**Step 3 — Apply and confirm**

```
$ python -m infrasync apply

  created  fs_directory.output_dir
  created  fs_file.readme
  created  fs_file.app_config

Applied: 3 created, 0 updated, 0 destroyed.

$ python -m infrasync plan
  No changes. Infrastructure is in sync.
```

**Step 4 — Simulate drift and detect it**

```
$ echo "someone changed this" > ./managed/README.md

$ python -m infrasync plan

InfraSync Plan:

  ~ fs_file.readme (drift detected — changed outside infrasync)
      content: someone changed this => Hello World\nManaged by InfraSync.\n

Plan: 0 to create, 1 to update, 0 to destroy.

$ python -m infrasync apply
  updated  fs_file.readme
Applied: 0 created, 1 updated, 0 destroyed.
```

Drift detected, corrected, done.

---

## SLIDE 6 — Provider Pattern & What's Next

# The Design That Makes It Extensible

**Right now:** InfraSync manages files and directories on your local filesystem.

**The architecture makes adding any backend straightforward:**

```python
class AWSProvider(Provider):
    def read(self, resource):      # describe the EC2 instance / S3 bucket
    def create(self, resource):    # boto3 call to create it
    def update(self, resource):    # boto3 call to modify it
    def delete(self, resource):    # boto3 call to remove it
    def fingerprint(self, resource): # hash of desired attributes

# One line in registry.py:
_PROVIDERS["aws_instance"] = AWSProvider()
```

The engine, planner, state manager, dependency graph, and CLI are untouched. That is the provider-agnostic design in practice.

**Trade-offs made intentionally:**

| Decision | Reason | Limitation |
|----------|--------|------------|
| Local JSON state | Simple, human-readable | No team sharing, no locking |
| Sequential apply | Guarantees dependency order | Slower on large resource sets |
| SHA-256 fingerprint | Fast drift detection | Doesn't track permissions |
| YAML config | Readable, no custom parser | No variable interpolation |

**With more time:**
- Remote state (S3 + DynamoDB locking)
- Import existing resources without recreating
- Parallel execution for independent resources
- Additional providers — cloud, database, HTTP API
- Variable interpolation in config files
