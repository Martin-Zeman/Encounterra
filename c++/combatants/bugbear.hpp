#include "core/combatant.hpp"

namespace enc
{

  class Bugbear : public Combatant
  {
  public:
    Bugbear(int num);

    static constexpr int getClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Bugbear";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::HUMANOID, _classLevel);
  };

}
