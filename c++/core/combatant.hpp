#pragma once

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <random>
#include <iostream>
#include <functional>
#include <sstream>
#include <string_view>
#include <cstdint>
#include <iomanip>
#include <memory>
#include <openssl/sha.h>
#include "core/misc.hpp"
#include "core/types.hpp"
#include "core/interfaces.hpp"
#include "core/conditions.hpp"
#include "core/resources.hpp"
#include "core/spellslots.hpp"
#include "actions/action_types.hpp"
#include "actions/action_constants.hpp"
#include "actions/action_plan_strategy.hpp"
#include "spells/firebolt.hpp"
#include "core/state_machine.hpp"

namespace enc
{

  class Wildshape;
  class Effect;

  using FactoryCreator = std::function<std::shared_ptr<ActoidFactory>()>;

  class Combatant
  {
  public:
    std::string _name;
    int _instanceId;

    Combatant(CombatantType type, SubType subtype, int level, std::string name, int hp, int ac, int initBonus, int spellToHit, int speed, int dc,
              std::unordered_set<DamageType> resistances = {}, std::unordered_set<DamageType> immunities = {},
              std::unordered_set<DamageType> vulnerabities = {}, Conditions conditionImmunities = Conditions::NONE);

    // Combatant(std::string name, int hp, int ac, int initBonus, int spellToHit, int speed, int dc, std::unordered_set<DamageType> resistances =
    // {},
    //           std::unordered_set<DamageType> immunities = {}, std::unordered_set<DamageType> vulnerabities = {});

    ~Combatant();

    static constexpr uint32_t fnv1a_32(uint32_t initial, uint32_t value)
    {
      uint32_t hash = initial;
      for(int i = 0; i < 32; i += 8)
        {
          hash ^= (value >> i) & 0xFF;
          hash *= 16777619u;
        }
      return hash;
    }

    static constexpr uint32_t fnv1a_32(std::string_view str)
    {
      uint32_t hash = 2166136261u;
      for(char c : str)
        {
          hash ^= static_cast<uint32_t>(c);
          hash *= 16777619u;
        }
      return hash;
    }

    template <typename SubType> static constexpr int generateClassId(std::string_view className, SubType subtype, int level)
    {
      uint32_t hash = fnv1a_32(className);
      hash = fnv1a_32(hash, static_cast<uint32_t>(subtype));
      hash = fnv1a_32(hash, static_cast<uint32_t>(level));
      return static_cast<int>(hash);
    }

    // Method to generate instance ID
    int generateInstanceId() const
    {
      static int nextId = 1;
      return ++nextId;
    }

    std::string toString() const;
    void setShortCode(const std::string &shortCode) { _shortCode = shortCode; }
    std::string getShortCode() const { return _shortCode; }
    virtual int getClassId() const = 0;
    virtual ResourceState exportResources() = 0;
    virtual void importResources(const ResourceState &resources) = 0;

