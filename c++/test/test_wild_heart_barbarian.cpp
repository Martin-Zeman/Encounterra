#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/action_resolver.hpp"
#include "actions/attack.hpp"
#include "actions/melee_attack.hpp"
#include "actions/movement.hpp"
#include "actions/action_types.hpp"
#include "abilities/rage.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/goblin.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include <algorithm>
#include <deque>
#include <functional>
#include <memory>
#include <vector>

using namespace enc;

namespace
{
  /**
   * Tests for the Path of the Wild Heart barbarian: the Rage of the Wilds aspects (Bear/Eagle/Wolf), the
   * Rage Damage bonus and duration bookkeeping, Reckless Attack's Advantage, the Danger Sense / Unarmored
   * Defense passives, and the Wolf aspect's allied-Advantage aura (verified via collectAttackRollTypes).
   */
  class WildHeartBarbarianTest : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    WildHeartBarbarianLvl3 *barbarian;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      barbarian = new WildHeartBarbarianLvl3(1);
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    static std::shared_ptr<RageFactory> rageFactory(Combatant *c, RageVariant variant)
    {
      for(auto &factory : c->getBonusActionFactories())
        {
          if(auto rage = std::dynamic_pointer_cast<RageFactory>(factory))
            {
              if(rage->getVariant() == variant)
                {
                  return rage;
                }
            }
        }
      return nullptr;
    }

    static std::shared_ptr<Rage> makeRage(Combatant *c, RageVariant variant)
    {
      auto factory = rageFactory(c, variant);
      if(!factory)
        {
          return nullptr;
        }
      return std::dynamic_pointer_cast<Rage>(factory->create(static_cast<void *>(c)));
    }

    static std::shared_ptr<Attack> makeMeleeAttack(Combatant *atk, Combatant *tgt)
    {
      auto factory = atk->getActionFactory(AbilityType::MELEE_ATTACK).lock();
      return std::dynamic_pointer_cast<Attack>(factory->create(static_cast<void *>(tgt)));
    }

    // Run the full planner (proto-DAG -> action DAG -> findBestSequence -> translate) and return the chosen
    // plan as an ordered list of concrete actoids, exactly as it would be executed this turn.
    std::deque<std::shared_ptr<Actoid>> planFor(Combatant *combatant)
    {
      auto [distances, shortestPaths] = battleMap->calcDijkstra(*combatant);
      combatant->setShortestPathsCache(shortestPaths);
      return combatant->calculateActionPlan(distances, shortestPaths);
    }

    // Index of the first actoid in the plan that satisfies `pred`, or -1 if none matches.
    static int firstIndexWhere(const std::deque<std::shared_ptr<Actoid>> &plan,
                               const std::function<bool(const std::shared_ptr<Actoid> &)> &pred)
    {
      for(int i = 0; i < static_cast<int>(plan.size()); ++i)
        {
          if(pred(plan[i]))
            {
              return i;
            }
        }
      return -1;
    }

