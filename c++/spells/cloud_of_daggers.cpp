#include "spells/cloud_of_daggers.hpp"

namespace enc
{

  CloudOfDaggersFactory::CloudOfDaggersFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("CloudOfDaggersFactory", "Cloud of Daggers", caster, abilityType), _abilityType(abilityType), _resource(resource),
        _dmgDice({{4, 4}})
  {}

  std::shared_ptr<Actoid> CloudOfDaggersFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<CloudOfDaggers>(*coord, *this);
  }

  std::vector<std::shared_ptr<Actoid>> CloudOfDaggersFactory::createAll(void *previousActionInDag)
  {
    return {}; // TODO
  }

  double CloudOfDaggersFactory::calculateThreatToTarget(const Combatant &target, const Kwargs &kwargs) const
  {
    return 0.0; // TODO
  }
  double CloudOfDaggersFactory::calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const
  {
    return 0.0; // TODO
  }
  double CloudOfDaggersFactory::calculateMaxThreat() const
  {
    return 0.0; // TODO
  }

  CloudOfDaggers::CloudOfDaggers(const Coord &coord, const CloudOfDaggersFactory &factory)
      : Actoid(const_cast<CloudOfDaggersFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType), Effect(factory._combatant),
        LimitedDurationEffect(factory._combatant, 100), SphericAoe(coord, TRANSLATE_RADIUS.at(CloudOfDaggersFactory::target)), _coord(coord),
        _factory(factory)
  {}

  CloudOfDaggers::~CloudOfDaggers() = default;

  std::string CloudOfDaggers::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_CLOUD_OF_DAGGERS) ? "Quickened " : "";
    std::stringstream ss;
    ss << _coord;
    return prefix + "Cloud of Daggers at " + ss.str();
  }

  std::string CloudOfDaggers::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_CLOUD_OF_DAGGERS) ? "Quickened " : "";
    return prefix + "Cloud of Daggers";
  }

  void CloudOfDaggers::activate(const Kwargs &kwargs) { /*TODO*/ }
  void CloudOfDaggers::deactivate() { /*TODO*/ }
  bool CloudOfDaggers::deactivateForCombatant(Combatant &combatant) { return false; /*TODO*/ }
  bool CloudOfDaggers::isAffecting(const Combatant &combatant) const { return false; /*TODO*/ }
  EffectType CloudOfDaggers::getEffectType() const { return EffectType::CLOUD_OF_DAGGERS; }

    std::optional<CoordVector>
  CloudOfDaggers::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    // TODO
    return std::nullopt;
  }

  double CloudOfDaggers::calculateThreat(const Kwargs &kwargs) { return 0.0; /*TODO*/ }
  double CloudOfDaggers::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; /*TODO*/ }

  size_t CloudOfDaggers::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_coord[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool CloudOfDaggers::equals(const Actoid &other) const
  {
    if(auto *cloudOfDaggers = dynamic_cast<const CloudOfDaggers *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _coord == cloudOfDaggers->_coord;
      }
    return false;
  }

} // namespace enc
