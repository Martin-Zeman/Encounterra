#pragma once

#include <memory>
#include <string>
#include <vector>
#include "abilities/on_hit_effect.hpp"
#include "core/misc.hpp"

namespace enc
{
  class Combatant;
  class Actoid;

  /**
   * On-hit rider that deals additional saving-throw damage (e.g. the Giant Spider's Bite venom).
   *
   * Mirrors the Python simulator/abilities/on_hit_saving_throw_dmg.py. On a hit, the target rolls
   * the given saving throw against _dc. On a failure it takes the full rolled damage; on a success it
   * takes half (when _halfOnSuccess) or none. On a critical hit the damage dice are doubled, matching
   * the base-attack crit handling. The threat contribution is the expected damage given the save,
   * computed with meanDmgDcAttack (the resolver multiplies by P(hit)).
   */
  class OnHitSavingThrowDmg : public OnHit
  {
  public:
    OnHitSavingThrowDmg(SavingThrow saveType, int dc, std::vector<Die> dmgDice, DamageType dmgType, bool halfOnSuccess,
                        std::string name = "")
        : _saveType(saveType), _dc(dc), _dmgDice(std::move(dmgDice)), _dmgType(dmgType), _halfOnSuccess(halfOnSuccess),
          _name(std::move(name))
    {}

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target, RollType rollType = RollType::STRAIGHT) override;

    std::unique_ptr<OnHit> clone() const override
    {
      return std::make_unique<OnHitSavingThrowDmg>(_saveType, _dc, _dmgDice, _dmgType, _halfOnSuccess, _name);
    }

  private:
    SavingThrow _saveType;
    int _dc;
    std::vector<Die> _dmgDice;
    DamageType _dmgType;
    bool _halfOnSuccess;
    std::string _name;
  };
}
