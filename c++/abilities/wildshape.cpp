#include "abilities/wildshape.hpp"
#include "core/teams.hpp"
#include "effects/effect_tracker.hpp"
#include <blaze/Math.h>
#include <algorithm>

namespace enc
{
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
    // TODO: Rework this, it needs some consideration for the dmg in Wildshape
    auto forms = _combatant->getAvailableWildshapeForms();
    if(forms.empty())
      return 0.0;

    if(_actionType == AbilityType::MOON_WILDSHAPE)
      {
        return 3 * _combatant->getLevel();
      }
    else
      {
        return _combatant->getLevel();
      }
  }

  Wildshape::Wildshape(Combatant *combatant, std::unique_ptr<Combatant> form, WildshapeFactory &factory)
      : Actoid(factory), Effect(combatant), CombatantEffect(combatant, std::vector<Combatant *>{combatant}), ActionEnablerEffect(combatant),
        _form(std::move(form)), _factory(factory)
  {
    _form->setOriginalForm(combatant);
  }

  std::string Wildshape::toString() const { return "Wildshape of " + getInitiator()->_name + " into " + _form->_name; }

  void Wildshape::activate(const Kwargs &kwargs)
  {
    auto &battleMap = BattleMap::getInstance();
    auto &effectTracker = EffectTracker::getInstance();
    Combatant *initiator = initiator;
    effectTracker.add(shared_from_this());

    Teams &teams = Teams::getInstance();
    teams.replaceCombatant(*initiator, *_form.get());
    auto wildshapeCoord = battleMap.findWildshapedCoordinate(initiator, _form->getSize());
    if(!wildshapeCoord.has_value())
      {
        throw std::runtime_error("No space for the wildshape form!");
      }
    battleMap.removeCombatant(*initiator);
    battleMap.setCombatantCoordinates(*_form.get(), wildshapeCoord.value());

    initiator->setCurrentWildshapeForm(_form.get());
    _form->setCurrentHp(_form->getMaxHp());
    _form->setMovement(std::max(0, _form->getSpeed() - (initiator->getSpeed() - initiator->getMovement())));

    static const std::array<SavingThrow, 3> mentalSaves = {SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA};

    for(SavingThrow save : mentalSaves)
      {
        _form->setSavingThrow(save, initiator->getSavingThrow(save));
        const auto &flatMods = initiator->getSavingThrowFlatMods(save);
        for(int mod : flatMods)
          {
            _form->addSavingThrowFlatMod(save, mod);
          }
        const auto &diceMods = initiator->getSavingThrowDiceMods(save);
        for(const Die &die : diceMods)
          {
            _form->addSavingThrowDiceMod(save, die);
          }
        const auto &rollTypeMods = initiator->getSavingThrowRollTypeMods(save);
        for(RollType type : rollTypeMods)
          {
            _form->addSavingThrowRollTypeMod(save, type);
          }
      }

    // Copy action states
    _form->setHasAction(initiator->hasAction());
    _form->setHasBonusAction(initiator->hasBonusAction());
    _form->setHasHasteAction(initiator->hasHasteAction());
    _form->setHasReaction(initiator->hasReaction());
    _form->setConcentrationEffect(initiator->getConcentrationEffect().lock());

    // Transfer eligible factories
    transferFactories();
  }

  void Wildshape::deactivate()
  {
    auto &battleMap = BattleMap::getInstance();
    Combatant *initiator = getInitiator();
    Combatant *currentForm = initiator->getCurrentWildshapeForm();

    currentForm->onDie();
    Teams &teams = Teams::getInstance();
    teams.replaceCombatant(*currentForm, *initiator);

    auto position = battleMap.getCombatantCoordinates(*currentForm);
    battleMap.removeCombatant(*currentForm);
    battleMap.setCombatantCoordinates(*initiator, position.getRoot());

    initiator->setMovement(std::min(initiator->getSpeed(), currentForm->getMovement()));
    // Copy ALL saving throw modifiers back to the original form before clearing them
    static const std::array<SavingThrow, 6> ALL_SAVES
      = {SavingThrow::STR, SavingThrow::DEX, SavingThrow::CON, SavingThrow::INT, SavingThrow::WIS, SavingThrow::CHA};

    for(SavingThrow save : ALL_SAVES)
      {
        const auto &flatMods = currentForm->getSavingThrowFlatMods(save);
        for(int mod : flatMods)
          {
            initiator->addSavingThrowFlatMod(save, mod);
          }
        const auto &diceMods = currentForm->getSavingThrowDiceMods(save);
        for(const Die &die : diceMods)
          {
            initiator->addSavingThrowDiceMod(save, die);
          }
        const auto &rollTypeMods = currentForm->getSavingThrowRollTypeMods(save);
        for(RollType type : rollTypeMods)
          {
            initiator->addSavingThrowRollTypeMod(save, type);
          }
        currentForm->clearSavingThrowFlatMods(save);
        currentForm->clearSavingThrowDiceMods(save);
        currentForm->clearSavingThrowRollTypeMods(save);
      }
    initiator->setCurrentWildshapeForm(nullptr);

    // Copy back action states
    initiator->setHasAction(currentForm->hasAction());
    initiator->setHasBonusAction(currentForm->hasBonusAction());
    initiator->setHasHasteAction(currentForm->hasHasteAction());
    initiator->setHasReaction(currentForm->hasReaction());

    // Reset factories
    restoreFactories();
  }

  bool Wildshape::deactivateForCombatant(Combatant *combatant)
  {
    deactivate();
    return false;
  }

  void Wildshape::enable()
  {
    Combatant *initiator = getInitiator();
    initiator->setCurrentWildshapeForm(_form.get());

    _form->setHasAction(initiator->hasAction());
    _form->setHasBonusAction(initiator->hasBonusAction());
    _form->setHasHasteAction(initiator->hasHasteAction());
    _form->setHasReaction(initiator->hasReaction());

    transferFactories();
  }

  void Wildshape::disable()
  {
    Combatant *initiator = getInitiator();
    initiator->setCurrentWildshapeForm(nullptr);

    initiator->setHasAction(_form->hasAction());
    initiator->setHasBonusAction(_form->hasBonusAction());
    initiator->setHasHasteAction(_form->hasHasteAction());
    initiator->setHasReaction(_form->hasReaction());

    restoreFactories();
  }

  double Wildshape::calculateThreat(const Kwargs &kwargs)
  {
    // TODO: Rework this, it needs some consideration for the dmg in Wildshape
    if(_factory._actionType == AbilityType::MOON_WILDSHAPE)
      {
        return 3 * _factory._combatant->getLevel();
      }
    else
      {
        return _factory._combatant->getLevel();
      }
  }

  double Wildshape::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  std::optional<CoordVector>
  Wildshape::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    auto &battleMap = BattleMap::getInstance();
    Combatant *initiator = getInitiator();

    if(!initiator->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        blaze::DynamicMatrix<int> mapAccessibility(battleMap.getGridSize(), battleMap.getGridSize(), 0);

        // Populate accessibility matrix
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

        auto originalCoord = battleMap.getCombatantCoordinates(*initiator).getRoot();
        mapAccessibility(originalCoord[0], originalCoord[1]) = 1;

        int wildshapeSizeIncrement = static_cast<int>(_form->getSize());
        CoordVector eligibleCoords;
        double minDistance = std::numeric_limits<double>::max();

        // Find eligible coordinates with minimum distance
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

        return eligibleCoords;
      }
    else if(auto coord = battleMap.findWildshapedCoordinate(initiator, _form->getSize()))
      {
        return battleMap.getCombatantCoordinates(*initiator).get();
      }

    return std::nullopt;
  }

  void Wildshape::transferFactories()
  {
    Combatant *initiator = getInitiator();
    // Transfer eligible factories from original form to wildshape form
    transferFactoryList(initiator->getActionFactoriesConst(), _form->getActionFactories());
    transferFactoryList(initiator->getBonusActionFactoriesConst(), _form->getBonusActionFactories());
    transferFactoryList(initiator->getHasteActionFactoriesConst(), _form->getHasteActionFactories());
  }

  void Wildshape::restoreFactories()
  {
    Combatant *initiator = getInitiator();
    // Remove transferred factories from wildshape form
    removeTransferredFactories(_form->getActionFactories());
    removeTransferredFactories(_form->getBonusActionFactories());
    removeTransferredFactories(_form->getHasteActionFactories());

    // Reset combatant pointers in original form's factories
    resetFactoryPointers(initiator->getActionFactoriesConst());
    resetFactoryPointers(initiator->getBonusActionFactoriesConst());
    resetFactoryPointers(initiator->getHasteActionFactoriesConst());
  }

  void Wildshape::transferFactoryList(const std::vector<std::shared_ptr<ActoidFactory>> &sourceFactories,
                                      std::vector<std::shared_ptr<ActoidFactory>> &targetFactories)
  {
    for(const auto &factory : sourceFactories)
      {
        if(factory->hasFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE))
          {
            auto factoryCopy = factory;
            factoryCopy->setCombatant(_form.get());
            targetFactories.push_back(std::move(factoryCopy));
          }
      }
  }

  void Wildshape::removeTransferredFactories(std::vector<std::shared_ptr<ActoidFactory>> &factories)
  {
    factories.erase(std::remove_if(factories.begin(), factories.end(),
                                   [](const auto &factory) { return factory->hasFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE); }),
                    factories.end());
  }

  void Wildshape::resetFactoryPointers(const std::vector<std::shared_ptr<ActoidFactory>> &factories)
  {
    Combatant *initiator = getInitiator();
    for(const auto &factory : factories)
      {
        factory->setCombatant(initiator);
      }
  }
}
