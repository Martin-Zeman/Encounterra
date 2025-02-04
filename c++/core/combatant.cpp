#include "core/combatant.hpp"
#include "actions/dodge.hpp"
#include "actions/disengage.hpp"
#include "core/rechargeable_factory.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/action_enabler_effect.hpp"
#include "actions/default_action_plan_strategy.cpp"
#include "actions/break_grapple.hpp"

namespace enc
{

  Combatant::Combatant(CombatantType type, SubType subtype, int level, std::string name, int hp, int ac, int initBonus, int spellToHit, int speed,
                       int dc, std::unordered_set<DamageType> resistances, std::unordered_set<DamageType> immunities,
                       std::unordered_set<DamageType> vulnerabities, Conditions conditionImmunities)
      : _name(name), _maxHp(hp), _currHp(hp), _ac(ac), _dc(dc), _initBonus(initBonus), _spellToHit(spellToHit), _speed(speed / 5),
        _movement(speed / 5), _resistances(resistances), _immunities(immunities), _vulnerabities(vulnerabities),
        _conditionImmunities(conditionImmunities), _type(type), _subtype(subtype), _level(level)
  {
    _dodgeFactory = new DodgeFactory(this);
    _disengageFactory = new DisengageFactory(this);
    _getUpFactory = new GetUpFactory(this);
    _breakGrappleFactory = new BreakGrappleFactory(this);
    _actionFactories.push_back(_dodgeFactory);
    _actionFactories.push_back(_disengageFactory);
    _actionPlanStrategy = std::make_unique<DefaultActionPlanStrategy>(*this);
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

  Combatant::~Combatant()
  {
    breakConcentration();

    delete _dodgeFactory;
    delete _disengageFactory;
    delete _getUpFactory;
    delete _breakGrappleFactory;
    // delete _dangerZoneAttack; this would lead to double deletion
    delete _aoOFactory;

    for(ActoidFactory *factory : _actionFactories)
      {
        if(factory != _dodgeFactory && factory != _disengageFactory)
          { // Avoid double deletion
            delete factory;
          }
      }
    _actionFactories.clear();

    for(ActoidFactory *factory : _bonusActionFactories)
      {
        delete factory;
      }
    _bonusActionFactories.clear();

    for(ActoidFactory *factory : _reactionFactories)
      {
        delete factory;
      }
    _reactionFactories.clear();

    for(ActoidFactory *factory : _hasteActionFactories)
      {
        delete factory;
      }
    _hasteActionFactories.clear();

    for(Wildshape *form : _availableWildshapeForms)
      {
        delete form;
      }
    _availableWildshapeForms.clear();

    for(Condition *condition : _conditions)
      {
        delete condition;
      }
    for(ConditionWithDC *condition : _dcConditions)
      {
        delete condition;
      }
  }

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
    if(_constrictedTarget && !_constrictedTarget->isAlive())
      {
        _constrictedTarget = nullptr;
      }
    _weaponDmgDealtThisTurn = 0;
  }

  void Combatant::setWildshapeForm(Combatant *form) { _wildshapeForm = form; }

  void Combatant::setBaseForm(Combatant *form) { _baseForm = form; }

  Combatant &Combatant::getCurrentForm()
  {
    if(_wildshapeForm)
      {
        return *_wildshapeForm;
      }
    return *this;
  }

  Combatant &Combatant::getBaseForm()
  {
    if(_baseForm)
      {
        return *_baseForm;
      }
    return *this;
  }

  bool Combatant::isWildshapeForm() const { return _baseForm != nullptr; }

  bool Combatant::isWildshaped() const { return _wildshapeForm != nullptr; }

  bool Combatant::isBaseForm() const { return _baseForm == nullptr; }

  bool Combatant::isAffectedBy(Conditions condition) const
  {
    return std::any_of(_conditions.begin(), _conditions.end(),
                       [condition](Condition *c) { return containsCondition(c->conditionComposite, condition); })
           || std::any_of(_dcConditions.begin(), _dcConditions.end(),
                          [condition](ConditionWithDC *c) { return containsCondition(c->conditionComposite, condition); });
  }

  bool Combatant::isImmuneTo(DamageType dmgType) const { return _immunities.find(dmgType) != _immunities.end(); }

  bool Combatant::isResistantTo(DamageType dmgType) const { return _resistances.find(dmgType) != _resistances.end(); }

  bool Combatant::isVulnerableTo(DamageType dmgType) const { return _vulnerabities.find(dmgType) != _vulnerabities.end(); }

  bool Combatant::hasPassiveAbility(AbilityType ability) const { return _passiveAbilities.contains(ability); }

  void Combatant::applyCondition(Condition *condition)
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

  void Combatant::applyDCCondition(ConditionWithDC *dcCondition)
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

