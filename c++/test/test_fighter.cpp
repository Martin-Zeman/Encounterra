#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/action_resolver.hpp"
#include "core/misc.hpp"
#include "actions/attack.hpp"
#include "actions/action_types.hpp"
#include "abilities/second_wind.hpp"
#include "abilities/action_surge.hpp"
#include "abilities/riposte.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/fighter_lvl_1.hpp"
#include "combatants/fighter_lvl_2.hpp"
#include "combatants/battlemaster_fighter_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_4.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include <memory>
#include <vector>

using namespace enc;

namespace
{
  /**
   * Tests for the migrated 2024 Fighter combatants (levels 1-5): the Second Wind self-heal, the Action Surge
   * free action, the Great Weapon Fighting fighting style, the greatsword/handaxe weapon masteries
   * (Graze / Vex), the Battle Master superiority dice and Riposte reaction, and the level-5 Extra Attack FSM.
   */
  class FighterTest : public ::testing::Test
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

    // Returns the attack factory carrying the given weapon mastery (Graze=greatsword, Vex=handaxe).
    static AttackFactory *weaponWithMastery(Combatant *c, WeaponMastery mastery)
    {
      for(const auto &factory : c->getActionFactoriesConst())
        {
          if(auto *attack = dynamic_cast<AttackFactory *>(factory.get()))
            {
              if(attack->getMastery() == mastery)
                {
                  return attack;
                }
            }
        }
      return nullptr;
    }

    static std::shared_ptr<SecondWindFactory> secondWindFactory(Combatant *c)
    {
      for(const auto &factory : c->getBonusActionFactoriesConst())
        {
          if(auto sw = std::dynamic_pointer_cast<SecondWindFactory>(factory))
            {
              return sw;
            }
        }
      return nullptr;
    }

