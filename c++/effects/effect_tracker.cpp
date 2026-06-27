#include "effects/effect_tracker.hpp"
#include "effects/aoe_square_effect.hpp"
#include "effects/aoe_spheric_effect.hpp"
#include <algorithm>

namespace enc
{
  std::weak_ptr<Effect> EffectTracker::add(std::shared_ptr<Effect> effect)
  {
    // Avoid double-tracking the same effect. Concentration spells call setConcentrationEffect()
    // during activate(), which re-adds an effect the action resolver already inserted. A duplicate
    // entry would be processed twice each round and linger as a zombie after the original is removed.
    if(std::find(_effects.begin(), _effects.end(), effect) != _effects.end())
      {
        return std::weak_ptr<Effect>(effect);
      }
    _effects.push_back(effect);
    return std::weak_ptr<Effect>(effect);
  }

  void EffectTracker::remove(const std::shared_ptr<Effect> &effect)
  {
    effect->deactivate();
    _effects.erase(std::remove(_effects.begin(), _effects.end(), effect), _effects.end());
  }

  void EffectTracker::startOfTurnTick(Combatant *combatant)
  {
    // Iterate over a snapshot: deactivate() on a concentration effect calls breakConcentration(),
    // which removes from _effects and would invalidate a live iterator over _effects.
    std::vector<std::shared_ptr<Effect>> snapshot = _effects;
    std::vector<std::shared_ptr<Effect>> remainingEffects;

    for(const auto &effect : snapshot)
      {
        if(effect->getInitiator() == combatant)
          {
            bool keep = effect->startOfTurnTick();
            if(!keep)
              {
                effect->deactivate();
                continue; // Effect expired
              }
          }
        remainingEffects.push_back(effect); // Effect persists
      }
    _effects = std::move(remainingEffects);
  }

  void EffectTracker::startOfTurn(Combatant *combatant)
  {
    // Iterate over a snapshot: deactivateForCombatant() on a concentration effect calls
    // breakConcentration(), which removes from _effects and would invalidate a live iterator.
    std::vector<std::shared_ptr<Effect>> snapshot = _effects;
    std::vector<std::shared_ptr<Effect>> remainingEffects;

    for(const auto &effect : snapshot)
      {
        if(effect->isAffecting(combatant))
          {
            if(!effect->startOfTurnForCombatant(combatant))
              {
                effect->deactivateForCombatant(combatant);
                continue; // Effect's been cancelled
              }
          }
        remainingEffects.push_back(effect);
      }
    _effects = std::move(remainingEffects);
  }

  void EffectTracker::endOfTurn(Combatant *combatant)
  {
    // Iterate over a snapshot: a successful save calls deactivateForCombatant(), which for a
    // concentration spell calls breakConcentration() -> remove(), mutating _effects mid-loop.
    // Iterating _effects directly would invalidate the iterator and crash.
    std::vector<std::shared_ptr<Effect>> snapshot = _effects;
    std::vector<std::shared_ptr<Effect>> remainingEffects;

    for(const auto &effect : snapshot)
      {
        if(effect->isAffecting(combatant))
          {
            if(!effect->combatantSavedAtEndOfTurn(combatant))
              {
                if(!effect->deactivateForCombatant(combatant))
                  {
                    continue; // Effect's been saved against or ceased
                  }
              }
          }
        remainingEffects.push_back(effect);
      }
    _effects = std::move(remainingEffects);
  }

  std::unordered_set<std::shared_ptr<Effect>> EffectTracker::getAffectingCombatant(Combatant *combatant) const
  {
    std::unordered_set<std::shared_ptr<Effect>> affectingEffects;
    for(const auto &effect : _effects)
      {
        if(effect->isAffecting(combatant))
          {
            affectingEffects.insert(effect);
          }
      }
    return affectingEffects;
  }

  bool EffectTracker::isAffectingCombatant(Combatant *combatant, EffectType effectType) const
  {
    for(const auto &effect : _effects)
      {
        if(effect->getEffectType() == effectType && effect->isAffecting(combatant))
          {
            return true;
          }
      }
    return false;
  }

