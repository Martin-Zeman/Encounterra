#include "action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/types.hpp"
#include "core/feasibility.hpp"
#include "actions/dodge.hpp"
#include "actions/attack.hpp"
#include "actions/break_grapple.hpp"
#include "actions/movement.hpp"
#include "spells/firebolt.hpp"
#include "spells/ray_of_frost.hpp"
#include "spells/scorching_ray.hpp"
#include "spells/misty_step.hpp"
#include "spells/healing_word.hpp"
#include "spells/cure_wounds.hpp"
#include "spells/bless.hpp"
#include "spells/guiding_bolt.hpp"
#include "spells/sacred_flame.hpp"
#include "spells/shield_of_faith.hpp"
#include "spells/starry_wisp.hpp"
#include "spells/toll_the_dead.hpp"
#include "spells/flaming_sphere.hpp"
#include "spells/moonbeam.hpp"
#include "spells/thunderwave.hpp"
#include "spells/magic_missile.hpp"
#include "spells/mage_armor.hpp"
#include "spells/vicious_mockery.hpp"
#include "spells/dissonant_whispers.hpp"
#include "spells/bane.hpp"
#include "spells/charm_person.hpp"
#include "spells/color_spray.hpp"
#include "spells/eldritch_blast.hpp"
#include "spells/hex.hpp"
#include "spells/armor_of_agathys.hpp"
#include "spells/darkness.hpp"
#include "spells/hypnotic_pattern.hpp"
#include "spells/blink.hpp"
#include "abilities/bardic_inspiration.hpp"
#include "abilities/cutting_words.hpp"
#include "spells/sleep.hpp"
#include "abilities/pounce.hpp"
#include "abilities/roar.hpp"
#include "abilities/rage.hpp"
#include "abilities/second_wind.hpp"
#include "abilities/lay_on_hands.hpp"
#include "abilities/on_hit_divine_smite.hpp"
#include "abilities/vow_of_enmity.hpp"
#include "abilities/weapon_mastery_effects.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>

namespace enc
{
  // When a Hex curse cast by the attacker is active on the target, every successful attack roll (weapon or
  // spell) deals an extra 1d6 Necrotic. A critical hit doubles the curse's damage dice just like the rest.
  void applyHexDamageOnHit(Combatant *attacker, Combatant *target, int multiplier)
  {
    EffectTracker &tracker = EffectTracker::getInstance();
    for(const auto &effect : tracker.getEffectsByInitiator(attacker))
      {
        if(effect->getEffectType() == EffectType::HEX && effect->isAffecting(target))
          {
            int hexDmg = multiplier * rollDiceMulti({HexFactory::extraDmgDice});
            if(hexDmg < 0)
              {
                hexDmg = 0;
              }
            std::cout << "Hex deals an extra " << hexDmg << " Necrotic damage to " << target->_name << std::endl;
            target->receiveDmg(hexDmg, HexFactory::dmgType, multiplier);
            return;
          }
      }
  }

