#pragma once

namespace enc
{
  enum class Artificer
  {
    ALCHEMIST,
    ARMORER,
    ARTILLERIST,
    BATTLE_SMITH
  };

  enum class Barbarian
  {
    PATH_OF_THE_ANCESTRAL_GUARDIAN,
    PATH_OF_THE_BEAST,
    PATH_OF_THE_BERSERKER,
    PATH_OF_THE_STORM_HERALD,
    PATH_OF_THE_TOTEM_WARRIOR,
    PATH_OF_THE_ZEALOT,
    PATH_OF_WILD_MAGIC,
    BEFORE_SUBCLASS
  };

  enum class Bard
  {
    COLLEGE_OF_CREATION,
    COLLEGE_OF_ELOQUENCE,
    COLLEGE_OF_GLAMOUR,
    COLLEGE_OF_LORE,
    COLLEGE_OF_SPIRITS,
    COLLEGE_OF_SWORDS,
    COLLEGE_OF_VALOR,
    COLLEGE_OF_WHISPERS,
    BEFORE_SUBCLASS
  };

  enum class Cleric
  {
    ARCANA_DOMAIN,
    DEATH_DOMAIN,
    FORGE_DOMAIN,
    GRAVE_DOMAIN,
    KNOWLEDGE_DOMAIN,
    LIFE_DOMAIN,
    LIGHT_DOMAIN,
    NATURE_DOMAIN,
    ORDER_DOMAIN,
    PEACE_DOMAIN,
    TEMPEST_DOMAIN,
    TRICKERY_DOMAIN,
    TWILIGHT_DOMAIN,
    WAR_DOMAIN
  };

  enum class Druid
  {
    CIRCLE_OF_DREAMS,
    CIRCLE_OF_SPORES,
    CIRCLE_OF_STARS,
    CIRCLE_OF_WILDFIRE,
    CIRCLE_OF_LAND,
    CIRCLE_OF_MOON,
    CIRCLE_OF_SHEPHERD,
    BEFORE_SUBCLASS
  };

  enum class Fighter
  {
    ARCANE_ARCHER,
    BATTLE_MASTER,
    CAVALIER,
    ECHO_KNIGHT,
    ELDRITCH_KNIGHT,
    PSI_WARRIOR,
    RUNE_KNIGHT,
    SAMURAI,
    PURPLE_DRAGON_KNIGHT,
    BEFORE_SUBCLASS
  };

  enum class Paladin
  {
    OATH_OF_CONQUEST,
    OATH_OF_DEVOTION,
    OATH_OF_GLORY,
    OATH_OF_REDEMPTION,
    OATH_OF_ANCIENTS,
    OATH_OF_CROWN,
    OATH_OF_WATCHERS,
    OATH_OF_VENGEANCE,
    OATHBREAKER,
    BEFORE_SUBCLASS
  };

  enum class Ranger
  {
    BEAST_MASTER,
    DRAKEWARDEN,
    FEY_WANDERER,
    GLOOM_STALKER,
    HORIZON_WALKER,
    HUNTER,
    MONSTER_SLAYER,
    SWARMKEEPER,
    BEFORE_SUBCLASS
  };

  enum class Rogue
  {
    ARCANE_TRICKSTER,
    ASSASSIN,
    INQUISITIVE,
    PHANTOM,
    MASTERMIND,
    SCOUT,
    SOULKNIFE,
    SWASHBUCKLER,
    THIEF,
    BEFORE_SUBCLASS
  };

  enum class Monk
  {
    WAY_OF_MERCY,
    WAY_OF_SHADOW,
    WAY_OF_THE_ASCENDANT_DRAGON,
    WAY_OF_ASTRAL_SELF,
    WAY_OF_DRUNKEN_MASTER,
    WAY_OF_THE_FOUR_ELEMENTS,
    WAY_OF_KENSEI,
    WAY_OF_THE_LONG_DEATH,
    WAY_OF_THE_OPEN_HAND,
    WAY_OF_THE_SUN_SOUL,
    BEFORE_SUBCLASS
  };

  enum class Sorcerer
  {
    ABERRANT_MIND,
    CLOCKWORK_SOUL,
    DIVINE_SOUL,
    DRACONIC_BLOODLINE,
    SHADOW_MAGIC,
    STORM_SORCERY,
    WILD_MAGIC
  };

  enum class Warlock
  {
    THE_ARCHFEY,
    THE_CELESTIAL,
    THE_FATHOMLESS,
    THE_FIEND,
    THE_GENIE,
    THE_GREAT_OLD_ONE,
    THE_HEXBLADE,
    THE_UNDEAD,
    THE_UNDYING
  };

  enum class Wizard
  {
    BLADESINGER,
    CHRONURGY,
    GRAVITURGY,
    ORDER_OF_SCRIBES,
    ABJURATION,
    CONJURATION,
    DIVINATION,
    ENCHANTMENT,
    EVOCATION,
    ILLUSION,
    NECROMANCY,
    TRANSMUTATION,
    WAR_MAGIC,
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

  enum class ClassType
  {
    ARTIFICER,
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

}
