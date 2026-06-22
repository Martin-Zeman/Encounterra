#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "core/resources.hpp"
#include "combatants/goblin.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "combatants/draconic_sorcerer_lvl_3.hpp"
#include "spells/innate_sorcery.hpp"
#include "spells/firebolt.hpp"
#include "spells/ray_of_frost.hpp"
#include "spells/scorching_ray.hpp"
#include "spells/hold_person.hpp"
#include "spells/misty_step.hpp"
#include "effects/effect_tracker.hpp"
#include "actions/action_types.hpp"
#include <algorithm>
#include <deque>
#include <memory>

using namespace enc;

namespace
{

  class DraconicSorcererLvl3Test : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    DraconicSorcererLvl3 *sorcerer;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      sorcerer = new DraconicSorcererLvl3(1);
      goblin = new Goblin(1);
    }

    void TearDown() override
    {
      // Test-body factories/actoids are stack-local; clear without deactivating.
      EffectTracker::getInstance().clearEffects();
    }

    static bool hasFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      return std::any_of(factories.begin(), factories.end(),
                         [type](const std::shared_ptr<ActoidFactory> &f) { return f->getAbilityType() == type; });
    }

    static ActoidFactory *findFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      for(const auto &f : factories)
        {
          if(f->getAbilityType() == type)
            {
              return f.get();
            }
        }
      return nullptr;
    }

    // True if the action plan contains at least one actoid of the given concrete spell type.
    template <typename SpellT>
    static bool planContains(const std::deque<std::shared_ptr<Actoid>> &plan)
    {
      return std::any_of(plan.begin(), plan.end(),
                         [](const std::shared_ptr<Actoid> &a) { return std::dynamic_pointer_cast<SpellT>(a) != nullptr; });
    }

    std::deque<std::shared_ptr<Actoid>> planFor(Combatant *combatant)
    {
      auto [distances, shortestPaths] = battleMap->calcDijkstra(*combatant);
      combatant->setShortestPathsCache(shortestPaths);
      return combatant->calculateActionPlan(distances, shortestPaths);
    }
  };

  TEST_F(DraconicSorcererLvl3Test, BaseStats)
  {
    EXPECT_EQ(sorcerer->getMaxHp(), 23);
    EXPECT_EQ(sorcerer->getAC(), 15);
    EXPECT_EQ(sorcerer->getDC(), 13);
    EXPECT_EQ(sorcerer->getLevel(), 3);
    EXPECT_EQ(sorcerer->getSpeed(), 6); // 30 ft stored as 6 grid cells (5 ft each)
    EXPECT_TRUE(sorcerer->isHumanoid());
  }

  TEST_F(DraconicSorcererLvl3Test, SavingThrows)
  {
    EXPECT_EQ(sorcerer->getSavingThrow(SavingThrow::STR), -1);
    EXPECT_EQ(sorcerer->getSavingThrow(SavingThrow::DEX), 2);
    EXPECT_EQ(sorcerer->getSavingThrow(SavingThrow::CON), 4);
    EXPECT_EQ(sorcerer->getSavingThrow(SavingThrow::INT), 1);
    EXPECT_EQ(sorcerer->getSavingThrow(SavingThrow::WIS), 1);
    EXPECT_EQ(sorcerer->getSavingThrow(SavingThrow::CHA), 5);
  }

  TEST_F(DraconicSorcererLvl3Test, ActionFactoriesPresent)
  {
    const auto &actions = sorcerer->getActionFactoriesConst();
    EXPECT_TRUE(hasFactory(actions, AbilityType::FIREBOLT));
    EXPECT_TRUE(hasFactory(actions, AbilityType::RAY_OF_FROST));
    EXPECT_TRUE(hasFactory(actions, AbilityType::SCORCHING_RAY));
    EXPECT_TRUE(hasFactory(actions, AbilityType::HOLD_PERSON));
  }

  TEST_F(DraconicSorcererLvl3Test, BonusActionFactoriesPresent)
  {
    const auto &bonus = sorcerer->getBonusActionFactoriesConst();
    EXPECT_TRUE(hasFactory(bonus, AbilityType::MISTY_STEP));
    EXPECT_TRUE(hasFactory(bonus, AbilityType::INNATE_SORCERY));
  }

  TEST_F(DraconicSorcererLvl3Test, ReactionFactoriesPresent)
  {
    const auto &reactions = sorcerer->getReactionFactoriesConst();
    EXPECT_TRUE(hasFactory(reactions, AbilityType::SHIELD));
  }

  TEST_F(DraconicSorcererLvl3Test, PassiveMarkers)
  {
    EXPECT_TRUE(sorcerer->hasPassiveAbility(AbilityType::DRACONIC_RESILIENCE));
    EXPECT_TRUE(sorcerer->hasPassiveAbility(AbilityType::METAMAGIC));
    EXPECT_TRUE(sorcerer->hasPassiveAbility(AbilityType::TWINNED_SPELL));
  }

  TEST_F(DraconicSorcererLvl3Test, QuickenedVariantsPresent)
  {
    const auto &bonus = sorcerer->getBonusActionFactoriesConst();
    EXPECT_TRUE(hasFactory(bonus, AbilityType::QUICKENED_FIREBOLT));
    EXPECT_TRUE(hasFactory(bonus, AbilityType::QUICKENED_RAY_OF_FROST));
    EXPECT_TRUE(hasFactory(bonus, AbilityType::QUICKENED_SCORCHING_RAY));
    EXPECT_TRUE(hasFactory(bonus, AbilityType::QUICKENED_HOLD_PERSON));
  }

  TEST_F(DraconicSorcererLvl3Test, RayOfFrostThreatPositive)
  {
    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});

    auto *factory = findFactory(sorcerer->getActionFactoriesConst(), AbilityType::RAY_OF_FROST);
    ASSERT_NE(factory, nullptr);
    auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(threatFactory, nullptr);
    EXPECT_GT(threatFactory->calculateThreatToTarget(goblin, {}), 0.0);
  }

  TEST_F(DraconicSorcererLvl3Test, ScorchingRayThreatPositive)
  {
    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});

    auto *factory = findFactory(sorcerer->getActionFactoriesConst(), AbilityType::SCORCHING_RAY);
    ASSERT_NE(factory, nullptr);
    auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(threatFactory, nullptr);
    EXPECT_GT(threatFactory->calculateThreatToTarget(goblin, {}), 0.0);
  }

  TEST_F(DraconicSorcererLvl3Test, HoldPersonThreatPositiveForHumanoid)
  {
    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});

    auto *factory = findFactory(sorcerer->getActionFactoriesConst(), AbilityType::HOLD_PERSON);
    ASSERT_NE(factory, nullptr);
    auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(threatFactory, nullptr);
    EXPECT_GT(threatFactory->calculateThreatToTarget(goblin, {}), 0.0);
  }

  TEST_F(DraconicSorcererLvl3Test, InnateSorceryIsThreatModifierNotDirectThreat)
  {
    auto *factory = findFactory(sorcerer->getBonusActionFactoriesConst(), AbilityType::INNATE_SORCERY);
    ASSERT_NE(factory, nullptr);
    EXPECT_NE(dynamic_cast<ThreatModifierFactory *>(factory), nullptr);
    EXPECT_EQ(dynamic_cast<DirectThreatFactory *>(factory), nullptr);
  }

  TEST_F(DraconicSorcererLvl3Test, InnateSorceryGeneratesThreat)
  {
    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});

    auto *factory = findFactory(sorcerer->getBonusActionFactoriesConst(), AbilityType::INNATE_SORCERY);
    ASSERT_NE(factory, nullptr);
    auto *modFactory = dynamic_cast<ThreatModifierFactory *>(factory);
    ASSERT_NE(modFactory, nullptr);
    // Advantage on the caster's spell attacks against a reachable enemy must yield positive threat.
    EXPECT_GT(modFactory->calculateThreatToTarget(goblin, {}), 0.0);
  }

  // ---------------------------------------------------------------------------
  // End-to-end action-plan selection: craft scenarios (mirroring the Python
  // simulator/test/test_error_cases.py style) that force the planner to pick a
  // specific spell, so we cover the spells beyond Scorching Ray / Innate Sorcery.
  // ---------------------------------------------------------------------------

  TEST_F(DraconicSorcererLvl3Test, PlanUsesFireboltWhenLeveledSlotsDepleted)
  {
    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{8, 3});

    // No leveled slots -> Scorching Ray / Hold Person / Misty Step are unavailable, so the best
    // remaining attack is a cantrip; Firebolt (1d10 fire) out-damages Ray of Frost (1d8 cold).
    sorcerer->getSpellslots().depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);

    auto plan = planFor(sorcerer);

    EXPECT_TRUE(planContains<Firebolt>(plan));
    EXPECT_FALSE(planContains<ScorchingRay>(plan));
  }

  TEST_F(DraconicSorcererLvl3Test, PlanUsesRayOfFrostAgainstFireImmuneTarget)
  {
    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{6, 3});

    // Cantrip-only (slots depleted) AND the target is immune to fire, so Firebolt deals nothing and
    // Ray of Frost (cold) becomes the best cantrip.
    sorcerer->getSpellslots().depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);
    goblin->addImmunity(DamageType::Fire);

    auto plan = planFor(sorcerer);

    EXPECT_TRUE(planContains<RayOfFrost>(plan));
    EXPECT_FALSE(planContains<Firebolt>(plan));
  }

  TEST_F(DraconicSorcererLvl3Test, PlanUsesHoldPersonAgainstStrongHumanoid)
  {
    auto *barbarian = new WildHeartBarbarianLvl5(1); // humanoid, high HP & damage output
    Combatant *ally = new BugbearWarrior(1);         // sorcerer's melee ally beside the target

    session->addCombatant(sorcerer, Color::BLUE);
    session->addCombatant(ally, Color::BLUE);
    session->addCombatant(static_cast<Combatant *>(barbarian), Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*sorcerer, Coord{2, 3});
    battleMap->setCombatantCoordinates(*barbarian, Coord{8, 3});
    battleMap->setCombatantCoordinates(*ally, Coord{8, 4}); // adjacent to the barbarian

    // Bias strongly toward control: paralysing a tanky, hard-hitting humanoid that an adjacent ally
    // can then auto-crit is worth far more than Scorching Ray, whose fire damage we further dampen
    // with resistance. A poor WIS save makes the paralysis very likely to land.
    barbarian->addResistance(DamageType::Fire);
    barbarian->setSavingThrow(SavingThrow::WIS, -5);

    auto plan = planFor(sorcerer);

    EXPECT_TRUE(planContains<HoldPerson>(plan));
  }

} // namespace
