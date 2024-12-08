#include "combatant.hpp"
#include "actions/dodge.hpp"
#include "actions/disengage.hpp"
#include "core/rechargeable_factory.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{

  Combatant::Combatant(CombatantType type, SubType subtype, int level, std::string name, int hp, int ac, int initBonus, int spellToHit, int speed,
                       int dc, std::unordered_set<DamageType> resistances, std::unordered_set<DamageType> immunities,
                       std::unordered_set<DamageType> vulnerabities, Conditions conditionImmunities)
      : _name(name), _maxHp(hp), _currHp(hp), _ac(ac), _dc(dc), _initBonus(initBonus), _spellToHit(spellToHit), _speed(speed / 5),
        _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities),
        _conditionImmunities(conditionImmunities), _type(type), _subtype(subtype), _level(level)
  {
    _dodgeFactory = std::make_shared<DodgeFactory>(this);
    _disengageFactory = std::make_shared<DisengageFactory>(this);
    _actionFactories.push_back(_dodgeFactory);
    _actionFactories.push_back(_disengageFactory);
  }

  // Combatant::Combatant(std::string name, int hp, int ac, int initBonus, int spellToHit, int speed, int dc,
  //                      std::unordered_set<DamageType> resistances = {}, std::unordered_set<DamageType> immunities = {},
  //                      std::unordered_set<DamageType> vulnerabities = {})
  //     : _name(name), _maxHp(hp), _currHp(hp), _ac(ac), _dc(dc), _initBonus(initBonus), _spellToHit(spellToHit), _speed(speed / 5),
  //       _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities)
  // {
  //   _dodgeFactory = std::make_shared<DodgeFactory>();
  //   _disengageFactory = std::make_shared<DisengageFactory>();
  //   _actionFactories = {_dodgeFactory, _disengageFactory};
  // }

  std::string Combatant::toString() const { return _name; }

  bool Combatant::isAlive() const { return _currHp > 0; }

  void Combatant::onDie()
  {
    // Implement functionality here...
  }

  void Combatant::onEndOfTurn() { _dmgTypesTookLastRound.clear(); }

  void Combatant::rollInitiative()
  {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> distrib(1, 20);
    _currInit = distrib(gen) + _initBonus;
  }

  void Combatant::reset() {
        _hasAction = true;
        _hasBonusAction = true;
        _hasReaction = true;
        _currHp = _maxHp;
        _movement = _speed;
        _isDodging = false;
        if (_spellslots)
        {
            _spellslots->reset();
        }
        for (auto& r : _resources)
        {
          r.second.reset();
        }
        _alreadyUsedSpellslotThisTurn = false;
        if(_isShieldSpellActive)
        {
            _ac -= 5;
        }
        _isShieldSpellActive = false;
        _conditions.clear();
        _dcConditions.clear();
        breakConcentration();
        _hasHasteAction = false;
        clearAllSavingThrowMods();
        for (auto& ammo : _ammo)
        {
          ammo.second.reset();
        }
        _oneTimeAcbonus = 0 ; // Not really needed
        _actionPlan.clear();
        _weaponDmgDealtThisTurn = 0;
  }

  void Combatant::newTurn() {
        _hasAction = true;
        _hasBonusAction = true;
        _hasReaction = true;
        _movement = _speed;
        // if (_isDodging)
        // {
        //     saving_throws_roll_type_mod[SavingThrow.DEX].add(RollType.STRAIGHT)
        // }
        // _isDodging = false # The effect tracker should be taking care of this
        _alreadyUsedSpellslotThisTurn = false;
        if (_isShieldSpellActive){
            _ac -= 5;
        }
        _isShieldSpellActive = false;
        _hasHasteAction = false;
        _attackFsm.reset();
        _actionPlan.clear();
        if (_constrictedTarget != nullptr && !_constrictedTarget->isAlive()){
            _constrictedTarget = nullptr;
            }
        _weaponDmgDealtThisTurn = 0;
  }

  Combatant *Combatant::getCurrentForm() { return _currentWildshapeForm == nullptr ? _originalForm : _currentWildshapeForm; }
  Combatant *Combatant::getOriginalForm() { return _originalForm; }

  bool Combatant::isAffectedBy(Conditions condition) const
  {
    return std::any_of(_conditions.begin(), _conditions.end(), [condition](const Condition &c) { return containsCondition(c.conditionComposite, condition); })
           || std::any_of(_dcConditions.begin(), _dcConditions.end(),
                          [condition](const ConditionWithDC &c) { return containsCondition(c.conditionComposite, condition); });
  }

  bool Combatant::isImmuneTo(DamageType dmgType) { return _immunities.find(dmgType) != _immunities.end(); }
  
  bool Combatant::isResistantTo(DamageType dmgType) { return _resistances.find(dmgType) != _resistances.end(); }

  bool Combatant::isVulnerableTo(DamageType dmgType) { return _vulnerabities.find(dmgType) != _vulnerabities.end(); }

  bool Combatant::hasPassiveAbility(AbilityType ability) const{
    return _passiveAbilities.contains(ability);
  }

  void Combatant::applyCondition(const Condition &condition)
  {
    _conditions.push_back(condition);
    if(containsCondition(condition.conditionComposite, Conditions::SWALLOWED))
      {
        _swallower = condition.initiator;
      }
  }

  void Combatant::applyDCCondition(const ConditionWithDC &dcCondition)
  {
    _dcConditions.push_back(dcCondition);
    if(containsCondition(dcCondition.conditionComposite, Conditions::SWALLOWED))
      {
        _swallower = dcCondition.initiator;
      }
  }

  bool Combatant::removeCondition(Conditions condition, const Combatant *initiator)
  {
    auto it = std::find_if(_conditions.begin(), _conditions.end(), [condition, initiator](const Condition &c) {
      return containsCondition(c.conditionComposite, condition) && (!initiator || c.initiator == initiator);
    });
    if(it != _conditions.end())
      {
        _conditions.erase(it);
        if(condition == Conditions::SWALLOWED)
          {
            _swallower = nullptr;
          }
        return true;
      }
    return false;
  }

  bool Combatant::removeDCCondition(Conditions condition, const Combatant *initiator)
  {
    auto it = std::find_if(_dcConditions.begin(), _dcConditions.end(), [condition, initiator](const ConditionWithDC &c) {
      return containsCondition(c.conditionComposite, condition) && (!initiator || c.initiator == initiator);
    });
    if(it != _dcConditions.end())
      {
        _dcConditions.erase(it);
        if(condition == Conditions::SWALLOWED)
          {
            _swallower = nullptr;
          }
        return true;
      }
    return false;
  }

  void Combatant::removeAllConditionsOfType(Conditions condition)
  {
    while(removeDCCondition(condition)) {};
    while(removeCondition(condition)) {};
  }

  Combatant *Combatant::getInitiatorOfCondition(Conditions condition)
  {
    auto initiator = checkConditionList(_dcConditions, condition);
    if(initiator)
      {
        return initiator;
      }

    return checkConditionList(_conditions, condition);
  }

  Combatant *Combatant::getGrappledTarget()
  {
    for(const auto &cond : _dcConditions)
      {
        if(containsCondition(cond.conditionComposite, Conditions::GRAPPLING) && cond.target.has_value())
          {
            return cond.target.value();
          }
      }
    for(const auto &cond : _conditions)
      {
        if(containsCondition(cond.conditionComposite, Conditions::GRAPPLING) && cond.target.has_value())
          {
            return cond.target.value();
          }
      }

    return nullptr;
  }

  std::optional<ConditionWithDC> Combatant::needsToBreakOutOfGrapple()
  {
    for(const auto &dcCond : _dcConditions)
      {
        if(containsCondition(dcCond.conditionComposite, Conditions::GRAPPLED) && dcCond.phase == PhaseOfTurn::ACTION)
          {
            return dcCond;
          }
      }
    return std::nullopt;
  }

  void Combatant::breakOutOfGrapple()
  {
    auto it = std::find_if(_dcConditions.begin(), _dcConditions.end(), [](const ConditionWithDC &cond) {
      return containsCondition(cond.conditionComposite, Conditions::GRAPPLED) && cond.phase == PhaseOfTurn::ACTION;
    });
    if(it != _dcConditions.end())
      {
        _dcConditions.erase(it);
      }
  }

  void Combatant::setConcentrationEffect(std::shared_ptr<Effect> effect)
  {
    breakConcentration(); // Break existing concentration if any

    // Store weak_ptr to avoid circular reference
    _concentrationEffect = EffectTracker::getInstance().add(effect);

    // Also set concentration for original form if in wildshape
    if(_currentWildshapeForm != nullptr && _originalForm != this)
      {
        _originalForm->_concentrationEffect = _concentrationEffect;
      }
  }

  void Combatant::breakConcentration()
  {
    if(auto effect = _concentrationEffect.lock())
      {
        EffectTracker::getInstance().remove(effect);
      }
    _concentrationEffect.reset();

    // Also break concentration for original form if in wildshape
    if(_currentWildshapeForm != nullptr && _originalForm != this)
      {
        _originalForm->_concentrationEffect.reset();
      }
  }

  bool Combatant::isConcentrating() const { return !_concentrationEffect.expired(); }

  bool Combatant::isAffectedByAny(const std::vector<Conditions> &conditions) const
  {
    for(const auto &condition : conditions)
      {
        if(isAffectedBy(condition))
          {
            return true;
          }
      }
    return false;
  }

  std::weak_ptr<ActoidFactory> Combatant::getActionFactory(AbilityType type)
    {
        for (auto& factory : _actionFactories)
        {
            if (factory->getAbilityType() == type)
            {
                return std::weak_ptr<ActoidFactory>(factory);
            }
        }
        return std::weak_ptr<ActoidFactory>();
    }

    void Combatant::rollForRecharge()
    {
      for(auto &factory : _actionFactories)
        {
          if(factory->hasFlag(FactoryFlags::IS_RECHARGE))
            {
              static_cast<RechargeableFactory *>(factory.get())->rollForRecharge();
            }
        }

      for(auto &factory : _bonusActionFactories)
        {
          if(factory->hasFlag(FactoryFlags::IS_RECHARGE))
            {
              static_cast<RechargeableFactory *>(factory.get())->rollForRecharge();
            }
        }
    }

    const std::vector<int> &Combatant::getSavingThrowFlatMods(SavingThrow type) const
    {
      auto it = _savingThrowsFlatMod.find(type);
      static const std::vector<int> empty;
      return it != _savingThrowsFlatMod.end() ? it->second : empty;
    }

    void Combatant::addSavingThrowFlatMod(SavingThrow type, int mod) { _savingThrowsFlatMod[type].push_back(mod); }

    void Combatant::clearSavingThrowFlatMods(SavingThrow type) { _savingThrowsFlatMod[type].clear(); }

    const std::vector<Die> &Combatant::getSavingThrowDiceMods(SavingThrow type) const
    {
      auto it = _savingThrowsDiceMod.find(type);
      static const std::vector<Die> empty;
      return it != _savingThrowsDiceMod.end() ? it->second : empty;
    }

    void Combatant::addSavingThrowDiceMod(SavingThrow type, const Die &mod) { _savingThrowsDiceMod[type].push_back(mod); }

    void Combatant::clearSavingThrowDiceMods(SavingThrow type) { _savingThrowsDiceMod[type].clear(); }

    const std::unordered_set<RollType> &Combatant::getSavingThrowRollTypeMods(SavingThrow type) const
    {
      auto it = _savingThrowsRollTypeMod.find(type);
      static const std::unordered_set<RollType> empty;
      return it != _savingThrowsRollTypeMod.end() ? it->second : empty;
    }

    void Combatant::addSavingThrowRollTypeMod(SavingThrow type, RollType rollType) { _savingThrowsRollTypeMod[type].insert(rollType); }

    void Combatant::removeSavingThrowRollTypeMod(SavingThrow type, RollType rollType)
    {
      auto it = _savingThrowsRollTypeMod.find(type);
      if(it != _savingThrowsRollTypeMod.end())
        {
          it->second.erase(rollType);
        }
    }

    void Combatant::clearSavingThrowRollTypeMods(SavingThrow type) { _savingThrowsRollTypeMod[type].clear(); }

    void Combatant::clearAllSavingThrowMods()
    {
      _savingThrowsFlatMod.clear();
      _savingThrowsDiceMod.clear();
      _savingThrowsRollTypeMod.clear();
    }

    // Private helper for damage calculations
