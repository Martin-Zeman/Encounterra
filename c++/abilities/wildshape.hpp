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

    std::string toString() const;

    void transferFactories();
    void restoreFactories();

    // Helper methods
    void transferFactoryList(const std::vector<std::shared_ptr<ActoidFactory>> &sourceFactories,
                             std::vector<std::shared_ptr<ActoidFactory>> &targetFactories);
    void removeTransferredFactories(std::vector<std::shared_ptr<ActoidFactory>> &factories);
    void resetFactoryPointers(const std::vector<std::shared_ptr<ActoidFactory>> &factories);

  protected:
    std::unique_ptr<Combatant> _form;
    WildshapeFactory &_factory;
  };
}
