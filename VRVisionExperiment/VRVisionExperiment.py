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
    self.vrView = None
    self.vrViewNode = None
    self.logic = VRVisionExperimentLogic()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/sphere.stl')
    success, self.sphereModel = slicer.util.loadModel(filename, True)

    # Parameters Area
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    # Init Button
    self.initButton = qt.QPushButton("Initialize")
    self.initButton.toolTip = "Reset everything."
    self.layout.addWidget(self.initButton)

    # Apply button
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    self.layout.addWidget(self.applyButton)

    # connections
    self.initButton.connect('clicked(bool)', self.onInitButton)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onInitButton(self):
    # Ensure VR module has been created
    if slicer.modules.virtualreality is None:
      logging.error("Unable to load VR module, has it been installed?")
      return()
    widget = slicer.modules.virtualreality.widgetRepresentation()

    # Set layout to 3D only
    slicer.app.layoutManager().setLayout(4)
    # Reset 3D view to A facing P
    slicer.app.layoutManager().threeDWidget(0).threeDController().lookFromAxis(ctk.ctkAxisWidget.Anterior)
    # Ensure all connections are correct
    self.vrView = widget.viewWidget()
    self.vrView.mrmlVirtualRealityViewNode().SetAndObserveReferenceViewNode(slicer.app.layoutManager().threeDWidget(0).mrmlViewNode())
    # Reset VR view to ref view
    self.vrView.updateViewFromReferenceViewCamera()

    # Create room

  def onApplyButton(self):
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
