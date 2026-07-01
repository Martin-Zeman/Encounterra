#include "abilities/on_hit_sneak_attack.hpp"
#include "actions/attack.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <iostream>

namespace enc
{
  Die OnHitSneakAttack::getDmgDice(int level)
  {
    // 1d6 at levels 1-2, 2d6 at 3-4, 3d6 at 5-6, ... = ceil(level / 2) d6.
    int numDice = (level + 1) / 2;
    if(numDice < 1)
      {
        numDice = 1;
      }
    return Die{static_cast<unsigned char>(numDice), 6};
  }

  std::vector<std::pair<int, DamageType>>
  OnHitSneakAttack::hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar)
  {
    if(attacker == nullptr || target == nullptr)
      {
        return {};
      }

    // A rogue with Disadvantage on the attack roll cannot land a Sneak Attack.
    RollType rollType = RollType::STRAIGHT;
    if(auto *concreteAttack = dynamic_cast<Attack *>(attack))
      {
        rollType = concreteAttack->getRollType();
      }
    if(rollType == RollType::DISADVANTAGE)
      {
        return {};
      }

    if(attacker->hasAlreadyUsedSneakAttackThisTurn())
      {
        return {};
      }

    // Sneak Attack triggers with Advantage on the roll, or when an ally of the rogue is within 5 ft of the target.
    bool allyAdjacent = BattleMap::getInstance().isAllyAdjacentToTarget(*attacker, *target);
    if(rollType != RollType::ADVANTAGE && !allyAdjacent)
      {
        return {};
      }

    attacker->setAlreadyUsedSneakAttackThisTurn(true);
    int dmg = rollDiceMulti(_dmgDice);
    if(multiplier >= 2)
      {
        dmg *= 2;
      }
    std::cout << attacker->_name << " lands a Sneak Attack on " << target->_name << " for " << dmg << " damage" << std::endl;
    return {{dmg, _dmgType}};
  }

  double OnHitSneakAttack::calculateThreat(Combatant *attacker, Combatant *target, RollType rollType)
  {
    if(attacker == nullptr || target == nullptr)
      {
        return 0.0;
      }
    // Mirror Python OnHitSneakAttack.calculate_threat. Disadvantage disables Sneak Attack outright.
    if(rollType == RollType::DISADVANTAGE)
      {
        return 0.0;
      }
    if(attacker->hasAlreadyUsedSneakAttackThisTurn())
      {
        return 0.0;
      }
    // Sneak Attack is credited only when the rogue has Advantage on the roll (e.g. after Hide) or an ally is within
    // 5 ft of the target. The base attack-threat path calls this with a STRAIGHT roll, so a lone rogue's melee
    // attack is not over-valued by ~3d6 (which would wrongly out-score a genuine Disengage/Dash flee); the
    // Advantage credit is supplied by Hide::calculateThreatForAttack passing RollType::ADVANTAGE.
    if(rollType != RollType::ADVANTAGE && !BattleMap::getInstance().isAllyAdjacentToTarget(*attacker, *target))
      {
        return 0.0;
      }
    double avg = avgRollMulti(_dmgDice);
    return avg + 0.05 * _critRange * avg;
  }
}
