#include "spells/fireball.hpp"
#include <memory>

namespace enc
{

  Coord FireballFactory::findBestArgs(const Combatant &combatant) const
  {
    // Implement this method using the Map class and find_best_placement_harmful_circular function
    return Coord{0, 0}; // Placeholder
  }

  std::vector<std::shared_ptr<Actoid>> FireballFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs(*_combatant);
    return {std::make_unique<Fireball>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> FireballFactory::create(void *target)
  {
    Coord* coord = static_cast<Coord*>(target);
    return std::make_shared<Fireball>(*coord, *this);
  }

  double FireballFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) { return 0; }
  double FireballFactory::calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/)
  {
    // No need for this ability
    return 0;
  }
  double FireballFactory::calculateMaxThreat()
  {
    auto bestCoord = findBestArgs(*_combatant);
    return Fireball(bestCoord, *this).calculateThreat(Kwargs());
  }

  double Fireball::calculateThreat(const Kwargs &kwargs) { return 0; }
  double Fireball::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) { return 0; }
  double Fireball::calculateThreatDelta(/*Add modifiers*/ const Kwargs &kwargs) { return 0; }
}