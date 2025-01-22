#include "actions/attack.hpp"
#include "core/teams.hpp"
#include "core/battle_map.hpp"

namespace enc
{

  AttackFactory::AttackFactory(const std::string &name, const std::string &abilityName, const std::shared_ptr<Combatant> &combatant,
                               AbilityType abilityType, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange,
                               int critRange, Uses &&ammo, std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg,
                               bool usesDex, bool twoHanded, Die toHitBonusDie)
      : DirectThreatFactory(name, abilityName, combatant, abilityType), _toHit(toHit), _dmgDice(dmgDice), _dmgBonus(dmgBonus), _dmgType(dmgType),
        _attackRange(attackRange), _shortRange(attackRange / 4), _critRange(critRange), _ammo(std::move(ammo)), _onHit(std::move(onHit)),
        _extraDmg(extraDmg), _usesDex(usesDex), _twoHanded(twoHanded), _toHitBonusDie(toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
    setFlag(FactoryFlags::IS_HASTE_ELIGIBLE_ATTACK);
  }

  AttackFactory::AttackFactory(const AttackFactory &other)
      : DirectThreatFactory(other), _toHit(other._toHit), _dmgDice(other._dmgDice), _dmgBonus(other._dmgBonus), _dmgType(other._dmgType),
        _attackRange(other._attackRange), _shortRange(other._shortRange), _critRange(other._critRange), _ammo(other._ammo),
        _extraDmg(other._extraDmg), _usesDex(other._usesDex), _twoHanded(other._twoHanded), _toHitBonusDie(other._toHitBonusDie)
  {
    for(const auto &onHit : other._onHit)
      {
        _onHit.push_back(onHit->clone());
      }
  }

  AttackFactory::AttackFactory(AttackFactory &&other) noexcept
      : DirectThreatFactory(std::move(other)), _toHit(other._toHit), _dmgDice(std::move(other._dmgDice)), _dmgBonus(other._dmgBonus),
        _dmgType(other._dmgType), _attackRange(other._attackRange), _shortRange(other._shortRange), _critRange(other._critRange),
        _ammo(std::move(other._ammo)), _onHit(std::move(other._onHit)), _extraDmg(std::move(other._extraDmg)), _usesDex(other._usesDex),
        _twoHanded(other._twoHanded), _toHitBonusDie(other._toHitBonusDie)
  {}

  AttackFactory &AttackFactory::operator=(const AttackFactory &other)
  {
    if(this != &other)
      {
        DirectThreatFactory::operator=(other);
        _toHit = other._toHit;
        _dmgDice = other._dmgDice;
        _dmgBonus = other._dmgBonus;
        _dmgType = other._dmgType;
        _attackRange = other._attackRange;
        _shortRange = other._shortRange;
        _critRange = other._critRange;
        _ammo = other._ammo;
        _extraDmg = other._extraDmg;
        _usesDex = other._usesDex;
        _twoHanded = other._twoHanded;
        _toHitBonusDie = other._toHitBonusDie;

        _onHit.clear();
        for(const auto &onHit : other._onHit)
          {
            _onHit.push_back(onHit->clone());
          }
      }
    return *this;
  }

  AttackFactory &AttackFactory::operator=(AttackFactory &&other) noexcept
  {
    if(this != &other)
      {
        DirectThreatFactory::operator=(std::move(other));
        _toHit = other._toHit;
        _dmgDice = std::move(other._dmgDice);
        _dmgBonus = other._dmgBonus;
        _dmgType = other._dmgType;
        _attackRange = other._attackRange;
        _shortRange = other._shortRange;
        _critRange = other._critRange;
        _ammo = std::move(other._ammo);
        _onHit = std::move(other._onHit);
        _extraDmg = std::move(other._extraDmg);
        _usesDex = other._usesDex;
        _twoHanded = other._twoHanded;
        _toHitBonusDie = other._toHitBonusDie;
      }
    return *this;
  }

  std::vector<std::weak_ptr<Combatant>> AttackFactory::getEligibleTargets() const
  {
    auto combatant = _combatant.lock();
    if(auto swallower = combatant->getSwallowerPtr())
      {
        return {swallower};
      }

    Teams &teams = Teams::getInstance();
    return teams.getAliveNonSwallowedEnemies(*combatant);
  }

  double AttackFactory::calculateThreatToTarget(const Combatant &target, const Kwargs &kwargs) const
  {
    bool considerDist = false;
    RollType rollType = RollType::STRAIGHT;

    if(kwargs.find("considerDist") != kwargs.end())
      {
        considerDist = std::any_cast<bool>(kwargs.at("considerDist"));
      }
    if(kwargs.find("roll_type") != kwargs.end())
      {
        rollType = std::any_cast<RollType>(kwargs.at("roll_type"));
      }

    int toHitTotal = _toHit;
    toHitTotal += getRollTypeDelta(rollType, std::max(0, std::min(target.getAC() - toHitTotal, 20)));
    if(_toHitBonusDie[0] > 0)
      {
        toHitTotal += avgRoll(_toHitBonusDie);
      }

    auto combatant = _combatant.lock();
    if(!considerDist || BattleMap::getInstance().getHopDistanceCombatants(*combatant, target) <= _attackRange)
      {
        double acc
          = meanDmg(toHitTotal, _dmgDice, _dmgBonus, target.getAC(), target.isImmuneTo(_dmgType), target.isResistantTo(_dmgType), _critRange);

        for(const auto &extra : _extraDmg)
          {
            acc += meanDmg(toHitTotal, {extra.first}, 0, target.getAC(), target.isImmuneTo(extra.second), target.isResistantTo(extra.second),
                           _critRange);
          }

        for(const auto &oh : _onHit)
          {
            acc += calcPHit(toHitTotal, target.getAC()) * oh->calculateThreat(*combatant, target);
          }

        return acc;
      }

    return 0.0;
  }

