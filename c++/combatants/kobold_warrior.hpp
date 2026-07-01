#include "core/combatant.hpp"

namespace enc
{

  class KoboldWarrior : public Combatant
  {
  public:
    KoboldWarrior(int num);
    KoboldWarrior(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Kobold Warrior";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::DRAGON, _classLevel);
  };

}
