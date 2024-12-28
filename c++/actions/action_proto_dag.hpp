#pragma once
#include <vector>
#include <memory>
#include <utility>
#include <unordered_set>
#include "core/interfaces.hpp"
#include "core/state_machine.hpp"

namespace enc
{
  class Combatant;

  struct ActionFootprint
  {
    std::unordered_set<size_t> actionHashes;
    // Optionally keep the actions if we need them later
    // std::vector<std::shared_ptr<Actoid>> actions;

    explicit ActionFootprint(const std::vector<std::shared_ptr<Actoid>> &actoids)// : actions(actoids) // Optional
    {
      for(const auto &actoid : actoids)
        {
          actionHashes.insert(actoid->getHash());
        }
    }

    bool operator==(const ActionFootprint &other) const { return actionHashes == other.actionHashes; }
  };

  struct ActionFootprintHash
  {
    size_t operator()(const ActionFootprint &fp) const
    {
      size_t hash = 0;
      for(auto h : fp.actionHashes)
        {
          hash ^= h + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        }
      return hash;
    }
  };

  class DummyActoid : public Actoid
  {
  public:
    DummyActoid(ActoidFactory &factory, std::string name, ActoidFlags flags = ActoidFlags::DEFAULT) : Actoid(factory, flags), _name(std::move(name))
    {}

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override
    {
      return std::nullopt;
    }

    std::string toString() const override { return _name; }

    bool equals(const Actoid &other) const override
    {
      if(auto *o = dynamic_cast<const DummyActoid *>(&other))
        {
          return _name == o->_name && _actoidFlags == o->_actoidFlags;
        }
      return false;
    }

  protected:
    size_t hash() const override
    {
      size_t h = std::hash<uint32_t>{}(_actoidFlags);
      h ^= std::hash<std::string>{}(_name) + 0x9e3779b9 + (h << 6) + (h >> 2);
      return h;
    }

  private:
    std::string _name;
  };

  class DummyActoidFactory : public ActoidFactory
  {
  public:
    DummyActoidFactory() : ActoidFactory("DummyFactory", "Dummy", nullptr, AbilityType::NOP) {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override { return {}; }

    std::shared_ptr<Actoid> create(void *target) override { return nullptr; }

    std::optional<Resource *> getResource() override { return std::nullopt; }

    std::shared_ptr<DummyActoid> createTestActoid(const std::string &name) { return std::make_shared<DummyActoid>(*this, name); }
  };

  std::vector<std::shared_ptr<ActoidFactory>> getAllFeasibleActionFactories(Combatant *combatant, int depth);

  /**
   * Finds the path through the DAG which represents all possible movements and actions for a combatant.
   * The DAG construction takes advantage of the fact that as a result of the DFS traversal, the actions
   * in generated sequences are coordianate-wise. Therefore, we can process the sequences by these
   * coord-wise blocks and call as_if_combatant_position once per block.
   *
   * @param combatant The combatant for whom the DAG is modeled
   * @return The state machine representing all possible action combinations
   */
  StateMachine generateProtoDAG(Combatant *combatant);

  /**
   * A special variation of generateProtoDAG which generates an action DAG where only Wildshape
   * actions are allowed as the first action.
   *
   * @param combatant The combatant for whom the DAG is modeled
   * @return The state machine representing all possible action combinations starting with Wildshape
   */
  StateMachine generateWildshapeProtoDAG(Combatant *combatant);
}