#include "actions/attack.hpp"
#include "core/teams.hpp"
#include "core/battle_map.hpp"

namespace enc
{

  AttackFactory::AttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                               int attackRange, int critRange, Uses &&ammo, std::vector<std::unique_ptr<OnHit>> onHit,
                               std::vector<DmgDieWithType> extraDmg, bool usesDex, bool twoHanded, Die toHitBonusDie)
      : DirectThreatFactory(), _name(name), _combatant(combatant), _toHit(toHit), _dmgDice(dmgDice), _dmgBonus(dmgBonus), _dmgType(dmgType),
        _attackRange(attackRange), _shortRange(attackRange / 4), _critRange(critRange), _ammo(std::move(ammo)), _onHit(std::move(onHit)),
        _extraDmg(extraDmg), _usesDex(usesDex), _twoHanded(twoHanded), _toHitBonusDie(toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
    setFlag(FactoryFlags::IS_HASTE_ELIGIBLE_ATTACK);
  }

  AttackFactory::AttackFactory(const AttackFactory &other)
      : DirectThreatFactory(other), _name(other._name), _combatant(other._combatant), _toHit(other._toHit), _dmgDice(other._dmgDice),
        _dmgBonus(other._dmgBonus), _dmgType(other._dmgType), _attackRange(other._attackRange), _shortRange(other._shortRange),
        _critRange(other._critRange), _ammo(other._ammo), _extraDmg(other._extraDmg), _usesDex(other._usesDex), _twoHanded(other._twoHanded),
        _toHitBonusDie(other._toHitBonusDie)
  {
    for(const auto &onHit : other._onHit)
      {
        _onHit.push_back(onHit->clone());
      }
  }

  AttackFactory::AttackFactory(AttackFactory &&other) noexcept
      : DirectThreatFactory(std::move(other)), _name(std::move(other._name)), _combatant(other._combatant), _toHit(other._toHit),
        _dmgDice(std::move(other._dmgDice)), _dmgBonus(other._dmgBonus), _dmgType(other._dmgType), _attackRange(other._attackRange),
        _shortRange(other._shortRange), _critRange(other._critRange), _ammo(std::move(other._ammo)), _onHit(std::move(other._onHit)),
        _extraDmg(std::move(other._extraDmg)), _usesDex(other._usesDex), _twoHanded(other._twoHanded), _toHitBonusDie(other._toHitBonusDie)
  {}

  AttackFactory &AttackFactory::operator=(const AttackFactory &other)
  {
    if(this != &other)
      {
        DirectThreatFactory::operator=(other);
        _name = other._name;
        _combatant = other._combatant;
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
        _name = std::move(other._name);
        _combatant = other._combatant;
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

  std::vector<Combatant *> AttackFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }

    Teams &teams = Teams::getInstance();
    return teams.getAliveNonSwallowedEnemies(*_combatant);
  }

  double AttackFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs)
  {
    bool considerDist = false;
    RollType rollType = RollType::STRAIGHT;

    if(kwargs.find("consider_dist") != kwargs.end())
      {
        considerDist = std::any_cast<bool>(kwargs.at("consider_dist"));
      }
    if(kwargs.find("roll_type") != kwargs.end())
      {
        rollType = std::any_cast<RollType>(kwargs.at("roll_type"));
      }

    int toHitTotal = _toHit;
    toHitTotal += getRollTypeDelta(rollType, std::max(0, std::min(target->getAC() - toHitTotal, 20)));
    if(_toHitBonusDie[0] > 0)
      {
        toHitTotal += avgRoll(_toHitBonusDie);
      }

    if(!considerDist || BattleMap::getInstance().getHopDistanceCombatants(*_combatant, *target) <= _attackRange)
      {
        double acc
          = meanDmg(toHitTotal, _dmgDice, _dmgBonus, target->getAC(), target->isImmuneTo(_dmgType), target->isResistantTo(_dmgType), _critRange);

        for(const auto &extra : _extraDmg)
          {
            acc += meanDmg(toHitTotal, {extra.first}, 0, target->getAC(), target->isImmuneTo(extra.second), target->isResistantTo(extra.second),
                           _critRange);
          }

        for(const auto &oh : _onHit)
          {
            acc += calcPHit(toHitTotal, target->getAC()) * oh->calculateThreat(_combatant, target);
          }

        return acc;
      }

    return 0.0;
  }

  double AttackFactory::calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/)
  {
    //! @todo
    return 0;
  }
  double AttackFactory::calculateMaxThreat()
  {
    //! @todo
    return 0;
  }
}