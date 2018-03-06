set(proj RobartsVTKLib)

# Set dependency list
set(${proj}_DEPENDS "")

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

# Sanity checks
if(DEFINED RobartsVTKLib_DIR AND NOT EXISTS ${RobartsVTKLib_DIR})
  message(FATAL_ERROR "RobartsVTKLib_DIR variable is defined but corresponds to nonexistent directory")
endif()

# Qt support
set(RobartsVTK_USE_QT OFF)
if(DEFINED Qt5_DIR)
  set(RobartsVTK_USE_QT ON)
  list(APPEND ADDITIONAL_CMAKE_ARGS
    -DQt5_DIR:PATH=${Qt5_DIR}
    )
endif()

# Default to OFF until CUDA build machines are enabled
set(_default OFF)
find_package(CUDA QUIET)
if(CUDA_FOUND AND USE_CUDA)
  set(_default ON)
endif()
option(RobartsVTKLib_USE_CUDA "Whether to include CUDA classes in the build of RobartsVTKLib" ${_default})

if(NOT DEFINED ${proj}_DIR AND NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  if(MSVC)
    LIST(APPEND ADDITIONAL_CMAKE_ARGS -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${Slicer_QTLOADABLEMODULES_LIB_DIR})
  else()
    LIST(APPEND ADDITIONAL_CMAKE_ARGS -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${Slicer_QTLOADABLEMODULES_SHARE_DIR})
  endif()

  ExternalProject_SetIfNotDefined(
    ${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY
    "${EP_GIT_PROTOCOL}://github.com/VASST/RobartsVTK.git"
    QUIET
    )

  ExternalProject_SetIfNotDefined(
    ${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG
    "master"
    QUIET
    )

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
    BINARY_DIR ${proj}-build
    GIT_REPOSITORY ${${CMAKE_PROJECT_NAME}_${proj}_GIT_REPOSITORY}
    GIT_TAG ${${CMAKE_PROJECT_NAME}_${proj}_GIT_TAG}
    CMAKE_CACHE_ARGS
      # Compiler settings
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_CXX_STANDARD:STRING=${CMAKE_CXX_STANDARD}
      -DCMAKE_CXX_STANDARD_REQUIRED:BOOL=${CMAKE_CXX_STANDARD_REQUIRED}
      -DCMAKE_CXX_EXTENSIONS:BOOL=${CMAKE_CXX_EXTENSIONS}
      # Install directories
      -DVTK_INSTALL_PYTHON_MODULE_DIR:PATH=${Slicer_QTLOADABLEMODULES_BIN_DIR}
      -DCMAKE_RUNTIME_OUTPUT_DIRECTORY:PATH=${Slicer_QTLOADABLEMODULES_BIN_DIR}
      -DCMAKE_LIBRARY_OUTPUT_DIRECTORY:PATH=${Slicer_QTLOADABLEMODULES_LIB_DIR}
      # Dependencies
      -DVTK_DIR:PATH=${VTK_DIR}
      -DITK_DIR:PATH=${ITK_DIR}
      -DPYTHON_INCLUDE_DIR:STRING=${PYTHON_INCLUDE_DIR}
      -DPYTHON_LIBRARY:FILEPATH=${PYTHON_LIBRARY}
      -DPYTHON_EXECUTABLE:FILEPATH=${PYTHON_EXECUTABLE}
      # Options
      -DBUILD_SHARED_LIBS:BOOL=ON
      -DBUILD_TESTING:BOOL=OFF
      -DRobartsVTK_USE_ITK:BOOL=ON
      -DRobartsVTK_USE_PLUS:BOOL=OFF
      -DRobartsVTK_USE_REGISTRATION:BOOL=ON
      -DRobartsVTK_USE_COMMON:BOOL=ON
      -DRobartsVTK_USE_CUDA:BOOL=${RobartsVTKLib_USE_CUDA}
      -DRobartsVTK_USE_CUDA_VISUALIZATION:BOOL=ON # Controlled by RobartsVTK_USE_CUDA
      -DRobartsVTK_USE_CUDA_ANALYTICS:BOOL=ON # Controlled by RobartsVTK_USE_CUDA
      -DRobartsVTK_USE_QT:BOOL=${RobartsVTK_USE_QT}
      -DRobartsVTK_BUILD_APPS:BOOL=OFF
      -DRobartsVTK_WRAP_PYTHON:BOOL=ON
      ${ADDITIONAL_CMAKE_ARGS}
    INSTALL_COMMAND "" # Do not install
    DEPENDS
      ${${proj}_DEPENDS}
    )
  set(${proj}_DIR ${CMAKE_BINARY_DIR}/${proj}-build)

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDS})
endif()

mark_as_superbuild(${proj}_DIR:PATH)
