#include "core/combatant.hpp"

namespace enc
{

  class WildHeartBarbarianLvl3 : public Combatant
  {
  public:
    WildHeartBarbarianLvl3(int num);
    WildHeartBarbarianLvl3(const std::string &name);

    int getClassId() const override { return _classId; }
    ResourceState exportResources() override;
    void importResources(const ResourceState &resources) override;

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Wild Heart Barbarian LVL 3";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Barbarian::PATH_OF_WILD_HEART, _classLevel);
  };

}
