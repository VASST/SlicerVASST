cmake_minimum_required(VERSION 3.5)

project(SlicerVASST)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/VASST/SlicerVASST")
set(EXTENSION_CATEGORY "Registration;Segmentation;Visualization")
set(EXTENSION_CONTRIBUTORS "Adam Rankin (Robarts Research Institute), Golafsoun Ameri (Robarts Research Institute), Elvis Chen (Robarts Research Institute)")
set(EXTENSION_DESCRIPTION "This extension contains a number of modules developed by the VASST laboratory at the Robarts Research Institute. It provides access to RobartsVTK, a library for visualization and image processing.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/VASST/SlicerVASST/master/docs/images/SlicerVASST_logo.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/VASST/SlicerVASST/master/docs/images/screenshot.png")
set(EXTENSION_DEPENDS "SlicerIGT;VASSTAlgorithms")
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

find_package(SlicerIGT REQUIRED)
mark_as_superbuild(SlicerIGT_DIR)

find_package(VASSTAlgorithms REQUIRED)
mark_as_superbuild(VASSTAlgorithms_DIR)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(NeoGuidance)
add_subdirectory(GuidedUSCal)
add_subdirectory(VRVisionExperiment)
## NEXT_MODULE

#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/;${RobartsVTKLib_DIR};RobartsVTKLib;ALL;/")
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
