# EncounTroll
Combat encounter simulator for D&D 5e

The architecture was designed with the following goals in mind:
- Abilities must be modular (meaning that assigning abilities to any character should be simple)
- Must lend itself easily to machine learning (e.g. RL)
- Ease of scalability in terms of adding new abilities and mechanics
- Combat sessions are independent of each other
- Must support parallel execution