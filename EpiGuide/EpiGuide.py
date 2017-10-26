import logging, os

from __main__ import vtk, qt, ctk, slicer

from Guidelet import Guidelet, GuideletLoadable, GuideletLogic, GuideletTest, GuideletWidget
from PlusRemote import PlusRemoteLogic

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
        self.parent.contributors = ["Golafsoun Ameri (Robarts Research Institute), Adam Rankin (Robarts Research Institute)"]
        self.parent.helpText = """This guidelet performs image guided navigation for epidural needle insertions. Requires Plus connections to an image and tracking server, as well as a single element transducer server."""
        self.parent.acknowledgementText = """This file was originally developed by Golafsoun Ameri and Adam Rankin, Robarts Research Institute and was partially funded by XYZ."""

# -----------------------------------------------------
#	EpiGuideGuidelet ###
# -----------------------------------------------------
class EpiGuideGuidelet(Guidelet):
    VIEW_ULTRASOUND_3D_3DCHART = unicode('Ultrasound + 3D + Chart')

    @staticmethod
    def printCommandResponse(command, q):
        statusText = "Command {0} [{1}]: {2}\n".format(command.GetCommandName(), command.GetID(), command.StatusToString(command.GetStatus()))
        if command.GetResponseMessage():
            statusText = statusText + command.GetResponseMessage()
        elif command.GetResponseText():
            statusText = statusText + command.GetResponseText()
        print statusText


    def __init__(self, parent, logic, configurationName='Default'):
        Guidelet.__init__(self, parent, logic, configurationName)
        logging.debug('EpiGuideGuidelet.__init__')
        self.logic.addValuesToDefaultConfiguration()

        self.navigationCollapsibleButton = None

        self.imageData = None
        self.imageDimensions = None
        self.line = None
        self.table = None
        self.chart = None
        self.view = None
        self.signalArray = None
        self.distanceArray = None
        self.boundsRecalculated = False
        self.fitUltrasoundImageToViewOnConnect = True

        self.firstPeakToSETTipTransformNode = None
        self.secondPeakToSETTipTransformNode = None
        self.thirdPeakToSETTipTransformNode = None

        self.firstPeakModelNode = None
        self.secondPeakModelNode = None
        self.thirdPeakModelNode = None

        self.needleWithTipModel = None
        self.trajectoryModel_needleModel = None
        self.trajectoryModel_needleTip = None

        self.slice3DChartCustomLayoutId = 5000

        self.referenceToRasTransform = None
        self.needleTipToNeedleTransform = None
        self.needleModelToNeedleTipTransform = None
        self.trajModelToNeedleTipTransform = None
        self.sphereModelToNeedleTipTransform = None
        self.needleToReferenceTransform = None
        self.setTipToReferenceTransformNode = None

        self.aModeImageNode = None

        self.timer = qt.QTimer()

        self.agilentCommandLogic = PlusRemoteLogic()
        self.agilentConnectorNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLIGTLConnectorNode())

        agilentServerHostNamePort = slicer.app.userSettings().value(self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/AgilentServerHostNamePort')
        [hostName, port] = agilentServerHostNamePort.split(':')

        self.agilentConnectorNode.SetTypeClient(hostName, port)
        self.agilentConnectorNode.Start()

        self.needleModelTipRadius = 0.0

        # Set up main frame
        self.sliceletDockWidget.setObjectName('EpiGuidePanel')
        self.sliceletDockWidget.setWindowTitle('EpiGuideNav')
        self.mainWindow.setWindowTitle('Epidural injection navigation')

        self.navigationView = self.VIEW_TRIPLE_3D  # should we change to VIEW_ULTRASOUND_3D_3DCHART ???

        # qt.QTimer().singleShot(500, self.assurePeaksParented) # 500

    def assurePeaksParented(self):
        # Check every 1/2 second if the transforms exist, if they do, parent them and stop checking
        if not self.findPeakTransforms():
            slicer.app.processEvents()
            qt.QTimer().singleShot(500, self.assurePeaksParented) # 500ms
            return
        self.parentPeakTransforms(self.needleTipToNeedleTransform,
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

        self.navigationCollapsibleButton = None

        self.imageData = None
        self.imageDimensions = None
        self.line = None
        self.table = None
        self.chart = None
        self.view = None
        self.signalArray = None
        self.distanceArray = None
        self.boundsRecalculated = False
        self.fitUltrasoundImageToViewOnConnect = True

        self.firstPeakToSETTipTransformNode = None
        self.secondPeakToSETTipTransformNode = None
        self.thirdPeakToSETTipTransformNode = None

        self.firstPeakModelNode = None
        self.secondPeakModelNode = None
        self.thirdPeakModelNode = None

        self.needleWithTipModel = None
        self.trajectoryModel_needleModel = None
        self.trajectoryModel_needleTip = None

        self.slice3DChartCustomLayoutId = 5000

        self.referenceToRasTransform = None
        self.needleTipToNeedleTransform = None
        self.needleModelToNeedleTipTransform = None
        self.trajModelToNeedleTipTransform = None
        self.sphereModelToNeedleTipTransform = None
        self.needleToReferenceTransform = None
        self.setTipToReferenceTransformNode = None

        self.aModeImageNode = None

        self.timer.Stop()
        self.timer = None

        self.agilentCommandLogic = None
        self.agilentConnectorNode.Stop()
        self.agilentConnectorNode = None

    def cleanup(self):
        Guidelet.cleanup(self)
        logging.debug('cleanup')

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
        layoutLogic.GetLayoutNode().AddLayoutDescription(self.slice3DChartCustomLayoutId, customLayout)

    def setupScene(self):  # applet specific
        logging.debug('setupScene')

        # Add a Qt timer, that fires every X ms (16.7ms = 60 FPS, 33ms = 30FPS)
        # Connect the timeout() signal of the qt timer to a function in this class that you will write
        self.timer.connect('timeout()', self.OnTimerTimeout)
        self.timer.start(16.7)

        # ReferenceToRas is needed for ultrasound initialization, so we need to
        # set it up before calling Guidelet.setupScene().
        self.referenceToRasTransform = slicer.util.getNode('ReferenceToRas')
        if not self.referenceToRasTransform:
            self.referenceToRasTransform = slicer.vtkMRMLLinearTransformNode()
            self.referenceToRasTransform.SetName("ReferenceToRas")
            m = self.logic.readTransformFromSettings('ReferenceToRas', self.configurationName)
            if m is None:
                # Create identity matrix
                m = self.logic.createMatrixFromString('1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1')
            self.referenceToRasTransform.SetMatrixTransformToParent(m)
            slicer.mrmlScene.AddNode(self.referenceToRasTransform)

        Guidelet.setupScene(self)

        logging.debug('Create transforms')
        # Coordinate system definitions: https://app.assembla.com/spaces/slicerigt/wiki/Coordinate_Systems

        self.needleTipToNeedleTransform = slicer.util.getNode('NeedleTipToNeedle')
        if not self.needleTipToNeedleTransform:
            self.needleTipToNeedleTransform = slicer.vtkMRMLLinearTransformNode()
            self.needleTipToNeedleTransform.SetName("NeedleTipToNeedle")
            m = self.logic.readTransformFromSettings('NeedleTipToNeedle', self.configurationName)
            if m:
                self.needleTipToNeedleTransform.SetMatrixTransformToParent(m)
            slicer.mrmlScene.AddNode(self.needleTipToNeedleTransform)

        self.needleModelToNeedleTipTransform = slicer.util.getNode('NeedleModelToNeedleTip')
        if not self.needleModelToNeedleTipTransform:
            self.needleModelToNeedleTipTransform = slicer.vtkMRMLLinearTransformNode()
            self.needleModelToNeedleTipTransform.SetName("NeedleModelToNeedleTip")
            m = self.logic.readTransformFromSettings('NeedleModelToNeedleTip', self.configurationName)
            if m:
                self.needleModelToNeedleTipTransform.SetMatrixTransformToParent(m)
            slicer.mrmlScene.AddNode(self.needleModelToNeedleTipTransform)

        self.trajModelToNeedleTipTransform = slicer.util.getNode('TrajModelToNeedleTip')
        if not self.trajModelToNeedleTipTransform:
            self.trajModelToNeedleTipTransform = slicer.vtkMRMLLinearTransformNode()
            self.trajModelToNeedleTipTransform.SetName("TrajModelToNeedleTip")
            m = self.logic.readTransformFromSettings('TrajModelToNeedleTip', self.configurationName)
            if m:
                self.trajModelToNeedleTipTransform.SetMatrixTransformToParent(m)
            slicer.mrmlScene.AddNode(self.trajModelToNeedleTipTransform)

        self.sphereModelToNeedleTipTransform = slicer.util.getNode('SphereModelToNeedleTip')
        if not self.sphereModelToNeedleTipTransform:
            self.sphereModelToNeedleTipTransform = slicer.vtkMRMLLinearTransformNode()
            self.sphereModelToNeedleTipTransform.SetName("SphereModelToNeedleTip")
            m = self.logic.readTransformFromSettings('SphereModelToNeedleTip', self.configurationName)
            if m:
                self.sphereModelToNeedleTipTransform.SetMatrixTransformToParent(m)
            slicer.mrmlScene.AddNode(self.sphereModelToNeedleTipTransform)

        # Create transforms that will be updated through OpenIGTLink
        self.needleToReferenceTransform = slicer.util.getNode('NeedleToReference')
        if not self.needleToReferenceTransform:
            self.needleToReferenceTransform = slicer.vtkMRMLLinearTransformNode()
            self.needleToReferenceTransform.SetName("NeedleToReference")
            slicer.mrmlScene.AddNode(self.needleToReferenceTransform)

        # Models
        logging.debug('Create models')

        self.needleWithTipModel = slicer.util.getNode('NeedleModel')
        if not self.needleWithTipModel:
            # length, radius, tipradius, bool markers, vtkMRMLModelNode(1 or 0: creates a ring close to tip)
            # length, radius, tipradius, bool markers, vtkMRMLModelNode(1 or 0: creates a ring close to tip)
            slicer.modules.createmodels.logic().CreateNeedle(65, 1.0, self.needleModelTipRadius, 0)
            self.needleWithTipModel = slicer.util.getNode(pattern="NeedleModel")
            self.needleWithTipModel.GetDisplayNode().SetColor(0.08, 0.84, 0.1)  # (1,0,1)#
            self.needleWithTipModel.SetName("NeedleModel")
            self.needleWithTipModel.GetDisplayNode().SliceIntersectionVisibilityOn()

        self.trajectoryModel_needleModel = slicer.util.getNode('TrajectoryModel')
        cylinderLength = 100
        if not self.trajectoryModel_needleModel:
            self.trajectoryModel_needleModel = slicer.modules.createmodels.logic().CreateCylinder(cylinderLength,
                                                                                                  0.1)  # 0.5mm tall, 4mm radius
            self.trajectoryModel_needleModel.SetName('TrajectoryModel')
            self.trajectoryModel_needleModel.GetDisplayNode().SetColor(0.69, 0.93, 0.93)  # (1, 1, 0.5)
            # here, we want to bake in a transform to move the origin of the cylinder to one of the ends (intead
            # of being in the middle)
            transformFilter = vtk.vtkTransformPolyDataFilter()
            transformFilter.SetInputConnection(self.trajectoryModel_needleModel.GetPolyDataConnection())
            trans = vtk.vtkTransform()
            trans.Translate(0, 0, cylinderLength / 2)
            transformFilter.SetTransform(trans)
            transformFilter.Update()
            self.trajectoryModel_needleModel.SetPolyDataConnection(transformFilter.GetOutputPort())

        # number of balls = cylinderLength / distance between markers (may be -1, depending on ball at tip (giggggity))
        number_spheres = cylinderLength / 10
        for i in range(0, number_spheres):
            # create sphere model if non-existent
            model = slicer.util.getNode('DistanceMarkerModel_'+str(i))
            if model is None:
                model = slicer.modules.createmodels.logic().CreateSphere(0.7)
                model.SetName('DistanceMarkerModel_'+str(i))
                R = 1.0
                G = 1.0
                B = 0.1 + i * (0.7 / (number_spheres - 1.0))  # yellow spectrum ranging from 0.1-0.7
                model.GetDisplayNode().SetColor(R, G, B)

            # create transform node, apply z translation i*distanceBetweenMarkers
            sphereTransformFilter = vtk.vtkTransformPolyDataFilter()
            sphereTransformFilter.SetInputConnection(self.sphereModel_needleModel.GetPolyDataConnection())
            sphereTrans = vtk.vtkTransform()
            sphereTrans.Translate(0, 0, (i + 1) * 10)
            sphereTransformFilter.SetTransform(sphereTrans)
            sphereTransformFilter.Update()
            self.sphereModel_needleModel.SetPolyDataConnection(sphereTransformFilter.GetOutputPort())

            self.needleToReferenceTransform.SetAndObserveTransformNodeID(self.referenceToRasTransform.GetID())
            self.needleTipToNeedleTransform.SetAndObserveTransformNodeID(self.needleToReferenceTransform.GetID())
            self.sphereModelToNeedleTipTransform.SetAndObserveTransformNodeID(self.needleTipToNeedleTransform.GetID())
            self.sphereModel_needleModel.SetAndObserveTransformNodeID(self.sphereModelToNeedleTipTransform.GetID())

        # Build transform tree
        logging.debug('Set up transform tree')
        self.needleModelToNeedleTipTransform.SetAndObserveTransformNodeID(self.needleTipToNeedleTransform.GetID())
        self.needleWithTipModel.SetAndObserveTransformNodeID(self.needleModelToNeedleTipTransform.GetID())
        # self.liveUltrasoundNode_Reference.SetAndObserveTransformNodeID(self.referenceToRasTransform.GetID()) # always commented out

        # self.needleToReferenceTransform.SetAndObserveTransformNodeID(self.referenceToRasTransform.GetID())
        # self.needleTipToNeedleTransform.SetAndObserveTransformNodeID(self.needleToReferenceTransform.GetID())
        # self.needleModelToNeedleTipTransform.SetAndObserveTransformNodeID(self.needleTipToNeedleTransform.GetID())
        self.trajModelToNeedleTipTransform.SetAndObserveTransformNodeID(self.needleTipToNeedleTransform.GetID())
        self.trajectoryModel_needleModel.SetAndObserveTransformNodeID(self.trajModelToNeedleTipTransform.GetID())

        # Hide slice view annotations (patient name, scale, color bar, etc.) as they
        # decrease re-slicing performance by 20%-100%
        # logging.debug('Hide slice view annotations')
        # import DataProbe
        # dataProbeUtil = DataProbe.DataProbeLib.DataProbeUtil()
        # dataProbeParameterNode = dataProbeUtil.getParameterNode()
        # dataProbeParameterNode.SetParameter('showSliceViewAnnotations', '0')

        # self.loadPeakModels()

    def setupConnections(self):
        logging.debug('EpiGuide.setupConnections()')
        Guidelet.setupConnections(self)

        self.navigationCollapsibleButton.connect('toggled(bool)', self.onNavigationPanelToggled)
        # Add our own behaviour (in addition to the default behavior) of the Ultrasound record button
        self.ultrasound.startStopRecordingButton.connect('clicked(bool)', self.onStartStopRecordingButtonClicked)

        ### Camera Sep8.17 ###
        # self.leftBullseyeCameraButton.connect('clicked()', lambda: self.onCameraButtonClicked('View1'))

    def disconnect(self):
        # see setupConnections
        logging.debug('EpiGuide.disconnect()')
        Guidelet.disconnect(self)

        # Remove observer to old parameter node
        self.navigationCollapsibleButton.disconnect('toggled(bool)', self.onNavigationPanelToggled)
        self.ultrasound.startStopRecordingButton.disconnect('clicked(bool)', self.onStartStopRecordingButtonClicked)

    def onStartStopRecordingButtonClicked(self):
        # You can create a intelligent file name based on participant, trial #, etc... (you may have to create a UI)
        # or you can just send a dummy filename and rename it later
        if self.ultrasound.startStopRecordingButton.isChecked():
            self.agilentCommandLogic.startRecording(self.agilentConnectorNode.GetID(),
                                                    self.ultrasound.captureDeviceName, 'agilent.nrrd', True,
                                                    self.printCommandResponse)
        else:
            self.agilentCommandLogic.stopRecording(self.agilentConnectorNode.GetID(), self.ultrasound.captureDeviceName,
                                                   self.printCommandResponse)

    def onUltrasoundPanelToggled(self, toggled):
        Guidelet.onUltrasoundPanelToggled(self, toggled)
        # The user may want to freeze the image (disconnect) to make contouring easier.
        # Disable automatic ultrasound image auto-fit when the user unfreezes (connect)
        # to avoid zooming out of the image.
        self.fitUltrasoundImageToViewOnConnect = not toggled

    def updateNavigationView(self):
        logging.debug("updateNavigationView")
        self.selectView(self.navigationView)

    def onNavigationPanelToggled(self, toggled):
        logging.debug("onNavigationPanelToggled")

        if not toggled:
            return

        logging.debug('onNavigationPanelToggled')
        self.updateNavigationView()

        # Stop live ultrasound.
        if not self.connectorNode is None:
            self.connectorNode.Stop()

    def setupViewerLayouts(self):
        Guidelet.setupViewerLayouts(self)
        # Now we can add our own layout to the drop down list
        self.viewSelectorComboBox.addItem(self.VIEW_ULTRASOUND_3D_3DCHART)

    def populateChart(self):
        # strip elements from 2nd 3d view
        # and add our own chart renderer to it
        self.aModeImageNode = slicer.util.getNode('Image_NeedleTip')
        if self.aModeImageNode is None:
            logging.debug("Cannot locate Image_NeedleTip, can't visualize chart")
            return

        self.imageData = self.aModeImageNode.GetImageData()

        if not self.table is None:
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
        # self.chart.RecalculateBounds() # either here or in OnTimerTimeout

    def onViewSelect(self, layoutIndex):
        # Check out layout request first, then pass on to parent to handle the existing ones
        text = self.viewSelectorComboBox.currentText
        if text == self.VIEW_ULTRASOUND_3D_3DCHART:
            # self.layoutManager.setLayout(self.slice3DChartCustomLayoutId)
            # self.delayedFitUltrasoundImageToView() # (8.30.17) may want to add this, but no change:
            # self.showUltrasoundIn3dView(True)
            # ####### this should keep the 2 panel
            self.layoutManager.setLayout(self.red3dCustomLayoutId)
            self.delayedFitUltrasoundImageToView()
            self.showUltrasoundIn3dView(True)
            # ######
            self.populateChart()
            return

        Guidelet.onViewSelect(self, layoutIndex)

    def OnTimerTimeout(self):
        if self.imageData is None or self.imageDimensions is None:
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
            return
        if secondPeakToSETTipTransformNode is None:
            return
        if thirdPeakToSETTipTransformNode is None:
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
    # def onConnectorNodeConnected(self, caller, event, force=False):
    #   Guidelet.onConnectorNodeConnected(self, caller, event, force)
    #
    #   if self.findPeakTransforms() == False:
    #     return
    #
    #   if self.needleTipToNeedleTransform is None:
    #     # Needle tip transform not available
    #     return
    #
    #   self.parentPeakTransforms(self.needleTipToNeedleTransform,
    #                             self.firstPeakToSETTipTransformNode,
    #                             self.secondPeakToSETTipTransformNode,
    #                             self.thirdPeakToSETTipTransformNode)

# -----------------------------------------------------
# EpiGuideLogic ###
# -----------------------------------------------------
class EpiGuideLogic(GuideletLogic):
    """Uses GuideletLogic base class, available at:"""

    def __init__(self, parent=None):
        GuideletLogic.__init__(self, parent)

    def addValuesToDefaultConfiguration(self):
        GuideletLogic.addValuesToDefaultConfiguration(self)
        moduleDir = os.path.dirname(slicer.modules.epiguide.path)
        defaultSavePathOfEpiGuide = os.path.join(moduleDir, 'SavedScenes')
        settingList = {'TipToSurfaceDistanceTextScale': '3',
             'TipToSurfaceDistanceTrajectory': 'True',
             'NeedleModelToNeedleTip': '1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1',
             'TrajModelToNeedleTip': '1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1',
             'SphereModelToNeedleTip': '1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0 0 0 1',
             'TestMode': 'False',
             'AgilentServerHostNamePort': 'localhost:18945',
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
        """Run as few or as many tests as needed here."""
        GuideletTest.runTest(self)
        # self.test_EpiGuide1() #add applet specific tests here

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
        # Add the second Plus connection info entry
        try:
            slicer.modules.plusremote
        except:
            return

        self.agilentServerHostNamePortLineEdit = qt.QLineEdit()
        leLabel = qt.QLabel()
        leLabel.setText("Set the Agilent Plus Server Host and Name Port:")
        hbox = qt.QHBoxLayout()
        hbox.addWidget(leLabel)
        hbox.addWidget(self.agilentServerHostNamePortLineEdit)
        self.launcherFormLayout.addRow(hbox)

        lnNode = slicer.util.getNode(self.moduleName)
        if lnNode is not None and lnNode.GetParameter('AgilentServerHostNamePort'):
            # logging.debug("There is already a connector PlusServerHostNamePort parameter " + lnNode.GetParameter('PlusServerHostNamePort'))
            self.agilentServerHostNamePortLineEdit.setDisabled(True)
            self.agilentServerHostNamePortLineEdit.setText(lnNode.GetParameter('AgilentServerHostNamePort'))
        else:
            agilentServerHostNamePort = slicer.app.userSettings().value(self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/AgilentServerHostNamePort')
            self.agilentServerHostNamePortLineEdit.setText(agilentServerHostNamePort)

        self.agilentServerHostNamePortLineEdit.connect('editingFinished()', self.onAgilentServerPreferencesChanged)

    def addConfigurationsSelector(self):
        pass

    def onAgilentServerPreferencesChanged(self):
        self.guideletLogic.updateSettings({'AgilentServerHostNamePort': self.agilentServerHostNamePortLineEdit.text}, self.selectedConfigurationName)

    def onConfigurationChanged(self, selectedConfigurationName):
        GuideletWidget.onConfigurationChanged(self, selectedConfigurationName)

    def createGuideletInstance(self):
        return EpiGuideGuidelet(None, self.guideletLogic, self.selectedConfigurationName)

    def createGuideletLogic(self):
        return EpiGuideLogic()