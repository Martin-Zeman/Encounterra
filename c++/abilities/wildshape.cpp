#include "abilities/wildshape.hpp"
#include "core/combatant.hpp"
#include "actions/attack.hpp"
#include "effects/effect_tracker.hpp"
#include <blaze/Math.h>
#include <algorithm>

namespace enc
{
  namespace
  {
    //! A beast's "weapon" attacks are its Melee/Ranged attack factories (excluding Dodge/Disengage etc.).
    bool isWeaponAttack(const std::shared_ptr<ActoidFactory> &f)
    {
      AbilityType t = f->getAbilityType();
      return t == AbilityType::MELEE_ATTACK || t == AbilityType::RANGED_ATTACK;
    }

    //! A druid action persists while shaped only if it is the Wild Shape action itself or it is explicitly
    //! flagged castable-while-shaped (the Circle of the Moon spell loadout). Everything else (mundane weapon
    //! attacks and ordinary spells) is suppressed for the duration of the form.
    bool persistsInWildshape(const std::shared_ptr<ActoidFactory> &f)
    {
      if(f->hasFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE))
        return true;
      AbilityType t = f->getAbilityType();
      return t == AbilityType::WILDSHAPE || t == AbilityType::MOON_WILDSHAPE;
    }

    //! Move every non-persisting druid factory out of `list` into `stash`.
    void stashFactories(std::vector<std::shared_ptr<ActoidFactory>> &list, std::vector<std::shared_ptr<ActoidFactory>> &stash)
    {
      for(auto &f : list)
        {
          if(!persistsInWildshape(f))
            stash.push_back(f);
        }
      list.erase(std::remove_if(list.begin(), list.end(), [](const auto &f) { return !persistsInWildshape(f); }), list.end());
    }

    //! Append the previously stashed factories back onto `list` and clear the stash.
    void restoreStashed(std::vector<std::shared_ptr<ActoidFactory>> &list, std::vector<std::shared_ptr<ActoidFactory>> &stash)
    {
      for(auto &f : stash)
        list.push_back(f);
      stash.clear();
    }

    //! Graft the beast's weapon-attack factories onto the druid's `target` list, retargeting them at `druid`.
    void graftBeastAttacks(const std::vector<std::shared_ptr<ActoidFactory>> &beastList, std::vector<std::shared_ptr<ActoidFactory>> &target,
                           std::vector<std::shared_ptr<ActoidFactory>> &added, Combatant *druid)
    {
      for(const auto &f : beastList)
        {
          if(isWeaponAttack(f))
            {
              f->setCombatant(druid);
              target.push_back(f);
              added.push_back(f);
            }
        }
    }

