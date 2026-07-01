#include "core/combatant.hpp"

namespace enc
{

  class FireGiant : public Combatant
  {
  public:
    FireGiant(int num);
    FireGiant(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Fire Giant";
    static constexpr int _classLevel = 9;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::GIANT, _classLevel);
  };

}
