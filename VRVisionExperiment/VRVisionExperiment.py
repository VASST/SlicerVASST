import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy as np
import logging

# VRVisionExperiment
class VRVisionExperiment(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VR Vision Experiment"
    self.parent.categories = ["Research"]
    self.parent.dependencies = ["VirtualReality"]
    self.parent.contributors = ["Adam Rankin (Robarts Research), Sara Pac (Western University)"]
    self.parent.helpText = """This module performs vision experiments involving a touching task in VR"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """This module was developed through funding provided by the BrainsCAN initiative."""

# VRVisionExperimentWidget
class VRVisionExperimentWidget(ScriptedLoadableModuleWidget):
  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

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
    self.rootCubeTransformNode = None
    self.sphereTransformNode = None

    self.isInit = False
    self.isStarted = False
    self.initButton = None
    self.startButton = None
    self.captureButton = None
    self.saveButton = None
    self.resetButton = None
    self.participantIdLineEdit = None
    self.inputsCollapsibleButton = None
    self.trialNumberSpinBox = None
    self.conditionComboBox = None

    self.sequenceGroupBox = None
    self.motionSequenceButton = None
    self.nomotionSequenceButton = None
    self.replaySequenceButton = None

    self.resultGroupBox = None
    self.resultLabel = None

    self.motionSequence = []
    self.nomotionSequence = []
    self.replaySequence = []

    self.capturedSequence = []
    self.currentReferenceSequence = []
    self.currentIndex = 0

    self.homePosition = []

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.layout.setContentsMargins(6,6,6,6)

    # Init Button
    self.initButton = qt.QPushButton("Initialize/Reset")
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
    self.participantIdLineEdit.text = "0"
    formLayout.addRow("Participant ID:", self.participantIdLineEdit)
    self.conditionComboBox = qt.QComboBox()
    self.conditionComboBox.addItem("Motion")
    self.conditionComboBox.addItem("No motion")
    self.conditionComboBox.addItem("Replay")
    formLayout.addRow("Condition:", self.conditionComboBox)
    self.trialNumberSpinBox = qt.QSpinBox()
    formLayout.addRow("Trial Number:", self.trialNumberSpinBox)
    self.trialNumberSpinBox.setValue(1)
    self.trialNumberSpinBox.setMinimum(1)

    self.sequenceGroupBox = qt.QGroupBox("Target Sequences")
    layout = qt.QHBoxLayout(self.sequenceGroupBox)
    self.motionSequenceButton = qt.QPushButton("Load Motion")
    layout.addWidget(self.motionSequenceButton)
    self.nomotionSequenceButton = qt.QPushButton("Load No-motion")
    layout.addWidget(self.nomotionSequenceButton)
    self.replaySequenceButton = qt.QPushButton("Load Replay")
    layout.addWidget(self.replaySequenceButton)
    formLayout.addRow(self.sequenceGroupBox)

    # capture, save buttons
    widget = qt.QWidget()
    layout = qt.QHBoxLayout(widget)
    layout.setContentsMargins(0,0,0,0)
    self.startButton = qt.QPushButton("Start")
    self.startButton.toolTip = "Start the capture sequence."
    self.startButton.enabled = False
    self.captureButton = qt.QPushButton("Capture")
    self.captureButton.toolTip = "Capture a data point."
    self.captureButton.enabled = False
    self.saveButton = qt.QPushButton("Save and reset")
    self.saveButton.toolTip = "Save the current data set to file."
    self.saveButton.enabled = False
    self.resetButton = qt.QPushButton("Reset")
    self.resetButton.toolTip = "Reset the capture."
    self.resetButton.enabled = False
    layout.addWidget(self.startButton)
    layout.addWidget(self.captureButton)
    layout.addWidget(self.saveButton)
    layout.addWidget(self.resetButton)
    self.layout.addWidget(widget)

    self.resultGroupBox = qt.QGroupBox("Results")
    layout = qt.QHBoxLayout(self.resultGroupBox)
    self.resultLabel = qt.QLabel("")
    layout.addWidget(self.resultLabel)
    self.layout.addWidget(self.resultGroupBox)

    # connections
    self.initButton.connect('clicked(bool)', self.onInitButton)
    self.startButton.connect('clicked(bool)', self.onStartButton)
    self.saveButton.connect('clicked(bool)', self.onSaveButton)
    self.resetButton.connect('clicked(bool)', self.onResetButton)
    self.captureButton.connect('clicked(bool)', self.onCaptureButton)
    self.motionSequenceButton.connect('clicked(bool)', self.onLoadMotionButton)
    self.nomotionSequenceButton.connect('clicked(bool)', self.onLoadNoMotionButton)
    self.replaySequenceButton.connect('clicked(bool)', self.onLoadReplayButton)
    self.conditionComboBox.connect('currentIndexChanged(int)', self.onConditionIndexChanged)

    self.onConditionIndexChanged(0)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    self.initButton.disconnect('clicked(bool)', self.onInitButton)
    self.startButton.disconnect('clicked(bool)', self.onStartButton)
    self.saveButton.disconnect('clicked(bool)', self.onSaveButton)
    self.resetButton.disconnect('clicked(bool)', self.onResetButton)
    self.captureButton.disconnect('clicked(bool)', self.onCaptureButton)
    self.motionSequenceButton.disconnect('clicked(bool)', self.onLoadMotionButton)
    self.nomotionSequenceButton.disconnect('clicked(bool)', self.onLoadNoMotionButton)
    self.replaySequenceButton.disconnect('clicked(bool)', self.onLoadReplayButton)
    self.conditionComboBox.disconnect('currentIndexChanged(int)', self.onConditionIndexChanged)

  def onResetButton(self):
    self.capturedSequence = []
    self.updateUI()
    self.isStarted = False
    self.updateUI()
    self.sphereModel.GetDisplayNode().SetVisibility(False)
    self.resultLabel.text = "Capture cleared."

  def onSaveButton(self):
    # Build filename string
    proto_filename = "participant" + self.participantIdLineEdit.text + "_trial" + str(self.trialNumberSpinBox.value) + "_" + self.conditionComboBox.currentText + ".txt"
    filename = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), "Save sequence", proto_filename)
    if filename == '':
      self.resultLabel.text = "File not saved."
      return()

    with open(filename, 'w') as f:
      f.write("#cap_x, cap_y, cap_z\n")
      for cap in self.capturedSequence:
        f.write(str(cap[0]) + "," + str(cap[1]) + "," + str(cap[2]) + "\n")

    self.onResetButton()
    self.resultLabel.text = "File saved. Capture cleared."

  def onInitButton(self):
    self.isInit = False

    # Reset module without using developer mode
    slicer.mrmlScene.Clear()
    self.currentReferenceSequence = []
    self.capturedSequence = []

    # Ensure VR module has been created
    if slicer.modules.virtualreality is None:
      self.error("Unable to load VR module, has it been installed?")
      return()
    widget = slicer.modules.virtualreality.widgetRepresentation()
    if widget is None:
      self.error("Unable to create VR widget, module is not functioning as expect, troubleshoot VR in Slicer.")
      return()

    l = slicer.modules.virtualreality.logic()
    l.SetAndObserveMRMLScene(slicer.mrmlScene)
    l.SetVirtualRealityConnected(1)
    l.SetVirtualRealityActive(1)

    # Set layout to 3D only
    slicer.app.layoutManager().setLayout(4)
    # Reset 3D view to A facing P, TODO: reset to a known view position as this method does not always return to exact same position (always same direction though)
    slicer.app.layoutManager().threeDWidget(0).threeDController().lookFromAxis(ctk.ctkAxesWidget.Anterior)
    # Ensure all connections are correct
    if hasattr(widget, 'viewWidget'):
      self.vrView = widget.viewWidget()
    else:
      for i in slicer.app.topLevelWidgets():
        if i.name == "VirtualRealityWidget":
          self.vrView = i
          break
    if self.vrView is None:
      self.error("VR in Slicer is not available. Is headset plugged in, SteamVR running?")
      return()
    if self.vrView.mrmlVirtualRealityViewNode() is None:
      self.error("VR is not running in Slicer. Please click the VR button in the quickbar, or use the VR module to start VR.")
      return ()
    self.vrView.mrmlVirtualRealityViewNode().SetAndObserveReferenceViewNode(slicer.app.layoutManager().threeDWidget(0).mrmlViewNode())
    # Reset VR view to ref view
    self.vrView.updateViewFromReferenceViewCamera()
    # Ensure transforms are updated for camera and VR controllers
    self.vrView.mrmlVirtualRealityViewNode().SetControllerTransformsUpdate(True)
    self.vrView.mrmlVirtualRealityViewNode().SetHMDTransformUpdate(True)
    # Hide trackers and controllers
    self.vrView.mrmlVirtualRealityViewNode().SetControllerModelsVisible(False)
    self.vrView.mrmlVirtualRealityViewNode().SetTrackerReferenceModelsVisible(False)
    # Set the RAStoPhysical magnification to 1x
    self.vrView.mrmlVirtualRealityViewNode().SetMagnification(1.0)
    # Disable interactor
    self.vrView.renderWindow().SetInteractor(None)

    # Give Slicer some time to update all the various things we just changed
    qt.QTimer.singleShot(5, self.onFinishInitButton)

  def onFinishInitButton(self):
    # Create sphere and parent transform, hide for now
    filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/sphere.stl')
    success, self.sphereModel = slicer.util.loadModel(filename, True)
    if not success:
      self.error("Unable to load sphere model. Is module installed correctly?")
      return()
    self.sphereModel.GetDisplayNode().SetVisibility(False)
    self.sphereTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.sphereTransformNode)
    self.sphereTransformNode.SetName("SpherePose")
    self.sphereModel.SetAndObserveTransformNodeID(self.sphereTransformNode.GetID())

    # Create needle model and parent transform
    filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/needle.stl')
    success, self.needleModelNode = slicer.util.loadModel(filename, True)
    if not success:
      self.error("Unable to load needle model. Is module installed correctly?")
      return()
    controllerNode = self.vrView.mrmlVirtualRealityViewNode().GetRightControllerTransformNode()
    if controllerNode is None or controllerNode.GetAttribute("VirtualReality.ControllerActive") == '0':
      controllerNode = self.vrView.mrmlVirtualRealityViewNode().GetLeftControllerTransformNode()
      if controllerNode is None or controllerNode.GetAttribute("VirtualReality.ControllerActive") == '0':
        self.error("Unable to find controller transform, is one of the controllers turned on and detected?")
        return()
    self.needleModelNode.SetAndObserveTransformNodeID(controllerNode.GetID())

    # Create room
    # Create parent transform to easily translate the room to the user's current position
    self.rootCubeTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.rootCubeTransformNode)
    self.rootCubeTransformNode.SetName("CubeRoot")
    for name in ['Back', 'Front', 'Left', 'Right', 'Roof', 'Floor']:
      filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Models/CubeModel.vtk')
      success, modelNode = slicer.util.loadModel(filename, True)
      if not success:
        self.error("Unable to load cube model, ensure module is correctly installed.")
        return()
      modelNode.SetName('CubeModel'+name)
      setattr(self, 'cubeModel' + name, modelNode)
      filename = os.path.join(os.path.dirname(slicer.modules.vrvisionexperiment.path), 'Resources/Slicer/Scene/ScaleCube'+name+'.h5')
      success, transformNode = slicer.util.loadTransform(filename, True)
      if not success:
        self.error("Unable to load cube transform, ensure module is correctly installed.")
        return()
      setattr(self, 'cubeTransform' + name, transformNode)
      modelNode.SetAndObserveTransformNodeID(transformNode.GetID())
      transformNode.SetAndObserveTransformNodeID(self.rootCubeTransformNode.GetID())

    # Update cube root position so that the room is centered about the headset, 0.6m below the headset
    cubeMat = vtk.vtkMatrix4x4()
    self.rootCubeTransformNode.GetMatrixTransformToParent(cubeMat)
    hmdMat = vtk.vtkMatrix4x4()
    self.vrView.mrmlVirtualRealityViewNode().GetHMDTransformNode().GetMatrixTransformToParent(hmdMat)
    cubeMat.SetElement(1, 3, hmdMat.GetElement(1,3))
    cubeMat.SetElement(2, 3, 600) #600mm = 0.6m
    self.rootCubeTransformNode.SetMatrixTransformToParent(cubeMat)
    self.homePosition = [hmdMat.GetElement(0,3), hmdMat.GetElement(1,3), hmdMat.GetElement(2,3)]

    self.isInit = True
    self.updateUI()
    self.resultLabel.text = "Reset."

  def updateUI(self):
    isEnabled = len(self.motionSequence) > 0 and len(self.nomotionSequence) > 0 and len(self.replaySequence) > 0 and self.isInit
    self.captureButton.enabled = isEnabled and len(self.capturedSequence) < len(self.currentReferenceSequence) and self.isStarted
    self.startButton.enabled = isEnabled
    self.resetButton.enabled = len(self.capturedSequence) > 0
    self.inputsCollapsibleButton.enabled = self.isInit
    self.saveButton.enabled = len(self.capturedSequence) > 0

  def onConditionIndexChanged(self, newIndex):
    self.currentReferenceSequence = []
    # Update the current sequence with the desired sequence
    if self.conditionComboBox.itemText(newIndex) == "Motion":
      self.currentReferenceSequence = self.motionSequence
    if self.conditionComboBox.itemText(newIndex) == "No motion":
      self.currentReferenceSequence = self.nomotionSequence
    if self.conditionComboBox.itemText(newIndex) == "Replay":
      self.currentReferenceSequence = self.replaySequence
    self.onSequenceChanged()

  def onStartButton(self):
    # Show sphere and move to first position in currentReferenceSequence position, relative to "home" position
    self.sphereModel.GetDisplayNode().SetVisibility(1)
    self.currentIndex = 0
    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0, 3, self.currentReferenceSequence[self.currentIndex][0])
    mat.SetElement(1, 3, self.currentReferenceSequence[self.currentIndex][1])
    mat.SetElement(2, 3, self.currentReferenceSequence[self.currentIndex][2])
    self.sphereTransformNode.SetMatrixTransformToParent(mat)
    self.isStarted = True
    self.updateUI()

  def onCaptureButton(self):
    controllerNode = slicer.mrmlScene.GetNodeByID(self.needleModelNode.GetTransformNodeID())
    mat = vtk.vtkMatrix4x4()
    controllerNode.GetMatrixTransformToParent(mat)
    x = mat.GetElement(0, 3)
    y = mat.GetElement(1, 3)
    z = mat.GetElement(2, 3)
    self.capturedSequence.append([x,y,z])
    self.currentIndex = self.currentIndex + 1
    self.onSequenceChanged()

    if self.currentIndex == len(self.currentReferenceSequence):
      return()

    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0, 3, self.currentReferenceSequence[self.currentIndex][0])
    mat.SetElement(1, 3, self.currentReferenceSequence[self.currentIndex][1])
    mat.SetElement(2, 3, self.currentReferenceSequence[self.currentIndex][2])
    self.sphereTransformNode.SetMatrixTransformToParent(mat)

  def onSequenceChanged(self):
    self.updateUI()
    self.resultLabel.text = str(len(self.capturedSequence)) + " points collected."

  def error(self, text):
    logging.error(text)
    self.resultLabel.text = text

  def loadSequence(self):
    filename = qt.QFileDialog.getOpenFileName()
    if filename == '':
      return []
    with open(filename) as f:
      content = f.readlines()
    content = [x.strip() for x in content]
    sequence = []
    for line in content:
      items = line.split(',')
      if len(items) != 3:
        self.error("Invalid line in sequence file: " + filename)
        return []
      sequence.append([float(items[0]), float(items[1]), float(items[2])])
    return sequence

  def onLoadMotionButton(self):
    self.motionSequence = []
    self.motionSequence = self.loadSequence()
    if len(self.motionSequence) == 0:
      self.error("Unable to load sequence.")
      return()
    else:
      self.resultLabel.text = "Motion sequence loaded " + str(len(self.motionSequence)) + " points."
    self.onConditionIndexChanged(self.conditionComboBox.currentIndex)

  def onLoadNoMotionButton(self):
    self.nomotionSequence = []
    self.nomotionSequence = self.loadSequence()
    if len(self.nomotionSequence) == 0:
      self.error("Unable to load sequence.")
      return()
    else:
      self.resultLabel.text = "No-motion sequence loaded " + str(len(self.motionSequence)) + " points."
    self.onConditionIndexChanged(self.conditionComboBox.currentIndex)

  def onLoadReplayButton(self):
    self.replaySequence = []
    self.replaySequence = self.loadSequence()
    if len(self.replaySequence) == 0:
      self.error("Unable to load sequence.")
      return()
    else:
      self.resultLabel.text = "Replay sequence loaded " + str(len(self.motionSequence)) + " points."
    self.onConditionIndexChanged(self.conditionComboBox.currentIndex)

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
