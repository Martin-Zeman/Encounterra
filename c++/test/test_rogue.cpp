#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "core/action_resolver.hpp"
#include "combatants/rogue_lvl_1.hpp"
#include "combatants/rogue_lvl_2.hpp"
#include "combatants/assassin_rogue_lvl_3.hpp"
#include "combatants/goblin.hpp"
#include "abilities/on_hit_sneak_attack.hpp"
#include "actions/attack.hpp"
#include "actions/hide.hpp"
#include "effects/effect_tracker.hpp"
#include "actions/action_types.hpp"
#include <algorithm>
#include <memory>

using namespace enc;

namespace
{
  class RogueTest : public ::testing::Test
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

    static bool hasSneakAttackRider(const AttackFactory *factory)
    {
      for(const auto &onHit : factory->getOnHits())
        {
          if(dynamic_cast<OnHitSneakAttack *>(onHit.get()) != nullptr)
            {
              return true;
            }
        }
      return false;
    }
  };

  // ----------------------------------------------------------------------------------------------------------
  // Level 1 rogue: base stats, weapons and Sneak Attack.
  // ----------------------------------------------------------------------------------------------------------
  TEST_F(RogueTest, Lvl1BaseStats)
  {
    RogueLvl1 rogue(1);
    EXPECT_EQ(rogue.getMaxHp(), 9);
    EXPECT_EQ(rogue.getAC(), 14);
    EXPECT_EQ(rogue.getDC(), 13);
    EXPECT_EQ(rogue.getLevel(), 1);
    EXPECT_EQ(rogue.getSpeed(), 6); // 30 ft stored as 6 grid cells (5 ft each)
    EXPECT_TRUE(rogue.isHumanoid());
  }

  TEST_F(RogueTest, Lvl1SavingThrowsAndSkills)
  {
    RogueLvl1 rogue(1);
    EXPECT_EQ(rogue.getSavingThrow(SavingThrow::STR), -1);
    EXPECT_EQ(rogue.getSavingThrow(SavingThrow::DEX), 5);
    EXPECT_EQ(rogue.getSavingThrow(SavingThrow::CON), 1);
    EXPECT_EQ(rogue.getSavingThrow(SavingThrow::INT), 4);
    EXPECT_EQ(rogue.getSavingThrow(SavingThrow::WIS), 1);
    EXPECT_EQ(rogue.getSavingThrow(SavingThrow::CHA), 1);
    EXPECT_EQ(rogue.getStealth(), 7);
    EXPECT_EQ(rogue.getPassivePerception(), 11);
  }

  TEST_F(RogueTest, Lvl1HasWeaponsAndSneakAttack)
  {
    RogueLvl1 rogue(1);
    EXPECT_TRUE(rogue.hasPassiveAbility(AbilityType::SNEAK_ATTACK));

    const auto &actions = rogue.getActionFactoriesConst();
    auto *melee = dynamic_cast<AttackFactory *>(findFactory(actions, AbilityType::MELEE_ATTACK));
    auto *ranged = dynamic_cast<AttackFactory *>(findFactory(actions, AbilityType::RANGED_ATTACK));
    ASSERT_NE(melee, nullptr);
    ASSERT_NE(ranged, nullptr);

    // The Finesse rapier is wielded with Dexterity, so both the rapier and shortbow qualify for Sneak Attack.
    EXPECT_TRUE(melee->usesDex());
    EXPECT_TRUE(hasSneakAttackRider(melee));
    EXPECT_TRUE(hasSneakAttackRider(ranged));
  }

  TEST_F(RogueTest, SneakAttackDiceScaleWithLevel)
  {
    // ceil(level / 2) d6: 1d6 at levels 1-2, 2d6 at level 3. Die is [count, sides].
    EXPECT_EQ(OnHitSneakAttack::getDmgDice(1)[0], 1u);
    EXPECT_EQ(OnHitSneakAttack::getDmgDice(1)[1], 6u);
    EXPECT_EQ(OnHitSneakAttack::getDmgDice(2)[0], 1u);
    EXPECT_EQ(OnHitSneakAttack::getDmgDice(3)[0], 2u);
  }

  TEST_F(RogueTest, Lvl1HasNoCunningActionOrAssassinate)
  {
    RogueLvl1 rogue(1);
    const auto &bonus = rogue.getBonusActionFactoriesConst();
    EXPECT_FALSE(hasFactory(bonus, AbilityType::CUNNING_DASH));
    EXPECT_FALSE(hasFactory(bonus, AbilityType::CUNNING_HIDE));
    EXPECT_FALSE(hasFactory(bonus, AbilityType::CUNNING_DISENGAGE));
    EXPECT_FALSE(rogue.hasPassiveAbility(AbilityType::ASSASSINATE));
  }

  TEST_F(RogueTest, SneakAttackFlagResetsEachTurn)
  {
    RogueLvl1 rogue(1);
    rogue.setAlreadyUsedSneakAttackThisTurn(true);
    EXPECT_TRUE(rogue.hasAlreadyUsedSneakAttackThisTurn());
    rogue.newTurn();
    EXPECT_FALSE(rogue.hasAlreadyUsedSneakAttackThisTurn());
  }

  // ----------------------------------------------------------------------------------------------------------
  // Level 2 rogue: Cunning Action.
  // ----------------------------------------------------------------------------------------------------------
  TEST_F(RogueTest, Lvl2BaseStats)
  {
    RogueLvl2 rogue(1);
    EXPECT_EQ(rogue.getMaxHp(), 15);
    EXPECT_EQ(rogue.getLevel(), 2);
  }

  TEST_F(RogueTest, Lvl2HasCunningActionBonusActions)
  {
    RogueLvl2 rogue(1);
    const auto &bonus = rogue.getBonusActionFactoriesConst();
    EXPECT_TRUE(hasFactory(bonus, AbilityType::CUNNING_DASH));
    EXPECT_TRUE(hasFactory(bonus, AbilityType::CUNNING_HIDE));
    EXPECT_TRUE(hasFactory(bonus, AbilityType::CUNNING_DISENGAGE));
    // Sneak Attack still present at level 2.
    EXPECT_TRUE(rogue.hasPassiveAbility(AbilityType::SNEAK_ATTACK));
    EXPECT_FALSE(rogue.hasPassiveAbility(AbilityType::ASSASSINATE));
  }

  // ----------------------------------------------------------------------------------------------------------
  // Level 3 Assassin rogue.
  // ----------------------------------------------------------------------------------------------------------
  TEST_F(RogueTest, AssassinBaseStatsAndAbilities)
  {
    AssassinRogueLvl3 rogue(1);
    EXPECT_EQ(rogue.getMaxHp(), 21);
    EXPECT_EQ(rogue.getAC(), 15);
    EXPECT_EQ(rogue.getLevel(), 3);
    EXPECT_TRUE(rogue.hasPassiveAbility(AbilityType::SNEAK_ATTACK));
    EXPECT_TRUE(rogue.hasPassiveAbility(AbilityType::ASSASSINATE));

    const auto &bonus = rogue.getBonusActionFactoriesConst();
    EXPECT_TRUE(hasFactory(bonus, AbilityType::CUNNING_HIDE));
  }

  // ----------------------------------------------------------------------------------------------------------
  // Hide grants the rogue Advantage on its next attack against the enemy it is hidden from.
  // ----------------------------------------------------------------------------------------------------------
  TEST_F(RogueTest, HiddenRogueAttacksWithAdvantage)
  {
    auto *rogue = new AssassinRogueLvl3(1);
    auto *goblin = new Goblin(1);
    session->addCombatant(rogue, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*rogue, Coord{3, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{4, 3});

    // Register the rogue as Hidden from the goblin (bypassing the random Stealth check to test the wiring
    // deterministically).
    HideFactory hideFactory(rogue, AbilityType::CUNNING_HIDE);
    auto hideActoid = hideFactory.create(static_cast<void *>(goblin));
    auto hideEffect = std::dynamic_pointer_cast<Effect>(hideActoid);
    ASSERT_NE(hideEffect, nullptr);
    EffectTracker::getInstance().add(hideEffect);
    ASSERT_TRUE(EffectTracker::getInstance().isCombatantHiddenFrom(rogue, goblin));

    auto *melee = dynamic_cast<AttackFactory *>(findFactory(rogue->getActionFactoriesConst(), AbilityType::MELEE_ATTACK));
    ASSERT_NE(melee, nullptr);
    auto attack = std::dynamic_pointer_cast<Attack>(melee->create(static_cast<void *>(goblin)));
    ASSERT_NE(attack, nullptr);

    ActionResolver resolver;
    auto types = resolver.collectAttackRollTypes(attack.get(), goblin, rogue);
    EXPECT_EQ(types.count(RollType::ADVANTAGE), 1u);
  }
}
