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
// #include "spells/fireball.hpp"
// #include "spells/firebolt.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
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
    DraconicSorcererLvl1* draconic_sorcerer_lvl_1;
    MoonDruidLvl5* Colormoon_druid_lvl_5;
    WildHeartBarbarianLvl3* wild_heart_barbarian_lvl_3;

    void SetUp() override
    {
        BattleMap::resetInstance();
        battleMap = &BattleMap::getInstance();
        Teams::resetInstance();
        teams = &Teams::getInstance();
        session = new Session();
        goblin = new Goblin(1);
        draconic_sorcerer_lvl_1 = new DraconicSorcererLvl1(1);
        Colormoon_druid_lvl_5 = new MoonDruidLvl5(1);
        wild_heart_barbarian_lvl_3 = new WildHeartBarbarianLvl3(1);
    }

    void TearDown() override
    {
        delete session;
        delete goblin;
        delete draconic_sorcerer_lvl_1;
        delete Colormoon_druid_lvl_5;
        delete wild_heart_barbarian_lvl_3;
    }
};

TEST_F(ResourceTest, UseResourcesSpellslots)
{
    teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
    
    FireboltFactory firebolt_factory(1, Action::FIREBOLT, draconic_sorcerer_lvl_1, draconic_sorcerer_lvl_1->getSpellslots());
    auto firebolt = firebolt_factory.create(goblin);
    
    FireballFactory fireball_factory(1, Action::FIREBALL, draconic_sorcerer_lvl_1, draconic_sorcerer_lvl_1->getSpellslots());
    auto fireball = fireball_factory.create(std::array<int, 2>{0, 0});

    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 4);

    useResources(draconic_sorcerer_lvl_1, firebolt.get());
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 4);

    useResources(draconic_sorcerer_lvl_1, fireball.get());
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 1);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 4);

    useResources(draconic_sorcerer_lvl_1, fireball.get());
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 0);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 4);

    draconic_sorcerer_lvl_1->getSpellslots()->reset();
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 4);
}

TEST_F(ResourceTest, UseResourcesAlreadyUsedSpellslotThisTurn)
{
    teams->addCombatantToTeam(draconic_sorcerer_lvl_1, Color::BLUE);
    
    FireboltFactory firebolt_factory(1, Action::FIREBOLT, draconic_sorcerer_lvl_1, draconic_sorcerer_lvl_1->getSpellslots());
    auto firebolt = firebolt_factory.create(goblin);
    
    FireballFactory fireball_factory(1, Action::FIREBALL, draconic_sorcerer_lvl_1, draconic_sorcerer_lvl_1->getSpellslots());
    auto fireball = fireball_factory.create(std::array<int, 2>{0, 0});

    EXPECT_FALSE(draconic_sorcerer_lvl_1->alreadyUsedSpellslotThisTurn());
    useResources(draconic_sorcerer_lvl_1, firebolt.get());
    EXPECT_FALSE(draconic_sorcerer_lvl_1->alreadyUsedSpellslotThisTurn());
    useResources(draconic_sorcerer_lvl_1, fireball.get());
    EXPECT_TRUE(draconic_sorcerer_lvl_1->alreadyUsedSpellslotThisTurn());
}

TEST_F(ResourceTest, DepleteResourceSpellslots)
{
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 2);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 3);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 4);

    draconic_sorcerer_lvl_1->getSpellslots()->depleteResource(ResourceDepletionLevel::PARTIALLY_DEPLETED);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 1);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 1);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 2);

    draconic_sorcerer_lvl_1->getSpellslots()->depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 0);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 0);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 0);

    draconic_sorcerer_lvl_1->getSpellslots()->depleteResource(ResourceDepletionLevel::PARTIALLY_DEPLETED);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(3), 1);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(2), 1);
    EXPECT_EQ(draconic_sorcerer_lvl_1->getSpellslots()->getResource(1), 2);
}