  bool hasAdvantageSavingThrow(SavingThrow savingThrow, Combatant *target, bool isSpellEffect)
  {
    if(target->getSavingThrowRollTypeMods(savingThrow).contains(RollType::ADVANTAGE))
      {
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target->hasPassiveAbility(AbilityType::DANGER_SENSE)
       && !target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::BLINDED, Conditions::DEAFENED}))
      {
        std::cout << target->_name << " gains advantage through Danger Sense" << std::endl;
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target->isDodging())
      {
        std::cout << target->_name << " gains advantage by dodging" << std::endl;
        return true;
      }

    if(isSpellEffect && target->hasPassiveAbility(AbilityType::MAGIC_RESISTANCE))
      {
        std::cout << target->_name << " gains advantage through Magic Resistance" << std::endl;
        return true;
      }

    return false;
  }

  bool hasDisadvantageSavingThrow(SavingThrow savingThrow, Combatant *target)
  {
    if(target->getSavingThrowRollTypeMods(savingThrow).contains(RollType::DISADVANTAGE))
      {
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target->isAffectedByAny({Conditions::RESTRAINED}))
      {
        std::cout << target->_name << " is restrained" << std::endl;
        return true;
      }

    return false;
  }

  bool resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant *target,
                             bool halfOnSuccess, bool isSpellEffect)
  {
    auto stBonus = target->getSavingThrow(savingThrowType);

    // Determine advantage/disadvantage
    std::unordered_set<RollType> types;
    if(hasAdvantageSavingThrow(savingThrowType, target, isSpellEffect))
      {
        types.insert(RollType::ADVANTAGE);
      }
    if(hasDisadvantageSavingThrow(savingThrowType, target))
      {
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
    if(rolled == 1)
      {
        saved = false;
      }
    else if(rolled == 20)
      {
        saved = true;
      }
    else
      {
        // Add bonus dice modifiers
        for(const auto &bonusDie : target->getSavingThrowDiceMods(savingThrowType))
          {
            int bonusDiceRoll = rollDice(bonusDie);
            std::cout << "Adding " << bonusDiceRoll << " from bonus " << bonusDie << "to the roll" << std::endl;
            rolled += bonusDiceRoll;
          }
        // Subtract penalty dice (e.g. Bane's 1d4)
        for(const auto &penaltyDie : target->getSavingThrowPenaltyDice(savingThrowType))
          {
            int penaltyRoll = rollDice(penaltyDie);
            std::cout << "Subtracting " << penaltyRoll << " from penalty " << penaltyDie << " on the save" << std::endl;
            rolled -= penaltyRoll;
          }
        saved = (rolled + stBonus >= dc);
      }

    // Apply damage
    if(!saved)
      {
        if(savingThrowType == SavingThrow::DEX && target->hasPassiveAbility(AbilityType::EVASION))
          {
            dmg /= 2;
            std::cout << target->_name << " failed the save but only receives " << dmg << " damage thanks to Evasion" << std::endl;
          }
        else
          {
            std::cout << abilityName << " deals " << dmg << " to " << target->_name << std::endl;
            target->receiveDmg(dmg, dmgType);
          }
      }
    else if(halfOnSuccess)
      {
        if(savingThrowType == SavingThrow::DEX && target->hasPassiveAbility(AbilityType::EVASION))
          {
            std::cout << target->_name << " made the save and receives no damage thanks to Evasion" << std::endl;
          }
        else
          {
            dmg /= 2;
            std::cout << abilityName << " deals " << dmg << " to " << target->_name << std::endl;
            target->receiveDmg(dmg, dmgType);
          }
      }

    BattleMap::getInstance().removeCombatantIfDead(*target);
    return saved;
  }

  std::shared_ptr<Actoid> ActionResolver::handleErrorCase(const std::shared_ptr<Actoid> &action, Combatant *combatant)
  {
    if(action->getFactory().getAbilityType() == AbilityType::STANDARD_MOVEMENT)
      {
        // The planner can hand us a movement step that is no longer feasible at resolution time. Report the
        // actual cause instead of always blaming difficult terrain (which is often absent from the map).
        auto &battleMap = BattleMap::getInstance();
        std::string reason = "its next step is blocked";
        if(auto *movement = dynamic_cast<MovementIncrement *>(action.get()))
          {
            Coords targetPosition = battleMap.getCombatantCoordinates(*combatant) + movement->getIncrement();
            const bool difficultTerrain = battleMap.isDifficultTerrainAt(targetPosition);
            if(!targetPosition.areValidCoords(battleMap.getGridSize()))
              {
                reason = "its next step would leave the battle map";
              }
            else if(!battleMap.areEmptyOrSelf(targetPosition, *combatant))
              {
                reason = "its next step is occupied by another combatant";
              }
            else if(combatant->getMovement() < (difficultTerrain ? 2 : 1))
              {
                reason = difficultTerrain ? "it doesn't have enough movement to enter difficult terrain"
                                          : "it has run out of movement";
              }
          }
        std::cerr << combatant->_name << " can't complete its movement: " << reason << std::endl;
        combatant->setMovement(0); // Avoid endless looping when the planned move turns out to be infeasible.
        return nullptr;
      }

    if(combatant->hasAction())
      {
        std::cerr << "Action " << action->toString() << " by " << combatant->_name << " is not feasible. Taking the Dodge action!" << std::endl;
        auto dodgeFactory = std::make_shared<DodgeFactory>(combatant);
        return dodgeFactory->create({});
      }

    std::cerr << "Action " << action->toString() << " by " << combatant->_name << " is not feasible" << std::endl;
    return nullptr;
  }

  // Graze mastery: on a miss, the target still takes damage equal to the attack's ability modifier (stored on
  // the factory as the graze damage). No effect for weapons that lack the Graze property.
  static void applyGrazeOnMiss(AttackFactory &factory, Combatant *target)
  {
    int grazeDmg = factory.getGrazeDamage();
    if(grazeDmg > 0)
      {
        std::cout << "Graze deals " << grazeDmg << " to " << target->_name << std::endl;
        target->receiveDmg(grazeDmg, factory.getDmgType());
        BattleMap::getInstance().removeCombatantIfDead(*target);
      }
  }

  std::unordered_set<RollType> ActionResolver::collectAttackRollTypes(Attack *attack, Combatant *target, Combatant *attacker) const
  {
    auto &battleMap = BattleMap::getInstance();
    EffectTracker &effectTracker = EffectTracker::getInstance();
    AttackFactory &factory = attack->getAttackFactory();

    std::unordered_set<RollType> types;
    // 2024: a Grappled creature has Disadvantage on attack rolls against any target other than the grappler.
    if(attacker->isAffectedBy(Conditions::GRAPPLED) && attacker->getInitiatorOfCondition(Conditions::GRAPPLED) != target)
      {
        types.insert(RollType::DISADVANTAGE);
      }
    // Some attacks (e.g. the Bugbear Warrior's Light Hammer) have Advantage against a creature this combatant grapples.
    if(factory.hasAdvantageVsGrappledTarget() && target->getInitiatorOfCondition(Conditions::GRAPPLED) == attacker)
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Reckless Attack: a barbarian attacking recklessly has Advantage on its Strength melee attacks until the
    // start of its next turn, and attack rolls against it have Advantage during that time as well.
    if(attack->getAbilityType() == AbilityType::RECKLESS_ATTACK
       || effectTracker.isAffectingCombatant(attacker, EffectType::RECKLESS_ATTACK)
       || effectTracker.isAffectingCombatant(target, EffectType::RECKLESS_ATTACK))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Wolf Rage: while the Wolf-aspect barbarian is raging, its allies have Advantage on attack rolls against
    // any enemy within 5 ft of the barbarian.
    for(const auto &effect : effectTracker.getEffectsByType(EffectType::RAGE))
      {
        auto rage = std::dynamic_pointer_cast<Rage>(effect);
        if(!rage || rage->getVariant() != RageVariant::WOLF)
          {
            continue;
          }
        Combatant *barbarian = rage->getInitiator();
        if(barbarian == attacker)
          {
            continue; // The benefit goes to the barbarian's allies, not the barbarian itself.
          }
        if(Teams::getInstance().areAllies(*attacker, *barbarian)
           && battleMap.getHopDistanceCombatants(*target, *barbarian) <= 1)
          {
            types.insert(RollType::ADVANTAGE);
            break;
          }
      }
    // Pack Tactics: a creature with this trait has Advantage on an attack roll against a target if at least one
    // of its allies is within 5 ft of the target and that ally is not Incapacitated.
    if(attacker->hasPassiveAbility(AbilityType::PACK_TACTICS) && battleMap.isAllyAdjacentToTarget(*attacker, *target))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Faerie Fire: attack rolls against a target affected by Faerie Fire are made with Advantage.
    if(effectTracker.isAffectingCombatant(target, EffectType::FAERIE_FIRE))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Sap mastery: a Sapped attacker has Disadvantage on its next attack roll.
    if(effectTracker.isAffectingCombatant(attacker, EffectType::SAPPED))
      {
        types.insert(RollType::DISADVANTAGE);
      }
    // Vex mastery: the wielder has Advantage on its next attack roll against the vexed target.
    for(const auto &effect : effectTracker.getEffectsByInitiator(attacker))
      {
        if(effect->getEffectType() == EffectType::VEXED && effect->getTarget() == target)
          {
            types.insert(RollType::ADVANTAGE);
            break;
          }
      }
    // Vow of Enmity: the paladin has Advantage on attack rolls against the vowed target.
    for(const auto &effect : effectTracker.getEffectsByInitiator(attacker))
      {
        if(effect->getEffectType() == EffectType::VOW_OF_ENMITY && effect->isAffecting(target))
          {
            types.insert(RollType::ADVANTAGE);
            break;
          }
      }
    // Guiding Bolt: the next attack roll against the lit target has Advantage.
    if(effectTracker.isAffectingCombatant(target, EffectType::GUIDING_BOLT))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // A Hidden attacker (2024 Hide) — or an Invisible one — has Advantage on its attack rolls. The Hidden
    // condition is tracked as a per-target HIDE effect (see EffectTracker::isCombatantHiddenFrom).
    if(attacker->isAffectedBy(Conditions::INVISIBLE) || effectTracker.isCombatantHiddenFrom(attacker, target))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Assassinate (2024 Assassin): the assassin has Advantage on attack rolls against any creature that has
    // not yet taken its turn in the combat. Approximated by the opening round with the assassin acting (higher
    // initiative) before the target.
    if(attacker->hasPassiveAbility(AbilityType::ASSASSINATE) && battleMap.getCombatRound() == 0
       && attacker->getCurrentInit() > target->getCurrentInit())
      {
        types.insert(RollType::ADVANTAGE);
      }
    return types;
  }

  ActionResult ActionResolver::resolveAttack(Attack *attack, Combatant *target, Combatant *attacker)
  {
    auto &battleMap = BattleMap::getInstance();
    AttackFactory &factory = attack->getAttackFactory();
    EffectTracker &effectTracker = EffectTracker::getInstance();

    // Detection of all advantage/disadvantage sources is side-effect-free (see collectAttackRollTypes).
    std::unordered_set<RollType> types = collectAttackRollTypes(attack, target, attacker);

    // The state mutations tied to actually making the attack are applied here, once, on resolution.
    // 2024 Rage duration: making an attack roll against an enemy extends the attacker's own Rage.
    if(Teams::getInstance().areEnemies(*attacker, *target))
      {
        for(const auto &effect : effectTracker.getEffectsByInitiator(attacker))
          {
            if(auto rage = std::dynamic_pointer_cast<Rage>(effect))
              {
                rage->markExtended();
              }
          }
      }
    // Sap mastery: the Disadvantage is consumed by this attack.
    if(effectTracker.isAffectingCombatant(attacker, EffectType::SAPPED))
      {
        effectTracker.removeEffectFromCombatantByType(attacker, EffectType::SAPPED);
      }
    // Vex mastery: the Advantage against this target is consumed by this attack.
    for(const auto &effect : effectTracker.getEffectsByInitiator(attacker))
      {
        if(effect->getEffectType() == EffectType::VEXED && effect->getTarget() == target)
          {
            effectTracker.remove(effect);
            break;
          }
      }
    // Guiding Bolt is consumed by the next attack roll made against the target.
    if(effectTracker.isAffectingCombatant(target, EffectType::GUIDING_BOLT))
      {
        effectTracker.removeEffectFromCombatantByType(target, EffectType::GUIDING_BOLT);
      }
    RollType finalModifier = reconcileRollTypes(types);

    Die d20{1, 20};
    int rolled;
    if(finalModifier == RollType::ADVANTAGE)
      {
        rolled = std::max(rollDice(d20), rollDice(d20));
      }
    else if(finalModifier == RollType::DISADVANTAGE)
      {
        rolled = std::min(rollDice(d20), rollDice(d20));
      }
    else
      {
        rolled = rollDice(d20);
      }

    std::cout << attacker->_name << " attacks " << target->_name << " with " << attack->shorthandStr() << std::endl;

    int multiplier = 1;

    if(rolled == 1)
      {
        std::cout << "Natural 1 rolled!" << std::endl;
        applyGrazeOnMiss(factory, target);
        return ActionResult::MISS;
      }
    else if(rolled >= 21 - factory.getCritRange())
      {
        multiplier = 2;
      }

    for(const auto &bonusDie : attacker->getToHitDiceMods())
      {
        int bonusDiceRoll = rollDice(bonusDie);
        std::cout << "Adding " << bonusDiceRoll << " from bonus " << bonusDie << " to the attack roll" << std::endl;
        rolled += bonusDiceRoll;
      }

    for(const auto &penaltyDie : attacker->getToHitPenaltyDice())
      {
        int penaltyRoll = rollDice(penaltyDie);
        std::cout << "Subtracting " << penaltyRoll << " from penalty " << penaltyDie << " on the attack roll" << std::endl;
        rolled -= penaltyRoll;
      }

    if(rolled + factory.getToHit() >= target->getAC())
      {
        const std::vector<Die> &dmgDice = factory.getDmgDice();
        int dmgDiceSum;
        // Great Weapon Fighting (2024): when rolling damage with a two-handed (or Versatile) melee weapon,
        // treat any 1 or 2 on a weapon damage die as a 3. Only the first (weapon) damage-dice entry gets the
        // floor; trailing entries such as a Battle Master Superiority Die are rolled normally.
        if(factory.isTwoHanded() && attacker->hasPassiveAbility(AbilityType::GREAT_WEAPON_FIGHTING) && !dmgDice.empty())
          {
            dmgDiceSum = rollDiceWithFloor(dmgDice[0], 3);
            if(dmgDice.size() > 1)
              {
                dmgDiceSum += rollDiceMulti(std::vector<Die>(dmgDice.begin() + 1, dmgDice.end()));
              }
          }
        else
          {
            dmgDiceSum = rollDiceMulti(dmgDice);
          }
        int baseDmg = multiplier * dmgDiceSum + factory.getDmgBonus();
        // Rage Damage (and similar flat ability bonuses) apply to Strength-based melee attacks. The flat
        // bonus is added once — it is not doubled on a critical hit.
        if(factory.hasFlag(FactoryFlags::IS_MELEE) && !factory.hasFlag(FactoryFlags::USES_DEX))
          {
            baseDmg += attacker->getAbilityDmgBonus();
          }
        if(baseDmg < 0)
          {
            baseDmg = 0;
          }
        std::cout << "The attack " << (multiplier == 2 ? "CRITS" : "hits") << " " << target->_name << " for " << baseDmg << " damage"
                  << std::endl;
        std::vector<std::pair<int, DamageType>> compoundDmg = {{baseDmg, factory.getDmgType()}};
        // Always-applied extra damage dice carried by the weapon (e.g. a Fire Giant Flame Sword's 3d6 Fire or a
        // Frost Giant Frost Axe's 2d8 Cold). Each entry rolls its own dice, is multiplied on a critical hit like
        // the base dice, and keeps its own damage type so target immunities/resistances apply independently.
        for(const auto &extra : factory.getExtraDmg())
          {
            compoundDmg.emplace_back(multiplier * rollDiceMulti({extra.first}), extra.second);
          }
        attack->setRollType(finalModifier);
        // Armor of Agathys: a creature that hits the warded caster with a melee attack takes Cold damage,
        // provided the caster still has the spell's temporary Hit Points at the moment of the hit. The
        // retaliation amount scales with the (upcast) slot level the spell was cast at, so read it from the
        // active effect instance.
        int agathysRetaliation = 0;
        if(factory.hasFlag(FactoryFlags::IS_MELEE) && target->getTemporaryHp() > 0)
          {
            for(const auto &effect : effectTracker.getAffectingCombatant(target))
              {
                if(auto armor = std::dynamic_pointer_cast<ArmorOfAgathys>(effect))
                  {
                    agathysRetaliation = armor->getRetaliationDamage();
                    break;
                  }
              }
          }
        // Uncanny Dodge (2024 Rogue level 5): a rogue that is hit by an attack it can see may spend its
        // Reaction to halve the damage. Mirrors the Python prompt_after_hit_reaction, which always uses the
        // reaction when available. It must be activated before the damage is applied so doReceiveDmg halves it.
        if(target->hasPassiveAbility(AbilityType::UNCANNY_DODGE) && target->hasReaction()
           && !target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED}))
          {
            std::cout << target->_name << " uses Uncanny Dodge" << std::endl;
            target->setUncannyDodgeActive(true);
            target->setHasReaction(false);
          }
        target->receiveCompoundDmg(compoundDmg, multiplier);
        applyHexDamageOnHit(attacker, target, multiplier);
        battleMap.removeCombatantIfDead(*target);
        if(agathysRetaliation > 0 && attacker->isAlive())
          {
            std::cout << attacker->_name << " takes " << agathysRetaliation << " Cold damage from Armor of Agathys" << std::endl;
            attacker->receiveDmg(agathysRetaliation, DamageType::Cold);
            battleMap.removeCombatantIfDead(*attacker);
          }
        // Apply on-hit riders (e.g. the grapple from a Grab) while the target is still in play.
        if(target->isAlive())
          {
            for(const auto &onHit : factory.getOnHits())
              {
                auto extraDmg = onHit->hit(attacker, attack, target, multiplier, baseDmg);
                if(!extraDmg.empty())
                  {
                    target->receiveCompoundDmg(extraDmg, multiplier);
                    battleMap.removeCombatantIfDead(*target);
                  }
              }
          }
        return ActionResult::HIT;
      }

    std::cout << "The attack misses " << target->_name << std::endl;
    applyGrazeOnMiss(factory, target);
    // Battle Master Riposte: when missed, the target may spend its Reaction and one Superiority Die to make a
    // melee weapon attack against the attacker (mirrors the Python prompt_after_miss_reaction). A Riposte
    // cannot itself provoke another Riposte. A combatant that is Incapacitated, Stunned or Paralyzed cannot
    // take reactions (mirrors Python check_feasibility's Reaction branch).
    if(attack->getAbilityType() != AbilityType::RIPOSTE && target->hasReaction()
       && !target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED})
       && target->hasPassiveAbility(AbilityType::BATTLE_MASTER_MANEUVERS))
      {
        if(AttackFactory *riposteFactory = target->getRiposteFactory())
          {
            auto die = riposteFactory->getResource();
            if(die && (*die)->hasUses() && battleMap.getHopDistanceCombatants(*target, *attacker) <= riposteFactory->getRange())
              {
                auto riposte = riposteFactory->create(attacker);
                resolveAction(riposte, target);
              }
          }
      }
    return ActionResult::MISS;
  }

  ActionResult ActionResolver::resolveRangedSpellAttack(Combatant *caster, int toHit, const Die &dmgDice, DamageType dmgType, Combatant *target, int dmgBonus)
  {
    auto &battleMap = BattleMap::getInstance();

    // Minimal port of resolve_ranged_spell_attack: collect the relevant advantage/disadvantage sources.
    std::unordered_set<RollType> types;
    // Innate Sorcery grants the caster advantage on its own spell attack rolls.
    if(caster->isInnateSorceryActive())
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Attacking a Paralyzed/Restrained/Stunned/Blinded creature is made with advantage.
    if(target->isAffectedByAny({Conditions::PARALYZED, Conditions::RESTRAINED, Conditions::STUNNED, Conditions::BLINDED}))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Ranged spell attacks are made with disadvantage while an enemy is adjacent to the caster.
    if(battleMap.isEnemyAdjacent(*caster))
      {
        types.insert(RollType::DISADVANTAGE);
      }
    if(target->isDodging())
      {
        types.insert(RollType::DISADVANTAGE);
      }
    if(EffectTracker::getInstance().isAffectingCombatant(target, EffectType::GUIDING_BOLT))
      {
        types.insert(RollType::ADVANTAGE);
      }
    RollType finalModifier = reconcileRollTypes(types);

    Die d20{1, 20};
    int rolled;
    if(finalModifier == RollType::ADVANTAGE)
      {
        rolled = std::max(rollDice(d20), rollDice(d20));
      }
    else if(finalModifier == RollType::DISADVANTAGE)
      {
        rolled = std::min(rollDice(d20), rollDice(d20));
      }
    else
      {
        rolled = rollDice(d20);
      }

    std::cout << caster->_name << " rolls a spell attack against " << target->_name;
    if(finalModifier == RollType::ADVANTAGE)
      {
        std::cout << " at advantage";
      }
    else if(finalModifier == RollType::DISADVANTAGE)
      {
        std::cout << " at disadvantage";
      }
    std::cout << std::endl;

    if(rolled == 1)
      {
        std::cout << "Natural 1 rolled!" << std::endl;
        return ActionResult::MISS;
      }
    int multiplier = (rolled == 20) ? 2 : 1;

    for(const auto &bonusDie : caster->getToHitDiceMods())
      {
        int bonusDiceRoll = rollDice(bonusDie);
        std::cout << "Adding " << bonusDiceRoll << " from bonus " << bonusDie << " to the spell attack roll" << std::endl;
        rolled += bonusDiceRoll;
      }

    if(EffectTracker::getInstance().isAffectingCombatant(target, EffectType::GUIDING_BOLT))
      {
        EffectTracker::getInstance().removeEffectFromCombatantByType(target, EffectType::GUIDING_BOLT);
      }

    if(rolled + toHit >= target->getAC())
      {
        int dmg = multiplier * rollDiceMulti({dmgDice}) + dmgBonus;
        if(dmg < 0)
          {
            dmg = 0;
          }
        std::cout << "The spell " << (multiplier == 2 ? "CRITS" : "hits") << " " << target->_name << " for " << dmg << " damage" << std::endl;
        target->receiveDmg(dmg, dmgType, multiplier);
        applyHexDamageOnHit(caster, target, multiplier);
        battleMap.removeCombatantIfDead(*target);
        return ActionResult::HIT;
      }

    std::cout << "The spell misses " << target->_name << std::endl;
    return ActionResult::MISS;
  }

  bool ActionResolver::requestMovement(Combatant *movingCombatant, MovementIncrement *movement)
  {
    auto &battleMap = BattleMap::getInstance();

    if(movement->incursAOO() && !movingCombatant->isDisengaging())
      {
        auto aooCandidates = battleMap.getAooEligibleCombatants(movingCombatant, movement->getIncrement());
        for(auto *candidate : aooCandidates)
          {
            AttackFactory *aooFactory = candidate->getAoOFactory();
            // A combatant that is Incapacitated, Stunned or Paralyzed cannot take reactions (mirrors Python
            // check_feasibility's Reaction branch), so it makes no opportunity attack.
            if(aooFactory && candidate->hasReaction()
               && !candidate->isAffectedByAny({Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED})
               && movingCombatant->isAlive())
              {
                // The reaction is consumed inside resolveAction -> useResources (mirrors Python prompt_aoo,
                // which leaves has_reaction for use_resources to clear). checkFeasibility still sees the
                // reaction as available.
                auto aoo = aooFactory->create(movingCombatant);
                resolveAction(aoo, candidate);
              }
          }
      }

    if(movingCombatant->isAlive())
      {
        battleMap.moveCombatantByIncrement(*movingCombatant, movement->getIncrement());
        return true;
      }
    return false;
  }

  ActionResult ActionResolver::resolveByActoidFlags(const std::shared_ptr<Actoid> &action, Combatant *combatant)
  {
    switch(action->getAbilityType())
      {
      case AbilityType::MELEE_ATTACK:
      case AbilityType::RANGED_ATTACK:
      case AbilityType::SMITE_MELEE_ATTACK:
      case AbilityType::BONUS_MELEE_ATTACK:
      case AbilityType::BONUS_RANGED_ATTACK:
      case AbilityType::HASTE_MELEE_ATTACK:
      case AbilityType::HASTE_RANGED_ATTACK:
      case AbilityType::REACTION_ATTACK:
      case AbilityType::RIPOSTE:
        {
          auto *attack = dynamic_cast<Attack *>(action.get());
          if(!attack)
            {
              return ActionResult::MISS;
            }
          ActionResult result = resolveAttack(attack, &attack->getTarget(), combatant);
          // 2024: making an attack ends the Hidden condition, so the rogue is no longer hidden from anyone
          // once it strikes (the Advantage was already applied to this attack in collectAttackRollTypes).
          EffectTracker::getInstance().removeEffectFromCombatantByType(combatant, EffectType::HIDE);
          return result;
        }

      case AbilityType::RECKLESS_ATTACK:
        {
          auto *attack = dynamic_cast<Attack *>(action.get());
          if(!attack)
            {
              return ActionResult::MISS;
            }
          // Apply the Reckless Attack effect first so that this attack — and, until the barbarian's next
          // turn, attacks against it — are resolved with Advantage.
          if(auto effect = std::dynamic_pointer_cast<Effect>(action))
            {
              EffectTracker::getInstance().add(effect);
              effect->activate();
            }
          std::cout << combatant->_name << " attacks recklessly" << std::endl;
          return resolveAttack(attack, &attack->getTarget(), combatant);
        }

      case AbilityType::STANDARD_MOVEMENT:
      case AbilityType::DISENGAGED_MOVEMENT:
        {
          // 2024: the Grappled (and Restrained) condition sets Speed to 0, so movement is blocked.
          if(combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::RESTRAINED}))
            {
              std::cout << combatant->_name << " can't move (Speed 0 while grappled/restrained)" << std::endl;
              return ActionResult::OTHER;
            }
          auto *movement = dynamic_cast<MovementIncrement *>(action.get());
          if(!movement)
            {
              return ActionResult::MISS;
            }
          if(!requestMovement(combatant, movement))
            {
              return ActionResult::MISS;
            }
          return ActionResult::OTHER;
        }

      case AbilityType::BREAK_GRAPPLE:
        {
          auto *breakGrappleFactory = dynamic_cast<BreakGrappleFactory *>(&action->getFactory());
          if(!breakGrappleFactory)
            {
              return ActionResult::MISS;
            }
          const ConditionWithDC &grapple = breakGrappleFactory->getGrappleCondition();
          // 2024 escape: the Grappled creature uses its action for a Strength (Athletics) or
          // Dexterity (Acrobatics) check against the escape DC, ending the condition on a success.
          int bonus = std::max(combatant->getAthletics(), combatant->getAcrobatics());
          std::cout << combatant->_name << " attempts to escape the grapple (DC " << grapple.dc << ")" << std::endl;
          if(combatant->attemptAbilityCheck(bonus, grapple.dc, RollType::STRAIGHT))
            {
              std::cout << combatant->_name << " breaks free of the grapple" << std::endl;
              if(grapple.initiator != nullptr)
                {
                  grapple.initiator->removeCondition(Conditions::GRAPPLING);
                }
              combatant->breakOutOfGrapple();
            }
          else
            {
              std::cout << combatant->_name << " fails to escape the grapple" << std::endl;
            }
          return ActionResult::OTHER;
        }

      case AbilityType::GET_UP_FROM_PRONE:
        combatant->removeCondition(Conditions::PRONE);
        std::cout << combatant->_name << " gets up from Prone" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::DODGE:
        // Minimal: the defensive effect is not applied yet, but the action is consumed by the planner.
        std::cout << combatant->_name << " takes the " << action->toString() << " action" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::DISENGAGE:
        // The base-action Disengage, like Cunning Action's bonus Disengage, stops the combatant's movement from
        // provoking opportunity attacks this turn. Mirrors the Python Disengage.activate (has_disengaged = True).
        combatant->setDisengaging(true);
        std::cout << combatant->_name << " takes the " << action->toString() << " action" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::HIDE:
      case AbilityType::CUNNING_HIDE:
      case AbilityType::HASTE_HIDE:
        {
          // Hide (2024): the effect rolls the Stealth check and, on success, registers the Hidden condition
          // with the EffectTracker in activate() (see Hide::activate).
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::DASH:
      case AbilityType::CUNNING_DASH:
        // Dashing grants extra movement equal to the combatant's Speed for the current turn.
        combatant->setMovement(combatant->getMovement() + combatant->getSpeed());
        std::cout << combatant->_name << " takes the " << action->toString() << " action" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::CUNNING_DISENGAGE:
        // Disengaging: the combatant's movement no longer provokes opportunity attacks this turn.
        combatant->setDisengaging(true);
        std::cout << combatant->_name << " takes the " << action->toString() << " action" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::LAY_ON_HANDS:
        {
          auto *layOnHands = dynamic_cast<LayOnHands *>(action.get());
          if(!layOnHands)
            {
              return ActionResult::MISS;
            }
          Combatant &target = layOnHands->getTarget();
          if(layOnHands->removesPoison())
            {
              target.removeAllConditionsOfType(Conditions::POISONED);
              std::cout << combatant->_name << " removes Poisoned from " << target._name << " with Lay on Hands" << std::endl;
            }
          else
            {
              int before = target.getCurrentHp();
              target.setCurrentHp(std::min(target.getMaxHp(), target.getCurrentHp() + layOnHands->getHpAmount()));
              std::cout << combatant->_name << " heals " << target._name << " for " << (target.getCurrentHp() - before)
                        << " with Lay on Hands" << std::endl;
            }
          return ActionResult::OTHER;
        }

      case AbilityType::VOW_OF_ENMITY:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " uses " << action->toString() << std::endl;
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::HEX:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Hex registers itself with the EffectTracker and the caster's concentration in activate().
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::ARMOR_OF_AGATHYS:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Armor of Agathys registers itself with the EffectTracker and grants temporary Hit Points in activate().
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::DARKNESS:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Darkness registers itself with the EffectTracker and the caster's concentration in activate().
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::HYPNOTIC_PATTERN:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Hypnotic Pattern only becomes a tracked Concentration effect if at least one creature fails its
          // save; activate() calls setConcentrationEffect() in that case (see Sleep / Faerie Fire).
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::BLINK:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Blink registers itself with the EffectTracker in activate(); the end-of-turn d6 and the
          // start-of-turn return are handled by the effect's turn hooks.
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::FIREBOLT:
      case AbilityType::QUICKENED_FIREBOLT:
        {
          auto *firebolt = dynamic_cast<Firebolt *>(action.get());
          if(!firebolt)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          return resolveRangedSpellAttack(combatant, firebolt->getToHit(), firebolt->getDmgDice(), FireboltFactory::dmgType, &firebolt->getTarget());
        }

      case AbilityType::ELDRITCH_BLAST:
        {
          auto *eldritchBlast = dynamic_cast<EldritchBlast *>(action.get());
          if(!eldritchBlast)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          Combatant *target = &eldritchBlast->getTarget();
          // Each beam is a separate spell attack roll. At level 1 there is a single beam; higher levels add
          // more. The planner concentrates every beam on this target, so stop early once it is defeated.
          ActionResult result = ActionResult::MISS;
          for(int beam = 0; beam < eldritchBlast->getNumBeams(); ++beam)
            {
              if(!target->isAlive())
                {
                  break;
                }
              ActionResult beamResult = resolveRangedSpellAttack(combatant, eldritchBlast->getToHit(), eldritchBlast->getDmgDice(),
                                                                 EldritchBlastFactory::dmgType, target, eldritchBlast->getDmgBonus());
              if(beamResult == ActionResult::HIT)
                {
                  result = ActionResult::HIT;
                  // Eldritch Invocation: Repelling Blast pushes a hit Large-or-smaller target 10 ft (2 cells)
                  // straight away from the caster.
                  if(eldritchBlast->isRepelling() && target->isAlive() && target->getSize() <= Size::LARGE)
                    {
                      auto &battleMap = BattleMap::getInstance();
                      std::cout << combatant->_name << " repels " << target->_name << " away" << std::endl;
                      battleMap.pushCombatantAwayFrom(battleMap.getCombatantCoordinates(*combatant).getCenter(), target, 2);
                    }
                }
            }
          return result;
        }

      case AbilityType::SACRED_FLAME:
        {
          auto *sacredFlame = dynamic_cast<SacredFlame *>(action.get());
          if(!sacredFlame)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          int damage = rollDice(sacredFlame->getDmgDice());
          resolveDmgSavingThrow(SacredFlameFactory::savingThrow, sacredFlame->getDc(), "Sacred Flame", damage, SacredFlameFactory::dmgType,
                                &sacredFlame->getTarget(), /*halfOnSuccess=*/false, /*isSpellEffect=*/true);
          return ActionResult::OTHER;
        }

      case AbilityType::TOLL_THE_DEAD:
        {
          auto *tollTheDead = dynamic_cast<TollTheDead *>(action.get());
          if(!tollTheDead)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          int damage = rollDice(tollTheDead->getDmgDice());
          resolveDmgSavingThrow(TollTheDeadFactory::savingThrow, tollTheDead->getDc(), "Toll the Dead", damage, TollTheDeadFactory::dmgType,
                                &tollTheDead->getTarget(), /*halfOnSuccess=*/false, /*isSpellEffect=*/true);
          return ActionResult::OTHER;
        }

      case AbilityType::VICIOUS_MOCKERY:
        {
          auto *viciousMockery = dynamic_cast<ViciousMockery *>(action.get());
          if(!viciousMockery)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          int damage = rollDice(viciousMockery->getDmgDice());
          bool saved = resolveDmgSavingThrow(ViciousMockeryFactory::savingThrow, viciousMockery->getDc(), "Vicious Mockery", damage,
                                             ViciousMockeryFactory::dmgType, &viciousMockery->getTarget(), /*halfOnSuccess=*/false, /*isSpellEffect=*/true);
          if(!saved)
            {
              // On a failed save the target has Disadvantage on its next attack roll (modeled as Sapped).
              Combatant *target = &viciousMockery->getTarget();
              EffectTracker &effectTracker = EffectTracker::getInstance();
              if(!effectTracker.isAffectingCombatant(target, EffectType::SAPPED))
                {
                  std::cout << target->_name << " has Disadvantage on its next attack roll from Vicious Mockery" << std::endl;
                  auto sapped = std::make_shared<SappedEffect>(target);
                  effectTracker.add(sapped);
                  sapped->activate();
                }
            }
          return ActionResult::OTHER;
        }

      case AbilityType::DISSONANT_WHISPERS:
        {
          auto *dissonantWhispers = dynamic_cast<DissonantWhispers *>(action.get());
          if(!dissonantWhispers)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          int damage = rollDice(dissonantWhispers->getDmgDice());
          bool saved = resolveDmgSavingThrow(DissonantWhispersFactory::savingThrow, dissonantWhispers->getDc(), "Dissonant Whispers", damage,
                                             DissonantWhispersFactory::dmgType, &dissonantWhispers->getTarget(), /*halfOnSuccess=*/true,
                                             /*isSpellEffect=*/true);
          if(!saved)
            {
              // On a failed save the target must immediately use its Reaction, if available, to move as far away as it can.
              Combatant *target = &dissonantWhispers->getTarget();
              if(target->getCurrentHp() > 0 && target->hasReaction())
                {
                  std::cout << target->_name << " uses its Reaction to flee as far as possible from Dissonant Whispers" << std::endl;
                  target->setHasReaction(false);
                  dissonantWhispers->forceFlee(combatant);
                }
            }
          return ActionResult::OTHER;
        }

      case AbilityType::BANE:
      case AbilityType::CHARM_PERSON:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Bane / Charm Person only land on creatures that fail their initial save; activate() registers
          // the effect, so we must not add it unconditionally (see Hold Person).
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::COLOR_SPRAY:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::BARDIC_INSPIRATION:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " grants " << action->toString() << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::CUTTING_WORDS:
        // Reaction: spends a Bardic Inspiration die to weaken a foe's roll. No tracked effect.
        std::cout << combatant->_name << " uses Cutting Words" << std::endl;
        return ActionResult::OTHER;


      case AbilityType::GUIDING_BOLT:
        {
          auto *guidingBolt = dynamic_cast<GuidingBolt *>(action.get());
          if(!guidingBolt)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          ActionResult result = resolveRangedSpellAttack(combatant, guidingBolt->getToHit(), guidingBolt->getDmgDice(), GuidingBoltFactory::dmgType,
                                                         &guidingBolt->getTarget());
          if(result == ActionResult::HIT && guidingBolt->getTarget().isAlive())
            {
              auto effect = std::make_shared<GuidingBoltEffect>(combatant, &guidingBolt->getTarget());
              EffectTracker::getInstance().add(effect);
            }
          return result;
        }

      case AbilityType::STARRY_WISP:
        {
          auto *starryWisp = dynamic_cast<StarryWisp *>(action.get());
          if(!starryWisp)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // On a hit Starry Wisp lights up the target, barring it from benefiting from invisibility.
          ActionResult result = resolveRangedSpellAttack(combatant, starryWisp->getToHit(), starryWisp->getDmgDice(), StarryWispFactory::dmgType,
                                                         &starryWisp->getTarget());
          if(result == ActionResult::HIT && starryWisp->getTarget().isAlive())
            {
              auto effect = std::make_shared<StarryWispEffect>(combatant, &starryWisp->getTarget());
              EffectTracker::getInstance().add(effect);
              effect->activate();
            }
          return result;
        }

      case AbilityType::RAY_OF_FROST:
      case AbilityType::QUICKENED_RAY_OF_FROST:
        {
          auto *rayOfFrost = dynamic_cast<RayOfFrost *>(action.get());
          if(!rayOfFrost)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // On a hit the 2024 Ray of Frost reduces the target's Speed by 10 ft until the caster's next turn.
          ActionResult result = resolveRangedSpellAttack(combatant, rayOfFrost->getToHit(), rayOfFrost->getDmgDice(), RayOfFrostFactory::dmgType,
                                                         &rayOfFrost->getTarget());
          if(result == ActionResult::HIT && rayOfFrost->getTarget().isAlive())
            {
              auto effect = std::make_shared<RayOfFrostEffect>(combatant, &rayOfFrost->getTarget());
              EffectTracker::getInstance().add(effect);
              effect->activate();
            }
          return result;
        }

      case AbilityType::MAGIC_MISSILE:
        {
          auto *magicMissile = dynamic_cast<MagicMissile *>(action.get());
          if(!magicMissile)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          for(auto *target : magicMissile->getTargets())
            {
              if(target != nullptr && target->isAlive())
                {
                  int damage = rollDice(MagicMissileFactory::dmgDice) + MagicMissileFactory::dmgBonus;
                  target->receiveDmg(damage, MagicMissileFactory::dmgType);
                }
            }
          return ActionResult::HIT;
        }

      case AbilityType::MAGE_ARMOR:
      case AbilityType::ARMOR_OF_SHADOWS:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::SLEEP:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Sleep becomes a tracked concentration effect only if at least one creature fails the initial
          // save; activate() calls setConcentrationEffect(), which adds it to the EffectTracker. Adding it
          // here would leave an inert tracked effect when every target saves.
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::SCORCHING_RAY:
      case AbilityType::QUICKENED_SCORCHING_RAY:
        {
          auto *scorchingRay = dynamic_cast<ScorchingRay *>(action.get());
          if(!scorchingRay)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Each ray is a separate spell attack.  All three must always be fired.  If the initial
          // target dies mid-cast, redirect remaining rays to the next eligible enemy so no ray is
          // silently wasted.
          Combatant *target = &scorchingRay->getTarget();
          ScorchingRayFactory &srFactory = dynamic_cast<ScorchingRayFactory &>(scorchingRay->getFactory());
          ActionResult result = ActionResult::MISS;
          for(int ray = 0; ray < ScorchingRay::getNumRays(); ++ray)
            {
              if(!target->isAlive())
                {
                  auto eligibleTargets = srFactory.getEligibleTargets();
                  if(eligibleTargets.empty())
                    {
                      break;
                    }
                  target = eligibleTargets.front();
                }
              ActionResult rayResult =
                  resolveRangedSpellAttack(combatant, scorchingRay->getToHit(), scorchingRay->getDmgDice(), ScorchingRayFactory::dmgType, target);
              if(rayResult == ActionResult::HIT)
                {
                  result = ActionResult::HIT;
                }
            }
          return result;
        }

      case AbilityType::HOLD_PERSON:
      case AbilityType::QUICKENED_HOLD_PERSON:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // Hold Person only takes hold if the target fails its initial save. activate() registers the
          // effect (via setConcentrationEffect) only on a failure, so we must NOT add it to the tracker
          // unconditionally here: doing so leaves a lingering effect that re-rolls the save -- and prints
          // "no longer paralyzed" -- at the end of the target's turns even though the spell never landed.
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::SPIKE_GROWTH:
      case AbilityType::FAERIE_FIRE:
      case AbilityType::BLESS:
      case AbilityType::FLAMING_SPHERE:
      case AbilityType::MOONBEAM:
      case AbilityType::SHIELD_OF_FAITH:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::FLAMING_SPHERE_RAM:
        {
          auto *ram = dynamic_cast<FlamingSphereRam *>(action.get());
          if(!ram)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " rams the Flaming Sphere into " << ram->getTarget()._name << std::endl;
          int damage = rollDiceMulti(ram->getDmgDice());
          resolveDmgSavingThrow(ram->getSavingThrow(), ram->getDc(), "Flaming Sphere", damage, FlamingSphereRamFactory::dmgType, &ram->getTarget(),
                                /*halfOnSuccess=*/true, /*isSpellEffect=*/true);
          ram->getEffect()->moveOrigin(ram->getCoord());
          return ActionResult::OTHER;
        }

      case AbilityType::THUNDERWAVE:
      case AbilityType::QUICKENED_THUNDERWAVE:
        {
          auto *thunderwave = dynamic_cast<Thunderwave *>(action.get());
          if(!thunderwave)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          BattleMap &battleMap = BattleMap::getInstance();
          const ThunderwaveFactory &factory = thunderwave->getThunderwaveFactory();
          std::vector<Combatant *> affected = battleMap.getCombatantsAffectedByBoxAoE(ThunderwaveFactory::target, thunderwave->getCoord());
          int damage = rollDiceMulti(factory.getDmgDice());
          Vector2D origin = battleMap.getCombatantCoordinates(*combatant).getCenter();
          for(auto *aff : affected)
            {
              bool saved = resolveDmgSavingThrow(factory.getSavingThrow(), factory.getDc(), "Thunderwave", damage, ThunderwaveFactory::dmgType, aff,
                                                 /*halfOnSuccess=*/true, /*isSpellEffect=*/true);
              // On a failed save the (surviving) creature is pushed 10 ft (2 cells) away from the caster.
              if(aff->isAlive() && !saved)
                {
                  battleMap.pushCombatantAwayFrom(origin, aff, 2);
                }
            }
          return ActionResult::OTHER;
        }

      case AbilityType::POUNCE:
        {
          auto *pounce = dynamic_cast<Pounce *>(action.get());
          if(!pounce)
            {
              return ActionResult::MISS;
            }
          Combatant *target = pounce->getTarget();
          PounceFactory &factory = pounce->getPounceFactory();
          std::cout << combatant->_name << " pounces on " << (target ? target->_name : std::string("?")) << std::endl;

          // Primary attack: carries the Prone rider (a failed save knocks the target Prone).
          ActionResult result = ActionResult::MISS;
          if(auto *primaryFactory = factory.getPrimaryAttack())
            {
              auto primaryActoid = primaryFactory->create(target);
              if(auto *atk = dynamic_cast<Attack *>(primaryActoid.get()))
                {
                  result = resolveAttack(atk, target, combatant);
                }
            }
          // Bonus-action follow-up: if the target was left Prone (and alive), bite it.
          if(target->isAlive() && target->isAffectedBy(Conditions::PRONE))
            {
              if(auto *secondaryFactory = factory.getSecondaryAttack())
                {
                  auto secondaryActoid = secondaryFactory->create(target);
                  if(auto *atk = dynamic_cast<Attack *>(secondaryActoid.get()))
                    {
                      resolveAttack(atk, target, combatant);
                    }
                }
            }
          return result;
        }

      case AbilityType::ROAR:
        {
          auto *roar = dynamic_cast<Roar *>(action.get());
          if(!roar)
            {
              return ActionResult::MISS;
            }
          RoarFactory &factory = roar->getRoarFactory();
          std::cout << combatant->_name << " roars" << std::endl;
          std::vector<Combatant *> frightened;
          for(auto *enemy : factory.getEligibleTargets())
            {
              // Wisdom save; on a failure the creature is Frightened until the start of the roarer's next turn.
              if(!rollSavingThrow(enemy->getSavingThrow(RoarFactory::savingThrow), factory.getDc(), RollType::STRAIGHT))
                {
                  std::cout << enemy->_name << " is Frightened by the roar" << std::endl;
                  frightened.push_back(enemy);
                }
            }
          if(!frightened.empty())
            {
              auto effect = std::make_shared<RoarFrightenedEffect>(combatant, frightened);
              EffectTracker::getInstance().add(effect);
              effect->activate();
            }
          return ActionResult::OTHER;
        }

      case AbilityType::MOON_WILDSHAPE:
      case AbilityType::WILDSHAPE:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " uses " << action->toString() << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::MISTY_STEP:
        {
          auto *mistyStep = dynamic_cast<MistyStep *>(action.get());
          if(!mistyStep)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          BattleMap::getInstance().moveCombatant(*combatant, mistyStep->getCoord());
          // Refreshing Step (Archfey Steps of the Fey): right after teleporting, the warlock gains 1d10
          // temporary hit points.
          if(combatant->hasPassiveAbility(AbilityType::STEPS_OF_THE_FEY))
            {
              int tempHp = rollDice(Die{1, 10});
              combatant->setTemporaryHp(tempHp);
              std::cout << combatant->_name << " gains " << tempHp << " temporary hit points from Refreshing Step" << std::endl;
            }
          return ActionResult::OTHER;
        }

      case AbilityType::HEALING_WORD:
        {
          auto *healingWord = dynamic_cast<HealingWord *>(action.get());
          if(!healingWord)
            {
              return ActionResult::MISS;
            }
          Combatant &target = healingWord->getTarget();
          int healed = rollDice(healingWord->getHealDice()) + healingWord->getMod();
          target.setCurrentHp(std::min(target.getMaxHp(), target.getCurrentHp() + healed));
          std::cout << combatant->_name << " casts " << action->toString() << " (heals " << healed << ")" << std::endl;
          return ActionResult::OTHER;
        }

      case AbilityType::SECOND_WIND:
        {
          auto *secondWind = dynamic_cast<SecondWind *>(action.get());
          if(!secondWind)
            {
              return ActionResult::MISS;
            }
          Combatant &target = secondWind->getTarget();
          int healed = rollDice(secondWind->getHealDice()) + secondWind->getMod();
          target.setCurrentHp(std::min(target.getMaxHp(), target.getCurrentHp() + healed));
          std::cout << combatant->_name << " uses Second Wind (heals " << healed << ")" << std::endl;
          return ActionResult::OTHER;
        }

      case AbilityType::ACTION_SURGE:
        // Free action: the extra Action was already granted by useResources (setHasAction(true)).
        std::cout << combatant->_name << " uses Action Surge" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::CURE_WOUNDS:
        {
          auto *cureWounds = dynamic_cast<CureWounds *>(action.get());
          if(!cureWounds)
            {
              return ActionResult::MISS;
            }
          Combatant &target = cureWounds->getTarget();
          int healed = rollDice(cureWounds->getHealDice()) + cureWounds->getMod();
          target.setCurrentHp(std::min(target.getMaxHp(), target.getCurrentHp() + healed));
          std::cout << combatant->_name << " casts " << action->toString() << " (heals " << healed << ")" << std::endl;
          return ActionResult::OTHER;
        }

      case AbilityType::SHIELD:
        // Reaction: +5 AC until the start of the caster's next turn.
        std::cout << combatant->_name << " casts Shield" << std::endl;
        combatant->applyShieldSpell();
        return ActionResult::OTHER;

      case AbilityType::RAGE:
        {
          // Bonus action self-buff: grants Rage Damage on Strength melee attacks and Resistance to (at
          // least) Bludgeoning/Piercing/Slashing for its duration, via the Rage effect.
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " enters a Rage (" << action->toString() << ")" << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::INNATE_SORCERY:
        // Bonus action self-buff: grants advantage on the caster's spell attacks for the encounter.
        std::cout << combatant->_name << " channels Innate Sorcery" << std::endl;
        combatant->setInnateSorceryActive(true);
        return ActionResult::OTHER;

      default:
        std::cerr << "resolveByActoidFlags: unhandled action " << action->toString() << " (treating as no-op)" << std::endl;
        return ActionResult::OTHER;
      }
  }

