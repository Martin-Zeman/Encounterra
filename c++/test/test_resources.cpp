#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/spellslots.hpp"
#include "core/resources.hpp"
#include "spells/spell_stats.hpp"
#include "spells/fireball.hpp"
#include "spells/firebolt.hpp"
#include "combatants/goblin.hpp"
#include "combatants/acolyte.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/draconic_sorcerer_lvl_5.hpp"
#include "combatants/moon_druid_lvl_5.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include <memory>
#include <array>

using namespace enc;

namespace {

class ResourceTest : public ::testing::Test
{
protected:
    BattleMap* battleMap;
    Teams* teams;
    Session* session;
    Goblin* goblin;
    Acolyte* acolyte;
    DraconicSorcererLvl1* draconic_sorcerer_lvl_1;
    DraconicSorcererLvl5* draconic_sorcerer_lvl_5;
    MoonDruidLvl5* moon_druid_lvl_5;
    WildHeartBarbarianLvl3* wild_heart_barbarian_lvl_3;

    void SetUp() override
    {
        BattleMap::resetInstance();
        battleMap = &BattleMap::getInstance();
        Teams::resetInstance();
        teams = &Teams::getInstance();
        session = new Session();
        goblin = new Goblin(1);
        acolyte = new Acolyte(1);
        draconic_sorcerer_lvl_1 = new DraconicSorcererLvl1(1);
        draconic_sorcerer_lvl_5 = new DraconicSorcererLvl5(1);
        moon_druid_lvl_5 = new MoonDruidLvl5(1);
        wild_heart_barbarian_lvl_3 = new WildHeartBarbarianLvl3(1);
    }

    void TearDown() override
    {
        delete session;
        delete goblin;
        delete acolyte;
        delete draconic_sorcerer_lvl_1;
        delete draconic_sorcerer_lvl_5;
        delete moon_druid_lvl_5;
        delete wild_heart_barbarian_lvl_3;
    }
};

TEST_F(ResourceTest, CombatantSimpleSpellslotCount)
{
  auto spellslots = draconic_sorcerer_lvl_5->getSpellslots();
  EXPECT_TRUE(spellslots.hasUses(1));
  EXPECT_EQ(spellslots.getUses(1), 4);
  EXPECT_TRUE(spellslots.hasUses(2));
  EXPECT_EQ(spellslots.getUses(2), 3);
  EXPECT_TRUE(spellslots.hasUses(3));
  EXPECT_EQ(spellslots.getUses(3), 2);
  EXPECT_FALSE(spellslots.hasUses(4));
  EXPECT_EQ(spellslots.getUses(4), 0);
}

TEST_F(ResourceTest, MonsterWithRegularSpellslots)
{
  auto spellslots = acolyte->getSpellslots();
  EXPECT_TRUE(spellslots.hasUses(1));
  EXPECT_EQ(spellslots.getUses(1), 3);
  EXPECT_FALSE(spellslots.hasUses(2));
  EXPECT_EQ(spellslots.getUses(2), 0);
}


TEST_F(ResourceTest, UseResourcesSpellslots)
{
    FireboltFactory fireboltFactory(1, AbilityType::FIREBOLT, draconic_sorcerer_lvl_5, &draconic_sorcerer_lvl_5->getSpellslots());
    auto firebolt = fireboltFactory.create(goblin);
    
    FireballFactory fireballFactory(1, AbilityType::FIREBALL, draconic_sorcerer_lvl_5, &draconic_sorcerer_lvl_5->getSpellslots());
    Coord targetCoord({0, 0});
    auto fireball = fireballFactory.create(&targetCoord);

    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(1), 4);

    useResources(draconic_sorcerer_lvl_5, *firebolt);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(1), 4);

    useResources(draconic_sorcerer_lvl_5, *fireball);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(3), 1);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(1), 4);

    useResources(draconic_sorcerer_lvl_5, *fireball);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(3), 0);
    EXPECT_FALSE(draconic_sorcerer_lvl_5->getSpellslots().hasUses(3));
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(1), 4);

    draconic_sorcerer_lvl_5->getSpellslots().reset();
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_5->getSpellslots().getUses(1), 4);
}

// TEST_F(ResourceTest, UseResourcesAlreadyUsedSpellslotThisTurn)
// {
//     teams->addCombatantToTeam(draconic_sorcerer_lvl_1, Color::BLUE);
    
//     FireboltFactory firebolt_factory(1, Action::FIREBOLT, draconic_sorcerer_lvl_1, draconic_sorcerer_lvl_1->getSpellslots());
//     auto firebolt = firebolt_factory.create(goblin);
    
//     FireballFactory fireball_factory(1, Action::FIREBALL, draconic_sorcerer_lvl_1, draconic_sorcerer_lvl_1->getSpellslots());
//     auto fireball = fireball_factory.create(std::array<int, 2>{0, 0});

//     EXPECT_FALSE(draconic_sorcerer_lvl_1->alreadyUsedSpellslotThisTurn());
//     useResources(draconic_sorcerer_lvl_1, firebolt.get());
//     EXPECT_FALSE(draconic_sorcerer_lvl_1->alreadyUsedSpellslotThisTurn());
//     useResources(draconic_sorcerer_lvl_1, fireball.get());
//     EXPECT_TRUE(draconic_sorcerer_lvl_1->alreadyUsedSpellslotThisTurn());
// }

