#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Lay on Hands (2024 Paladin, level 1): as a Bonus Action the paladin touches itself or another creature
   * and spends points from a pool equal to five times Paladin level. This model creates one heal actoid per
   * target for the largest currently useful heal amount; Poison removal is represented by the actoid flag.
   */
  class LayOnHandsFactory : public DirectThreatFactory
  {
    friend class LayOnHands;

  public:
    static constexpr int range = 1;
    static constexpr int hpPerLevel = 5;
    static constexpr int poisonedRemovalCost = 5;

    LayOnHandsFactory(Combatant *combatant, Resource *resource);

    static int getPoolSize(int paladinLevel) { return hpPerLevel * paladinLevel; }

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::shared_ptr<Actoid> createPoisonRemoval(Combatant *target);
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;
    int getRange() const override { return range; }

  private:
    Resource *_resource;
  };

  class LayOnHands : public Actoid, public DirectThreat
  {
  public:
    LayOnHands(Combatant &target, const LayOnHandsFactory &factory, int hpAmount, bool removePoison = false)
        : Actoid(const_cast<LayOnHandsFactory &>(factory), ActoidFlags::DEFAULT, AbilityType::LAY_ON_HANDS), _target(target), _factory(factory),
          _hpAmount(hpAmount), _removePoison(removePoison)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getHpAmount() const { return _hpAmount; }
    bool removesPoison() const { return _removePoison; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const LayOnHandsFactory &_factory;
    int _hpAmount;
    bool _removePoison;
  };
}
