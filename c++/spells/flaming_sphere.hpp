#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_square_effect.hpp"
#include "effects/action_enabler_effect.hpp"

namespace enc
{
  class Combatant;
  class FlamingSphere;

  /**
   * Flaming Sphere (2024): level 2. Creates a 5-foot-diameter sphere of fire within 60 feet. A creature that
   * ends its turn (or that the sphere enters) makes a Dexterity save, taking 2d6 Fire damage on a failure
   * (half on a success). As a bonus action the caster can move the sphere up to 30 feet, ramming a creature
   * (the Flaming Sphere Ram bonus action). Concentration, up to 1 minute (10 rounds).
   */
  class FlamingSphereFactory : public DirectThreatFactory
  {
    friend class FlamingSphere;

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::BOX_5;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Fire;

    FlamingSphereFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    Coord findBestArgs() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
    SavingThrow _savingThrow;
    std::vector<Die> _dmgDice;
  };

  class FlamingSphere : public Actoid,
                        public LimitedDurationEffect,
                        public ActionEnablerEffect,
                        public AoeSquareEffect,
                        public DirectThreat,
                        public AoeThreat
  {
  public:
    FlamingSphere(const Coord &coord, const FlamingSphereFactory &factory)
        : Effect(factory._combatant), // Explicitly construct the virtual base
          Actoid(const_cast<FlamingSphereFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 100),
          ActionEnablerEffect(factory._combatant),
          AoeSquareEffect(factory._combatant, coord, TRANSLATE_BOX.at(FlamingSphereFactory::target)), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::FLAMING_SPHERE; }

    int getDc() const { return _factory._dc; }
    void moveOrigin(const Coord &coord);

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    bool isAffecting(Combatant *combatant) const override;
    void enable() override;
    void disable() override;
    void onEnter(Combatant *combatant) override;
    void onMoveWithin(Combatant *combatant) override;
    void onExit(Combatant *combatant) override;
    void onStartOfTurn(Combatant *combatant) override;
    void onEndOfTurn(Combatant *combatant) override;

    double threatOnEnter(Combatant *target, const Kwargs &kwargs) const override;
    double threatOnEndOfTurn(Combatant *target, const Kwargs &kwargs) const override;

    const CoordVector &getAffectedCoords() const override { return SquareAoe::getAffectedCoords(); }

  private:
    Coord _coord;
    const FlamingSphereFactory &_factory;
  };

  /**
   * Flaming Sphere Ram: bonus action that moves the sphere into an enemy, forcing a Dexterity save for
   * 2d6 Fire damage (half on success). Flagged TRANSITIONS_TO_WILDSHAPE so a Circle of the Moon druid can
   * keep ramming the sphere while in beast form.
   */
  class FlamingSphereRamFactory : public DirectThreatFactory
  {
    friend class FlamingSphereRam;

  public:
    static constexpr int RANGE = 6; // 30 feet, in cells
    static constexpr DamageType dmgType = DamageType::Fire;

    FlamingSphereRamFactory(Combatant *caster, int dc, FlamingSphere *actionEnablerEffect);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return std::nullopt; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    FlamingSphere *_actionEnablerEffect;
    SavingThrow _savingThrow;
    std::vector<Die> _dmgDice;
  };

  class FlamingSphereRam : public Actoid, public DirectThreat
  {
  public:
    FlamingSphereRam(Combatant *target, const Coord &coord, const FlamingSphereRamFactory &factory)
        : Actoid(const_cast<FlamingSphereRamFactory &>(factory), ActoidFlags::DEFAULT, AbilityType::FLAMING_SPHERE_RAM), _target(target),
          _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return *_target; }
    const Coord &getCoord() const { return _coord; }
    FlamingSphere *getEffect() const { return _factory._actionEnablerEffect; }
    int getDc() const { return _factory._dc; }
    const std::vector<Die> &getDmgDice() const { return _factory._dmgDice; }
    SavingThrow getSavingThrow() const { return _factory._savingThrow; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant *_target;
    Coord _coord;
    const FlamingSphereRamFactory &_factory;
  };
}
