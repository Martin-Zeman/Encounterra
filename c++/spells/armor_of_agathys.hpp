#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/combatant_effect.hpp"

namespace enc
{
  class Combatant;

  /**
   * Armor of Agathys (2024): level 1 Abjuration, cast as a Bonus Action on self. The caster gains 5
   * temporary Hit Points, and while it has any of those temporary Hit Points a creature that hits it with a
   * melee attack takes 5 Cold damage. Lasts 1 hour, no Concentration.
   *
   * Modeled as a self-targeting buff: activate() grants the temporary Hit Points; the Cold-damage retaliation
   * is applied in ActionResolver::resolveAttack while the effect is active and temporary Hit Points remain.
   */
  class ArmorOfAgathysFactory : public DirectThreatFactory
  {
    friend class ArmorOfAgathys;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::SELF;
    static constexpr SpellTarget target = SpellTarget::SELF;
    static constexpr Duration duration = Duration::UNLIMITED;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::BUFF;
    static constexpr DamageType dmgType = DamageType::Cold;
    static constexpr int TEMP_HP = 5;
    static constexpr int RETALIATION_DMG = 5;

    ArmorOfAgathysFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    //! Temporary Hit Points and Cold-retaliation damage when cast at this caster's casting level. Armor of
    //! Agathys gains +5 to both for each slot level above 1, and a Warlock's Pact Magic always upcasts it to
    //! its pact-slot level, so this scales with getCastingSlotLevel.
    int getScaledValue() const;

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    Resource *_resource;
  };

  class ArmorOfAgathys : public Actoid, public LimitedDurationEffect, public CombatantEffect, public DirectThreat
  {
  public:
    ArmorOfAgathys(const ArmorOfAgathysFactory &factory)
        : Effect(factory._combatant), Actoid(const_cast<ArmorOfAgathysFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 600), CombatantEffect(factory._combatant, {factory._combatant}), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;
    EffectType getEffectType() const override { return EffectType::ARMOR_OF_AGATHYS; }

    //! Cold damage dealt to a creature that hits the warded caster with a melee attack, scaled to the slot
    //! level the spell was cast at (captured when the buff is activated).
    int getRetaliationDamage() const { return _retaliationDamage; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const ArmorOfAgathysFactory &_factory;
    int _retaliationDamage = ArmorOfAgathysFactory::RETALIATION_DMG;
  };
}
