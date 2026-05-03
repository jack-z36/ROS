# This module defines the following variables:
#
# PipeWire_FOUND
# PipeWire_INCLUDE_DIRS
# PipeWire_LIBRARIES
# SPA_INCLUDE_DIRS
#
# PipeWire::PipeWire        - PipeWire target
# 

find_package(PkgConfig QUIET)

if(PKG_CONFIG_FOUND)
    pkg_check_modules(PKG_PIPEWIRE QUIET libpipewire-0.3)
    pkg_check_modules(PKG_SPA QUIET libspa-0.2)

    set(PipeWire_COMPILE_FLAGS "${PKG_PIPEWIRE_CFLAGS}" "${PKG_SPA_CFLAGS}")
    set(PipeWire_VERSION "${PKG_PIPEWIRE_VERSION}")
endif()

find_path(
    PipeWire_INCLUDE_DIRS
    NAMES pipewire/pipewire.h
    HINTS ${PKG_PIPEWIRE_INCLUDE_DIRS}
)

find_library(
    PipeWire_LIBRARIES
    NAMES pipewire-0.3
    HINTS ${PKG_PIPEWIRE_LIBRARY_DIRS}
)

find_path(
    SPA_INCLUDE_DIRS
    NAMES spa/param/props.h
    HINTS ${PKG_SPA_INCLUDE_DIRS} ${PKG_SPA_INCLUDE_DIRS}/spa-0.2
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(
    PipeWire 
    FOUND_VAR PipeWire_FOUND
    REQUIRED_VARS PipeWire_INCLUDE_DIRS PipeWire_LIBRARIES SPA_INCLUDE_DIRS
    VERSION_VAR PipeWire_VERSION
)

if(PipeWire_FOUND AND NOT TARGET PipeWire::PipeWire)
    if(IS_ABSOLUTE "${PipeWire_LIBRARIES}")
        add_library(PipeWire::PipeWire UNKNOWN IMPORTED)
        set_target_properties(PipeWire::PipeWire PROPERTIES IMPORTED_LOCATION "${PipeWire_LIBRARIES}")
    else()
        add_library(PipeWire::PipeWire INTERFACE IMPORTED)
        set_target_properties(PipeWire::PipeWire PROPERTIES IMPORTED_LIBNAME "${PipeWire_LIBRARIES}")
    endif()

    set_target_properties(
        PipeWire::PipeWire 
        PROPERTIES
            INTERFACE_COMPILE_OPTIONS "${PipeWire_COMPILE_FLAGS}"
            INTERFACE_INCLUDE_DIRECTORIES "${PipeWire_INCLUDE_DIRS};${SPA_INCLUDE_DIRS}"
    )
endif()
