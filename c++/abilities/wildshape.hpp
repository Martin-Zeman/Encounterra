#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/action_enabler_effect.hpp"
#include "core/battle_map.hpp"
#include "core/conditions.hpp"
#include <vector>
#include <memory>
#include <cmath>

namespace enc
{
  class Combatant;

  class WildshapeFactory : public TransformerFactory
  {
    friend class Wildshape;

  public:
    WildshapeFactory(Combatant *combatant, AbilityType actionType);

    std::string getAbilityName() const override { return "Wildshape"; }
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *form) override;
    std::optional<Resource *> getResource() override { return {}; }
    double calculateThreat(const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

    static int getWildshapeUses(int level);
    static std::vector<Size> getWildshapeFormSizes(int level, AbilityType actionType);

  protected:
    Combatant *_combatant;
    AbilityType _actionType;
  };

  class Wildshape : public Actoid, public CombatantEffect, public ActionEnablerEffect, public DirectThreat
  {
  public:
    Wildshape(Combatant *combatant, std::shared_ptr<Combatant> form, WildshapeFactory &factory)
        : Actoid(factory), CombatantEffect(combatant, std::vector<Combatant *>{combatant}), ActionEnablerEffect(combatant), _form(form),
          _factory(factory)
    {
      _form->setOriginalForm(combatant);
    }

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

    std::optional<std::vector<Coord>> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    std::string toString() const;

  protected:
    std::shared_ptr<Combatant> _form;
    WildshapeFactory &_factory;
  };
}
