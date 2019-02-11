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

    self.sphereModelNode = None
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
    self.previousButton = None
    self.nextButton = None
    self.captureButton = None
    self.saveButton = None
    self.resetButton = None

    self.participantIdLineEdit = None
    self.inputsGroupBox = None
    self.trialNumberSpinBox = None
    self.conditionComboBox = None

    self.calibrateGroupBox = None
    self.floorButton = None
    self.faceButton = None

    self.sequenceGroupBox = None
    self.motionSequenceButton = None
    self.nomotionSequenceButton = None
    self.replaySequenceButton = None

    self.controlGroupBox = None
    self.showControllerCheckBox = None
    self.showNeedleCheckBox = None
    self.showSphereCheckBox = None

    self.resultGroupBox = None
    self.resultLabel = None

    self.motionSequence = []
    self.nomotionSequence = []
    self.replaySequence = []

    self.capturedSequence = []
    self.currentReferenceSequence = []
    self.currentIndex = 0

    self.floorHeight = 0.0
    self.facePosition = []

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.layout.setContentsMargins(6,6,6,6)

    # Init Button
    self.initButton = qt.QPushButton("Initialize")
    self.initButton.toolTip = "Initialize VR system, controllers, and room."
    self.layout.addWidget(self.initButton)

    # Calibration buttons
    self.calibrateGroupBox = qt.QGroupBox("Calibrations")
    self.calibrateGroupBox.enabled = False
    layout = qt.QHBoxLayout(self.calibrateGroupBox)
    layout.setContentsMargins(0, 0, 0, 0)
    self.floorButton = qt.QPushButton("Floor")
    self.floorButton.toolTip = "Calibrate the floor."
    self.faceButton = qt.QPushButton("Face")
    self.faceButton.toolTip = "Calibrate the face."
    layout.addWidget(self.floorButton)
    layout.addWidget(self.faceButton)
    self.layout.addWidget(self.calibrateGroupBox)

    # Inputs Area
    self.inputsGroupBox = qt.QGroupBox("Inputs")
    self.inputsGroupBox.enabled = False
    layout = qt.QFormLayout(self.inputsGroupBox)
    layout.setContentsMargins(0,0,0,0)
    self.participantIdLineEdit = qt.QLineEdit()
    self.participantIdLineEdit.text = "000"
    self.conditionComboBox = qt.QComboBox()
    self.conditionComboBox.addItem("Motion")
    self.conditionComboBox.addItem("No motion")
    self.conditionComboBox.addItem("Replay")
    self.trialNumberSpinBox = qt.QSpinBox()
    self.trialNumberSpinBox.setValue(1)
    self.trialNumberSpinBox.setMinimum(1)
    layout.addRow("Participant ID:", self.participantIdLineEdit)
    layout.addRow("Condition:", self.conditionComboBox)
    layout.addRow("Trial Number:", self.trialNumberSpinBox)
    self.layout.addWidget(self.inputsGroupBox)

    # Sequences loading
    self.sequenceGroupBox = qt.QGroupBox("Target Sequences")
    layout = qt.QHBoxLayout(self.sequenceGroupBox)
    self.motionSequenceButton = qt.QPushButton("Load Motion")
    self.nomotionSequenceButton = qt.QPushButton("Load No-motion")
    self.replaySequenceButton = qt.QPushButton("Load Replay")
    layout.addWidget(self.motionSequenceButton)
    layout.addWidget(self.nomotionSequenceButton)
    layout.addWidget(self.replaySequenceButton)
    self.layout.addWidget(self.sequenceGroupBox)

    # Control UI
    self.controlGroupBox = qt.QGroupBox("Controls")
    layout = qt.QFormLayout(self.controlGroupBox)
    self.showControllerCheckBox = qt.QCheckBox()
    self.showNeedleCheckBox = qt.QCheckBox()
    self.showSphereCheckBox = qt.QCheckBox()
    layout.addRow("Show controller: ", self.showControllerCheckBox)
    layout.addRow("Show needle: ", self.showNeedleCheckBox)
    layout.addRow("Show sphere: ", self.showSphereCheckBox)
    self.layout.addWidget(self.controlGroupBox)

    # Capture related buttons
    widget = qt.QWidget()
    layout = qt.QHBoxLayout(widget)
    layout.setContentsMargins(0,0,0,0)
    self.startButton = qt.QPushButton("Start")
    self.startButton.toolTip = "Start the capture sequence."
    self.startButton.enabled = False
    self.previousButton = qt.QPushButton("Previous")
    self.previousButton.toolTip = "Capture previous point."
    self.previousButton.enabled = False
    self.nextButton = qt.QPushButton("Next")
    self.nextButton.toolTip = "Capture next point."
    self.nextButton.enabled = False
    self.captureButton = qt.QPushButton("Capture")
    self.captureButton.toolTip = "Capture a data point."
    self.captureButton.enabled = False
    self.saveButton = qt.QPushButton("Save")
    self.saveButton.toolTip = "Save the current data set to file."
    self.saveButton.enabled = False
    self.resetButton = qt.QPushButton("Reset")
    self.resetButton.toolTip = "Reset the capture."
    self.resetButton.enabled = False
    layout.addWidget(self.startButton)
    layout.addWidget(self.previousButton)
    layout.addWidget(self.nextButton)
    layout.addWidget(self.captureButton)
    layout.addWidget(self.saveButton)
    layout.addWidget(self.resetButton)
    self.layout.addWidget(widget)

    # Results box
    self.resultGroupBox = qt.QGroupBox("Results")
    layout = qt.QHBoxLayout(self.resultGroupBox)
    self.resultLabel = qt.QLabel("")
    layout.addWidget(self.resultLabel)
    self.layout.addWidget(self.resultGroupBox)

    self.doConnect()

    # Add vertical spacer
    self.layout.addStretch(1)

  def doConnect(self):
    # Connections
    self.initButton.connect('clicked(bool)', self.onInitButton)

    self.startButton.connect('clicked(bool)', self.onStartButton)
    self.previousButton.connect('clicked(bool)', self.onPreviousButton)
    self.nextButton.connect('clicked(bool)', self.onNextButton)
    self.saveButton.connect('clicked(bool)', self.onSaveButton)
    self.resetButton.connect('clicked(bool)', self.onResetButton)
    self.captureButton.connect('clicked(bool)', self.onCaptureButton)

    self.showControllerCheckBox.connect('stateChanged(int)', self.onShowControllerCheckBox)
    self.showNeedleCheckBox.connect('stateChanged(int)', self.onShowNeedleCheckBox)
    self.showSphereCheckBox.connect('stateChanged(int)', self.onShowSphereCheckBox)

    self.floorButton.connect('clicked(bool)', self.onFloorButton)
    self.faceButton.connect('clicked(bool)', self.onFaceButton)

    self.motionSequenceButton.connect('clicked(bool)', self.onLoadMotionButton)
    self.nomotionSequenceButton.connect('clicked(bool)', self.onLoadNoMotionButton)
    self.replaySequenceButton.connect('clicked(bool)', self.onLoadReplayButton)

  def safeDisconnect(self, obj, functionName, function):
    if obj is not None and hasattr(obj, "disconnect"):
      obj.disconnect(functionName, function)

  def cleanup(self):
    self.safeDisconnect(self.initButton, 'clicked(bool)', self.onInitButton)

    self.safeDisconnect(self.startButton, 'clicked(bool)', self.onStartButton)
    self.safeDisconnect(self.previousButton, 'clicked(bool)', self.onPreviousButton)
    self.safeDisconnect(self.nextButton, 'clicked(bool)', self.onNextButton)
    self.safeDisconnect(self.saveButton, 'clicked(bool)', self.onSaveButton)
    self.safeDisconnect(self.resetButton, 'clicked(bool)', self.onResetButton)
    self.safeDisconnect(self.captureButton, 'clicked(bool)', self.onCaptureButton)

    self.safeDisconnect(self.showControllerCheckBox, 'stateChanged(int)', self.onShowControllerCheckBox)
    self.safeDisconnect(self.showNeedleCheckBox, 'stateChanged(int)', self.onShowNeedleCheckBox)
    self.safeDisconnect(self.showSphereCheckBox, 'stateChanged(int)', self.onShowSphereCheckBox)

    self.safeDisconnect(self.floorButton, 'clicked(bool)', self.onFloorButton)
    self.safeDisconnect(self.faceButton, 'clicked(bool)', self.onFaceButton)

    self.safeDisconnect(self.motionSequenceButton, 'clicked(bool)', self.onLoadMotionButton)
    self.safeDisconnect(self.nomotionSequenceButton, 'clicked(bool)', self.onLoadNoMotionButton)
    self.safeDisconnect(self.replaySequenceButton, 'clicked(bool)', self.onLoadReplayButton)

  def onFloorButton(self):
    # Record current Y position of controller as floor
    controllerNode = slicer.mrmlScene.GetNodeByID(self.needleModelNode.GetTransformNodeID())
    mat = vtk.vtkMatrix4x4()
    controllerNode.GetMatrixTransformToParent(mat)
    self.floorHeight = mat.GetElement(2, 3)
    self.updateRoomPosition()

  def onFaceButton(self):
    # Record current position of controller as the face
    controllerNode = slicer.mrmlScene.GetNodeByID(self.needleModelNode.GetTransformNodeID())
    mat = vtk.vtkMatrix4x4()
    controllerNode.GetMatrixTransformToParent(mat)
    x = mat.GetElement(0, 3)
    y = mat.GetElement(1, 3)
    z = mat.GetElement(2, 3)
    self.facePosition = [x,y,z]
    self.updateRoomPosition()

  def updateRoomPosition(self):
    # Update cube root position so that the room is centered about the headset, 0.6m below the headset
    cubeMat = vtk.vtkMatrix4x4()
    self.rootCubeTransformNode.GetMatrixTransformToParent(cubeMat)
    hmdMat = vtk.vtkMatrix4x4()
    self.vrView.mrmlVirtualRealityViewNode().GetHMDTransformNode().GetMatrixTransformToParent(hmdMat)
    cubeMat.SetElement(0, 3, hmdMat.GetElement(0, 3))
    cubeMat.SetElement(1, 3, hmdMat.GetElement(1, 3))
    # Calculate the face position and set the floor height of the cube
    _userFaceHeight = self.facePosition[2] - self.floorHeight
    # cube is centered at 1m
    cubeMat.SetElement(2, 3, _userFaceHeight)
    self.rootCubeTransformNode.SetMatrixTransformToParent(cubeMat)

  def onShowControllerCheckBox(self, newState):
    self.vrView.mrmlVirtualRealityViewNode().SetControllerModelsVisible(newState)

  def onShowNeedleCheckBox(self, newState):
    self.needleModelNode.GetDisplayNode().SetVisibility(newState)

  def onShowSphereCheckBox(self, newState):
    self.sphereModelNode.GetDisplayNode().SetVisibility(newState)

  def onStartButton(self):# Update the current sequence with the desired sequence
    self.currentReferenceSequence = []
    if self.conditionComboBox.currentText == "Motion":
      self.currentReferenceSequence = self.motionSequence
    if self.conditionComboBox.currentText == "No motion":
      self.currentReferenceSequence = self.nomotionSequence
    if self.conditionComboBox.currentText == "Replay":
      self.currentReferenceSequence = self.replaySequence
    if len(self.currentReferenceSequence) == 0:
      self.error("Unable to load reference sequence.")
      return()

    # Show sphere and move to first position in currentReferenceSequence position, relative to "home" position
    self.showSphereCheckBox.checked = True
    self.sphereModelNode.GetDisplayNode().SetVisibility(True)
    self.currentIndex = 0
    self.onCurrentIndexChanged()

    # Resize capture list to the size of the reference list
    self.capturedSequence = []
    for i in range(0, len(self.currentReferenceSequence)):
      self.capturedSequence.append([0,0,0])

    self.isStarted = True
    self.updateUI()

  def onNextButton(self):
    self.currentIndex = min(self.currentIndex + 1, len(self.currentReferenceSequence)-1)
    self.onCurrentIndexChanged()

  def onPreviousButton(self):
    self.currentIndex = max(self.currentIndex - 1, 0)
    self.onCurrentIndexChanged()

  def onCurrentIndexChanged(self):
    # Transform point in face coord system to world/RAS coord system
    _point_face = np.asarray([[self.currentReferenceSequence[self.currentIndex][0]],
                         [self.currentReferenceSequence[self.currentIndex][1]],
                         [self.currentReferenceSequence[self.currentIndex][2]],
                         [1.0]], dtype=np.float64)
    _faceToWorld = np.asmatrix(np.eye(4))
    _faceToWorld[0, 3] = self.facePosition[0]
    _faceToWorld[1, 3] = self.facePosition[1]
    _faceToWorld[2, 3] = self.facePosition[2]
    _point_world = _faceToWorld * _point_face
    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0, 3, _point_world[0,0])
    mat.SetElement(1, 3, _point_world[1,0])
    mat.SetElement(2, 3, _point_world[2,0])
    self.sphereTransformNode.SetMatrixTransformToParent(mat)
    self.resultLabel.text = "Now capturing index " + str(self.currentIndex+1) + " of " + str(len(self.currentReferenceSequence)) + "."

  def onCaptureButton(self):
    controllerNode = slicer.mrmlScene.GetNodeByID(self.needleModelNode.GetTransformNodeID())
    mat = vtk.vtkMatrix4x4()
    controllerNode.GetMatrixTransformToParent(mat)
    x = mat.GetElement(0, 3)
    y = mat.GetElement(1, 3)
    z = mat.GetElement(2, 3)
    _worldToFace = np.asmatrix(np.eye(4))
    _worldToFace[0, 3] = -self.facePosition[0]
    _worldToFace[1, 3] = -self.facePosition[1]
    _worldToFace[2, 3] = -self.facePosition[2]
    _point_world = np.asarray([[x],[y],[z],[1.0]], dtype=np.float64)
    _point_face = _worldToFace * _point_world
    self.capturedSequence[self.currentIndex] = [ [_point_face[0,0], _point_face[1,0], _point_face[2,0]], self.currentReferenceSequence[self.currentIndex] ]
    self.updateUI()
    self.resultLabel.text = "Point for index " + str(self.currentIndex) + " collected."

  def onSaveButton(self):
    # Build filename string
    proto_filename = "participant" + self.participantIdLineEdit.text + "_trial" + str(self.trialNumberSpinBox.value) + "_" + self.conditionComboBox.currentText + ".txt"
    filename = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), "Save sequence", proto_filename)
    if filename == '':
      self.resultLabel.text = "File not saved."
      return()

    with open(filename, 'w') as f:
      f.write("#cap_x, cap_y, cap_z, ref_x, ref_y, ref_z\n")
      for cap in self.capturedSequence:
        f.write(str(cap[0][0]) + "," + str(cap[0][1]) + "," + str(cap[0][2]) + "," + str(cap[1][0]) + "," + str(cap[1][1]) + "," + str(cap[1][2]) + "\n")

    self.onResetButton()
    self.resultLabel.text = "File saved. Capture cleared."

  def onResetButton(self):
    self.isStarted = False
    self.showSphereCheckBox.checked = False
    self.sphereModelNode.GetDisplayNode().SetVisibility(False)
    self.updateUI()
    self.resultLabel.text = "Capture cleared."

  def onInitButton(self):
    self.isInit = False
    self.facePosition = []
    self.floorHeight = 0.0

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

    # Reset VR view to ref view
    self.vrView.mrmlVirtualRealityViewNode().SetAndObserveReferenceViewNode(slicer.app.layoutManager().threeDWidget(0).mrmlViewNode())
    self.vrView.updateViewFromReferenceViewCamera()

    # Ensure transforms are updated for camera and VR controllers
    self.vrView.mrmlVirtualRealityViewNode().SetControllerTransformsUpdate(True)
    self.vrView.mrmlVirtualRealityViewNode().SetHMDTransformUpdate(True)
    # Hide trackers and controllers
    self.showControllerCheckBox.checked = False
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
    success, self.sphereModelNode = slicer.util.loadModel(filename, True)
    if not success:
      self.error("Unable to load sphere model. Is module installed correctly?")
      return()
    self.sphereModelNode.GetDisplayNode().SetVisibility(False)
    self.sphereTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.sphereTransformNode)
    self.sphereTransformNode.SetName("SpherePose")
    self.sphereModelNode.SetAndObserveTransformNodeID(self.sphereTransformNode.GetID())

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
    self.showNeedleCheckBox.checked = True

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

    self.cubeModelRoof.GetDisplayNode().SetColor(0.9, 0.9, 0.9) # near white
    self.cubeModelFloor.GetDisplayNode().SetColor(0.4, 0.4, 0.4) # dark grey
    self.cubeModelLeft.GetDisplayNode().SetColor(0.7, 0.7, 0.7)  # medium grey
    self.cubeModelRight.GetDisplayNode().SetColor(0.7, 0.7, 0.7) # medium grey
    self.cubeModelFront.GetDisplayNode().SetColor(0.7, 0.7, 0.7)  # medium grey
    self.cubeModelBack.GetDisplayNode().SetColor(0.7, 0.7, 0.7)  # medium grey

    # Just to sort of get things close, set the face position to the HMD position
    hmdMat = vtk.vtkMatrix4x4()
    self.vrView.mrmlVirtualRealityViewNode().GetHMDTransformNode().GetMatrixTransformToParent(hmdMat)
    self.facePosition = [hmdMat.GetElement(0, 3), hmdMat.GetElement(1, 3), hmdMat.GetElement(2, 3)]
    self.updateRoomPosition()

    # Reset clipping
    self.vrView.renderWindow().GetRenderers().GetFirstRenderer().GetActiveCamera().SetClippingRange(0.1, 100000)

    self.isInit = True
    self.updateUI()
    self.resultLabel.text = "Reset."

  def updateUI(self):
    isReady = len(self.motionSequence) > 0 and len(self.nomotionSequence) > 0 and len(self.replaySequence) > 0 and self.isInit

    self.startButton.enabled = isReady and not self.isStarted and len(self.facePosition) > 0 and self.floorHeight != 0.0
    self.previousButton.enabled = self.isStarted
    self.nextButton.enabled = self.isStarted
    self.captureButton.enabled = self.isStarted
    self.resetButton.enabled = len(self.capturedSequence) > 0
    self.saveButton.enabled = len(self.capturedSequence) > 0

    self.showControllerCheckBox.enabled = self.vrView is not None and hasattr(self.vrView, "mrmlVirtualRealityViewNode") and isReady
    self.showNeedleCheckBox = self.needleModelNode is not None

    self.calibrateGroupBox.enabled = self.isInit
    self.inputsGroupBox.enabled = self.isInit

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
    self.updateUI()

  def onLoadNoMotionButton(self):
    self.nomotionSequence = []
    self.nomotionSequence = self.loadSequence()
    if len(self.nomotionSequence) == 0:
      self.error("Unable to load sequence.")
      return()
    else:
      self.resultLabel.text = "No-motion sequence loaded " + str(len(self.motionSequence)) + " points."
    self.updateUI()

  def onLoadReplayButton(self):
    self.replaySequence = []
    self.replaySequence = self.loadSequence()
    if len(self.replaySequence) == 0:
      self.error("Unable to load sequence.")
      return()
    else:
      self.resultLabel.text = "Replay sequence loaded " + str(len(self.motionSequence)) + " points."
    self.updateUI()

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