    //! Remove the previously grafted factories from `list` (by pointer identity).
    void removeGrafted(std::vector<std::shared_ptr<ActoidFactory>> &list, const std::vector<std::shared_ptr<ActoidFactory>> &added)
    {
      list.erase(std::remove_if(list.begin(), list.end(),
                                [&](const auto &f) { return std::find(added.begin(), added.end(), f) != added.end(); }),
                 list.end());
    }
  }

  WildshapeFactory::WildshapeFactory(Combatant *combatant, AbilityType actionType)
      : TransformerFactory("WildshapeFactory", "Wildshape", combatant, actionType), _combatant(combatant), _actionType(actionType)
  {
    setFlag(FactoryFlags::TARGETS_SELF);
  }

  int WildshapeFactory::getWildshapeUses(int level) { return level == 20 ? std::numeric_limits<int>::max() : 2; }

  std::vector<Size> WildshapeFactory::getWildshapeFormSizes(int level, AbilityType actionType)
  {
    if(actionType == AbilityType::WILDSHAPE)
      {
        return {Size::LARGE};
      }
    else if(actionType == AbilityType::MOON_WILDSHAPE)
      {
        if(level >= 2 && level <= 5)
          return {Size::LARGE};
        if(level >= 6)
          return {Size::LARGE, Size::HUGE};
      }
    return {};
  }

  std::vector<std::shared_ptr<Actoid>> WildshapeFactory::createAll(void *previousActionInDag)
  {
    const auto &forms = _combatant->getAvailableWildshapeForms();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(forms.size());
    for(const auto &form : forms)
      {
        // Same-form restriction: the druid cannot reshape into the animal it is already in. It must pick a
        // different form (or revert first).
        if(form->getForm()->getClassId() == _combatant->getActiveWildshapeFormId())
          {
            continue;
          }
        result.push_back(std::static_pointer_cast<Actoid>(form));
      }
    return result;
  }

  std::shared_ptr<Actoid> WildshapeFactory::create(void *form)
  {
    auto *formPtr = static_cast<std::unique_ptr<Combatant> *>(form);
    return std::make_shared<Wildshape>(_combatant, std::move(*formPtr), *this);
  }

  double WildshapeFactory::calculateThreat(const Kwargs &kwargs)
  {
    auto forms = _combatant->getAvailableWildshapeForms();
    if(forms.empty())
      return 0.0;
    return (_actionType == AbilityType::MOON_WILDSHAPE) ? 3.0 * _combatant->getLevel() : static_cast<double>(_combatant->getLevel());
  }

  Wildshape::Wildshape(Combatant *combatant, std::unique_ptr<Combatant> form, WildshapeFactory &factory)
      : Actoid(factory, ActoidFlags::IS_ACTION_ENABLER, factory._actionType), Effect(combatant),
        CombatantEffect(combatant, std::vector<Combatant *>{combatant}), ActionEnablerEffect(combatant), _form(std::move(form)), _factory(factory)
  {}

  std::string Wildshape::toString() const { return "Wildshape of " + getInitiator()->_name + " into " + _form->_name; }

  int Wildshape::circleOfMoonAc() const
  {
    Combatant *druid = getInitiator();
    int level = druid->getLevel();
    int proficiency = 2 + (level - 1) / 4;
    // Spell save DC = 8 + proficiency + Wisdom modifier, so Wisdom modifier = DC - 8 - proficiency.
    int wisMod = druid->getDC() - 8 - proficiency;
    return 13 + wisMod;
  }

  void Wildshape::applyShapeTransform()
  {
    if(_shaped)
      {
        return;
      }
    Combatant *druid = getInitiator();

    // Armour Class: the beast's AC. Circle of the Moon raises this to a floor of 13 + the druid's Wis mod.
    _savedAc = druid->getAC();
    int newAc = isCircleOfMoon() ? std::max(_form->getAC(), circleOfMoonAc()) : _form->getAC();
    druid->setAC(newAc);

    // Speed: adopt the beast's Speed, preserving any movement already spent this turn.
    _savedSpeed = druid->getSpeed();
    _savedMovement = druid->getMovement();
    int usedMovement = std::max(0, _savedSpeed - _savedMovement);
    druid->setSpeed(_form->getSpeed());
    druid->setMovement(std::max(0, _form->getSpeed() - usedMovement));

    // Suppress the druid's own actions (weapons and ordinary spells). Only abilities flagged
    // TRANSITIONS_TO_WILDSHAPE (the Circle of the Moon loadout) and the Wild Shape action survive.
    _savedAoOFactory = druid->getAoOFactory();
    _savedDangerZone = druid->getDangerZoneAttack();

    stashFactories(druid->getActionFactories(), _stashedActionFactories);
    stashFactories(druid->getBonusActionFactories(), _stashedBonusActionFactories);
    stashFactories(druid->getReactionFactories(), _stashedReactionFactories);
    stashFactories(druid->getHasteActionFactories(), _stashedHasteActionFactories);

    // Graft the beast's attacks onto the druid (action + reaction lists), retargeting them at the druid.
    graftBeastAttacks(_form->getActionFactoriesConst(), druid->getActionFactories(), _addedActionFactories, druid);
    graftBeastAttacks(_form->getReactionFactoriesConst(), druid->getReactionFactories(), _addedReactionFactories, druid);

    // Opportunity attacks now use the beast's reaction attack, if it has one.
    if(_form->getAoOFactory() != nullptr)
      {
        druid->setAoOFactory(_form->getAoOFactory());
      }
    if(_form->getDangerZoneAttack() != nullptr)
      {
        druid->setDangerZoneAttack(_form->getDangerZoneAttack());
      }

    // Adopt the beast's multiattack pattern. The beast's FSM edges reference the very factory objects just
    // grafted onto the druid, so a fresh copy works directly on the druid.
    _savedFsm = druid->getAttackFsm();
    AttackFsm beastFsm = _form->getAttackFsm();
    beastFsm.reset();
    druid->setAttackFsm(beastFsm);

    _shaped = true;
  }

  void Wildshape::revertShapeTransform()
  {
    if(!_shaped)
      {
        return;
      }
    Combatant *druid = getInitiator();

    // Remove grafted beast attacks and hand the beast's factories back to the beast template.
    removeGrafted(druid->getActionFactories(), _addedActionFactories);
    removeGrafted(druid->getReactionFactories(), _addedReactionFactories);
    for(auto &f : _addedActionFactories)
      f->setCombatant(_form.get());
    for(auto &f : _addedReactionFactories)
      f->setCombatant(_form.get());
    _addedActionFactories.clear();
    _addedReactionFactories.clear();

    // Restore the druid's own suppressed actions.
    restoreStashed(druid->getActionFactories(), _stashedActionFactories);
    restoreStashed(druid->getBonusActionFactories(), _stashedBonusActionFactories);
    restoreStashed(druid->getReactionFactories(), _stashedReactionFactories);
    restoreStashed(druid->getHasteActionFactories(), _stashedHasteActionFactories);

    // Restore FSM, AC, Speed, opportunity attack and danger zone.
    druid->setAttackFsm(_savedFsm);
    druid->setAC(_savedAc);
    druid->setSpeed(_savedSpeed);
    druid->setMovement(std::min(druid->getMovement(), _savedSpeed));
    druid->setAoOFactory(_savedAoOFactory);
    druid->setDangerZoneAttack(_savedDangerZone);

    _shaped = false;
  }

  void Wildshape::activate(const Kwargs &kwargs)
  {
    applyShapeTransform();

    Combatant *druid = getInitiator();
    // Assuming a Wild Shape form grants Temporary Hit Points: the druid's level normally, or 3 x level for
    // the Circle of the Moon. These persist as ordinary temporary hit points (they are NOT cleared when the
    // form ends).
    druid->setTemporaryHp((isCircleOfMoon() ? 3 : 1) * druid->getLevel());
    // Remember the active form so the druid cannot reshape into the same animal.
    druid->setActiveWildshapeFormId(_form->getClassId());
  }

  void Wildshape::deactivate()
  {
    revertShapeTransform();

    Combatant *druid = getInitiator();
    druid->setActiveWildshapeFormId(0);
    // Temporary hit points granted by Wild Shape are deliberately NOT cleared here; they persist like any
    // other temporary hit points until depleted or overwritten.
  }

  bool Wildshape::deactivateForCombatant(Combatant *combatant)
  {
    deactivate();
    return false;
  }

  void Wildshape::enable() { applyShapeTransform(); }

  void Wildshape::disable() { revertShapeTransform(); }

  double Wildshape::calculateThreat(const Kwargs &kwargs)
  {
    return (_factory._actionType == AbilityType::MOON_WILDSHAPE) ? 3.0 * _factory._combatant->getLevel()
                                                                 : static_cast<double>(_factory._combatant->getLevel());
  }

  double Wildshape::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  std::optional<CoordVector>
  Wildshape::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    // Wild Shape targets the druid itself, but the druid may move before shaping and the chosen form may be
    // larger than the druid. We therefore look for every reachable square where a block of cells large enough
    // for the form fits, then keep only those at the minimum travel distance from the druid's current cell.
    auto &battleMap = BattleMap::getInstance();
    Combatant *initiator = getInitiator();

    if(!initiator->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        blaze::DynamicMatrix<int> mapAccessibility(battleMap.getGridSize(), battleMap.getGridSize(), 0);

        // Populate accessibility matrix from the reachable squares (Dijkstra result).
        for(size_t x = 0; x < shortestPaths.rows(); ++x)
          {
            for(size_t y = 0; y < shortestPaths.columns(); ++y)
              {
                if(shortestPaths(x, y) != Coord{-1, -1})
                  {
                    mapAccessibility(x, y) = 1;
                  }
              }
          }

        // The druid's own cell is always available (it can shape in place without moving).
        auto originalCoord = battleMap.getCombatantCoordinates(*initiator).getRoot();
        mapAccessibility(originalCoord[0], originalCoord[1]) = 1;

        int wildshapeSizeIncrement = static_cast<int>(_form->getSize());
        CoordVector eligibleCoords;
        double minDistance = std::numeric_limits<double>::max();

        // Find every square whose (size+1)x(size+1) block of cells is fully accessible, keeping only those at
        // the smallest travel distance.
        for(int col = 0; col < battleMap.getGridSize() - wildshapeSizeIncrement; ++col)
          {
            for(int row = 0; row < battleMap.getGridSize() - wildshapeSizeIncrement; ++row)
              {
                bool valid = true;
                for(int dx = 0; dx <= wildshapeSizeIncrement && valid; ++dx)
                  {
                    for(int dy = 0; dy <= wildshapeSizeIncrement && valid; ++dy)
                      {
                        if(mapAccessibility(row + dx, col + dy) == 0)
                          {
                            valid = false;
                          }
                      }
                  }

                if(valid)
                  {
                    double dist = distances[col * battleMap.getGridSize() + row];
                    if(dist < minDistance)
                      {
                        minDistance = dist;
                        eligibleCoords.clear();
                        eligibleCoords.push_back({col, row});
                      }
                    else if(dist == minDistance)
                      {
                        eligibleCoords.push_back({col, row});
                      }
                  }
              }
          }

        if(eligibleCoords.empty())
          {
            return std::nullopt;
          }
        return eligibleCoords;
      }
    else if(auto coord = battleMap.findWildshapedCoordinate(initiator, _form->getSize()))
      {
        // Grappled/restrained: the druid cannot move, but may still shape in place if the form fits.
        return battleMap.getCombatantCoordinates(*initiator).get();
      }

    return std::nullopt;
  }
}
