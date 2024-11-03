#pragma once

#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "effects/effect.hpp"

namespace enc
{
  class EffectTracker
  {
  public:
    EffectTracker() = default;

    void add(std::shared_ptr<Effect> effect);

    void remove(std::shared_ptr<Effect> effect);

    void startOfTurnTick(Combatant *combatant);

    void startOfTurn(Combatant *combatant);

    void endOfTurn(Combatant *combatant);

    std::unordered_set<std::shared_ptr<Effect>> getAffectingCombatant(Combatant *combatant) const;

    bool isAffectingCombatant(Combatant *combatant, EffectType effectType) const;

    std::vector<std::shared_ptr<Effect>> getAoeEffects() const;

    std::vector<std::shared_ptr<Effect>> getEffectsByInitiator(Combatant *initiator) const;

    void combatantDied(Combatant *combatant);

    void createPostHasteLethargy(Combatant *initiator, Combatant *combatant);

    void removeEffectFromCombatantByType(Combatant *combatant, EffectType effectType);

    void removeEffectFromCombatant(Combatant *combatant, std::shared_ptr<Effect> effect);

    bool isCombatantHiddenFrom(Combatant *combatant, Combatant *target) const;

    // bool isAffectedByVowOfEnmity(Combatant *initiator, Combatant *target) const;

    void reset();

  private:
    std::vector<std::shared_ptr<Effect>> _effects;
  };
}
