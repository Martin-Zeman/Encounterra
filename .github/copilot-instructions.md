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
---

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

## Migration Note

Most of the python files have their direct equivalent in C++. However, a few key differentces should be noted:
- In python each action used to be uniquely defined by a string representation in the action tree. For the sake of efficiency, this has been replaced by a custom hash function in C++.
- In C++ the multiple inheritance has to deal with the diamond problem by using virtual inheritance. This is not an issue in python.
- Most test from Python have been migrated but some are still in progress. Even though the testing framework is also different (GTest vs pytest) the test files try to be direct equivalents.
- The `simulator/utils/state_machine_template.py` has been replaced by a much leaner `c++/core/state_machine.cpp/.hpp`
