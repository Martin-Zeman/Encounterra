#pragma once

#include "core/interfaces.hpp"
#include "core/combatant.hpp"

namespace enc
{
  class Attack;
  class MovementIncrement;

  class ActionResolver
  {
  public:
    /**
     * The core of action resolution
     *
     * @param action The action to be resolved
     * @param combatant Initiator of the action
     * @return ActionResult indicating the outcome of the action (HIT/MISS/OTHER/UNFEASIBLE)
     */
    ActionResult resolveAction(const std::shared_ptr<Actoid> &action, Combatant *combatant);
    /**
     * Applies the aspect of effects that need to be reapplied at the beginning of a turn
     * or would otherwise be reset by the new turn.
     *
     * @param effects Set of effects to be applied
     * @param combatant The combatant to apply the effects to
     */
    void resolveEffects(const std::unordered_set<std::shared_ptr<Effect>> &effects, Combatant *combatant);
    /**
     * Collects the advantage/disadvantage sources that apply to a given attack, without mutating any state
     * (no Rage extension, no Sap/Vex consumption). Exposed so the roll-type logic can be verified
     * deterministically in tests, since the d20 RNG itself cannot be seeded.
     *
     * @param attack The attack being made
     * @param target The target of the attack
     * @param attacker The attacker
     * @return The set of RollType modifiers contributed by all sources
     */
    std::unordered_set<RollType> collectAttackRollTypes(Attack *attack, Combatant *target, Combatant *attacker) const;
    // TODO
  private:
    std::shared_ptr<Actoid> handleErrorCase(const std::shared_ptr<Actoid> &action, Combatant *combatant);
    ActionResult resolveByActoidFlags(const std::shared_ptr<Actoid> &action, Combatant *combatant);
    ActionResult resolveAttack(Attack *attack, Combatant *target, Combatant *attacker);
    ActionResult resolveRangedSpellAttack(Combatant *caster, int toHit, const Die &dmgDice, DamageType dmgType, Combatant *target);
    bool requestMovement(Combatant *movingCombatant, MovementIncrement *movement);
  };

  bool hasAdvantageSavingThrow(SavingThrow savingThrow, Combatant *target, bool isSpellEffect);
  bool hasDisadvantageSavingThrow(SavingThrow savingThrow, Combatant *target);
  bool resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant *target,
                             bool halfOnSuccess = false, bool isSpellEffect = false);
}