#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class OathOfVengeancePaladinLvl3 : public Combatant
  {
  public:
    OathOfVengeancePaladinLvl3(int num);
    OathOfVengeancePaladinLvl3(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Oath of Vengeance Paladin LVL 3";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Paladin::OATH_OF_VENGEANCE, _classLevel);
  };
}
