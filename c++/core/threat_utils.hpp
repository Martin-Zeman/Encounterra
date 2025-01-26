#pragma once

#include <vector>
#include <array>
#include <memory>
#include <unordered_map>
#include "core/misc.hpp"
#include "core/coords.hpp"
#include "core/battle_map.hpp"
#include "core/interfaces.hpp"
#include "core/types.hpp"
#include "effects/aoe_effect.hpp"

namespace enc
{

  class Combatant;

  constexpr double DZ_CONSTANT = 0.33;
  constexpr double MAX_HP_MODIFIER_MULTIPLIER = 1.25;

  struct PathSearchResult
  {
    std::vector<double> threat;
    CoordVector path;
  };

  struct StateIdPairHash
  {
    size_t operator()(const std::pair<StateId, StateId> &p) const
    {
      size_t h1 = std::hash<StateId>{}(p.first);
      size_t h2 = std::hash<StateId>{}(p.second);
      return h1 ^ (h2 << 1);
    }
  };

  /**
   *  Calculates the increase in mean dmg for an attack-like ability using a flat to-hit bonus
      @param toHit: to hit bonus
      @param dmgDice: damage dice in a string form
      @param dmgBonus: bonus to damage
      @param ac: target's AC
      @param toHitIncrement:
      @param target:
      @param dmgType:
      @param critRange:
      @return: mean damage increment not accounting for critical failures
   */
  double dmgIncrementForToHitFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int toHitIncrement, const Combatant &target,
                                  DamageType dmgType, int critRange = 1);

/**
 * Calculates the increase in mean dmg for an attack-like ability using a flat damage bonus
    @param toHit: to hit bonus
    @param dmgDice: damage dice in a string form
    @param dmgBonus: bonus to damage
    @param ac: target's AC
    @param dmgIncrement:
    @param target:
    @param dmgType:
    @return: mean damage increment not accounting for critical failures
 */
  double
  dmgIncrementForDmgFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int dmgIncrement, const Combatant &target, DamageType dmgType);

  /**
   *  Calculates the decrease in mean dmg received for an attack-like ability using a flat AC bonus
      @param toHit: to hit bonus
      @param dmgDice: damage dice in a string form
      @param dmgBonus: bonus to damage
      @param ac: target's AC
      @param acBonus: bonus to target's AC
      @param target:
      @param dmgType:
      @param critRange:
      @return: mean damage decrement not accounting for critical failures (positive value)
   */
  double dmgDecrementForAcFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int acBonus, const Combatant &target, DamageType dmgType,
                               int critRange = 1);

  // std::vector<std::shared_ptr<DirectThreatFactory>> getDirectThreatFactories(const std::vector<std::shared_ptr<ActoidFactory>> &factories);

  /**
   *  Estimates the change in mean dmg from enemies within radius assuming they'd all attack the combatant given a dictionary of modifiers.
      This is a simplification. It doesn't take into account that action, bonus action and haste actions might all be combined.
      At the same time, combining them blindly with no respect for feasibility is probably even worse.
      @param combatant: the potential receiver of the dmg
      @param threatRadius: radius within which enemies are to be considered
      @param modifiers: dictionary of modifiers
      @param factoryFlags: the kind of factory which is relevant for this calculation(e.g. attacks only or any direct threat...)
      @return: estimated change in dmg, negative for advantage, positive for disadvantage
   */
  std::pair<double, double>
  calculateThreatInDelta(const Combatant &combatant, int threatRadius, const ThreatModifiers &modifiers, uint32_t factoryFlags);

  /**
   *  Estimates the change in mean dmg to enemies within radius assuming the best delta will be picked given a dictionary of modifiers
      @param combatant: the attacker
      @param threatRadius: radius within which enemies are to be considered
      @param modifiers: dictionary of modifiers
      @param factoryFlags: the kind of factory which is relevant for this calculation(e.g. attacks only or any direct threat...)
      @return: estimated change in dmg, negative for advantage, positive for disadvantage
   */
  std::pair<double, double>
  calculateThreatOutDelta(const Combatant &combatant, int threatRadius, const ThreatModifiers &modifiers, uint32_t factoryFlags);

  /**
   *  Estimates the mean dmg from enemies within radius they'd all attack the combatant
      @param combatant: the potential receiver of the dmg
      @param threatRadius: radius within which enemies are to be considered
      @param factoryFlags: the kind of factory which is relevant for this calculation(e.g. attacks only or any direct threat...)
      @return: estimated change in dmg, negative for advantage, positive for disadvantage
   */
  double calculateAvgThreatIn(const Combatant &combatant, int threatRadius, uint32_t factoryFlags);

  /**
   *  Calculates the probability of a successful saving throw given the DC and the ST bonus
      @param dc: DC
      @param stBonus: respective saving throw bonus
      @return:
   */
  double getSavingThrowSuccessProb(int dc, int stBonus);

  /**
   *
   * Calculates the probability of a saving throw failure given the DC and the ST bonus
    @param dc: DC
    @param stBonus: respective saving throw bonus
    @return:
   */
  double getSavingThrowFailProb(int dc, int stBonus);

