#include "action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/types.hpp"

namespace enc
{
bool hasAdvantageSavingThrow(SavingThrow savingThrow, Combatant* target, bool isSpellEffect) {
    if (target->getSavingThrowRollTypeMods(savingThrow).contains(RollType::ADVANTAGE)) {
        return true;
    }

    if (savingThrow == SavingThrow::DEX && 
        target->hasPassiveAbility(AbilityType::DANGER_SENSE) && 
        !target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::BLINDED, Conditions::DEAFENED})) {
        std::cout << target->_name << " gains advantage through Danger Sense" << std::endl;
        return true;
    }

    if (savingThrow == SavingThrow::DEX && target->isDodging()) {
        std::cout << target->_name << " gains advantage by dodging" << std::endl;
        return true;
    }

    if (isSpellEffect && target->hasPassiveAbility(AbilityType::MAGIC_RESISTANCE)) {
        std::cout << target->_name << " gains advantage through Magic Resistance" << std::endl;
        return true;
    }

    return false;
}

bool hasDisadvantageSavingThrow(SavingThrow savingThrow, Combatant* target) {
    if (target->getSavingThrowRollTypeMods(savingThrow).contains(RollType::DISADVANTAGE)) {
        return true;
    }

    if (savingThrow == SavingThrow::DEX && target->isAffectedByAny({Conditions::RESTRAINED})) {
        std::cout << target->_name << " is restrained" << std::endl;
        return true;
    }

    return false;
}

  void resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant *target,
                               bool halfOnSuccess = false, bool isSpellEffect = false)
  {
    auto stBonus = target->getSavingThrow(savingThrowType);
    
    // Determine advantage/disadvantage
    std::unordered_set<RollType> types;
    if (hasAdvantageSavingThrow(savingThrowType, target, isSpellEffect)) {
        types.insert(RollType::ADVANTAGE);
    }
    if (hasDisadvantageSavingThrow(savingThrowType, target)) {
        types.insert(RollType::DISADVANTAGE);
    }
    auto finalModifier = reconcileRollTypes(types);

    Die d20{1, 20};
    int rolled;

    if(finalModifier == RollType::STRAIGHT)
      {
        rolled = rollDice(d20);
      }
    else if(finalModifier == RollType::ADVANTAGE)
      {
        rolled = std::max(rollDice(d20), rollDice(d20));
      }
    else
      { // DISADVANTAGE
        rolled = std::min(rollDice(d20), rollDice(d20));
      }

    // Handle natural 1s and 20s
    bool saved;
    if (rolled == 1) {
        saved = false;
    } else if (rolled == 20) {
        saved = true;
    } else {
        // Add bonus dice modifiers
        for (const auto& bonusDie : target->getSavingThrowDiceMods(savingThrowType)) {
            int bonusDiceRoll = rollDice(bonusDie);
            std::cout << "Adding " << bonusDiceRoll << " from bonus " << bonusDie <<  "to the roll" << std::endl;
            rolled += bonusDiceRoll;
        }
        saved = (rolled + stBonus >= dc);
    }

    // Apply damage
    if (!saved) {
        if (savingThrowType == SavingThrow::DEX && 
            target->hasPassiveAbility(AbilityType::EVASION)) {
            dmg /= 2;
            std::cout << target->_name << " failed the save but only receives " << dmg << " damage thanks to Evasion" << std::endl;
        } else {
            std::cout << abilityName << " deals " << dmg << " to " << target->_name << std::endl;
            target->receiveDmg(dmg, dmgType);
        }
    } else if (halfOnSuccess) {
        if (savingThrowType == SavingThrow::DEX && 
            target->hasPassiveAbility(AbilityType::EVASION)) {
            std::cout << target->_name << " made the save and receives no damage thanks to Evasion" << std::endl;
        } else {
            dmg /= 2;
            std::cout << abilityName << " deals " << dmg << " to " << target->_name << std::endl;
            target->receiveDmg(dmg, dmgType);
        }
    }

    BattleMap::getInstance().removeCombatantIfDead(*target);
  }
}
