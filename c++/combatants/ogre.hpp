#include "core/combatant.hpp"

namespace enc
{

  class Ogre : public Combatant
  {
  public:
    Ogre(int num);
    Ogre(const std::string &name);

    int getClassId() const override { return _classId; }
    ResourceState exportResources() override;
    void importResources(const ResourceState &resources) override;

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Ogre";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Monster::GIANT, _classLevel);
  };

}
