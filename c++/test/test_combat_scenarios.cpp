#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/types.hpp"
#include "core/action_resolver.hpp"
#include "core/round_manager.hpp"
#include "actions/action_selection.hpp"
#include "actions/attack.hpp"
#include "actions/melee_attack.hpp"
#include "actions/action_types.hpp"
#include "spells/faerie_fire.hpp"
#include "effects/effect.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/goblin.hpp"
#include "combatants/dire_wolf.hpp"
#include "combatants/moon_druid_lvl_3.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include <memory>

using namespace enc;

namespace
{
  /**
   * Integration / scenario tests. Unlike the unit tests, these set up a real encounter on the battle map, ask
   * the engine for the next action via getAction(), resolve it with the ActionResolver, and advance from turn to
   * turn -- mirroring the inner loop of RoundManager::simulate() and the step-through style used in the Python
   * simulator's tests. Scenarios are made (near-)deterministic by pinning positions, lowering target AC to 1 and
   * giving targets a large HP pool, and by driving several turns so a single unlucky d20 cannot flip the outcome.
   */
  class CombatScenarioTest : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    ActionResolver resolver;

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

    // Drives a single full turn for `c`, faithfully reproducing the per-combatant phases of
    // RoundManager::simulate(): start-of-turn effects, action-economy reset, then the get-action / resolve
    // loop until no further action is feasible, then end-of-turn bookkeeping.
    void runTurn(Combatant *c)
    {
      auto &effectTracker = EffectTracker::getInstance();

      c->rollForRecharge();
      effectTracker.startOfTurnTick(c);
      effectTracker.startOfTurn(c);
      if(!c->isAlive())
        {
          return;
        }

      c->newTurn();
      c->endGrappleIfGrapplerIncapacitated();
      resolver.resolveEffects(effectTracker.getAffectingCombatant(c), c);

      while(true)
        {
          auto action = getAction(c);
          if(!action)
            {
              break;
            }
          ActionResult resolution = resolver.resolveAction(action, c);
          if(resolution == ActionResult::UNFEASIBLE)
            {
              break;
            }
          if(!c->isAlive())
            {
              effectTracker.combatantDied(c);
              break;
            }
        }

      if(c->isAlive())
        {
          effectTracker.endOfTurn(c);
          c->onEndOfTurn();
        }
    }
  };

  // A full encounter driven through the engine's own RoundManager loop (initiative, rounds, per-combatant turns,
  // win detection) -- the closest analogue to the Python statistical/system tests. A strong barbarian against a
  // single fragile, adjacent goblin resolves to a barbarian victory well within the round budget.
  TEST_F(CombatScenarioTest, FullEncounterResolvesWithStrongerSideWinning)
  {
    WildHeartBarbarianLvl5 barbarian(1);
    Goblin enemy("Enemy");
    teams->addCombatantToTeam(barbarian, Color::BLUE);
    teams->addCombatantToTeam(enemy, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(barbarian, Coord{5, 5});
    battleMap->setCombatantCoordinates(enemy, Coord{6, 5}); // adjacent: melee from round one, no long-range planning

    enemy.setAC(1);          // the barbarian's swings connect
    enemy.setCurrentHp(5);   // and the goblin is fragile enough to fall quickly

    std::vector<Combatant *> combatants{&barbarian, &enemy};
    RoundManager roundManager(combatants, 10);
    roundManager.simulate();

    EXPECT_FALSE(enemy.isAlive());                                  // the goblin was defeated
    EXPECT_TRUE(barbarian.isAlive());                              // by the surviving barbarian
    EXPECT_EQ(teams->getSurvivingTeams().size(), 1u);             // the fight is decided
  }

  // An adjacent attacker grinds the enemy's HP down over several turns. Each turn the action economy resets so the
  // attacker can strike again; the target's large HP pool means it survives long enough to observe the damage.
  TEST_F(CombatScenarioTest, AdjacentAttackerWearsDownEnemyAcrossTurns)
  {
    Goblin striker("Striker");
    Goblin enemy("Enemy");
    teams->addCombatantToTeam(striker, Color::BLUE);
    teams->addCombatantToTeam(enemy, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(striker, Coord{5, 5});
    battleMap->setCombatantCoordinates(enemy, Coord{6, 5}); // adjacent: in reach from the start

    enemy.setAC(1);             // any roll but a natural 1 connects
    enemy.setCurrentHp(200);    // and it survives the whole scenario

    runTurn(&striker);
    // Having an enemy in range, the turn necessarily spends the Attack action; this is independent of the d20.
    EXPECT_FALSE(striker.hasAction());

    // The start of the next turn refreshes the action economy, which is what lets the attacker keep striking.
    striker.newTurn();
    EXPECT_TRUE(striker.hasAction());
    EXPECT_EQ(striker.getMovement(), striker.getSpeed());

    // Drive a few more turns; across this many swings vs AC 1 a total whiff is astronomically unlikely.
    runTurn(&striker);
    runTurn(&striker);
    EXPECT_LT(enemy.getCurrentHp(), 200); // the enemy has taken damage over the turns
  }

  // Pack Tactics in a live encounter: with an ally next to the target, the Dire Wolf's bite is made with
  // Advantage, and over a few turns it reliably draws blood.
  TEST_F(CombatScenarioTest, PackTacticsBiteHitsWithAdvantageOverTurns)
  {
    DireWolf wolf(1);
    Goblin ally("Ally");
    Goblin target("Target");
    teams->addCombatantToTeam(wolf, Color::BLUE);
    teams->addCombatantToTeam(ally, Color::BLUE);
    teams->addCombatantToTeam(target, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(wolf, Coord{5, 5});
    battleMap->setCombatantCoordinates(target, Coord{7, 6}); // adjacent to the Large wolf's footprint
    battleMap->setCombatantCoordinates(ally, Coord{8, 6});   // adjacent to the target -> triggers Pack Tactics

    target.setAC(1);
    target.setCurrentHp(200);

    // The advantage source is deterministic regardless of the dice.
    auto bite = makeMeleeAttack(&wolf, &target);
    ASSERT_NE(bite, nullptr);
    auto types = resolver.collectAttackRollTypes(bite.get(), &target, &wolf);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);

    // The advantage also pays off in a driven turn: bite with advantage vs AC 1 across a few turns connects.
    runTurn(&wolf);
    runTurn(&wolf);
    EXPECT_LT(target.getCurrentHp(), 200);
  }

  // Faerie Fire in a live encounter: an outlined target is attacked with Advantage, the outline keeps granting it
  // across the target's own intervening turn, and the attacker grinds it down over several rounds.
  TEST_F(CombatScenarioTest, FaerieFireOutlineGrantsAdvantageAndPersistsAcrossTurns)
  {
    MoonDruidLvl3 druid(1);
    Goblin attacker("Attacker");
    Goblin target("Target");
    teams->addCombatantToTeam(druid, Color::BLUE);
    teams->addCombatantToTeam(attacker, Color::BLUE);
    teams->addCombatantToTeam(target, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(druid, Coord{2, 2});
    battleMap->setCombatantCoordinates(target, Coord{5, 5});
    battleMap->setCombatantCoordinates(attacker, Coord{6, 5}); // adjacent to the target

    target.setAC(1);
    target.setCurrentHp(200);
    target.setSavingThrow(SavingThrow::DEX, -100); // make the outline land deterministically

    // Stand in for the druid having cast Faerie Fire on the target's square.
    auto factory = std::dynamic_pointer_cast<FaerieFireFactory>(druid.getActionFactory(AbilityType::FAERIE_FIRE).lock());
    ASSERT_NE(factory, nullptr);
    Coord coord = battleMap->getCombatantCoordinates(target).getRoot();
    auto faerieFire = std::dynamic_pointer_cast<FaerieFire>(factory->create(static_cast<void *>(&coord)));
    ASSERT_NE(faerieFire, nullptr);
    EffectTracker::getInstance().add(std::dynamic_pointer_cast<Effect>(faerieFire));
    for(int i = 0; i < 100 && !faerieFire->isAffecting(&target); ++i)
      {
        faerieFire->activate();
      }
    ASSERT_TRUE(EffectTracker::getInstance().isAffectingCombatant(&target, EffectType::FAERIE_FIRE));

    // The outline grants attackers Advantage -- verified deterministically before any dice are thrown.
    auto attack = makeMeleeAttack(&attacker, &target);
    ASSERT_NE(attack, nullptr);
    auto types = resolver.collectAttackRollTypes(attack.get(), &target, &attacker);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);

    // Attacker takes its turn against the outlined enemy.
    runTurn(&attacker);

    // The target now takes its own turn; the outline (the druid's concentration) should survive it.
    runTurn(&target);
    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(&target, EffectType::FAERIE_FIRE));

    // A couple more attacker turns wear the outlined target down.
    runTurn(&attacker);
    runTurn(&attacker);
    EXPECT_LT(target.getCurrentHp(), 200);
  }

  TEST_F(CombatScenarioTest, GetUpFromProneClearsProneAndDoesNotRepeat)
  {
    Goblin prone("Prone");
    Goblin enemy("Enemy");
    teams->addCombatantToTeam(prone, Color::BLUE);
    teams->addCombatantToTeam(enemy, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(prone, Coord{5, 5});
    battleMap->setCombatantCoordinates(enemy, Coord{6, 5});

    prone.applyCondition(Condition(Conditions::PRONE, &enemy, nullptr, &prone));
    prone.newTurn();
    prone.setMovement(5);

    auto action = getAction(&prone);
    ASSERT_NE(action, nullptr);
    ASSERT_EQ(action->getAbilityType(), AbilityType::GET_UP_FROM_PRONE);

    EXPECT_EQ(resolver.resolveAction(action, &prone), ActionResult::OTHER);
    EXPECT_FALSE(prone.isAffectedBy(Conditions::PRONE));
    EXPECT_EQ(prone.getMovement(), 5 - std::max(1, prone.getSpeed() / 2));

    auto nextAction = getAction(&prone);
    ASSERT_NE(nextAction, nullptr);
    EXPECT_NE(nextAction->getAbilityType(), AbilityType::GET_UP_FROM_PRONE);
  }

  TEST_F(CombatScenarioTest, GetUpFromProneRequiresHalfSpeedMovement)
  {
    Goblin prone("Prone");
    Goblin enemy("Enemy");
    teams->addCombatantToTeam(prone, Color::BLUE);
    teams->addCombatantToTeam(enemy, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(prone, Coord{5, 5});
    battleMap->setCombatantCoordinates(enemy, Coord{6, 5});

    prone.applyCondition(Condition(Conditions::PRONE, &enemy, nullptr, &prone));
    prone.newTurn();
    prone.setMovement(1);

    auto action = getAction(&prone);
    ASSERT_NE(action, nullptr);
    EXPECT_NE(action->getAbilityType(), AbilityType::GET_UP_FROM_PRONE);
  }
} // namespace
