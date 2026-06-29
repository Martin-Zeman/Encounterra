#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class BardCollegeOfLoreLvl3 : public Combatant
  {
  public:
    BardCollegeOfLoreLvl3(int num);
    BardCollegeOfLoreLvl3(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Bard College of Lore LVL 3";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Bard::COLLEGE_OF_LORE, _classLevel);
  };
}