int Combatant::doReceiveDmg(int dmg, DamageType dmgType) {
    // Check immunities first
    if (_immunities.find(dmgType) != _immunities.end()) {
        std::cout << _name << " is immune to " << DAMAGE_TYPE_TO_STRING.at(dmgType) << " and reduces the damage to 0" << std::endl;
        return 0;
    }
    
    // Check resistances
    if (_resistances.find(dmgType) != _resistances.end()) {
        dmg = std::floor(dmg / 2);
        std::cout << _name <<" is resistant to " << DAMAGE_TYPE_TO_STRING.at(dmgType) << " and reduces the damage to " << dmg << std::endl;
    }
    
    // Check vulnerabilities
    if (_vulnerabities.find(dmgType) != _vulnerabities.end()) {
        dmg *= 2;
        std::cout << _name << " is vulnerable to " << DAMAGE_TYPE_TO_STRING.at(dmgType) << " which doubles the damage to " << dmg << std::endl;
    }

    // Apply uncanny dodge if active
    if (_uncannyDodgeActive) {
        dmg = std::floor(dmg / 2);
        std::cout << _name << " uses Uncanny Dodge which reduces the damage to " << dmg << std::endl;
    }
    
    assert(_temporaryHp >= 0);
    _temporaryHp -= dmg;
    
    if (_temporaryHp < 0) {
        _currHp += _temporaryHp;
        _temporaryHp = 0;
    }
    
    _dmgTypesTookLastRound.insert(dmgType);
    return dmg;
}

