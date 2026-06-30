#include <gtest/gtest.h>
#include "core/action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/misc.hpp"
#include "core/session.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include "combatants/goblin.hpp"
#include "combatants/night_hag.hpp"
#include "combatants/warlock_lvl_1.hpp"
#include "combatants/warlock_lvl_2.hpp"
#include "combatants/warlock_lvl_3.hpp"
#include "combatants/warlock_lvl_4.hpp"
#include "combatants/warlock_lvl_5.hpp"
#include "spells/eldritch_blast.hpp"
#include "spells/hex.hpp"
#include "spells/armor_of_agathys.hpp"
#include "spells/darkness.hpp"
#include "spells/hypnotic_pattern.hpp"
#include "spells/blink.hpp"
#include "core/conditions.hpp"
#include "core/resources.hpp"
#include "core/spellslots.hpp"
#include <algorithm>

using namespace enc;

namespace
{
  class WarlockLvl1Test : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    WarlockLvl1 *warlock;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      warlock = new WarlockLvl1(1);
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
      session->addCombatant(warlock, Color::BLUE);
      session->addCombatant(goblin, Color::RED);
      battleMap->buildBaseAdjacencyMatrix();
      battleMap->setCombatantCoordinates(*warlock, Coord{1, 3});
      battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});
    }
  };

  TEST_F(WarlockLvl1Test, BaseStatsFromSheet)
  {
    EXPECT_EQ(warlock->getMaxHp(), 10);
    // Armor of Shadows (Mage Armor base 13 + DEX 0) is assumed already cast going into the fight, so the
    // warlock starts at AC 13 rather than the unarmored 10.
    EXPECT_EQ(warlock->getAC(), 13);
    EXPECT_EQ(warlock->getDC(), 13);
    EXPECT_EQ(warlock->getLevel(), 1);
    EXPECT_EQ(warlock->getSpeed(), 6);
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::STR), -1);
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::DEX), 0);
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::CON), 2);
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::INT), 1);
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::WIS), 4);
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::CHA), 5);
  }

  TEST_F(WarlockLvl1Test, ArmorOfShadowsEffectActiveAtConstruction)
  {
    // The invocation must leave a persistent effect on the warlock (not just bump the AC number).
    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(warlock, EffectType::MAGE_ARMOR));
    EXPECT_EQ(warlock->getAC(), 13);
  }

  TEST_F(WarlockLvl1Test, FactoriesAndPactSlotPresent)
  {
    const auto &actions = warlock->getActionFactoriesConst();
    EXPECT_TRUE(hasFactory(actions, AbilityType::ELDRITCH_BLAST));
    EXPECT_TRUE(hasFactory(actions, AbilityType::ARMOR_OF_SHADOWS));
    EXPECT_TRUE(hasFactory(actions, AbilityType::BANE));
    EXPECT_TRUE(hasFactory(actions, AbilityType::CHARM_PERSON));

    const auto &bonus = warlock->getBonusActionFactoriesConst();
    EXPECT_TRUE(hasFactory(bonus, AbilityType::HEX));

    // Pact magic: a single 1st-level slot.
    EXPECT_EQ(warlock->getSpellslots().getUses(1), 1);
  }

  TEST_F(WarlockLvl1Test, EldritchBlastIsSingleForceBeamAtLevelOne)
  {
    placeCombatants();
    auto *factory = findFactory(warlock->getActionFactoriesConst(), AbilityType::ELDRITCH_BLAST);
    ASSERT_NE(factory, nullptr);
    auto *directThreat = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(directThreat, nullptr);

    EXPECT_EQ(EldritchBlastFactory::getNumBeams(1), 1);
    EXPECT_EQ(EldritchBlastFactory::getNumBeams(5), 2);
    EXPECT_EQ(EldritchBlastFactory::getNumBeams(11), 3);
    EXPECT_EQ(EldritchBlastFactory::getNumBeams(17), 4);
    EXPECT_EQ(EldritchBlastFactory::dmgType, DamageType::Force);

    auto actoid = factory->create(static_cast<void *>(goblin));
    auto *eldritchBlast = dynamic_cast<EldritchBlast *>(actoid.get());
    ASSERT_NE(eldritchBlast, nullptr);
    EXPECT_EQ(eldritchBlast->getNumBeams(), 1);

    EXPECT_GT(directThreat->calculateThreatToTarget(goblin, {}), 0.0);
  }

  TEST_F(WarlockLvl1Test, EldritchBlastDoesNotConsumeSpellSlot)
  {
    placeCombatants();
    auto *factory = findFactory(warlock->getActionFactoriesConst(), AbilityType::ELDRITCH_BLAST);
    ASSERT_NE(factory, nullptr);
    auto action = factory->create(static_cast<void *>(goblin));

    ActionResolver resolver;
    const int slotsBefore = warlock->getSpellslots().getUses(1);
    resolver.resolveAction(action, warlock);
    // Eldritch Blast is a cantrip: it must never burn the warlock's single pact slot.
    EXPECT_EQ(warlock->getSpellslots().getUses(1), slotsBefore);
  }

  TEST_F(WarlockLvl1Test, HexCursesTargetWithConcentration)
  {
    placeCombatants();
    auto *factory = findFactory(warlock->getBonusActionFactoriesConst(), AbilityType::HEX);
    ASSERT_NE(factory, nullptr);
    // Hex is a buff/curse, not a direct-damage spell.
    EXPECT_NE(dynamic_cast<ThreatModifierFactory *>(factory), nullptr);
    EXPECT_EQ(dynamic_cast<DirectThreatFactory *>(factory), nullptr);
    EXPECT_GT(dynamic_cast<ThreatModifierFactory *>(factory)->calculateThreatToTarget(goblin, {}), 0.0);

    auto actoid = factory->create(static_cast<void *>(goblin));
    auto effect = std::dynamic_pointer_cast<Effect>(actoid);
    ASSERT_NE(effect, nullptr);
    effect->activate();

    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(goblin, EffectType::HEX));
    EXPECT_FALSE(warlock->getConcentrationEffect().expired());
  }

  TEST_F(WarlockLvl1Test, HexAddsNecroticDieToEldritchBlast)
  {
    placeCombatants();
    auto *factory = findFactory(warlock->getActionFactoriesConst(), AbilityType::ELDRITCH_BLAST);
    ASSERT_NE(factory, nullptr);
    auto *directThreat = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(directThreat, nullptr);

    const double base = directThreat->calculateThreatToTarget(goblin, {});
    EXPECT_GT(base, 0.0);

    ThreatModifiers mods;
    mods.set(ThreatModifierType::DMG_BONUS_DIE, std::vector<Die>{HexFactory::extraDmgDice});
    const double hexBonus = directThreat->calculateThreatToTargetDelta(goblin, mods);

    // calculateThreatToTargetDelta returns the *incremental* threat from the modifiers, so the +1d6
    // Necrotic from Hex must add positive threat against the cursed target.
    EXPECT_GT(hexBonus, 0.0);
  }

  // ----------------------------------------------------------------------------------------------------------
  // Shared helpers for the higher-level warlock fixtures.
  // ----------------------------------------------------------------------------------------------------------
  template <typename T> bool hasActionFactory(T *warlock, AbilityType type)
  {
    const auto &factories = warlock->getActionFactoriesConst();
    return std::any_of(factories.begin(), factories.end(),
                       [type](const std::shared_ptr<ActoidFactory> &f) { return f->getAbilityType() == type; });
  }

  template <typename T> bool hasBonusFactory(T *warlock, AbilityType type)
  {
    const auto &factories = warlock->getBonusActionFactoriesConst();
    return std::any_of(factories.begin(), factories.end(),
                       [type](const std::shared_ptr<ActoidFactory> &f) { return f->getAbilityType() == type; });
  }

  template <typename T> std::shared_ptr<ActoidFactory> findBonusFactory(T *warlock, AbilityType type)
  {
    for(const auto &f : warlock->getBonusActionFactoriesConst())
      {
        if(f->getAbilityType() == type)
          {
            return f;
          }
      }
    return nullptr;
  }

  ActoidFactory *findFactoryGeneric(const std::vector<std::shared_ptr<ActoidFactory>> &factories, AbilityType type)
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

  // ==========================================================================================================
  // Pact Magic slot scaling: a warlock only has slots at its single pact-slot level, and every leveled spell
  // is automatically upcast to that level.
  // ==========================================================================================================
  TEST(WarlockSlotScaling, Level3CastsAtSlotLevelTwo)
  {
    BattleMap::resetInstance();
    Teams::resetInstance();
    EffectTracker::resetInstance();
    Session session;
    WarlockLvl3 warlock(1);

    // A level-3 warlock has two 2nd-level pact slots and no 1st-level slots.
    EXPECT_EQ(warlock.getSpellslots().getMaxSlotLevel(), 2);
    EXPECT_EQ(warlock.getSpellslots().getUses(2), 2);
    EXPECT_EQ(warlock.getSpellslots().getUses(1), 0);

    // Every leveled spell upcasts to the pact-slot level (never below its own base level).
    EXPECT_EQ(warlock.getCastingSlotLevel(1), 2); // e.g. Hex / Armor of Agathys
    EXPECT_EQ(warlock.getCastingSlotLevel(2), 2); // e.g. Darkness
  }

  TEST(WarlockSlotScaling, Level5CastsAtSlotLevelThree)
  {
    BattleMap::resetInstance();
    Teams::resetInstance();
    EffectTracker::resetInstance();
    Session session;
    WarlockLvl5 warlock(1);

    EXPECT_EQ(warlock.getSpellslots().getMaxSlotLevel(), 3);
    EXPECT_EQ(warlock.getSpellslots().getUses(3), 2);
    EXPECT_EQ(warlock.getSpellslots().getUses(2), 0);
    EXPECT_EQ(warlock.getSpellslots().getUses(1), 0);

    EXPECT_EQ(warlock.getCastingSlotLevel(1), 3); // level-1 spell upcast to 3
    EXPECT_EQ(warlock.getCastingSlotLevel(2), 3); // level-2 spell upcast to 3
    EXPECT_EQ(warlock.getCastingSlotLevel(3), 3); // level-3 spell stays at 3
  }

  // ==========================================================================================================
  // Level 2 Warlock: second pact slot, Agonizing Blast + Devil's Sight invocations, Armor of Agathys.
  // ==========================================================================================================
  class WarlockLvl2Test : public ::testing::Test
  {
  protected:
    Session *session;
    WarlockLvl2 *warlock;

    void SetUp() override
    {
      BattleMap::resetInstance();
      Teams::resetInstance();
      EffectTracker::resetInstance();
      session = new Session();
      warlock = new WarlockLvl2(1);
    }
    void TearDown() override { EffectTracker::getInstance().clearEffects(); }
  };

  TEST_F(WarlockLvl2Test, BaseStatsAndInvocations)
  {
    EXPECT_EQ(warlock->getMaxHp(), 17);
    EXPECT_EQ(warlock->getDC(), 13);
    EXPECT_EQ(warlock->getLevel(), 2);
    // Two 1st-level pact slots.
    EXPECT_EQ(warlock->getSpellslots().getMaxSlotLevel(), 1);
    EXPECT_EQ(warlock->getSpellslots().getUses(1), 2);
    // Devil's Sight invocation.
    EXPECT_TRUE(warlock->hasPassiveAbility(AbilityType::DEVILS_SIGHT));
    // Armor of Agathys is a bonus-action option.
    EXPECT_TRUE(hasBonusFactory(warlock, AbilityType::ARMOR_OF_AGATHYS));
  }

  TEST_F(WarlockLvl2Test, ArmorOfAgathysGrantsFiveTempHpAtSlotLevelOne)
  {
    auto factory = findBonusFactory(warlock, AbilityType::ARMOR_OF_AGATHYS);
    ASSERT_NE(factory, nullptr);
    auto actoid = factory->create(nullptr);
    auto armor = std::dynamic_pointer_cast<ArmorOfAgathys>(actoid);
    ASSERT_NE(armor, nullptr);
    auto effect = std::dynamic_pointer_cast<Effect>(actoid);
    ASSERT_NE(effect, nullptr);

    effect->activate();
    // Cast with a 1st-level pact slot: 5 temporary Hit Points and 5 Cold retaliation.
    EXPECT_EQ(warlock->getTemporaryHp(), 5);
    EXPECT_EQ(armor->getRetaliationDamage(), 5);
    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(warlock, EffectType::ARMOR_OF_AGATHYS));
  }

  // ==========================================================================================================
  // Level 3 Warlock of the Archfey: 2nd-level slots, always-prepared Faerie Fire/Sleep, Steps of the Fey,
  // Darkness, and upcast Armor of Agathys.
  // ==========================================================================================================
  class WarlockLvl3Test : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    WarlockLvl3 *warlock;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      warlock = new WarlockLvl3(1);
      goblin = new Goblin(1);
    }
    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    void placeCombatants()
    {
      session->addCombatant(warlock, Color::BLUE);
      session->addCombatant(goblin, Color::RED);
      battleMap->buildBaseAdjacencyMatrix();
      battleMap->setCombatantCoordinates(*warlock, Coord{1, 3});
      battleMap->setCombatantCoordinates(*goblin, Coord{5, 3});
    }
  };

  TEST_F(WarlockLvl3Test, ArchfeySpellsAndStepsOfTheFey)
  {
    EXPECT_EQ(warlock->getMaxHp(), 24);
    EXPECT_EQ(warlock->getLevel(), 3);
    EXPECT_EQ(warlock->getSpellslots().getMaxSlotLevel(), 2);

    // Archfey always-prepared spells plus the chosen Darkness.
    EXPECT_TRUE(hasActionFactory(warlock, AbilityType::FAERIE_FIRE));
    EXPECT_TRUE(hasActionFactory(warlock, AbilityType::SLEEP));
    EXPECT_TRUE(hasActionFactory(warlock, AbilityType::DARKNESS));

    // Steps of the Fey provides a free Misty Step as a bonus action drawing from a dedicated (non-slot) pool.
    EXPECT_TRUE(warlock->hasPassiveAbility(AbilityType::STEPS_OF_THE_FEY));
    EXPECT_TRUE(hasBonusFactory(warlock, AbilityType::MISTY_STEP));
    auto mistyResource = warlock->getResource(AbilityType::MISTY_STEP);
    ASSERT_TRUE(mistyResource.has_value());
    // The free Misty Step pool is a plain Uses resource, not the Pact spell slots.
    EXPECT_EQ(dynamic_cast<Spellslots *>(*mistyResource), nullptr);
    // Number of free uses equals the spellcasting modifier (CHA +3 at level 3).
    EXPECT_EQ((*mistyResource)->getUses(1), 3);
  }

  TEST_F(WarlockLvl3Test, ArmorOfAgathysUpcastsToTenTempHp)
  {
    auto factory = findBonusFactory(warlock, AbilityType::ARMOR_OF_AGATHYS);
    ASSERT_NE(factory, nullptr);
    auto actoid = factory->create(nullptr);
    auto armor = std::dynamic_pointer_cast<ArmorOfAgathys>(actoid);
    ASSERT_NE(armor, nullptr);
    std::dynamic_pointer_cast<Effect>(actoid)->activate();

    // A level-3 warlock upcasts Armor of Agathys to slot level 2: 10 temporary Hit Points and 10 retaliation.
    EXPECT_EQ(warlock->getTemporaryHp(), 10);
    EXPECT_EQ(armor->getRetaliationDamage(), 10);
  }

  TEST_F(WarlockLvl3Test, DarknessBlindsEnemiesButNotDevilsSight)
  {
    placeCombatants();
    auto *factory = findFactoryGeneric(warlock->getActionFactoriesConst(), AbilityType::DARKNESS);
    ASSERT_NE(factory, nullptr);

    // Darkness is modeled as a threat MODIFIER (its value comes from the Blinded roll-type changes), not a
    // direct-threat. A creature without Devil's Sight is a worthwhile target; one with it is worthless.
    EXPECT_EQ(dynamic_cast<DirectThreatFactory *>(factory), nullptr);
    auto *modifier = dynamic_cast<ThreatModifierFactory *>(factory);
    ASSERT_NE(modifier, nullptr);
    EXPECT_GT(modifier->calculateThreatToTarget(goblin, {}), 0.0);
    WarlockLvl2 devilsSightDummy(99); // has Devil's Sight
    EXPECT_DOUBLE_EQ(modifier->calculateThreatToTarget(&devilsSightDummy, {}), 0.0);

    // Create the sphere centred on the goblin and confirm it Blinds a creature entering it.
    Coord center = battleMap->getCombatantCoordinates(*goblin).getRoot();
    auto actoid = factory->create(static_cast<void *>(&center));
    auto darkness = std::dynamic_pointer_cast<Darkness>(actoid);
    ASSERT_NE(darkness, nullptr);

    darkness->onEnter(goblin);
    EXPECT_TRUE(goblin->isAffectedBy(Conditions::BLINDED));

    // A creature with Devil's Sight is never Blinded by the darkness.
    darkness->onEnter(&devilsSightDummy);
    EXPECT_FALSE(devilsSightDummy.isAffectedBy(Conditions::BLINDED));
  }

  // ==========================================================================================================
  // Level 4 Warlock: the ASI raises Charisma 16 -> 18 (higher DC, save and Agonizing Blast), and Steps of the
  // Fey now has 4 free uses.
  // ==========================================================================================================
  TEST(WarlockLvl4Test, AbilityScoreImprovementRaisesCharisma)
  {
    BattleMap::resetInstance();
    Teams::resetInstance();
    EffectTracker::resetInstance();
    Session session;
    WarlockLvl4 warlock(1);

    EXPECT_EQ(warlock.getMaxHp(), 31);
    EXPECT_EQ(warlock.getLevel(), 4);
    EXPECT_EQ(warlock.getDC(), 14);                       // 8 + prof 2 + CHA 4
    EXPECT_EQ(warlock.getSpellcastingModifier(), 4);      // CHA +4 after the ASI
    EXPECT_EQ(warlock.getSavingThrow(SavingThrow::CHA), 6); // 4 + prof 2
    EXPECT_EQ(warlock.getSpellslots().getMaxSlotLevel(), 2);

    // Steps of the Fey free Misty Step uses scale with the spellcasting modifier (now 4).
    auto mistyResource = warlock.getResource(AbilityType::MISTY_STEP);
    ASSERT_TRUE(mistyResource.has_value());
    EXPECT_EQ((*mistyResource)->getUses(1), 4);
  }

  // ==========================================================================================================
  // Level 5 Warlock: 3rd-level slots, two Eldritch Blast beams, Repelling Blast + Eldritch Mind, and the
  // level-3 spells Hypnotic Pattern and Blink.
  // ==========================================================================================================
  class WarlockLvl5Test : public ::testing::Test
  {
  protected:
    BattleMap *battleMap;
    Teams *teams;
    Session *session;
    WarlockLvl5 *warlock;
    Goblin *goblin;

    void SetUp() override
    {
      BattleMap::resetInstance();
      battleMap = &BattleMap::getInstance();
      Teams::resetInstance();
      teams = &Teams::getInstance();
      EffectTracker::resetInstance();
      session = new Session();
      warlock = new WarlockLvl5(1);
      goblin = new Goblin(1);
    }
    void TearDown() override { EffectTracker::getInstance().clearEffects(); }

    void placeCombatants()
    {
      session->addCombatant(warlock, Color::BLUE);
      session->addCombatant(goblin, Color::RED);
      battleMap->buildBaseAdjacencyMatrix();
      battleMap->setCombatantCoordinates(*warlock, Coord{1, 3});
      battleMap->setCombatantCoordinates(*goblin, Coord{3, 3});
    }
  };

  TEST_F(WarlockLvl5Test, BaseStatsBeamsAndInvocations)
  {
    EXPECT_EQ(warlock->getMaxHp(), 38);
    EXPECT_EQ(warlock->getLevel(), 5);
    EXPECT_EQ(warlock->getDC(), 15);                       // 8 + prof 3 + CHA 4
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::WIS), 5); // 2 + prof 3
    EXPECT_EQ(warlock->getSavingThrow(SavingThrow::CHA), 7); // 4 + prof 3
    EXPECT_EQ(warlock->getSpellslots().getMaxSlotLevel(), 3);

    // Eldritch Blast fires two beams at level 5.
    auto *factory = findFactoryGeneric(warlock->getActionFactoriesConst(), AbilityType::ELDRITCH_BLAST);
    ASSERT_NE(factory, nullptr);
    auto actoid = factory->create(static_cast<void *>(goblin));
    auto *eldritchBlast = dynamic_cast<EldritchBlast *>(actoid.get());
    ASSERT_NE(eldritchBlast, nullptr);
    EXPECT_EQ(eldritchBlast->getNumBeams(), 2);

    // Invocations: Devil's Sight and Eldritch Mind (Concentration advantage).
    EXPECT_TRUE(warlock->hasPassiveAbility(AbilityType::DEVILS_SIGHT));
    EXPECT_TRUE(warlock->hasPassiveAbility(AbilityType::ELDRITCH_MIND));

    // Level-3 spells.
    EXPECT_TRUE(hasActionFactory(warlock, AbilityType::HYPNOTIC_PATTERN));
    EXPECT_TRUE(hasActionFactory(warlock, AbilityType::BLINK));
    EXPECT_TRUE(hasActionFactory(warlock, AbilityType::DARKNESS));
  }

  TEST_F(WarlockLvl5Test, ArmorOfAgathysUpcastsToFifteenTempHp)
  {
    auto factory = findBonusFactory(warlock, AbilityType::ARMOR_OF_AGATHYS);
    ASSERT_NE(factory, nullptr);
    auto actoid = factory->create(nullptr);
    auto armor = std::dynamic_pointer_cast<ArmorOfAgathys>(actoid);
    ASSERT_NE(armor, nullptr);
    std::dynamic_pointer_cast<Effect>(actoid)->activate();

    // A level-5 warlock upcasts Armor of Agathys to slot level 3: 15 temporary Hit Points and 15 retaliation.
    EXPECT_EQ(warlock->getTemporaryHp(), 15);
    EXPECT_EQ(armor->getRetaliationDamage(), 15);
  }

  TEST_F(WarlockLvl5Test, BlinkMakesCasterEtherealAndUntargetable)
  {
    placeCombatants();
    auto *factory = findFactoryGeneric(warlock->getActionFactoriesConst(), AbilityType::BLINK);
    ASSERT_NE(factory, nullptr);
    auto actoid = factory->create(nullptr);
    auto blink = std::dynamic_pointer_cast<Blink>(actoid);
    ASSERT_NE(blink, nullptr);
    auto effect = std::dynamic_pointer_cast<Effect>(actoid);
    ASSERT_NE(effect, nullptr);

    effect->activate();
    EXPECT_TRUE(EffectTracker::getInstance().isAffectingCombatant(warlock, EffectType::BLINK));
    EXPECT_FALSE(warlock->isEtherealUntargetable()); // starts on the material plane

    // Over many end-of-turn d6 rolls the caster blinks into the Border Ethereal at least once (4-6).
    seedThreadRNG(7);
    bool everEthereal = false;
    for(int i = 0; i < 60; ++i)
      {
        warlock->setEtherealUntargetable(false);
        effect->combatantSavedAtEndOfTurn(warlock);
        if(warlock->isEtherealUntargetable())
          {
            everEthereal = true;
            break;
          }
      }
    EXPECT_TRUE(everEthereal);

    // While ethereal the caster is excluded from enemy target lists.
    warlock->setEtherealUntargetable(true);
    auto targetable = battleMap->getNonSwallowedEnemiesWithinRadius(goblin, 20);
    EXPECT_TRUE(std::find(targetable.begin(), targetable.end(), warlock) == targetable.end());

    // At the start of its next turn the caster returns to the material plane.
    EXPECT_TRUE(effect->startOfTurnForCombatant(warlock));
    EXPECT_FALSE(warlock->isEtherealUntargetable());
  }

  TEST_F(WarlockLvl5Test, HypnoticPatternCharmsAndIncapacitatesOnFailedSave)
  {
    placeCombatants();
    auto *factory = findFactoryGeneric(warlock->getActionFactoriesConst(), AbilityType::HYPNOTIC_PATTERN);
    ASSERT_NE(factory, nullptr);
    auto *direct = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(direct, nullptr);
    // A goblin (no Wisdom save proficiency) is very likely to fail against DC 15, so it is a real threat.
    EXPECT_GT(direct->calculateThreatToTarget(goblin, {}), 0.0);

    // Activate the pattern centred on the goblin; with a low Wisdom save it fails and is Charmed +
    // Incapacitated. Use a fixed seed so the save roll is deterministic.
    seedThreadRNG(1);
    Coord center = battleMap->getCombatantCoordinates(*goblin).getRoot();
    auto actoid = factory->create(static_cast<void *>(&center));
    auto effect = std::dynamic_pointer_cast<Effect>(actoid);
    ASSERT_NE(effect, nullptr);
    effect->activate();

    EXPECT_TRUE(goblin->isAffectedBy(Conditions::CHARMED));
    EXPECT_TRUE(goblin->isAffectedBy(Conditions::INCAPACITATED));
    EXPECT_TRUE(effect->isAffecting(goblin));
  }

  TEST_F(WarlockLvl5Test, HypnoticPatternIgnoresCharmImmuneCreatures)
  {
    // A Night Hag is immune to the Charmed condition, so Hypnotic Pattern poses no threat to it and never
    // takes hold of it.
    NightHag *hag = new NightHag(1);
    ASSERT_TRUE(hag->isImmuneToCondition(Conditions::CHARMED));

    session->addCombatant(warlock, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(static_cast<Combatant *>(hag), Color::RED);
    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*warlock, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{3, 3});
    battleMap->setCombatantCoordinates(*hag, Coord{4, 3});

    auto *factory = findFactoryGeneric(warlock->getActionFactoriesConst(), AbilityType::HYPNOTIC_PATTERN);
    ASSERT_NE(factory, nullptr);
    auto *direct = dynamic_cast<DirectThreatFactory *>(factory);
    ASSERT_NE(direct, nullptr);
    // The charm-immune Night Hag contributes no threat, while the goblin does.
    EXPECT_DOUBLE_EQ(direct->calculateThreatToTarget(hag, {}), 0.0);
    EXPECT_GT(direct->calculateThreatToTarget(goblin, {}), 0.0);

    // Activating the pattern over both creatures never Charms the immune Night Hag.
    seedThreadRNG(1);
    Coord center = battleMap->getCombatantCoordinates(*goblin).getRoot();
    auto actoid = factory->create(static_cast<void *>(&center));
    auto effect = std::dynamic_pointer_cast<Effect>(actoid);
    ASSERT_NE(effect, nullptr);
    effect->activate();

    EXPECT_FALSE(hag->isAffectedBy(Conditions::CHARMED));
    EXPECT_FALSE(effect->isAffecting(hag));
  }
}

