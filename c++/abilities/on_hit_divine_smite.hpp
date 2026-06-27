#pragma once

#include "abilities/on_hit_effect.hpp"
#include "actions/attack.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Divine Smite (2024 Paladin): a Bonus Action spell taken immediately after a hit with a melee weapon or
   * unarmed strike. The planner models it as a Bonus Action attack modifier so choosing it reserves the
   * Paladin's Bonus Action before the attack, and the resolver spends the free cast / spell slot only when a
   * later melee hit actually lands.
   */
  class DivineSmiteFactory : public ThreatModifierFactory
  {
    friend class DivineSmite;

  public:
    DivineSmiteFactory(Combatant *combatant, Resource *freeCastResource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _freeCastResource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    Resource *_freeCastResource;
  };

  class DivineSmite : public AttackThreatModifier
  {
  public:
    explicit DivineSmite(const DivineSmiteFactory &factory)
        : AttackThreatModifier(const_cast<DivineSmiteFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_PRIORITY, AbilityType::DIVINE_SMITE),
          _factory(factory)
    {}

    std::string toString() const override { return "Divine Smite"; }
    std::string shorthandStr() const { return "Divine Smite"; }

    double calculateThreat(const Kwargs &kwargs) override { return 0.0; }
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const DivineSmiteFactory &_factory;
  };

  class OnHitDivineSmite : public OnHit
  {
  public:
    static Die getDmgDice(int spellSlotLevel);
    static Die getDmgDiceUndeadOrFiend(int spellSlotLevel);
    static bool isUndeadOrFiend(Combatant *target);
    static bool canSmite(Combatant *attacker);
    static int chooseSmiteLevel(Combatant *attacker, Combatant *target, double multiplier = 1.0, double dmgSoFar = 0.0);
    static std::shared_ptr<Actoid> createPendingSmiteMarker();
    static bool isPendingSmiteMarker(const std::shared_ptr<Actoid> &actoid);
    static std::vector<std::pair<int, DamageType>>
    consumeArmedSmite(Combatant *attacker, Combatant *target, double multiplier, double dmgSoFar);

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target) override;

    std::unique_ptr<OnHit> clone() const override { return std::make_unique<OnHitDivineSmite>(*this); }
  };
}
