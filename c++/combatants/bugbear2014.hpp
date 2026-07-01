#include "core/combatant.hpp"

namespace enc
{

  class Bugbear2014 : public Combatant
  {
  public:
    Bugbear2014(int num);
    Bugbear2014(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Bugbear(2014)";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::HUMANOID, _classLevel);
  };

}
