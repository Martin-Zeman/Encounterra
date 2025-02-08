#include "spells/cloud_of_daggers.hpp"

namespace enc
{

  CloudOfDaggersFactory::CloudOfDaggersFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("CloudOfDaggersFactory", "Cloud of Daggers", caster, abilityType), _abilityType(abilityType), _resource(resource),
        _dmgDice({{4, 4}})
  {}

  Actoid * CloudOfDaggersFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return new CloudOfDaggers(*coord, *this);
  }

  std::vector<Actoid *> CloudOfDaggersFactory::createAll(void *previousActionInDag)
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
      : Effect(factory._combatant), // Initialize virtual base first
        Actoid(const_cast<CloudOfDaggersFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
        LimitedDurationEffect(factory._combatant, 100), AoeEffect(factory._combatant),
        AoeSquareEffect(factory._combatant, coord, TRANSLATE_BOX.at(CloudOfDaggersFactory::target)), _factory(factory)
  {}

  CloudOfDaggers::~CloudOfDaggers() = default;

  std::string CloudOfDaggers::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_CLOUD_OF_DAGGERS) ? "Quickened " : "";
    std::stringstream ss;
    ss << _origin;
    return prefix + "Cloud of Daggers at " + ss.str();
  }

  std::string CloudOfDaggers::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_CLOUD_OF_DAGGERS) ? "Quickened " : "";
    return prefix + "Cloud of Daggers";
  }

  void CloudOfDaggers::onStartOfTurn(Combatant &combatant) { /*TODO*/ };
  void CloudOfDaggers::onEndOfTurn(Combatant &combatant) { /*TODO*/ };
  void CloudOfDaggers::onEnter(Combatant &combatant) { /*TODO*/ };
  void CloudOfDaggers::onMoveWithin(Combatant &combatant) { /*TODO*/ };
  void CloudOfDaggers::onExit(Combatant &combatant) { /*TODO*/ };

  double CloudOfDaggers::threatOnEnter(const Combatant &target, const Kwargs &kwargs) const { return avgRoll(_factory._dmgDice); };
  double CloudOfDaggers::threatOnEndOfTurn(const Combatant &target, const Kwargs &kwargs) const { return avgRoll(_factory._dmgDice); };

  void CloudOfDaggers::activate(const Kwargs &kwargs) { /*TODO*/ }
  void CloudOfDaggers::deactivate() { /*TODO*/ }
  bool CloudOfDaggers::deactivateForCombatant(Combatant &combatant) { return false; /*TODO*/ }
  bool CloudOfDaggers::isAffecting(const Combatant &combatant) const { return false; /*TODO*/ }
  EffectType CloudOfDaggers::getEffectType() const { return EffectType::CLOUD_OF_DAGGERS; }

  const CoordVector &CloudOfDaggers::getAffectedCoords() const { return SquareAoe::getAffectedCoords(); }

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
    h ^= std::hash<int>{}(_origin[0]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_origin[1]) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool CloudOfDaggers::equals(const Actoid &other) const
  {
    if(auto *cloudOfDaggers = dynamic_cast<const CloudOfDaggers *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _origin == cloudOfDaggers->_origin;
      }
    return false;
  }

} // namespace enc