TEST_F(ResourceTest, DepleteResourceUses)
{
    auto& rage_resource = wild_heart_barbarian_lvl_3->getResources()[BonusAction::TOTEM_RAGE];

    EXPECT_TRUE(rage_resource->hasResource(1));
    EXPECT_EQ(rage_resource->getResource(1), 3);

    rage_resource->useResource(1);
    EXPECT_EQ(rage_resource->getResource(1), 2);

    rage_resource->useResource(1);
    EXPECT_EQ(rage_resource->getResource(1), 1);

    rage_resource->useResource(1);
    EXPECT_EQ(rage_resource->getResource(1), 0);
    EXPECT_FALSE(rage_resource->hasResource(1));

    rage_resource->depleteResource(ResourceDepletionLevel::PARTIALLY_DEPLETED);
    EXPECT_EQ(rage_resource->getResource(1), 1);

    rage_resource->depleteResource(ResourceDepletionLevel::FULLY_DEPLETED);
    EXPECT_EQ(rage_resource->getResource(1), 0);
    EXPECT_FALSE(rage_resource->hasResource(1));
}

TEST_F(ResourceTest, DepleteResourcesUsesOnCombatant)
{
    auto& barbarian_rage = wild_heart_barbarian_lvl_3->getResources()[BonusAction::TOTEM_RAGE];
    auto& druid_wildshape = Colormoon_druid_lvl_5->getResources()[Action::WILDSHAPE];
    auto& sorcerer_metamagic = draconic_sorcerer_lvl_1->getResources()[Passive::METAMAGIC];

    EXPECT_TRUE(barbarian_rage->hasResource(1));
    EXPECT_EQ(barbarian_rage->getResource(1), 3);
    wild_heart_barbarian_lvl_3->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED);
    EXPECT_EQ(barbarian_rage->getResource(1), 1);
    wild_heart_barbarian_lvl_3->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED);
    EXPECT_EQ(barbarian_rage->getResource(1), 0);
    EXPECT_FALSE(barbarian_rage->hasResource(1));

    EXPECT_TRUE(druid_wildshape->hasResource(1));
    EXPECT_EQ(druid_wildshape->getResource(1), 2);
    Colormoon_druid_lvl_5->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED);
    EXPECT_EQ(druid_wildshape->getResource(1), 1);
    Colormoon_druid_lvl_5->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED);
    EXPECT_EQ(druid_wildshape->getResource(1), 0);
    EXPECT_FALSE(druid_wildshape->hasResource(1));

    EXPECT_TRUE(sorcerer_metamagic->hasResource(1));
    EXPECT_EQ(sorcerer_metamagic->getResource(1), 5);
    draconic_sorcerer_lvl_1->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED);
    EXPECT_EQ(sorcerer_metamagic->getResource(1), 2);
    draconic_sorcerer_lvl_1->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED);
    EXPECT_EQ(sorcerer_metamagic->getResource(1), 0);
    EXPECT_FALSE(sorcerer_metamagic->hasResource(1));
}

TEST_F(ResourceTest, DepleteResourcesOnCombatantWithNoResources)
{
    EXPECT_NO_THROW(goblin->depleteResources(ResourceDepletionLevel::PARTIALLY_DEPLETED));
    EXPECT_NO_THROW(goblin->depleteResources(ResourceDepletionLevel::FULLY_DEPLETED));
}

TEST_F(ResourceTest, ResourceDepletionOnSession)
{
    session->addCombatant(DraconicSorcererLvl1::id, Color::BLUE, ResourceDepletionLevel::FULLY_DEPLETED);
    session->addCombatant(MoonDruidLvl5::id, Color::RED, ResourceDepletionLevel::PARTIALLY_DEPLETED);

    EXPECT_EQ(session->getCombatants()[0]->getSpellslots()->getResource(3), 0);
    EXPECT_EQ(session->getCombatants()[0]->getSpellslots()->getResource(2), 0);
    EXPECT_EQ(session->getCombatants()[0]->getSpellslots()->getResource(1), 0);
    EXPECT_FALSE(session->getCombatants()[0]->getResources()[Passive::METAMAGIC]->hasResource(1));
    EXPECT_EQ(session->getCombatants()[1]->getResources()[Action::WILDSHAPE]->getResource(1), 1);
}

} // namespace