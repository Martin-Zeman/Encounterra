#include "utils.hpp"

namespace enc
{
  std::string concatName(std::string name, int num) { return name + " (" + std::to_string(num) + ")"; }
} // namespace enc