  bool Combatant::removeCondition(Conditions condition, Combatant *initiator)
  {
    auto it = std::find_if(_conditions.begin(), _conditions.end(), [condition, initiator](Condition *c) {
      return containsCondition(c->conditionComposite, condition) && (!initiator || c->initiator == initiator);
    });

    if(it != _conditions.end())
      {
        delete *it;
        _conditions.erase(it);
        if(condition == Conditions::SWALLOWED)
          {
            _swallower = nullptr;
          }
        return true;
      }
    return false;
  }

  bool Combatant::removeDCCondition(Conditions condition, Combatant *initiator)
  {
    auto it = std::find_if(_dcConditions.begin(), _dcConditions.end(), [condition, initiator](ConditionWithDC *c) {
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

  Combatant *Combatant::getInitiatorOfCondition(Conditions condition)
  {
    // First check DC conditions
    auto initiator = checkConditionList(_dcConditions, condition);
    if(initiator)
      {
        return initiator;
      }

    // Then check regular conditions
    return checkConditionList(_conditions, condition);
  }

  Combatant *Combatant::getGrappledTarget()
  {
    for(const auto &cond : _dcConditions)
      {
        if(containsCondition(cond->conditionComposite, Conditions::GRAPPLING) && cond->target)
          {
            return cond->target;
          }
      }

    for(const auto &cond : _conditions)
      {
        if(containsCondition(cond->conditionComposite, Conditions::GRAPPLING) && cond->target)
          {
            return cond->target;
          }
      }

    return nullptr;
  }

  std::vector<ConditionWithDC *> Combatant::needsToBreakOutOfGrapple() const
  {
    std::vector<ConditionWithDC *> grappleConditions;
    for(ConditionWithDC *dcCond : _dcConditions)
      {
        if(containsCondition(dcCond->conditionComposite, Conditions::GRAPPLED) && dcCond->phase == PhaseOfTurn::ACTION)
          {
            grappleConditions.push_back(dcCond);
          }
      }
    return grappleConditions;
  }

  bool Combatant::breakOutOfGrapple(ConditionWithDC *condition)
  {
    auto it = std::find(_dcConditions.begin(), _dcConditions.end(), condition);
    if(it != _dcConditions.end())
      {
        _dcConditions.erase(it);
        return true;
      }
    return false;
  }

  void Combatant::setConcentrationEffect(Effect *effect)
  {
    breakConcentration();
    _concentrationEffect = effect;
    EffectTracker::getInstance().add(effect);

    if(_baseForm)
      {
        _baseForm->_concentrationEffect = effect;
      }
    else if(_wildshapeForm)
      {
        _wildshapeForm->_concentrationEffect = effect;
      }
  }

  void Combatant::breakConcentration()
  {
    std::cout << "Breaking concentration for " << this << std::endl;

    if(_concentrationEffect)
      {
        EffectTracker::getInstance().remove(_concentrationEffect);
      }
    _concentrationEffect = nullptr;

    Combatant &baseForm = getBaseForm(); // in case we were wildshaped
    baseForm._concentrationEffect = nullptr;
  }

  bool Combatant::isConcentrating() const { return _concentrationEffect != nullptr; }

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

  ActoidFactory* Combatant::getActionFactory(AbilityType type)
  {
    for(auto &factory : _actionFactories)
      {
        if(factory->getAbilityType() == type)
          {
            return factory;
          }
      }
    return nullptr;
  }

  void Combatant::rollForRecharge()
  {
    for(auto &factory : _actionFactories)
      {
        if(factory->hasFlag(FactoryFlags::IS_RECHARGE))
          {
            static_cast<RechargeableFactory *>(factory)->rollForRecharge();
          }
      }

    for(auto &factory : _bonusActionFactories)
      {
        if(factory->hasFlag(FactoryFlags::IS_RECHARGE))
          {
            static_cast<RechargeableFactory *>(factory)->rollForRecharge();
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

    if(_currHp <= 0 && _baseForm)
      {
        _baseForm->_currHp += _currHp; // Carry-over damage
        EffectTracker::getInstance().removeEffectFromCombatantByType(*_baseForm, EffectType::WILDSHAPE);
      }

    // Handle effects of taking damage
    if(dmg > 0)
      {
        checkConcentration(dmg);

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

    if(_currHp <= 0 && _baseForm)
      {
        _baseForm->_currHp += _currHp; // Carry-over damage
        EffectTracker::getInstance().removeEffectFromCombatantByType(*_baseForm, EffectType::WILDSHAPE);
      }

    if(totalDmg > 0)
      {
        checkConcentration(totalDmg);

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

  std::vector<Actoid *>
  Combatant::calculateActionPlan(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return _actionPlanStrategy->calculateActionPlan(distances, shortestPaths);
  }

  const std::vector<Actoid *> &Combatant::getActionPlan() const { return _actionPlan; }

  void Combatant::setActionPlan(std::vector<Actoid *> plan) { _actionPlan = std::move(plan); }

  Actoid * Combatant::popActionPlan()
  {
    if(_actionPlan.empty())
      return nullptr;
    auto action = _actionPlan.front();
    _actionPlan.erase(_actionPlan.begin());
    return action;
  }
} // namespace enc
