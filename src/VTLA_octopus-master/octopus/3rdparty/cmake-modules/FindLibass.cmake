# This module defines the following variables:
#
# Libass_FOUND
# Libass_INCLUDE_DIRS
# Libass_LIBRARIES
#
# ass::ass        - Libass target
#

find_package(PkgConfig QUIET)

find_path(
    Libass_INCLUDE_DIRS
    NAMES ass/ass.h
    HINTS ${LIBASS_INCLUDE_DIRS}
    PATH_SUFFIXES include
)

find_library(
    Libass_LIBRARIES
    NAMES ass
    HINTS ${LIBASS_LIBRARY_DIRS}
    PATH_SUFFIXES x64 bin/x64 lib lib/x64
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(
    Libass
    FOUND_VAR Libass_FOUND
    REQUIRED_VARS Libass_INCLUDE_DIRS Libass_LIBRARIES
    VERSION_VAR Libass_VERSION
)

if(Libass_FOUND AND NOT TARGET ass::ass)
    if(IS_ABSOLUTE "${Libass_LIBRARIES}")
        add_library(ass::ass UNKNOWN IMPORTED)
        set_target_properties(ass::ass PROPERTIES IMPORTED_LOCATION "${Libass_LIBRARIES}")
    else()
        add_library(ass::ass INTERFACE IMPORTED)
        set_target_properties(ass::ass PROPERTIES IMPORTED_LIBNAME "${Libass_LIBRARIES}")
    endif()

    set_target_properties(
        ass::ass
        PROPERTIES
            INTERFACE_COMPILE_OPTIONS "${Libass_COMPILE_FLAGS}"
            INTERFACE_INCLUDE_DIRECTORIES "${Libass_INCLUDE_DIRS}"
    )
endif()
