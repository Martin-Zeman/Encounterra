#include "core/combatant.hpp"
#include "actions/dodge.hpp"
#include "actions/disengage.hpp"
#include "core/rechargeable_factory.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/action_enabler_effect.hpp"

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

  Combatant::~Combatant() { breakConcentration(); }

  bool Combatant::operator==(const Combatant &other) const { return _instanceId == other._instanceId; }

  bool Combatant::operator!=(const Combatant &other) const { return !(*this == other); }

  bool Combatant::operator==(const std::shared_ptr<Combatant> &other) const { return other && _instanceId == other->_instanceId; }

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

  void Combatant::reset()
  {
    _hasAction = true;
    _hasBonusAction = true;
    _hasReaction = true;
    _currHp = _maxHp;
    _movement = _speed;
    _isDodging = false;
    if(_spellslots)
      {
        _spellslots->reset();
      }
    for(auto &r : _resources)
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
    for(auto &ammo : _ammo)
      {
        ammo.second.reset();
      }
    _oneTimeAcbonus = 0; // Not really needed
    _actionPlan.clear();
    _weaponDmgDealtThisTurn = 0;
  }

  void Combatant::newTurn()
  {
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
    if(_isShieldSpellActive)
      {
        _ac -= 5;
      }
    _isShieldSpellActive = false;
    _hasHasteAction = false;
    _attackFsm.reset();
    _actionPlan.clear();
    if(_constrictedTarget != nullptr && !_constrictedTarget->isAlive())
      {
        _constrictedTarget = nullptr;
      }
    _weaponDmgDealtThisTurn = 0;
  }

  void Combatant::setWildshapeForm(const std::shared_ptr<Combatant> &form)
  {
    if(form)
      {
        _wildshapeForm = form;
      }
    else
      {
        _wildshapeForm = std::nullopt;
      }
  }

  std::weak_ptr<Combatant> Combatant::getCurrentForm()
  {
    if(_wildshapeForm && !_wildshapeForm->expired())
      {
        return *_wildshapeForm;
      }
    return _baseForm; // Will be empty if this is the base form
  }

  std::weak_ptr<Combatant> Combatant::getOriginalForm()
  {
    return _baseForm; // Will be empty if this is the base form
  }

  bool Combatant::isWildshaped() const { return _wildshapeForm.has_value() && !_wildshapeForm->expired(); }

  void Combatant::setBaseForm(const std::shared_ptr<Combatant> &form) { _baseForm = form; }

  bool Combatant::isAffectedBy(Conditions condition) const
  {
    return std::any_of(_conditions.begin(), _conditions.end(),
                       [condition](const std::shared_ptr<Condition> &c) { return containsCondition(c->conditionComposite, condition); })
           || std::any_of(_dcConditions.begin(), _dcConditions.end(),
                          [condition](const std::shared_ptr<ConditionWithDC> &c) { return containsCondition(c->conditionComposite, condition); });
  }

  bool Combatant::isImmuneTo(DamageType dmgType) { return _immunities.find(dmgType) != _immunities.end(); }

  bool Combatant::isResistantTo(DamageType dmgType) { return _resistances.find(dmgType) != _resistances.end(); }

  bool Combatant::isVulnerableTo(DamageType dmgType) { return _vulnerabities.find(dmgType) != _vulnerabities.end(); }

  bool Combatant::hasPassiveAbility(AbilityType ability) const { return _passiveAbilities.contains(ability); }

  void Combatant::applyCondition(std::shared_ptr<Condition> condition)
  {
    if(!condition)
      {
        return;
      }

    if(containsCondition(condition->conditionComposite, Conditions::SWALLOWED))
      {
        _swallower = condition->initiator;
      }
    _conditions.push_back(std::move(condition));
  }

  void Combatant::applyDCCondition(std::shared_ptr<ConditionWithDC> dcCondition)
  {
    if(!dcCondition)
      {
        return;
      }

    if(containsCondition(dcCondition->conditionComposite, Conditions::SWALLOWED))
      {
        _swallower = dcCondition->initiator;
      }
    _dcConditions.push_back(std::move(dcCondition));
  }

  bool Combatant::removeCondition(Conditions condition, const const std::shared_ptr<Combatant>& initiator)
  {
    auto it = std::find_if(_conditions.begin(), _conditions.end(), [condition, initiator](const std::shared_ptr<Condition> &c) {
      return containsCondition(c->conditionComposite, condition) && (!initiator || c->initiator == initiator);
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

  bool Combatant::removeDCCondition(Conditions condition, const const std::shared_ptr<Combatant>& initiator)
  {
    auto it = std::find_if(_dcConditions.begin(), _dcConditions.end(), [condition, initiator](const std::shared_ptr<ConditionWithDC> &c) {
      return containsCondition(c->conditionComposite, condition) && (!initiator || c->initiator == initiator);
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

  std::weak_ptr<Combatant> Combatant::getInitiatorOfCondition(Conditions condition)
  {
    auto initiator = checkConditionList(_dcConditions, condition);
    if(!initiator.expired())
      {
        return initiator;
      }

    return checkConditionList(_conditions, condition); // TODO: How to handle this?
  }

  std::weak_ptr<Combatant> Combatant::getGrappledTarget()
  {
    for(const auto &cond : _dcConditions)
      {
        if(containsCondition(cond->conditionComposite, Conditions::GRAPPLING) && cond->target.has_value())
          {
            return cond->target.value();
          }
      }

    for(const auto &cond : _conditions)
      {
        if(containsCondition(cond->conditionComposite, Conditions::GRAPPLING) && cond->target.has_value())
          {
            return cond->target.value();
          }
      }

    return {};
  }

  std::vector<std::weak_ptr<ConditionWithDC>> Combatant::needsToBreakOutOfGrapple() const
  {
    std::vector<std::weak_ptr<ConditionWithDC>> grappleConditions;
    for(const auto &dcCond : _dcConditions)
      {
        if(containsCondition(dcCond->conditionComposite, Conditions::GRAPPLED) && dcCond->phase == PhaseOfTurn::ACTION)
          {
            grappleConditions.push_back(dcCond);
          }
      }
    return grappleConditions;
  }

  bool Combatant::breakOutOfGrapple(const std::weak_ptr<ConditionWithDC> &condition)
  {
    if(auto sharedCond = condition.lock())
      {
        auto it = std::find(_dcConditions.begin(), _dcConditions.end(), sharedCond);
        if(it != _dcConditions.end())
          {
            _dcConditions.erase(it);
            return true;
          }
      }
    return false;
  }

  void Combatant::setConcentrationEffect(std::shared_ptr<Effect> effect)
  {
    breakConcentration(); // Break existing concentration if any

    // Store weak_ptr to avoid circular reference
    _concentrationEffect = EffectTracker::getInstance().add(effect);

    // Also set concentration for original form if in wildshape
    if(!_wildshapeForm.expired() && _baseForm != this)
      {
        _baseForm->_concentrationEffect = _concentrationEffect;
      }
  }

  void Combatant::breakConcentration()
  {
    std::cout << "Breaking concentration for " << this << std::endl;
    if(auto ptr = _concentrationEffect.lock())
      {
        std::cout << "  Effect ptr valid: " << ptr.get() << std::endl;
        EffectTracker::getInstance().remove(ptr);
      }
    else
      {
        std::cout << "  No valid effect ptr" << std::endl;
      }
    _concentrationEffect.reset();

    // Also break concentration for original form if in wildshape
    if(!_wildshapeForm.expired() && _baseForm != this)
      {
        std::cout << "  Breaking concentration for original form" << std::endl;
        _baseForm->_concentrationEffect.reset();
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
    for(auto &factory : _actionFactories)
      {
        if(factory->getAbilityType() == type)
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

  RollType Combatant::getSavingThrowRollTypeMods(SavingThrow type) const
  {
    auto it = _savingThrowsRollTypeMod.find(type);
    RollType straight = RollType::STRAIGHT;
    return it != _savingThrowsRollTypeMod.end() ? it->second : straight;
  }

  void Combatant::addSavingThrowRollTypeMod(SavingThrow type, RollType rollType) { _savingThrowsRollTypeMod[type] |= rollType; }

  void Combatant::setSavingThrowRollTypeMod(SavingThrow type, RollType rollType) { _savingThrowsRollTypeMod[type] = rollType; }

  void Combatant::removeSavingThrowRollTypeMod(SavingThrow type, RollType rollType)
  {
    auto it = _savingThrowsRollTypeMod.find(type);
    if(it != _savingThrowsRollTypeMod.end())
      {
        it->second &= ~rollType;
      }
  }

  void Combatant::clearSavingThrowRollTypeMods(SavingThrow type) { _savingThrowsRollTypeMod.erase(type); }

  void Combatant::clearAllSavingThrowMods()
  {
    _savingThrowsFlatMod.clear();
    _savingThrowsDiceMod.clear();
    _savingThrowsRollTypeMod.clear();
  }

  void Combatant::setShortestPathsCache(const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    if(!_shortestPathsCache)
      {
        _shortestPathsCache = std::make_unique<blaze::DynamicMatrix<Coord>>();
      }
    *_shortestPathsCache = shortestPaths;
  }

  // Private helper for damage calculations
  int Combatant::doReceiveDmg(int dmg, DamageType dmgType)
  {
    // Check immunities first
    if(_immunities.find(dmgType) != _immunities.end())
      {
        std::cout << _name << " is immune to " << DAMAGE_TYPE_TO_STRING.at(dmgType) << " and reduces the damage to 0" << std::endl;
        return 0;
      }

    // Check resistances
    if(_resistances.find(dmgType) != _resistances.end())
      {
        dmg = std::floor(dmg / 2);
        std::cout << _name << " is resistant to " << DAMAGE_TYPE_TO_STRING.at(dmgType) << " and reduces the damage to " << dmg << std::endl;
      }

    // Check vulnerabilities
    if(_vulnerabities.find(dmgType) != _vulnerabities.end())
      {
        dmg *= 2;
        std::cout << _name << " is vulnerable to " << DAMAGE_TYPE_TO_STRING.at(dmgType) << " which doubles the damage to " << dmg << std::endl;
      }

    // Apply uncanny dodge if active
    if(_uncannyDodgeActive)
      {
        dmg = std::floor(dmg / 2);
        std::cout << _name << " uses Uncanny Dodge which reduces the damage to " << dmg << std::endl;
      }

    assert(_temporaryHp >= 0);
    _temporaryHp -= dmg;

    if(_temporaryHp < 0)
      {
        _currHp += _temporaryHp;
        _temporaryHp = 0;
      }

    _dmgTypesTookLastRound.insert(dmgType);
    return dmg;
  }

  int Combatant::receiveDmg(int dmg, DamageType dmg_type, int multiplier)
  {
    dmg = doReceiveDmg(dmg, dmg_type);

    // Undead Fortitude check
    if(_currHp <= 0 && hasPassiveAbility(AbilityType::UNDEAD_FORTITUDE) && multiplier == 1 && dmg_type != DamageType::Radiant)
      {
        bool saved = rollSavingThrow(_savingThrows.at(SavingThrow::CON), 5 + dmg, reconcileRollTypes(_savingThrowsRollTypeMod[SavingThrow::CON]));
        if(saved)
          {
            _currHp = 1;
            std::cout << "Instead of dying, " << _name << " drops to 1 HP thanks to Undead Fortitude" << std::endl;
          }
      }

    // Handle wildshape damage overflow
    if(_currHp <= 0 && getOriginalForm() != this)
      {
        getOriginalForm()->_currHp += _currHp; // Carry-over damage
        EffectTracker::getInstance().removeEffectFromCombatantByType(getOriginalForm(), EffectType::WILDSHAPE);
      }

    // Handle effects of taking damage
    if(dmg > 0)
      {
        checkConcentration(this, dmg);

        if(isAffectedBy(Conditions::AWAKENED_BY_DMG))
          {
            std::cout << _name << " is awakened by taking damage" << std::endl;
            removeCondition(Conditions::AWAKENED_BY_DMG);
          }
      }

    return dmg;
  }

  int Combatant::receiveCompoundDmg(const std::vector<std::pair<int, DamageType>> &dmg, int multiplier)
  {
    int totalDmg = 0;
    bool received_radiant_dmg = false;

    for(const auto &[damage, type] : dmg)
      {
        totalDmg += doReceiveDmg(damage, type);
        if(type == DamageType::Radiant)
          {
            received_radiant_dmg = true;
          }
      }

    if(_currHp <= 0 && hasPassiveAbility(AbilityType::UNDEAD_FORTITUDE) && multiplier == 1 && !received_radiant_dmg)
      {
        bool saved
          = rollSavingThrow(_savingThrows.at(SavingThrow::CON), 5 + totalDmg, reconcileRollTypes(_savingThrowsRollTypeMod[SavingThrow::CON]));
        if(saved)
          {
            _currHp = 1;
            std::cout << "Instead of dying, " << _name << " drops to 1 HP thanks to Undead Fortitude" << std::endl;
          }
      }

    //! @todo this is different now
    if(_currHp <= 0 && getOriginalForm() != this)
      {
        getOriginalForm()->_currHp += _currHp; // Carry-over damage
        EffectTracker::getInstance().removeEffectFromCombatantByType(getOriginalForm(), EffectType::WILDSHAPE);
      }

    if(totalDmg > 0)
      {
        checkConcentration(this, totalDmg);

        if(isAffectedBy(Conditions::AWAKENED_BY_DMG))
          {
            std::cout << _name << " is awakened by taking damage" << std::endl;
            removeCondition(Conditions::AWAKENED_BY_DMG);
          }
      }

    _uncannyDodgeActive = false;
    return totalDmg;
  }

  bool Combatant::checkConcentration(int dmg)
  {
    // If not concentrating, no check needed
    if(!isConcentrating())
      {
        return true;
      }

    // Calculate DC for the check (higher of 10 or half the damage taken)
    int dc = std::max(10, dmg / 2);

    // Roll the save
    bool saved = rollSavingThrow(_savingThrows.at(SavingThrow::CON), dc, reconcileRollTypes(_savingThrowsRollTypeMod[SavingThrow::CON]));

    // If failed, break concentration
    if(!saved)
      {
        std::cout << _name << " fails their concentration check and loses concentration" << std::endl;
        breakConcentration();
        return false;
      }

    std::cout << _name << " maintains concentration" << std::endl;
    return true;
  }

  void Combatant::withActionEnablerEffect(Actoid &action, const std::function<void(bool)> &fn)
  {
    if(auto *actionEnabler = dynamic_cast<ActionEnablerEffect *>(&action))
      {
        try
          {
            actionEnabler->enable();
            fn(true);
          }
        catch(...)
          {
            actionEnabler->disable();
            throw;
          }
        actionEnabler->disable();
      }
    else
      {
        fn(false);
      }
  }

  void Combatant::withHasAction(const std::function<void()> &fn)
  {
    bool originalHasAction = _hasAction;
    try
      {
        _hasAction = true;
        fn();
      }
    catch(...)
      {
        _hasAction = originalHasAction;
        throw;
      }
    _hasAction = originalHasAction;
  }

  void Combatant::addUndeadFortitude() { _passiveAbilities.insert(AbilityType::UNDEAD_FORTITUDE); }

  void Combatant::addResistance(DamageType dmgType) { _resistances.insert(dmgType); }

  void Combatant::removeResistance(DamageType dmgType) { _resistances.erase(dmgType); }

  void Combatant::addImmunity(DamageType dmgType) { _immunities.insert(dmgType); }

  void Combatant::removeImmunity(DamageType dmgType) { _immunities.erase(dmgType); }

  void Combatant::addVulnerability(DamageType dmgType) { _vulnerabities.insert(dmgType); }

  void Combatant::removeVulnerability(DamageType dmgType) { _vulnerabities.erase(dmgType); }

  std::vector<std::shared_ptr<Actoid>>
  Combatant::calculateActionPlan(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return _actionPlanStrategy->calculateActionPlan(distances, shortestPaths);
  }

  const std::vector<std::shared_ptr<Actoid>> &Combatant::getActionPlan() const { return _actionPlan; }

  void Combatant::setActionPlan(std::vector<std::shared_ptr<Actoid>> plan) { _actionPlan = std::move(plan); }

  std::shared_ptr<Actoid> Combatant::popActionPlan()
  {
    if(_actionPlan.empty())
      return nullptr;
    auto action = _actionPlan.front();
    _actionPlan.erase(_actionPlan.begin());
    return action;
  }
} // namespace enc
