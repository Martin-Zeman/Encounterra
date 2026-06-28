apt install cmake
apt install clang-format

To make Blaze work:
apt-get install libblas-dev
sudo apt-get install liblapack-dev


apt-get install libssl-dev

## Python Implementation

The Python implementation uses poetry as the dependency manager.

### Installing Dependencies and Running

#### Prerequisites

- Python 3.11 or later (up to 3.12.x)
- Poetry (dependency manager): `pip install poetry`

#### Setup

```bash
cd Encounterra
poetry install --no-root
```

This installs all dependencies listed in `pyproject.toml` into a virtual environment.

If you want the environment in the project directory (recommended), run:

```bash
poetry config virtualenvs.in-project true --local
```

This creates `.venv/` in the repository root.

#### Run Simulation

```bash
poetry run python main.py
```

This runs the combat simulation with the combatants, teams, and encounter parameters defined in `main.py`.

#### Run Tests

```bash
poetry run pytest
```

For verbose output:

```bash
poetry run pytest -v
```

Run specific test files:

```bash
poetry run pytest simulator/test_combatant.py -v
```

#### Working with Poetry

To add new dependencies:

```bash
poetry add package_name
```

To update dependencies:

```bash
poetry update
```

To activate the virtual environment:

```bash
poetry shell
```


- Spells to migrate: Bless, Magic Missile, Mage Armor, Shield, Sleep, Tasha's hideous Laughter, Armor of Agathys, Bane, Dissonant Whispers, Entangle, Guiding Bolt, Shield of Faith, Hex, Hellish Rebuke, Hunter's Mark, Divine Smite, Sanctuary, Protection from Evil and Good, Burning Hands, Web, Spiritual Weapon, Silence, Misty Step, Heat Metal, Cloud of Daggers, Barkskin, Conjure Animals, Counterspell, Fireball, Fear, Haste, Hypnotic Pattern, Spirit Guardians, Aura of Vitality, Blinding Smite, Conjure Barrage, Slow, Call Lightning, Hunger of Hadar, Lightning Bolt, Lightning Arrow

## Performance Optimizations (C++)

The C++ action-selection hot path was profiled with `perf` (release build, `simulateN(100)`, logging
suppressed) and optimized. The work targeted the action-tree DFS/pruning in
`core/state_machine.cpp/.hpp` and `actions/action_selection.cpp/.hpp`. Cumulatively these took the
100-iteration release wall time from **33.84 s → ~11.3 s (≈3.0× faster)**, while the final optimized
release runs **~97× faster per iteration than the Python+numba reference** (10.98 s → 0.113 s per iteration).

Optimizations applied, in order (each line shows the resulting 100-iteration release time):

1. **Integer transition identity (string → int).** Previously the DFS encoded integer transition
   indices as `std::string` (via `std::to_string`), and `pruneSequences` parsed them back with
   `std::stoul`, building set-keys through O(n²) string concatenation. Replaced with plain `int`
   transition indices end-to-end (`StateMachine::dfs` returns `vector<vector<int>>`,
   `transitionToSimplified` keyed by `int`). Eliminated string formatting/parsing/hashing. → 24.30 s
2. **Footprint dedup via `unordered_set<vector<int>>`.** Replaced the per-sequence
   `std::set<int>` / `std::set<std::set<int>>` (red-black-tree node allocations) with a sorted+uniqued
   contiguous `std::vector<int>` footprint deduped through an `unordered_set` with a custom hash. → 14.07 s
3. **Recursive backtracking DFS + move semantics.** Rewrote the iterative stack-based `dfs` (which
   copied a fresh `vector<int>` prefix at every branch) as `StateMachine::dfsRecurse`, a backtracking
   recursion that pushes/pops a single shared `path` buffer and materializes each complete path exactly
   once. Additionally `pruneSequences` now takes its input **by value** and `std::move`s surviving
   sequences into the result (caller does `pruneSequences(std::move(allSequences), ...)`), removing a
   copy per surviving sequence. This attacked the dominant allocator churn
   (`malloc`/`free`/`malloc_consolidate`). → 11.84 s
4. **Bitmask footprint dedup.** When the simplified-transition index space fits in 64 entries (the
   common case for a single combatant's turn DAG), each footprint is encoded as a `uint64_t` bitmask
   deduped via `unordered_set<uint64_t>` — no per-sequence vector allocation, no sort/unique, no
   `memcmp` on keys. Falls back to the sorted-vector footprint (opt 2) when an index ≥ 64 appears. → 11.27 s
5. **Dense `vector` lookup tables.** Because transition indices are assigned sequentially (`0..N-1`),
   `transitionToSimplified` and `indexToActoid` were changed from `unordered_map` to `std::vector`
   (O(1) array indexing, no hashing), built via `push_back` in `getFlattenedDag`. Wall-time-neutral but
   reduces `pruneSequences` self-time and makes the per-turn state-machine build cheaper.

**Logging suppression for benchmarking:** `core/logger.cpp/.hpp` defines
`enum class LogLevel { NONE, ERROR, INFO }` and `Logger::setLevel/getLevel`. At levels below `INFO`,
`std::cout`/`std::cerr` `rdbuf` are redirected to a null sink, so timing runs incur no I/O overhead.

**Profiling notes / gotchas:**
- Use `perf record -g --call-graph dwarf -- ./bin/encounterra` then
  `perf report --stdio --no-children` (self time) or without the flag (inclusive/children time).
- **Write `perf.data` to a real disk** (e.g. `Encounterra/.buildtmp/`), **not `/tmp`** — `/tmp` is a 4 GB
  tmpfs and the multi-hundred-MB perf captures fill it, producing a truncated file
  (`data size field is 0`, exit 255).
- Release builds: `cd c++/build-release` (RelWithDebInfo, `-O2`),
  `export TMPDIR=/home/yc320/repos/Encounterra/.buildtmp`, `make -j18 encounterra`.
