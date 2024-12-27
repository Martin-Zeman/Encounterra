#include "core/combatant.hpp"

namespace enc
{

  class Acolyte : public Combatant
  {
  public:
    Acolyte(int num);
    Acolyte(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Acolyte";
    static constexpr int _classLevel = 2;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::HUMANOID, _classLevel);
  };

}
