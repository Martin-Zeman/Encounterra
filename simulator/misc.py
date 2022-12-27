from enum import Enum


class SavingThrow(Enum):
    STR = 1
    DEX = 2
    CON = 3
    INT = 4
    WIS = 5
    CHA = 6

class DamageType(Enum):
    Bludgeoning = 0
    Slashing = 1
    Piercing = 2
    Fire = 3
    Cold = 4
    Poison = 5
    Acid = 6
    Lightning = 7
    Radiant = 8
    Necrotic = 9
    Force = 10
    Psychic = 11


class Conditions(Enum):
    BLINDED = 1
    CHARMED = 2
    DEAFENED = 3
    FRIGHTENED = 4
    GRAPPLED = 5
    INCAPACITATED = 6
    INVISIBLE = 7
    PARALYZED = 8
    PETRIFIED = 9
    POISONED = 10
    PRONE = 11
    RESTRAINED = 12
    STUNNED = 13
    UNCONSCIOUS = 14
