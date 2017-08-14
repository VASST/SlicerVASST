import os
from __main__ import vtk, qt, ctk, slicer

from Guidelet import GuideletLoadable, GuideletLogic, GuideletTest, GuideletWidget
from Guidelet import Guidelet
import logging
import time
import math

# -----------------------------------------------------
# EpiGuide ###
# -----------------------------------------------------
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

# -----------------------------------------------------
# EpiGuideWidget
# -----------------------------------------------------
class EpiGuideWidget(GuideletWidget):
  """Uses GuideletWidget base class, available at:
  """

  def __init__(self, parent=None):
    GuideletWidget.__init__(self, parent)

  def setup(self):
    GuideletWidget.setup(self)

  def addLauncherWidgets(self):
    GuideletWidget.addLauncherWidgets(self)

  def onConfigurationChanged(self, selectedConfigurationName):
    GuideletWidget.onConfigurationChanged(self, selectedConfigurationName)

  def createGuideletInstance(self):
    return EpiGuideGuidelet(None, self.guideletLogic, self.selectedConfigurationName)

  def createGuideletLogic(self):
    return EpiGuideLogic()

# -----------------------------------------------------
# EpiGuideLogic ###
# -----------------------------------------------------
class EpiGuideLogic(GuideletLogic):
  """Uses GuideletLogic base class, available at:
  """  # TODO add path

  def __init__(self, parent=None):
    GuideletLogic.__init__(self, parent)

  def addValuesToDefaultConfiguration(self):
    GuideletLogic.addValuesToDefaultConfiguration(self)
    moduleDir = os.path.dirname(slicer.modules.epiguide.path)
    defaultSavePathOfEpiGuide = os.path.join(moduleDir, 'SavedScenes')
    settingList = {'TipToSurfaceDistanceTextScale': '3',
             'TipToSurfaceDistanceTrajectory': 'True',
             #'NeedleModelToNeedleTip': '0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 1.0 0.0 0.0 0.0 0 0 0 1',
             #'TrajModelToNeedleTip': '0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 1.0 0.0 0.0 0.0 0 0 0 1',
             'NeedleModelToNeedleTip': '1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1',
             'TrajModelToNeedleTip': '1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1',
             'SphereModelToNeedleTip': '1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1',
             'TestMode': 'False',
             'SavedScenesDirectory': defaultSavePathOfEpiGuide
             }
    self.updateSettings(settingList, 'Default')

