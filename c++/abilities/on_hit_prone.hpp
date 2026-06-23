#pragma once

#include <memory>
#include "abilities/on_hit_effect.hpp"
#include "core/misc.hpp"

namespace enc
{
  class Combatant;
  class Actoid;

  /**
   * On-hit rider that knocks the target Prone.
   *
   * Two flavours, both mirroring the Python simulator/abilities/on_hit_prone.py:
   *  - Save-based (e.g. Tiger Pounce): the target rolls the given saving throw against _dc; on a failure
   *    it gains the Prone condition.
   *  - Automatic (e.g. 2024 Dire Wolf Bite): no saving throw; the target gains the Prone condition outright,
   *    provided it is no larger than _maxSize ("Huge or smaller").
   * Applies no extra damage and (like the grapple rider) contributes no direct threat of its own.
   */
  class OnHitProne : public OnHit
  {
  public:
    // Save-based prone (no size restriction).
    OnHitProne(SavingThrow saveType, int dc) : _requiresSave(true), _saveType(saveType), _dc(dc), _maxSize(Size::GARGANTUAN) {}

    // Automatic prone with no saving throw, gated on the target being no larger than maxSize.
    explicit OnHitProne(Size maxSize) : _requiresSave(false), _saveType(SavingThrow::STR), _dc(0), _maxSize(maxSize) {}

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target) override { return 0.0; }

    bool requiresSave() const { return _requiresSave; }
    SavingThrow getSaveType() const { return _saveType; }
    int getDc() const { return _dc; }
    Size getMaxSize() const { return _maxSize; }

    std::unique_ptr<OnHit> clone() const override
    {
      return _requiresSave ? std::make_unique<OnHitProne>(_saveType, _dc) : std::make_unique<OnHitProne>(_maxSize);
    }

  private:
    bool _requiresSave;
    SavingThrow _saveType;
    int _dc;
    Size _maxSize;
  };
}
