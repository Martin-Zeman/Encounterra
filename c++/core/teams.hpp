#pragma once

#include <unordered_map>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>
#include "combatant.hpp"
#include "types.hpp"

namespace enc
{

  class Teams
  {
  public:

    static Teams &getInstance()
    {
      static Teams instance;
      return instance;
    }

    void addCombatantToTeam(std::shared_ptr<Combatant> combatant, Color teamColor);

    void replaceCombatant(std::shared_ptr<Combatant>  combatantOld, std::shared_ptr<Combatant>  combatantNew);

    std::string getTeamColorCode(const Combatant& combatant) const;

    Color getTeamColor(const Combatant& combatant) const;

    std::vector<Color> getSurvivingTeams() const;

    std::pair<int, int> getDeathCount() const;

    std::vector<Color> getTeamColors() const;

    bool areAllies(const Combatant& first, const Combatant& second) const;

    bool areEnemies(const Combatant& first, const Combatant& second) const;

    Color getTeam(const Combatant& combatant) const;

    std::vector<std::shared_ptr<Combatant>> getAllies(const Combatant& combatant) const;

    std::vector<std::shared_ptr<Combatant>> getEnemies(const Combatant& combatant) const;

    std::shared_ptr<Combatant> getCombatantById(int id) const;

  private:
    Teams() = default;
    ~Teams() = default;
    Teams(const Teams &) = delete;
    Teams &operator=(const Teams &) = delete;

    std::unordered_map<Color, std::vector<int>> _colorToCombatantIds;
    std::unordered_map<int, Color> _combatantIdToTeamColor;
    std::unordered_map<int, std::shared_ptr<Combatant>> _idToCombatant;

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