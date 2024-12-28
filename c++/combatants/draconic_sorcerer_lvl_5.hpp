#include "core/combatant.hpp"

namespace enc
{

  class DraconicSorcererLvl5 : public Combatant
  {
  public:
    DraconicSorcererLvl5(int num);
    DraconicSorcererLvl5(const std::string &name);

    int getClassId() const override { return _classId; }
    ResourceState exportResources() override;
    void importResources(const ResourceState &resources) override;

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Draconic Sorcerer LVL 5";
    static constexpr int _classLevel = 5;
    static constexpr int _classId = Combatant::generateClassId(_className, Sorcerer::DRACONIC_SORCERY, _classLevel);
  };

}