// Main damage receiving function
int Combatant::receiveDmg(int dmg, DamageType dmg_type, int multiplier) {
    dmg = doReceiveDmg(dmg, dmg_type);
    
    // Undead Fortitude check
    if (_currHp <= 0 && hasPassiveAbility(AbilityType::UNDEAD_FORTITUDE) && 
        multiplier == 1 && dmg_type != DamageType::Radiant) {
        
        std::vector<RollType> rollTypes(_savingThrowsRollTypeMod[SavingThrow::CON].begin(),
                                      _savingThrowsRollTypeMod[SavingThrow::CON].end());
        bool saved = rollSavingThrow(_savingThrows.at(SavingThrow::CON), 
                                     5 + dmg, 
                                     reconcileRollTypes(_savingThrowsRollTypeMod[SavingThrow::CON]));
        if (saved) {
            _currHp = 1;
            std::cout << "Instead of dying, " << _name << " drops to 1 HP thanks to Undead Fortitude" << std::endl;
        }
    }

    // Handle wildshape damage overflow
    if (_currHp <= 0 && getOriginalForm() != this) {
        getOriginalForm()->_currHp += _currHp;  // Carry-over damage
        EffectTracker::getInstance().removeEffectFromCombatantByType(getOriginalForm(), EffectType::WILDSHAPE);
    }

    // Handle effects of taking damage
    if (dmg > 0) {
        checkConcentration(this, dmg);
        
        if (isAffectedBy(Conditions::AWAKENED_BY_DMG)) {
            std::cout << _name << " is awakened by taking damage" << std::endl;
            removeCondition(Conditions::AWAKENED_BY_DMG);
        }
    }
    
    return dmg;
}

