#pragma once

#include <cstdint>
#include <memory>

namespace enc
{

  class Combatant;

  enum class EffectType : uint32_t
  {
    POST_HASTE_LETHARGY = 1 << 0,
    WILDSHAPE = 1 << 1,
    RAGE = 1 << 2,
    TOTEM_RAGE = 1 << 3,
    HASTE = 1 << 4,
    TWINNED_HASTE = 1 << 5,
    DODGE = 1 << 6,
    DISENGAGE = 1 << 7,
    HIDE = 1 << 8,
    RECKLESS_ATTACK = 1 << 9,
    FLAMING_SPHERE = 1 << 10,
    SPIKE_GROWTH = 1 << 11,
    CLOUD_OF_DAGGERS = 1 << 12,
    HUNGER_OF_HADAR = 1 << 13,
    HOLD_PERSON = 1 << 14,
    FAERIE_FIRE = 1 << 15,
    DIGESTION = 1 << 16,
    REGENERATION = 1 << 17,
    BLESS = 1 << 18,
    RAY_OF_ENFEEBLEMENT = 1 << 19,
    RAY_OF_FROST = 1 << 20,
    SLEEP = 1 << 21,
    SHILLELAGH = 1 << 22,
    MENACING_ATTACK_FRIGHTENED = 1 << 23,
    PARALYZING_ATTACK_PARALYZED = 1 << 24,
    SHIELD_OF_FAITH = 1 << 25,
    VOW_OF_ENMITY = 1 << 26
  };

  class Effect
  {
  public:
    Effect(const Combatant *initiator) : initiator(initiator) {}
    virtual ~Effect() = default;

    virtual EffectType getEffectType() const = 0;
    virtual void activate(/* ... */) = 0;
    virtual void deactivate() = 0;
    virtual bool deactivateForCombatant(const Combatant &combatant) = 0;
    virtual bool isAffecting(const Combatant &combatant) const = 0;

    virtual bool combatantSavedAtEndOfTurn(const Combatant &combatant) { return true; }
    virtual bool startOfTurnForCombatant(const Combatant &combatant) { return true; }
    virtual bool newTurn() { return true; }

  protected:
    const Combatant *initiator;
  };
}
