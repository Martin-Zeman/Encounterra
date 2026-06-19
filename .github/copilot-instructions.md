# Copilot Instructions — Encounterra

## Project Overview

**Encounterra** is a combat encounter simulator for Dungeons and Dragons 5th Edition. It allows DMs to quickly create and simulate encounters with various monsters, NPCs, and player characters, providing detailed combat logs and statistics.
This repository holds the core simulation engine, which is designed for extensibility and performance. The engine supports a wide range of D&D mechanics, including actions, reactions,, special class abilities, monster abilities, spellcasting, and more. The tool is currently written in Python but due to the computational intensity of simulating complex encounters, there's an ongoing effort to rewite the tool in C++ for improved performance. The work-in-progress C++ code can be found in the c++ directory.

## Architecture and Algorithm

The architecture heavily relies on inheritance patterns for its modularity. This concept is used heavily for all abilities and spells.
The main idea of the AI which controls the combatans is a so-called concept of 'threat'. For simple damage-dealing abilities the threat is equal to the average damage dealt times the probability of hitting the target. For more complex abilities the threat is calculated using custom logic. But every action as well as movement gets evaluated in terms of threat. An action tree is constructed for the combatants before each actoid is taken. An actoid can either be an action, bonus action, free action, movement increment or just a single attack. The tree is then traversed to find the path with the highest cumulative threat. Potential incoming threat has a negative value while potential outgoing threat has a positive value. The combatant then takes the first actoid on the path with the highest cumulative threat. For the next actoid the tree is reconstructed and the process is repeated until the combatant runs out of resources or there are no more actoids with positive cumulative threat. This allows the combatant to adapt to the changing combat situation based on the outcome of previous actoids.
Actoids are created by factories. Both the factories and actoids inherit from various base classes.  Multiple inheritance is used heavily. Abitilites, actions, attacks and spells inherit from different threat interface classes such as DirectThread or AttackThreatModifier, while factories inherit from ThreatModifierFactory, DirectThreatFactory etc.

## Python Implementation

The Python implementation uses poetry as the dependency manager.

### Important Files

| File | Purpose |
|------|---------|
| `main.py` | The main entry point for the simulation. It defines the combatants, their team assigment, obstacles on the map and number of iterations. |
| `simulator/battle_map.py` | Singletton. Handles all operations related to the battle map such as pathfinding, distances, keeping track of combatant positions, AoE templates, and other spatial calculations. |
| `simulator/action_resolver.py` | Responsible for resolving actions taken by combatants, including attacks, spells, and other abilities. |
| `simulator/combatant.py` | The main parent class for all combatants. |
| `simulator/feasibility.py` | Determines a feasibility of actions, bonus actions and reactions etc. based on current state of combatant's resources. |
| `simulator/geometry.py` | Deals with pure geometric calculations. Used heavily by battle_map.py |
| `simulator/resources.py` | Tracks resources such as action, bonus actions, reactions, movement etc. |
| `simulator/round_manager.py` | Contains the main simulation loop that iterates over all combatants in each round. |
| `simulator/session.py` | The most high level class that sets up the game. Uses the `round_manager.py` to control the flow of combat. |
| `simulator/spellslots.py` | Manages spell slot numbers for each class/level combinations. |
| `simulator/actions/actoid.py` | Proto-action base class. It doesn't map onto an 'action' directly as an Actoid can represent even a partial action such as one attack which is part of a multiattack or a movement increment. |
| `simulator/actions/action_dag.py` | Builds the action tree based on the available actoids and resources (no movement is added yet). |
| `simulator/actions/action_selector.py` | The main action selection logic. Enriches the action graph with feasible coordinates and selects the best action from the action tree. |
| `simulator/spells/*.py` | Manages individual spells and their effects. |
| `simulator/actions/*.py` | Contains different action types such as attacks, movements, dodges, grapples, dashes etc. |
| `simulator/abilities/*.py` | Manages individual abilities, On-hit triggers and their effects. |
| `simulator/combatants/*.py` | Manages individual combatants. |
| `simulator/effects/*.py` | Manages all different types of long lasting effects including AoEs. |

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

---

## C++ Implementation

The C++ implementation is a work in progress. For matrix operations, it uses the Blaze library. GTest is the testing framework of choice. The C++ code is organized in a similar way to the Python code, with separate directories for different components of the simulation. The main simulation loop and combatant logic are still being developed, but the core data structures and some of the action logic have been implemented.

### Important Files

