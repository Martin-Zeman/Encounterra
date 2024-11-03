#pragma once

namespace enc
{
  class AoeEffect : public Effect
  {
  public:
    explicit AoeEffect(Combatant *initiator) : Effect(initiator) {}
    virtual ~AoeEffect() = default;

    // Pure virtual methods specific to AoeEffect
    virtual std::vector<Coord> getAffectedCoords() const = 0;
    virtual void onEnter(Combatant *combatant) = 0;
    virtual void onMoveWithin(Combatant *combatant) = 0;
    virtual void onExit(Combatant *combatant) = 0;
    virtual void onStartOfTurn(Combatant *combatant) = 0;
    virtual void onEndOfTurn(Combatant *combatant) = 0;

    // Concrete implementation of isAffecting from Effect base class
    bool isAffecting(Combatant *combatant) const override
    {
      BattleMap &battleMap = BattleMap::getInstance();
      std::vector<Coord> coords = getAffectedCoords();

      auto combatantPosition = battleMap.getCombatantCoordinates(*combatant);
      if(!combatantPosition.has_value())
        {
          return false;
        }

      return nf::getHopDistanceCoords(combatantPosition.value(), coords) == 0;
    }

  protected:
    // Add any protected members needed by derived classes
  };
}
