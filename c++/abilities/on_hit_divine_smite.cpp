#include "abilities/on_hit_divine_smite.hpp"

#include "actions/dummy_actoid.hpp"
#include "actions/dummy_actoid_factory.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>
#include <iostream>

namespace enc
{
  namespace
  {
    constexpr const char *PENDING_SMITE_MARKER_NAME = "Pending Divine Smite";
  }

  DivineSmiteFactory::DivineSmiteFactory(Combatant *combatant, Resource *freeCastResource)
      : ThreatModifierFactory("DivineSmiteFactory", "Divine Smite", combatant, AbilityType::DIVINE_SMITE), _freeCastResource(freeCastResource)
  {
    setFlag(FactoryFlags::TARGETS_SELF);
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
  }

  std::vector<std::shared_ptr<Actoid>> DivineSmiteFactory::createAll(void *previousActionInDag)
  {
    return {std::make_shared<DivineSmite>(*this)};
  }

  std::shared_ptr<Actoid> DivineSmiteFactory::create(void *target)
  {
    return std::make_shared<DivineSmite>(*this);
  }

  double DivineSmiteFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    DivineSmite smite(*this);
    double best = 0.0;
    for(const auto &factory : _combatant->getActionFactoriesConst())
      {
        if(auto *attackFactory = dynamic_cast<AttackFactory *>(factory.get()))
          {
            auto attack = attackFactory->create(target);
            best = std::max(best, smite.calculateThreatForAttack(_combatant, attack.get(), {}));
          }
      }
    return best;
  }

  Die OnHitDivineSmite::getDmgDice(int spellSlotLevel)
  {
    return Die{static_cast<unsigned char>(std::clamp(spellSlotLevel + 1, 2, 5)), 8};
  }

  Die OnHitDivineSmite::getDmgDiceUndeadOrFiend(int spellSlotLevel)
  {
    return Die{static_cast<unsigned char>(std::clamp(spellSlotLevel + 2, 3, 6)), 8};
  }

  bool OnHitDivineSmite::isUndeadOrFiend(Combatant *target)
  {
    Combatant *form = target->getOriginalForm();
    return form->isMonsterType(Monster::UNDEAD) || form->isMonsterType(Monster::FIEND);
  }

  bool OnHitDivineSmite::canSmite(Combatant *attacker)
  {
    if(attacker == nullptr || !attacker->hasPassiveAbility(AbilityType::DIVINE_SMITE))
      {
        return false;
      }
    if(auto freeSmite = attacker->getResource(AbilityType::DIVINE_SMITE); freeSmite && (*freeSmite)->hasUses())
      {
        return true;
      }
    if(attacker->hasAlreadyUsedSpellslotThisTurn() && !attacker->hasPendingDivineSmite())
      {
        return false;
      }
    for(int level = 4; level >= 1; --level)
      {
        if(attacker->getSpellslots().hasUses(level))
          {
            return true;
          }
      }
    return false;
  }

  int OnHitDivineSmite::chooseSmiteLevel(Combatant *attacker, Combatant *target, double multiplier, double dmgSoFar)
  {
    if(!canSmite(attacker))
      {
        return 0;
      }
    if(auto freeSmite = attacker->getResource(AbilityType::DIVINE_SMITE); freeSmite && (*freeSmite)->hasUses())
      {
        return 1;
      }

    for(int level = 4; level >= 1; --level)
      {
        if(attacker->getSpellslots().hasUses(level))
          {
            Die dice = isUndeadOrFiend(target) ? getDmgDiceUndeadOrFiend(level) : getDmgDice(level);
            double avgDmg = avgRoll(dice);
            if((target->getCurrentHp() - dmgSoFar) * 1.3 >= avgDmg * multiplier)
              {
                return level;
              }
          }
      }
    return 0;
  }

  std::shared_ptr<Actoid> OnHitDivineSmite::createPendingSmiteMarker()
  {
    return std::make_shared<DummyActoid>(DummyActoidFactory::getInstance(), PENDING_SMITE_MARKER_NAME);
  }

  bool OnHitDivineSmite::isPendingSmiteMarker(const std::shared_ptr<Actoid> &actoid)
  {
    return actoid != nullptr && actoid->toString() == PENDING_SMITE_MARKER_NAME;
  }

  std::vector<std::pair<int, DamageType>>
  OnHitDivineSmite::consumeArmedSmite(Combatant *attacker, Combatant *target, double multiplier, double dmgSoFar)
  {
    if(attacker == nullptr || target == nullptr || !attacker->hasPendingDivineSmite())
      {
        return {};
      }

    int chosenLevel = chooseSmiteLevel(attacker, target, multiplier, dmgSoFar);
    attacker->clearPendingDivineSmite();
    if(chosenLevel == 0)
      {
        return {};
      }

    if(auto freeSmite = attacker->getResource(AbilityType::DIVINE_SMITE); freeSmite && (*freeSmite)->hasUses())
      {
        (*freeSmite)->useResource();
      }
    else
      {
        attacker->getSpellslots().useResource(chosenLevel);
        attacker->setAlreadyUsedSpellslotThisTurn(true);
      }

    Die dice = isUndeadOrFiend(target) ? getDmgDiceUndeadOrFiend(chosenLevel) : getDmgDice(chosenLevel);
    int dmg = rollDice(dice);
    if(multiplier >= 2)
      {
        dmg *= 2;
      }
    std::cout << attacker->_name << " uses Divine Smite of level " << chosenLevel << " on " << target->_name << std::endl;
    return {{dmg, DamageType::Radiant}};
  }

  std::vector<std::pair<int, DamageType>>
  OnHitDivineSmite::hit(Combatant *attacker, Actoid * /*attack*/, Combatant *target, double multiplier, double dmgSoFar)
  {
    return consumeArmedSmite(attacker, target, multiplier, dmgSoFar);
  }

  double OnHitDivineSmite::calculateThreat(Combatant *attacker, Combatant *target)
  {
    int chosenLevel = chooseSmiteLevel(attacker, target);
    if(chosenLevel == 0)
      {
        return 0.0;
      }
    return avgRoll(isUndeadOrFiend(target) ? getDmgDiceUndeadOrFiend(chosenLevel) : getDmgDice(chosenLevel));
  }

  double DivineSmite::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    if(attacker != _factory._combatant || attack == nullptr || !OnHitDivineSmite::canSmite(attacker))
      {
        return 0.0;
      }
    auto *attackActoid = dynamic_cast<Attack *>(attack);
    if(attackActoid == nullptr)
      {
        return 0.0;
      }
    AttackFactory &attackFactory = attackActoid->getAttackFactory();
    if(!attackFactory.hasFlag(FactoryFlags::IS_MELEE))
      {
        return 0.0;
      }

    Combatant *target = &attackActoid->getTarget();
    int chosenLevel = OnHitDivineSmite::chooseSmiteLevel(attacker, target);
    if(chosenLevel == 0)
      {
        return 0.0;
      }
    Die dice = OnHitDivineSmite::isUndeadOrFiend(target) ? OnHitDivineSmite::getDmgDiceUndeadOrFiend(chosenLevel)
                                                         : OnHitDivineSmite::getDmgDice(chosenLevel);
    return meanDmg(attackFactory.getToHit(), {dice}, 0, target->getAC(), target->isImmuneTo(DamageType::Radiant),
                   target->isResistantTo(DamageType::Radiant), attackFactory.getCritRange());
  }

  std::optional<CoordVector>
  DivineSmite::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }
}