int Combatant::receiveCompoundDmg(const std::vector<std::pair<int, DamageType>>& dmg, int multiplier) {
    int totalDmg = 0;
    bool received_radiant_dmg = false;
    
    for (const auto& [damage, type] : dmg) {
        totalDmg += doReceiveDmg(damage, type);
        if (type == DamageType::Radiant) {
            received_radiant_dmg = true;
        }
    }
    
    if (_currHp <= 0 && hasPassiveAbility(AbilityType::UNDEAD_FORTITUDE) && 
        multiplier == 1 && !received_radiant_dmg) {
        
        std::vector<RollType> rollTypes(_savingThrowsRollTypeMod[SavingThrow::CON].begin(),
                                      _savingThrowsRollTypeMod[SavingThrow::CON].end());
        bool saved = rollSavingThrow(_savingThrows.at(SavingThrow::CON), 
                                     5 + totalDmg,
                                     reconcileRollTypes(_savingThrowsRollTypeMod[SavingThrow::CON]));
        if (saved) {
            _currHp = 1;
            std::cout << "Instead of dying, " << _name << " drops to 1 HP thanks to Undead Fortitude" << std::endl;
        }
    }

    //! @todo this is different now
    if (_currHp <= 0 && getOriginalForm() != this) {
        getOriginalForm()->_currHp += _currHp;  // Carry-over damage
        EffectTracker::getInstance().removeEffectFromCombatantByType(getOriginalForm(), EffectType::WILDSHAPE);
    }

    if (totalDmg > 0) {
        checkConcentration(this, totalDmg);
        
        if (isAffectedBy(Conditions::AWAKENED_BY_DMG)) {
            std::cout << _name << " is awakened by taking damage" << std::endl;
            removeCondition(Conditions::AWAKENED_BY_DMG);
        }
    }

    _uncannyDodgeActive = false;
    return totalDmg;
}

bool Combatant::checkConcentration(Combatant* combatant, int dmg) {
    // If not concentrating, no check needed
    if (!combatant->isConcentrating()) {
        return true;
    }
    
    // Calculate DC for the check (higher of 10 or half the damage taken)
    int dc = std::max(10, dmg / 2);
    
    // Roll the save
    bool saved = rollSavingThrow(
        _savingThrows.at(SavingThrow::CON),
        dc,
        reconcileRollTypes(_savingThrowsRollTypeMod[SavingThrow::CON])
    );
    
    // If failed, break concentration
    if (!saved) {
        std::cout << _name << " fails their concentration check and loses concentration" << std::endl;
        combatant->breakConcentration();
        return false;
    }
    
    std::cout << _name << " maintains concentration" << std::endl;
    return true;
}

void Combatant::addUndeadFortitude() { _passiveAbilities.insert(AbilityType::UNDEAD_FORTITUDE); }

void Combatant::addResistance(DamageType dmgType) { _resistances.insert(dmgType); }

void Combatant::removeResistance(DamageType dmgType) { _resistances.erase(dmgType); }

void Combatant::addImmunity(DamageType dmgType) { _immunities.insert(dmgType); }

void Combatant::removeImmunity(DamageType dmgType) { _immunities.erase(dmgType); }

void Combatant::addVulnerability(DamageType dmgType) { _vulnerabities.insert(dmgType); }

void Combatant::removeVulnerability(DamageType dmgType) { _vulnerabities.erase(dmgType); }
}