    bool isAlive() const;
    void onDie();
    void onEndOfTurn();
    void rollInitiative();
    void reset();
    void newTurn();
    void setSize(Size size) { _size = size; };
    Size getSize() const { return _size; };
    int getAC() const { return _ac; };
    void setTeamColor(Color teamColor) { _teamColor = teamColor; }
    bool hasAction() const { return _hasAction; }
    bool hasBonusAction() const { return _hasBonusAction; }
    bool hasHasteAction() const { return _hasHasteAction; }
    bool hasReaction() const { return _hasReaction; }
    void setHasAction(bool has) { _hasAction = has; }
    void setHasBonusAction(bool has) { _hasBonusAction = has; }
    void setHasHasteAction(bool has) { _hasHasteAction = has; }
    void setHasReaction(bool has) { _hasReaction = has; }
    bool hasAlreadyUsedSpellslotThisTurn() const { return _alreadyUsedSpellslotThisTurn; }
    void setAlreadyUsedSpellslotThisTurn(bool used) { _alreadyUsedSpellslotThisTurn = used; }
    int getMeleeReactionRange() { return _meleeReactionRange; }
    void setWildshapeForm(Combatant* form);
    void setBaseForm(Combatant *form);
    Combatant &getCurrentForm();
    Combatant &getBaseForm();
    bool isWildshapeForm() const;
    bool isWildshaped() const;
    bool isBaseForm() const;
    Combatant *getSwallower() const { return _swallower; }
    void setSwallower(Combatant *swallower) { _swallower = swallower; }
    bool isSwallowed() const { return _swallower != nullptr; }
    const std::vector<Condition *> &getConditions() const { return _conditions; }
    const std::vector<ConditionWithDC *> &getDCConditions() const { return _dcConditions; }
    bool isAffectedBy(Conditions condition) const;
    void applyCondition(Condition *condition);
    void applyDCCondition(ConditionWithDC *dcCondition);
    bool removeCondition(Conditions condition, Combatant *initiator = nullptr);
    bool removeDCCondition(Conditions condition, Combatant *initiator = nullptr);
    void removeAllConditionsOfType(Conditions condition);
    Combatant *getInitiatorOfCondition(Conditions condition);
    Combatant *getGrappledTarget();
    std::vector<ConditionWithDC*> needsToBreakOutOfGrapple() const;
    bool breakOutOfGrapple(ConditionWithDC *grappleCondition);
    void setConcentrationEffect(Effect *effect);
    Effect *getConcentrationEffect() const { return _concentrationEffect; }
    void breakConcentration();
    bool isConcentrating() const;
    bool isAffectedByAny(const std::vector<Conditions> &conditions) const;
    void setResourceDepletionLevel(ResourceDepletionLevel level) { _resouceDepletionLevel = level; }
    bool isImmuneTo(DamageType dmgType) const;
    bool isResistantTo(DamageType dmgType) const;
    bool isVulnerableTo(DamageType dmgType) const;
    Spellslots &getSpellslots() { return *_spellslots; }
    int getLevel() const { return _level; }
    int getCurrentHp() const { return _currHp; }
    void setCurrentHp(int hp) { _currHp = hp; }
    int getMaxHp() const { return _maxHp; }
    void setTemporaryHp(int hp) { _temporaryHp = std::max(_temporaryHp, hp); }
    int getTemporaryHp() { return _temporaryHp; }
    int getCurrentInit() const { return _currInit; }
    int getMovement() const { return _movement; }
    void setMovement(int movement) { _movement = movement; }
    bool hasMovement(int dist = 1) const { return _movement >= dist; }
    void decrementMovement(int dist = 1) { _movement -= dist; }
    int getSpeed() const { return _speed; }
    bool hasPassiveAbility(AbilityType ability) const;
    const std::unordered_map<SavingThrow, int> &getSavingThrows() const { return _savingThrows; }
    int getSavingThrow(SavingThrow st) const { return _savingThrows.at(st); }
    void setSavingThrow(SavingThrow st, int value) { _savingThrows.at(st) = value; }
    const std::vector<int> &getSavingThrowFlatMods(SavingThrow type) const;
    void addSavingThrowFlatMod(SavingThrow type, int mod);
    void clearSavingThrowFlatMods(SavingThrow type);
    const std::vector<Die> &getSavingThrowDiceMods(SavingThrow type) const;
    void addSavingThrowDiceMod(SavingThrow type, const Die &mod);
    void clearSavingThrowDiceMods(SavingThrow type);
    RollType getSavingThrowRollTypeMods(SavingThrow type) const;
    void addSavingThrowRollTypeMod(SavingThrow type, RollType rollType);
    void setSavingThrowRollTypeMod(SavingThrow type, RollType rollType);
    void removeSavingThrowRollTypeMod(SavingThrow type, RollType rollType);
    void clearSavingThrowRollTypeMods(SavingThrow type);
    ActoidFactory *getActionFactory(AbilityType type);
    void clearAllSavingThrowMods();
    void rollForRecharge();
    const std::vector<ActoidFactory *> &getActionFactoriesConst() const { return _actionFactories; }
    const std::vector<ActoidFactory *> &getBonusActionFactoriesConst() const { return _bonusActionFactories; }
    const std::vector<ActoidFactory *> &getReactionFactoriesConst() const { return _reactionFactories; }
    const std::vector<ActoidFactory *> &getHasteActionFactoriesConst() const { return _hasteActionFactories; }
    std::vector<ActoidFactory *> &getActionFactories() { return _actionFactories; }
    std::vector<ActoidFactory *> &getBonusActionFactories() { return _bonusActionFactories; }
    std::vector<ActoidFactory *> &getReactionFactories() { return _reactionFactories; }
    std::vector<ActoidFactory *> &getHasteActionFactories() { return _hasteActionFactories; }
    void setAvailableWildshapeForms(std::vector<Wildshape *> wildshapeForms) { _availableWildshapeForms = wildshapeForms; }
    const std::vector<Wildshape *> &getAvailableWildshapeForms() { return _availableWildshapeForms; }
    DirectThreatFactory* getDangerZoneAttack() { return _dangerZoneAttack; }
    void setDangerZoneAttack(DirectThreatFactory *dangerZoneAttack) { _dangerZoneAttack = dangerZoneAttack; }
    AttackFactory *getAoOFactory() { return _aoOFactory; }
    ActoidFactory *getGetUpFactory() { return _getUpFactory; }
    ActoidFactory *getBreakGrappleFactory() { return _breakGrappleFactory; }
    ActoidFactory *getDodgeFactory() { return _dodgeFactory; }
    ActoidFactory *getDisengageFactory() { return _disengageFactory; }
    void setShortestPathsCache(const blaze::DynamicMatrix<Coord> &shortestPaths);
    const blaze::DynamicMatrix<Coord> &getShortestPathsCache() const { return *_shortestPathsCache; }
    int receiveDmg(int dmg, DamageType dmg_type, int multiplier = 1);
    int receiveCompoundDmg(const std::vector<std::pair<int, DamageType>>& dmg, int multiplier = 1);
    void addResistance(DamageType dmgType);
    void removeResistance(DamageType dmgType);
    void addImmunity(DamageType dmgType);
    void removeImmunity(DamageType dmgType);
    void addVulnerability(DamageType dmgType);
    void removeVulnerability(DamageType dmgType);
    bool isDodging() const { return _isDodging; }
    /**
     * Handles concentration checks when a combatant takes damage.
     *
     * @param combatant The combatant who needs to make the concentration check
     * @param dmg The amount of damage that triggered the check
     * @return true if concentration was maintained, false if it was lost
     */
    bool checkConcentration(int dmg);
    void withActionEnablerEffect(Actoid& action, const std::function<void(bool)>& fn);
    void withHasAction(const std::function<void()> &fn);
    const std::vector<Actoid *> &getActionPlan() const;
    void setActionPlan(std::vector<Actoid *> plan);
    Actoid * popActionPlan(); // Removes and returns first action
    std::vector<Actoid *>
    calculateActionPlan(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths);

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Action abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    ActoidFactory *addMeleeAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice, int dmgBonus,
                                  DamageType damageType, int attackRange)
    {
      auto factory = new MeleeAttackFactory("MeleeAttackFactory", name, owner, AbilityType::MELEE_ATTACK, toHit, dmgDice, dmgBonus, damageType, attackRange);
      _actionFactories.emplace_back(factory);
      return factory;
    }

