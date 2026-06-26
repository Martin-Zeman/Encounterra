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
    EffectTracker(const EffectTracker&) = delete;
    EffectTracker& operator=(const EffectTracker&) = delete;

    // Singleton access method.
    // thread_local: each worker thread gets its own independent EffectTracker so simulations can run in
    // parallel without sharing the (mutable, non-thread-safe) singleton state.
    static EffectTracker& getInstance() {
        static thread_local EffectTracker instance;
        return instance;
    }

    // Reset singleton for testing
    static void resetInstance() {
        auto& instance = getInstance();
        instance.reset();
    }

    // For test teardown: clear effects without calling deactivate (factories may be destroyed).
    void clearEffects() { _effects.clear(); }

    std::weak_ptr<Effect> add(std::shared_ptr<Effect> effect);

    void remove(const std::shared_ptr<Effect> &effect);

    void startOfTurnTick(Combatant *combatant);

    void startOfTurn(Combatant *combatant);

    void endOfTurn(Combatant *combatant);

    std::unordered_set<std::shared_ptr<Effect>> getAffectingCombatant(Combatant *combatant) const;

    bool isAffectingCombatant(Combatant *combatant, EffectType effectType) const;

    std::vector<std::shared_ptr<AoeEffect>> getAoeEffects() const;

    std::vector<std::shared_ptr<Effect>> getEffectsByInitiator(Combatant *initiator) const;

    std::vector<std::shared_ptr<Effect>> getEffectsByType(EffectType effectType) const;

    void combatantDied(Combatant *combatant);

    void createPostHasteLethargy(Combatant *initiator, Combatant *combatant);

    void removeEffectFromCombatantByType(Combatant *combatant, EffectType effectType);

    void removeEffectFromCombatant(Combatant *combatant, const std::shared_ptr<Effect>& effect);

    bool isCombatantHiddenFrom(Combatant *combatant, Combatant *target) const;

    // bool isAffectedByVowOfEnmity(Combatant *initiator, Combatant *target) const;

    void reset();

  private:
    EffectTracker() = default;

    std::vector<std::shared_ptr<Effect>> _effects;
  };
}
