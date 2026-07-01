#pragma once

#include <any>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <deque>
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
#include "spells/firebolt.hpp"
#include "spells/ray_of_frost.hpp"
#include "spells/scorching_ray.hpp"
#include "spells/hold_person.hpp"
#include "spells/spike_growth.hpp"
#include "spells/faerie_fire.hpp"
#include "spells/flaming_sphere.hpp"
#include "spells/moonbeam.hpp"
#include "spells/misty_step.hpp"
#include "spells/shield.hpp"
#include "spells/innate_sorcery.hpp"
#include "spells/healing_word.hpp"
#include "spells/cure_wounds.hpp"
#include "spells/bless.hpp"
#include "spells/guiding_bolt.hpp"
#include "spells/sacred_flame.hpp"
#include "spells/shield_of_faith.hpp"
#include "spells/starry_wisp.hpp"
#include "spells/toll_the_dead.hpp"
#include "spells/thunderwave.hpp"
#include "spells/magic_missile.hpp"
#include "spells/mage_armor.hpp"
#include "spells/sleep.hpp"
#include "spells/vicious_mockery.hpp"
#include "spells/dissonant_whispers.hpp"
#include "spells/bane.hpp"
#include "spells/charm_person.hpp"
#include "spells/color_spray.hpp"
#include "spells/eldritch_blast.hpp"
#include "spells/hex.hpp"
#include "spells/armor_of_agathys.hpp"
#include "spells/darkness.hpp"
#include "spells/hypnotic_pattern.hpp"
#include "spells/blink.hpp"
#include "abilities/bardic_inspiration.hpp"
#include "abilities/cutting_words.hpp"
#include "abilities/on_hit_grapple.hpp"
#include "abilities/on_hit_prone.hpp"
#include "abilities/on_hit_saving_throw_dmg.hpp"
#include "abilities/pounce.hpp"
#include "abilities/roar.hpp"
#include "abilities/rage.hpp"
#include "abilities/reckless_attack.hpp"
#include "abilities/on_hit_mastery.hpp"
#include "abilities/on_hit_sneak_attack.hpp"
#include "actions/dash.hpp"
#include "actions/disengage.hpp"
#include "actions/hide.hpp"
#include "abilities/second_wind.hpp"
#include "abilities/action_surge.hpp"
#include "abilities/riposte.hpp"
#include "abilities/lay_on_hands.hpp"
#include "abilities/on_hit_divine_smite.hpp"
#include "abilities/vow_of_enmity.hpp"
#include "actions/smite_melee_attack.hpp"
#include "effects/effect.hpp"
#include "core/state_machine.hpp"
#include "core/attack_fsm.hpp"

namespace enc
{

  class Wildshape;

  using FactoryCreator = std::function<std::shared_ptr<ActoidFactory>()>;

