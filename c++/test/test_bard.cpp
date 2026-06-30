#include <gtest/gtest.h>
#include "actions/attack.hpp"
#include "combatants/bard_college_of_lore_lvl_3.hpp"
#include "combatants/goblin.hpp"
#include "combatants/ogre.hpp"
#include "core/action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/conditions.hpp"
#include "core/misc.hpp"
#include "core/session.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/effect.hpp"
#include <algorithm>
#include <vector>

using namespace enc;

namespace
{
  class BardCollegeOfLoreLvl3Test : public ::testing::Test
  {
  protected:
    void SetUp() override
    {
      BattleMap::resetInstance();
      Teams::resetInstance();
      EffectTracker::resetInstance();
      // Seed the RNG to a known state so save-roll outcomes are deterministic and independent of test
      // ordering. Several tests use extreme save modifiers (+/-30) to force a save success/failure, but the
      // engine treats a natural 1 as an auto-fail and a natural 20 as an auto-success, so an unseeded roll
      // could occasionally override the intended outcome.
      seedThreadRNG(7);
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    static bool hasFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      return std::any_of(factories.begin(), factories.end(),
                         [type](const std::shared_ptr<ActoidFactory> &factory) { return factory->getAbilityType() == type; });
    }

    static ActoidFactory *findFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      for(const auto &factory : factories)
        {
          if(factory->getAbilityType() == type)
            {
              return factory.get();
            }
        }
      return nullptr;
    }

