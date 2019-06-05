project(vtkSlicer${MODULE_NAME}ModuleLogic)

#-----------------------------------------------------------------------------
find_package(VASSTAlgorithms REQUIRED NO_MODULE)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "VTK_SLICER_${MODULE_NAME_UPPER}_MODULE_LOGIC_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  ${vtkSlicerPointToLineRegistrationModuleLogic_INCLUDE_DIRS}
  ${vtkSlicerVideoCamerasModuleMRML_INCLUDE_DIRS}
  )

set(${KIT}_SRCS
  vtkSlicer${MODULE_NAME}Logic.cxx
  vtkSlicer${MODULE_NAME}Logic.h
  )

set(${KIT}_TARGET_LIBRARIES
  opencv_imgproc
  opencv_videoio
  vtkSlicerPointToLineRegistrationModuleLogic
  vtkSlicerVideoCamerasModuleMRML
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleLogic(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  )
