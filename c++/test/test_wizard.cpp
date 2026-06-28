#include <gtest/gtest.h>
#include "core/action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/misc.hpp"
#include "core/session.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/goblin.hpp"
#include "combatants/wizard_lvl_1.hpp"
#include "spells/mage_armor.hpp"
#include "spells/magic_missile.hpp"
#include "spells/sleep.hpp"
#include <algorithm>
#include <array>

using namespace enc;

namespace
{
  class WizardLvl1Test : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    WizardLvl1 *wizard;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      wizard = new WizardLvl1(1);
      goblin = new Goblin(1);
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

    void placeCombatants()
    {
      session->addCombatant(wizard, Color::BLUE);
      session->addCombatant(goblin, Color::RED);
      battleMap->buildBaseAdjacencyMatrix();
      battleMap->setCombatantCoordinates(*wizard, Coord{1, 3});
      battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});
    }
  };

  TEST_F(WizardLvl1Test, BaseStatsFromSheet)
  {
    EXPECT_EQ(wizard->getMaxHp(), 7);
    EXPECT_EQ(wizard->getAC(), 11);
    EXPECT_EQ(wizard->getDC(), 13);
    EXPECT_EQ(wizard->getLevel(), 1);
    EXPECT_EQ(wizard->getSpeed(), 6);
    EXPECT_EQ(wizard->getSavingThrow(SavingThrow::STR), -1);
    EXPECT_EQ(wizard->getSavingThrow(SavingThrow::DEX), 1);
    EXPECT_EQ(wizard->getSavingThrow(SavingThrow::CON), 1);
    EXPECT_EQ(wizard->getSavingThrow(SavingThrow::INT), 5);
    EXPECT_EQ(wizard->getSavingThrow(SavingThrow::WIS), 4);
    EXPECT_EQ(wizard->getSavingThrow(SavingThrow::CHA), 0);
  }

  TEST_F(WizardLvl1Test, FactoriesAndSpellSlotsPresent)
  {
    const auto &actions = wizard->getActionFactoriesConst();
    EXPECT_TRUE(hasFactory(actions, AbilityType::MAGE_ARMOR));
    EXPECT_TRUE(hasFactory(actions, AbilityType::MAGIC_MISSILE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::SLEEP));
    EXPECT_TRUE(hasFactory(actions, AbilityType::RAY_OF_FROST));
    EXPECT_EQ(wizard->getSpellslots().getUses(1), 2);
  }

  TEST_F(WizardLvl1Test, MageArmorRaisesWizardAc)
  {
    placeCombatants();
    auto *factory = findFactory(wizard->getActionFactoriesConst(), AbilityType::MAGE_ARMOR);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(wizard));

    ActionResolver resolver;
    EXPECT_EQ(wizard->getAC(), 11);
    EXPECT_EQ(resolver.resolveAction(action, wizard), ActionResult::OTHER);
    EXPECT_EQ(wizard->getAC(), 14);
    EXPECT_EQ(wizard->getSpellslots().getUses(1), 1);
  }

  TEST_F(WizardLvl1Test, MagicMissileThreatAndSlotUse)
  {
    placeCombatants();
    auto *factory = findFactory(wizard->getActionFactoriesConst(), AbilityType::MAGIC_MISSILE);
    ASSERT_NE(factory, nullptr);
    auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(threatFactory, nullptr);
    EXPECT_DOUBLE_EQ(threatFactory->calculateThreatToTarget(goblin, {}), 7.0);
    goblin->setAC(30);
    EXPECT_DOUBLE_EQ(threatFactory->calculateThreatToTarget(goblin, {}), 7.0);

    std::array<Combatant *, 3> targets{goblin, goblin, goblin};
    auto action = factory->create(static_cast<void *>(&targets));
    useResources(wizard, *action);
    EXPECT_TRUE(wizard->hasAlreadyUsedSpellslotThisTurn());
    EXPECT_EQ(wizard->getSpellslots().getUses(1), 1);
  }

  TEST_F(WizardLvl1Test, SleepCanIncapacitateOnFailedSave)
  {
    placeCombatants();
    seedThreadRNG(4);
    goblin->addSavingThrowRollTypeMod(SavingThrow::WIS, RollType::DISADVANTAGE);
    SleepFactory sleepFactory(30, AbilityType::SLEEP, wizard, &wizard->getSpellslots());
    Coord targetCoord = battleMap->getCombatantCoordinates(*goblin).getRoot();
    auto action = sleepFactory.create(static_cast<void *>(&targetCoord));

    ActionResolver resolver;
    EXPECT_EQ(resolver.resolveAction(action, wizard), ActionResult::OTHER);
    EXPECT_TRUE(goblin->isAffectedBy(Conditions::INCAPACITATED));
    EXPECT_TRUE(wizard->isConcentrating());
    EXPECT_EQ(wizard->getSpellslots().getUses(1), 1);

    goblin->receiveDmg(1, DamageType::Slashing);
    EXPECT_FALSE(goblin->isAffectedBy(Conditions::INCAPACITATED));
    EXPECT_FALSE(goblin->isAffectedBy(Conditions::UNCONSCIOUS));
    EXPECT_FALSE(wizard->isConcentrating());
  }
}
