#include "spells/innate_sorcery.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include <memory>
#include <algorithm>

namespace enc
{

  namespace
  {
    // Innate Sorcery lasts 1 minute; the buff's benefit is projected over this short planning horizon.
    constexpr int ROUND_HORIZON = 3;

    // The caster's spell-attack factories whose attack rolls gain advantage from Innate Sorcery.
    std::vector<DirectThreatFactory *> getSpellAttackFactories(Combatant *caster)
    {
      std::vector<DirectThreatFactory *> result;
      auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
            if(!factory->hasFlag(FactoryFlags::IS_ATTACK_LIKE))
              {
                continue;
              }
            if(auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory.get()))
              {
                result.push_back(threatFactory);
              }
          }
      };
      collect(caster->getActionFactoriesConst());
      collect(caster->getBonusActionFactoriesConst());
      return result;
    }
  }

  InnateSorceryFactory::InnateSorceryFactory(Combatant *caster, Resource *resource)
      : ThreatModifierFactory("InnateSorceryFactory", "Innate Sorcery", caster, AbilityType::INNATE_SORCERY), _resource(resource)
  {
    setFlag(FactoryFlags::TARGETS_SELF);
  }

  std::vector<std::shared_ptr<Actoid>> InnateSorceryFactory::createAll(void *previousActionInDag)
  {
    return {std::make_shared<InnateSorcery>(*this)};
  }

  std::shared_ptr<Actoid> InnateSorceryFactory::create(void *target)
  {
    return std::make_shared<InnateSorcery>(*this);
  }

  double InnateSorceryFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // Best improvement advantage grants to one of the caster's spell attacks against this target,
    // projected over the spell's duration (mirrors RageFactory's per-attack delta * ROUND_HORIZON).
    ThreatModifiers mods;
    mods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);

    double bestDelta = 0.0;
    for(auto *attackFactory : getSpellAttackFactories(_combatant))
      {
        bestDelta = std::max(bestDelta, attackFactory->calculateThreatToTargetDelta(target, mods));
      }
    return bestDelta * ROUND_HORIZON;
  }

  double InnateSorceryFactory::calculateMaxThreat() const
  {
    Teams &teams = Teams::getInstance();
    double maxThreat = 0.0;
    for(auto *enemy : teams.getAliveNonSwallowedEnemies(*_combatant))
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(enemy, {}));
      }
    return maxThreat;
  }

  double InnateSorcery::calculateThreat(const Kwargs &kwargs)
  {
    return _factory.calculateMaxThreat();
  }

  std::optional<CoordVector>
  InnateSorcery::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }

} // namespace enc
