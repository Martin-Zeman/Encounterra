#include "core/combatant.hpp"

namespace enc
{

  class Zombie : public Combatant
  {
  public:
    Zombie(int num);
    Zombie(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Zombie";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::UNDEAD, _classLevel);
  };

}
