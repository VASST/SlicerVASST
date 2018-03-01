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

if(Qt5_DIR)
  list(APPEND ADDITIONAL_CMAKE_ARGS
    -DRobartsVTK_USE_QT:BOOL=ON
    -DQt5_DIR:PATH=${Qt5_DIR}
    )
else()
  list(APPEND ADDITIONAL_CMAKE_ARGS
    -DRobartsVTK_USE_QT:BOOL=OFF
    )
endif()

if(QT_QMAKE_EXECUTABLE)
  list(APPEND ADDITIONAL_CMAKE_ARGS
    -DQT_QMAKE_EXECUTABLE:FILEPATH=${QT_QMAKE_EXECUTABLE}
    )
endif()

option(USE_CUDA "Whether to include CUDA classes in the build of RobartsVTKLib" OFF) # Default to OFF until CUDA build machines are enabled
find_package(CUDA QUIET)
if(CUDA_FOUND AND USE_CUDA)
  list(APPEND ADDITIONAL_CMAKE_ARGS
    -DRobartsVTK_USE_CUDA:BOOL=ON
    )
else()
  list(APPEND ADDITIONAL_CMAKE_ARGS
    -DRobartsVTK_USE_CUDA:BOOL=OFF
    )
endif()

if(NOT DEFINED ${proj}_DIR AND NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  if(NOT DEFINED git_protocol)
    set(git_protocol "git")
  endif()
  
  if(NOT WIN32)
    set(ep_common_cxx_flags "${ep_common_cxx_flags} -std=c++11")
  endif()

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
    BINARY_DIR ${proj}-build
    #--Download step--------------
    GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/VASST/RobartsVTK.git
    GIT_TAG master
    #--Configure step-------------
    CMAKE_CACHE_ARGS
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
      -DBUILD_TESTING:BOOL=OFF
      -DRobartsVTK_USE_ITK:BOOL=ON
      -DVTK_DIR:PATH=${VTK_DIR}
      -DITK_DIR:PATH=${ITK_DIR}
      -DRobartsVTK_USE_PLUS:BOOL=OFF
      -DRobartsVTK_USE_REGISTRATION:BOOL=ON
      -DRobartsVTK_USE_COMMON:BOOL=ON
      -DRobartsVTK_USE_CUDA:BOOL=${CUDA_FOUND}
      -DRobartsVTK_USE_CUDA_VISUALIZATION:BOOL=ON # Controlled by RobartsVTK_USE_CUDA
      -DRobartsVTK_USE_CUDA_ANALYTICS:BOOL=ON # Controlled by RobartsVTK_USE_CUDA
      -DRobartsVTK_BUILD_APPS:BOOL=OFF
      -DRobartsVTK_WRAP_PYTHON:BOOL=ON
      -DVTK_INSTALL_PYTHON_MODULE_DIR:PATH=${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}
      -DBUILD_SHARED_LIBS:BOOL=ON 
      -DPYTHON_INCLUDE_DIR:STRING=${PYTHON_INCLUDE_DIR}
      -DPYTHON_LIBRARY:FILEPATH=${PYTHON_LIBRARY}
      -DPYTHON_EXECUTABLE:FILEPATH=${PYTHON_EXECUTABLE}
      ${ADDITIONAL_CMAKE_ARGS}
    #--Install step-----------------
    INSTALL_COMMAND "" # Do not install
    DEPENDS
      ${${proj}_DEPENDS}
    )
  set(${proj}_DIR ${CMAKE_BINARY_DIR}/${proj}-build)

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDS})
endif()

mark_as_superbuild(${proj}_DIR:PATH)