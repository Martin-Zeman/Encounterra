#include "teams.hpp"

namespace enc
{

  std::unique_ptr<Teams> Teams::_instance = nullptr;

  Teams &Teams::getInstance()
  {
    if(!_instance)
      {
        _instance = std::unique_ptr<Teams>(new Teams());
      }
    return *_instance;
  }

  void Teams::resetInstance() { _instance.reset(new Teams()); }

  void Teams::addCombatantToTeam(Combatant &combatant, Color teamColor)
  {
    _idToCombatant[combatant._instanceId] = &combatant;
    _combatantIdToTeamColor[combatant._instanceId] = teamColor;
    _colorToCombatantIds[teamColor].push_back(combatant._instanceId);
    combatant.setTeamColor(teamColor);
  }

  void Teams::replaceCombatant(const Combatant &combatantOld, Combatant &combatantNew)
  {
    Color teamColor = _combatantIdToTeamColor[combatantOld._instanceId];
    _combatantIdToTeamColor[combatantNew._instanceId] = teamColor;
    _combatantIdToTeamColor.erase(combatantOld._instanceId);

    auto &teamIds = _colorToCombatantIds[teamColor];
    teamIds.erase(std::remove(teamIds.begin(), teamIds.end(), combatantOld._instanceId), teamIds.end());
    teamIds.push_back(combatantNew._instanceId);

    _idToCombatant.erase(combatantOld._instanceId);
    _idToCombatant[combatantNew._instanceId] = &combatantNew;
  }

  std::string Teams::getTeamColorCode(const Combatant &combatant) const { return toString(_combatantIdToTeamColor.at(combatant._instanceId)); }

  Color Teams::getTeamColor(const Combatant &combatant) const { return _combatantIdToTeamColor.at(combatant._instanceId); }

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
      return combatantIds.size()
             - std::count_if(combatantIds.begin(), combatantIds.end(), [this](int id) { return _idToCombatant.at(id)->isAlive(); });
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

  bool Teams::areAllies(const Combatant &first, const Combatant &second) const
  {
    return _combatantIdToTeamColor.at(first._instanceId) == _combatantIdToTeamColor.at(second._instanceId);
  }

  bool Teams::areEnemies(const Combatant &first, const Combatant &second) const
  {
    return _combatantIdToTeamColor.at(first._instanceId) != _combatantIdToTeamColor.at(second._instanceId);
  }

  Color Teams::getTeam(const Combatant &combatant) const { return _combatantIdToTeamColor.at(combatant._instanceId); }

  std::vector<Combatant *> Teams::getAllies(const Combatant &combatant) const
  {
    std::vector<int> allyIds = _colorToCombatantIds.at(_combatantIdToTeamColor.at(combatant._instanceId));
    std::vector<Combatant *> allies;
    allies.reserve(allyIds.size());
    for(auto id : allyIds)
      {
        allies.push_back(_idToCombatant.at(id));
      }
    return allies;
  }

  std::vector<Combatant *> Teams::getEnemies(const Combatant &combatant) const
  {
    Color otherTeam = (_combatantIdToTeamColor.at(combatant._instanceId) == Color::BLUE) ? Color::RED : Color::BLUE;
    std::vector<int> enemyIds = _colorToCombatantIds.at(otherTeam);
    std::vector<Combatant *> enemies;
    enemies.reserve(enemyIds.size());
    for(auto id : enemyIds)
      {
        enemies.push_back(_idToCombatant.at(id));
      }
    return enemies;
  }

  Combatant *Teams::getCombatantById(int id) const { return _idToCombatant.at(id); }

} // namespace enc