// TEST_F(ResourceTest, DepleteResourceSpellslots)
// {
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(3), 2);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(2), 3);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(1), 4);

//     draconic_sorcerer_lvl_1->getSpellslots()->depleteResource(ResourceDepletionLevel::PARTIALLY_DEPLETED);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(3), 1);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(2), 1);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(1), 2);

//     draconic_sorcerer_lvl_1->getSpellslots()->depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(3), 0);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(2), 0);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(1), 0);

//     draconic_sorcerer_lvl_1->getSpellslots()->depleteResource(ResourceDepletionLevel::PARTIALLY_DEPLETED);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(3), 1);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(2), 1);
//     EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getUses(1), 2);
// }

// TEST_F(ResourceTest, DepleteResourceUses)
// {
//     auto& rage_resource = wild_heart_barbarian_lvl_3->getResources()[BonusAction::TOTEM_RAGE];

//     EXPECT_TRUE(rage_resource->hasUses1));
//     EXPECT_EQ(rage_resource->getUses(1), 3);

//     rage_resource->useResource(1);
//     EXPECT_EQ(rage_resource->getUses(1), 2);

//     rage_resource->useResource(1);
//     EXPECT_EQ(rage_resource->getUses(1), 1);

//     rage_resource->useResource(1);
//     EXPECT_EQ(rage_resource->getUses(1), 0);
//     EXPECT_FALSE(rage_resource->hasUses1));

//     rage_resource->depleteResource(ResourceDepletionLevel::PARTIALLY_DEPLETED);
//     EXPECT_EQ(rage_resource->getUses(1), 1);

//     rage_resource->depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);
//     EXPECT_EQ(rage_resource->getUses(1), 0);
//     EXPECT_FALSE(rage_resource->hasUses1));
// }

// TEST_F(ResourceTest, DepleteResourcesUsesOnCombatant)
// {
//     auto& barbarian_rage = wild_heart_barbarian_lvl_3->getResources()[BonusAction::TOTEM_RAGE];
//     auto& druid_wildshape = moon_druid_lvl_5->getResources()[Action::WILDSHAPE];
//     auto& sorcerer_metamagic = draconic_sorcerer_lvl_1->getResources()[Passive::METAMAGIC];

//     EXPECT_TRUE(barbarian_rage->hasUses1));
//     EXPECT_EQ(barbarian_rage->getUses(1), 3);
//     wild_heart_barbarian_lvl_3->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED);
//     EXPECT_EQ(barbarian_rage->getUses(1), 1);
//     wild_heart_barbarian_lvl_3->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED);
//     EXPECT_EQ(barbarian_rage->getUses(1), 0);
//     EXPECT_FALSE(barbarian_rage->hasUses1));

//     EXPECT_TRUE(druid_wildshape->hasUses1));
//     EXPECT_EQ(druid_wildshape->getUses(1), 2);
//     moon_druid_lvl_5->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED);
//     EXPECT_EQ(druid_wildshape->getUses(1), 1);
//     moon_druid_lvl_5->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED);
//     EXPECT_EQ(druid_wildshape->getUses(1), 0);
//     EXPECT_FALSE(druid_wildshape->hasUses1));

//     EXPECT_TRUE(sorcerer_metamagic->hasUses1));
//     EXPECT_EQ(sorcerer_metamagic->getUses(1), 5);
//     draconic_sorcerer_lvl_1->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED);
//     EXPECT_EQ(sorcerer_metamagic->getUses(1), 2);
//     draconic_sorcerer_lvl_1->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED);
//     EXPECT_EQ(sorcerer_metamagic->getUses(1), 0);
//     EXPECT_FALSE(sorcerer_metamagic->hasUses1));
// }

// TEST_F(ResourceTest, DepleteResourcesOnCombatantWithNoResources)
// {
//     EXPECT_NO_THROW(goblin->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED));
//     EXPECT_NO_THROW(goblin->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED));
// }

// TEST_F(ResourceTest, ResourceDepletionOnSession)
// {
//     session->addCombatant(DraconicSorcererLvl1::id, Color::BLUE, ResourceDepletionLevel::FULLY_DEPLETED);
//     session->addCombatant(MoonDruidLvl5::id, Color::RED, ResourceDepletionLevel::PARTIALLY_DEPLETED);

//     EXPECT_EQ(session->getCombatants()[0]->getSpellslots()->getUses3), 0);
//     EXPECT_EQ(session->getCombatants()[0]->getSpellslots()->getUses2), 0);
//     EXPECT_EQ(session->getCombatants()[0]->getSpellslots()->getUses1), 0);
//     EXPECT_FALSE(session->getCombatants()[0]->getResources()[Passive::METAMAGIC]->hasUses1));
//     EXPECT_EQ(session->getCombatants()[1]->getResources()[Action::WILDSHAPE]->getUses1), 1);
// }


} // namespace