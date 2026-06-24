#include "abilities/on_hit_mastery.hpp"

#include <algorithm>
#include <iostream>

#include "abilities/weapon_mastery_effects.hpp"
#include "actions/attack.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  namespace
  {
    //! Cleave: on a hit, make one extra attack against a second enemy within 5 ft of the first target that is
    //! within the wielder's reach (once per turn). The second hit deals the weapon's dice only (no ability
    //! modifier), per the 2024 rules.
    void resolveCleave(Combatant *attacker, AttackFactory &factory, Combatant *firstTarget)
    {
      if(!attacker->tryUseMasteryThisTurn(WeaponMastery::CLEAVE))
        {
          return; // Cleave can be used only once per turn.
        }
      auto &battleMap = BattleMap::getInstance();
      int reach = factory.getRange();
      Combatant *second = nullptr;
      for(Combatant *candidate : battleMap.getNonSwallowedEnemiesWithinRadius(firstTarget, 1))
        {
          if(candidate == firstTarget || candidate == attacker || !candidate->isAlive())
            {
              continue;
            }
          if(battleMap.getHopDistanceCombatants(*attacker, *candidate) <= reach)
            {
              second = candidate;
              break;
            }
        }
      if(second == nullptr)
        {
          return;
        }
      Die d20{1, 20};
      int rolled = rollDice(d20);
      std::cout << attacker->_name << " Cleaves into " << second->_name << std::endl;
      if(rolled != 1 && (rolled == 20 || rolled + factory.getToHit() >= second->getAC()))
        {
          int multiplier = (rolled == 20) ? 2 : 1;
          int dmg = std::max(0, multiplier * rollDiceMulti(factory.getDmgDice()));
          second->receiveDmg(dmg, factory.getDmgType(), multiplier);
          battleMap.removeCombatantIfDead(*second);
        }
    }
  }

  std::vector<std::pair<int, DamageType>>
  OnHitMastery::hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double /*dmgSoFar*/)
  {
    auto *factory = attack ? dynamic_cast<AttackFactory *>(&attack->getFactory()) : nullptr;
    auto &effectTracker = EffectTracker::getInstance();
    auto &battleMap = BattleMap::getInstance();

    switch(_mastery)
      {
      case WeaponMastery::CLEAVE:
        if(factory)
          {
            resolveCleave(attacker, *factory, target);
          }
        break;

      case WeaponMastery::PUSH:
        // Push a Large-or-smaller target up to 10 ft (2 cells) straight away from the wielder.
        if(target->getSize() <= Size::LARGE)
          {
            std::cout << attacker->_name << " pushes " << target->_name << " away" << std::endl;
            battleMap.pushCombatantAwayFrom(battleMap.getCombatantCoordinates(*attacker).getCenter(), target, 2);
          }
        break;

      case WeaponMastery::SAP:
        // The target has Disadvantage on its next attack roll before the wielder's next turn.
        if(!effectTracker.isAffectingCombatant(target, EffectType::SAPPED))
          {
            std::cout << target->_name << " is Sapped" << std::endl;
            auto effect = std::make_shared<SappedEffect>(target);
            effectTracker.add(effect);
            effect->activate();
          }
        break;

      case WeaponMastery::SLOW:
        // Reduce the target's Speed by 10 ft until the start of the wielder's next turn.
        if(!effectTracker.isAffectingCombatant(target, EffectType::SLOWED))
          {
            std::cout << target->_name << " is Slowed" << std::endl;
            auto effect = std::make_shared<SlowedEffect>(attacker, target);
            effectTracker.add(effect);
            effect->activate();
          }
        break;

      case WeaponMastery::TOPPLE:
        // The target makes a Constitution save (DC 8 + ability modifier + proficiency) or is knocked Prone.
        if(factory && !target->isAffectedBy(Conditions::PRONE))
          {
            int proficiency = 2 + (attacker->getLevel() - 1) / 4;
            int dc = 8 + factory->getDmgBonus() + proficiency;
            if(!rollSavingThrow(target->getSavingThrow(SavingThrow::CON), dc, RollType::STRAIGHT))
              {
                std::cout << target->_name << " is knocked Prone by Topple (DC " << dc << ")" << std::endl;
                target->applyCondition(Condition(Conditions::PRONE, attacker, nullptr, target));
              }
          }
        break;

      case WeaponMastery::VEX:
        // The wielder has Advantage on its next attack roll against this target.
        std::cout << attacker->_name << " has Advantage (Vex) against " << target->_name << std::endl;
        {
          auto effect = std::make_shared<VexedEffect>(attacker, target);
          effectTracker.add(effect);
          effect->activate();
        }
        break;

      case WeaponMastery::GRAZE:
      case WeaponMastery::NICK:
      case WeaponMastery::NONE:
        break; // Handled outside the on-hit path (or intentionally inert).
      }

    return {};
  }
}
