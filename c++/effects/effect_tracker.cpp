#include "effects/effect_tracker.hpp"
#include "effects/aoe_square_effect.hpp"
#include "effects/aoe_spheric_effect.hpp"

namespace enc
{
  Effect* EffectTracker::add(Effect* effect)
  {
    _effects.push_back(effect);
    return _effects.back();
  }

  void EffectTracker::remove(Effect* effect)
  {
    effect->deactivate();
    _effects.erase(std::remove(_effects.begin(), _effects.end(), effect), _effects.end());
  }

  void EffectTracker::startOfTurnTick(const Combatant &combatant)
  {
    std::vector<Effect *> remainingEffects;

    for(const auto &effect : _effects)
      {
        if(&combatant == effect->getInitiator())
          {
            bool keep = effect->startOfTurnTick();
            if(!keep)
              {
                effect->deactivate();
                continue; // Effect expired
              }
          }
        remainingEffects.push_back(effect);  // Effect persists
      }
    _effects = std::move(remainingEffects);
  }

  void EffectTracker::startOfTurn(Combatant &combatant)
  {
    std::vector<Effect *> remainingEffects;

    for(const auto &effect : _effects)
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

  void EffectTracker::endOfTurn(Combatant &combatant)
  {
    std::vector<Effect *> remainingEffects;

    for(const auto &effect : _effects)
      {
        if(effect->isAffecting(combatant))
          {
            if(!effect->combatantSavedAtEndOfTurn(combatant))
              {
                if(!effect->deactivateForCombatant(combatant))
                  {
                    continue;
                  }
              }
          }
        remainingEffects.push_back(effect);
      }
    _effects = std::move(remainingEffects);
  }

  std::vector<Effect *> EffectTracker::getAffectingCombatant(const Combatant &combatant) const
  {
    std::vector<Effect *> affectingEffects;
    for(const auto &effect : _effects)
      {
        if(effect->isAffecting(combatant))
          {
            affectingEffects.push_back(effect);
          }
      }
    return affectingEffects;
  }

  bool EffectTracker::isAffectingCombatant(const Combatant &combatant, EffectType effectType) const
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

  std::vector<AoeEffect *> EffectTracker::getAoeEffects() const
  {
    std::vector<AoeEffect *> aoeEffects;
    for(const auto &effect : _effects)
      {
        if(auto aoeEffect = dynamic_cast<AoeEffect *>(effect))
          {
            aoeEffects.push_back(aoeEffect);
          }
      }
    return aoeEffects;
  }

  std::vector<Effect *> EffectTracker::getEffectsByInitiator(const Combatant &initiator) const
  {
    std::vector<Effect *> initiatorEffects;
    for(const auto &effect : _effects)
      {
        if(effect->getInitiator() == &initiator)
          {
            initiatorEffects.push_back(effect);
          }
      }
    return initiatorEffects;
  }

  void EffectTracker::combatantDied(const Combatant &combatant)
  {
    auto initiatorEffects = getEffectsByInitiator(combatant);
    for(const auto &effect : initiatorEffects)
      {
        effect->deactivate();
        _effects.erase(
          std::remove_if(_effects.begin(), _effects.end(), [&combatant](const auto &effect) { return effect->getInitiator() == &combatant; }),
          _effects.end());
      }
  }

  // void createPostHasteLethargy(Combatant *initiator, Combatant *combatant)
  // {
  //   _effects.push_back(std::make_shared<PostHasteLethargyEffect>(initiator, combatant));
  // }

  void EffectTracker::removeEffectFromCombatantByType(Combatant &combatant, EffectType effectType)
  {
    std::vector<Effect *> remainingEffects;
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

  void EffectTracker::removeEffectFromCombatant(Combatant &combatant, Effect *effect)
  {
    if(!effect->deactivateForCombatant(combatant))
      {
        _effects.erase(std::remove(_effects.begin(), _effects.end(), effect), _effects.end());
      }
  }

  bool EffectTracker::isCombatantHiddenFrom(const Combatant &combatant, const Combatant &target) const
  {
    for(const auto &effect : getEffectsByInitiator(combatant))
      {
        auto tgt = effect->getTarget();
        if(effect->getEffectType() == EffectType::HIDE && tgt && tgt == &target)
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
    for(const auto &effect : _effects)
      {
        effect->deactivate();
      }
    _effects.clear();
  }
}
