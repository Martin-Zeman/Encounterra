#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/resources.hpp"
#include "combatants/brown_bear.hpp"
#include "combatants/goblin.hpp"
#include "effects/effect_tracker.hpp"
#include "actions/action_types.hpp"
#include <algorithm>
#include <deque>
#include <memory>
#include <vector>

using namespace enc;

namespace
{

  /**
   * A general test for the multiattack FSM. The Brown Bear is selected as a convenient testbed since it has a simple Multiattack (one Bite + one
   * Claw) that can be easily verified at the Actoid level.
   */
  class BrownBearTest : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    BrownBear *bear;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      bear = new BrownBear(1);
      goblin = new Goblin(1);
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    std::deque<std::shared_ptr<Actoid>> planFor(Combatant *combatant)
    {
      auto [distances, shortestPaths] = battleMap->calcDijkstra(*combatant);
      combatant->setShortestPathsCache(shortestPaths);
      return combatant->calculateActionPlan(distances, shortestPaths);
    }

    static std::vector<ActoidFactory *> meleeFactories(Combatant *combatant)
    {
      std::vector<ActoidFactory *> result;
      for(const auto &f : combatant->getActionFactoriesConst())
        if(f->getAbilityType() == AbilityType::MELEE_ATTACK)
          result.push_back(f.get());
      return result;
    }

    static int countMeleeAttacks(const std::deque<std::shared_ptr<Actoid>> &plan)
    {
      return static_cast<int>(
        std::count_if(plan.begin(), plan.end(), [](const std::shared_ptr<Actoid> &a) { return a->getAbilityType() == AbilityType::MELEE_ATTACK; }));
    }
  };

  TEST_F(BrownBearTest, BaseStats)
  {
    EXPECT_EQ(bear->getMaxHp(), 22);
    EXPECT_EQ(bear->getAC(), 11);
    EXPECT_EQ(bear->getSize(), Size::LARGE);
    EXPECT_EQ(meleeFactories(bear).size(), 2u); // Bite + Claw
  }

  // The attack FSM models Multiattack: after the first attack the FSM grants exactly the
  // complementary attack, then exhausts (no third attack, no repeat of the same attack).
  TEST_F(BrownBearTest, AttackFsmGrantsComplementarySecondAttack)
  {
    auto melee = meleeFactories(bear);
    ASSERT_EQ(melee.size(), 2u);
    ActoidFactory *first = melee[0];
    ActoidFactory *second = melee[1];

    EXPECT_TRUE(bear->isAttackFsmAtStart());

    // First attack: FSM leaves the start state.
    bear->triggerAttackFsm(first);
    EXPECT_FALSE(bear->isAttackFsmAtStart());
    EXPECT_TRUE(bear->attackFsmHasTransition(second)); // the other attack of the pair is granted
    EXPECT_FALSE(bear->attackFsmHasTransition(first)); // the same attack cannot be repeated

    // Second (complementary) attack: the multiattack sequence is now exhausted.
    bear->triggerAttackFsm(second);
    EXPECT_FALSE(bear->attackFsmHasTransition(first));
    EXPECT_FALSE(bear->attackFsmHasTransition(second));
  }

  // A single-attack combatant (goblin) builds a trivial 0->nop FSM for each attack, so after making
  // one attack the FSM grants no further attacks (no Multiattack).
  TEST_F(BrownBearTest, SingleAttackCombatantGrantsNoSecondAttack)
  {
    auto melee = meleeFactories(goblin);
    ASSERT_FALSE(melee.empty());
    ActoidFactory *scimitar = melee[0];
    EXPECT_TRUE(goblin->isAttackFsmAtStart());

    goblin->triggerAttackFsm(scimitar);
    // The trivial FSM leaves the start state but offers no further attack transition.
    EXPECT_FALSE(goblin->attackFsmHasTransition(scimitar));
  }

  // End-to-end: the planner should select both attacks of the Multiattack (one Bite + one Claw).
  TEST_F(BrownBearTest, PlanContainsTwoMeleeAttacks)
  {
    session->addCombatant(bear, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*bear, Coord{2, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{6, 3});

    auto plan = planFor(bear);

    EXPECT_EQ(countMeleeAttacks(plan), 2);
  }

} // namespace
