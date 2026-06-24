#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/action_resolver.hpp"
#include "actions/attack.hpp"
#include "actions/melee_attack.hpp"
#include "actions/action_types.hpp"
#include "abilities/pounce.hpp"
#include "abilities/roar.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/dire_wolf.hpp"
#include "combatants/tiger.hpp"
#include "combatants/lion.hpp"
#include "combatants/goblin.hpp"
#include <memory>
#include <vector>

using namespace enc;

namespace
{
  /**
   * Tests for the new beasts: the Dire Wolf's Pack Tactics aura and knock-Prone Bite, the Tiger's Pounce
   * structure, and the Lion's Roar (DC/range and its Frightened rider).
   */
  class BeastTest : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    static std::shared_ptr<Attack> makeMeleeAttack(Combatant *atk, Combatant *tgt)
    {
      auto factory = atk->getActionFactory(AbilityType::MELEE_ATTACK).lock();
      return std::dynamic_pointer_cast<Attack>(factory->create(static_cast<void *>(tgt)));
    }
  };

  // The Dire Wolf has the Pack Tactics passive marker.
  TEST_F(BeastTest, DireWolfHasPackTactics)
  {
    DireWolf wolf(1);
    EXPECT_TRUE(wolf.hasPassiveAbility(AbilityType::PACK_TACTICS));
  }

  // Pack Tactics grants Advantage when an ally is adjacent to the target, and not otherwise.
  TEST_F(BeastTest, PackTacticsAdvantageWhenAllyAdjacent)
  {
    DireWolf wolf(1);
    Goblin ally("AllyGoblin");
    Goblin target("TargetGoblin");
    teams->addCombatantToTeam(wolf, Color::BLUE);
    teams->addCombatantToTeam(ally, Color::BLUE);
    teams->addCombatantToTeam(target, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(wolf, Coord{1, 1});
    battleMap->setCombatantCoordinates(target, Coord{5, 5});
    battleMap->setCombatantCoordinates(ally, Coord{5, 6}); // adjacent to the target

    ActionResolver resolver;
    auto attack = makeMeleeAttack(&wolf, &target);
    ASSERT_NE(attack, nullptr);
    auto types = resolver.collectAttackRollTypes(attack.get(), &target, &wolf);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);
  }

  TEST_F(BeastTest, PackTacticsNoAdvantageWithoutAdjacentAlly)
  {
    DireWolf wolf(1);
    Goblin target("TargetGoblin");
    teams->addCombatantToTeam(wolf, Color::BLUE);
    teams->addCombatantToTeam(target, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(wolf, Coord{1, 1}); // the wolf itself does not count
    battleMap->setCombatantCoordinates(target, Coord{8, 8});

    ActionResolver resolver;
    auto attack = makeMeleeAttack(&wolf, &target);
    ASSERT_NE(attack, nullptr);
    auto types = resolver.collectAttackRollTypes(attack.get(), &target, &wolf);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 0u);
  }

  // The Dire Wolf's Bite carries an on-hit rider (the knock-Prone effect).
  TEST_F(BeastTest, DireWolfBiteHasOnHitRider)
  {
    DireWolf wolf(1);
    auto factory = wolf.getActionFactory(AbilityType::MELEE_ATTACK).lock();
    ASSERT_NE(factory, nullptr);
    auto *biteFactory = dynamic_cast<AttackFactory *>(factory.get());
    ASSERT_NE(biteFactory, nullptr);
    EXPECT_FALSE(biteFactory->getOnHits().empty());
  }

  // The Tiger's Pounce wraps a primary claw (with a Prone rider) and a follow-up Bite over a 4-cell charge.
  TEST_F(BeastTest, TigerPounceStructure)
  {
    Tiger tiger(1);
    auto factory = tiger.getActionFactory(AbilityType::POUNCE).lock();
    ASSERT_NE(factory, nullptr);
    auto *pounce = dynamic_cast<PounceFactory *>(factory.get());
    ASSERT_NE(pounce, nullptr);

    EXPECT_EQ(pounce->getDistance(), 4);
    ASSERT_NE(pounce->getPrimaryAttack(), nullptr);
    ASSERT_NE(pounce->getSecondaryAttack(), nullptr);
    // The primary attack knocks the target Prone on a hit (its on-hit rider).
    EXPECT_FALSE(pounce->getPrimaryAttack()->getOnHits().empty());
  }

  // The Lion's Roar is a DC 11 Wisdom-save Frighten with a 15 ft (3 cell) reach.
  TEST_F(BeastTest, LionRoarConfiguration)
  {
    Lion lion(1);
    auto factory = lion.getActionFactory(AbilityType::ROAR).lock();
    ASSERT_NE(factory, nullptr);
    auto *roar = dynamic_cast<RoarFactory *>(factory.get());
    ASSERT_NE(roar, nullptr);
    EXPECT_EQ(roar->getDc(), 11);
    EXPECT_EQ(roar->getRange(), 3);
  }

  // The Roar Frightened rider applies the Frightened condition on activation and clears it on deactivation.
  TEST_F(BeastTest, RoarFrightenedEffectAppliesAndClearsCondition)
  {
    Lion lion(1);
    Goblin victim(1);
    teams->addCombatantToTeam(lion, Color::BLUE);
    teams->addCombatantToTeam(victim, Color::RED);

    auto effect = std::make_shared<RoarFrightenedEffect>(&lion, std::vector<Combatant *>{&victim});
    effect->activate();
    EXPECT_TRUE(victim.isAffectedBy(Conditions::FRIGHTENED));

    effect->deactivate();
    EXPECT_FALSE(victim.isAffectedBy(Conditions::FRIGHTENED));
  }
} // namespace
