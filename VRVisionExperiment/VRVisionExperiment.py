import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# VRVisionExperiment
class VRVisionExperiment(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VR Vision Experiment"
    self.parent.categories = ["Research"]
    self.parent.dependencies = ["virtualreality"]
    self.parent.contributors = ["Adam Rankin (Robarts Research), Sara Pac (Western University)"]
    self.parent.helpText = """This module performs vision experiments involving a touching task in VR"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """This module was developed through funding provided by the BrainsCAN initiative."""

# VRVisionExperimentWidget
class VRVisionExperimentWidget(ScriptedLoadableModuleWidget):
  def __init__(self):
    self.sphereModel = None
    self.needleModelNode = None

    self.vrView = None
    self.vrViewNode = None
    self.logic = VRVisionExperimentLogic()

    self.cubeModelBack = None
    self.cubeModelFront = None
    self.cubeModelLeft = None
    self.cubeModelRight = None
    self.cubeModelRoof = None
    self.cubeModelFloor = None
    self.transformNodeBack = None
    self.transformNodeFront = None
    self.transformNodeLeft = None
    self.transformNodeRight = None
    self.transformNodeRoof = None
    self.transformNodeFloor = None

    self.initButton = None
    self.captureButton = None
    self.saveButton = None
    self.participantIdLineEdit = None
    self.inputsCollapsibleButton = None
    self.trialNumberSpinBox = None
    self.conditionLineEdit = None

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Init Button
    self.initButton = qt.QPushButton("Initialize")
    self.initButton.toolTip = "Reset everything."
    self.layout.addWidget(self.initButton)

    # Inputs Area
    self.inputsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.inputsCollapsibleButton.text = "Inputs"
    self.inputsCollapsibleButton.enabled = False
    self.layout.addWidget(self.inputsCollapsibleButton)

    # Layout within the collapsible button
    formLayout = qt.QFormLayout(self.inputsCollapsibleButton)

    # Participant information (for save file name generation)
    self.participantIdLineEdit = qt.QLineEdit()
    formLayout.addRow("Participant ID:", self.participantIdLineEdit)
    self.conditionLineEdit = qt.QLineEdit()
    formLayout.addRow("Condition:", self.conditionLineEdit)
    self.trialNumberSpinBox = qt.QSpinBox()
    formLayout.addRow("Trial Number:", self.trialNumberSpinBox)
    self.trialNumberSpinBox.SetValue(1)
    self.trialNumberSpinBox.setMinimum(1)
    self.saveButton = qt.QPushButton("Save")
    self.saveButton.toolTip = "Save the current data set to file."
    self.saveButton.enabled = False
    formLayout.addRow(self.saveButton)

    # Apply button
    self.captureButton = qt.QPushButton("Capture")
    self.captureButton.toolTip = "Capture a data point."
    self.captureButton.enabled = False
    self.layout.addWidget(self.captureButton)

    # connections
    self.initButton.connect('clicked(bool)', self.onInitButton)
    self.saveButton.connect('clicked(bool)', self.onSaveButton)
    self.captureButton.connect('clicked(bool)', self.onCaptureButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    self.initButton.disconnect('clicked(bool)', self.onInitButton)
    self.saveButton.disconnect('clicked(bool)', self.onSaveButton)
    self.captureButton.disconnect('clicked(bool)', self.onCaptureButton)

  def onSaveButton(self):
    self.saveButton.enabled = False

  def onInitButton(self):
    # Ensure VR module has been created
    if slicer.modules.virtualreality is None:
      logging.error("Unable to load VR module, has it been installed?")
      return()
    widget = slicer.modules.virtualreality.widgetRepresentation()
    if widget is None:
      logging.error("Unable to create VR widget, module is not functioning as expect, troubleshoot VR in Slicer.")
      return ()

    # Set layout to 3D only
    slicer.app.layoutManager().setLayout(4)
    # Reset 3D view to A facing P, TODO: reset to a known view position as this method does not always return to exact same position (always same direction though)
    slicer.app.layoutManager().threeDWidget(0).threeDController().lookFromAxis(ctk.ctkAxisWidget.Anterior)
    # Ensure all connections are correct
    self.vrView = widget.viewWidget()
    if self.vrView is None:
      logging.error("VR in Slicer is not available. Is headset plugged in, SteamVR running?")
      return()
    self.vrView.mrmlVirtualRealityViewNode().SetAndObserveReferenceViewNode(slicer.app.layoutManager().threeDWidget(0).mrmlViewNode())
    # Reset VR view to ref view
    self.vrView.updateViewFromReferenceViewCamera()
    # Ensure transforms are updated for VR controllers
    self.vrView.mrmlVirtualRealityViewNode().SetControllerTransformsUpdate(True)
    # Hide controllers
    self.vrView.SetControllerModelsVisible(False)

    # Create sphere, hide for now
    filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/sphere.stl')
    success, self.sphereModel = slicer.util.loadModel(filename, True)
    if not success:
      logging.error("Unable to load sphere model. Is module installed correctly?")
      return()
    self.sphereModel.GetDisplayNode().SetVisibility(False)

    # Create needle model and parent transform
    filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/needle.stl')
    success, self.needleModelNode = slicer.util.loadModel(filename, True)
    controllerNode = self.vrView.mrmlVirtualRealityViewNode().GetRightControllerTransformNode()
    if controllerNode is None:
      controllerNode = self.vrView.mrmlVirtualRealityViewNode().GetLeftControllerTransformNode()
      if controllerNode is None:
        logging.error("Unable to find controller transform, is one of the controllers turned on and detected?")
        return()
    self.needleModelNode.SetAndObserveTransformNodeID(controllerNode.GetID())

    # Create room
    for name in ['Back', 'Front', 'Left', 'Right', 'Roof', 'Floor']:
      filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/CubeModel.vtk')
      success, modelNode = slicer.util.loadModel(filename, True)
      if not success:
        logging.error("Unable to load cube model, ensure module is correctly installed.")
        return()
      modelNode.SetName('CubeModel'+name)
      setattr(self, 'cubeModel' + name, modelNode)
      filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Slicer/ScaleCube'+name+'.vtk')
      success, transformNode = slicer.util.loadTransform(filename, True)
      if not success:
        logging.error("Unable to load cube transform, ensure module is correctly installed.")
        return()
      setattr(self, 'cubeTransform' + name, transformNode)
      modelNode.SetAndObserveTransformNodeID(transformNode.GetID())

    self.captureButton.enabled = True
    self.inputsCollapsibleButton.enabled = True

  def onCaptureButton(self):
    self.saveButton.enabled = True
    self.logic.run()

# VRVisionExperimentLogic
class VRVisionExperimentLogic(ScriptedLoadableModuleLogic):
  def run(self):
    return True

# VRVisionExperimentTest
class VRVisionExperimentTest(ScriptedLoadableModuleTest):
  def setUp(self):
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    self.setUp()
    self.test_VRVisionExperiment1()

  def test_VRVisionExperiment1(self):
    self.delayDisplay("Starting the test")
    self.delayDisplay('Test passed!')
