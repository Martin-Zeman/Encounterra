#pragma once

#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "actions/action_types.hpp"
#include "actions/melee_attack.hpp"
#include <memory>
#include <vector>

namespace enc
{
  class Combatant;

  /**
   * Pounce (port of the Python simulator/abilities/pounce.py).
   *
   * A leaping charge: if the beast can travel `distance` cells in a straight line up to a target, it makes a
   * primary attack that knocks the target Prone on a failed save; if the target is left Prone it follows up with
   * a secondary (bonus-action) attack. Pounce is a single Action and only its primary/secondary attacks deal
   * damage, so they are kept "suppressed" (owned by the factory, not registered as independent actions).
   *
   * Threat mirrors Python: primary.threat + p_fail * secondary.threat, where p_fail is the chance the target
   * fails the primary's Prone saving throw.
   */
  class PounceFactory : public DirectThreatFactory
  {
    friend class Pounce;

  public:
    PounceFactory(Combatant *combatant, std::shared_ptr<MeleeAttackFactory> primary, std::shared_ptr<MeleeAttackFactory> secondary, int distance);

    std::vector<Combatant *> getEligibleTargets() const;

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return std::nullopt; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

    //! Repoint the factory and the suppressed primary/secondary attacks at `combatant` (used by Wild Shape
    //! grafting, which moves the ability between the beast template and the druid).
    void setCombatant(Combatant *combatant) override;

    MeleeAttackFactory *getPrimaryAttack() const { return _primary.get(); }
    MeleeAttackFactory *getSecondaryAttack() const { return _secondary.get(); }
    int getDistance() const { return _distance; }

  private:
    std::shared_ptr<MeleeAttackFactory> _primary;
    std::shared_ptr<MeleeAttackFactory> _secondary;
    int _distance;

    //! Chance the target fails the primary attack's Prone saving throw (0 if the primary carries no Prone rider).
    double proneFailProb(Combatant *target) const;
  };

  class Pounce : public Actoid, public DirectThreat
  {
  public:
    Pounce(Combatant *target, PounceFactory &factory)
        : Actoid(factory, ActoidFlags::IS_ATTACK_LIKE, AbilityType::POUNCE), _target(target), _factory(factory)
    {}

    Combatant *getTarget() const { return _target; }
    PounceFactory &getPounceFactory() const { return _factory; }

    std::string toString() const override;
    std::string shorthandStr() const;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

  private:
    Combatant *_target;
    PounceFactory &_factory;

    //! True iff a straight charge of `distance` cells reaches `endCoord` from the beast's current position.
    bool isStraightLinePath(const Coord &endCoord, const blaze::DynamicMatrix<Coord> &shortestPaths);
  };
}
