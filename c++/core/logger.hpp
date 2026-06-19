#pragma once

namespace enc
{
  // Verbosity levels for the simulation's console output.
  //   NONE  - suppress everything (used for benchmarking / batch runs).
  //   ERROR - only error / warning output (std::cerr).
  //   INFO  - full combat narration (std::cout + std::cerr). This is the default,
  //           so existing behaviour is unchanged unless a level is set explicitly.
  enum class LogLevel
  {
    NONE = 0,
    ERROR = 1,
    INFO = 2
  };

  // Lightweight global logging switch. The engine narrates combat directly through
  // std::cout / std::cerr; setLevel() (re)routes those streams to a null sink so the
  // verbosity can be controlled from a single place without touching every call site.
  class Logger
  {
  public:
    static void setLevel(LogLevel level);
    static LogLevel getLevel();

  private:
    static LogLevel _level;
  };
}
