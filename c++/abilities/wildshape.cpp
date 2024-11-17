#include "abilities/wildshape.hpp"
#include "core/teams.hpp"
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

  std::vector<std::shared_ptr<Actoid>> WildshapeFactory::createAll(void *previousActionInDag) { return _combatant->getAvailableWildshapeForms(); }

  std::shared_ptr<Actoid> WildshapeFactory::create(void *form)
  {
    return std::make_shared<Wildshape>(_combatant, std::static_pointer_cast<Combatant>(static_cast<std::shared_ptr<void> *>(form)->get()), *this);
  }

  double WildshapeFactory::calculateThreat(const Kwargs &kwargs) const
  {
    auto forms = _combatant->getAvailableWildshapeForms();
    if(forms.empty())
      return 0.0;

    return std::max_element(forms.begin(), forms.end(), [](const auto &a, const auto &b) { return a->getCurrentHp() < b->getCurrentHp(); })
      ->get()
      ->getCurrentHp();
  }

  double WildshapeFactory::calculateMaxThreat() const { return calculateThreat({}); }

  Wildshape::Wildshape(Combatant *combatant, std::shared_ptr<Combatant> form, WildshapeFactory &factory)
      : Actoid(factory), CombatantEffect(combatant), _form(form), _factory(factory)
  {
    _form->setOriginalForm(combatant);
  }

  std::string Wildshape::toString() const { return "Wildshape of " + _factory.getCombatant()->getName() + " into " + _form->getName(); }

  void Wildshape::activate(const Kwargs &kwargs)
  {
    auto &battleMap = BattleMap::getInstance();
    auto &effectTracker = battleMap.getEffectTracker();
    effectTracker.add(shared_from_this());

    battleMap.getTeams().replaceCombatant(getCombatant(), _form.get());
    auto wildshapeCoord = battleMap.findWildshapedCoordinate(getCombatant(), _form->getSize());
    battleMap.removeCombatant(getCombatant());
    battleMap.setCombatantCoordinates(_form.get(), wildshapeCoord);

    getCombatant()->setCurrentWildshapeForm(_form);
    _form->setCurrentHp(_form->getMaxHp());
    _form->setMovement(std::max(0, _form->getSpeed() - (getCombatant()->getSpeed() - getCombatant()->getMovement())));

    // Copy saving throws
    _form->setSavingThrow(SavingThrow::INT, getCombatant()->getSavingThrow(SavingThrow::INT));
    _form->setSavingThrow(SavingThrow::WIS, getCombatant()->getSavingThrow(SavingThrow::WIS));
    _form->setSavingThrow(SavingThrow::CHA, getCombatant()->getSavingThrow(SavingThrow::CHA));

    // Copy action states
    _form->setHasAction(getCombatant()->hasAction());
    _form->setHasBonusAction(getCombatant()->hasBonusAction());
    _form->setHasHasteAction(getCombatant()->hasHasteAction());
    _form->setHasReaction(getCombatant()->hasReaction());
    _form->setConcentrationEffect(getCombatant()->getConcentrationEffect());

    // Transfer eligible factories
    transferFactories();
  }

  void Wildshape::deactivate()
  {
    auto &battleMap = BattleMap::getInstance();
    auto *originalForm = getCombatant();
    auto *currentForm = originalForm->getCurrentWildshapeForm().get();

    currentForm->onDie();
    battleMap.getTeams().replaceCombatant(currentForm, originalForm);

    auto position = battleMap.getCombatantCoordinates(currentForm);
    battleMap.removeCombatant(currentForm);
    battleMap.setCombatantCoordinates(originalForm, position);

    originalForm->setMovement(std::min(originalForm->getSpeed(), currentForm->getMovement()));
    originalForm->setCurrentWildshapeForm(nullptr);

    // Copy back action states
    originalForm->setHasAction(currentForm->hasAction());
    originalForm->setHasBonusAction(currentForm->hasBonusAction());
    originalForm->setHasHasteAction(currentForm->hasHasteAction());
    originalForm->setHasReaction(currentForm->hasReaction());

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
    getCombatant()->setCurrentWildshapeForm(_form);

    _form->setHasAction(getCombatant()->hasAction());
    _form->setHasBonusAction(getCombatant()->hasBonusAction());
    _form->setHasHasteAction(getCombatant()->hasHasteAction());
    _form->setHasReaction(getCombatant()->hasReaction());

    transferFactories();
  }

  void Wildshape::disable()
  {
    getCombatant()->setCurrentWildshapeForm(nullptr);

    getCombatant()->setHasAction(_form->hasAction());
    getCombatant()->setHasBonusAction(_form->hasBonusAction());
    getCombatant()->setHasHasteAction(_form->hasHasteAction());
    getCombatant()->setHasReaction(_form->hasReaction());

    restoreFactories();
  }

  double Wildshape::calculateThreat(const Kwargs &kwargs) { return _form->getMaxHp(); }

  double Wildshape::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  std::optional<std::vector<Coord>>
  Wildshape::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    auto &battleMap = BattleMap::getInstance();

    if(!isAffectedByAny(getCombatant(), {Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        blaze::DynamicMatrix<int> mapAccessibility(battleMap.getSize(), battleMap.getSize(), 0);

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

        auto originalCoord = battleMap.getCombatantCoordinates(getCombatant());
        mapAccessibility(originalCoord[0], originalCoord[1]) = 1;

        int wildshapeSizeIncrement = static_cast<int>(_form->getSize());
        std::vector<Coord> eligibleCoords;
        double minDistance = std::numeric_limits<double>::max();

        // Find eligible coordinates with minimum distance
        for(int col = 0; col < battleMap.getSize() - wildshapeSizeIncrement; ++col)
          {
            for(int row = 0; row < battleMap.getSize() - wildshapeSizeIncrement; ++row)
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
                    double dist = distances[col * battleMap.getSize() + row];
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
    else if(auto coord = battleMap.findWildshapedCoordinate(getCombatant(), _form->getSize()))
      {
        return std::vector<Coord>{battleMap.getCombatantCoordinates(getCombatant())};
      }

    return std::nullopt;
  }
}
