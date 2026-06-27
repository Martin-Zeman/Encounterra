#include "abilities/vow_of_enmity.hpp"

#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include "actions/attack.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>

namespace enc
{
  VowOfEnmityFactory::VowOfEnmityFactory(Combatant *combatant, Resource *channelDivinity)
      : ThreatModifierFactory("VowOfEnmityFactory", "Vow of Enmity", combatant, AbilityType::VOW_OF_ENMITY),
        _channelDivinity(channelDivinity)
  {
    setFlag(FactoryFlags::IS_ATTACK_MODIFIER);
  }

  std::vector<std::shared_ptr<Actoid>> VowOfEnmityFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    if(!_channelDivinity->hasUses() || _combatant->getSwallower())
      {
        return result;
      }
    for(auto *enemy : BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, range))
      {
        result.push_back(std::make_shared<VowOfEnmity>(*enemy, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> VowOfEnmityFactory::create(void *target)
  {
    return std::make_shared<VowOfEnmity>(*static_cast<Combatant *>(target), *this);
  }

  double VowOfEnmityFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    ThreatModifiers mods;
    mods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    double maxDelta = 0.0;

    auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
      for(const auto &factory : factories)
        {
          if(factory->hasFlag(FactoryFlags::IS_ATTACK_LIKE))
            {
              if(auto *directThreat = dynamic_cast<DirectThreatFactory *>(factory.get()))
                {
                  maxDelta = std::max(maxDelta, directThreat->calculateThreatToTargetDelta(target, mods));
                }
            }
        }
    };
    collect(_combatant->getActionFactoriesConst());
    collect(_combatant->getBonusActionFactoriesConst());
    collect(_combatant->getHasteActionFactoriesConst());
    return maxDelta * 3.0;
  }

  VowOfEnmity::VowOfEnmity(Combatant &target, VowOfEnmityFactory &factory)
      : Effect(factory.getCombatant(), &target),
        AttackThreatModifier(factory, ActoidFlags::IS_ATTACK_MODIFIER | ActoidFlags::IS_PRIORITY, AbilityType::VOW_OF_ENMITY),
        CombatantEffect(factory.getCombatant(), {&target}), LimitedDurationEffect(factory.getCombatant(), VowOfEnmityFactory::durationRounds),
        _factory(factory)
  {}

  void VowOfEnmity::activate(const Kwargs &kwargs)
  {
    EffectTracker &tracker = EffectTracker::getInstance();
    for(const auto &effect : tracker.getEffectsByInitiator(_factory.getCombatant()))
      {
        if(effect->getEffectType() == EffectType::VOW_OF_ENMITY)
          {
            tracker.remove(effect);
          }
      }
    tracker.add(std::dynamic_pointer_cast<Effect>(shared_from_this()));
  }

  void VowOfEnmity::deactivate() {}

  bool VowOfEnmity::deactivateForCombatant(Combatant *combatant)
  {
    deactivate();
    return false;
  }

  std::string VowOfEnmity::toString() const
  {
    return "Vow of Enmity on " + getCombatants().front()->_name;
  }

  std::string VowOfEnmity::shorthandStr() const { return "Vow of Enmity"; }

  std::optional<CoordVector>
  VowOfEnmity::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *paladin = _factory.getCombatant();
    Combatant *target = getCombatants().front();
    Coord currCoord = battleMap.getCombatantCoordinates(*paladin).getRoot();
    if(!paladin->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*target).get(), distances, paladin->getSize(),
                                                       VowOfEnmityFactory::range, paladin->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*paladin, *target) <= VowOfEnmityFactory::range)
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }

  double VowOfEnmity::calculateThreat(const Kwargs &kwargs)
  {
    return _factory.calculateThreatToTarget(getCombatants().front(), kwargs);
  }

  double VowOfEnmity::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    auto *directThreat = dynamic_cast<DirectThreat *>(attack);
    if(attacker != _factory.getCombatant() || directThreat == nullptr)
      {
        return 0.0;
      }
    auto *attackActoid = dynamic_cast<Attack *>(attack);
    if(attackActoid == nullptr || &attackActoid->getTarget() != getCombatants().front())
      {
        return 0.0;
      }
    ThreatModifiers mods;
    mods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    return directThreat->calculateThreatDelta(mods);
  }
}
