#include <gtest/gtest.h>
#include "actions/attack.hpp"
#include "combatants/cleric_lvl_1.hpp"
#include "combatants/goblin.hpp"
#include "combatants/ogre.hpp"
#include "core/action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/session.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include "spells/bless.hpp"
#include "spells/guiding_bolt.hpp"
#include "spells/shield_of_faith.hpp"
#include "spells/toll_the_dead.hpp"
#include <algorithm>

using namespace enc;

namespace
{
  class ClericLvl1Test : public ::testing::Test
  {
  protected:
    void SetUp() override
    {
      BattleMap::resetInstance();
      Teams::resetInstance();
      EffectTracker::resetInstance();
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

    static AttackFactory *maceFactory(Combatant *combatant)
    {
      for(const auto &factory : combatant->getActionFactoriesConst())
        {
          if(auto *attack = dynamic_cast<AttackFactory *>(factory.get()))
            {
              if(attack->getMastery() == WeaponMastery::SAP)
                {
                  return attack;
                }
            }
        }
      return nullptr;
    }
  };

  TEST_F(ClericLvl1Test, StatsAndFactoriesFromSheet)
  {
    ClericLvl1 cleric(1);

    EXPECT_EQ(cleric.getMaxHp(), 9);
    EXPECT_EQ(cleric.getAC(), 14);
    EXPECT_EQ(cleric.getSpeed(), 6);
    EXPECT_EQ(cleric.getDC(), 13);
    EXPECT_EQ(cleric.getLevel(), 1);
    EXPECT_EQ(cleric.getSavingThrow(SavingThrow::STR), 2);
    EXPECT_EQ(cleric.getSavingThrow(SavingThrow::DEX), -1);
    EXPECT_EQ(cleric.getSavingThrow(SavingThrow::CON), 1);
    EXPECT_EQ(cleric.getSavingThrow(SavingThrow::INT), 0);
    EXPECT_EQ(cleric.getSavingThrow(SavingThrow::WIS), 5);
    EXPECT_EQ(cleric.getSavingThrow(SavingThrow::CHA), 3);

    EXPECT_EQ(cleric.getSpellslots().getUses(1), 2);
    EXPECT_TRUE(hasFactory(cleric.getActionFactoriesConst(), AbilityType::SACRED_FLAME));
    EXPECT_TRUE(hasFactory(cleric.getActionFactoriesConst(), AbilityType::TOLL_THE_DEAD));
    EXPECT_TRUE(hasFactory(cleric.getActionFactoriesConst(), AbilityType::BLESS));
    EXPECT_TRUE(hasFactory(cleric.getActionFactoriesConst(), AbilityType::CURE_WOUNDS));
    EXPECT_TRUE(hasFactory(cleric.getActionFactoriesConst(), AbilityType::GUIDING_BOLT));
    EXPECT_TRUE(hasFactory(cleric.getBonusActionFactoriesConst(), AbilityType::SHIELD_OF_FAITH));

    AttackFactory *mace = maceFactory(&cleric);
    ASSERT_NE(mace, nullptr);
    EXPECT_EQ(mace->getToHit(), 4);
    EXPECT_EQ(mace->getDmgBonus(), 2);
  }

  TEST_F(ClericLvl1Test, BlessAddsAttackAndSavingThrowDice)
  {
    ClericLvl1 cleric(1);
    auto *factory = findFactory(cleric.getActionFactoriesConst(), AbilityType::BLESS);
    ASSERT_NE(factory, nullptr);

    std::vector<Combatant *> targets{&cleric};
    auto action = factory->create(static_cast<void *>(&targets));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, &cleric), ActionResult::OTHER);

