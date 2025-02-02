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
    std::weak_ptr<ActoidFactory> getActionFactory(AbilityType type);
    void clearAllSavingThrowMods();
    void rollForRecharge();
    const std::vector<std::shared_ptr<ActoidFactory>> &getActionFactoriesConst() const { return _actionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getBonusActionFactoriesConst() const { return _bonusActionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getReactionFactoriesConst() const { return _reactionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getHasteActionFactoriesConst() const { return _hasteActionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getActionFactories() { return _actionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getBonusActionFactories() { return _bonusActionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getReactionFactories() { return _reactionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getHasteActionFactories() { return _hasteActionFactories; }
    void setAvailableWildshapeForms(std::vector<Wildshape *> wildshapeForms) { _availableWildshapeForms = wildshapeForms; }
    const std::vector<Wildshape *> &getAvailableWildshapeForms() { return _availableWildshapeForms; }
    DirectThreatFactory* getDangerZoneAttack() { return _dangerZoneAttack; }
    void setDangerZoneAttack(DirectThreatFactory *dangerZoneAttack) { _dangerZoneAttack = dangerZoneAttack; }
    AttackFactory* getAoOFactory() { return _aoOFactory; }
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

    std::shared_ptr<ActoidFactory> addMeleeAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice, int dmgBonus,
                                                  DamageType damageType, int attackRange)
    {
      auto factory = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", name, owner, AbilityType::MELEE_ATTACK, toHit, dmgDice, dmgBonus, damageType, attackRange);
      _actionFactories.emplace_back(factory);
      return factory;
    }

    std::shared_ptr<ActoidFactory> addRangedAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice,
                                                   int dmgBonus, DamageType damageType, int attackRange)
    {
      auto factory = std::make_shared<RangedAttackFactory>("RangedAttackFactory", name, owner, AbilityType::RANGED_ATTACK, toHit, dmgDice, dmgBonus, damageType, attackRange);
      _actionFactories.emplace_back(factory);
      return factory;
    }

    std::shared_ptr<ActoidFactory> addRecklessAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addPreSwallowBite() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBiteAndSwallow() { return nullptr; }
    std::shared_ptr<ActoidFactory> addDodge() { return nullptr; }
    std::shared_ptr<ActoidFactory> addDash() { return nullptr; }
    std::shared_ptr<ActoidFactory> addDisengage() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFireball() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFirebolt() { 
      auto factory = std::make_shared<FireboltFactory>(_spellToHit, AbilityType::FIREBOLT, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;

     }
    std::shared_ptr<ActoidFactory> addChaosBolt() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHaste() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHungerOfHadar() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSpikeGrowth() { return nullptr; }
    std::shared_ptr<ActoidFactory> addCloudOfDaggers() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHide() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedFirebolt() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedHaste() { return nullptr; }
    std::shared_ptr<ActoidFactory> addScorchingRay() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFaerieFire() { return nullptr; }
    std::shared_ptr<ActoidFactory> addWildshape() { return nullptr; }
    std::shared_ptr<ActoidFactory> addPounce() { return nullptr; }
    std::shared_ptr<ActoidFactory> addConstrict() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBreakGrapple() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFlamingSphere() { return nullptr; }
    std::shared_ptr<ActoidFactory> addWeb() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHoldPerson() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedHoldPerson() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShockingGrasp() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedShockingGrasp() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMagicMissile() { return nullptr; }
    std::shared_ptr<ActoidFactory> addGrapple() { return nullptr; }
    std::shared_ptr<ActoidFactory> addGrappleAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addVampiricBite() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBless() { return nullptr; }
    std::shared_ptr<ActoidFactory> addRayOfEnfeeblement() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedRayOfEnfeeblement() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSleep() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShakeAllyAwake() { return nullptr; }
    std::shared_ptr<ActoidFactory> addThunderwave() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMenacingMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addParalyzingMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMenacingRangedAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addPrecisionAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addLayOnHands() { return nullptr; }
    std::shared_ptr<ActoidFactory> addCureWounds() { return nullptr; }
    std::shared_ptr<ActoidFactory> addAbjureEnemy() { return nullptr; }
    std::shared_ptr<ActoidFactory> addConicBreathWeapon() { return nullptr; }
    std::shared_ptr<ActoidFactory> addConicBreathWeaponAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addLineBreathWeapon() { return nullptr; }
    std::shared_ptr<ActoidFactory> addRayOfFrost() { return nullptr; }

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Bonus Action abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    std::shared_ptr<ActoidFactory> addBonusMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBonusRangedAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addPamBonusAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addRage() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTotemRage() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMistyStep() { return nullptr; }
    std::shared_ptr<ActoidFactory> addCunningDisengage() { return nullptr; }
    std::shared_ptr<ActoidFactory> addCunningDash() { return nullptr; }
    std::shared_ptr<ActoidFactory> addCunningHide() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedFireball() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedFirebolt() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedChaosBolt() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedHaste() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedHungerOfHadar() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedSpikeGrowth() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedCloudOfDaggers() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedScorchingRay() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedFaerieFire() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedBless() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedFlamingSphere() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedHoldPerson() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedRayOfFrost() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFlamingSphereRam() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMoonWildshape() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedShockingGrasp() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedMagicMissile() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedRayOfEnfeeblement() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedSleep() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSecondWind() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHealingWord() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedHealingWord() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShillelagh() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedThunderwave() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBonusMenacingMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBonusMenacingRangedAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShieldOfFaith() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedCureWounds() { return nullptr; }
    std::shared_ptr<ActoidFactory> addVowOfEnmity() { return nullptr; }
    std::shared_ptr<ActoidFactory> addAggressive() { return nullptr; }
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Reaction abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    std::shared_ptr<ActoidFactory> addReactionAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShield() { return nullptr; }
    std::shared_ptr<ActoidFactory> addPreSwallowBiteReaction() { return nullptr; }
    std::shared_ptr<ActoidFactory> addUncannyDodge() { return nullptr; }
    std::shared_ptr<ActoidFactory> addParry() { return nullptr; }
    std::shared_ptr<ActoidFactory> addRiposte() { return nullptr; }
    std::shared_ptr<ActoidFactory> addReactionParalyzingMeleeAttack() { return nullptr; }
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Haste abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    std::shared_ptr<ActoidFactory> addHasteMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteRangedAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteDash() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteDisengage() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteHide() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHastePreSwallowBite() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteBiteAndSwallow() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteGrappleAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteGrapple() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteVampiricBite() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHasteParalyzingMeleeAttack() { return nullptr; }
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

    std::shared_ptr<ActoidFactory> _dodgeFactory;
    std::shared_ptr<ActoidFactory> _disengageFactory;
    std::vector<std::shared_ptr<ActoidFactory>> _actionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _bonusActionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _reactionFactories;
    std::vector<std::shared_ptr<ActoidFactory>> _hasteActionFactories;
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
