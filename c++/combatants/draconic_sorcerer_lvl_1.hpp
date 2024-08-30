#include "core/combatant.hpp"

namespace enc
{

  class DraconicSorcererLvl1 : public Combatant
  {
  public:
    DraconicSorcererLvl1(int num);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Draconic Sorcerer LVL 1";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Sorcerer::BEFORE_SUBCLASS, _classLevel);
  };

}
