# This module defines the following variables:
#
# FFmpeg_FOUND          - All required components and the core library were found
# FFmpeg_INCLUDE_DIRS   - Combined list of all components include dirs
# FFmpeg_LIBRARIES      - Combined list of all components libraries
# FFmpeg_VERSION        - Version defined in libavutil/ffversion.h
#
# ffmpeg::ffmpeg        - FFmpeg target
#
# For each requested component the following variables are defined:
#
# FFmpeg_<component>_FOUND          - The component was found
# FFmpeg_<component>_INCLUDE_DIRS   - The components include dirs
# FFmpeg_<component>_LIBRARIES      - The components libraries
# FFmpeg_<component>_VERSION        - The components version
#
# ffmpeg::<component>               - The component target
#
# Usage:
#   find_package(FFmpeg REQUIRED)
#   find_package(FFmpeg 5.1.2 COMPONENTS avutil avcodec avformat avdevice avfilter REQUIRED)

find_package(PkgConfig QUIET)

# find the root dir for specified version
function(find_ffmpeg_root_by_version EXPECTED_VERSION)
    set(FFMPEG_FIND_PATHS $ENV{PATH} $ENV{FFMPEG_PATH} $ENV{FFMPEG_ROOT} /opt /usr /sw)

    set(FOUND_VERSION)
    set(FOUND_ROOT_DIR)

    foreach(ROOT_DIR ${FFMPEG_FIND_PATHS})
        unset(FFMPEG_VERSION_HEADER CACHE)
        find_file(
            FFMPEG_VERSION_HEADER
            NAMES "ffversion.h"
            PATHS ${ROOT_DIR} ${ROOT_DIR}/include ${ROOT_DIR}/include/${CMAKE_LIBRARY_ARCHITECTURE}
            PATH_SUFFIXES libavutil
            NO_DEFAULT_PATH
        )
        mark_as_advanced(FFMPEG_VERSION_HEADER)

        if(NOT "${FFMPEG_VERSION_HEADER}" STREQUAL "FFMPEG_VERSION_HEADER-NOTFOUND")
            file(STRINGS "${FFMPEG_VERSION_HEADER}" FFMPEG_VERSION_STRING REGEX "FFMPEG_VERSION")

            # #define FFMPEG_VERSION "6.0-full_build-www.gyan.dev"
            # fixme:    #define FFMPEG_VERSION "N-111059-gd78bffbf3d"
            string(REGEX REPLACE ".*FFMPEG_VERSION[ \t]+\"[n]?([0-9\\.]*).*\"" "\\1" CURRENT_VERSION "${FFMPEG_VERSION_STRING}")

            # not specified, return the first one
            if("${EXPECTED_VERSION}" STREQUAL "")
                set(FOUND_VERSION ${CURRENT_VERSION})
                set(FOUND_ROOT_DIR ${ROOT_DIR})
                break()
            endif()

            # otherwise, the minimum one of suitable versions
            if(${CURRENT_VERSION} VERSION_GREATER_EQUAL "${EXPECTED_VERSION}")
                if((NOT FOUND_VERSION) OR(${CURRENT_VERSION} VERSION_LESS "${FOUND_VERSION}"))
                    set(FOUND_VERSION ${CURRENT_VERSION})
                    set(FOUND_ROOT_DIR ${ROOT_DIR})
                endif()
            endif()
        endif()
    endforeach()

    set(FFmpeg_VERSION ${FOUND_VERSION} PARENT_SCOPE)
    set(FFmpeg_ROOT_DIR ${FOUND_ROOT_DIR} PARENT_SCOPE)
endfunction()