ActionResult ActionResolver::resolveAction(const std::shared_ptr<Actoid>& action, Combatant* combatant) 
{
    // Takes care of possible wildshape
    combatant = combatant->getCurrentForm();

    if (!action) {
        return ActionResult::UNFEASIBLE;
    }

    if (!checkFeasibility(combatant, *action)) {
        auto newAction = handleErrorCase(action, combatant);
        if (!newAction) {
            return ActionResult::UNFEASIBLE;
        }
        useResources(combatant, *newAction);
        return resolveByActoidFlags(newAction, combatant);
    }

    useResources(combatant, *action);
    return resolveByActoidFlags(action, combatant);
}

  void ActionResolver::resolveEffects(const std::unordered_set<std::shared_ptr<Effect>> &effects, Combatant *combatant)
  {
    for(const auto &effect : effects)
      {
        EffectType effectType = effect->getEffectType();

        switch(effectType)
          {
          case EffectType::HASTE:
          case EffectType::TWINNED_HASTE:
            combatant->setMovement(combatant->getSpeed() * 2);
            combatant->setHasHasteAction(true);
            break;

          case EffectType::POST_HASTE_LETHARGY:
            combatant->setMovement(0);
            combatant->setHasAction(false);
            combatant->setHasBonusAction(false);
            combatant->setHasReaction(false);
            break;

          case EffectType::RAGE:
          case EffectType::WILDSHAPE:
          case EffectType::DODGE:
          case EffectType::DISENGAGE:
          case EffectType::RECKLESS_ATTACK:
          case EffectType::FLAMING_SPHERE:
          case EffectType::SPIKE_GROWTH:
          case EffectType::CLOUD_OF_DAGGERS:
          case EffectType::HUNGER_OF_HADAR:
          case EffectType::FAERIE_FIRE:
          case EffectType::HOLD_PERSON:
          case EffectType::DIGESTION:
          case EffectType::BLESS:
          case EffectType::REGENERATION:
          case EffectType::SLEEP:
          case EffectType::MAGE_ARMOR:
          case EffectType::SHIELD_OF_FAITH:
          case EffectType::SHILLELAGH:
          case EffectType::MENACING_ATTACK_FRIGHTENED:
          case EffectType::VOW_OF_ENMITY:
          case EffectType::RAY_OF_FROST:
          case EffectType::STARRY_WISP:
          case EffectType::GUIDING_BOLT:
          case EffectType::PARALYZING_ATTACK_PARALYZED:
          case EffectType::BANE:
          case EffectType::CHARM_PERSON:
          case EffectType::COLOR_SPRAY:
          case EffectType::ARMOR_OF_AGATHYS:
          case EffectType::DARKNESS:
          case EffectType::HYPNOTIC_PATTERN:
          case EffectType::BLINK:
          case EffectType::BARDIC_INSPIRATION:
            // TODO: track if the barbarian attacked or received damage
            break;

          default: std::cerr << "Unknown effect " << static_cast<int>(effectType) << std::endl; break;
          }
      }
  }
  } // namespace enc
