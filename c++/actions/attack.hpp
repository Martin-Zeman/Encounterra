#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"
#include "abilities/on_hit_effect.hpp"
#include <vector>

namespace enc
{

  class AttackFactory : public DirectThreatFactory
  {
  public:
    AttackFactory(const std::string &name, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange = 1,
                  Uses &&ammo, OnHit *onHit = nullptr, std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false, bool twoHanded = false,
                  Die toHitBonusDie = {})
        : _name(name), _toHit(toHit), _dmgDice(dmgDice), _dmgBonus(dmgBonus), _dmgType(dmgType), _attackRange(attackRange), _critRange(critRange),
          _ammo(std::move(ammo)), _onHit(onHit), _extraDmg(extraDmg), _usesDex(usesDex), _twoHanded(twoHanded), _toHitBonusDie(toHitBonusDie)
    {}

    double calculateThreatToTarget(ICombatant *target) override;
    double calculateThreatToTargetDelta(ICombatant *target /*Add modifiers*/) override;
    double calculateMaxThreat() override;

  protected:
    std::string _name;
    int _toHit;
    std::vector<Die> _dmgDice;
    int _dmgBonus;
    DamageType _dmgType;
    int _attackRange;
    int _critRange;
    Uses _ammo;
    OnHit *_onHit;
    std::vector<DmgDieWithType> _extraDmg;
    bool _usesDex;
    bool _twoHanded;
    Die _toHitBonusDie;
  };

}