/**
 *  Adds potential threat projected by the virtue of being near an enemy. It adds up all the projected threat for all
    enemies within their projection range.
    move.
    @param coords: as np.array of size nx2 where n is the number of coords the combatant takes up
    @param combatant:
    @param delta: to be added to the distance to enemies, used for dash threat calculation
    @return: danger zone threat (positive)
 */
  double getDangerZoneThreat(const Coords &coords, const Combatant &combatant, int delta = 0);

  /**
   *  Estimates te threat associated with staying at a coordinate. This is really an estimate since the character may still
      move.
      @param coords: as np.array of size nx2 where n is the number of coords the combatant takes up
      @param combatant:
      @return: estimated threat (positive)
   */
  double getThreatForStayingAtCoord(const Coords &coords, const Combatant &combatant);

  /**
   *
      A helper caching function which accumulates threats from AoE and AoO along a path.
      Caution: get_aoe_and_aoo_threat_for_increment uses a global cache which may need to be cleared!
      @param currCoordsData: current coordinate as np.array
      @param increment: the current coordinate increment
      @param combatant: the moving combatant
      @param effectToCoords: mapping of AoE effects to their coordinates
      @param disengaged: If True then don't include the AoOs
      @return: accumulated threat (negative)
   */
  double getAoeAndAooThreatForIncrement(const CoordVector &currCoordsData, const Coord &increment, const Combatant &combatant,
                                        const std::unordered_map<AoeEffect*, CoordVector> &effectToCoords, bool disengaged = false,
                                        bool dodged = false);

  /**
   *  Accumulates threats along a path. Also takes into account the threat associated with ending/starting a turn
      at the final destination. Caution: get_aoe_and_aoo_threat_for_increment uses a global cache which may need to be cleared!
      @param path: path as a sequence of np.array coordinates
      @param combatant: the moving combatant
      @param effectToCoords: mapping of AoE effects to their coordinates
      @param disengaged: If True then don't include the AoOs
      @param dodged: If True then attacks at the moving combatant are calculated at a disadvantage
      @return: tuple of cumulative threats along the path
   */
  std::vector<double> accumulateThreatAlongPath(const CoordVector &path, Combatant &combatant,
                                                const std::unordered_map<AoeEffect*, CoordVector> &effectToCoords,
                                                bool disengaged = false, bool dodged = false);

  /**
   *  Accumulates threats along a path. Also takes into account the threat associated with ending/starting a turn
      at the final destination. Caution: get_aoe_and_aoo_threat_for_increment uses a global cache which may need to be cleared!
      @param path: path as a sequence of np.array coordinates
      @param combatant: the moving combatant
      @param effectToCoords: mapping of AoE effects to their coordinates
      @return: accumulated threat (negative)
   */
  PathSearchResult calcThreatForPathWithMistyStep(const CoordVector &path, const Combatant &combatant,
                                                  const std::unordered_map<AoeEffect*, CoordVector> &effectToCoords);

} // namespace enc