# find a ffmpeg component
function(find_ffmpeg_component ROOT_DIR COMPONENT HEADER)
    # header
    find_path(
        FFmpeg_${COMPONENT}_INCLUDE_DIR
        NAMES "lib${COMPONENT}/${HEADER}" "lib${COMPONENT}/version.h"
        PATHS ${ROOT_DIR} ${ROOT_DIR}/include/${CMAKE_LIBRARY_ARCHITECTURE}
        PATH_SUFFIXES ffmpeg libav include
        NO_DEFAULT_PATH
    )

    # version
    if(EXISTS "${FFmpeg_${COMPONENT}_INCLUDE_DIR}/lib${COMPONENT}/version.h")
        if(EXISTS "${FFmpeg_${COMPONENT}_INCLUDE_DIR}/lib${COMPONENT}/version_major.h")
            file(STRINGS "${FFmpeg_${COMPONENT}_INCLUDE_DIR}/lib${COMPONENT}/version_major.h" MAJOR_VERSION_STRING REGEX "^.*VERSION_MAJOR[ \t]+[0-9]+[ \t]*$")
        endif()

        # other
        file(STRINGS "${FFmpeg_${COMPONENT}_INCLUDE_DIR}/lib${COMPONENT}/version.h" VERSION_STRING REGEX "^.*VERSION_(MAJOR|MINOR|MICRO)[ \t]+[0-9]+[ \t]*$")

        list(APPEND VERSION_STRING ${MAJOR_VERSION_STRING})

        string(REGEX REPLACE ".*VERSION_MAJOR[ \t]+([0-9]+).*" "\\1" MAJOR "${VERSION_STRING}")
        string(REGEX REPLACE ".*VERSION_MINOR[ \t]+([0-9]+).*" "\\1" MINOR "${VERSION_STRING}")
        string(REGEX REPLACE ".*VERSION_MICRO[ \t]+([0-9]+).*" "\\1" PATCH "${VERSION_STRING}")

        set(FFmpeg_${COMPONENT}_VERSION "${MAJOR}.${MINOR}.${PATCH}" PARENT_SCOPE)
    else()
        message(STATUS "'${FFmpeg_${COMPONENT}_INCLUDE_DIR}/lib${COMPONENT}/version.h' does not exist.")
    endif()

    # library
    if(WIN32)
        find_library(
            FFmpeg_${COMPONENT}_IMPLIB
            NAMES "${COMPONENT}" "lib${COMPONENT}"
            PATHS ${ROOT_DIR} ${ROOT_DIR}/lib/${CMAKE_LIBRARY_ARCHITECTURE}
            PATH_SUFFIXES lib lib64 bin bin64
            NO_DEFAULT_PATH
        )

        find_program(
            FFmpeg_${COMPONENT}_LIBRARY
            NAMES "${COMPONENT}-${MAJOR}.dll" "${COMPONENT}.dll"
            PATHS ${ROOT_DIR} ${ROOT_DIR}/bin
            NO_DEFAULT_PATH
        )
    else()
        find_library(
            FFmpeg_${COMPONENT}_LIBRARY
            NAMES "${COMPONENT}" "lib${COMPONENT}"
            PATHS ${ROOT_DIR} ${ROOT_DIR}/lib/${CMAKE_LIBRARY_ARCHITECTURE}
            PATH_SUFFIXES lib lib64 bin bin64
            NO_DEFAULT_PATH
        )
    endif()

    mark_as_advanced(FFmpeg_${COMPONENT}_INCLUDE_DIR FFmpeg_${COMPONENT}_LIBRARY FFmpeg_${COMPONENT}_IMPLIB)

    if(FFmpeg_${COMPONENT}_INCLUDE_DIR AND FFmpeg_${COMPONENT}_LIBRARY)
        set(FFmpeg_${COMPONENT}_FOUND TRUE PARENT_SCOPE)

        set(FFmpeg_${COMPONENT}_IMPLIBS ${FFmpeg_${COMPONENT}_IMPLIB} PARENT_SCOPE)
        set(FFmpeg_${COMPONENT}_LIBRARIES ${FFmpeg_${COMPONENT}_LIBRARY} PARENT_SCOPE)
        set(FFmpeg_${COMPONENT}_INCLUDE_DIRS ${FFmpeg_${COMPONENT}_INCLUDE_DIR} PARENT_SCOPE)
    endif()
endfunction()

