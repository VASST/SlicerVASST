#-----------------------------------------------------------------------------
set(MODULE_NAME VRVisionExperiment)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Models/CubeModel.vtk
  Resources/Models/needle.stl
  Resources/Models/sphere.stl
  Resources/Slicer/Scene/motion.txt
  Resources/Slicer/Scene/nomotion.txt
  Resources/Slicer/Scene/replay.txt
  Resources/Slicer/Scene/ScaleCubeBack.h5
  Resources/Slicer/Scene/ScaleCubeFront.h5
  Resources/Slicer/Scene/ScaleCubeLeft.h5
  Resources/Slicer/Scene/ScaleCubeRight.h5
  Resources/Slicer/Scene/ScaleCubeRoof.h5
  Resources/Slicer/Scene/ScaleCubeFloor.h5
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
