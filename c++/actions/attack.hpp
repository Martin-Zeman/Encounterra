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
                  int attackRange, int critRange = 1, Uses &&ammo = Uses(), OnHit *onHit = nullptr, std::vector<DmgDieWithType> extraDmg = {},
                  bool usesDex = false, bool twoHanded = false, Die toHitBonusDie = {})
        : DirectThreatFactory(), _name(name), _combatant(combatant), _toHit(toHit), _dmgDice(dmgDice), _dmgBonus(dmgBonus), _dmgType(dmgType),
          _attackRange(attackRange), _shortRange(attackRange / 4), _critRange(critRange), _ammo(std::move(ammo)), _onHit(onHit), _extraDmg(extraDmg),
          _usesDex(usesDex), _twoHanded(twoHanded), _toHitBonusDie(toHitBonusDie)
    {
      setFlag(FactoryFlags::IS_ATTACK_LIKE);
      setFlag(FactoryFlags::IS_HASTE_ELIGIBLE_ATTACK);
    }

    //! This ensures that you get a proper copy of the derived class, even when working with base class pointers.
    virtual std::unique_ptr<AttackFactory> clone() const = 0;

    std::vector<Combatant *> getEligibleTargets() const;
    double calculateThreatToTarget(Combatant *target) override;
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
    OnHit *_onHit;
    std::vector<DmgDieWithType> _extraDmg;
    bool _usesDex;
    bool _twoHanded;
    Die _toHitBonusDie;
  };

}
