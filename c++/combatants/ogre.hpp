#include "core/combatant.hpp"

namespace enc
{

  class Ogre : public Combatant
  {
  public:
    Ogre(int num);
    static constexpr int getClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Ogre";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::GIANT, _classLevel);
  };

}
