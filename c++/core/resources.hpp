#pragma once

namespace enc
{

  enum class ResourceDepletionLevel
  {
    FULLY_RESTED = 1,
    PARTIALLY_DEPLETED,
    FULLY_DEPLETED
  };

  enum class ResourceRefreshType
  {
    LONG_REST,
    SHORT_REST,
    ROUND,
    NEVER
  };
}