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

    void addCombatantToTeam(const std::shared_ptr<Combatant> &combatant, Color teamColor);

    void replaceCombatant(const Combatant &combatantOld, const Combatant &combatantNew);

    std::string getTeamColorCode(const Combatant &combatant) const;

    Color getTeamColor(const Combatant& combatant) const;

    std::vector<Color> getSurvivingTeams() const;

    std::pair<int, int> getDeathCount() const;

    std::vector<Color> getTeamColors() const;

    bool areAllies(const Combatant &first, const Combatant &second) const;

    bool areEnemies(const Combatant &first, const Combatant &second) const;

    Color getTeam(const Combatant &combatant) const;

    std::vector<std::weak_ptr<Combatant>> getAllAllies(const Combatant &combatant) const;

    std::vector<std::weak_ptr<Combatant>> getAllEnemies(const Combatant &combatant) const;

    std::vector<std::weak_ptr<Combatant>> getAliveEnemies(const Combatant &combatant) const;

    std::vector<std::weak_ptr<Combatant>> getAliveNonSwallowedEnemies(const Combatant &combatant) const;

    std::vector<std::weak_ptr<Combatant>> getAliveNonSwallowedAllies(const Combatant &combatant) const;

    std::vector<std::weak_ptr<Combatant>> getAliveCombatants(const Combatant &excludeCombatant) const;

    std::vector<std::weak_ptr<Combatant>> getAliveAllies(const Combatant &combatant) const;

    std::weak_ptr<Combatant> getCombatantById(int id) const;

  private:
    Teams() = default;
    Teams(const Teams &) = delete;
    Teams &operator=(const Teams &) = delete;

    static std::unique_ptr<Teams> _instance;
    std::unordered_map<Color, std::vector<int>> _colorToCombatantIds;
    std::unordered_map<int, Color> _combatantIdToTeamColor;
    std::unordered_map<int, std::weak_ptr<Combatant>> _idToCombatant;

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