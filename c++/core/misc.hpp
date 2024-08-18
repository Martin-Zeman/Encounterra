#pragma once

#include <map>
#include <cstdint>
#include <variant>

namespace enc
{
  // enum class Artificer
  // {
  //   ALCHEMIST,
  //   ARMORER,
  //   ARTILLERIST,
  //   BATTLE_SMITH
  // };

  enum class Barbarian
  {
    PATH_OF_THE_BERSERKER,
    PATH_OF_THE_ZEALOT,
    PATH_OF_WILD_HEART,
    PATH_OF_WORLD_TREE,
    BEFORE_SUBCLASS
  };

  enum class Bard
  {
    COLLEGE_OF_DANCE,
    COLLEGE_OF_GLAMOUR,
    COLLEGE_OF_LORE,
    COLLEGE_OF_VALOR,
    BEFORE_SUBCLASS
  };

  enum class Cleric
  {
    LIFE_DOMAIN,
    LIGHT_DOMAIN,
    TRICKERY_DOMAIN,
    WAR_DOMAIN,
    BEFORE_SUBCLASS
  };

  enum class Druid
  {
    CIRCLE_OF_LAND,
    CIRCLE_OF_MOON,
    CIRCLE_OF_SEA,
    CIRCLE_OF_STARS,
    BEFORE_SUBCLASS
  };

  enum class Fighter
  {
    BATTLE_MASTER,
    ELDRITCH_KNIGHT,
    PSI_WARRIOR,
    CHAMPION,
    BEFORE_SUBCLASS
  };

  enum class Paladin
  {
    OATH_OF_DEVOTION,
    OATH_OF_GLORY,
    OATH_OF_ANCIENTS,
    OATH_OF_VENGEANCE,
    BEFORE_SUBCLASS
  };

  enum class Ranger
  {
    BEAST_MASTER,
    FEY_WANDERER,
    GLOOM_STALKER,
    HUNTER,
    BEFORE_SUBCLASS
  };

  enum class Rogue
  {
    ARCANE_TRICKSTER,
    ASSASSIN,
    SOULKNIFE,
    THIEF,
    BEFORE_SUBCLASS
  };

  enum class Monk
  {
    WARRIOR_OF_MERCY,
    WARRIOR_OF_SHADOW,
    WARRIOR_OF_THE_OPEN_HAND,
    WARRIOR_OF_THE_ELEMENTS,
    BEFORE_SUBCLASS
  };

  enum class Sorcerer
  {
    ABERRANT_SORCERY,
    CLOCKWORK_SORCERY,
    DRACONIC_SORCERY,
    WILD_MAGIC,
    BEFORE_SUBCLASS
  };

  enum class Warlock
  {
    ARCHFEY_PATRON,
    CELESTIAL_PATRON,
    FIEND_PATRON,
    GREAT_OLD_ONE_PATRON,
    UNDYING
  };

  enum class Wizard
  {
    ABJURER,
    DIVINER,
    EVOKER,
    ILLUSIONIST,
    BEFORE_SUBCLASS
  };

  enum class Monster
  {
    HUMANOID,
    GIANT,
    MONSTROSITY,
    BEAST,
    UNDEAD,
    DRAGON,
    CONSTRUCT,
    ELEMENTAL,
    ABERRATION,
    FEY,
    OOZE,
    PLANT,
    FIEND
  };

  enum class CombatantType
  {
    // ARTIFICER,
    BARBARIAN,
    BARD,
    CLERIC,
    DRUID,
    FIGHTER,
    PALADIN,
    RANGER,
    ROGUE,
    MONK,
    SORCERER,
    WARLOCK,
    WIZARD,
    MONSTER
  };

  using SubType = std::variant<Monster, Barbarian, Bard, Cleric, Druid, Fighter, Paladin, Rogue, Ranger, Monk, Sorcerer, Warlock, Wizard>;

  enum class SpellcastingResourceType
  {
    SPELLSLOTS,
    SPECIAL
  };

  enum class SavingThrow
  {
    STR = 1,
    DEX,
    CON,
    INT,
    WIS,
    CHA
  };

  enum class SkillCheck
  {
    ATHLETICS = 1,
    ACROBATICS
  };

  enum class DamageType
  {
    Bludgeoning = 0,
    Slashing,
    Piercing,
    Fire,
    Cold,
    Poison,
    Acid,
    Lightning,
    Radiant,
    Necrotic,
    Force,
    Psychic,
    Thunder,
    BludgeoningMagical,
    SlashingMagical,
    PiercingMagical,
    Random
  };

  enum class Size
  {
    TINY = -2,
    SMALL = -1,
    MEDIUM = 0,
    LARGE = 1,
    HUGE = 2,
    GARGANTUAN = 3
  };

  enum class PhaseOfTurn
  {
    START_OF_TURN,
    END_OF_TURN,
    ACTION
  };

  enum class RollType : uint8_t
  {
    STRAIGHT = 1 << 0,
    ADVANTAGE = 1 << 1,
    DISADVANTAGE = 1 << 2
  };

  inline RollType operator|(RollType a, RollType b) { return static_cast<RollType>(static_cast<uint8_t>(a) | static_cast<uint8_t>(b)); }

  inline RollType operator&(RollType a, RollType b) { return static_cast<RollType>(static_cast<uint8_t>(a) & static_cast<uint8_t>(b)); }

  const std::map<RollType, std::map<int, int>> ROLL_TYPE_DELTA
    = {{RollType::STRAIGHT, {{0, 0},  {1, 0},  {2, 0},  {3, 0},  {4, 0},  {5, 0},  {6, 0},  {7, 0},  {8, 0},  {9, 0}, {10, 0},
                             {11, 0}, {12, 0}, {13, 0}, {14, 0}, {15, 0}, {16, 0}, {17, 0}, {18, 0}, {19, 0}, {20, 0}}},
       {RollType::ADVANTAGE, {{0, 0},  {1, 0},  {2, 3},  {3, 4},  {4, 5},  {5, 5},  {6, 5},  {7, 5},  {8, 5},  {9, 5}, {10, 4},
                              {11, 4}, {12, 4}, {13, 3}, {14, 3}, {15, 3}, {16, 2}, {17, 2}, {18, 1}, {19, 1}, {20, 0}}},
       {RollType::DISADVANTAGE, {{0, 0},   {1, 0},   {2, 0},   {3, -1},  {4, -1},  {5, -2},  {6, -2},  {7, -3},  {8, -3},  {9, -3}, {10, -4},
                                 {11, -4}, {12, -4}, {13, -5}, {14, -5}, {15, -5}, {16, -5}, {17, -5}, {18, -5}, {19, -4}, {20, -3}}}};

  const std::map<RollType, double> ROLL_TYPE_CRIT_DELTA = {{RollType::STRAIGHT, 1.0}, {RollType::ADVANTAGE, 2.0}, {RollType::DISADVANTAGE, 0.5}};

  enum class ThreatModifierType
  {
    TO_HIT_FLAT,
    TO_HIT_DIE,
    ROLL_TYPE,
    RANGE,
    DMG_BONUS_FLAT,
    DMG_BONUS_DIE,
    CRIT_RANGE,
    AUTO_CRIT,
    TARGET_AC
  };

  enum class Terrain
  {
    NORMAL_TERRAIN = 0,
    DIFFICULT_TERRAIN,
    IMPASSABLE_TERRAIN
  };

  enum class Occupancy
  {
    FREE = 1,
    OCCUPIED_BY_COMBATANT
  };
}