    // Scenario: a lone goblin sits 3 cells outside the greataxe's reach, so the barbarian must Rage, walk up and
    // swing. Returns the planner's chosen plan in execution order.
    std::deque<std::shared_ptr<Actoid>> planRageScenario()
    {
      auto *enemy = new Goblin(1); // heap-allocated like the other end-to-end plan tests (owned by the session)
      session->addCombatant(barbarian, Color::BLUE);
      session->addCombatant(enemy, Color::RED);
      battleMap->buildBaseAdjacencyMatrix();
      battleMap->setCombatantCoordinates(*barbarian, Coord{2, 3});
      battleMap->setCombatantCoordinates(*enemy, Coord{6, 3}); // out of the greataxe's 1-cell reach
      return planFor(barbarian);
    }
  };

  // All three aspects are offered as Rage bonus actions, sharing one pool of Rage uses.
  TEST_F(WildHeartBarbarianTest, OffersAllThreeRageAspects)
  {
    EXPECT_NE(rageFactory(barbarian, RageVariant::BEAR), nullptr);
    EXPECT_NE(rageFactory(barbarian, RageVariant::EAGLE), nullptr);
    EXPECT_NE(rageFactory(barbarian, RageVariant::WOLF), nullptr);
  }

  // Entering a Rage grants the Rage Damage bonus (+2 at 3rd level); leaving the Rage removes it.
  TEST_F(WildHeartBarbarianTest, RageGrantsDamageBonus)
  {
    auto rage = makeRage(barbarian, RageVariant::WOLF);
    ASSERT_NE(rage, nullptr);
    const int before = barbarian->getAbilityDmgBonus();

    rage->activate();
    EXPECT_EQ(barbarian->getAbilityDmgBonus(), before + RageFactory::getRageBonus(barbarian->getLevel()));

    rage->deactivate();
    EXPECT_EQ(barbarian->getAbilityDmgBonus(), before);
  }

  // The Bear aspect resists a broad set of damage types (e.g. Fire); the resistance is removed when it ends.
  TEST_F(WildHeartBarbarianTest, BearRageResistsFire)
  {
    auto rage = makeRage(barbarian, RageVariant::BEAR);
    ASSERT_NE(rage, nullptr);

    rage->activate();
    EXPECT_TRUE(barbarian->isResistantTo(DamageType::Fire));
    EXPECT_TRUE(barbarian->isResistantTo(DamageType::Slashing));

    rage->deactivate();
    EXPECT_FALSE(barbarian->isResistantTo(DamageType::Fire));
  }

  // The non-Bear aspects resist only Bludgeoning/Piercing/Slashing (their benefit is mobility / ally support).
  TEST_F(WildHeartBarbarianTest, WolfRageResistsOnlyPhysical)
  {
    auto rage = makeRage(barbarian, RageVariant::WOLF);
    ASSERT_NE(rage, nullptr);

    rage->activate();
    EXPECT_TRUE(barbarian->isResistantTo(DamageType::Bludgeoning));
    EXPECT_FALSE(barbarian->isResistantTo(DamageType::Fire));
  }

  // The Eagle aspect Dashes and Disengages on entering the Rage: extra movement equal to Speed, no AoOs.
  TEST_F(WildHeartBarbarianTest, EagleRageDashesAndDisengages)
  {
    auto rage = makeRage(barbarian, RageVariant::EAGLE);
    ASSERT_NE(rage, nullptr);

    barbarian->newTurn(); // Movement starts at Speed.
    const int before = barbarian->getMovement();
    const int speed = barbarian->getSpeed();

    rage->activate();
    EXPECT_EQ(barbarian->getMovement(), before + speed);
    EXPECT_TRUE(barbarian->isDisengaging());
  }

  // 2024 Rage duration: entering counts as the first extension, so it survives one tick; without a further
  // extension it ends on the next tick, but markExtended() carries it for another round.
  TEST_F(WildHeartBarbarianTest, RageDurationRequiresExtension)
  {
    auto rage = makeRage(barbarian, RageVariant::BEAR);
    ASSERT_NE(rage, nullptr);

    rage->activate();
    EXPECT_TRUE(rage->startOfTurnTick());  // entering the Rage counted as an extension
    EXPECT_FALSE(rage->startOfTurnTick()); // no extension this round -> Rage ends

    auto rage2 = makeRage(barbarian, RageVariant::BEAR);
    ASSERT_NE(rage2, nullptr);
    rage2->activate();
    EXPECT_TRUE(rage2->startOfTurnTick());
    rage2->markExtended();
    EXPECT_TRUE(rage2->startOfTurnTick()); // extended this round -> survives
    EXPECT_FALSE(rage2->startOfTurnTick());
  }

  // Danger Sense and Unarmored Defense are registered as passive markers.
  TEST_F(WildHeartBarbarianTest, HasDefensivePassives)
  {
    EXPECT_TRUE(barbarian->hasPassiveAbility(AbilityType::DANGER_SENSE));
    EXPECT_TRUE(barbarian->hasPassiveAbility(AbilityType::UNARMORED_DEFENSE));
  }

  // The thrown javelin is a limited-ammunition ranged attack (4 javelins).
  TEST_F(WildHeartBarbarianTest, JavelinHasLimitedAmmo)
  {
    AttackFactory *javelin = nullptr;
    for(const auto &factory : barbarian->getActionFactoriesConst())
      {
        if(factory->getAbilityType() == AbilityType::RANGED_ATTACK)
          {
            javelin = dynamic_cast<AttackFactory *>(factory.get());
            break;
          }
      }
    ASSERT_NE(javelin, nullptr);
    auto resource = javelin->getResource();
    ASSERT_TRUE(resource.has_value());
    EXPECT_EQ(resource.value()->getUses(), 4);
  }

  // Reckless Attack is made with Advantage on the attack roll.
  TEST_F(WildHeartBarbarianTest, RecklessAttackHasAdvantage)
  {
    Goblin enemy(1);
    teams->addCombatantToTeam(*barbarian, Color::BLUE);
    teams->addCombatantToTeam(enemy, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*barbarian, Coord{3, 3});
    battleMap->setCombatantCoordinates(enemy, Coord{4, 3});

    auto factory = barbarian->getActionFactory(AbilityType::RECKLESS_ATTACK).lock();
    ASSERT_NE(factory, nullptr);
    auto attack = std::dynamic_pointer_cast<Attack>(factory->create(static_cast<void *>(&enemy)));
    ASSERT_NE(attack, nullptr);

    ActionResolver resolver;
    auto types = resolver.collectAttackRollTypes(attack.get(), &enemy, barbarian);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);
  }

  // Wolf aspect: while the barbarian rages, its allies have Advantage on attacks against enemies within 5 ft
  // of the barbarian. The barbarian itself does not benefit from its own aura.
  TEST_F(WildHeartBarbarianTest, WolfRageGivesAlliesAdvantage)
  {
    Goblin ally("AllyGoblin");
    Goblin enemy("EnemyGoblin");
    teams->addCombatantToTeam(*barbarian, Color::BLUE);
    teams->addCombatantToTeam(ally, Color::BLUE);
    teams->addCombatantToTeam(enemy, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*barbarian, Coord{5, 5});
    battleMap->setCombatantCoordinates(enemy, Coord{5, 6}); // within 5 ft of the barbarian
    battleMap->setCombatantCoordinates(ally, Coord{2, 2});

    auto rage = makeRage(barbarian, RageVariant::WOLF);
    ASSERT_NE(rage, nullptr);
    rage->activate();
    EffectTracker::getInstance().add(std::dynamic_pointer_cast<Effect>(rage));

    ActionResolver resolver;

    // The ally attacking the nearby enemy benefits from the Wolf aura.
    auto allyAttack = makeMeleeAttack(&ally, &enemy);
    ASSERT_NE(allyAttack, nullptr);
    auto allyTypes = resolver.collectAttackRollTypes(allyAttack.get(), &enemy, &ally);
    EXPECT_EQ(allyTypes.count(RollType::ADVANTAGE), 1u);

    // The barbarian attacking the same enemy does NOT get Advantage from its own aura.
    auto barbAttack = makeMeleeAttack(barbarian, &enemy);
    ASSERT_NE(barbAttack, nullptr);
    auto barbTypes = resolver.collectAttackRollTypes(barbAttack.get(), &enemy, barbarian);
    EXPECT_EQ(barbTypes.count(RollType::ADVANTAGE), 0u);
  }

  // ---------------------------------------------------------------------------------------------------------
  // Rage ordering — a priority bonus action that buffs the rest of the turn must be activated FIRST.
  //
  // Rage is a PRIORITY_BONUS_ACTION, so buildPriorityTransitions wires it into the action DAG as
  //
  //     state 0 --Rage--> "Raged" --move(coord)--> postState --axe--> nop
  //
  // i.e. it can only ever appear at the head of a sequence: there is no edge that places Rage after a movement
  // or an attack. These two tests pin that guarantee end-to-end through the planner (and therefore through the
  // S6 movement/action split, which keeps Rage in the movement prefix and splices the deduped action suffix
  // behind it). With the enemy out of melee reach, the chosen plan is [Rage, move..., axe]; Rage must precede
  // both the AoO-incurring movement (so its damage resistance is already up) and the attack it is meant to buff.
  // ---------------------------------------------------------------------------------------------------------

  TEST_F(WildHeartBarbarianTest, RageIsActivatedBeforeMovingAndProvokingAoO)
  {
    auto plan = planRageScenario();

    const int rageIdx = firstIndexWhere(plan, [](const std::shared_ptr<Actoid> &a) { return std::dynamic_pointer_cast<Rage>(a) != nullptr; });
    const int moveIdx =
      firstIndexWhere(plan, [](const std::shared_ptr<Actoid> &a) { return std::dynamic_pointer_cast<MovementIncrement>(a) != nullptr; });

    ASSERT_GE(rageIdx, 0) << "the planner did not choose to Rage";
    ASSERT_GE(moveIdx, 0) << "the planner did not move toward the out-of-reach enemy";
    EXPECT_LT(rageIdx, moveIdx) << "Rage must be entered before moving so its damage resistance mitigates any opportunity attack";
    EXPECT_EQ(rageIdx, 0) << "Rage should be the very first action of the turn";
  }

  TEST_F(WildHeartBarbarianTest, RageIsActivatedBeforeAttacking)
  {
    auto plan = planRageScenario();

    const int rageIdx = firstIndexWhere(plan, [](const std::shared_ptr<Actoid> &a) { return std::dynamic_pointer_cast<Rage>(a) != nullptr; });
    const int attackIdx = firstIndexWhere(plan, [](const std::shared_ptr<Actoid> &a) { return a->getAbilityType() == AbilityType::MELEE_ATTACK; });

    ASSERT_GE(rageIdx, 0) << "the planner did not choose to Rage";
    ASSERT_GE(attackIdx, 0) << "the planner did not choose to attack";
    EXPECT_LT(rageIdx, attackIdx) << "Rage must be entered before the attack so the Rage Damage bonus applies to the swing";
  }
} // namespace