    ActoidFactory *addRangedAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice, int dmgBonus,
                                   DamageType damageType, int attackRange)
    {
      auto factory = new RangedAttackFactory("RangedAttackFactory", name, owner, AbilityType::RANGED_ATTACK, toHit, dmgDice, dmgBonus, damageType, attackRange);
      _actionFactories.emplace_back(factory);
      return factory;
    }

    ActoidFactory *addRecklessAttack() { return nullptr; }
    ActoidFactory *addPreSwallowBite() { return nullptr; }
    ActoidFactory *addBiteAndSwallow() { return nullptr; }
    ActoidFactory *addDodge() { return nullptr; }
    ActoidFactory *addDash() { return nullptr; }
    ActoidFactory *addDisengage() { return nullptr; }
    ActoidFactory *addFireball() { return nullptr; }
    ActoidFactory *addFirebolt() { 
      auto factory = new FireboltFactory(_spellToHit, AbilityType::FIREBOLT, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;

     }
    ActoidFactory *addChaosBolt() { return nullptr; }
    ActoidFactory *addHaste() { return nullptr; }
    ActoidFactory *addHungerOfHadar() { return nullptr; }
    ActoidFactory *addSpikeGrowth() { return nullptr; }
    ActoidFactory *addCloudOfDaggers() { return nullptr; }
    ActoidFactory *addHide() { return nullptr; }
    ActoidFactory *addTwinnedFirebolt() { return nullptr; }
    ActoidFactory *addTwinnedHaste() { return nullptr; }
    ActoidFactory *addScorchingRay() { return nullptr; }
    ActoidFactory *addFaerieFire() { return nullptr; }
    ActoidFactory *addWildshape() { return nullptr; }
    ActoidFactory *addPounce() { return nullptr; }
    ActoidFactory *addConstrict() { return nullptr; }
    ActoidFactory *addBreakGrapple() { return nullptr; }
    ActoidFactory *addFlamingSphere() { return nullptr; }
    ActoidFactory *addWeb() { return nullptr; }
    ActoidFactory *addHoldPerson() { return nullptr; }
    ActoidFactory *addTwinnedHoldPerson() { return nullptr; }
    ActoidFactory *addShockingGrasp() { return nullptr; }
    ActoidFactory *addTwinnedShockingGrasp() { return nullptr; }
    ActoidFactory *addMagicMissile() { return nullptr; }
    ActoidFactory *addGrapple() { return nullptr; }
    ActoidFactory *addGrappleAttack() { return nullptr; }
    ActoidFactory *addVampiricBite() { return nullptr; }
    ActoidFactory *addBless() { return nullptr; }
    ActoidFactory *addRayOfEnfeeblement() { return nullptr; }
    ActoidFactory *addTwinnedRayOfEnfeeblement() { return nullptr; }
    ActoidFactory *addSleep() { return nullptr; }
    ActoidFactory *addShakeAllyAwake() { return nullptr; }
    ActoidFactory *addThunderwave() { return nullptr; }
    ActoidFactory *addMenacingMeleeAttack() { return nullptr; }
    ActoidFactory *addParalyzingMeleeAttack() { return nullptr; }
    ActoidFactory *addMenacingRangedAttack() { return nullptr; }
    ActoidFactory *addPrecisionAttack() { return nullptr; }
    ActoidFactory *addLayOnHands() { return nullptr; }
    ActoidFactory *addCureWounds() { return nullptr; }
    ActoidFactory *addAbjureEnemy() { return nullptr; }
    ActoidFactory *addConicBreathWeapon() { return nullptr; }
    ActoidFactory *addConicBreathWeaponAttack() { return nullptr; }
    ActoidFactory *addLineBreathWeapon() { return nullptr; }
    ActoidFactory *addRayOfFrost() { return nullptr; }

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Bonus Action abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    ActoidFactory *addBonusMeleeAttack() { return nullptr; }
    ActoidFactory *addBonusRangedAttack() { return nullptr; }
    ActoidFactory *addPamBonusAttack() { return nullptr; }
    ActoidFactory *addRage() { return nullptr; }
    ActoidFactory *addTotemRage() { return nullptr; }
    ActoidFactory *addMistyStep() { return nullptr; }
    ActoidFactory *addCunningDisengage() { return nullptr; }
    ActoidFactory *addCunningDash() { return nullptr; }
    ActoidFactory *addCunningHide() { return nullptr; }
    ActoidFactory *addQuickenedFireball() { return nullptr; }
    ActoidFactory *addQuickenedFirebolt() { return nullptr; }
    ActoidFactory *addQuickenedChaosBolt() { return nullptr; }
    ActoidFactory *addQuickenedHaste() { return nullptr; }
    ActoidFactory *addQuickenedHungerOfHadar() { return nullptr; }
    ActoidFactory *addQuickenedSpikeGrowth() { return nullptr; }
    ActoidFactory *addQuickenedCloudOfDaggers() { return nullptr; }
    ActoidFactory *addQuickenedScorchingRay() { return nullptr; }
    ActoidFactory *addQuickenedFaerieFire() { return nullptr; }
    ActoidFactory *addQuickenedBless() { return nullptr; }
    ActoidFactory *addQuickenedFlamingSphere() { return nullptr; }
    ActoidFactory *addQuickenedHoldPerson() { return nullptr; }
    ActoidFactory *addQuickenedRayOfFrost() { return nullptr; }
    ActoidFactory *addFlamingSphereRam() { return nullptr; }
    ActoidFactory *addMoonWildshape() { return nullptr; }
    ActoidFactory *addQuickenedShockingGrasp() { return nullptr; }
    ActoidFactory *addQuickenedMagicMissile() { return nullptr; }
    ActoidFactory *addQuickenedRayOfEnfeeblement() { return nullptr; }
    ActoidFactory *addQuickenedSleep() { return nullptr; }
    ActoidFactory *addSecondWind() { return nullptr; }
    ActoidFactory *addHealingWord() { return nullptr; }
    ActoidFactory *addTwinnedHealingWord() { return nullptr; }
    ActoidFactory *addShillelagh() { return nullptr; }
    ActoidFactory *addQuickenedThunderwave() { return nullptr; }
    ActoidFactory *addBonusMenacingMeleeAttack() { return nullptr; }
    ActoidFactory *addBonusMenacingRangedAttack() { return nullptr; }
    ActoidFactory *addShieldOfFaith() { return nullptr; }
    ActoidFactory *addQuickenedCureWounds() { return nullptr; }
    ActoidFactory *addVowOfEnmity() { return nullptr; }
    ActoidFactory *addAggressive() { return nullptr; }
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Reaction abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    ActoidFactory *addReactionAttack() { return nullptr; }
    ActoidFactory *addShield() { return nullptr; }
    ActoidFactory *addPreSwallowBiteReaction() { return nullptr; }
    ActoidFactory *addUncannyDodge() { return nullptr; }
    ActoidFactory *addParry() { return nullptr; }
    ActoidFactory *addRiposte() { return nullptr; }
    ActoidFactory *addReactionParalyzingMeleeAttack() { return nullptr; }
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Haste abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    ActoidFactory *addHasteMeleeAttack() { return nullptr; }
    ActoidFactory *addHasteRangedAttack() { return nullptr; }
    ActoidFactory *addHasteDash() { return nullptr; }
    ActoidFactory *addHasteDisengage() { return nullptr; }
    ActoidFactory *addHasteHide() { return nullptr; }
    ActoidFactory *addHastePreSwallowBite() { return nullptr; }
    ActoidFactory *addHasteBiteAndSwallow() { return nullptr; }
    ActoidFactory *addHasteGrappleAttack() { return nullptr; }
    ActoidFactory *addHasteGrapple() { return nullptr; }
    ActoidFactory *addHasteVampiricBite() { return nullptr; }
    ActoidFactory *addHasteParalyzingMeleeAttack() { return nullptr; }
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Passive abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    void addSpellSlots()
    {
      if(_type != CombatantType::MONSTER)
        {
          _spellslots = spellslotFactory(_type, _level);
          _resources.insert({AbilityType::SPELLSLOTS, _spellslots});
        }
      else
        {
          throw std::runtime_error("Cannot use this overload of addSpellSlots for a monster.");
        }
    }

    void addSpellSlots(CombatantType type, int level)
    {
      if(_type == CombatantType::MONSTER)
        {
          _spellslots = spellslotFactory(type, level);
          _resources.insert({AbilityType::SPELLSLOTS, _spellslots});
        }
      else
        {
          throw std::runtime_error("Cannot use this overload of addSpellSlots for a non-monster.");
        }
    }

    void addSentinel() {}
    void addPolearmMaster() {}
    void addDangerSense() {}
    void addMetamagic() {}
    void addPackTactics() {}
    void addFanaticAdvantage() {}
    void addWarCaster() {}
    void addEldritchMind() {}
    void addSneakAttack() {}
    void addCunningAction() {}
    void addAssassinate() {}
    void addRegeneration() {}
    void addEvasion() {}
    void addHeartOfHruggek() {}
    void addDarkDevotion() {}
    void addBlindsight() {}
    void addMagicResistance() {}
    void addCharmImmunity() {}
    void addGreatWeaponFighting() {}
    void addDueling() {}
    void addBattleMasterManeuvers() {}
    void addDraconicResilience() {}
    void addUnarmoredDefense() {}
    void addDivineSmite() {}
    void addChannelDivinity() {}
    void addUndeadFortitude();
    void addMartialAdvantage() {}
    void addQuickenedSpell() {}
    void addTwinnedSpell() {}
    void addEmpoweredSpell() {}
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Non-action abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    void addActionSurge() {}
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

  private:
    template <typename ConditionType> Combatant *checkConditionList(const std::vector<ConditionType *> &condList, Conditions condition)
    {
      for(const auto &cond : condList)
        {
          if(containsCondition(cond->conditionComposite, condition))
            {
              return cond->initiator;
            }
        }
      return nullptr;
    }

    int doReceiveDmg(int dmg, DamageType dmg_type);

    std::string _shortCode;
    int _maxHp;
    int _currHp;
    int _maxHpModifier = 0;
    int _temporaryHp = 0;
    int _ac;
    int _dc;
    int _initBonus;
    int _spellToHit;
    int _aooFactory = 0;
    int _pamFactory = 0;
    int _abilityDmgBonus = 0;
    int _currInit = 0;
    bool _hasAction = true;
    bool _hasBonusAction = true;
    bool _hasReaction = true;
    bool _hasHasteAction = false;
    bool _alreadyUsedSpellslotThisTurn = false;
    bool _isDodging = false;
    bool _isShieldSpellActive = false;
    int _meleeReactionRange = 1;
    int _speed;
    int _movement;
    Color _teamColor;
    StateMachine _attackFsm;
    std::unordered_map<std::string, std::shared_ptr<Uses>> _ammo; // TODO: Unify this with attacks so that it's shared between them
    std::unordered_set<DamageType> _resistances;
    std::unordered_set<DamageType> _immunities;
    std::unordered_set<DamageType> _vulnerabities;
    Conditions _conditionImmunities;
    // ... Other member variables

    ActoidFactory *_dodgeFactory;
    ActoidFactory *_disengageFactory;
    ActoidFactory *_getUpFactory;
    ActoidFactory *_breakGrappleFactory;
    std::vector<ActoidFactory *> _actionFactories;
    std::vector<ActoidFactory *> _bonusActionFactories;
    std::vector<ActoidFactory *> _reactionFactories;
    std::vector<ActoidFactory *> _hasteActionFactories;
    DirectThreatFactory *_dangerZoneAttack = nullptr;
    AttackFactory *_aoOFactory = nullptr;
    std::unordered_set<AbilityType> _passiveAbilities;
    std::unordered_map<SavingThrow, int> _savingThrows
      = {{SavingThrow::STR, 0}, {SavingThrow::DEX, 0}, {SavingThrow::CON, 0}, {SavingThrow::INT, 0}, {SavingThrow::WIS, 0}, {SavingThrow::CHA, 0}};
    std::unordered_map<SavingThrow, std::vector<int>> _savingThrowsFlatMod;
    std::unordered_map<SavingThrow, std::vector<Die>> _savingThrowsDiceMod;
    std::unordered_map<SavingThrow, RollType> _savingThrowsRollTypeMod;
    std::unordered_set<DamageType> _dmgTypesTookLastRound;
    Combatant *_baseForm{this};
    Combatant *_wildshapeForm{nullptr};
    Combatant *_swallower{nullptr};
    Combatant *_swallowedTarget{nullptr};
    Combatant *_constrictedTarget{nullptr};
    std::vector<Condition *> _conditions;
    std::vector<ConditionWithDC *> _dcConditions;
    ResourceDepletionLevel _resouceDepletionLevel;
    std::shared_ptr<Spellslots> _spellslots;
    std::unordered_map<AbilityType, std::shared_ptr<Resource>> _resources;
    std::unique_ptr<ActionPlanStrategy> _actionPlanStrategy;
    std::vector<Actoid *> _actionPlan;
    int _weaponDmgDealtThisTurn = 0; // This is used for ActionSurge
    int _oneTimeAcbonus = 0; // TODO: Parry may work differently in 2024 (battle master parry reduces dmg, let's wait for monsters)
    Effect *_concentrationEffect{nullptr};
    std::vector<Wildshape *> _availableWildshapeForms;
    std::unique_ptr<blaze::DynamicMatrix<Coord>> _shortestPathsCache = nullptr; // TODO: Do I still need this?
    bool _uncannyDodgeActive = false;

  protected:
    Size _size{Size::MEDIUM};
    int _classId;
    CombatantType _type;
    SubType _subtype;
    int _level;
  };

} // namespace enc
