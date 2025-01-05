#include "draconic_sorcerer_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  DraconicSorcererLvl1::DraconicSorcererLvl1(int num) : DraconicSorcererLvl1(concatName(std::string(_className), num)) {}

  DraconicSorcererLvl1::DraconicSorcererLvl1(const std::string &name)
      : Combatant(CombatantType::SORCERER, Sorcerer::BEFORE_SUBCLASS, _classLevel, name, 7, 15, 2, 5, 30, 0)
  {
    _instanceId = generateInstanceId();
    addSpellSlots();
    addFirebolt();
  }

  ResourceState DraconicSorcererLvl1::exportResources()
  {
    // TODO
    return {};
  }
  void DraconicSorcererLvl1::importResources(const ResourceState &resources)
  {
    // TODO
  }
}