| File | Purpose |
|------|---------|
| `main.cpp` | Currently just used for testing Blaze but should be equivalent to `main.py` in the Python implementation. |
| `core/battle_map.cpp/.hpp` | Singletton. Handles all operations related to the battle map such as pathfinding, distances, keeping track of combatant positions, AoE templates, and other spatial calculations. |
| `core/action_resolver.cpp/.hpp` | Responsible for resolving actions taken by combatants, including attacks, spells, and other abilities. |
| `core/combatant.cpp/.hpp` | The main parent class for all combatants. |
| `core/feasibility.cpp/.hpp` | Determines a feasibility of actions, bonus actions and reactions etc. based on current state of combatant's resources. |
| `core/geometry.cpp/.hpp` | Deals with pure geometric calculations. Used heavily by battle_map.cpp |
| `core/resources.cpp/.hpp` | Tracks resources such as action, bonus actions, reactions, movement etc. |
| `core/round_manager.cpp/.hpp` | Contains the main simulation loop that iterates over all combatants in each round. |
| `core/session.cpp/.hpp` | The most high level class that sets up the game. Uses the `round_manager.py` to control the flow of combat. |
| `core/spellslots.cpp/.hpp` | Manages spell slot numbers for each class/level combinations. |
| `core/interfaces.hpp` | Contains the interface classes such as Actoid, ActoidFactory, Threat etc. that abilities derive from. |
| `actions/action_dag.cpp/.hpp` | Builds the action tree based on the available actoids and resources (no movement is added yet). |
| `actions/action_selection.cpp/hpp` | The main action selection logic. Enriches the action graph with feasible coordinates and selects the best action from the action tree. |
| `spells/*.cpp/.hpp` | Manages individual spells and their effects. |
| `actions/*.cpp/.hpp` | Contains different action types such as attacks, movements, dodges, grapples, dashes etc. |
| `abilities/*.cpp/.hpp` | Manages individual abilities, On-hit triggers and their effects. |
| `combatants/*.cpp/.hpp` | Manages individual combatants. |
| `effects/*.cpp/.hpp` | Manages all different types of long lasting effects including AoEs. |

### Building and Running

#### Prerequisites

- CMake 3.22.1 or later
- C++20 compatible compiler (GCC, Clang, or MSVC)
- Blaze 3.x library (`/usr/local/include/blaze/`)
- LAPACK/BLAS libraries (`liblapack-dev`, `libblas-dev`)
- OpenSSL development files (`libssl-dev`)
- GTest (included as submodule in `c++/googletest`)

**Note**: The build first tries the system Blaze installation. If it is unavailable or inaccessible (for example due to permissions on `/usr/local/share/blaze/cmake/`), it automatically falls back to the local `.blaze-cmake/` copy. Do not delete this directory.

#### Build Steps

```bash
cd c++/build
cmake ..
make -j$(nproc)
```

The first `cmake ..` automatically detects and configures the Blaze library using the local `.blaze-cmake/` directory. Subsequent builds can simply run `make -j$(nproc)` to compile.

#### Run Tests

```bash
cd c++/build
./test/test_encounterra
```

Or run specific test suites:

```bash
./test/test_encounterra --gtest_filter="ThreatUtilsTest.*"
```

Depending on the active CMake output layout, the binary may also be at `./bin/test_encounterra`.

#### Clean Build

```bash
cd c++/build
rm -rf *
cmake ..
make -j$(nproc)
```

---

## Migration Note

Most of the python files have their direct equivalent in C++. However, a few key differentces should be noted:
- In python each action used to be uniquely defined by a string representation in the action tree. For the sake of efficiency, this has been replaced by a custom hash function in C++.
- In C++ the multiple inheritance has to deal with the diamond problem by using virtual inheritance. This is not an issue in python.
- Most test from Python have been migrated but some are still in progress. Even though the testing framework is also different (GTest vs pytest) the test files try to be direct equivalents.
- The `simulator/utils/state_machine_template.py` has been replaced by a much leaner `c++/core/state_machine.cpp/.hpp`
- The python implementation is written based on 2014 version of the 5e rules whereas the c++ implementation is based on 2024 version. This means some mechanics (such as grappling etc.), class names and abilities have changed. 

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
  `export TMPDIR=/home/yc320/repos/Encounterra/.buildtmp`, `make -j16 encounterra`.

**Remaining hotspots (next gains are algorithmic, not micro-optimizations):** `pruneSequences` is now
volume-bound (cost scales with the *number* of generated sequences, not per-element work); diffuse
allocator churn remains from per-turn state-machine rebuilds and DFS output vectors;
`buildActionStateMachine` is rebuilt every combatant turn (a candidate for caching). The
string-keyed `unordered_map<std::string, std::shared_ptr<Actoid>>` in `findBestSequence` is the source
of the remaining `memcmp` cost and could be de-stringified. Note: `dfs`/`pruneSequences`/
`findBestSequence` are not unit-tested — only the end-to-end simulation validates them.
