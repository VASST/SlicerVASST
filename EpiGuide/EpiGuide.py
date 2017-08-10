import os
from __main__ import vtk, qt, ctk, slicer

from Guidelet import GuideletLoadable, GuideletLogic, GuideletTest, GuideletWidget
from Guidelet import Guidelet
import logging
import time
import math


#
# EpiGuide ###
#
class EpiGuide(GuideletLoadable):
  """Uses GuideletLoadable class, available at:
  """

  def __init__(self, parent):
    GuideletLoadable.__init__(self, parent)
    self.parent.title = "EpiGuide Navigation"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = [
      "Golafsoun Ameri (Robarts Research Institute), Adam Rankin (Robarts Research Institute)"]
    self.parent.helpText = """
  This is an example of scripted loadable module bundled in an extension.
  """
    self.parent.acknowledgementText = """
  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
  and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
  """  # replace with organization, grant and thanks.


#
# EpiGuideWidget
#

class EpiGuideWidget(GuideletWidget):
  """Uses GuideletWidget base class, available at:
  """

  def __init__(self, parent=None):
    try:
      import BreachWarningLight
      self.breachWarningLightLogic = BreachWarningLight.BreachWarningLightLogic()
    except ImportError:
      self.breachWarningLightLogic = None
      logging.warning('BreachWarningLight module is not available. Light feedback is disabled.')

    GuideletWidget.__init__(self, parent)

  def setup(self):
    GuideletWidget.setup(self)

  def addLauncherWidgets(self):
    GuideletWidget.addLauncherWidgets(self)

    # BreachWarning
    self.addBreachWarningLightPreferences()

  def onConfigurationChanged(self, selectedConfigurationName):
    GuideletWidget.onConfigurationChanged(self, selectedConfigurationName)
    if self.breachWarningLightLogic:
      settings = slicer.app.userSettings()
      lightEnabled = settings.value(
        self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/EnableBreachWarningLight')
      self.breachWarningLightCheckBox.checked = (lightEnabled == 'True')

  def addBreachWarningLightPreferences(self):
    lnNode = slicer.util.getNode(self.moduleName)

    if self.breachWarningLightLogic:

      self.breachWarningLightCheckBox = qt.QCheckBox()
      checkBoxLabel = qt.QLabel()
      hBoxCheck = qt.QHBoxLayout()
      hBoxCheck.setAlignment(0x0001)
      checkBoxLabel.setText("Use Breach Warning Light: ")
      hBoxCheck.addWidget(checkBoxLabel)
      hBoxCheck.addWidget(self.breachWarningLightCheckBox)
      hBoxCheck.setStretch(1, 2)
      self.launcherFormLayout.addRow(hBoxCheck)

      if (lnNode is not None and lnNode.GetParameter('EnableBreachWarningLight')):
        # logging.debug("There is already a connector EnableBreachWarningLight parameter " + lnNode.GetParameter('EnableBreachWarningLight'))
        self.breachWarningLightCheckBox.checked = lnNode.GetParameter('EnableBreachWarningLight')
        self.breachWarningLightCheckBox.setDisabled(True)
      else:
        self.breachWarningLightCheckBox.setEnabled(True)
        settings = slicer.app.userSettings()
        lightEnabled = settings.value(
          self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/EnableBreachWarningLight',
          'True')
        self.breachWarningLightCheckBox.checked = (lightEnabled == 'True')

      self.breachWarningLightCheckBox.connect('stateChanged(int)', self.onBreachWarningLightChanged)

  def onBreachWarningLightChanged(self, state):
    lightEnabled = ''
    if self.breachWarningLightCheckBox.checked:
      lightEnabled = 'True'
    elif not self.breachWarningLightCheckBox.checked:
      lightEnabled = 'False'
    self.guideletLogic.updateSettings({'EnableBreachWarningLight': lightEnabled}, self.selectedConfigurationName)

  def createGuideletInstance(self):
    return EpiGuideGuidelet(None, self.guideletLogic, self.selectedConfigurationName)

  def createGuideletLogic(self):
    return EpiGuideLogic()


#
# EpiGuideLogic ###
#

class EpiGuideLogic(GuideletLogic):
  """Uses GuideletLogic base class, available at:
  """  # TODO add path

  def __init__(self, parent=None):
    GuideletLogic.__init__(self, parent)

  def addValuesToDefaultConfiguration(self):
    GuideletLogic.addValuesToDefaultConfiguration(self)
    moduleDir = os.path.dirname(slicer.modules.epiguide.path)
    defaultSavePathOfEpiGuide = os.path.join(moduleDir, 'SavedScenes')
    settingList = {'EnableBreachWarningLight': 'False',
             'TipToSurfaceDistanceTextScale': '3',
             'BreachWarningLightMarginSizeMm': '2.0',
             'TipToSurfaceDistanceTrajectory': 'True',
             # 'NeedleModelToNeedleTip': '1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 0.0 1.0',
             'NeedleModelToNeedleTip' : '0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 1.0 0.0 0.0 0.0 0 0 0 1',
             'TestMode': 'False'
             }
    self.updateSettings(settingList, 'Default')


#
#	EpiGuideTest ###
#

class EpiGuideTest(GuideletTest):
  """This is the test case for your scripted module.
  """

  def runTest(self):
    """Run as few or as many tests as needed here.
  """
    GuideletTest.runTest(self)
    # self.test_EpiGuide1() #add applet specific tests here


class EpiGuideGuidelet(Guidelet):
  VIEW_ULTRASOUND_3D_3DCHART = unicode('Ultrasound + 3D + Chart')

  def __init__(self, parent, logic, configurationName='Default'):
    try:
      import BreachWarningLight
      self.breachWarningLightLogic = BreachWarningLight.BreachWarningLightLogic()
    except ImportError:
      self.breachWarningLightLogic = None

    Guidelet.__init__(self, parent, logic, configurationName)
    logging.debug('EpiGuideGuidelet.__init__')
    self.logic.addValuesToDefaultConfiguration()

    self.imageData = None
    self.imageDimensions = None
    self.line = None
    self.table = None
    self.chart = None
    self.view = None
    self.signalArray = None
    self.distanceArray = None
    self.boundsRecalculated = False

    moduleDirectoryPath = slicer.modules.epiguide.path.replace('EpiGuide.py', '')
    self.needleModelTipRadius = 0.0

    # Set up main frame.

    self.sliceletDockWidget.setObjectName('EpiGuidePanel')
    self.sliceletDockWidget.setWindowTitle('EpiGuideNav')
    self.mainWindow.setWindowTitle('Epidural injection navigation')

    # Set needle transforms and models
    self.setupScene()

    self.navigationView = self.VIEW_TRIPLE_3D

    # Setting button open on startup.

  def createFeaturePanels(self):
    # Create GUI panels.
    featurePanelList = Guidelet.createFeaturePanels(self)

    self.navigationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.setupNavigationPanel()

    featurePanelList[len(featurePanelList):] = [self.navigationCollapsibleButton]

    return featurePanelList

  def __del__(self):  # common
    self.cleanup()

  # Clean up when slicelet is closed
  def cleanup(self):  # common
    Guidelet.cleanup(self)
    logging.debug('cleanup')
    self.breachWarningNode.UnRegister(slicer.mrmlScene)
    if self.breachWarningLightLogic:
      self.breachWarningLightLogic.stopLightFeedback()

  def setupConnections(self):
    logging.debug('EpiGuide.setupConnections()')
    Guidelet.setupConnections(self)

    self.navigationCollapsibleButton.connect('toggled(bool)', self.onNavigationPanelToggled)
    self.leftBullseyeCameraButton.connect('clicked()', lambda: self.onCameraButtonClicked('View1'))
    self.rightBullseyeCameraButton.connect('clicked()', lambda: self.onCameraButtonClicked('View2'))
    self.bottomBullseyeCameraButton.connect('clicked()', lambda: self.onCameraButtonClicked('View3'))
    self.leftAutoCenterCameraButton.connect('clicked()', lambda: self.onAutoCenterButtonClicked('View1'))
    self.rightAutoCenterCameraButton.connect('clicked()', lambda: self.onAutoCenterButtonClicked('View2'))
    self.bottomAutoCenterCameraButton.connect('clicked()', lambda: self.onAutoCenterButtonClicked('View3'))

    self.dual3dButton.connect('clicked()', self.onDual3dButtonClicked)
    self.triple3dButton.connect('clicked()', self.onTriple3dButtonClicked)

    import Viewpoint
    self.viewpointLogic = Viewpoint.ViewpointLogic()

  def registerCustomLayouts(self):
    Guidelet.registerCustomLayouts(self)
    layoutLogic = self.layoutManager.layoutLogic()
    customLayout = (
      "<layout type=\"horizontal\" split=\"false\" >"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "  <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <layout type=\"vertical\" split=\"false\" >"
      "   <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Red\">"
      "   <property name=\"orientation\" action=\"default\">Axial</property>"
      "   <property name=\"viewlabel\" action=\"default\">R</property>"
      "   <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
      "  </view>"
      "   </item>"
      "   <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"2\">"
      "   <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      "   </item>"
      "  </layout>"
      " </item>"
      "</layout>")
    self.slice3DChartCustomLayoutId = 508
    layoutLogic.GetLayoutNode().AddLayoutDescription(self.slice3DChartCustomLayoutId, customLayout)

  def setupScene(self):  # applet specific
    logging.debug('setupScene')

    # Add a Qt timer, that fires every X ms (16.7ms = 60 FPS, 33ms = 30FPS)
    # Connect the timeout() signal of the qt timer to a function in this class that you will write
    self.timer = qt.QTimer()
    self.timer.connect('timeout()', self.OnTimerTimeout)
    self.timer.start(16.7)

    # ReferenceToRas is needed for ultrasound initialization, so we need to
    # set it up before calling Guidelet.setupScene().
    self.referenceToRas = slicer.util.getNode('ReferenceToRas')
    if not self.referenceToRas:
      self.referenceToRas = slicer.vtkMRMLLinearTransformNode()
      self.referenceToRas.SetName("ReferenceToRas")
      m = self.logic.readTransformFromSettings('ReferenceToRas', self.configurationName)
      if m is None:
        # By default ReferenceToRas is tilted 15deg around the patient LR axis as the reference
        # sensor is attached to the sternum, which is not horizontal.
        m = self.logic.createMatrixFromString('0 0 -1 0 0.258819 -0.965926 0 0 -0.965926 -0.258819 0 0 0 0 0 1')
      self.referenceToRas.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.referenceToRas)

    Guidelet.setupScene(self)

    logging.debug('Create transforms')
    # Coordinate system definitions: https://app.assembla.com/spaces/slicerigt/wiki/Coordinate_Systems

    self.needleTipToNeedle = slicer.util.getNode('NeedleTipToNeedle')
    if not self.needleTipToNeedle:
      self.needleTipToNeedle = slicer.vtkMRMLLinearTransformNode()
      self.needleTipToNeedle.SetName("NeedleTipToNeedle")
      m = self.logic.readTransformFromSettings('NeedleTipToNeedle', self.configurationName)
      if m:
        self.needleTipToNeedle.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.needleTipToNeedle)

    self.needleModelToNeedleTip = slicer.util.getNode('NeedleModelToNeedleTip')
    if not self.needleModelToNeedleTip:
      self.needleModelToNeedleTip = slicer.vtkMRMLLinearTransformNode()
      self.needleModelToNeedleTip.SetName("NeedleModelToNeedleTip")
      m = self.logic.readTransformFromSettings('NeedleModelToNeedleTip', self.configurationName)
      if m:
        self.needleModelToNeedleTip.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.needleModelToNeedleTip)

      # self.cauteryCameraToCautery = slicer.util.getNode('CauteryCameraToCautery')
      # if not self.cauteryCameraToCautery:
      # self.cauteryCameraToCautery=slicer.vtkMRMLLinearTransformNode()
      # self.cauteryCameraToCautery.SetName("CauteryCameraToCautery")
      # m = self.logic.createMatrixFromString('0 0 -1 0 1 0 0 0 0 -1 0 0 0 0 0 1')
      # self.cauteryCameraToCautery.SetMatrixTransformToParent(m)
      # slicer.mrmlScene.AddNode(self.cauteryCameraToCautery)

      # self.CauteryToNeedle = slicer.util.getNode('CauteryToNeedle')
      # if not self.CauteryToNeedle:
      # self.CauteryToNeedle=slicer.vtkMRMLLinearTransformNode()
      # self.CauteryToNeedle.SetName("CauteryToNeedle")
      # slicer.mrmlScene.AddNode(self.CauteryToNeedle)

    # Create transforms that will be updated through OpenIGTLink

    self.needleToReference = slicer.util.getNode('NeedleToReference')
    if not self.needleToReference:
      self.needleToReference = slicer.vtkMRMLLinearTransformNode()
      self.needleToReference.SetName("NeedleToReference")
      slicer.mrmlScene.AddNode(self.needleToReference)

    # Models
    logging.debug('Create models')

    self.needleModel_NeedleTip = slicer.util.getNode('NeedleModel')
    if not self.needleModel_NeedleTip:
      slicer.modules.createmodels.logic().CreateNeedle(65, 1.0, self.needleModelTipRadius,
                               0)  # length, radius,tipradius, bool marjers, vtkmrmlmodelNode(1 or 0: creates a ring close to tip)
      self.needleModel_NeedleTip = slicer.util.getNode(pattern="NeedleModel")
      self.needleModel_NeedleTip.GetDisplayNode().SetColor(1.0, 0.0, 1.0)
      self.needleModel_NeedleTip.SetName("NeedleModel")
      self.needleModel_NeedleTip.GetDisplayNode().SliceIntersectionVisibilityOn()

    # Models: needle and A-mode signal peak models
    # self.needleModel_NeedleTip = slicer.util.getNode('NeedleModel')
    self.setTipToReferenceTransformNode = slicer.util.getNode('NeedleToReference')
    self.firstPeakNode = slicer.util.getNode('FirstPeakToNeedleTip')
    self.secondPeakNode = slicer.util.getNode('SecondPeakToNeedleTip')
    self.thirdPeakNode = slicer.util.getNode('ThirdPeakToNeedleTip')
    self.loadAndParentModels(self.tipToReferenceNode, self.firstPeakNode, self.secondPeakNode, self.thirdPeakNode)

    # Set up breach warning node
    logging.debug('Set up breach warning')
    self.breachWarningNode = slicer.util.getNode('EpiGuideBreachWarning')

    if not self.breachWarningNode:
      self.breachWarningNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLBreachWarningNode')
      self.breachWarningNode.UnRegister(None)  # Python variable already holds a reference to it
      self.breachWarningNode.SetName("EpiGuideBreachWarning")
      slicer.mrmlScene.AddNode(self.breachWarningNode)
      self.breachWarningNode.SetPlayWarningSound(True)
      self.breachWarningNode.SetWarningColor(1, 0, 0)
      breachWarningLogic = slicer.modules.breachwarning.logic()
      # Line properties can only be set after the line is creaed (made visible at least once)
      breachWarningLogic.SetLineToClosestPointVisibility(True, self.breachWarningNode)
      distanceTextScale = self.parameterNode.GetParameter('TipToSurfaceDistanceTextScale')
      breachWarningLogic.SetLineToClosestPointTextScale(float(distanceTextScale), self.breachWarningNode)
      breachWarningLogic.SetLineToClosestPointColor(0, 0, 1, self.breachWarningNode)
      breachWarningLogic.SetLineToClosestPointVisibility(False, self.breachWarningNode)

    # Set up breach warning light
    if self.breachWarningLightLogic:
      logging.debug('Set up breach warning light')
      self.breachWarningLightLogic.setMarginSizeMm(
        float(self.parameterNode.GetParameter('BreachWarningLightMarginSizeMm')))
      if (self.parameterNode.GetParameter('EnableBreachWarningLight') == 'True'):
        logging.debug("BreachWarningLight: active")
        self.breachWarningLightLogic.startLightFeedback(self.breachWarningNode, self.connectorNode)
      else:
        logging.debug("BreachWarningLight: shutdown")
        self.breachWarningLightLogic.shutdownLight(self.connectorNode)

    # Build transform tree
    logging.debug('Set up transform tree')
    self.needleToReference.SetAndObserveTransformNodeID(self.referenceToRas.GetID())
    self.needleTipToNeedle.SetAndObserveTransformNodeID(self.needleToReference.GetID())
    self.needleModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
    self.needleModel_NeedleTip.SetAndObserveTransformNodeID(self.needleModelToNeedleTip.GetID())
    # self.liveUltrasoundNode_Reference.SetAndObserveTransformNodeID(self.referenceToRas.GetID()) # always commented out

    # Hide slice view annotations (patient name, scale, color bar, etc.) as they
    # decrease reslicing performance by 20%-100%
    logging.debug('Hide slice view annotations')
    import DataProbe
    dataProbeUtil = DataProbe.DataProbeLib.DataProbeUtil()
    dataProbeParameterNode = dataProbeUtil.getParameterNode()
    dataProbeParameterNode.SetParameter('showSliceViewAnnotations', '0')

  def disconnect(self):  # TODO see connect
    logging.debug('EpiGuide.disconnect()')
    Guidelet.disconnect(self)

    # # Remove observer to old parameter node
    self.navigationCollapsibleButton.disconnect('toggled(bool)', self.onNavigationPanelToggled)
    self.leftBullseyeCameraButton.disconnect('clicked()', lambda: self.onCameraButtonClicked('View1'))
    self.rightBullseyeCameraButton.disconnect('clicked()', lambda: self.onCameraButtonClicked('View2'))
    self.bottomBullseyeCameraButton.disconnect('clicked()', lambda: self.onCameraButtonClicked('View3'))
    self.leftAutoCenterCameraButton.disconnect('clicked()', lambda: self.onAutoCenterButtonClicked('View1'))
    self.rightAutoCenterCameraButton.disconnect('clicked()', lambda: self.onAutoCenterButtonClicked('View2'))
    self.bottomAutoCenterCameraButton.disconnect('clicked()', lambda: self.onAutoCenterButtonClicked('View3'))


    # def onPlaceClicked(self, pushed):
    # logging.debug('onPlaceClicked')
    # interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    # if pushed:
    # # activate placement mode
    # selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    # selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
    # selectionNode.SetActivePlaceNodeID(self.tumorMarkups_Needle.GetID())
    # interactionNode.SetPlaceModePersistence(1)
    # interactionNode.SetCurrentInteractionMode(interactionNode.Place)
    # else:
    # # deactivate placement mode
    # interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)

  def setupNavigationPanel(self):
    logging.debug('setupNavigationPanel')

    self.sliderTranslationDefaultMm = 0
    self.sliderTranslationMinMm = -500
    self.sliderTranslationMaxMm = 500
    self.sliderViewAngleDefaultDeg = 30
    self.cameraViewAngleMinDeg = 5.0  # maximum magnification
    self.cameraViewAngleMaxDeg = 150.0  # minimum magnification

    self.sliderSingleStepValue = 1
    self.sliderPageStepValue = 10

    self.navigationCollapsibleButton.setProperty('collapsedHeight', 20)
    self.navigationCollapsibleButton.text = "Navigation"
    self.sliceletPanelLayout.addWidget(self.navigationCollapsibleButton)

    self.navigationCollapsibleLayout = qt.QFormLayout(self.navigationCollapsibleButton)
    self.navigationCollapsibleLayout.setContentsMargins(12, 4, 4, 4)
    self.navigationCollapsibleLayout.setSpacing(4)

    self.leftBullseyeCameraButton = qt.QPushButton("Left camera")
    self.leftBullseyeCameraButton.setCheckable(True)

    self.rightBullseyeCameraButton = qt.QPushButton("Right camera")
    self.rightBullseyeCameraButton.setCheckable(True)

    self.bottomBullseyeCameraButton = qt.QPushButton("Bottom camera")
    self.bottomBullseyeCameraButton.setCheckable(True)

    bullseyeHBox = qt.QHBoxLayout()
    bullseyeHBox.addWidget(self.leftBullseyeCameraButton)
    bullseyeHBox.addWidget(self.rightBullseyeCameraButton)
    self.navigationCollapsibleLayout.addRow(bullseyeHBox)

    # "View" Collapsible
    self.viewCollapsibleButton = ctk.ctkCollapsibleGroupBox()
    self.viewCollapsibleButton.title = "View"
    self.viewCollapsibleButton.collapsed = True
    self.navigationCollapsibleLayout.addRow(self.viewCollapsibleButton)

    # Layout within the collapsible button
    self.viewFormLayout = qt.QFormLayout(self.viewCollapsibleButton)

    # Camera distance to focal point slider
    self.cameraViewAngleLabel = qt.QLabel(qt.Qt.Horizontal, None)
    self.cameraViewAngleLabel.setText("Field of view [degrees]: ")
    self.cameraViewAngleSlider = slicer.qMRMLSliderWidget()
    self.cameraViewAngleSlider.minimum = self.cameraViewAngleMinDeg
    self.cameraViewAngleSlider.maximum = self.cameraViewAngleMaxDeg
    self.cameraViewAngleSlider.value = self.sliderViewAngleDefaultDeg
    self.cameraViewAngleSlider.singleStep = self.sliderSingleStepValue
    self.cameraViewAngleSlider.pageStep = self.sliderPageStepValue
    self.cameraViewAngleSlider.setDisabled(True)
    self.viewFormLayout.addRow(self.cameraViewAngleLabel, self.cameraViewAngleSlider)

    self.cameraXPosLabel = qt.QLabel(qt.Qt.Horizontal, None)
    self.cameraXPosLabel.text = "Left/Right [mm]: "
    self.cameraXPosSlider = slicer.qMRMLSliderWidget()
    self.cameraXPosSlider.minimum = self.sliderTranslationMinMm
    self.cameraXPosSlider.maximum = self.sliderTranslationMaxMm
    self.cameraXPosSlider.value = self.sliderTranslationDefaultMm
    self.cameraXPosSlider.singleStep = self.sliderSingleStepValue
    self.cameraXPosSlider.pageStep = self.sliderPageStepValue
    self.cameraXPosSlider.setDisabled(True)
    self.viewFormLayout.addRow(self.cameraXPosLabel, self.cameraXPosSlider)

    self.cameraYPosLabel = qt.QLabel(qt.Qt.Horizontal, None)
    self.cameraYPosLabel.setText("Down/Up [mm]: ")
    self.cameraYPosSlider = slicer.qMRMLSliderWidget()
    self.cameraYPosSlider.minimum = self.sliderTranslationMinMm
    self.cameraYPosSlider.maximum = self.sliderTranslationMaxMm
    self.cameraYPosSlider.value = self.sliderTranslationDefaultMm
    self.cameraYPosSlider.singleStep = self.sliderSingleStepValue
    self.cameraYPosSlider.pageStep = self.sliderPageStepValue
    self.cameraYPosSlider.setDisabled(True)
    self.viewFormLayout.addRow(self.cameraYPosLabel, self.cameraYPosSlider)

    self.cameraZPosLabel = qt.QLabel(qt.Qt.Horizontal, None)
    self.cameraZPosLabel.setText("Front/Back [mm]: ")
    self.cameraZPosSlider = slicer.qMRMLSliderWidget()
    self.cameraZPosSlider.minimum = self.sliderTranslationMinMm
    self.cameraZPosSlider.maximum = self.sliderTranslationMaxMm
    self.cameraZPosSlider.value = self.sliderTranslationDefaultMm
    self.cameraZPosSlider.singleStep = self.sliderSingleStepValue
    self.cameraZPosSlider.pageStep = self.sliderPageStepValue
    self.cameraZPosSlider.setDisabled(True)
    self.viewFormLayout.addRow(self.cameraZPosLabel, self.cameraZPosSlider)

    self.dual3dButton = qt.QPushButton("Dual 3D")
    self.triple3dButton = qt.QPushButton("Triple 3D")

    bullseyeHBox = qt.QHBoxLayout()
    bullseyeHBox.addWidget(self.dual3dButton)
    bullseyeHBox.addWidget(self.triple3dButton)
    self.viewFormLayout.addRow(bullseyeHBox)

    autoCenterLabel = qt.QLabel("Auto-center: ")

    self.leftAutoCenterCameraButton = qt.QPushButton("Left")
    self.leftAutoCenterCameraButton.setCheckable(True)

    self.rightAutoCenterCameraButton = qt.QPushButton("Right")
    self.rightAutoCenterCameraButton.setCheckable(True)

    self.bottomAutoCenterCameraButton = qt.QPushButton("Bottom")
    self.bottomAutoCenterCameraButton.setCheckable(True)

    self.viewFormLayout.addRow(self.bottomBullseyeCameraButton)

    autoCenterHBox = qt.QHBoxLayout()
    autoCenterHBox.addWidget(autoCenterLabel)
    autoCenterHBox.addWidget(self.leftAutoCenterCameraButton)
    autoCenterHBox.addWidget(self.bottomAutoCenterCameraButton)
    autoCenterHBox.addWidget(self.rightAutoCenterCameraButton)
    self.viewFormLayout.addRow(autoCenterHBox)

  # def onCalibrationPanelToggled(self, toggled):
    # if toggled == False:
      # return

    # logging.debug('onCalibrationPanelToggled: {0}'.format(toggled))

    # self.selectView(self.VIEW_ULTRASOUND_3D)
    # self.placeButton.checked = False

  def onUltrasoundPanelToggled(self, toggled):
    Guidelet.onUltrasoundPanelToggled(self, toggled)
    # The user may want to freeze the image (disconnect) to make contouring easier.
    # Disable automatic ultrasound image auto-fit when the user unfreezes (connect)
    # to avoid zooming out of the image.
    self.fitUltrasoundImageToViewOnConnect = not toggled

  def getCamera(self, viewName):
    """
  Get camera for the selected 3D view
  """
    logging.debug("getCamera")
    camerasLogic = slicer.modules.cameras.logic()
    camera = camerasLogic.GetViewActiveCameraNode(slicer.util.getNode(viewName))
    return camera

  def getViewNode(self, viewName):
    """
  Get the view node for the selected 3D view
  """
    logging.debug("getViewNode")
    viewNode = slicer.util.getNode(viewName)
    return viewNode

  def onCameraButtonClicked(self, viewName):
    viewNode = self.getViewNode(viewName)
    logging.debug("onCameraButtonClicked")
    if (self.viewpointLogic.getViewpointForViewNode(viewNode).isCurrentModeBullseye()):
      self.disableBullseyeInViewNode(viewNode)
      self.enableAutoCenterInViewNode(viewNode)
    else:
      self.disableViewpointInViewNode(viewNode)  # disable any other modes that might be active
      self.enableBullseyeInViewNode(viewNode)
    self.updateGUIButtons()

  def enableBullseyeInViewNode(self, viewNode):
    logging.debug("enableBullseyeInViewNode")
    self.disableViewpointInViewNode(viewNode)
    self.viewpointLogic.getViewpointForViewNode(viewNode).setViewNode(viewNode)
    self.viewpointLogic.getViewpointForViewNode(viewNode).bullseyeSetTransformNode(self.cauteryCameraToCautery)
    self.viewpointLogic.getViewpointForViewNode(viewNode).bullseyeStart()
    self.updateGUISliders(viewNode)

  def disableBullseyeInViewNode(self, viewNode):
    logging.debug("disableBullseyeInViewNode")
    if (self.viewpointLogic.getViewpointForViewNode(viewNode).isCurrentModeBullseye()):
      self.viewpointLogic.getViewpointForViewNode(viewNode).bullseyeStop()
      self.updateGUISliders(viewNode)

  def disableBullseyeInAllViewNodes(self):
    logging.debug("disableBullseyeInAllViewNodes")
    leftViewNode = self.getViewNode('View1')
    self.disableBullseyeInViewNode(leftViewNode)
    rightViewNode = self.getViewNode('View2')
    self.disableBullseyeInViewNode(rightViewNode)
    bottomViewNode = self.getViewNode('View3')
    self.disableBullseyeInViewNode(bottomViewNode)

  def updateGUISliders(self, viewNode):
    logging.debug("updateGUISliders")
    if (self.viewpointLogic.getViewpointForViewNode(viewNode).isCurrentModeBullseye()):
      self.cameraViewAngleSlider.connect('valueChanged(double)', self.viewpointLogic.getViewpointForViewNode(
        viewNode).bullseyeSetCameraViewAngleDeg)
      self.cameraXPosSlider.connect('valueChanged(double)',
                      self.viewpointLogic.getViewpointForViewNode(viewNode).bullseyeSetCameraXPosMm)
      self.cameraYPosSlider.connect('valueChanged(double)',
                      self.viewpointLogic.getViewpointForViewNode(viewNode).bullseyeSetCameraYPosMm)
      self.cameraZPosSlider.connect('valueChanged(double)',
                      self.viewpointLogic.getViewpointForViewNode(viewNode).bullseyeSetCameraZPosMm)
      self.cameraViewAngleSlider.setDisabled(False)
      self.cameraXPosSlider.setDisabled(False)
      self.cameraZPosSlider.setDisabled(False)
      self.cameraYPosSlider.setDisabled(False)
    else:
      self.cameraViewAngleSlider.disconnect('valueChanged(double)', self.viewpointLogic.getViewpointForViewNode(
        viewNode).bullseyeSetCameraViewAngleDeg)
      self.cameraXPosSlider.disconnect('valueChanged(double)', self.viewpointLogic.getViewpointForViewNode(
        viewNode).bullseyeSetCameraXPosMm)
      self.cameraYPosSlider.disconnect('valueChanged(double)', self.viewpointLogic.getViewpointForViewNode(
        viewNode).bullseyeSetCameraYPosMm)
      self.cameraZPosSlider.disconnect('valueChanged(double)', self.viewpointLogic.getViewpointForViewNode(
        viewNode).bullseyeSetCameraZPosMm)
      self.cameraViewAngleSlider.setDisabled(True)
      self.cameraXPosSlider.setDisabled(True)
      self.cameraZPosSlider.setDisabled(True)
      self.cameraYPosSlider.setDisabled(True)

  def onAutoCenterButtonClicked(self, viewName):  ###
    viewNode = self.getViewNode(viewName)
    logging.debug("onAutoCenterButtonClicked")
    if (self.viewpointLogic.getViewpointForViewNode(viewNode).isCurrentModeAutoCenter()):
      self.disableAutoCenterInViewNode(viewNode)
    else:
      self.enableAutoCenterInViewNode(viewNode)
    self.updateGUIButtons()

  def disableAutoCenterInViewNode(self, viewNode):
    logging.debug("disableAutoCenterInViewNode")
    if (self.viewpointLogic.getViewpointForViewNode(viewNode).isCurrentModeAutoCenter()):
      self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterStop()

  def enableAutoCenterInViewNode(self, viewNode):
    logging.debug("enableAutoCenterInViewNode")
    self.disableViewpointInViewNode(viewNode)
    heightViewCoordLimits = 0.6;
    widthViewCoordLimits = 0.9;
    self.viewpointLogic.getViewpointForViewNode(viewNode).setViewNode(viewNode)
    self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterSetSafeXMinimum(-widthViewCoordLimits)
    self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterSetSafeXMaximum(widthViewCoordLimits)
    self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterSetSafeYMinimum(-heightViewCoordLimits)
    self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterSetSafeYMaximum(heightViewCoordLimits)
    #  self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterSetModelNode(self.tumorModel_Needle)
    self.viewpointLogic.getViewpointForViewNode(viewNode).autoCenterStart()

  def disableViewpointInViewNode(self, viewNode):
    logging.debug("disableViewpointInViewNode")
    self.disableBullseyeInViewNode(viewNode)
    self.disableAutoCenterInViewNode(viewNode)

  def updateGUIButtons(self):
    logging.debug("updateGUIButtons")

    leftViewNode = self.getViewNode('View1')

    blockSignalState = self.leftAutoCenterCameraButton.blockSignals(True)
    if (self.viewpointLogic.getViewpointForViewNode(leftViewNode).isCurrentModeAutoCenter()):
      self.leftAutoCenterCameraButton.setChecked(True)
    else:
      self.leftAutoCenterCameraButton.setChecked(False)
    self.leftAutoCenterCameraButton.blockSignals(blockSignalState)

    blockSignalState = self.leftBullseyeCameraButton.blockSignals(True)
    if (self.viewpointLogic.getViewpointForViewNode(leftViewNode).isCurrentModeBullseye()):
      self.leftBullseyeCameraButton.setChecked(True)
      # cauteryNode = slicer.util.getNode('CauteryModel')
      # cauteryNode.GetDisplayNode().SetOpacity(0.3)
      print("left cam set opacity to 0.3")
    else:
      self.leftBullseyeCameraButton.setChecked(False)
      # cauteryNode = slicer.util.getNode('CauteryModel')
      # cauteryNode.GetDisplayNode().SetOpacity(1)
      # print("left cam set opacity to 1")
    self.leftBullseyeCameraButton.blockSignals(blockSignalState)

    rightViewNode = self.getViewNode('View2')

    blockSignalState = self.rightAutoCenterCameraButton.blockSignals(True)
    if (self.viewpointLogic.getViewpointForViewNode(rightViewNode).isCurrentModeAutoCenter()):
      self.rightAutoCenterCameraButton.setChecked(True)
    else:
      self.rightAutoCenterCameraButton.setChecked(False)
    self.rightAutoCenterCameraButton.blockSignals(blockSignalState)

    blockSignalState = self.rightBullseyeCameraButton.blockSignals(True)
    if (self.viewpointLogic.getViewpointForViewNode(rightViewNode).isCurrentModeBullseye()):
      self.rightBullseyeCameraButton.setChecked(True)
      # cauteryNode = slicer.util.getNode('CauteryModel')
      # cauteryNode.GetDisplayNode().SetOpacity(0.3)
      print("r cam set opacity to 0.3")
    else:
      self.rightBullseyeCameraButton.setChecked(False)
      # cauteryNode = slicer.util.getNode('CauteryModel')
      # if self.rightBullseyeCameraButton.setChecked(False):
      # cauteryNode.GetDisplayNode().SetOpacity(1)
      # print("r cam set opacity to 01")
    self.rightBullseyeCameraButton.blockSignals(blockSignalState)

    centerViewNode = self.getViewNode('View3')

    blockSignalState = self.bottomAutoCenterCameraButton.blockSignals(True)
    if (self.viewpointLogic.getViewpointForViewNode(centerViewNode).isCurrentModeAutoCenter()):
      self.bottomAutoCenterCameraButton.setChecked(True)
    else:
      self.bottomAutoCenterCameraButton.setChecked(False)
    self.bottomAutoCenterCameraButton.blockSignals(blockSignalState)

    blockSignalState = self.bottomBullseyeCameraButton.blockSignals(True)
    if (self.viewpointLogic.getViewpointForViewNode(centerViewNode).isCurrentModeBullseye()):
      self.bottomBullseyeCameraButton.setChecked(True)
    else:
      self.bottomBullseyeCameraButton.setChecked(False)
    self.bottomBullseyeCameraButton.blockSignals(blockSignalState)

  def onDual3dButtonClicked(self):
    logging.debug("onDual3dButtonClicked")
    self.navigationView = self.VIEW_DUAL_3D
    self.updateNavigationView()

  def onTriple3dButtonClicked(self):
    logging.debug("onDual3dButtonClicked")
    self.navigationView = self.VIEW_TRIPLE_3D
    self.updateNavigationView()

  def updateNavigationView(self):
    logging.debug("updateNavigationView")
    self.selectView(self.navigationView)

    # Reset orientation marker
    if hasattr(slicer.vtkMRMLViewNode(),
           'SetOrientationMarkerType'):  # orientation marker is not available in older Slicer versions
      v1 = slicer.util.getNode('View1')
      v1v2OrientationMarkerSize = v1.OrientationMarkerSizeMedium if self.navigationView == self.VIEW_TRIPLE_3D else v1.OrientationMarkerSizeSmall
      v1.SetOrientationMarkerType(v1.OrientationMarkerTypeHuman)
      v1.SetOrientationMarkerSize(v1v2OrientationMarkerSize)
      v1.SetBoxVisible(False)
      v1.SetAxisLabelsVisible(False)
      v2 = slicer.util.getNode('View2')
      v2.SetOrientationMarkerType(v2.OrientationMarkerTypeHuman)
      v2.SetOrientationMarkerSize(v1v2OrientationMarkerSize)
      v2.SetBoxVisible(False)
      v2.SetAxisLabelsVisible(False)
      v3 = slicer.util.getNode('View3')
      if v3:  # only available in triple view
        v3.SetOrientationMarkerType(v1.OrientationMarkerTypeHuman)
        v3.SetOrientationMarkerSize(v1.OrientationMarkerSizeLarge)
        v3.SetBoxVisible(False)
        v3.SetAxisLabelsVisible(False)

    # Reset the third view to show the patient from a standard direction (from feet)
    depthViewCamera = self.getCamera('View3')
    if depthViewCamera:  # only available in triple view
      depthViewCamera.RotateTo(depthViewCamera.Inferior)

  def onNavigationPanelToggled(self, toggled):
    logging.debug("onNavigationPanelToggled")

    breachWarningLogic = slicer.modules.breachwarning.logic()
    showTrajectoryToClosestPoint = toggled and (
    self.parameterNode.GetParameter('TipToSurfaceDistanceTrajectory') == 'True')
    breachWarningLogic.SetLineToClosestPointVisibility(showTrajectoryToClosestPoint, self.breachWarningNode)

    if toggled == False:
      return

    logging.debug('onNavigationPanelToggled')
    self.updateNavigationView()
    # self.placeButton.checked = False
    # if self.tumorMarkups_Needle:
    # self.tumorMarkups_Needle.SetDisplayVisibility(0)

    # Stop live ultrasound.
    if self.connectorNode != None:
      self.connectorNode.Stop()

  # def onNeedleLengthModified(self, newLength):
    # logging.debug('onNeedleLengthModified {0}'.format(newLength))
    # needleTipToNeedleBaseMatrix = vtk.vtkMatrix4x4()
    # needleTipToNeedleBaseMatrix.SetElement(1,3,newLength)
    # needleTipToNeedleMatrix = vtk.vtkMatrix4x4()
    # self.needleTipToNeedle.SetMatrixTransformToParent(needleTipToNeedleMatrix)
    # self.logic.writeTransformToSettings('NeedleTipToNeedle', needleTipToNeedleMatrix, self.configurationName)
    # slicer.modules.createmodels.logic().CreateNeedle(newLength,1.0, self.needleModelTipRadius, False, self.needleModel_NeedleTip)

    
