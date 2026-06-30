#include "spells/blink.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>

namespace enc
{
  namespace
  {
    // The best (most dangerous) attack a single enemy poses to the caster, mirroring how RageFactory sizes
    // an enemy's incoming threat from its own attack factories.
    double bestIncomingThreat(Combatant *enemy, Combatant *caster)
    {
      double maxIncoming = 0.0;
      auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
            if(!factory->hasFlag(FactoryFlags::IS_DIRECT_THREAT))
              {
                continue;
              }
            if(auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory.get()))
              {
                maxIncoming = std::max(maxIncoming, threatFactory->calculateThreatToTarget(caster, {}));
              }
          }
      };
      collect(enemy->getActionFactoriesConst());
      collect(enemy->getBonusActionFactoriesConst());
      collect(enemy->getHasteActionFactoriesConst());
      return maxIncoming;
    }
  }

  BlinkFactory::BlinkFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("BlinkFactory", "Blink", caster, abilityType), _resource(resource)
  {}

  std::vector<std::shared_ptr<Actoid>> BlinkFactory::createAll(void *previousActionInDag) { return {std::make_shared<Blink>(*this)}; }

  std::shared_ptr<Actoid> BlinkFactory::create(void *target) { return std::make_shared<Blink>(*this); }

  double BlinkFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // Blink is purely defensive: roughly half the time the caster is untargetable on the enemies' turns,
    // causing their attacks to miss outright. Its value is therefore that fraction of the threat the nearby
    // enemies actually pose to the caster, summing each enemy's most dangerous attack (rather than a flat
    // per-enemy constant).
    auto &battleMap = BattleMap::getInstance();
    double avoidedThreat = 0.0;
    for(auto *enemy : battleMap.getNonSwallowedEnemiesWithinHopDistance(_combatant, BlinkFactory::THREAT_RADIUS))
      {
        avoidedThreat += bestIncomingThreat(enemy, _combatant);
      }
    return BlinkFactory::ETHEREAL_PROB * avoidedThreat;
  }

  double BlinkFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double BlinkFactory::calculateMaxThreat() const { return calculateThreatToTarget(_combatant, {}); }

  std::string Blink::toString() const { return "Blink"; }

  std::string Blink::shorthandStr() const { return "Blink"; }

  double Blink::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(_factory._combatant, kwargs); }

  double Blink::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  void Blink::activate(const Kwargs &kwargs)
  {
    // Blink is not a Concentration spell; it simply persists for its duration via the LimitedDurationEffect
    // turn counter. The caster starts on the material plane and only blinks out at the end of its turns.
    EffectTracker::getInstance().add(Effect::shared_from_this());
    _factory._combatant->setEtherealUntargetable(false);
    std::cout << _factory._combatant->_name << " casts Blink" << std::endl;
  }

  void Blink::deactivate()
  {
    // Make sure the caster is returned to the material plane if Blink ends while it is in the Border Ethereal.
    _factory._combatant->setEtherealUntargetable(false);
  }

  bool Blink::deactivateForCombatant(Combatant *combatant) { return false; }

  bool Blink::startOfTurnForCombatant(Combatant *combatant)
  {
    if(combatant == _factory._combatant && combatant->isEtherealUntargetable())
      {
        combatant->setEtherealUntargetable(false);
        std::cout << combatant->_name << " returns to the material plane from Blink" << std::endl;
      }
    return true; // Blink continues for its full duration.
  }

  bool Blink::combatantSavedAtEndOfTurn(Combatant *combatant)
  {
    if(combatant == _factory._combatant)
      {
        if(rollDice(Die{1, 6}) >= 4)
          {
            combatant->setEtherealUntargetable(true);
            std::cout << combatant->_name << " blinks into the Border Ethereal and becomes untargetable" << std::endl;
          }
      }
    // Returning true keeps the effect active (this is not a saving throw to end it).
    return true;
  }

  std::optional<CoordVector>
  Blink::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }
}
