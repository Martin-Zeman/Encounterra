#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class OathOfVengeancePaladinLvl4 : public Combatant
  {
  public:
    OathOfVengeancePaladinLvl4(int num);
    OathOfVengeancePaladinLvl4(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Oath of Vengeance Paladin LVL 4";
    static constexpr int _classLevel = 4;
    static constexpr int _classId = Combatant::generateClassId(_className, Paladin::OATH_OF_VENGEANCE, _classLevel);
  };
}
