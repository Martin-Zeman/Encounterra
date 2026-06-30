#include "session.hpp"
#include "combatants/fighter_lvl_1.hpp"
#include "combatants/fighter_lvl_2.hpp"
#include "combatants/battlemaster_fighter_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_4.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/paladin_lvl_1.hpp"
#include "combatants/paladin_lvl_2.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_3.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_4.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_5.hpp"
#include "combatants/cleric_lvl_1.hpp"
#include "combatants/brown_bear.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/goblin.hpp"
#include "combatants/sorcerer_lvl_1.hpp"
#include "combatants/draconic_sorcerer_lvl_3.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/ogre.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "combatants/wild_heart_barbarian_lvl_4.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "combatants/green_dragon_wyrmling.hpp"
#include "combatants/moon_druid_lvl_3.hpp"
#include "combatants/dire_wolf.hpp"
#include "combatants/giant_spider.hpp"
#include "combatants/tiger.hpp"
#include "combatants/lion.hpp"
#include "combatants/wizard_lvl_1.hpp"
#include "combatants/bard_college_of_lore_lvl_3.hpp"
#include "combatants/warlock_lvl_1.hpp"
#include "combatants/warlock_lvl_2.hpp"
#include "combatants/warlock_lvl_3.hpp"
#include "combatants/warlock_lvl_4.hpp"
#include "combatants/warlock_lvl_5.hpp"

namespace enc
{

  Session::Session() : _teams(Teams::getInstance())
  {
    // Register all combatant types
    registerCombatantType<FighterLvl1>();
    registerCombatantType<FighterLvl2>();
    registerCombatantType<BattlemasterFighterLvl3>();
    registerCombatantType<BattlemasterFighterLvl4>();
    registerCombatantType<BattlemasterFighterLvl5>();
    registerCombatantType<PaladinLvl1>();
    registerCombatantType<PaladinLvl2>();
    registerCombatantType<OathOfVengeancePaladinLvl3>();
    registerCombatantType<OathOfVengeancePaladinLvl4>();
    registerCombatantType<OathOfVengeancePaladinLvl5>();
    registerCombatantType<ClericLvl1>();
    registerCombatantType<BrownBear>();
    registerCombatantType<BugbearWarrior>();
    registerCombatantType<SorcererLvl1>();
    registerCombatantType<DraconicSorcererLvl3>();
    registerCombatantType<GiantToad>();
    registerCombatantType<Goblin>();
    registerCombatantType<GreenDragonWyrmling>();
    registerCombatantType<Ogre>();
    registerCombatantType<StoneGiant>();
    registerCombatantType<WildHeartBarbarianLvl3>();
    registerCombatantType<WildHeartBarbarianLvl4>();
    registerCombatantType<WildHeartBarbarianLvl5>();
    registerCombatantType<MoonDruidLvl3>();
    registerCombatantType<DireWolf>();
    registerCombatantType<GiantSpider>();
    registerCombatantType<Tiger>();
    registerCombatantType<Lion>();
    registerCombatantType<WizardLvl1>();
    registerCombatantType<BardCollegeOfLoreLvl3>();
    registerCombatantType<WarlockLvl1>();
    registerCombatantType<WarlockLvl2>();
    registerCombatantType<WarlockLvl3>();
    registerCombatantType<WarlockLvl4>();
    registerCombatantType<WarlockLvl5>();
    // Register other combatant types...
  }

  template <typename CombatantType> void Session::addCombatant(Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    int classId = CombatantType::getStaticClassId();
    auto factoryIt = _combatantFactories.find(classId);

    if(factoryIt == _combatantFactories.end())
      {
        throw std::runtime_error("Unsupported combatant type");
      }

    auto combatant = factoryIt->second(++_typeCounter[classId] + 1);
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.push_back(std::move(combatant));
    generateUniqueShortCodes();
  }
  
  template <typename CombatantType> void Session::addCombatant(CombatantType* combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    // For testing purposes
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.emplace_back(std::move(std::unique_ptr<Combatant>(combatant)));
    generateUniqueShortCodes();
  }

  template <typename CombatantType> void Session::registerCombatantType()
  {
    int classId = CombatantType::getStaticClassId();
    _combatantFactories[classId] = [](int num) { return std::make_unique<CombatantType>(num); };
  }

  // Explicit template instantiations
  template void Session::addCombatant<BattlemasterFighterLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<PaladinLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<PaladinLvl2>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<OathOfVengeancePaladinLvl3>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<OathOfVengeancePaladinLvl4>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<OathOfVengeancePaladinLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<ClericLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BrownBear>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BugbearWarrior>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<SorcererLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl3>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl4>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<MoonDruidLvl3>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<DireWolf>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantSpider>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Tiger>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Lion>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WizardLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BardCollegeOfLoreLvl3>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl2>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl3>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl4>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BattlemasterFighterLvl5>(BattlemasterFighterLvl5*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<PaladinLvl1>(PaladinLvl1*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<PaladinLvl2>(PaladinLvl2*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<OathOfVengeancePaladinLvl3>(OathOfVengeancePaladinLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<OathOfVengeancePaladinLvl4>(OathOfVengeancePaladinLvl4*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<OathOfVengeancePaladinLvl5>(OathOfVengeancePaladinLvl5*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<ClericLvl1>(ClericLvl1*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BrownBear>(BrownBear*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BugbearWarrior>(BugbearWarrior*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<SorcererLvl1>(SorcererLvl1*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl3>(DraconicSorcererLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(GiantToad*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(Goblin*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(GreenDragonWyrmling*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(Ogre*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(StoneGiant*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(WildHeartBarbarianLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl4>(WildHeartBarbarianLvl4*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl5>(WildHeartBarbarianLvl5*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<MoonDruidLvl3>(MoonDruidLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DireWolf>(DireWolf*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantSpider>(GiantSpider*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Tiger>(Tiger*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Lion>(Lion*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WizardLvl1>(WizardLvl1*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BardCollegeOfLoreLvl3>(BardCollegeOfLoreLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl1>(WarlockLvl1*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl2>(WarlockLvl2*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl3>(WarlockLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl4>(WarlockLvl4*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WarlockLvl5>(WarlockLvl5*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Combatant>(Combatant*, Color, ResourceDepletionLevel);

  // Add more explicit instantiations for other combatant types
}
