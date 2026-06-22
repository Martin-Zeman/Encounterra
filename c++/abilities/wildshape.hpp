#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/action_enabler_effect.hpp"
#include "core/battle_map.hpp"
#include "core/conditions.hpp"
#include "core/attack_fsm.hpp"
#include <vector>
#include <memory>
#include <cmath>

namespace enc
{
  class Combatant;
  class AttackFactory;

  class WildshapeFactory : public TransformerFactory
  {
    friend class Wildshape;

  public:
    WildshapeFactory(Combatant *combatant, AbilityType actionType);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *form) override;
    std::optional<Resource *> getResource() override { return {}; }
    double calculateThreat(const Kwargs &kwargs) override;

    static int getWildshapeUses(int level);
    static std::vector<Size> getWildshapeFormSizes(int level, AbilityType actionType);

  protected:
    Combatant *_combatant;
    AbilityType _actionType;
  };

  /**
   * 2024 Wild Shape.
   *
   * Unlike the 2014 implementation this does NOT swap the druid off the battle map for a separate beast
   * combatant. The druid keeps its own HP, position and identity. Activating instead:
   *  - overrides AC to the beast's AC (Circle of the Moon raises this floor to 13 + the druid's Wisdom
   *    modifier),
   *  - adopts the beast's Speed,
   *  - replaces the druid's own actions (weapon attacks AND spells) with the beast's attacks and
   *    multiattack FSM. The only druid abilities that remain usable while shaped are those flagged
   *    FactoryFlags::TRANSITIONS_TO_WILDSHAPE (the Circle of the Moon spell loadout) and the Wild Shape
   *    action itself, and
   *  - records which form is active so the druid cannot reshape into the same animal.
   *
   * Assuming a Wild Shape form grants Temporary Hit Points equal to the druid's level; the Circle of the
   * Moon instead grants 3 x druid level and raises its AC floor to 13 + the druid's Wisdom modifier. These
   * temporary hit points persist like any others and are NOT cleared when the form ends.
   *
   * The druid is never knocked out of the form: at 0 HP it simply dies (the temp-HP mechanic in
   * Combatant::doReceiveDmg already absorbs damage first, with no carry-over). Reverting restores the
   * saved AC/Speed/attacks/FSM.
   *
   * enable()/disable() apply/revert the same structural transform (attacks, FSM, AC, Speed) without the
   * temp-HP grant or effect registration, so the action-DAG planner can explore post-shape options.
   */
  class Wildshape : public Actoid, virtual public CombatantEffect, virtual public ActionEnablerEffect, public DirectThreat
  {
  public:
    Wildshape(Combatant *combatant, std::unique_ptr<Combatant> form, WildshapeFactory &factory);

    ~Wildshape() override = default;

    EffectType getEffectType() const override { return EffectType::WILDSHAPE; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    bool isAffecting(Combatant *combatant) const override { return CombatantEffect::isAffecting(combatant); }

    void enable() override;
    void disable() override;

    double calculateThreat(const Kwargs &kwargs = {}) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    std::string toString() const override;

    //! The preallocated beast template that supplies this form's stats, attacks and identity.
    Combatant *getForm() const { return _form.get(); }

  protected:
    //! Apply the structural shape transform (attacks, multiattack FSM, AC, Speed). Idempotent: a no-op if
    //! already applied. Saves the druid's pre-shape state so revertShapeTransform() can restore it.
    void applyShapeTransform();
    //! Revert the structural shape transform, restoring the saved AC/Speed/attacks/FSM.
    void revertShapeTransform();

    //! 13 + the druid's Wisdom modifier (Circle of the Moon AC floor), derived from the druid's spell DC.
    int circleOfMoonAc() const;

    //! True for the Circle of the Moon (MOON_WILDSHAPE), which grants temp HP and a raised AC floor.
    bool isCircleOfMoon() const { return _factory._actionType == AbilityType::MOON_WILDSHAPE; }

    std::unique_ptr<Combatant> _form;
    WildshapeFactory &_factory;

    bool _shaped = false;
    int _savedAc = 0;
    int _savedSpeed = 0;
    int _savedMovement = 0;
    AttackFsm _savedFsm;
    AttackFactory *_savedAoOFactory = nullptr;
    DirectThreatFactory *_savedDangerZone = nullptr;
    // Druid actions (weapons and non-persisting spells) removed for the duration of the shape, by list.
    std::vector<std::shared_ptr<ActoidFactory>> _stashedActionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _stashedBonusActionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _stashedReactionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _stashedHasteActionFactories;
    // Beast attack factories grafted onto the druid (removed on revert).
    std::vector<std::shared_ptr<ActoidFactory>> _addedActionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _addedReactionFactories;
  };
}
