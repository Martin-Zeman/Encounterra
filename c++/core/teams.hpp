#pragma once

#include <unordered_map>
#include <vector>
#include <string>
#include <algorithm>
#include "combatant.hpp"
#include "types.hpp"

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

    bool areAllies(const Combatant& first, const Combatant& second) const;

    bool areEnemies(const Combatant& first, const Combatant& second) const;

    Color getTeam(const Combatant& combatant) const;

    std::vector<Combatant*> getAllies(const Combatant& combatant) const;

    std::vector<Combatant*> getEnemies(const Combatant& combatant) const;

    Combatant* getCombatantById(int id) const;

  private:
    Teams() = default;
    Teams(const Teams &) = delete;
    Teams &operator=(const Teams &) = delete;

    static std::unique_ptr<Teams> _instance;
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