    static std::shared_ptr<ActionSurgeFactory> actionSurgeFactory(Combatant *c)
    {
      for(const auto &factory : c->getFreeActionFactoriesConst())
        {
          if(auto as = std::dynamic_pointer_cast<ActionSurgeFactory>(factory))
            {
              return as;
            }
        }
      return nullptr;
    }
  };

  // --- Weapon masteries -----------------------------------------------------------------------------------

  // The greatsword carries Graze (on-miss damage) and the handaxe carries Vex (on-hit rider).
  TEST_F(FighterTest, WeaponsCarryExpectedMasteries)
  {
    FighterLvl1 fighter(1);

    AttackFactory *greatsword = weaponWithMastery(&fighter, WeaponMastery::GRAZE);
    AttackFactory *handaxe = weaponWithMastery(&fighter, WeaponMastery::VEX);

    ASSERT_NE(greatsword, nullptr) << "Greatsword should carry the Graze mastery";
    ASSERT_NE(handaxe, nullptr) << "Handaxe should carry the Vex mastery";

    EXPECT_EQ(greatsword->getAbilityType(), AbilityType::MELEE_ATTACK);
    EXPECT_EQ(greatsword->getGrazeDamage(), greatsword->getDmgBonus());
    EXPECT_TRUE(greatsword->isTwoHanded()) << "Greatsword must be two-handed for Great Weapon Fighting";

    EXPECT_EQ(handaxe->getAbilityType(), AbilityType::RANGED_ATTACK);
    EXPECT_EQ(handaxe->getOnHits().size(), 1u);
  }

  // The handaxe is a thrown weapon with limited ammunition (2 in hand).
  TEST_F(FighterTest, HandaxeHasLimitedAmmo)
  {
    FighterLvl1 fighter(1);
    AttackFactory *handaxe = weaponWithMastery(&fighter, WeaponMastery::VEX);
    ASSERT_NE(handaxe, nullptr);
    auto resource = handaxe->getResource();
    ASSERT_TRUE(resource.has_value());
    EXPECT_EQ(resource.value()->getUses(), 2);
  }

  // --- Second Wind ----------------------------------------------------------------------------------------

  // Every fighter level offers Second Wind as a bonus action with a single Short Rest use.
  TEST_F(FighterTest, OffersSecondWind)
  {
    FighterLvl1 fighter(1);
    auto factory = secondWindFactory(&fighter);
    ASSERT_NE(factory, nullptr);
    auto resource = factory->getResource();
    ASSERT_TRUE(resource.has_value());
    EXPECT_EQ(resource.value()->getUses(), 1);
  }

  // Resolving Second Wind heals the fighter for 1d10 + level, capped at maximum hit points.
  TEST_F(FighterTest, SecondWindHealsAndIsCapped)
  {
    FighterLvl1 fighter(1);
    auto factory = secondWindFactory(&fighter);
    ASSERT_NE(factory, nullptr);

    fighter.setCurrentHp(1);
    auto actoid = factory->create(static_cast<void *>(&fighter));
    ASSERT_NE(actoid, nullptr);

    ActionResolver resolver;
    resolver.resolveAction(actoid, &fighter);

    EXPECT_GT(fighter.getCurrentHp(), 1) << "Second Wind should restore hit points";
    EXPECT_LE(fighter.getCurrentHp(), fighter.getMaxHp()) << "Healing is capped at the maximum";
  }

  // --- Great Weapon Fighting & Action Surge ----------------------------------------------------------------

  // The Great Weapon Fighting fighting style is registered as a passive on every fighter level.
  TEST_F(FighterTest, HasGreatWeaponFighting)
  {
    FighterLvl1 fighter(1);
    EXPECT_TRUE(fighter.hasPassiveAbility(AbilityType::GREAT_WEAPON_FIGHTING));
  }

  // Great Weapon Fighting (2024): each weapon damage die that comes up 1 or 2 counts as a 3, so a 2d6 weapon
  // never rolls below 6 (and never above 12) on its weapon dice.
  TEST_F(FighterTest, GreatWeaponFightingFloorsLowDice)
  {
    const Die greatswordDice{2, 6};
    bool sawFlooredValue = false;
    for(int i = 0; i < 2000; ++i)
      {
        int sum = rollDiceWithFloor(greatswordDice, 3);
        ASSERT_GE(sum, 6) << "Each of 2d6 must count as at least 3 under Great Weapon Fighting";
        ASSERT_LE(sum, 12) << "2d6 can never exceed 12";
        if(sum == 6)
          {
            sawFlooredValue = true; // both dice were 1/2/3, i.e. the floor was exercised
          }
      }
    EXPECT_TRUE(sawFlooredValue) << "The 1/2 -> 3 floor should be exercised over many rolls";
  }

  // Action Surge is gained at 2nd level: a free action gated by a single Short Rest use.
  TEST_F(FighterTest, ActionSurgeFromLevelTwo)
  {
    FighterLvl1 fighterL1(1);
    EXPECT_FALSE(fighterL1.hasPassiveAbility(AbilityType::ACTION_SURGE));
    EXPECT_EQ(actionSurgeFactory(&fighterL1), nullptr);

    FighterLvl2 fighterL2(1);
    EXPECT_TRUE(fighterL2.hasPassiveAbility(AbilityType::ACTION_SURGE));
    auto factory = actionSurgeFactory(&fighterL2);
    ASSERT_NE(factory, nullptr);
    auto resource = factory->getResource();
    ASSERT_TRUE(resource.has_value());
    EXPECT_EQ(resource.value()->getUses(), 1);
  }

  // Resolving Action Surge grants the fighter an extra Action for the turn.
  TEST_F(FighterTest, ActionSurgeGrantsExtraAction)
  {
    FighterLvl2 fighter(1);
    auto factory = actionSurgeFactory(&fighter);
    ASSERT_NE(factory, nullptr);

    fighter.setHasAction(false);
    auto actoid = factory->create(static_cast<void *>(&fighter));
    ASSERT_NE(actoid, nullptr);
    EXPECT_TRUE(actoid->hasFlag(ActoidFlags::IS_ACTION_ENABLER));
  }

  // --- Tactical Mind --------------------------------------------------------------------------------------

  // Tactical Mind is a 2nd-level feature: a level-1 fighter does not have it, but levels 2+ do.
  TEST_F(FighterTest, TacticalMindFromLevelTwo)
  {
    FighterLvl1 fighterL1(1);
    EXPECT_FALSE(fighterL1.hasPassiveAbility(AbilityType::TACTICAL_MIND));

    FighterLvl2 fighterL2(1);
    EXPECT_TRUE(fighterL2.hasPassiveAbility(AbilityType::TACTICAL_MIND));

    BattlemasterFighterLvl3 fighterL3(1);
    EXPECT_TRUE(fighterL3.hasPassiveAbility(AbilityType::TACTICAL_MIND));
  }

  // An ability check that succeeds outright never expends Second Wind (Tactical Mind only kicks in on a fail).
  TEST_F(FighterTest, TacticalMindNotUsedOnSuccess)
  {
    FighterLvl2 fighter(1);
    auto sw = secondWindFactory(&fighter);
    ASSERT_NE(sw, nullptr);
    const int usesBefore = sw->getResource().value()->getUses();

    // A trivially easy check (DC 1) always succeeds without any help.
    EXPECT_TRUE(fighter.attemptAbilityCheck(50, 1, RollType::STRAIGHT));
    EXPECT_EQ(sw->getResource().value()->getUses(), usesBefore);
  }

  // An impossible check (even a nat-20 plus the Tactical Mind 1d10 cannot reach the DC) returns failure and,
  // since the 1d10 never turns it into a success, the Second Wind use is not expended.
  TEST_F(FighterTest, TacticalMindNotConsumedWhenItCannotRescue)
  {
    FighterLvl2 fighter(1);
    auto sw = secondWindFactory(&fighter);
    ASSERT_NE(sw, nullptr);
    const int usesBefore = sw->getResource().value()->getUses();

    EXPECT_FALSE(fighter.attemptAbilityCheck(0, 100, RollType::STRAIGHT));
    EXPECT_EQ(sw->getResource().value()->getUses(), usesBefore);
  }

  // When the base check fails but the Tactical Mind 1d10 can bridge the gap, the check succeeds and the
  // Second Wind use is expended. With bonus 0 vs DC 2 the only failing base roll is a 1, which 1 + 1d10
  // always rescues; over many fresh fighters at least one failing roll exercises the consume-the-resource
  // path, and the check never reports an unrecoverable failure.
  TEST_F(FighterTest, TacticalMindRescuesFailedCheckAndExpendsResource)
  {
    bool sawResourceConsumed = false;
    for(int i = 0; i < 400; ++i)
      {
        FighterLvl2 fighter(1);
        auto sw = secondWindFactory(&fighter);
        ASSERT_NE(sw, nullptr);

        EXPECT_TRUE(fighter.attemptAbilityCheck(0, 2, RollType::STRAIGHT));
        if(sw->getResource().value()->getUses() == 0)
          {
            sawResourceConsumed = true;
          }
      }
    EXPECT_TRUE(sawResourceConsumed) << "Tactical Mind should expend Second Wind when its 1d10 rescues a failed check";
  }

  // --- Battle Master: superiority dice & Riposte ----------------------------------------------------------

  // Battle Master maneuvers (3rd level) register the superiority dice resource (4 dice at level 3).
  TEST_F(FighterTest, BattleMasterHasSuperiorityDice)
  {
    BattlemasterFighterLvl3 fighter(1);
    EXPECT_TRUE(fighter.hasPassiveAbility(AbilityType::BATTLE_MASTER_MANEUVERS));

    AttackFactory *riposte = fighter.getRiposteFactory();
    ASSERT_NE(riposte, nullptr) << "Battle Master should register a Riposte reaction";
    auto resource = riposte->getResource();
    ASSERT_TRUE(resource.has_value());
    EXPECT_EQ(resource.value()->getUses(), getSuperiorityDiceCount(3));
  }

  // The Riposte attack adds a superiority die to the opportunity attack's damage dice.
  TEST_F(FighterTest, RiposteAddsSuperiorityDieDamage)
  {
    BattlemasterFighterLvl3 fighter(1);
    AttackFactory *riposte = fighter.getRiposteFactory();
    ASSERT_NE(riposte, nullptr);
    EXPECT_EQ(riposte->getAbilityType(), AbilityType::RIPOSTE);

    // Greatsword AoO is 2d6, so the Riposte should have an extra (superiority) die entry on top of it.
    const auto &dmgDice = riposte->getDmgDice();
    ASSERT_EQ(dmgDice.size(), 2u) << "Riposte should append the superiority die to the AoO damage";
    EXPECT_EQ(dmgDice.back(), getSuperiorityDie(3));
  }

  // Higher Battle Master levels scale the superiority dice count and die size correctly.
  TEST_F(FighterTest, SuperiorityDiceScaleWithLevel)
  {
    BattlemasterFighterLvl4 fighterL4(1);
    AttackFactory *riposteL4 = fighterL4.getRiposteFactory();
    ASSERT_NE(riposteL4, nullptr);
    EXPECT_EQ(riposteL4->getResource().value()->getUses(), getSuperiorityDiceCount(4));

    BattlemasterFighterLvl5 fighterL5(1);
    AttackFactory *riposteL5 = fighterL5.getRiposteFactory();
    ASSERT_NE(riposteL5, nullptr);
    EXPECT_EQ(riposteL5->getResource().value()->getUses(), getSuperiorityDiceCount(5));
  }

  // --- Extra Attack (level 5) ------------------------------------------------------------------------------

  // At 5th level the Extra Attack FSM grants a second attack with the same weapon (two greatsword swings),
  // then exhausts. The two weapons do not chain into one another.
  TEST_F(FighterTest, ExtraAttackGrantsSecondAttack)
  {
    BattlemasterFighterLvl5 fighter(1);
    AttackFactory *greatsword = weaponWithMastery(&fighter, WeaponMastery::GRAZE);
    AttackFactory *handaxe = weaponWithMastery(&fighter, WeaponMastery::VEX);
    ASSERT_NE(greatsword, nullptr);
    ASSERT_NE(handaxe, nullptr);

    EXPECT_TRUE(fighter.isAttackFsmAtStart());

    // First greatsword swing: a second greatsword swing is granted, but not a handaxe throw.
    fighter.triggerAttackFsm(greatsword);
    EXPECT_FALSE(fighter.isAttackFsmAtStart());
    EXPECT_TRUE(fighter.attackFsmHasTransition(greatsword));
    EXPECT_FALSE(fighter.attackFsmHasTransition(handaxe));

    // Second greatsword swing: the Extra Attack sequence is now exhausted.
    fighter.triggerAttackFsm(greatsword);
    EXPECT_FALSE(fighter.attackFsmHasTransition(greatsword));
    EXPECT_FALSE(fighter.attackFsmHasTransition(handaxe));
  }

  // A pre-Extra-Attack fighter (level 1) makes only a single attack: no second attack is granted.
  TEST_F(FighterTest, LevelOneHasNoExtraAttack)
  {
    FighterLvl1 fighter(1);
    AttackFactory *greatsword = weaponWithMastery(&fighter, WeaponMastery::GRAZE);
    ASSERT_NE(greatsword, nullptr);

    EXPECT_TRUE(fighter.isAttackFsmAtStart());
    fighter.triggerAttackFsm(greatsword);
    EXPECT_FALSE(fighter.attackFsmHasTransition(greatsword));
  }
}
