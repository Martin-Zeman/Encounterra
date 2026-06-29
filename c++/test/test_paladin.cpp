#include <gtest/gtest.h>
#include "actions/attack.hpp"
#include "actions/action_selection.hpp"
#include "actions/action_types.hpp"
#include "abilities/lay_on_hands.hpp"
#include "abilities/on_hit_divine_smite.hpp"
#include "abilities/vow_of_enmity.hpp"
#include "combatants/ogre.hpp"
#include "combatants/paladin_lvl_1.hpp"
#include "combatants/paladin_lvl_2.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_3.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_4.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_5.hpp"
#include "core/action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/conditions.hpp"
#include "core/resources.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <memory>

using namespace enc;

namespace
{
  class PaladinTest : public ::testing::Test
  {
  protected:
    void SetUp() override
    {
      BattleMap::resetInstance();
      Teams::resetInstance();
      EffectTracker::resetInstance();
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

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

    static std::shared_ptr<LayOnHandsFactory> layOnHandsFactory(Combatant *c)
    {
      for(const auto &factory : c->getBonusActionFactoriesConst())
        {
          if(auto lay = std::dynamic_pointer_cast<LayOnHandsFactory>(factory))
            {
              return lay;
            }
        }
      return nullptr;
    }

    static std::shared_ptr<VowOfEnmityFactory> vowFactory(Combatant *c)
    {
      for(const auto &factory : c->getBonusActionFactoriesConst())
        {
          if(auto vow = std::dynamic_pointer_cast<VowOfEnmityFactory>(factory))
            {
              return vow;
            }
        }
      return nullptr;
    }

    static std::shared_ptr<ActoidFactory> smiteAttackFactory(Combatant *c)
    {
      for(const auto &factory : c->getActionFactoriesConst())
        {
          if(factory->getAbilityType() == AbilityType::SMITE_MELEE_ATTACK)
            {
              return factory;
            }
        }
      return nullptr;
    }

    std::deque<std::shared_ptr<Actoid>> planFor(Combatant *combatant)
    {
      auto [distances, shortestPaths] = BattleMap::getInstance().calcDijkstra(*combatant);
      combatant->setShortestPathsCache(shortestPaths);
      return combatant->calculateActionPlan(distances, shortestPaths);
    }
  };

  TEST_F(PaladinTest, LevelOneHasSpellcastingLayOnHandsAndWeaponMastery)
  {
    PaladinLvl1 paladin(1);

    EXPECT_EQ(paladin.getSpellslots().getUses(1), 2);
    auto lay = layOnHandsFactory(&paladin);
    ASSERT_NE(lay, nullptr);
    ASSERT_TRUE(lay->getResource().has_value());
    EXPECT_EQ(lay->getResource().value()->getUses(), 5);

    AttackFactory *battleaxe = weaponWithMastery(&paladin, WeaponMastery::TOPPLE);
    AttackFactory *javelin = weaponWithMastery(&paladin, WeaponMastery::SLOW);
    ASSERT_NE(battleaxe, nullptr);
    ASSERT_NE(javelin, nullptr);
    EXPECT_EQ(javelin->getResource().value()->getUses(), 4);
  }

  TEST_F(PaladinTest, LayOnHandsIsBonusActionAndSpendsPool)
  {
    PaladinLvl1 paladin(1);
    auto lay = layOnHandsFactory(&paladin);
    ASSERT_NE(lay, nullptr);

    paladin.setCurrentHp(1);
    auto actoid = lay->create(static_cast<void *>(&paladin));
    ASSERT_NE(actoid, nullptr);

    ActionResolver resolver;
    resolver.resolveAction(actoid, &paladin);

    EXPECT_EQ(paladin.getCurrentHp(), 6);
    EXPECT_TRUE(paladin.hasAction());
    EXPECT_FALSE(paladin.hasBonusAction());
    EXPECT_EQ(lay->getResource().value()->getUses(), 0);
  }

  TEST_F(PaladinTest, LayOnHandsCanRemovePoisoned)
  {
    PaladinLvl1 paladin(1);
    auto lay = layOnHandsFactory(&paladin);
    ASSERT_NE(lay, nullptr);

    paladin.applyCondition(Condition(Conditions::POISONED, &paladin));
    ASSERT_TRUE(paladin.isAffectedBy(Conditions::POISONED));

    auto actoid = lay->createPoisonRemoval(&paladin);
    ActionResolver resolver;
    resolver.resolveAction(actoid, &paladin);

    EXPECT_FALSE(paladin.isAffectedBy(Conditions::POISONED));
    EXPECT_EQ(lay->getResource().value()->getUses(), 0);
  }

