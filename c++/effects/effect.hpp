#pragma once

#include <memory>
#include "core/types.hpp"

namespace enc
{

  class Combatant;
  enum class EffectType
  {
    POST_HASTE_LETHARGY,
    WILDSHAPE,
    RAGE,
    HASTE,
    TWINNED_HASTE,
    DODGE,
    DISENGAGE,
    HIDE,
    RECKLESS_ATTACK,
    FLAMING_SPHERE,
    SPIKE_GROWTH,
    CLOUD_OF_DAGGERS,
    HUNGER_OF_HADAR,
    HOLD_PERSON,
    FAERIE_FIRE,
    DIGESTION,
    REGENERATION,
    BLESS,
    RAY_OF_ENFEEBLEMENT,
    RAY_OF_FROST,
    SLEEP,
    SHILLELAGH,
    MENACING_ATTACK_FRIGHTENED,
    PARALYZING_ATTACK_PARALYZED,
    SHIELD_OF_FAITH,
    VOW_OF_ENMITY,
    INNATE_SORCERY,
    MOONBEAM,
    STARRY_WISP,
    MAGE_ARMOR,
    ROAR_FRIGHTENED,
    SLOWED,
    SAPPED,
    VEXED,
    GUIDING_BOLT,
  };

  class Effect : public std::enable_shared_from_this<Effect>
  {
  public:
    explicit Effect(Combatant *initiator, Combatant *target = nullptr) : _initiator(initiator), _target(target) {}
    virtual ~Effect() = default;

    // Pure virtual methods (must be implemented by derived classes)
    virtual EffectType getEffectType() const = 0;
    virtual void activate(const Kwargs &kwargs = {}) = 0;
    virtual void deactivate() = 0;
    virtual bool deactivateForCombatant(Combatant *combatant) = 0;
    virtual bool isAffecting(Combatant *combatant) const = 0;

    virtual bool startOfTurnTick()
    {
      return true; // Default: effect continues
    }

    // Virtual methods with default implementations
    virtual bool combatantSavedAtEndOfTurn(Combatant *combatant)
    {
      return true; // Default: abilities that cannot be saved against
    }

    virtual bool startOfTurnForCombatant(Combatant *combatant)
    {
      return true; // Default: all abilities
    }

    virtual bool newTurn() { return true; }

    // Non-virtual methods
    Combatant *getInitiator() const { return _initiator; }
    Combatant *getTarget() const { return _target; }

  protected:
    Combatant *_initiator;
    Combatant *_target; // only relevant for Hide as of now
  };
}
