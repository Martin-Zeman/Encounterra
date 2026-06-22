#include "core/combatant.hpp"

namespace enc
{

  class DraconicSorcererLvl3 : public Combatant
  {
  public:
    DraconicSorcererLvl3(int num);
    DraconicSorcererLvl3(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Draconic Sorcerer LVL 3";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Sorcerer::DRACONIC_SORCERY, _classLevel);
  };

}