    // Builds a 1v1 (or 1v1+ally) scenario with adjacent combatants so range checks pass, then returns it.
    static void placeAdjacent(Combatant &bard, Combatant &enemy)
    {
      BattleMap::getInstance().setCombatantCoordinates(bard, Coord{5, 5});
      BattleMap::getInstance().setCombatantCoordinates(enemy, Coord{5, 6});
      BattleMap::getInstance().buildBaseAdjacencyMatrix();
    }
  };

  TEST_F(BardCollegeOfLoreLvl3Test, StatsAndFactoriesFromSheet)
  {
    BardCollegeOfLoreLvl3 bard(1);

    EXPECT_EQ(bard.getMaxHp(), 24);
    EXPECT_EQ(bard.getAC(), 13);
    EXPECT_EQ(bard.getSpeed(), 6);
    EXPECT_EQ(bard.getDC(), 13);
    EXPECT_EQ(bard.getLevel(), 3);

    EXPECT_EQ(bard.getSavingThrow(SavingThrow::STR), 0);
    EXPECT_EQ(bard.getSavingThrow(SavingThrow::DEX), 4);
    EXPECT_EQ(bard.getSavingThrow(SavingThrow::CON), 1);
    EXPECT_EQ(bard.getSavingThrow(SavingThrow::INT), 0);
    EXPECT_EQ(bard.getSavingThrow(SavingThrow::WIS), 1);
    EXPECT_EQ(bard.getSavingThrow(SavingThrow::CHA), 5);

    // Bard is a full caster: 4 first-level and 2 second-level slots at level 3.
    EXPECT_EQ(bard.getSpellslots().getUses(1), 4);
    EXPECT_EQ(bard.getSpellslots().getUses(2), 2);

    // Actions
    EXPECT_TRUE(hasFactory(bard.getActionFactoriesConst(), AbilityType::VICIOUS_MOCKERY));
    EXPECT_TRUE(hasFactory(bard.getActionFactoriesConst(), AbilityType::BANE));
    EXPECT_TRUE(hasFactory(bard.getActionFactoriesConst(), AbilityType::CHARM_PERSON));
    EXPECT_TRUE(hasFactory(bard.getActionFactoriesConst(), AbilityType::COLOR_SPRAY));
    EXPECT_TRUE(hasFactory(bard.getActionFactoriesConst(), AbilityType::DISSONANT_WHISPERS));

    // College of Lore features
    EXPECT_TRUE(hasFactory(bard.getBonusActionFactoriesConst(), AbilityType::BARDIC_INSPIRATION));
    EXPECT_TRUE(hasFactory(bard.getBonusActionFactoriesConst(), AbilityType::HEALING_WORD));
    EXPECT_TRUE(hasFactory(bard.getReactionFactoriesConst(), AbilityType::CUTTING_WORDS));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, BardicInspirationUsesEqualCharismaModifier)
  {
    BardCollegeOfLoreLvl3 bard(1);

    // Spellcasting modifier is +3 (DC 13), so Bardic Inspiration starts with 3 uses.
    EXPECT_EQ(bard.getSpellcastingModifier(), 3);

    auto resource = bard.getResource(AbilityType::BARDIC_INSPIRATION);
    ASSERT_TRUE(resource.has_value());
    EXPECT_EQ((*resource)->getUses(), 3);
  }

  TEST_F(BardCollegeOfLoreLvl3Test, RapierMeleeAttackUsesDexterity)
  {
    BardCollegeOfLoreLvl3 bard(1);

    AttackFactory *rapier = nullptr;
    for(const auto &factory : bard.getActionFactoriesConst())
      {
        if(auto *attack = dynamic_cast<AttackFactory *>(factory.get()))
          {
            rapier = attack;
            break;
          }
      }

    ASSERT_NE(rapier, nullptr);
    EXPECT_EQ(rapier->getToHit(), 4);
    EXPECT_EQ(rapier->getDmgBonus(), 2);
  }

  // ------------------------------------------------------------------------------------------------------------
  // Combat-scenario tests: a real battle is set up, the ability is resolved and the resulting effect verified.
  // Saving throws are made deterministic by giving the target an extreme save bonus (very high to always pass,
  // very low to always fail) versus the bard's spell DC of 13.
  // ------------------------------------------------------------------------------------------------------------

  TEST_F(BardCollegeOfLoreLvl3Test, BaneAppliesSavePenaltyOnFailedSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *goblin = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(goblin, Color::RED);
    placeAdjacent(*bard, *goblin);

    goblin->setSavingThrow(SavingThrow::CHA, -30); // guaranteed to fail the save

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::BANE);
    ASSERT_NE(factory, nullptr);
    std::vector<Combatant *> targets{goblin};
    auto action = factory->create(static_cast<void *>(&targets));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, bard), ActionResult::OTHER);

    // A failed save subtracts 1d4 from the target's attack rolls and saving throws (no flat modifier).
    EXPECT_FALSE(goblin->getToHitPenaltyDice().empty());
    EXPECT_FALSE(goblin->getSavingThrowPenaltyDice(SavingThrow::WIS).empty());
    EXPECT_TRUE(goblin->getSavingThrowFlatMods(SavingThrow::WIS).empty());
    EXPECT_TRUE(bard->isConcentrating());
  }

  TEST_F(BardCollegeOfLoreLvl3Test, BaneHasNoEffectWhenTargetSaves)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *goblin = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(goblin, Color::RED);
    placeAdjacent(*bard, *goblin);

    goblin->setSavingThrow(SavingThrow::CHA, 30); // guaranteed to succeed

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::BANE);
    ASSERT_NE(factory, nullptr);
    std::vector<Combatant *> targets{goblin};
    auto action = factory->create(static_cast<void *>(&targets));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_TRUE(goblin->getToHitPenaltyDice().empty());
    EXPECT_TRUE(goblin->getSavingThrowPenaltyDice(SavingThrow::WIS).empty());
    EXPECT_FALSE(bard->isConcentrating());
  }

  TEST_F(BardCollegeOfLoreLvl3Test, CharmPersonCharmsHumanoidOnFailedSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *goblin = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(goblin, Color::RED);
    placeAdjacent(*bard, *goblin);

    ASSERT_TRUE(goblin->isHumanoid());
    goblin->setSavingThrow(SavingThrow::WIS, -30); // guaranteed failure

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::CHARM_PERSON);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(goblin));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_TRUE(goblin->isAffectedBy(Conditions::CHARMED));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, CharmPersonFailsWhenTargetSaves)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *goblin = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(goblin, Color::RED);
    placeAdjacent(*bard, *goblin);

    goblin->setSavingThrow(SavingThrow::WIS, 30); // guaranteed success

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::CHARM_PERSON);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(goblin));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_FALSE(goblin->isAffectedBy(Conditions::CHARMED));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, AttackAvoidsCharmedEnemyWhenAnotherIsAvailable)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *charmed = new Goblin(1);
    auto *other = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(charmed, Color::RED);
    session.addCombatant(other, Color::RED);
    BattleMap::getInstance().setCombatantCoordinates(*bard, Coord{5, 5});
    BattleMap::getInstance().setCombatantCoordinates(*charmed, Coord{5, 6});
    BattleMap::getInstance().setCombatantCoordinates(*other, Coord{6, 5});
    BattleMap::getInstance().buildBaseAdjacencyMatrix();

    charmed->applyCondition(Condition(Conditions::CHARMED, bard));

    auto enemies = BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(bard, 3);
    EXPECT_TRUE(std::find(enemies.begin(), enemies.end(), other) != enemies.end());
    EXPECT_TRUE(std::find(enemies.begin(), enemies.end(), charmed) == enemies.end());
  }

  TEST_F(BardCollegeOfLoreLvl3Test, AttackTargetsCharmedEnemyWhenItIsTheOnlyOne)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *charmed = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(charmed, Color::RED);
    placeAdjacent(*bard, *charmed);

    charmed->applyCondition(Condition(Conditions::CHARMED, bard));

    auto enemies = BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(bard, 3);
    EXPECT_TRUE(std::find(enemies.begin(), enemies.end(), charmed) != enemies.end());
  }

  TEST_F(BardCollegeOfLoreLvl3Test, CharmedCombatantSkipsItsTurn)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *charmed = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(charmed, Color::RED);
    placeAdjacent(*bard, *charmed);

    charmed->applyCondition(Condition(Conditions::CHARMED, bard));

    // A charmed combatant treats the caster's side as friendly and so has no one to act against: the round
    // manager skips its turn via the same condition gate as Incapacitated/Stunned/etc.
    EXPECT_TRUE(charmed->isAffectedByAny({Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED,
                                          Conditions::PETRIFIED, Conditions::UNCONSCIOUS, Conditions::CHARMED}));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, ColorSprayBlindsEnemiesInBurstOnFailedSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *goblin = new Goblin(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(goblin, Color::RED);
    placeAdjacent(*bard, *goblin);

    goblin->setSavingThrow(SavingThrow::CON, -30); // guaranteed failure

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::COLOR_SPRAY);
    ASSERT_NE(factory, nullptr);
    auto actions = factory->createAll();
    ASSERT_FALSE(actions.empty());

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(actions.front(), bard), ActionResult::OTHER);

    EXPECT_TRUE(goblin->isAffectedBy(Conditions::BLINDED));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, ViciousMockeryDamagesTargetOnFailedSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    ogre->setSavingThrow(SavingThrow::WIS, -30); // guaranteed failure -> takes psychic damage
    int startHp = ogre->getCurrentHp();

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::VICIOUS_MOCKERY);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, bard), ActionResult::OTHER);
    EXPECT_LT(ogre->getCurrentHp(), startHp);
  }

  TEST_F(BardCollegeOfLoreLvl3Test, ViciousMockeryGivesDisadvantageOnNextAttackOnFailedSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    ogre->setSavingThrow(SavingThrow::WIS, -30); // guaranteed failure -> Disadvantage on next attack

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::VICIOUS_MOCKERY);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(ogre, EffectType::SAPPED));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, ViciousMockeryNoDisadvantageWhenTargetSaves)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    ogre->setSavingThrow(SavingThrow::WIS, 30); // guaranteed success -> no Disadvantage rider

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::VICIOUS_MOCKERY);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_FALSE(EffectTracker::getInstance().isAffectingCombatant(ogre, EffectType::SAPPED));
  }

  TEST_F(BardCollegeOfLoreLvl3Test, DissonantWhispersHalvesDamageOnSuccessfulSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    ogre->setSavingThrow(SavingThrow::WIS, 30); // guaranteed success -> half damage, not zero
    int startHp = ogre->getCurrentHp();

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::DISSONANT_WHISPERS);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, bard), ActionResult::OTHER);
    EXPECT_LT(ogre->getCurrentHp(), startHp); // still takes half on a save
  }

  TEST_F(BardCollegeOfLoreLvl3Test, DissonantWhispersForcesReactionFleeOnFailedSave)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    ogre->setSavingThrow(SavingThrow::WIS, -30); // guaranteed failure -> must flee using its Reaction
    ASSERT_TRUE(ogre->hasReaction());
    const int startDist = BattleMap::getInstance().getHopDistanceCombatants(*ogre, *bard);

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::DISSONANT_WHISPERS);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_FALSE(ogre->hasReaction()); // Reaction spent fleeing
    // The target must end up farther from the caster than it started.
    EXPECT_GT(BattleMap::getInstance().getHopDistanceCombatants(*ogre, *bard), startDist);
  }

  TEST_F(BardCollegeOfLoreLvl3Test, DissonantWhispersKeepsReactionWhenTargetSaves)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    ogre->setSavingThrow(SavingThrow::WIS, 30); // guaranteed success -> no forced flee
    ASSERT_TRUE(ogre->hasReaction());

    auto *factory = findFactory(bard->getActionFactoriesConst(), AbilityType::DISSONANT_WHISPERS);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    resolver.resolveAction(action, bard);

    EXPECT_TRUE(ogre->hasReaction());
  }

  TEST_F(BardCollegeOfLoreLvl3Test, BardicInspirationGrantsAllyToHitAndSaveDie)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ally = new Goblin(1);
    auto *enemy = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ally, Color::BLUE);
    session.addCombatant(enemy, Color::RED);
    BattleMap::getInstance().setCombatantCoordinates(*bard, Coord{5, 5});
    BattleMap::getInstance().setCombatantCoordinates(*ally, Coord{5, 6});
    BattleMap::getInstance().setCombatantCoordinates(*enemy, Coord{8, 8});
    BattleMap::getInstance().buildBaseAdjacencyMatrix();

    auto *factory = findFactory(bard->getBonusActionFactoriesConst(), AbilityType::BARDIC_INSPIRATION);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ally));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, bard), ActionResult::OTHER);

    ASSERT_EQ(ally->getToHitDiceMods().size(), 1u);
    EXPECT_EQ(ally->getToHitDiceMods().front()[0], 1);
    EXPECT_EQ(ally->getToHitDiceMods().front()[1], 6);
    ASSERT_EQ(ally->getSavingThrowDiceMods(SavingThrow::DEX).size(), 1u);
    EXPECT_EQ(ally->getSavingThrowDiceMods(SavingThrow::DEX).front()[1], 6);
  }

  TEST_F(BardCollegeOfLoreLvl3Test, CuttingWordsResolvesAsReaction)
  {
    auto *bard = new BardCollegeOfLoreLvl3(1);
    auto *ogre = new Ogre(1);
    Session session;
    session.addCombatant(bard, Color::BLUE);
    session.addCombatant(ogre, Color::RED);
    placeAdjacent(*bard, *ogre);

    auto *factory = findFactory(bard->getReactionFactoriesConst(), AbilityType::CUTTING_WORDS);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(ogre));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, bard), ActionResult::OTHER);
  }
}
