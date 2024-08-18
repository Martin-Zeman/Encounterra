#include "core/combatant.hpp"

namespace enc
{

  class GreenDragonWyrmling : public Combatant
  {
  public:
    GreenDragonWyrmling(int num);

    static constexpr int getClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Green Dragon Wyrmling";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::DRAGON, _classLevel);
  };

}