  TEST_F(PaladinTest, LevelTwoAddsDuelingAndDivineSmite)
  {
    PaladinLvl2 paladin(1);
    EXPECT_TRUE(paladin.hasPassiveAbility(AbilityType::DUELING));
    EXPECT_TRUE(paladin.hasPassiveAbility(AbilityType::DIVINE_SMITE));
    ASSERT_TRUE(paladin.getResource(AbilityType::DIVINE_SMITE).has_value());
    EXPECT_EQ(paladin.getResource(AbilityType::DIVINE_SMITE).value()->getUses(), 1);
    EXPECT_NE(smiteAttackFactory(&paladin), nullptr);

    AttackFactory *battleaxe = weaponWithMastery(&paladin, WeaponMastery::TOPPLE);
    ASSERT_NE(battleaxe, nullptr);
    EXPECT_EQ(battleaxe->getDmgBonus(), 5);
    EXPECT_EQ(battleaxe->getOnHits().size(), 1u); // Topple mastery; Divine Smite lives on the smite attack variant.
  }

  TEST_F(PaladinTest, DivineSmiteAttackConsumesActionBonusAndUsesFreeCastOnHit)
  {
    PaladinLvl2 paladin(1);
    Ogre target(1);
    target.setCurrentHp(100);
    auto smiteFactory = smiteAttackFactory(&paladin);
    ASSERT_NE(smiteFactory, nullptr);

    // Spending the smite attack consumes both the Action and the Bonus Action.
    auto smiteActoid = smiteFactory->create(static_cast<void *>(&target));
    useResources(&paladin, *smiteActoid);
    EXPECT_FALSE(paladin.hasAction());
    EXPECT_FALSE(paladin.hasBonusAction());

    // The on-hit rider spends the once-per-rest free cast first, leaving spell slots intact.
    auto beforeSlots = paladin.getSpellslots().getUses(1);
    OnHitDivineSmite rider;
    auto damage = rider.hit(&paladin, nullptr, &target, 1, 0);
    EXPECT_FALSE(damage.empty());
    EXPECT_EQ(paladin.getResource(AbilityType::DIVINE_SMITE).value()->getUses(), 0);
    EXPECT_EQ(paladin.getSpellslots().getUses(1), beforeSlots);
  }

  TEST_F(PaladinTest, DivineSmiteSpendsSpellSlotAfterFreeCast)
  {
    PaladinLvl2 paladin(1);
    Ogre target(1);
    target.setAC(-100);
    target.setCurrentHp(100);
    paladin.getResource(AbilityType::DIVINE_SMITE).value()->useResource();

    auto beforeSlots = paladin.getSpellslots().getUses(1);
    OnHitDivineSmite rider;
    auto damage = rider.hit(&paladin, nullptr, &target, 1, 0);

    EXPECT_FALSE(damage.empty());
    EXPECT_EQ(paladin.getSpellslots().getUses(1), beforeSlots - 1);
  }

  TEST_F(PaladinTest, OathOfVengeanceHasTwoChannelDivinityUsesAndVow)
  {
    OathOfVengeancePaladinLvl3 paladin(1);
    auto vow = vowFactory(&paladin);
    ASSERT_NE(vow, nullptr);
    ASSERT_TRUE(vow->getResource().has_value());
    EXPECT_EQ(vow->getResource().value()->getUses(), 2);
    EXPECT_TRUE(paladin.hasPassiveAbility(AbilityType::CHANNEL_DIVINITY));
  }

  TEST_F(PaladinTest, VowOfEnmityConsumesChannelDivinityAndGrantsAdvantage)
  {
    OathOfVengeancePaladinLvl3 paladin(1);
    Ogre target(1);
    auto vow = vowFactory(&paladin);
    ASSERT_NE(vow, nullptr);

    auto vowActoid = vow->create(static_cast<void *>(&target));
    ActionResolver resolver;
    resolver.resolveAction(vowActoid, &paladin);

    EXPECT_EQ(vow->getResource().value()->getUses(), 1);
    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(&target, EffectType::VOW_OF_ENMITY));

    AttackFactory *battleaxe = weaponWithMastery(&paladin, WeaponMastery::TOPPLE);
    ASSERT_NE(battleaxe, nullptr);
    auto attack = battleaxe->create(static_cast<void *>(&target));
    auto *attackPtr = dynamic_cast<Attack *>(attack.get());
    ASSERT_NE(attackPtr, nullptr);
    auto rollTypes = resolver.collectAttackRollTypes(attackPtr, &target, &paladin);
    EXPECT_TRUE(rollTypes.contains(RollType::ADVANTAGE));
  }

