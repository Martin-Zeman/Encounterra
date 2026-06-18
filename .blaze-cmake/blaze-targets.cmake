# Blaze targets
# Defines the blaze::blaze IMPORTED target

if(NOT TARGET blaze::blaze)
  add_library(blaze::blaze INTERFACE IMPORTED)
  set_target_properties(blaze::blaze PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "/usr/local/include"
    INTERFACE_COMPILE_DEFINITIONS "BLAZE_CACHE_SIZE=31457280"
  )
endif()
