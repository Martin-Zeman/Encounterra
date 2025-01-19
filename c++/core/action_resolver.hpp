#pragma once

#include "core/interfaces.hpp"
#include "core/combatant.hpp"

namespace enc
{
  /**
   * The core of action resolution
   *
   * @param action The action to be resolved
   * @param combatant Initiator of the action
   * @return ActionResult indicating the outcome of the action (HIT/MISS/OTHER/UNFEASIBLE)
   */
  ActionResult resolveAction(const std::shared_ptr<Actoid> &action, Combatant &combatant);
  /**
   * Applies the aspect of effects that need to be reapplied at the beginning of a turn
   * or would otherwise be reset by the new turn.
   *
   * @param effects Set of effects to be applied
   * @param combatant The combatant to apply the effects to
   */
  void resolveEffects(const std::vector<std::weak_ptr<Effect>> &effects, Combatant &combatant);
  void resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant &target,
                             bool halfOnSuccess = false, bool isSpellEffect = false);
  // TODO
  std::shared_ptr<Actoid> handleErrorCase(const std::shared_ptr<Actoid> &action, Combatant &combatant);
  ActionResult resolveByActoidFlags(const std::shared_ptr<Actoid> &action, Combatant &combatant);
  bool hasAdvantageSavingThrow(SavingThrow savingThrow, const Combatant &target, bool isSpellEffect);
  bool hasDisadvantageSavingThrow(SavingThrow savingThrow, const Combatant &target);
}