    EXPECT_FALSE(cleric.hasAction());
    EXPECT_EQ(cleric.getSpellslots().getUses(1), 1);
    EXPECT_TRUE(cleric.isConcentrating());
    ASSERT_EQ(cleric.getToHitDiceMods().size(), 1u);
    EXPECT_EQ(cleric.getToHitDiceMods().front()[0], 1);
    EXPECT_EQ(cleric.getToHitDiceMods().front()[1], 4);
    ASSERT_EQ(cleric.getSavingThrowDiceMods(SavingThrow::WIS).size(), 1u);
    EXPECT_EQ(cleric.getSavingThrowDiceMods(SavingThrow::WIS).front()[1], 4);
  }

  TEST_F(ClericLvl1Test, ShieldOfFaithRaisesAcAndConsumesBonusActionSlot)
  {
    ClericLvl1 cleric(1);
    auto *factory = findFactory(cleric.getBonusActionFactoriesConst(), AbilityType::SHIELD_OF_FAITH);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(&cleric));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, &cleric), ActionResult::OTHER);

    EXPECT_EQ(cleric.getAC(), 16);
    EXPECT_TRUE(cleric.hasAction());
    EXPECT_FALSE(cleric.hasBonusAction());
    EXPECT_EQ(cleric.getSpellslots().getUses(1), 1);
    EXPECT_TRUE(cleric.isConcentrating());
  }

  TEST_F(ClericLvl1Test, TollTheDeadUsesD12AgainstWoundedTargets)
  {
    ClericLvl1 cleric(1);
    Goblin target(1);
    auto *factory = findFactory(cleric.getActionFactoriesConst(), AbilityType::TOLL_THE_DEAD);
    ASSERT_NE(factory, nullptr);

    auto fullHpAction = factory->create(static_cast<void *>(&target));
    auto *fullHpToll = dynamic_cast<TollTheDead *>(fullHpAction.get());
    ASSERT_NE(fullHpToll, nullptr);
    EXPECT_EQ(fullHpToll->getDmgDice()[0], 1);
    EXPECT_EQ(fullHpToll->getDmgDice()[1], 8);

    target.setCurrentHp(target.getMaxHp() - 1);
    auto woundedAction = factory->create(static_cast<void *>(&target));
    auto *woundedToll = dynamic_cast<TollTheDead *>(woundedAction.get());
    ASSERT_NE(woundedToll, nullptr);
    EXPECT_EQ(woundedToll->getDmgDice()[0], 1);
    EXPECT_EQ(woundedToll->getDmgDice()[1], 12);
  }

  TEST_F(ClericLvl1Test, GuidingBoltGrantsAndConsumesNextAttackAdvantage)
  {
    auto *cleric = new ClericLvl1(1);
    auto *target = new Ogre(1);
    Session session;
    session.addCombatant(cleric, Color::BLUE);
    session.addCombatant(target, Color::RED);
    BattleMap::getInstance().setCombatantCoordinates(*cleric, Coord{5, 5});
    BattleMap::getInstance().setCombatantCoordinates(*target, Coord{5, 6});
    BattleMap::getInstance().buildBaseAdjacencyMatrix();

    auto effect = std::make_shared<GuidingBoltEffect>(cleric, target);
    EffectTracker::getInstance().add(effect);
    ASSERT_TRUE(EffectTracker::getInstance().isAffectingCombatant(target, EffectType::GUIDING_BOLT));

    AttackFactory *mace = maceFactory(cleric);
    ASSERT_NE(mace, nullptr);
    auto attack = mace->create(static_cast<void *>(target));
    auto *attackPtr = dynamic_cast<Attack *>(attack.get());
    ASSERT_NE(attackPtr, nullptr);

    ActionResolver resolver;
    auto rollTypes = resolver.collectAttackRollTypes(attackPtr, target, cleric);
    EXPECT_TRUE(rollTypes.contains(RollType::ADVANTAGE));

    target->setAC(100);
    resolver.resolveAction(attack, cleric);
    EXPECT_FALSE(EffectTracker::getInstance().isAffectingCombatant(target, EffectType::GUIDING_BOLT));
  }
}
