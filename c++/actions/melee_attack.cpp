#include "actions/melee_attack.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"

namespace enc
{
  MeleeAttackFactory::MeleeAttackFactory(const std::string &name, const std::string &abilityName, Combatant *combatant, AbilityType abilityType,
                                         int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange,
                                         Uses &&ammo, std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg, bool usesDex,
                                         bool twoHanded, Die toHitBonusDie)
      : AttackFactory(name, abilityName, combatant, abilityType, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo),
                      std::move(onHit), extraDmg, usesDex, twoHanded, toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_MELEE);
  }

  std::vector<Actoid *> MeleeAttackFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<Actoid *> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<MeleeAttack>(AbilityType::MELEE_ATTACK, *target, *this));
      }
    return result;
  }

  Actoid * MeleeAttackFactory::create(void *target) { return std::make_shared<MeleeAttack>(AbilityType::MELEE_ATTACK, *static_cast<Combatant *>(target), *this); }

  std::optional<CoordVector>
  MeleeAttack::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    MeleeAttackFactory &factory = dynamic_cast<MeleeAttackFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();

    auto combatant = factory._combatant;
    if(Combatant *swallower = combatant->getSwallower())
      {
        if(*swallower == _target)
          {
            return CoordVector{battleMap.getCombatantCoordinates(*combatant).getRoot()};
          }
        return {};
      }

    if(!combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInHopRange(battleMap.getCombatantCoordinates(_target).get(), distances, combatant->getSize(),
                                                 factory._attackRange, combatant->_instanceId);
      }
    else if(battleMap.getHopDistanceCombatants(*combatant, _target) <= factory._attackRange)
      {
        return CoordVector{battleMap.getCombatantCoordinates(*combatant).getRoot()};
      }

    return {};
  }

  size_t MeleeAttack::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_target._instanceId) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<std::string>{}(_factory._name) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool MeleeAttack::equals(const Actoid &other) const
  {
    if(auto *meleeAttack = dynamic_cast<const MeleeAttack *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _target._instanceId == meleeAttack->_target._instanceId
               && _factory._name == meleeAttack->_factory._name;
      }
    return false;
  }
}