  double AttackFactory::calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const
  {
    double avgToHitBonusDieRoll = 0;
    if(_toHitBonusDie[0] > 0)
      {
        avgToHitBonusDieRoll = avgRoll(_toHitBonusDie);
      }
    double baselineToHit = _toHit + avgToHitBonusDieRoll;
    double baseline
      = meanDmg(baselineToHit, _dmgDice, _dmgBonus, target.getAC(), target.isImmuneTo(_dmgType), target.isResistantTo(_dmgType), _critRange);

    for(const auto &extra : _extraDmg)
      {
        baseline += meanDmg(baselineToHit, {extra.first}, 0, target.getAC(), target.isImmuneTo(extra.second), target.isResistantTo(extra.second),
                            _critRange);
      }

    auto combatant = _combatant.lock();
    for(const auto &oh : _onHit)
      {
        baseline += calcPHit(baselineToHit, target.getAC()) * oh->calculateThreat(*combatant, target);
      }

    int modDmgFlat = modifiers.getOrDefault(ThreatModifierType::DMG_BONUS_FLAT, 0);
    std::vector<Die> modDmgDie = modifiers.getOrDefault(ThreatModifierType::DMG_BONUS_DIE, std::vector<Die>{{0, 0}});
    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    int modCritRange = modifiers.getOrDefault(ThreatModifierType::CRIT_RANGE, 0);
    bool autoCrit = modifiers.getOrDefault(ThreatModifierType::AUTO_CRIT, false);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);

    int totalTargetAC = target.getAC() + targetAC;
    double toHitTotal = std::floor(baselineToHit + modToHitFlat + avgRoll(modToHitDie));

    try
      {
        toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20)));
      }
    catch(const std::out_of_range &)
      {
        // Can happen for extreme differences between the AC and the to_hit
        // The effect is negligible in that case, so we ignore it
      }

    double totalCrit = _critRange + modCritRange;
    totalCrit *= ROLL_TYPE_CRIT_DELTA.at(rollType);
    totalCrit = autoCrit ? 20 : totalCrit;

    double modified;
    try
      {
        std::vector<Die> totalDmgDice = _dmgDice;
        totalDmgDice.insert(totalDmgDice.end(), modDmgDie.begin(), modDmgDie.end());

        modified = meanDmg(toHitTotal, totalDmgDice, _dmgBonus + modDmgFlat, totalTargetAC, target.isImmuneTo(_dmgType),
                           target.isResistantTo(_dmgType), totalCrit);

        for(const auto &extra : _extraDmg)
          {
            modified += meanDmg(toHitTotal, {extra.first}, 0, totalTargetAC, target.isImmuneTo(extra.second), target.isResistantTo(extra.second),
                                totalCrit);
          }

        for(const auto &oh : _onHit)
          {
            modified += calcPHit(toHitTotal, totalTargetAC) * oh->calculateThreat(*combatant, target);
          }
      }
    catch(const std::exception &e)
      {
        std::cerr << "Error in meanDmg of calculateThreatToTargetDelta of AttackFactory: " << e.what() << std::endl;
        modified = baseline;
      }

    return modified - baseline;
  }

  double AttackFactory::calculateMaxThreat() const
  {
    std::vector<std::weak_ptr<Combatant>> targets = getEligibleTargets();

    if(targets.empty())
      {
        return 0.0;
      }

    double maxThreat = std::numeric_limits<double>::lowest();

    for(auto weakTarget : targets)
      {
        if(auto target = weakTarget.lock())
          {
            double threat = calculateThreatToTarget(*target, {});
            if(threat > maxThreat)
              {
                maxThreat = threat;
              }
          }
        return maxThreat;
      }
  }

  std::string Attack::toString() const
  {
    auto combatant = _factory.getCombatant().lock();

    std::string formPrefix;
    if(auto wildshapeForm = combatant->getWildshapePtr())
      {
        formPrefix = wildshapeForm->_name + " ";
      }

    std::string hastedPrefix = (_abilityType > AbilityType::HASTE_ACTION_DELIMITER && _abilityType < AbilityType::PASSIVE_DELIMITER) ? "Hasted " : "";

    return formPrefix + hastedPrefix + _factory._name + " on " + _target._name;
  }

  std::string Attack::shorthandStr() const
  {
    std::string hastedPrefix = (_abilityType > AbilityType::HASTE_ACTION_DELIMITER && _abilityType < AbilityType::PASSIVE_DELIMITER) ? "Hasted " : "";
    return hastedPrefix + _factory._name;
  }

  double Attack::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(_target, kwargs); }

  double Attack::calculateThreatDelta(const ThreatModifiers &modifiers) const { return _factory.calculateThreatToTargetDelta(_target, modifiers); }
  }