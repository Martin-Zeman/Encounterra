#include "abilities/wildshape_utils.hpp"
#include <iostream>

namespace enc
{
  std::vector<WildshapeUtils::CombatantFactory> WildshapeUtils::getAvailableWildshapeForms(int level, AbilityType actionType)
  {
    if(actionType == AbilityType::WILDSHAPE)
      {
        return {};
      }
    else if(actionType == AbilityType::MOON_WILDSHAPE)
      {
        std::vector<CombatantFactory> forms;

        if(level < 3)
          {
            std::cerr << "Incorrect character level. No wildshape forms added!" << std::endl;
            return forms;
          }

        // Base forms available at all levels 3+
        forms = {[](const std::string &name) { return std::make_unique<DireWolf>(name); },
                 [](const std::string &name) { return std::make_unique<BrownBear>(name); },
                 [](const std::string &name) { return std::make_unique<GiantToad>(name); },
                 [](const std::string &name) { return std::make_unique<GiantSpider>(name); }};

        // Add additional forms based on level
        if(level >= 6)
          {
            forms.push_back([](const std::string &name) { return std::make_unique<GiantConstrictorSnake>(name); });
            forms.push_back([](const std::string &name) { return std::make_unique<SaberToothedTiger>(name); });
          }

        /* Commented out forms
        if (level >= 9)
        {
          forms.push_back([](const std::string& name) { return std::make_unique<Quetzalcoatlus>(name); });
          // forms.push_back([](const std::string& name) { return std::make_unique<Ankylosaurus>(name); });
          // forms.push_back([](const std::string& name) { return std::make_unique<GiantScorpion>(name); });
        }

        if (level >= 12)
        {
          // forms.push_back([](const std::string& name) { return std::make_unique<Stegosaurus>(name); });
        }

        if (level >= 15)
        {
          // forms.push_back([](const std::string& name) { return std::make_unique<GiantCrocodile>(name); });
        }

        if (level >= 18)
        {
          // forms.push_back([](const std::string& name) { return std::make_unique<Mammoth>(name); });
        }
        */

        return forms;
      }

    return {};
  }

  std::vector<std::shared_ptr<Wildshape>>
  WildshapeUtils::preallocateWildshapeForms(Combatant *combatant, AbilityType actionType, WildshapeFactory &factory)
  {
    auto formFactories = getAvailableWildshapeForms(combatant->getLevel(), actionType);
    std::vector<std::shared_ptr<Wildshape>> forms;
    forms.reserve(formFactories.size());

    for(const auto &formFactory : formFactories)
      {
        auto form = formFactory(combatant->getName() + " wildshaped");
        forms.push_back(std::make_shared<Wildshape>(combatant, std::move(form), factory));
      }

    return forms;
  }

} // namespace enc
