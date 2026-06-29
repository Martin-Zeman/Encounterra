#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // --- Description (Cutting Words, College of Lore level 3 feature) ---
  // You learn to use your wit to distract, confuse, and otherwise sap the confidence and competence of others.
  // When a creature you can see within 60 feet makes a damage roll or succeeds on an attack roll or ability check,
  // you can take a Reaction to expend one use of Bardic Inspiration and roll the die, subtracting the number from
  // the creature's roll. You can do so after the roll but before the GM determines success or failure.

  // Cutting Words (College of Lore, 2024) — a reaction that spends one Bardic Inspiration die to subtract a
  // d6 from a foe's attack roll, damage roll or ability check. Like Shield it is a reactive buff with no
  // offensive threat of its own; the bardic die is consumed from the shared Bardic Inspiration pool.
  class CuttingWordsFactory : public ActoidFactory
  {
    friend class CuttingWords;

  public:
    static constexpr Die cuttingDie{1, 6};
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;

    CuttingWordsFactory(Combatant *caster, Resource *resource)
        : ActoidFactory("CuttingWordsFactory", "Cutting Words", caster, AbilityType::CUTTING_WORDS), _resource(resource)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

  private:
    Resource *_resource;
  };

  class CuttingWords : public Actoid, public Threat
  {
  public:
    CuttingWords(const CuttingWordsFactory &factory)
        : Actoid(const_cast<CuttingWordsFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::CUTTING_WORDS), _factory(factory)
    {}

    std::string toString() const override { return "Cutting Words"; }
    std::string shorthandStr() const { return "Cutting Words"; }

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const CuttingWordsFactory &_factory;
  };
}
