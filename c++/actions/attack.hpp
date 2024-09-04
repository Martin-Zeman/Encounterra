#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include <vector>

namespace enc
{

  class AttackFactory : public DirectThreatFactory
  {
  public:
    AttackFactory(const std::string &name, int toHit, std::vector<std::pair<int, int>> dmgDice, int dmgBonus, DamageType dmgType, int attackRange)
        : _name(name), _toHit(toHit), _dmgDice(dmgDice), _dmgBonus(dmgBonus), _dmgType(dmgType), _attackRange(attackRange)
    {}

    double calculateThreatToTarget(ICombatant *target) override;
    double calculateThreatToTargetDelta(ICombatant *target /*Add modifiers*/) override;
    double calculateMaxThreat() override;

  protected:
    std::string _name;
    int _toHit;
    std::vector<std::pair<int, int>> _dmgDice;
    int _dmgBonus;
    DamageType _dmgType;
    int _attackRange;
  };

}
