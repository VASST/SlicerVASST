cmake_minimum_required(VERSION 3.13.4)

project(SlicerVASST)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/VASST/SlicerVASST")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Adam Rankin (Robarts Research Institute), Golafsoun Ameri (Robarts Research Institute), Elvis Chen (Robarts Research Institute)")
set(EXTENSION_DESCRIPTION "This extension contains a number of modules developed by the VASST laboratory at the Robarts Research Institute.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/VASST/SlicerVASST/master/docs/images/SlicerVASST_logo.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/VASST/SlicerVASST/master/docs/images/screenshot.png")
set(EXTENSION_DEPENDS "VASSTAlgorithms;SlicerIGT;SlicerVirtualReality;Sequences;SlicerOpenCV")
set(EXTENSION_STATUS "Stable")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(GuidedUSCal)
add_subdirectory(VRVisionExperiment)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
