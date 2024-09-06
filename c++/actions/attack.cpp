#include "actions/attack.hpp"
#include "core/teams.hpp"

namespace enc
{

  std::vector<Combatant *> AttackFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }

    Teams &teams = Teams::getInstance();
    return teams.getAliveNonSwallowedEnemies(*_combatant);
  }

  double AttackFactory::calculateThreatToTarget(Combatant *target, const Kwargs& kwargs)
  {
    bool considerDist = false;
    RollType rollType = RollType::STRAIGHT;

    // Extract parameters from kwargs
    if(kwargs.find("consider_dist") != kwargs.end())
      {
        considerDist = std::any_cast<bool>(kwargs.at("consider_dist"));
      }
    if(kwargs.find("roll_type") != kwargs.end())
      {
        rollType = std::any_cast<RollType>(kwargs.at("roll_type"));
      }

    int toHitTotal = _toHit;
    toHitTotal += getRollTypeDelta(rollType, std::max(0, std::min(target->getAC() - toHitTotal, 20)));
    if (_toHitBonusDie[0] > 0)
    {
        toHitTotal += avgRoll(_toHitBonusDie);
    }

    // if (!considerDist || Map::getInstance().getHopDistanceCombatants(_combatant, target) <= _attackRange)
    // {
    //     double acc = meanDmg(toHitTotal, _dmgDice, _dmgBonus, target->getAC(),
    //                          target->isImmuneTo(_dmgType), target->isResistantTo(_dmgType),
    //                          _critRange);

    //     for (const auto& extra : _extraDmg)
    //     {
    //         acc += meanDmg(toHitTotal, {extra.die}, 0, target->getAC(),
    //                        target->isImmuneTo(extra.type), target->isResistantTo(extra.type),
    //                        _critRange);
    //     }

    //     for (const auto& oh : _onHit)
    //     {
    //         acc += calcPHit(toHitTotal, target->getAC()) * oh->calculateThreat(_combatant, target);
    //     }

    //     return acc;
    // }

    return 0.0;
  }

  double AttackFactory::calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/)
  {
    //! @todo
    return 0;
  }
  double AttackFactory::calculateMaxThreat()
  {
    //! @todoa
    return 0;
  }
}