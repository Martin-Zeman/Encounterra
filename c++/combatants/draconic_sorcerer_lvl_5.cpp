#include "combatants/draconic_sorcerer_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  DraconicSorcererLvl5::DraconicSorcererLvl5(int num)
      : Combatant(CombatantType::SORCERER, Sorcerer::DRACONIC_SORCERY, _classLevel, concatName(std::string(_className), num), 37, 15, 2, 7, 30, 15)
  {
    _instanceId = generateInstanceId();
    addSpellSlots();
    addFirebolt();
  }

  DraconicSorcererLvl5::DraconicSorcererLvl5(const std::string &name)
      : Combatant(CombatantType::SORCERER, Sorcerer::DRACONIC_SORCERY, _classLevel, name, 37, 15, 2, 7, 30, 15)
  {
    _instanceId = generateInstanceId();
    addSpellSlots();
    addFirebolt();
  }

  ResourceState DraconicSorcererLvl5::exportResources()
  {
    // TODO
    return {};
  }
  void DraconicSorcererLvl5::importResources(const ResourceState &resources)
  {
    // TODO
  }
}