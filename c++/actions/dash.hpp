#pragma once

#include <vector>
#include <memory>
#include "core/interfaces.hpp"

namespace enc
{
  //! Dash (2024). Offered as a bonus action to a rogue with Cunning Action (AbilityType::CUNNING_DASH). Taking
  //! it grants extra movement equal to the combatant's Speed for the current turn. Location independent: it is
  //! always available from the combatant's current square.
  class DashFactory : public ActoidFactory
  {
    friend class Dash;

  public:
    DashFactory(Combatant *combatant, AbilityType abilityType = AbilityType::DASH)
        : ActoidFactory("DashFactory", "Dash", combatant, abilityType)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return {}; }
  };

  //! Dash mirrors Python's actions.dash.Dash (an AttackThreatModifier). Its value to the planner is purely
  //! defensive: the extra Speed of movement it grants lets the combatant travel further along its chosen path,
  //! and calculateThreat scores how much projected threat (danger zone / AoE / AoO) that extra distance shaves
  //! off. It is only credited when used to flee (baseline - modified > 0), never to close on an enemy.
  class Dash : public Actoid, public Threat
  {
  public:
    explicit Dash(ActoidFactory &factory)
        : Actoid(factory, ActoidFlags::IS_DASH | ActoidFlags::LOCATION_INDEPENDENT, factory.getAbilityType())
    {}

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    std::string toString() const override;

    //! Threat contribution of taking Dash, mirroring Python Dash.calculate_threat. Reads the "movementThreat"
    //! kwarg (the cumulative-threat-along-path array the planner computed for this sequence's destination) and
    //! returns the reduction in projected threat unlocked by moving an extra Speed of cells along that path.
    double calculateThreat(const Kwargs &kwargs) override;
  };
}