  TEST_F(PaladinTest, PlannedCombatUsesDivineSmiteOnAHit)
  {
    bool sawSmiteUsed = false;
    for(int attempt = 0; attempt < 80 && !sawSmiteUsed; ++attempt)
      {
        BattleMap::resetInstance();
        Teams::resetInstance();
        EffectTracker::resetInstance();

        PaladinLvl2 paladin(1);
        Ogre target(1);
        paladin.setHasBonusAction(true);
        target.setAC(-100);
        target.setCurrentHp(100);

        Teams::getInstance().addCombatantToTeam(paladin, Color::BLUE);
        Teams::getInstance().addCombatantToTeam(target, Color::RED);
        BattleMap::getInstance().setCombatantCoordinates(paladin, Coord{5, 5});
        BattleMap::getInstance().setCombatantCoordinates(target, Coord{5, 6});
        BattleMap::getInstance().buildBaseAdjacencyMatrix();

        auto plan = planFor(&paladin);
        auto smiteIt = std::find_if(plan.begin(), plan.end(), [](const std::shared_ptr<Actoid> &a) {
          return a->getAbilityType() == AbilityType::SMITE_MELEE_ATTACK;
        });
        ASSERT_NE(smiteIt, plan.end()) << "The planner should choose a smite attack variant";

        ActionResolver resolver;
        const int freeSmitesBefore = paladin.getResource(AbilityType::DIVINE_SMITE).value()->getUses();
        paladin.setActionPlan(plan);
        while(auto actoid = getAction(&paladin))
          {
            resolver.resolveAction(actoid, &paladin);
            if(paladin.getResource(AbilityType::DIVINE_SMITE).value()->getUses() < freeSmitesBefore)
              {
                sawSmiteUsed = true;
                break;
              }
          }
      }
    EXPECT_TRUE(sawSmiteUsed) << "With AC forced very low, a planned smite attack should consume Divine Smite";
  }

  TEST_F(PaladinTest, NormalMeleeAttackDoesNotSpendDivineSmite)
  {
    bool sawUnmarkedHit = false;
    for(int attempt = 0; attempt < 80 && !sawUnmarkedHit; ++attempt)
      {
        BattleMap::resetInstance();
        Teams::resetInstance();
        EffectTracker::resetInstance();

        PaladinLvl2 paladin(1);
        Ogre target(1);
        target.setAC(-100);
        target.setCurrentHp(100);

        Teams::getInstance().addCombatantToTeam(paladin, Color::BLUE);
        Teams::getInstance().addCombatantToTeam(target, Color::RED);
        BattleMap::getInstance().setCombatantCoordinates(paladin, Coord{5, 5});
        BattleMap::getInstance().setCombatantCoordinates(target, Coord{5, 6});

        AttackFactory *battleaxe = weaponWithMastery(&paladin, WeaponMastery::TOPPLE);
        ASSERT_NE(battleaxe, nullptr);
        const int freeSmitesBefore = paladin.getResource(AbilityType::DIVINE_SMITE).value()->getUses();

        ActionResolver resolver;
        auto attack = battleaxe->create(static_cast<void *>(&target));
        ActionResult result = resolver.resolveAction(attack, &paladin);
        EXPECT_EQ(paladin.getResource(AbilityType::DIVINE_SMITE).value()->getUses(), freeSmitesBefore);
        if(result == ActionResult::HIT)
          {
            sawUnmarkedHit = true;
          }
      }
    EXPECT_TRUE(sawUnmarkedHit) << "With AC forced very low, at least one base attack should hit without spending Divine Smite";
  }

  TEST_F(PaladinTest, LevelFiveAddsOathSpellsAndExtraAttack)
  {
    OathOfVengeancePaladinLvl5 paladin(1);
    EXPECT_EQ(paladin.getSpellslots().getUses(1), 4);
    EXPECT_EQ(paladin.getSpellslots().getUses(2), 2);

    bool hasHoldPerson = false;
    bool hasMistyStep = false;
    for(const auto &factory : paladin.getActionFactoriesConst())
      {
        hasHoldPerson |= factory->getAbilityType() == AbilityType::HOLD_PERSON;
      }
    for(const auto &factory : paladin.getBonusActionFactoriesConst())
      {
        hasMistyStep |= factory->getAbilityType() == AbilityType::MISTY_STEP;
      }
    EXPECT_TRUE(hasHoldPerson);
    EXPECT_TRUE(hasMistyStep);

    AttackFactory *battleaxe = weaponWithMastery(&paladin, WeaponMastery::TOPPLE);
    AttackFactory *javelin = weaponWithMastery(&paladin, WeaponMastery::SLOW);
    ASSERT_NE(battleaxe, nullptr);
    ASSERT_NE(javelin, nullptr);

    EXPECT_TRUE(paladin.isAttackFsmAtStart());
    paladin.triggerAttackFsm(battleaxe);
    EXPECT_TRUE(paladin.attackFsmHasTransition(battleaxe));
    EXPECT_FALSE(paladin.attackFsmHasTransition(javelin));
  }
}
