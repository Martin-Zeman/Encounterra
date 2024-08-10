#include "teams.hpp"

namespace enc
{

  void Teams::addCombatantToTeam(std::shared_ptr<Combatant> combatant, Color teamColor)
  {
    _idToCombatant[combatant->_id] = combatant;
    _combatantIdToTeamColor[combatant->_id] = teamColor;
    _colorToCombatantIds[teamColor].push_back(combatant->_id);
    combatant->setTeamColor(teamColor);
  }

  void Teams::replaceCombatant(std::shared_ptr<Combatant>  combatantOld, std::shared_ptr<Combatant>  combatantNew)
  {
    Color teamColor = _combatantIdToTeamColor[combatantOld->_id];
    _combatantIdToTeamColor[combatantNew->_id] = teamColor;
    _combatantIdToTeamColor.erase(combatantOld->_id);

    auto &teamIds = _colorToCombatantIds[teamColor];
    teamIds.erase(std::remove(teamIds.begin(), teamIds.end(), combatantOld->_id), teamIds.end());
    teamIds.push_back(combatantNew->_id);

    _idToCombatant.erase(combatantOld->_id);
    _idToCombatant[combatantNew->_id] = combatantNew;
  }

  std::string Teams::getTeamColorCode(const Combatant& combatant) const { return toString(_combatantIdToTeamColor.at(combatant._id)); }

  Color Teams::getTeamColor(const Combatant& combatant) const { return _combatantIdToTeamColor.at(combatant._id); }

  std::vector<Color> Teams::getSurvivingTeams() const
  {
    std::vector<Color> survivingTeams;
    for(const auto &[color, combatantIds] : _colorToCombatantIds)
      {
        if(std::any_of(combatantIds.begin(), combatantIds.end(), [this](int id) { return _idToCombatant.at(id)->isAlive(); }))
          {
            survivingTeams.push_back(color);
          }
      }
    return survivingTeams;
  }

  std::pair<int, int> Teams::getDeathCount() const
  {
    auto getDeathCountForTeam = [this](Color color) {
      const auto &combatantIds = _colorToCombatantIds.at(color);
      return combatantIds.size() - std::count_if(combatantIds.begin(), combatantIds.end(), [this](int id) { return _idToCombatant.at(id)->isAlive(); });
    };
    return {getDeathCountForTeam(Color::BLUE), getDeathCountForTeam(Color::RED)};
  }

  std::vector<Color> Teams::getTeamColors() const
  {
    std::vector<Color> colors;
    for(const auto &[color, _] : _colorToCombatantIds)
      {
        colors.push_back(color);
      }
    return colors;
  }

  bool Teams::areAllies(const Combatant& first, const Combatant& second) const { return _combatantIdToTeamColor.at(first._id) == _combatantIdToTeamColor.at(second._id); }

  bool Teams::areEnemies(const Combatant& first, const Combatant& second) const { return _combatantIdToTeamColor.at(first._id) != _combatantIdToTeamColor.at(second._id); }

  Color Teams::getTeam(const Combatant& combatant) const { return _combatantIdToTeamColor.at(combatant._id); }

  std::vector<std::shared_ptr<Combatant>> Teams::getAllies(const Combatant& combatant) const
  {
    std::vector<int> allyIds = _colorToCombatantIds.at(_combatantIdToTeamColor.at(combatant._id));
    std::vector<std::shared_ptr<Combatant>> allies;
    allies.reserve(allyIds.size());
    for (auto id : allyIds)
    {
      allies.push_back(_idToCombatant.at(id));
    }
    return allies;
  }

  std::vector<std::shared_ptr<Combatant>> Teams::getEnemies(const Combatant& combatant) const
  {
    Color otherTeam = (_combatantIdToTeamColor.at(combatant._id) == Color::BLUE) ? Color::RED : Color::BLUE;
    std::vector<int> enemyIds = _colorToCombatantIds.at(otherTeam);
    std::vector<std::shared_ptr<Combatant>> enemies;
    enemies.reserve(enemyIds.size());
    for (auto id : enemyIds)
    {
      enemies.push_back(_idToCombatant.at(id));
    }
    return enemies;
  }

  std::shared_ptr<Combatant> Teams::getCombatantById(int id) const { return _idToCombatant.at(id); }

} // namespace enc
