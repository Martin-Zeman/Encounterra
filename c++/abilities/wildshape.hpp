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
    WildshapeFactory(Combatant* combatant, AbilityType actionType);

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override;
    Actoid *create(void *form) override;
    std::optional<Resource *> getResource() override { return {}; }
    double calculateThreat(const Kwargs &kwargs) override;

    static int getWildshapeUses(int level);
    static std::vector<Size> getWildshapeFormSizes(int level, AbilityType actionType);

  protected:
    AbilityType _actionType;
  };

  class Wildshape : public Actoid, virtual public CombatantEffect, virtual public ActionEnablerEffect, public DirectThreat
  {
  public:
    Wildshape(Combatant *combatant, Combatant *form, WildshapeFactory &factory);

    Wildshape(const Wildshape &other)
        : Effect(other._factory.getCombatant()) // Init virtual base
          ,
          CombatantEffect(other._factory.getCombatant(), std::vector<Combatant *>{other._factory.getCombatant()}),
          ActionEnablerEffect(other._factory.getCombatant()), Actoid(other._factory), DirectThreat(other), _form(other._form),
          _factory(other._factory)
    {
      _form->setBaseForm(other._factory.getCombatant());
    }

    ~Wildshape() override = default;

    Actoid *clone() const override { return new Wildshape(*this); }

    EffectType getEffectType() const override { return EffectType::WILDSHAPE; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant &combatant) override;
    bool isAffecting(const Combatant &combatant) const override { return CombatantEffect::isAffecting(combatant); }

    void enable() override;
    void disable() override;

    double calculateThreat(const Kwargs &kwargs = {}) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    std::string toString() const override;

    void transferFactories();
    void restoreFactories();

    // Helper methods
    void transferFactoryList(const std::vector<ActoidFactory *> &sourceFactories, std::vector<ActoidFactory *> &targetFactories);
    void removeTransferredFactories(std::vector<ActoidFactory *> &factories);
    void resetFactoryPointers(const std::vector<ActoidFactory *> &factories);

    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;

    Combatant *_form;
    WildshapeFactory &_factory;
  };
}