# -----------------------------------------------------
#	EpiGuideTest ###
# -----------------------------------------------------
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
    self.setTipToReferenceTransformNode = None
    self.firstPeakNode = None
    self.secondPeakNode = None
    self.thirdPeakNode = None
    self.firstPeakModelNode = None
    self.secondPeakModelNode = None
    self.thirdPeakModelNode = None
    self.trajectoryModel_needleModel = None
    self.trajectoryModel_needleTip = None

    n = slicer.mrmlScene.AddNode(slicer.vtkMRMLIGTLConnectorNode())
    n.SetTypeClient('129.100.44.102', 18944)
    n.Start()

    slicer.app.processEvents()
    self.needleModelTipRadius = 0.0

    # Set up main frame
    self.sliceletDockWidget.setObjectName('EpiGuidePanel')
    self.sliceletDockWidget.setWindowTitle('EpiGuideNav')
    self.mainWindow.setWindowTitle('Epidural injection navigation')

    self.setupScene()

    self.navigationView = self.VIEW_TRIPLE_3D # should we change to VIEW_ULTRASOUND_3D_3DCHART ???

    qt.QTimer().singleShot(500, self.assurePeaksParented)

  def assurePeaksParented(self):
    # Check every 1/2 second if the transforms exist, if they do, parent them and stop checking
    if self.findPeakTransforms() == False:
      slicer.app.processEvents()
      qt.QTimer().singleShot(500, self.assurePeaksParented)
      return

    self.parentPeakTransforms(self.needleTipToNeedle,
                              self.firstPeakToSETTipTransformNode,
                              self.secondPeakToSETTipTransformNode,
                              self.thirdPeakToSETTipTransformNode)

  def createFeaturePanels(self):
    # Create GUI panels.
    featurePanelList = Guidelet.createFeaturePanels(self)

    self.navigationCollapsibleButton = ctk.ctkCollapsibleButton()

    featurePanelList[len(featurePanelList):] = [self.navigationCollapsibleButton]

    return featurePanelList

  def __del__(self):
    self.cleanup()

  def cleanup(self):
    Guidelet.cleanup(self)
    logging.debug('cleanup')

  def setupConnections(self):
    logging.debug('EpiGuide.setupConnections()')
    Guidelet.setupConnections(self)

    self.navigationCollapsibleButton.connect('toggled(bool)', self.onNavigationPanelToggled)
    import Viewpoint

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
        #m = self.logic.createMatrixFromString('1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1')
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

    self.trajModelToNeedleTip = slicer.util.getNode('TrajModelToNeedleTip')
    if not self.trajModelToNeedleTip:
      self.trajModelToNeedleTip = slicer.vtkMRMLLinearTransformNode()
      self.trajModelToNeedleTip.SetName("TrajModelToNeedleTip")
      m = self.logic.readTransformFromSettings('TrajModelToNeedleTip', self.configurationName)
      if m:
        self.trajModelToNeedleTip.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.trajModelToNeedleTip)

    self.sphereModelToNeedleTip = slicer.util.getNode('SphereModelToNeedleTip')
    if not self.sphereModelToNeedleTip:
      self.sphereModelToNeedleTip = slicer.vtkMRMLLinearTransformNode()
      self.sphereModelToNeedleTip.SetName("SphereModelToNeedleTip")
      m = self.logic.readTransformFromSettings('SphereModelToNeedleTip', self.configurationName)
      if m:
        self.sphereModelToNeedleTip.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.sphereModelToNeedleTip)

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
      # length, radius, tipradius, bool markers, vtkMRMLModelNode(1 or 0: creates a ring close to tip)
      slicer.modules.createmodels.logic().CreateNeedle(65, 1.0, self.needleModelTipRadius, 0)
      self.needleModel_NeedleTip = slicer.util.getNode(pattern="NeedleModel")
      self.needleModel_NeedleTip.GetDisplayNode().SetColor(1,0,1)#(0.08, 0.84, 0.1)#(1,0,0)#
      self.needleModel_NeedleTip.SetName("NeedleModel")
      self.needleModel_NeedleTip.GetDisplayNode().SliceIntersectionVisibilityOn()


    self.trajectoryModel_needleModel = slicer.util.getNode('TrajectoryModel')
    cylinderLength = 100
    if not self.trajectoryModel_needleModel:
      self.trajectoryModel_needleModel = slicer.modules.createmodels.logic().CreateCylinder(cylinderLength, 0.2)  # 0.5mm tall, 4mm radius
      self.trajectoryModel_needleModel.SetName('TrajectoryModel')
      self.trajectoryModel_needleModel.GetDisplayNode().SetColor(1, 1, 0.5)
      # here, we want to bake in a transform to move the origin of the cylinder to one of the ends (intead
      # of being in the middle)
      transformFilter = vtk.vtkTransformPolyDataFilter()
      transformFilter.SetInputConnection(self.trajectoryModel_needleModel.GetPolyDataConnection())
      trans = vtk.vtkTransform()
      trans.Translate(0, 0, cylinderLength/2)
      transformFilter.SetTransform(trans)
      transformFilter.Update()
      self.trajectoryModel_needleModel.SetPolyDataConnection(transformFilter.GetOutputPort())

    #number of balls = cylinderLength / distance between markers (may be -1, depending on ball at tip (giggggity))
    number_spheres = cylinderLength/10
    for i in range(0,number_spheres):
      #  create sphere model
      self.sphereModel_needleModel = slicer.util.getNode('SphereModel')
      self.sphereModel_needleModel  = slicer.modules.createmodels.logic().CreateSphere(0.7)  # 0.5mm tall, 4mm radius
      self.sphereModel_needleModel.SetName('SphereModel')
      #self.sphereModel_needleModel .GetDisplayNode().SetColor(0.92, 0.84, 0.92)
      prcentage = (number_spheres -i)/10
      R = 1.0
      G = 1.0
      B = 0.1 + i * (0.6/(number_spheres-1.0)) # yellow spectrum ranging from 0.1-0.7
      # R = i*1.0 / number_spheres*1.0
      # G = (number_spheres*1.0 - i*1.0)/number_spheres*1.0
      # B = 0.0
      self.sphereModel_needleModel.GetDisplayNode().SetColor(R, G, B)

    # # create transform node, apply z translation i*distanceBetweenMarkers
      sphereTransformFilter = vtk.vtkTransformPolyDataFilter()
      sphereTransformFilter.SetInputConnection(self.sphereModel_needleModel.GetPolyDataConnection())
      sphereTrans = vtk.vtkTransform()
      sphereTrans.Translate(0, 0, (i+1)*10)
      sphereTransformFilter.SetTransform(sphereTrans)
      sphereTransformFilter.Update()
      self.sphereModel_needleModel.SetPolyDataConnection(sphereTransformFilter.GetOutputPort())
    #
      self.needleToReference.SetAndObserveTransformNodeID(self.referenceToRas.GetID())
      self.needleTipToNeedle.SetAndObserveTransformNodeID(self.needleToReference.GetID())
      self.sphereModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
      self.sphereModel_needleModel.SetAndObserveTransformNodeID(self.sphereModelToNeedleTip.GetID())


    #  parent sphere model to new transform node
    #  parent new transform node to NeedleTipToNeedle
    #  dance like no one is watching (I'm watching...)
    #  get model display node from new model
    #  set colour of display node to some algorithm
    #    three colour linear interpolation is what I did, you can do otherwise

    # self.sphereModel = slicer.util.getNode('sphereModel')
    # if not self.sphereModel:
    #   self.sphereModel = slicer.modules.createmodels.logic().CreateSphere(5)  # 0.5mm tall, 4mm radius
    #   self.sphereModel.SetName('sphereModel')
    #   self.sphereModel.GetDisplayNode().SetColor(1, 1, 0)


    # Build transform tree
    logging.debug('Set up transform tree')
    self.needleToReference.SetAndObserveTransformNodeID(self.referenceToRas.GetID())
    self.needleTipToNeedle.SetAndObserveTransformNodeID(self.needleToReference.GetID())
    self.needleModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
    self.needleModel_NeedleTip.SetAndObserveTransformNodeID(self.needleModelToNeedleTip.GetID())
    #self.liveUltrasoundNode_Reference.SetAndObserveTransformNodeID(self.referenceToRas.GetID()) # always commented out

    # self.needleToReference.SetAndObserveTransformNodeID(self.referenceToRas.GetID())
    # self.needleTipToNeedle.SetAndObserveTransformNodeID(self.needleToReference.GetID())
    # self.needleModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
    self.trajModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
    self.trajectoryModel_needleModel.SetAndObserveTransformNodeID(self.trajModelToNeedleTip.GetID())

    # Hide slice view annotations (patient name, scale, color bar, etc.) as they
    # decrease reslicing performance by 20%-100%
    logging.debug('Hide slice view annotations')
    import DataProbe
    dataProbeUtil = DataProbe.DataProbeLib.DataProbeUtil()
    dataProbeParameterNode = dataProbeUtil.getParameterNode()
    dataProbeParameterNode.SetParameter('showSliceViewAnnotations', '0')

    self.loadPeakModels()

  def disconnect(self):  # TODO see connect
    logging.debug('EpiGuide.disconnect()')
    Guidelet.disconnect(self)

  # Remove observer to old parameter node
    self.navigationCollapsibleButton.disconnect('toggled(bool)', self.onNavigationPanelToggled)

  def onUltrasoundPanelToggled(self, toggled):
    Guidelet.onUltrasoundPanelToggled(self, toggled)
    # The user may want to freeze the image (disconnect) to make contouring easier.
    # Disable automatic ultrasound image auto-fit when the user unfreezes (connect)
    # to avoid zooming out of the image.
    self.fitUltrasoundImageToViewOnConnect = not toggled

  def getViewNode(self, viewName):
    """
  Get the view node for the selected 3D view
  """
    logging.debug("getViewNode")
    viewNode = slicer.util.getNode(viewName)
    return viewNode


  def updateNavigationView(self):
    logging.debug("updateNavigationView")
    self.selectView(self.navigationView)

  def onNavigationPanelToggled(self, toggled):
    logging.debug("onNavigationPanelToggled")

    if toggled == False:
      return

    logging.debug('onNavigationPanelToggled')
    self.updateNavigationView()

    # Stop live ultrasound.
    if self.connectorNode != None:
      self.connectorNode.Stop()
    
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

    inc = 1000 * 1480 / (2 * 420e6)  # distance in mm. The delay distance is added to the increments.  (2e-6*1480/2) +
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


  def loadPeakModels(self):
    # Calling this function will ask SlicerIGT's create models to create 3 disks (short cylinders),
    #
    # To make this more advanced, you could have it clean up any existing models (look for by name using slicer.util.getNode)
    # so you could call this repeatedly. However, best to just call this once (in init or setup)
    if self.firstPeakModelNode is None:
      self.firstPeakModelNode = slicer.util.getNode('FirstPeakModel')
      if self.firstPeakModelNode is None:
        self.firstPeakModelNode = slicer.modules.createmodels.logic().CreateCylinder(0.5, 4)  # 0.5mm tall, 4mm radius
        self.firstPeakModelNode.SetName('FirstPeakModel')
        self.firstPeakModelNode.GetDisplayNode().SetColor(1.0, 0.0, 0.0)  # r, g, b [0.0,1.0]

    if self.secondPeakModelNode is None:
      self.secondPeakModelNode = slicer.util.getNode('SecondPeakModel')
      if self.secondPeakModelNode is None:
        self.secondPeakModelNode = slicer.modules.createmodels.logic().CreateCylinder(0.5, 4)  # 0.5mm tall, 4mm radius
        self.secondPeakModelNode.SetName('SecondPeakModel')
        self.secondPeakModelNode.GetDisplayNode().SetColor(0.0, 1.0, 0.0)  # r, g, b [0.0,1.0]

    if self.thirdPeakModelNode is None:
      self.thirdPeakModelNode = slicer.util.getNode('ThirdPeakModel')
      if self.thirdPeakModelNode is None:
        self.thirdPeakModelNode = slicer.modules.createmodels.logic().CreateCylinder(0.5, 4)  # 0.5mm tall, 4mm radius
        self.thirdPeakModelNode.SetName('ThirdPeakModel')
        self.thirdPeakModelNode.GetDisplayNode().SetColor(0.0, 0.0, 1.0)  # r, g, b [0.0,1.0]


  def parentPeakTransforms(self, setTipToReferenceTransformNode, firstPeakToSETTipTransformNode,
                        secondPeakToSETTipTransformNode, thirdPeakToSETTipTransformNode):
    # parent each disk to a peak transform, and parent each peak transform to the setTipToReference
    # Prior to calling this, you will have to identify which transformNode corresponds to which peak
    # These should be sent from plus as FirstPeakToReference, SecondPeakToReference, etc...
    # To find those, after connecting to Plus (oscilloscope machine)
    #
    # self.firstPeakNode = slicer.util.getNode('FirstPeakToReference')
    # self.secondPeakNode = slicer.util.getNode('SecondPeakToReference')
    # ...
    # then call
    # self.parentPeakTransforms(self.tipToReferenceNode, self.firstPeakNode, self.secondPeakNode, self.thirdPeakNode)
    if firstPeakToSETTipTransformNode is None:
      logging.Debug("first peak null")
      return
    if secondPeakToSETTipTransformNode is None:
      logging.Debug("second peak null")
      return
    if thirdPeakToSETTipTransformNode is None:
      logging.Debug("third peak null")
      return

    self.firstPeakModelNode.SetAndObserveTransformNodeID(firstPeakToSETTipTransformNode.GetID())
    firstPeakToSETTipTransformNode.SetAndObserveTransformNodeID(setTipToReferenceTransformNode.GetID())

    self.secondPeakModelNode.SetAndObserveTransformNodeID(secondPeakToSETTipTransformNode.GetID())
    secondPeakToSETTipTransformNode.SetAndObserveTransformNodeID(setTipToReferenceTransformNode.GetID())

    self.thirdPeakModelNode.SetAndObserveTransformNodeID(thirdPeakToSETTipTransformNode.GetID())
    thirdPeakToSETTipTransformNode.SetAndObserveTransformNodeID(setTipToReferenceTransformNode.GetID())

  def findPeakTransforms(self):
    # Try to find peaks
    self.firstPeakToSETTipTransformNode = slicer.util.getNode('FirstPeakToNeedleTip')
    if self.firstPeakToSETTipTransformNode is None:
      # Cannot find a peak, this is not the connector you're looking for
      return False

    # Note the missing p at the end, OpenIGTLink has a maxmimum character count of 20
    self.secondPeakToSETTipTransformNode = slicer.util.getNode('SecondPeakToNeedleTi')
    if self.secondPeakToSETTipTransformNode is None:
      # Cannot find a peak, this is not the connector you're looking for
      return False

    self.thirdPeakToSETTipTransformNode = slicer.util.getNode('ThirdPeakToNeedleTip')
    if self.thirdPeakToSETTipTransformNode is None:
      # Cannot find a peak, this is not the connector you're looking for
      return False

    return True

  # this will not work, because this is onConnectorNodeConnected for the 'default' connector node, not our
  # secondary one
  def onConnectorNodeConnected(self, caller, event, force=False):
    Guidelet.onConnectorNodeConnected(self, caller, event, force)

    if self.findPeakTransforms() == False:
      return

    if self.needleTipToNeedle is None:
      # Needle tip transform not available
      return

    self.parentPeakTransforms(self.needleTipToNeedle,
                              self.firstPeakToSETTipTransformNode,
                              self.secondPeakToSETTipTransformNode,
                              self.thirdPeakToSETTipTransformNode)