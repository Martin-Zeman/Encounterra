#pragma once

#include <unordered_map>
#include <vector>
#include <string>
#include <algorithm>
#include "core/combatant.hpp"
#include "core/types.hpp"

namespace enc
{

  class Teams
  {
  public:

    static Teams &getInstance();

    ~Teams() = default;

    static void resetInstance();

    void addCombatantToTeam(Combatant& combatant, Color teamColor);

    void replaceCombatant(const Combatant& combatantOld, Combatant& combatantNew);

    std::string getTeamColorCode(const Combatant& combatant) const;

    Color getTeamColor(const Combatant& combatant) const;

    std::vector<Color> getSurvivingTeams() const;

    std::pair<int, int> getDeathCount() const;

    std::vector<Color> getTeamColors() const;

    bool areAllies(const Combatant &first, const Combatant &second) const;

    bool areEnemies(const Combatant &first, const Combatant &second) const;

    Color getTeam(const Combatant &combatant) const;

    std::vector<Combatant *> getAllAllies(const Combatant &combatant) const;

    std::vector<Combatant *> getAllEnemies(const Combatant &combatant) const;

    std::vector<Combatant *> getAliveEnemies(const Combatant &combatant) const;

    std::vector<Combatant *> getAliveNonSwallowedEnemies(const Combatant &combatant) const;

    std::vector<Combatant *> getAliveNonSwallowedAllies(const Combatant &combatant) const;

    std::vector<Combatant *> getAliveCombatants(const Combatant *excludeCombatant) const;

    std::vector<Combatant *> getAliveAllies(const Combatant &combatant) const;

    Combatant *getCombatantById(int id) const;

  private:
    Teams() = default;
    Teams(const Teams &) = delete;
    Teams &operator=(const Teams &) = delete;

    // thread_local: each worker thread gets its own independent Teams so simulations can run in
    // parallel without sharing the (mutable, non-thread-safe) singleton state.
    static thread_local std::unique_ptr<Teams> _instance;
    std::unordered_map<Color, std::vector<int>> _colorToCombatantIds;
    std::unordered_map<int, Color> _combatantIdToTeamColor;
    std::unordered_map<int, Combatant*> _idToCombatant;

    static std::string toString(Color color)
    {
      switch(color)
        {
        case Color::BLUE: return "\x1b[38;5;39m";
        case Color::RED: return "\x1b[38;5;196m";
        default: return "";
        }
    }
  };
}