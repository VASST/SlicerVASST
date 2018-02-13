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

find_package(CUDA QUIET)
if(CUDA_FOUND)

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
    GIT_REPOSITORY https://github.com/VASST/RobartsVTK.git
    GIT_TAG master
    #--Configure step-------------
    CMAKE_CACHE_ARGS
      -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
      -DBUILD_TESTING:BOOL=OFF
      -DRobartsVTK_USE_QT:BOOL=ON
      -DRobartsVTK_USE_ITK:BOOL=ON
      -DVTK_DIR:PATH=${VTK_DIR}
      -DITK_DIR:PATH=${ITK_DIR}
      -DRobartsVTK_USE_PLUS:BOOL=OFF
      -DRobartsVTK_USE_REGISTRATION:BOOL=ON
      -DRobartsVTK_USE_COMMON:BOOL=ON
      -DRobartsVTK_USE_CUDA:BOOL=${CUDA_FOUND}
      -DRobartsVTK_USE_CUDA_VISUALIZATION:BOOL=${CUDA_FOUND}
      -DRobartsVTK_USE_CUDA_ANALYTICS:BOOL=${CUDA_FOUND}
      -DRobartsVTK_BUILD_APPS:BOOL=OFF
      -DRobartsVTK_WRAP_PYTHON:BOOL=ON
      -DVTK_INSTALL_PYTHON_MODULE_DIR:PATH=${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}
      -DBUILD_SHARED_LIBS:BOOL=ON 
      -DPYTHON_INCLUDE_DIR:STRING=${PYTHON_INCLUDE_DIR}
      -DPYTHON_LIBRARY:FILEPATH=${PYTHON_LIBRARY}
      -DPYTHON_EXECUTABLE:FILEPATH=${PYTHON_EXECUTABLE}
      -DQT_QMAKE_EXECUTABLE:FILEPATH=${QT_QMAKE_EXECUTABLE}
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