# ---------------------------------------------------------
# incorporating A-mode signal into the scene
# ---------------------------------------------------------
  def setupViewerLayouts(self):
    Guidelet.setupViewerLayouts(self)
    # Now we can add our own layout to the drop downlist
    self.viewSelectorComboBox.addItem(self.VIEW_ULTRASOUND_3D_3DCHART)

  def populateChart(self):
    # strip elements from 2nd 3d view
    # and add our own chart renderer to it
    self.imageNode = slicer.util.getNode('Image_NeedleTip')
    if self.imageNode == None:
      logging.debug("Cannot locate Image_NeedleTip, can't visualize chart")
      return

    self.imageData = self.imageNode.GetImageData()

    if self.table != None:
      # We already have created all of the things, don't recreate
      self.view.GetInteractor().Initialize()
      self.chart.RecalculateBounds()
      return

    self.table = vtk.vtkTable()
    self.chart = vtk.vtkChartXY()
    self.line = self.chart.AddPlot(0)
    self.view = vtk.vtkContextView()
    self.signalArray = vtk.vtkDoubleArray()
    self.signalArray.SetName("RF Signal")
    self.distanceArray = vtk.vtkDoubleArray()
    self.distanceArray.SetName("Distance (mm)")

    self.imageDimensions = self.imageData.GetDimensions()
    self.signalArray.SetNumberOfTuples(self.imageDimensions[0])
    self.distanceArray.SetNumberOfTuples(self.imageDimensions[0])

    self.table.AddColumn(self.distanceArray)
    self.table.AddColumn(self.signalArray)

    self.line = self.chart.AddPlot(0)
    self.line.SetInputData(self.table, 0, 1)
    self.line.SetColor(0, 255, 0, 255)
    self.line.SetWidth(1.0)

    inc = 1000 * 1480 / (
    2 * 420e6)  # distance in mm. The delay distance is added to the increments.  (2e-6*1480/2) +
    distanceDelay = 1000 * 2e-6 * 1480 / 2
    for i in range(self.imageDimensions[0]):
      self.distanceArray.SetComponent(i, 0, distanceDelay + inc * i)

    self.view.GetRenderer().SetBackground(1.0, 1.0, 1.0)
    self.view.GetRenderWindow().SetSize(400, 300)
    # self.contextScene = vtk.vtkContextScene()
    # self.contextScene.AddItem(self.chart)
    # self.contextActor = vtk.vtkContextActor()
    self.view.GetScene().AddItem(self.chart)
    self.view.GetRenderWindow().SetMultiSamples(0)
    # self.layoutManager.threeDWidget(1).threeDView.renderWindow().GetRenderer().GetFirstRenderer().AddActor(self.contextActor)

    self.view.GetInteractor().Initialize()
    #self.chart.RecalculateBounds() # either here or in OnTimerTimeout

  def onViewSelect(self, layoutIndex):
    # Check out layout request first, then pass on to parent to handle the existing ones
    text = self.viewSelectorComboBox.currentText
    if text == self.VIEW_ULTRASOUND_3D_3DCHART:
      self.layoutManager.setLayout(self.slice3DChartCustomLayoutId)
      self.delayedFitUltrasoundImageToView()
      self.populateChart()
      return

    Guidelet.onViewSelect(self, layoutIndex)

  def OnTimerTimeout(self):
    if self.imageData == None or self.imageDimensions == None:
      return

    # To update graph, grab latest data
    for i in range(self.imageDimensions[0]):
      self.signalArray.SetComponent(i, 0, self.imageData.GetScalarComponentAsDouble(i, 0, 0, 0))

    if not self.boundsRecalculated:
      self.chart.RecalculateBounds()
      self.boundsRecalculated = True

    # And one of these is the magical call to update the window
    self.chart.RecalculateBounds()
    self.table.Modified()
    self.line.Update()
    self.view.Update()

    # However, I'm 99% sure this one is always necessary
    self.view.GetInteractor().Render()


  #def loadAndParentModels( setTipToReferenceTransformNode, firstPeakToSETTipTransformNode,
                        secondPeakToSETTipTransformNode, thirdPeakToSETTipTransformNode):
    # Calling this function will ask SlicerIGT's create models to create 3 disks (short cylinders),
    # parent each disk to a peak transform, and parent each peak transform to the setTipToReference
    #
    # Prior to calling this, you will have to identify which transformNode corresponds to which peak
    # These should be sent from plus as FirstPeakToReference, SecondPeakToReference, etc...
    # To find those, after connecting to Plus (oscilloscope machine)
    #
    # self.firstPeakNode = slicer.util.getNode('FirstPeakToReference')
    # self.secondPeakNode = slicer.util.getNode('SecondPeakToReference')
    # ...
    # then call
    # self.loadAndParentModels(self.tipToReferenceNode, self.firstPeakNode, self.secondPeakNode, self.thirdPeakNode)
    #
    # To make this more advanced, you could have it clean up any existing models (look for by name using slicer.util.getNode)
    # so you could call this repeatedly. However, best to just call this once (in init or setup)

    # self.needleModel_NeedleTip.GetDisplayNode().SetColor(1.0, 0.0, 1.0)
    # self.needleModel_NeedleTip.SetName("NeedleModel")
    # self.needleModel_NeedleTip.GetDisplayNode().SliceIntersectionVisibilityOn()
    # setTipToReferenceTransformNode
    
    # self.NeedleModelNode = slicer.modules.createmodels.logic().CreateNeedle(65, 1.0, self.needleModelTipRadius,0)
    # self.NeedleModelNode.SetName("NeedleModel")
    # self.NeedleModelNode.GetDisplayNode().SetColor(1.0, 0.0, 1.0)    
    # self.NeedleModelNode.GetDisplayNode().SliceIntersectionVisibilityOn()

    # self.firstPeakModelNode = slicer.modules.createmodels.logic().CreateCylinder(0.5, 4)  # 0.5mm tall, 4mm radius
    # self.firstPeakModelNode.SetName('FirstPeakModel')
    # self.firstPeakModelNode.GetDisplayNode().SetColor(1.0, 0.0, 0.0)  # r, g, b [0.0,1.0]
    # self.firstPeakModelNode.SetAndObserveTransformNodeID(firstPeakToSETTipTransformNode.GetID())
    # firstPeakToSETTipTransformNode.SetAndObserveTransformNodeID(setTipToReferenceTransformNode.GetID())

    # self.secondPeakModelNode = slicer.modules.createmodels.logic().CreateCylinder(0.5, 4)  # 0.5mm tall, 4mm radius
    # self.secondPeakModelNode.SetName('SecondPeakModel')
    # self.secondPeakModelNode.GetDisplayNode().SetColor(0.0, 1.0, 0.0)  # r, g, b [0.0,1.0]
    # self.secondPeakModelNode.SetAndObserveTransformNodeID(secondPeakToSETTipTransformNode.GetID())
    # secondPeakToSETTipTransformNode.SetAndObserveTransformNodeID(setTipToReferenceTransformNode.GetID())

    # self.thirdPeakModelNode = slicer.modules.createmodels.logic().CreateCylinder(0.5, 4)  # 0.5mm tall, 4mm radius
    # self.thirdPeakModelNode.SetName('ThirdPeakModel')
    # self.thirdPeakModelNode.GetDisplayNode().SetColor(0.0, 0.0, 1.0)  # r, g, b [0.0,1.0]
    # self.thirdPeakModelNode.SetAndObserveTransformNodeID(thirdPeakToSETTipTransformNode.GetID())
    # thirdPeakToSETTipTransformNode.SetAndObserveTransformNodeID(setTipToReferenceTransformNode.GetID())