  class Combatant/* : public ICombatant*/
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
      // thread_local: each worker thread numbers its own combatants independently (deterministic per
      // thread, no data race) so parallel simulations stay self-contained.
      static thread_local int nextId = 1;
      return ++nextId;
    }

    std::string toString() const;
    void setShortCode(const std::string &shortCode) { _shortCode = shortCode; }
    std::string getShortCode() const { return _shortCode; }
    virtual int getClassId() const = 0;

    bool isAlive() const;
    void onDie();
    void onEndOfTurn();
    void rollInitiative();
    void reset();
    void newTurn();
    void setSize(Size size) { _size = size; };
    Size getSize() const { return _size; };
    int getAC() const { return _ac; };
    void setAC(int ac) { _ac = ac; };
    void setTeamColor(Color teamColor) { _teamColor = teamColor; }
    bool hasAction() const { return _hasAction; }
    bool hasBonusAction() const { return _hasBonusAction; }
    bool hasHasteAction() const { return _hasHasteAction; }
    bool hasReaction() const { return _hasReaction; }
    void setHasAction(bool has) { _hasAction = has; }
    void setHasBonusAction(bool has) { _hasBonusAction = has; }
    void setHasHasteAction(bool has) { _hasHasteAction = has; }
    void setHasReaction(bool has) { _hasReaction = has; }
    bool hasAlreadyUsedSpellslotThisTurn() { return _alreadyUsedSpellslotThisTurn; }
    void setAlreadyUsedSpellslotThisTurn(bool used) { _alreadyUsedSpellslotThisTurn = used; }
    // Shield (reaction): +5 AC until the start of the caster's next turn, where newTurn()/reset() undo it.
    bool isShieldSpellActive() const { return _isShieldSpellActive; }
    void applyShieldSpell()
    {
      if(!_isShieldSpellActive)
        {
          _ac += 5;
          _isShieldSpellActive = true;
        }
    }
    // Innate Sorcery (2024): while active the caster has advantage on its own spell attack rolls.
    bool isInnateSorceryActive() const { return _innateSorceryActive; }
    void setInnateSorceryActive(bool active) { _innateSorceryActive = active; }
    // Uncanny Dodge (reaction): while active the next incoming damage instance is halved in doReceiveDmg.
    bool isUncannyDodgeActive() const { return _uncannyDodgeActive; }
    void setUncannyDodgeActive(bool active) { _uncannyDodgeActive = active; }
    bool hasPendingDivineSmite() const { return _pendingDivineSmite; }
    void armDivineSmite() { _pendingDivineSmite = true; }
    void clearPendingDivineSmite() { _pendingDivineSmite = false; }
    int getMeleeReactionRange() { return _meleeReactionRange; }
    Combatant *getCurrentForm();
    Combatant *getOriginalForm();
    void setOriginalForm(Combatant *form) { _originalForm = form; };
    void setCurrentWildshapeForm(Combatant *form) { _currentWildshapeForm = form; };
    Combatant *getCurrentWildshapeForm() { return _currentWildshapeForm; };
    Combatant *getSwallower() const { return _swallower; }
    void setSwallower(Combatant *swallower) { _swallower = swallower; }
    bool isSwallowed() const { return _swallower != nullptr; }
    //! While Blinked into the Border Ethereal, the creature can't be targeted or affected by anything on the
    //! material plane (it returns at the start of its next turn). Modeled by excluding it from enemy/ally
    //! target lists, mirroring how a swallowed creature is untargetable.
    bool isEtherealUntargetable() const { return _etherealUntargetable; }
    void setEtherealUntargetable(bool value) { _etherealUntargetable = value; }
    //! A creature is a valid target only while it is alive, not swallowed by another creature, and not
    //! Blinked into the Border Ethereal.
    bool isTargetable() const { return isAlive() && !isSwallowed() && !isEtherealUntargetable(); }
    const std::vector<Condition> &getConditions() const { return _conditions; }
    const std::vector<ConditionWithDC> &getDCConditions() const { return _dcConditions; }
    bool isAffectedBy(Conditions condition) const;
    void applyCondition(const Condition &condition);
    void applyDCCondition(const ConditionWithDC &dcCondition);
    bool removeCondition(Conditions condition, const Combatant *initiator = nullptr);
    bool removeDCCondition(Conditions condition, const Combatant *initiator = nullptr);
    void removeAllConditionsOfType(Conditions condition);
    Combatant *getInitiatorOfCondition(Conditions condition);
    Combatant *getGrappledTarget();
    std::optional<ConditionWithDC> needsToBreakOutOfGrapple();
    void breakOutOfGrapple();
    // 2024: a grapple ends if the grappler gains the Incapacitated condition. Call at the start of the
    // grappled creature's turn to release it from a grapple whose grappler can no longer maintain it.
    void endGrappleIfGrapplerIncapacitated()
    {
      Combatant *grappler = getInitiatorOfCondition(Conditions::GRAPPLED);
      if(grappler != nullptr && grappler->isAffectedBy(Conditions::INCAPACITATED))
        {
          grappler->removeCondition(Conditions::GRAPPLING);
          removeAllConditionsOfType(Conditions::GRAPPLED);
        }
    }
    void setConcentrationEffect(std::shared_ptr<Effect> effect);
    std::weak_ptr<Effect> getConcentrationEffect() { return _concentrationEffect; }
    void breakConcentration();
    bool isConcentrating() const;
    bool isAffectedByAny(const std::vector<Conditions> &conditions) const;
    bool isImmuneToCondition(Conditions condition) const { return containsCondition(_conditionImmunities, condition); }
    void setResourceDepletionLevel(ResourceDepletionLevel level) { _resouceDepletionLevel = level; }
    bool isImmuneTo(DamageType dmgType);
    bool isResistantTo(DamageType dmgType);
    bool isVulnerableTo(DamageType dmgType);
    Spellslots &getSpellslots() { return *_spellslots; }
    std::optional<Resource *> getResource(AbilityType type)
    {
      auto it = _resources.find(type);
      if(it == _resources.end())
        {
          return std::nullopt;
        }
      return it->second.get();
    }
    int getLevel() const { return _level; }
    int getDC() const { return _dc; }
    //! The caster's spellcasting ability modifier, derived from the spell save DC (DC = 8 + proficiency +
    //! ability modifier). Used by heals such as Healing Word / Cure Wounds.
    int getSpellcastingModifier() const { return _dc - 8 - (2 + (_level - 1) / 4); }
    //! The spell-slot level a leveled spell with the given base level is actually cast at. A Warlock's Pact
    //! Magic only has slots at a single (highest) level and automatically upcasts every spell to it, so for
    //! Warlocks this returns that pact-slot level (never below the spell's own base level). Every other caster
    //! casts at the spell's base level.
    int getCastingSlotLevel(int spellBaseLevel) const
    {
      if(_type == CombatantType::WARLOCK && _spellslots)
        {
          return std::max(spellBaseLevel, _spellslots->getMaxSlotLevel());
        }
      return spellBaseLevel;
    }
    // A creature is humanoid if it's a player-class combatant or a monster of the Humanoid type
    // (used by spells such as Hold Person that only affect humanoids).
    bool isHumanoid() const
    {
      if(_type != CombatantType::MONSTER)
        {
          return true;
        }
      return std::holds_alternative<Monster>(_subtype) && std::get<Monster>(_subtype) == Monster::HUMANOID;
    }
    bool isMonsterType(Monster monsterType) const
    {
      return _type == CombatantType::MONSTER && std::holds_alternative<Monster>(_subtype) && std::get<Monster>(_subtype) == monsterType;
    }
    int getCurrentHp() const { return _currHp; }
    void setCurrentHp(int hp) { _currHp = hp; }
    int getMaxHp() const { return _maxHp; }
    void setTemporaryHp(int hp) { _temporaryHp = std::max(_temporaryHp, hp); }
    int getTemporaryHp() { return _temporaryHp; }
    //! Drop any temporary hit points (e.g. when a Wild Shape ends).
    void clearTemporaryHp() { _temporaryHp = 0; }
    int getCurrentInit() const { return _currInit; }
    int getMovement() const { return _movement; }
    void setMovement(int movement) { _movement = movement; }
    bool hasMovement(int dist = 1) const { return _movement >= dist; }
    void decrementMovement(int dist = 1) { _movement -= dist; }
    int getSpeed() const { return _speed; }

    //! Flat bonus added to the damage of the combatant's Strength-based melee attacks (e.g. the Barbarian's
    //! Rage Damage). Toggled on/off by the Rage effect and consumed by resolveAttack.
    int getAbilityDmgBonus() const { return _abilityDmgBonus; }
    void addAbilityDmgBonus(int delta) { _abilityDmgBonus += delta; }
    void setSpeed(int speed) { _speed = speed; }
    bool hasPassiveAbility(AbilityType ability) const;
    //! Make an ability check against @p dc using @p bonus, applying Tactical Mind (2024 Fighter, level 2):
    //! on a failed check the fighter may expend a use of Second Wind to add 1d10, and the use is only spent
    //! if that 1d10 turns the failure into a success.
    bool attemptAbilityCheck(int bonus, int dc, RollType rollType = RollType::STRAIGHT);
    // Current number of Metamagic sorcery points (0 if the combatant has no Metamagic resource).
    int getSorceryPoints() const;
    // Spend Metamagic sorcery points (no-op if the combatant has no Metamagic resource).
    void consumeSorceryPoints(int amount);
    // Attack FSM (multiattack gating). Combatants register transitions keyed by their attack factories; the FSM is
    // reset to its start state at the beginning of each turn and advanced as attacks are spent.
    void addAttackTransition(const ActoidFactory *factory, int origin, int destination) { _attackFsm.addTransition(factory, origin, destination); }
    bool isAttackFsmAtStart() const { return _attackFsm.isAtStart(); }
    bool attackFsmHasTransition(const ActoidFactory *factory) const { return _attackFsm.hasAvailableTransition(factory); }
    void triggerAttackFsm(const ActoidFactory *factory) { _attackFsm.trigger(factory); }
    int getAttackFsmState() const { return _attackFsm.getState(); }
    void setAttackFsmState(int state) { _attackFsm.setState(state); }
    //! Whole finite-state-machine accessors used by Wild Shape to temporarily adopt a beast's multiattack pattern.
    const AttackFsm &getAttackFsm() const { return _attackFsm; }
    void setAttackFsm(const AttackFsm &fsm) { _attackFsm = fsm; }
    const std::unordered_map<SavingThrow, int> &getSavingThrows() { return _savingThrows; }
    int getSavingThrow(SavingThrow st) { return _savingThrows.at(st); }
    void setSavingThrow(SavingThrow st, int value) { _savingThrows.at(st) = value; }
    int getAthletics() const { return _athletics; }
    void setAthletics(int value) { _athletics = value; }
    int getAcrobatics() const { return _acrobatics; }
    void setAcrobatics(int value) { _acrobatics = value; }
    int getStealth() const { return _stealth; }
    void setStealth(int value) { _stealth = value; }
    int getPassivePerception() const { return _passivePerception; }
    void setPassivePerception(int value) { _passivePerception = value; }
    bool hasAlreadyUsedSneakAttackThisTurn() const { return _alreadyUsedSneakAttackThisTurn; }
    void setAlreadyUsedSneakAttackThisTurn(bool used) { _alreadyUsedSneakAttackThisTurn = used; }
    const std::vector<int> &getSavingThrowFlatMods(SavingThrow type) const;
    void addSavingThrowFlatMod(SavingThrow type, int mod);
    void clearSavingThrowFlatMods(SavingThrow type);
    const std::vector<Die> &getSavingThrowDiceMods(SavingThrow type) const;
    void addSavingThrowDiceMod(SavingThrow type, const Die &mod);
    void removeSavingThrowDiceMod(SavingThrow type, const Die &mod);
    void clearSavingThrowDiceMods(SavingThrow type);
    const std::vector<Die> &getToHitDiceMods() const { return _toHitDiceMod; }
    void addToHitDiceMod(const Die &mod) { _toHitDiceMod.push_back(mod); }
    void removeToHitDiceMod(const Die &mod);
    void clearToHitDiceMods() { _toHitDiceMod.clear(); }
    // Penalty dice (e.g. Bane's 1d4) are rolled and subtracted from the relevant roll. Stored separately
    // from bonus dice because Die is unsigned and cannot represent a negative modifier directly.
    const std::vector<Die> &getToHitPenaltyDice() const { return _toHitPenaltyDice; }
    void addToHitPenaltyDie(const Die &mod) { _toHitPenaltyDice.push_back(mod); }
    void removeToHitPenaltyDie(const Die &mod);
    const std::vector<Die> &getSavingThrowPenaltyDice(SavingThrow type) const;
    void addSavingThrowPenaltyDie(SavingThrow type, const Die &mod);
    void removeSavingThrowPenaltyDie(SavingThrow type, const Die &mod);
    const std::unordered_set<RollType> &getSavingThrowRollTypeMods(SavingThrow type) const;
    void addSavingThrowRollTypeMod(SavingThrow type, RollType rollType);
    void removeSavingThrowRollTypeMod(SavingThrow type, RollType rollType);
    void clearSavingThrowRollTypeMods(SavingThrow type);
    std::weak_ptr<ActoidFactory> getActionFactory(AbilityType type);
    void clearAllSavingThrowMods();
    void rollForRecharge();
    const std::vector<std::shared_ptr<ActoidFactory>> &getActionFactoriesConst() { return _actionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getBonusActionFactoriesConst() { return _bonusActionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getReactionFactoriesConst() { return _reactionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getHasteActionFactoriesConst() { return _hasteActionFactories; }
    const std::vector<std::shared_ptr<ActoidFactory>> &getFreeActionFactoriesConst() { return _freeActionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getActionFactories() { return _actionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getBonusActionFactories() { return _bonusActionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getReactionFactories() { return _reactionFactories; }
    std::vector<std::shared_ptr<ActoidFactory>> &getHasteActionFactories() { return _hasteActionFactories; }
    void setAvailableWildshapeForms(std::vector<std::shared_ptr<Wildshape>> wildshapeForms) { _availableWildshapeForms = wildshapeForms; }
    const std::vector<std::shared_ptr<Wildshape>> &getAvailableWildshapeForms() { return _availableWildshapeForms; }
    DirectThreatFactory *getDangerZoneAttack() { 
      return _dangerZoneAttack;
    }
    void setDangerZoneAttack(DirectThreatFactory* factory) {
      _dangerZoneAttack = factory;
    }
    AttackFactory* getAoOFactory() { return _aoOFactory; }
    void setAoOFactory(AttackFactory* factory) { _aoOFactory = factory; }
    //! On-demand Riposte reaction attack factory (Battle Master). Null if the combatant has no maneuvers.
    AttackFactory* getRiposteFactory() { return _riposteFactory; }
    //! Class id of the beast currently shaped into (0 = not wild-shaped). Used to forbid reshaping into the same form.
    int getActiveWildshapeFormId() const { return _activeWildshapeFormId; }
    void setActiveWildshapeFormId(int classId) { _activeWildshapeFormId = classId; }
    void setShortestPathsCache(const blaze::DynamicMatrix<Coord> &shortestPaths) { _shortestPathsCache = shortestPaths; }
    const blaze::DynamicMatrix<Coord> &getShortestPathsCache() const { return _shortestPathsCache; }
    std::deque<std::shared_ptr<Actoid>> &getActionPlan() { return _actionPlan; }
    void setActionPlan(std::deque<std::shared_ptr<Actoid>> plan) { _actionPlan = std::move(plan); }
    std::deque<std::shared_ptr<Actoid>> calculateActionPlan(const blaze::DynamicVector<int> &distances,
                                                            const blaze::DynamicMatrix<Coord> &shortestPaths);
    // Snapshot/restore of resource state during proto-DAG exploration. The base implementation preserves the action
    // economy (action/bonus/reaction/haste flags, movement, spell-slot usage) and every action factory's ammo, so that
    // the speculative useResources() calls made while exploring the DAG don't permanently drain the combatant
    // (mirrors Python's per-combatant export_resources()/import_resources()). Specialized combatants may override.
    virtual std::any exportResources();
    virtual void importResources(const std::any &resources);
    int receiveDmg(int dmg, DamageType dmg_type, int multiplier = 1);
    int receiveCompoundDmg(const std::vector<std::pair<int, DamageType>>& dmg, int multiplier = 1);
    void addResistance(DamageType dmgType);
    void removeResistance(DamageType dmgType);
    void addImmunity(DamageType dmgType);
    void removeImmunity(DamageType dmgType);
    void addVulnerability(DamageType dmgType);
    void removeVulnerability(DamageType dmgType);
    bool isDodging() { return _isDodging; }
    //! When disengaging, the combatant's movement does not provoke opportunity attacks this turn.
    bool isDisengaging() const { return _isDisengaging; }
    void setDisengaging(bool value) { _isDisengaging = value; }
    //! Claim a once-per-turn weapon mastery (e.g. Cleave). Returns false if it was already used this turn.
    bool tryUseMasteryThisTurn(WeaponMastery mastery)
    {
      return _masteriesUsedThisTurn.insert(mastery).second;
    }
    /**
     * Handles concentration checks when a combatant takes damage.
     *
     * @param combatant The combatant who needs to make the concentration check
     * @param dmg The amount of damage that triggered the check
     * @return true if concentration was maintained, false if it was lost
     */
    bool checkConcentration(Combatant *combatant, int dmg);

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Action abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    std::shared_ptr<ActoidFactory> addMeleeAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice, int dmgBonus,
                                                  DamageType damageType, int attackRange, bool usesDex = false)
    {
      auto factory = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", name, owner, AbilityType::MELEE_ATTACK, toHit, dmgDice, dmgBonus,
                                                          damageType, attackRange, 1, Uses(), std::vector<std::unique_ptr<OnHit>>{},
                                                          std::vector<DmgDieWithType>{}, usesDex);
      _actionFactories.emplace_back(factory);
      return factory;
    }

    //! Melee attack carrying on-hit riders (e.g. a beast's knock-Prone or save-for-half venom) and/or
    //! always-applied extra damage dice. Mirrors the Python add_ability(MELEE_ATTACK, ..., on_hit=[...]).
    std::shared_ptr<ActoidFactory> addMeleeAttackWithRiders(const std::string &name, Combatant *owner, int toHit,
                                                            const std::vector<Die> &dmgDice, int dmgBonus, DamageType damageType, int attackRange,
                                                            std::vector<std::unique_ptr<OnHit>> onHit,
                                                            std::vector<DmgDieWithType> extraDmg = {})
    {
      auto factory = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", name, owner, AbilityType::MELEE_ATTACK, toHit, dmgDice, dmgBonus,
                                                          damageType, attackRange, 1, Uses(), std::move(onHit), std::move(extraDmg));
      _actionFactories.emplace_back(factory);
      return factory;
    }

    std::shared_ptr<ActoidFactory> addRangedAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice,
                                                   int dmgBonus, DamageType damageType, int attackRange, int ammo = Uses::INFINITE_USES)
    {
      auto factory = std::make_shared<RangedAttackFactory>("RangedAttackFactory", name, owner, AbilityType::RANGED_ATTACK, toHit, dmgDice,
                                                           dmgBonus, damageType, attackRange, 1,
                                                           ammo == Uses::INFINITE_USES ? Uses() : Uses(ammo));
      _actionFactories.emplace_back(factory);
      return factory;
    }

    //! Ranged attack carrying on-hit riders and/or always-applied extra damage dice (e.g. a Fire Giant's Hammer
    //! Throw with rider Fire damage, a Frost Giant's Great Bow with rider Cold damage). Mirrors the melee
    //! addMeleeAttackWithRiders.
    std::shared_ptr<ActoidFactory> addRangedAttackWithRiders(const std::string &name, Combatant *owner, int toHit,
                                                             const std::vector<Die> &dmgDice, int dmgBonus, DamageType damageType, int attackRange,
                                                             std::vector<std::unique_ptr<OnHit>> onHit,
                                                             std::vector<DmgDieWithType> extraDmg = {}, int ammo = Uses::INFINITE_USES)
    {
      auto factory = std::make_shared<RangedAttackFactory>("RangedAttackFactory", name, owner, AbilityType::RANGED_ATTACK, toHit, dmgDice,
                                                           dmgBonus, damageType, attackRange, 1,
                                                           ammo == Uses::INFINITE_USES ? Uses() : Uses(ammo), std::move(onHit), std::move(extraDmg));
      _actionFactories.emplace_back(factory);
      return factory;
    }

    //! Reckless Attack (Barbarian): a two-handed melee Strength attack made with Advantage that, until the
    //! barbarian's next turn, also lets enemies attack it with Advantage. Registered as an Action factory.
    std::shared_ptr<ActoidFactory> addRecklessAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice,
                                                     int dmgBonus, DamageType damageType, int attackRange)
    {
      auto factory = std::make_shared<RecklessAttackFactory>(name, owner, toHit, dmgDice, dmgBonus, damageType, attackRange);
      _actionFactories.emplace_back(factory);
      return factory;
    }
    //! Attach a 2024 weapon-mastery property to a weapon's attack factory. Graze is stored as on-miss damage
    //! (the attack's ability modifier); the on-hit masteries are bolted on as an OnHitMastery rider. Nick and
    //! None add no rider here.
    void applyWeaponMastery(const std::shared_ptr<ActoidFactory> &factory, WeaponMastery mastery)
    {
      auto *attackFactory = dynamic_cast<AttackFactory *>(factory.get());
      if(attackFactory == nullptr || mastery == WeaponMastery::NONE)
        {
          return;
        }
      attackFactory->setMastery(mastery);
      if(mastery == WeaponMastery::GRAZE)
        {
          attackFactory->setGrazeDamage(attackFactory->getDmgBonus());
        }
      else if(mastery != WeaponMastery::NICK)
        {
          attackFactory->addOnHit(std::make_unique<OnHitMastery>(mastery));
        }
    }
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
    std::shared_ptr<ActoidFactory> addStarryWisp()
    {
      auto factory = std::make_shared<StarryWispFactory>(_spellToHit, AbilityType::STARRY_WISP, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addHungerOfHadar() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSpikeGrowth()
    {
      auto factory = std::make_shared<SpikeGrowthFactory>(AbilityType::SPIKE_GROWTH, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addCloudOfDaggers() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHide() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedFirebolt() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedHaste() { return nullptr; }
    std::shared_ptr<ActoidFactory> addScorchingRay()
    {
      auto factory = std::make_shared<ScorchingRayFactory>(_spellToHit, AbilityType::SCORCHING_RAY, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addFaerieFire() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFaerieFire(int dc)
    {
      auto factory = std::make_shared<FaerieFireFactory>(dc, AbilityType::FAERIE_FIRE, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addPounce() { return nullptr; }
    //! Register a Pounce action built from a (suppressed) primary attack carrying the Prone rider and a
    //! (suppressed) secondary follow-up attack. The primary/secondary are owned by the PounceFactory and are
    //! NOT registered as independent actions. `distance` is the straight-line charge length in cells.
    std::shared_ptr<ActoidFactory> addPounce(std::shared_ptr<MeleeAttackFactory> primary, std::shared_ptr<MeleeAttackFactory> secondary, int distance)
    {
      auto factory = std::make_shared<PounceFactory>(this, std::move(primary), std::move(secondary), distance);
      _actionFactories.emplace_back(factory);
      return factory;
    }
    //! Register a Roar action: a WIS-save Frighten affecting enemies within `range` cells of the roarer.
    std::shared_ptr<ActoidFactory> addRoar(int dc, int range)
    {
      auto factory = std::make_shared<RoarFactory>(this, dc, range);
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addConstrict() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBreakGrapple() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFlamingSphere() { return nullptr; }
    std::shared_ptr<ActoidFactory> addFlamingSphere(int dc)
    {
      auto factory = std::make_shared<FlamingSphereFactory>(dc, AbilityType::FLAMING_SPHERE, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addMoonbeam(int dc)
    {
      auto factory = std::make_shared<MoonbeamFactory>(dc, AbilityType::MOONBEAM, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    //! Darkness (2024): level-2 Concentration spell creating a 15-foot sphere of magical darkness that Blinds
    //! creatures inside it (except those with Devil's Sight). Modeled with no lighting system as a Blinding
    //! sphere effect.
    std::shared_ptr<ActoidFactory> addDarkness()
    {
      auto factory = std::make_shared<DarknessFactory>(AbilityType::DARKNESS, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    //! Hypnotic Pattern (2024): level-3 Concentration spell. Creatures in a 30-foot cube that fail a Wisdom
    //! save are Charmed + Incapacitated (Speed 0) until they take damage or are shaken awake.
    std::shared_ptr<ActoidFactory> addHypnoticPattern()
    {
      auto factory = std::make_shared<HypnoticPatternFactory>(_dc, AbilityType::HYPNOTIC_PATTERN, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    //! Blink (2024): level-3 self buff. At the end of each of the caster's turns, a d6 of 4-6 sends it into
    //! the Border Ethereal until the start of its next turn, making it untargetable. Lasts 1 minute, no
    //! Concentration.
    std::shared_ptr<ActoidFactory> addBlink()
    {
      auto factory = std::make_shared<BlinkFactory>(AbilityType::BLINK, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addWeb() { return nullptr; }
    std::shared_ptr<ActoidFactory> addHoldPerson()
    {
      auto factory = std::make_shared<HoldPersonFactory>(_dc, AbilityType::HOLD_PERSON, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addTwinnedHoldPerson() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShockingGrasp() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedShockingGrasp() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMagicMissile()
    {
      auto factory = std::make_shared<MagicMissileFactory>(AbilityType::MAGIC_MISSILE, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addGrapple() { return nullptr; }
    std::shared_ptr<ActoidFactory> addGrappleAttack() { return nullptr; }

    /**
     * Add a melee attack that, on a hit, applies the 2024 Grappled condition to the target
     * (escape DC = escapeDC, escaped with a Strength (Athletics) or Dexterity (Acrobatics) check)
     * and gives this combatant the Grappling condition pointing at the target.
     * Mirrors the Python OnHitAutoRestrained rider, adapted to the 2024 Grab (Grappled only).
     */
    std::shared_ptr<ActoidFactory> addGrappleAttack(const std::string &name, Combatant *owner, int toHit,
                                                    const std::vector<Die> &dmgDice, int dmgBonus, DamageType damageType,
                                                    int attackRange, int escapeDC, SkillCheck escapeSkill = SkillCheck::ATHLETICS)
    {
      std::vector<std::unique_ptr<OnHit>> onHit;
      onHit.push_back(std::make_unique<OnHitGrapple>(escapeDC, escapeSkill));
      auto factory = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", name, owner, AbilityType::MELEE_ATTACK, toHit,
                                                          dmgDice, dmgBonus, damageType, attackRange, 1, Uses(), std::move(onHit));
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addVampiricBite() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBless()
    {
      auto factory = std::make_shared<BlessFactory>(AbilityType::BLESS, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addRayOfEnfeeblement() { return nullptr; }
    std::shared_ptr<ActoidFactory> addTwinnedRayOfEnfeeblement() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSleep()
    {
      auto factory = std::make_shared<SleepFactory>(_dc, AbilityType::SLEEP, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addShakeAllyAwake() { return nullptr; }
    std::shared_ptr<ActoidFactory> addThunderwave() { return nullptr; }
    std::shared_ptr<ActoidFactory> addThunderwave(int dc)
    {
      auto factory = std::make_shared<ThunderwaveFactory>(dc, AbilityType::THUNDERWAVE, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addMenacingMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addParalyzingMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addMenacingRangedAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addPrecisionAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addLayOnHands()
    {
      auto resource = std::make_shared<Uses>(LayOnHandsFactory::getPoolSize(_level), ResourceRefreshType::LONG_REST);
      _resources.insert({AbilityType::LAY_ON_HANDS, resource});
      auto factory = std::make_shared<LayOnHandsFactory>(this, resource.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addCureWounds()
    {
      auto factory = std::make_shared<CureWoundsFactory>(this, _spellslots.get(), getSpellcastingModifier());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addAbjureEnemy() { return nullptr; }
    std::shared_ptr<ActoidFactory> addConicBreathWeapon() { return nullptr; }
    std::shared_ptr<ActoidFactory> addConicBreathWeaponAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addLineBreathWeapon() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSacredFlame()
    {
      auto factory = std::make_shared<SacredFlameFactory>(_dc, AbilityType::SACRED_FLAME, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addViciousMockery()
    {
      auto factory = std::make_shared<ViciousMockeryFactory>(_dc, AbilityType::VICIOUS_MOCKERY, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addDissonantWhispers()
    {
      auto factory = std::make_shared<DissonantWhispersFactory>(_dc, AbilityType::DISSONANT_WHISPERS, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addBane()
    {
      auto factory = std::make_shared<BaneFactory>(_dc, AbilityType::BANE, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addCharmPerson()
    {
      auto factory = std::make_shared<CharmPersonFactory>(_dc, AbilityType::CHARM_PERSON, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addColorSpray()
    {
      auto factory = std::make_shared<ColorSprayFactory>(_dc, AbilityType::COLOR_SPRAY, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addTollTheDead()
    {
      auto factory = std::make_shared<TollTheDeadFactory>(_dc, AbilityType::TOLL_THE_DEAD, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addGuidingBolt()
    {
      auto factory = std::make_shared<GuidingBoltFactory>(_spellToHit, AbilityType::GUIDING_BOLT, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addRayOfFrost()
    {
      auto factory = std::make_shared<RayOfFrostFactory>(_spellToHit, AbilityType::RAY_OF_FROST, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addMageArmor(int armoredBaseAc)
    {
      auto factory = std::make_shared<MageArmorFactory>(this, _spellslots.get(), armoredBaseAc);
      _actionFactories.emplace_back(factory);
      return factory;
    }
    //! Armor of Shadows (Eldritch Invocation). The warlock can cast Mage Armor on itself at will without
    //! expending a spell slot, so it reuses the Mage Armor effect but under its own ability type (no slot gate).
    std::shared_ptr<ActoidFactory> addArmorOfShadows(int armoredBaseAc)
    {
      auto factory = std::make_shared<MageArmorFactory>(this, nullptr, armoredBaseAc, AbilityType::ARMOR_OF_SHADOWS);
      _actionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addEldritchBlast()
    {
      auto factory = std::make_shared<EldritchBlastFactory>(_spellToHit, AbilityType::ELDRITCH_BLAST, this, _spellslots.get());
      _actionFactories.emplace_back(factory);
      return factory;
    }

    //! Agonizing Blast (Eldritch Invocation). Adds the warlock's spellcasting modifier to each Eldritch
    //! Blast beam's damage. Must be called after addEldritchBlast().
    void addAgonizingBlast()
    {
      for(auto &factory : _actionFactories)
        {
          if(auto *eb = dynamic_cast<EldritchBlastFactory *>(factory.get()))
            {
              eb->setAgonizingBlast(getSpellcastingModifier());
            }
        }
    }

    //! Repelling Blast (Eldritch Invocation). A hit Large-or-smaller target is pushed 10 ft away from the
    //! warlock. Must be called after addEldritchBlast().
    void addRepellingBlast()
    {
      for(auto &factory : _actionFactories)
        {
          if(auto *eb = dynamic_cast<EldritchBlastFactory *>(factory.get()))
            {
              eb->setRepellingBlast();
            }
        }
    }

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
    //! Rage (Path of the Wild Heart, 2024). Registers the shared pool of Rage uses (refreshed on a long
    //! rest) and offers the three Rage of the Wilds animal aspects (Bear, Eagle, Wolf) as separate bonus
    //! action options drawing from that pool. Returns the first (Bear) factory.
    std::shared_ptr<ActoidFactory> addRage()
    {
      auto resource = std::make_shared<Uses>(RageFactory::getRageUses(_level), ResourceRefreshType::LONG_REST);
      _resources.insert({AbilityType::RAGE, resource});
      std::shared_ptr<ActoidFactory> first;
      for(RageVariant variant : {RageVariant::BEAR, RageVariant::EAGLE, RageVariant::WOLF})
        {
          auto factory = std::make_shared<RageFactory>(this, resource.get(), variant, AbilityType::RAGE);
          _bonusActionFactories.emplace_back(factory);
          if(!first)
            {
              first = factory;
            }
        }
      return first;
    }
    std::shared_ptr<ActoidFactory> addMistyStep()
    {
      auto factory = std::make_shared<MistyStepFactory>(this, _spellslots.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }

    //! Innate Sorcery (2024): bonus action, twice per long rest. Registers its limited-use resource and
    //! a self-targeting threat-modifier factory whose threat reflects the advantage it grants the
    //! caster's own spell attacks (see InnateSorceryFactory).
    std::shared_ptr<ActoidFactory> addInnateSorcery()
    {
      auto resource = std::make_shared<Uses>(InnateSorceryFactory::maxUses, ResourceRefreshType::LONG_REST);
      _resources.insert({AbilityType::INNATE_SORCERY, resource});
      auto factory = std::make_shared<InnateSorceryFactory>(this, resource.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
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
    //! Circle of the Moon Wild Shape (bonus action). Registers a 2-uses-per-short-rest resource and a
    //! WildshapeFactory bound to it. Defined out of line in combatant.cpp to avoid a circular include with
    //! abilities/wildshape.hpp.
    std::shared_ptr<ActoidFactory> addMoonWildshape();
    //! Generic (non-Moon) Wild Shape (bonus action). Same wiring as addMoonWildshape but with the WILDSHAPE
    //! ability type (druid-level temporary hit points, plain beast AC).
    std::shared_ptr<ActoidFactory> addWildshape();
    std::shared_ptr<ActoidFactory> addQuickenedShockingGrasp() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedMagicMissile() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedRayOfEnfeeblement() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedSleep() { return nullptr; }
    std::shared_ptr<ActoidFactory> addSecondWind()
    {
      // 2024 Second Wind: a self-heal of 1d10 + Fighter level, refreshed on a Short or Long Rest (one use,
      // mirroring the Python combatant).
      auto resource = std::make_shared<Uses>(1, ResourceRefreshType::SHORT_REST);
      _resources.insert({AbilityType::SECOND_WIND, resource});
      auto factory = std::make_shared<SecondWindFactory>(this, resource.get(), _level);
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addHealingWord()
    {
      auto factory = std::make_shared<HealingWordFactory>(this, _spellslots.get(), getSpellcastingModifier());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addTwinnedHealingWord() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShillelagh() { return nullptr; }
    std::shared_ptr<ActoidFactory> addQuickenedThunderwave() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBonusMenacingMeleeAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addBonusMenacingRangedAttack() { return nullptr; }
    std::shared_ptr<ActoidFactory> addShieldOfFaith()
    {
      auto factory = std::make_shared<ShieldOfFaithFactory>(this, _spellslots.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addBardicInspiration()
    {
      auto resource = getResource(AbilityType::BARDIC_INSPIRATION);
      if(!resource)
        {
          auto pool = std::make_shared<Uses>(BardicInspirationFactory::getUses(getSpellcastingModifier()), ResourceRefreshType::LONG_REST);
          _resources.insert({AbilityType::BARDIC_INSPIRATION, pool});
          resource = pool.get();
        }
      auto factory = std::make_shared<BardicInspirationFactory>(AbilityType::BARDIC_INSPIRATION, this, resource.value());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addQuickenedCureWounds() { return nullptr; }
    std::shared_ptr<ActoidFactory> addVowOfEnmity()
    {
      auto resource = getResource(AbilityType::CHANNEL_DIVINITY);
      if(!resource)
        {
          auto channelDivinity = std::make_shared<Uses>(2, ResourceRefreshType::SHORT_REST);
          _resources.insert({AbilityType::CHANNEL_DIVINITY, channelDivinity});
          resource = channelDivinity.get();
        }
      auto factory = std::make_shared<VowOfEnmityFactory>(this, *resource);
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addHex()
    {
      auto factory = std::make_shared<HexFactory>(AbilityType::HEX, this, _spellslots.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    //! Armor of Agathys (2024): bonus-action level-1 self-buff granting 5 temporary Hit Points and Cold
    //! retaliation against melee attackers while those temporary Hit Points last.
    std::shared_ptr<ActoidFactory> addArmorOfAgathys()
    {
      auto factory = std::make_shared<ArmorOfAgathysFactory>(AbilityType::ARMOR_OF_AGATHYS, this, _spellslots.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
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

    //! Adds a melee reaction attack (e.g. opportunity attack). Mirrors the Python
    //! `add_ability(Reaction.REACTION_ATTACK, ...)` which sets both the AoO factory and
    //! the default danger-zone attack to this reaction.
    std::shared_ptr<ActoidFactory> addReactionAttack(const std::string &name, Combatant *owner, int toHit, const std::vector<Die> &dmgDice,
                                                     int dmgBonus, DamageType damageType, int attackRange)
    {
      auto factory = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", name, owner, AbilityType::REACTION_ATTACK, toHit, dmgDice, dmgBonus,
                                                          damageType, attackRange);
      _reactionFactories.emplace_back(factory);
      _aoOFactory = static_cast<AttackFactory *>(factory.get());
      _dangerZoneAttack = static_cast<DirectThreatFactory *>(factory.get());
      _meleeReactionRange = attackRange;
      return factory;
    }
    std::shared_ptr<ActoidFactory> addShield()
    {
      auto factory = std::make_shared<ShieldFactory>(this, _spellslots.get());
      _reactionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addCuttingWords()
    {
      auto resource = getResource(AbilityType::BARDIC_INSPIRATION);
      if(!resource)
        {
          auto pool = std::make_shared<Uses>(BardicInspirationFactory::getUses(getSpellcastingModifier()), ResourceRefreshType::LONG_REST);
          _resources.insert({AbilityType::BARDIC_INSPIRATION, pool});
          resource = pool.get();
        }
      auto factory = std::make_shared<CuttingWordsFactory>(this, resource.value());
      _reactionFactories.emplace_back(factory);
      return factory;
    }
    std::shared_ptr<ActoidFactory> addPreSwallowBiteReaction() { return nullptr; }
    //! Uncanny Dodge (2024 Rogue, level 5): when the rogue is hit by an attack it can see, it may spend its
    //! Reaction to halve that attack's damage. Modelled as a passive marker consulted in the action resolver
    //! (which sets uncannyDodgeActive before the damage is applied). Mirrors Python
    //! combatant.add_ability(Reaction.UNCANNY_DODGE) + prompt_after_hit_reaction.
    std::shared_ptr<ActoidFactory> addUncannyDodge()
    {
      _passiveAbilities.insert(AbilityType::UNCANNY_DODGE);
      return nullptr;
    }
    std::shared_ptr<ActoidFactory> addParry() { return nullptr; }
    std::shared_ptr<ActoidFactory> addRiposte() { return nullptr; }    std::shared_ptr<ActoidFactory> addReactionParalyzingMeleeAttack() { return nullptr; }
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
    //! Danger Sense (Barbarian): Advantage on Dexterity saving throws against effects the barbarian can see.
    //! Registered as a passive marker.
    void addDangerSense() { _passiveAbilities.insert(AbilityType::DANGER_SENSE); }
    //! Metamagic (2024): grants a pool of sorcery points (= sorcerer level) refreshed on a long rest,
    //! and marks the combatant as having Metamagic so metamagic options become available.
    void addMetamagic()
    {
      _passiveAbilities.insert(AbilityType::METAMAGIC);
      _resources.insert({AbilityType::METAMAGIC, std::make_shared<Uses>(_level, ResourceRefreshType::LONG_REST)});
    }
    //! Pack Tactics: the creature has Advantage on an attack roll against a target if at least one of its
    //! allies is within 5 ft of the target and the ally is not Incapacitated. Registered as a passive marker.
    void addPackTactics() { _passiveAbilities.insert(AbilityType::PACK_TACTICS); }
    void addFanaticAdvantage() {}
    //! War Caster: Advantage on Constitution saving throws made to maintain Concentration. Passive marker.
    void addWarCaster() { _passiveAbilities.insert(AbilityType::WAR_CASTER); }
    //! Eldritch Mind (Eldritch Invocation): Advantage on Constitution saving throws to maintain
    //! Concentration. Passive marker (mirrors War Caster for concentration purposes).
    void addEldritchMind() { _passiveAbilities.insert(AbilityType::ELDRITCH_MIND); }
    //! Devil's Sight (Eldritch Invocation): the warlock sees normally in Darkness, magical or not, so it is
    //! never Blinded by its own Darkness spell. Passive marker.
    void addDevilsSight() { _passiveAbilities.insert(AbilityType::DEVILS_SIGHT); }
    //! Steps of the Fey (Archfey patron, 2024): the warlock can cast Misty Step without expending a spell
    //! slot a number of times equal to its spellcasting modifier per long rest. Registers the free-use pool
    //! and a Misty Step factory drawing from it, plus a passive marker so the Refreshing Step rider (temp HP)
    //! is granted on resolution.
    std::shared_ptr<ActoidFactory> addStepsOfTheFey()
    {
      auto resource = std::make_shared<Uses>(std::max(1, getSpellcastingModifier()), ResourceRefreshType::LONG_REST);
      _resources.insert({AbilityType::MISTY_STEP, resource});
      _passiveAbilities.insert(AbilityType::STEPS_OF_THE_FEY);
      auto factory = std::make_shared<MistyStepFactory>(this, resource.get());
      _bonusActionFactories.emplace_back(factory);
      return factory;
    }
    //! Sneak Attack (2024 Rogue). Marks the passive and attaches an OnHitSneakAttack rider to every Finesse
    //! or ranged weapon attack the rogue has (across the action, bonus action, haste and reaction factory
    //! lists). Mirrors Python combatant.add_ability(Passive.SNEAK_ATTACK). Must be called after the rogue's
    //! attacks have been registered.
    void addSneakAttack()
    {
      _passiveAbilities.insert(AbilityType::SNEAK_ATTACK);
      _alreadyUsedSneakAttackThisTurn = false;
      auto attachSneakAttack = [this](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
            auto *attackFactory = dynamic_cast<AttackFactory *>(factory.get());
            if(attackFactory == nullptr)
              {
                continue;
              }
            if(attackFactory->usesDex() || attackFactory->hasFlag(FactoryFlags::IS_RANGED))
              {
                attackFactory->addOnHit(std::make_unique<OnHitSneakAttack>(
                  std::vector<Die>{OnHitSneakAttack::getDmgDice(_level)}, attackFactory->getDmgType(), attackFactory->getCritRange()));
              }
          }
      };
      attachSneakAttack(_actionFactories);
      attachSneakAttack(_bonusActionFactories);
      attachSneakAttack(_hasteActionFactories);
      attachSneakAttack(_reactionFactories);
    }
    //! Cunning Action (2024 Rogue): grants Disengage, Dash and Hide as Bonus Action options. Mirrors Python
    //! combatant.add_ability(Passive.CUNNING_ACTION).
    void addCunningAction()
    {
      _passiveAbilities.insert(AbilityType::CUNNING_ACTION);
      _bonusActionFactories.emplace_back(std::make_shared<DisengageFactory>(this, AbilityType::CUNNING_DISENGAGE));
      _bonusActionFactories.emplace_back(std::make_shared<DashFactory>(this, AbilityType::CUNNING_DASH));
      _bonusActionFactories.emplace_back(std::make_shared<HideFactory>(this, AbilityType::CUNNING_HIDE));
    }
    //! Assassinate (2024 Assassin, level 3): the rogue has Advantage on attack rolls against any creature that
    //! has not yet taken a turn in the combat. Resolved in the action resolver; here it is only a passive
    //! marker. Mirrors Python combatant.add_ability(Passive.ASSASSINATE).
    void addAssassinate() { _passiveAbilities.insert(AbilityType::ASSASSINATE); }
    void addRegeneration() {}
    void addEvasion() {}
    void addHeartOfHruggek() {}
    void addDarkDevotion() {}
    void addBlindsight() {}
    void addMagicResistance() {}
    void addCharmImmunity() {}
    void addGreatWeaponFighting() { _passiveAbilities.insert(AbilityType::GREAT_WEAPON_FIGHTING); }
    void addDueling() { _passiveAbilities.insert(AbilityType::DUELING); }
    //! Battle Master maneuvers (2024): registers the Superiority Dice resource (4/5/6 dice by level, refreshed
    //! on a Short or Long Rest) and a Riposte reaction built from the fighter's opportunity attack with a
    //! Superiority Die added to its damage. Must be called after the reaction (AoO) attack has been registered.
    void addBattleMasterManeuvers()
    {
      _passiveAbilities.insert(AbilityType::BATTLE_MASTER_MANEUVERS);
      auto resource = std::make_shared<Uses>(getSuperiorityDiceCount(_level), ResourceRefreshType::SHORT_REST);
      _resources.insert({AbilityType::BATTLE_MASTER_MANEUVERS, resource});
      if(_aoOFactory != nullptr)
        {
          std::vector<Die> dmgDice = _aoOFactory->getDmgDice();
          dmgDice.push_back(getSuperiorityDie(_level));
          auto riposte = std::make_shared<RiposteFactory>("Riposte", this, _aoOFactory->getToHit(), dmgDice, _aoOFactory->getDmgBonus(),
                                                          _aoOFactory->getDmgType(), _aoOFactory->getRange(), resource.get());
          _reactionFactories.emplace_back(riposte);
          _riposteFactory = static_cast<AttackFactory *>(riposte.get());
        }
    }
    //! Draconic Resilience (2024): +3 HP at level 3 plus 1 per sorcerer level, and an unarmored AC of
    //! 10 + Dex + Cha. The final HP and AC are baked into the combatant's constructor stats, so this
    //! only registers the passive marker.
    void addDraconicResilience() { _passiveAbilities.insert(AbilityType::DRACONIC_RESILIENCE); }
    //! Unarmored Defense (Barbarian): AC = 10 + Dex + Con while wearing no armor. The resulting AC is baked
    //! into the combatant's constructor stats, so this only registers the passive marker.
    void addUnarmoredDefense() { _passiveAbilities.insert(AbilityType::UNARMORED_DEFENSE); }
    //! Divine Smite (2024): register the passive marker plus the once-per-long-rest free cast, then add a
    //! smite-consuming variant of every melee / unarmed attack already known. The variant uses both the Action
    //! and the Bonus Action and resolves the radiant damage on hit; the planner picks at most one per turn and
    //! the multiattack FSM delegates to the original attack so the remaining attacks resolve normally.
    void addDivineSmite()
    {
      _passiveAbilities.insert(AbilityType::DIVINE_SMITE);
      auto resource = std::make_shared<Uses>(1, ResourceRefreshType::LONG_REST);
      _resources.insert({AbilityType::DIVINE_SMITE, resource});
      std::vector<std::shared_ptr<ActoidFactory>> smiteVariants;
      for(const auto &af : _actionFactories)
        {
          if(auto *melee = dynamic_cast<MeleeAttackFactory *>(af.get()))
            {
              smiteVariants.push_back(std::make_shared<SmiteMeleeAttackFactory>(*melee, af.get()));
            }
        }
      for(auto &variant : smiteVariants)
        {
          _actionFactories.emplace_back(variant);
        }
    }
    void addChannelDivinity()
    {
      _passiveAbilities.insert(AbilityType::CHANNEL_DIVINITY);
      _resources.insert({AbilityType::CHANNEL_DIVINITY, std::make_shared<Uses>(_level >= 11 ? 3 : 2, ResourceRefreshType::SHORT_REST)});
    }
    void addUndeadFortitude();
    void addMartialAdvantage() {}
    //! Tactical Mind (2024 Fighter, level 2): when the fighter fails an ability check it may expend a use of
    //! Second Wind to add 1d10 to the check (the use is only spent if it turns the failure into a success).
    //! The behaviour lives in attemptAbilityCheck(); this only registers the passive marker. Must be called
    //! after addSecondWind() so the Second Wind resource exists.
    void addTacticalMind() { _passiveAbilities.insert(AbilityType::TACTICAL_MIND); }
    //! Quickened Spell metamagic: for each eligible action spell already known, add a bonus-action
    //! quickened variant (reusing the same factory class with the quickened ability type). Must be
    //! called after the spells it should quicken have been added and after addMetamagic().
    void addQuickenedSpell()
    {
      _passiveAbilities.insert(AbilityType::QUICKENED_SPELL);
      std::vector<std::shared_ptr<ActoidFactory>> quickened;
      for(const auto &af : _actionFactories)
        {
          switch(af->getAbilityType())
            {
            case AbilityType::FIREBOLT:
              quickened.push_back(std::make_shared<FireboltFactory>(_spellToHit, AbilityType::QUICKENED_FIREBOLT, this, _spellslots.get()));
              break;
            case AbilityType::RAY_OF_FROST:
              quickened.push_back(std::make_shared<RayOfFrostFactory>(_spellToHit, AbilityType::QUICKENED_RAY_OF_FROST, this, _spellslots.get()));
              break;
            case AbilityType::SCORCHING_RAY:
              quickened.push_back(std::make_shared<ScorchingRayFactory>(_spellToHit, AbilityType::QUICKENED_SCORCHING_RAY, this, _spellslots.get()));
              break;
            case AbilityType::HOLD_PERSON:
              quickened.push_back(std::make_shared<HoldPersonFactory>(_dc, AbilityType::QUICKENED_HOLD_PERSON, this, _spellslots.get()));
              break;
            default: break;
            }
        }
      for(auto &q : quickened)
        {
          _bonusActionFactories.emplace_back(q);
        }
    }
    //! Twinned Spell metamagic. The 2024 twinned-spell variant factories (which retarget a single-target
    //! spell at a second creature) have not yet been ported to C++, so this registers the metamagic
    //! option marker without generating separate twinned factories.
    void addTwinnedSpell() { _passiveAbilities.insert(AbilityType::TWINNED_SPELL); }
    void addEmpoweredSpell() {}
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     * Non-action abilities
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */
    void addActionSurge()
    {
      // Action Surge is a Free Action gated by its own limited-use resource; the extra Action it grants is
      // surfaced to the planner by the ActionSurge actoid's IS_ACTION_ENABLER flag together with the
      // setHasAction(true) in useResources.
      _passiveAbilities.insert(AbilityType::ACTION_SURGE);
      auto resource = std::make_shared<Uses>(ActionSurgeFactory::getActionSurgeUses(_level), ResourceRefreshType::SHORT_REST);
      _resources.insert({AbilityType::ACTION_SURGE, resource});
      auto factory = std::make_shared<ActionSurgeFactory>(this, resource.get());
      _freeActionFactories.emplace_back(factory);
    }
    /**
     * ----------------------------------------------------------------------------------------------------------------------------------------------
     */

  private:
    template <typename ConditionType> Combatant *checkConditionList(const std::vector<ConditionType> &condList, Conditions condition) const
    {
      for(const auto &cond : condList)
        {
          if(containsCondition(cond.conditionComposite, condition))
            {
              return cond.initiator;
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
    bool _isDisengaging = false;
    std::unordered_set<WeaponMastery> _masteriesUsedThisTurn;
    bool _isShieldSpellActive = false;
    bool _innateSorceryActive = false;
    bool _pendingDivineSmite = false;
    int _meleeReactionRange = 1;
    int _speed;
    int _movement;
    int _athletics = 0;
    int _acrobatics = 0;
    int _stealth = 0;
    int _passivePerception = 0;
    bool _alreadyUsedSneakAttackThisTurn = false;
    Color _teamColor;
    AttackFsm _attackFsm;
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
    AttackFactory *_riposteFactory = nullptr;
    std::vector<std::shared_ptr<ActoidFactory>> _freeActionFactories;
    std::unordered_set<AbilityType> _passiveAbilities;
    std::unordered_map<SavingThrow, int> _savingThrows
      = {{SavingThrow::STR, 0}, {SavingThrow::DEX, 0}, {SavingThrow::CON, 0}, {SavingThrow::INT, 0}, {SavingThrow::WIS, 0}, {SavingThrow::CHA, 0}};
    std::unordered_map<SavingThrow, std::vector<int>> _savingThrowsFlatMod;
    std::unordered_map<SavingThrow, std::vector<Die>> _savingThrowsDiceMod;
    std::unordered_map<SavingThrow, std::vector<Die>> _savingThrowsPenaltyDice;
    std::unordered_map<SavingThrow, std::unordered_set<RollType>> _savingThrowsRollTypeMod;
    std::vector<Die> _toHitDiceMod;
    std::vector<Die> _toHitPenaltyDice;
    std::unordered_set<DamageType> _dmgTypesTookLastRound;
    Combatant *_originalForm = this;
    Combatant *_currentWildshapeForm = nullptr;
    int _activeWildshapeFormId = 0;
    Combatant *_swallower = nullptr;
    Combatant *_swallowedTarget = nullptr;
    Combatant *_constrictedTarget = nullptr;
    bool _etherealUntargetable = false;
    std::vector<Condition> _conditions;
    std::vector<ConditionWithDC> _dcConditions;
    ResourceDepletionLevel _resouceDepletionLevel;
    std::shared_ptr<Spellslots> _spellslots;
    std::unordered_map<AbilityType, std::shared_ptr<Resource>> _resources;
    std::deque<std::shared_ptr<Actoid>> _actionPlan; // ordered movement increments / (bonus) actions for the current turn
    int _weaponDmgDealtThisTurn = 0; // This is used for ActionSurge
    int _oneTimeAcbonus = 0; // TODO: Parry may work differently in 2024 (battle master parry reduces dmg, let's wait for monsters)
    std::weak_ptr<Effect> _concentrationEffect;
    std::vector<std::shared_ptr<Wildshape>> _availableWildshapeForms;
    blaze::DynamicMatrix<Coord> _shortestPathsCache;
    bool _uncannyDodgeActive = false;

  protected:
    Size _size{Size::MEDIUM};
    int _classId;
    // int _instanceId;
    CombatantType _type;
    SubType _subtype;
    int _level;
  };

}
