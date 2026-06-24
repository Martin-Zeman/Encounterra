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

    // The caster's spell factories that can benefit from Innate Sorcery: spell attacks gain advantage on
    // their attack roll, while save-based spells benefit from the +1 spell save DC. Every such factory is a
    // DirectThreatFactory whose calculateThreatToTargetDelta responds to the relevant modifier.
    std::vector<DirectThreatFactory *> getSpellThreatFactories(Combatant *caster)
    {
      std::vector<DirectThreatFactory *> result;
      auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
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
    // Once the buff is already active it grants no further advantage, so it generates no threat (mirrors
    // Python: a self-buff's threat is conditioned on it not being active yet).
    if(_combatant->isInnateSorceryActive())
      {
        return 0.0;
      }

    // Innate Sorcery's value is the best of two riders against this target: advantage on the caster's spell
    // attacks, or +1 to the caster's spell save DC on its save-based spells. Spell attacks respond to the
    // ROLL_TYPE modifier, save spells to SAVE_DC; each factory ignores the modifier that does not apply to it.
    ThreatModifiers advantageMods;
    advantageMods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    ThreatModifiers saveDcMods;
    saveDcMods.set(ThreatModifierType::SAVE_DC, InnateSorceryFactory::dcBonus);

    double bestThreat = 0.0;
    for(auto *attackFactory : getSpellThreatFactories(_combatant))
      {
        // The advantage delta is a single attack's improvement, projected over the spell's duration. The
        // save-DC delta already spans the save spell's own horizon, so it is not projected again.
        bestThreat = std::max(bestThreat, attackFactory->calculateThreatToTargetDelta(target, advantageMods) * ROUND_HORIZON);
        bestThreat = std::max(bestThreat, attackFactory->calculateThreatToTargetDelta(target, saveDcMods));
      }
    return bestThreat;
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
    // Innate Sorcery has no inherent threat of its own (no damage, no survival benefit). Its entire value is
    // the advantage / save-DC bonus it grants to subsequent sorcerer spells in the same plan, contributed via
    // calculateThreatForAttack. Returning the value here as well would double-count it.
    return 0.0;
  }

  double InnateSorcery::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    // Once the buff is already active it grants no further benefit, so it adds no threat to the spell
    // (mirrors Python: the buff's threat is conditioned on it not being active yet).
    if(_factory._combatant->isInnateSorceryActive())
      {
        return 0.0;
      }
    // Innate Sorcery only empowers the sorcerer's own spells: advantage on spell attack rolls and +1 to the
    // spell save DC. Both riders are offered; each spell uses whichever applies to it.
    if(attack == nullptr || !attack->hasFlag(ActoidFlags::IS_SPELL))
      {
        return 0.0;
      }
    auto *directThreat = dynamic_cast<DirectThreat *>(attack);
    if(directThreat == nullptr)
      {
        return 0.0;
      }
    ThreatModifiers mods;
    mods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    mods.set(ThreatModifierType::SAVE_DC, InnateSorceryFactory::dcBonus);
    return directThreat->calculateThreatDelta(mods);
  }

  std::optional<CoordVector>
  InnateSorcery::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }

} // namespace enc
