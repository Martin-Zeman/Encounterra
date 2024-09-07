#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"
#include "abilities/on_hit_effect.hpp"
#include <vector>

namespace enc
{
  class Combatant;

  class AttackFactory : public DirectThreatFactory
  {
  public:
    AttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                  int attackRange, int critRange = 1, Uses &&ammo = Uses(), std::vector<std::unique_ptr<OnHit>> onHit = {},
                  std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false, bool twoHanded = false, Die toHitBonusDie = {});

    AttackFactory(const AttackFactory& other);

    AttackFactory(AttackFactory&& other) noexcept;

    AttackFactory& operator=(const AttackFactory& other);

    AttackFactory& operator=(AttackFactory&& other) noexcept;

    //! This ensures that you get a proper copy of the derived class, even when working with base class pointers.
    virtual std::unique_ptr<AttackFactory> clone() const = 0;

    std::vector<Combatant *> getEligibleTargets() const;
    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) override;
    double calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/) override;
    double calculateMaxThreat() override;
    bool usesDex() { return _usesDex; }
    bool isTwoHanded() { return _twoHanded; }

  protected:
    std::string _name;
    Combatant *_combatant;
    int _toHit;
    std::vector<Die> _dmgDice;
    int _dmgBonus;
    DamageType _dmgType;
    int _attackRange;
    int _shortRange;
    int _critRange;
    Uses _ammo;
    std::vector<std::unique_ptr<OnHit>> _onHit;
    std::vector<DmgDieWithType> _extraDmg;
    bool _usesDex;
    bool _twoHanded;
    Die _toHitBonusDie;
  };

}
