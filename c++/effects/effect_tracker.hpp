#pragma once

// #include "core/battle_map.hpp"
#include "effects/effect.hpp"
#include "effects/aoe_effect.hpp"
#include <unordered_set>

namespace enc
{
  class Combatant;

  class EffectTracker
  {
  public:
    // Delete copy constructor and assignment operator
    EffectTracker(const EffectTracker &) = delete;
    EffectTracker &operator=(const EffectTracker &) = delete;

    // Singleton access method
    static EffectTracker &getInstance()
    {
      static EffectTracker instance;
      return instance;
    }

    // Reset singleton for testing
    static void resetInstance()
    {
      auto &instance = getInstance();
      instance.reset();
    }

    std::weak_ptr<Effect> add(std::shared_ptr<Effect> effect);

    void remove(const std::shared_ptr<Effect> &effect);

    void startOfTurnTick(const Combatant &combatant);

    void startOfTurn(Combatant &ombatant);

    void endOfTurn(Combatant &combatant);

    std::vector<std::weak_ptr<Effect>> getAffectingCombatant(const Combatant &combatant) const;

    bool isAffectingCombatant(const Combatant &combatant, EffectType effectType) const;

    std::vector<std::weak_ptr<AoeEffect>> getAoeEffects() const;

    std::vector<std::weak_ptr<Effect>> getEffectsByInitiator(const Combatant &initiator) const;

    void combatantDied(const Combatant &combatant);

    void createPostHasteLethargy(const Combatant &initiator, const Combatant &combatant);

    void removeEffectFromCombatantByType(Combatant &combatant, EffectType effectType);

    void removeEffectFromCombatant(Combatant &combatant, const std::shared_ptr<Effect> &effect);

    bool isCombatantHiddenFrom(const Combatant &combatant, const Combatant &target) const;

    // bool isAffectedByVowOfEnmity(const Combatant&initiator, const Combatant&target) const;

    void reset();

  private:
    EffectTracker() = default;

    std::vector<std::shared_ptr<Effect>> _effects;
  };
}
