#include <gtest/gtest.h>
#include "actions/attack.hpp"
#include "combatants/bard_college_of_lore_lvl_3.hpp"
#include "combatants/goblin.hpp"
#include "combatants/ogre.hpp"
#include "core/action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/session.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>

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
    }

    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    static bool hasFactory(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
    {
      return std::any_of(factories.begin(), factories.end(),
                         [type](const std::shared_ptr<ActoidFactory> &factory) { return factory->getAbilityType() == type; });
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
}
