cmake_minimum_required(VERSION 3.0)

project(SlicerVASST)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/SlicerVASST")
set(EXTENSION_CATEGORY "Registration;Segmentation;Visualization")
set(EXTENSION_CONTRIBUTORS "Adam Rankin (Robarts Research Institute)")
set(EXTENSION_DESCRIPTION "This extension contains a number of modules developed by the VASST laboratory at the Robarts Research Institute. It provides access to RobartsVTK, a library for visualization and image processing.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SlicerVASST.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SlicerVASST/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # NA if none
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT RobartsVTK)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
include(${Slicer_EXTENSION_CPACK})
