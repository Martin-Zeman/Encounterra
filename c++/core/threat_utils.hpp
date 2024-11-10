#pragma once

#include <vector>
#include <array>
#include <memory>
#include <unordered_map>
#include "core/misc.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/interfaces.hpp"
#include "effects/aoe_effect.hpp"

namespace enc
{

  constexpr double DZ_CONSTANT = 0.33;
  constexpr double MAX_HP_MODIFIER_MULTIPLIER = 1.25;

  enum class MovementThreatType
  {
    STANDARD,
    DISENGAGED,
    DODGED,
    MISTY_STEPPED
  };

  double dmgIncrementForToHitFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int toHitIncrement, Combatant *target,
                                  DamageType dmgType, int critRange = 1);

  double
  dmgIncrementForDmgFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int dmgIncrement, Combatant *target, DamageType dmgType);

  double dmgDecrementForAcFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int acBonus, Combatant *target, DamageType dmgType,
                               int critRange = 1);

  std::pair<double, double>
  calculateThreatInDelta(Combatant *combatant, int threatRadius, const std::unordered_map<std::string, double> &modifiers, uint32_t factoryFlags);

  std::pair<double, double>
  calculateThreatOutDelta(Combatant *combatant, int threatRadius, const std::unordered_map<std::string, double> &modifiers, uint32_t factoryFlags);

  double calculateAvgThreatIn(Combatant *combatant, int threatRadius, uint32_t factoryFlags);

  double getSavingThrowSuccessProb(int dc, int stBonus);
  double getSavingThrowFailProb(int dc, int stBonus);

  double getDangerZoneThreat(const std::vector<Coord> &coords, Combatant *combatant, int delta = 0);

  double getThreatForStayingAtCoord(const std::vector<Coord> &coords, Combatant *combatant);

  double getAoeAndAooThreatForIncrement(const std::vector<Coord> &currCoordsData, const std::vector<int> &increment, Combatant *combatant,
                                        const std::unordered_map<AoeEffect *, std::vector<Coord>> &effectToCoords, bool disengaged = false,
                                        bool dodged = false);

  std::vector<double>
  accumulateThreatAlongPath(const std::vector<std::vector<int>> &path, Combatant *combatant,
                            const std::unordered_map<AoeEffect *, std::vector<Coord>> &effectToCoords, bool disengaged = false, bool dodged = false);

  std::pair<std::vector<double>, std::vector<std::string>>
  calcThreatForPathWithMistyStep(const std::vector<std::vector<int>> &path, Combatant *combatant,
                                 const std::unordered_map<AoeEffect *, std::vector<Coord>> &effectToCoords);

} // namespace enc