  std::vector<std::shared_ptr<AoeEffect>> EffectTracker::getAoeEffects() const
  {
    std::vector<std::shared_ptr<AoeEffect>> aoeEffects;
    for(const auto &effect : _effects)
      {
        if(auto aoeEffect = std::dynamic_pointer_cast<AoeEffect>(effect))
          {
            aoeEffects.push_back(aoeEffect);
          }
      }
    return aoeEffects;
  }

  std::vector<std::shared_ptr<Effect>> EffectTracker::getEffectsByInitiator(Combatant *initiator) const
  {
    std::vector<std::shared_ptr<Effect>> initiatorEffects;
    for(const auto &effect : _effects)
      {
        if(effect->getInitiator() == initiator)
          {
            initiatorEffects.push_back(effect);
          }
      }
    return initiatorEffects;
  }

  std::vector<std::shared_ptr<Effect>> EffectTracker::getEffectsByType(EffectType effectType) const
  {
    std::vector<std::shared_ptr<Effect>> matching;
    for(const auto &effect : _effects)
      {
        if(effect->getEffectType() == effectType)
          {
            matching.push_back(effect);
          }
      }
    return matching;
  }

  void EffectTracker::combatantDied(Combatant *combatant)
  {
    // Work from a snapshot because deactivating concentration effects can recursively mutate _effects.
    std::vector<std::shared_ptr<Effect>> snapshot = _effects;
    std::vector<std::shared_ptr<Effect>> remainingEffects;

    for(const auto &effect : snapshot)
      {
        if(effect->getInitiator() == combatant)
          {
            effect->deactivate();
            continue;
          }
        else if(effect->isAffecting(combatant))
          {
            if(!effect->deactivateForCombatant(combatant))
              {
                continue;
              }
          }

        remainingEffects.push_back(effect);
      }
    _effects = std::move(remainingEffects);
  }

  // void createPostHasteLethargy(Combatant *initiator, Combatant *combatant)
  // {
  //   _effects.push_back(std::make_shared<PostHasteLethargyEffect>(initiator, combatant));
  // }

  void EffectTracker::removeEffectFromCombatantByType(Combatant *combatant, EffectType effectType)
  {
    std::vector<std::shared_ptr<Effect>> remainingEffects;
    for(const auto &effect : _effects)
      {
        if(effect->isAffecting(combatant) && effect->getEffectType() == effectType)
          {
            if(!effect->deactivateForCombatant(combatant))
              {
                continue;
              }
          }
        remainingEffects.push_back(effect);
      }
    _effects = std::move(remainingEffects);
  }

  void EffectTracker::removeEffectFromCombatant(Combatant *combatant, const std::shared_ptr<Effect>& effect)
  {
    if(!effect->deactivateForCombatant(combatant))
      {
        _effects.erase(std::remove(_effects.begin(), _effects.end(), effect), _effects.end());
      }
  }

  bool EffectTracker::isCombatantHiddenFrom(Combatant *combatant, Combatant *target) const
  {
    for(const auto &effect : getEffectsByInitiator(combatant))
      {
        if(effect->getEffectType() == EffectType::HIDE && effect->getTarget() == target)
          {
            return true;
          }
      }
    return false;
  }

//   bool EffectTracker::isAffectedByVowOfEnmity(Combatant *initiator, Combatant *target) const
//   {
//     for(const auto &effect : getEffectsByInitiator(initiator))
//       {
//         if(effect->getEffectType() == EffectType::VOW_OF_ENMITY && !effect->getCombatants().empty() && effect->getCombatants()[0] == target)
//           {
//             return true;
//           }
//       }
//     return false;
//   }

  void EffectTracker::reset()
  {
    // Iterate over a snapshot: deactivate() on a concentration effect calls breakConcentration(),
    // which removes from _effects and would invalidate a live iterator over _effects (mirrors
    // startOfTurnTick). The final clear() guarantees the tracker ends empty for the next iteration.
    std::vector<std::shared_ptr<Effect>> snapshot = _effects;
    for(const auto &effect : snapshot)
      {
        effect->deactivate();
      }
    _effects.clear();
  }
}
