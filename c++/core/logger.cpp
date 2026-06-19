#include "core/logger.hpp"

#include <iostream>
#include <streambuf>

namespace enc
{
  namespace
  {
    // A streambuf that discards everything written to it.
    class NullBuffer : public std::streambuf
    {
    public:
      int overflow(int c) override { return c; }
    };

    NullBuffer nullBuffer;

    // Original stream buffers, saved while a stream is being suppressed so it can be
    // restored when logging is re-enabled.
    std::streambuf *savedCout = nullptr;
    std::streambuf *savedCerr = nullptr;

    void setStreamEnabled(std::ostream &stream, bool enabled, std::streambuf *&saved)
    {
      if(!enabled)
        {
          if(saved == nullptr)
            saved = stream.rdbuf(&nullBuffer);
        }
      else if(saved != nullptr)
        {
          stream.rdbuf(saved);
          saved = nullptr;
        }
    }
  } // namespace

  LogLevel Logger::_level = LogLevel::INFO;

  void Logger::setLevel(LogLevel level)
  {
    _level = level;
    const bool showInfo = static_cast<int>(level) >= static_cast<int>(LogLevel::INFO);
    const bool showError = static_cast<int>(level) >= static_cast<int>(LogLevel::ERROR);
    setStreamEnabled(std::cout, showInfo, savedCout);
    setStreamEnabled(std::cerr, showError, savedCerr);
  }

  LogLevel Logger::getLevel() { return _level; }
}