# start finding
if(NOT FFmpeg_FIND_COMPONENTS)
    list(APPEND FFmpeg_FIND_COMPONENTS avutil avcodec avdevice avfilter avformat swresample swscale postproc)
endif()

find_ffmpeg_root_by_version("${FFmpeg_FIND_VERSION}")

if((NOT FFmpeg_VERSION) OR(NOT FFmpeg_ROOT_DIR))
    message(FATAL_ERROR "Can not find the suitable version.")
endif()

list(REMOVE_DUPLICATES FFmpeg_FIND_COMPONENTS)

foreach(COMPONENT ${FFmpeg_FIND_COMPONENTS})
    if(COMPONENT STREQUAL "postproc")
        find_ffmpeg_component(${FFmpeg_ROOT_DIR} ${COMPONENT} "postprocess.h")
    else()
        find_ffmpeg_component(${FFmpeg_ROOT_DIR} ${COMPONENT} "${component}.h")
    endif()

    if(FFmpeg_${COMPONENT}_FOUND)
        list(APPEND FFmpeg_LIBRARIES ${FFmpeg_${COMPONENT}_LIBRARIES})
        list(APPEND FFmpeg_INCLUDE_DIRS ${FFmpeg_${COMPONENT}_INCLUDE_DIRS})
    endif()
endforeach()

list(REMOVE_DUPLICATES FFmpeg_LIBRARIES)
list(REMOVE_DUPLICATES FFmpeg_INCLUDE_DIRS)

#
include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(
    FFmpeg
    FOUND_VAR FFmpeg_FOUND
    REQUIRED_VARS FFmpeg_ROOT_DIR FFmpeg_INCLUDE_DIRS FFmpeg_LIBRARIES
    VERSION_VAR FFmpeg_VERSION
    HANDLE_COMPONENTS
)

if(FFmpeg_FOUND)
    if(NOT TARGET ffmpeg::ffmpeg)
        add_library(ffmpeg::ffmpeg INTERFACE IMPORTED)
    endif()

    foreach(component IN LISTS FFmpeg_FIND_COMPONENTS)
        if(FFmpeg_${component}_FOUND AND NOT TARGET ffmpeg::${component})
            if(IS_ABSOLUTE "${FFmpeg_${component}_LIBRARIES}")
                if(DEFINED FFmpeg_${component}_IMPLIBS)
                    if(FFmpeg_${component}_IMPLIBS STREQUAL FFmpeg_${component}_LIBRARIES)
                        add_library(ffmpeg::${component} STATIC IMPORTED)
                    else()
                        add_library(ffmpeg::${component} SHARED IMPORTED)
                        set_property(TARGET ffmpeg::${component} PROPERTY IMPORTED_IMPLIB "${FFmpeg_${component}_IMPLIBS}")
                    endif()
                else()
                    add_library(ffmpeg::${component} UNKNOWN IMPORTED)
                endif()

                set_property(TARGET ffmpeg::${component} PROPERTY IMPORTED_LOCATION "${FFmpeg_${component}_LIBRARIES}")
            else()
                add_library(ffmpeg::${component} INTERFACE IMPORTED)
                set_target_properties(ffmpeg::${component} PROPERTIES IMPORTED_LIBNAME "${FFmpeg_${component}_LIBRARIES}")
            endif()

            set_target_properties(ffmpeg::${component} PROPERTIES
                INTERFACE_INCLUDE_DIRECTORIES "${FFmpeg_${component}_INCLUDE_DIRS}"
                VERSION "${FFmpeg_${component}_VERSION}"
            )

            get_target_property(FFMPEG_INTERFACE_LIBRARIES ffmpeg::ffmpeg INTERFACE_LINK_LIBRARIES)

            if(NOT ffmpeg::${component} IN_LIST FFMPEG_INTERFACE_LIBRARIES)
                set_property(TARGET ffmpeg::ffmpeg APPEND PROPERTY INTERFACE_LINK_LIBRARIES ffmpeg::${component})
            endif()
        endif()
    endforeach()
endif()
