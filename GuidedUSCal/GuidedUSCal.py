import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import re
import SimpleITK as sitk
import numpy as np 

# This is the basis of your module and will load the basic module GUI 
class GuidedUSCal(ScriptedLoadableModule):
  # comment string showing where to obtain this 
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """ 
  #define some things about your module here 
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    #Module title 
    self.parent.title= "US Calibration Module"
    #where in the module list it will appear 
    self.parent.categories=["IGT"]
    #who wrote it 
    self.parent.contributors=["Leah Groves"]
    # discriptor string telling what the module does 
    self.parent.helpText="""
This is a scripted loadable module that performs Ultrsound Calibration
"""
    self.parent.helpText = self.getDefaultModuleDocumentationLink()
  
#this contains the widget (GUI) portion of the code         
class GuidedUSCalWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, parent=None):
    # set variables here
    ScriptedLoadableModuleWidget.__init__(self, parent)
    #sets important variable equal to None 
    self.fiducialNode = None
    self.connectorNode = None
    self.sceneObserverTag = None
    self.numFid = None
    self.logic = GuidedUSCalLogic()
    self.resliceLogic = slicer.modules.volumereslicedriver.logic()
    self.imageNode = None
    self.probeNode = None
    self.numFid = 0

    self.isVisualizing = False
    self.outputRegistrationTransformNode = None
    self.inputRegistrationTransformNode = None
    self.NeedleTipToReferenceTransformNode = None

  def setup(self):
    # this is the function that implements all GUI 
    ScriptedLoadableModuleWidget.setup(self)

    slicer.mymod = self
     #This sets the view being used to the red view only 
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
    l=slicer.modules.createmodels.logic()
    self.needle = l.CreateNeedle(150, 1.03, 0, False)
    
	
    #This code block creates a collapsible button 
    #This defines which type of button you are using 
    self.usButton = ctk.ctkCollapsibleButton()
    #This is what the button will say 
    self.usButton.text = "Ultrasound Information"
    #Thiss actually creates that button
    self.layout.addWidget(self.usButton)
    #This creates a variable that describes layout within this collapsible button 
    self.usLayout = qt.QFormLayout(self.usButton)

    #This descirbes the type of widget 
    self.inputIPLineEdit = qt.QLineEdit()
    #This sets a placehoder example of what should be inputted to the line edit 
    self.inputIPLineEdit.setPlaceholderText("127.0.0.1")
    #This is the help tooltip 
    self.inputIPLineEdit.toolTip = "Put the IP address of your ultrasound device here"
    #This is the text that is input inot the line 
    self.usLayout.addRow("Server IP:", self.inputIPLineEdit)

    #This code block is the exact same as the one above only it asks for the server port 
    self.layout.addWidget(self.usButton)
    self.inputPortLineEdit = qt.QLineEdit()
    self.inputPortLineEdit.setPlaceholderText("18944")
    self.inputPortLineEdit.setValidator(qt.QIntValidator())
    self.inputPortLineEdit.toolTip = "Put the Port of your ultrasound device here"
    self.usLayout.addRow("Server Port:", self.inputPortLineEdit)

      #This is a push button 
    self.connectButton = qt.QPushButton()
    self.connectButton.setDefault(False)
    #This button says connect 
    self.connectButton.text = "Connect"
    #help tooltip that explains the funciton 
    self.connectButton.toolTip = "Connects to Ultrasound"
    #adds the widget to the layout 
    self.usLayout.addWidget(self.connectButton)

    # Combobox for image selection
    self.imageSelector = slicer.qMRMLNodeComboBox()
    self.imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.imageSelector.selectNodeUponCreation = True
    self.imageSelector.addEnabled = False
    self.imageSelector.removeEnabled = False
    self.imageSelector.noneEnabled = True
    self.imageSelector.showHidden = False
    self.imageSelector.showChildNodeTypes = False
    self.imageSelector.setMRMLScene( slicer.mrmlScene )
    self.imageSelector.setToolTip( "Pick the image to be used." )
    self.usLayout.addRow("US Volume: ", self.imageSelector)

    self.manualButton = qt.QCheckBox()
    self.manualButton.text = "Select to perform automatic segmentation"
    self.manualButton.toolTip = "This allows the user to select if they want to use the guidance"
    self.usLayout.addRow(self.manualButton)
   
    # This creates another collapsible button
    self.fiducialContainer = ctk.ctkCollapsibleButton()
    self.fiducialContainer.text = "Registration"
    self.fiducialLayout = qt.QFormLayout(self.fiducialContainer)
	
	 #add combo box for linear transform node 
    self.TransformSelector = slicer.qMRMLNodeComboBox()
    self.TransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.TransformSelector.selectNodeUponCreation = True
    self.TransformSelector.addEnabled = False
    self.TransformSelector.removeEnabled = False
    self.TransformSelector.noneEnabled = True
    self.TransformSelector.showHidden = False
    self.TransformSelector.showChildNodeTypes = False
    self.TransformSelector.setMRMLScene( slicer.mrmlScene )
    self.TransformSelector.setToolTip( "Pick the transform representing the straw line." )
    self.fiducialLayout.addRow("Tip to Probe: ", self.TransformSelector)
   
	
	   #This is the exact same as the code block below but it freezes the US to capture a screenshot 
    self.freezeButton = qt.QPushButton()
    self.freezeButton.text = "Freeze"
    self.freezeButton.toolTip = "Freeze the ultrasound image for fiducial placement"
    self.fiducialLayout.addRow(self.freezeButton)
    self.KeySequence = qt.QKeySequence('f')
    self.shortcut = qt.QShortcut(self.KeySequence, slicer.util.mainWindow())
	
    self.numFidLabel = qt.QLabel()
    self.fiducialLayout.addRow(qt.QLabel("Fiducials collected:"), self.numFidLabel)

    self.validationContainer = ctk.ctkCollapsibleButton()
    self.validationContainer.text = "Validation"
    self.validationLayout = qt.QFormLayout(self.validationContainer)

    self.visualizeButton = qt.QPushButton('Show 3D Scene')
    self.visualizeButton.toolTip = "This button enables the 3D view for visual validation"
    self.validationLayout.addRow(self.visualizeButton)
    self.visualizeButton.connect('clicked(bool)', self.onVisualizeButtonClicked)


    self.resetButton = qt.QPushButton('Reset')
    self.resetButton.setDefault(False)
    self.resetButton.toolTip = "This Button Resets the Module"
    self.validationLayout.addRow(self.resetButton)

    # Add the containers to the parent
    self.layout.addWidget(self.usButton)
    self.layout.addWidget(self.fiducialContainer)
    self.layout.addWidget(self.validationContainer)

     # Add vertical spacer
    self.layout.addStretch(1)

    # Connections
    self.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
    self.freezeButton.connect('clicked(bool)', self.onConnectButtonClicked)
    self.shortcut.connect('activated()', self.onConnectButtonClicked)
    self.inputIPLineEdit.connect('textChanged(QString)', self.onInputChanged)
    self.inputPortLineEdit.connect('textChanged(QString)', self.onInputChanged)
    self.imageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)
    self.resetButton.connect('clicked(bool)', self.onResetButtonClicked)

    # Disable buttons until conditions are met
    self.connectButton.setEnabled(False) 
    self.freezeButton.setEnabled(False) 

    self.sceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.onNodeAdded)

    self.outputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.outputRegistrationTransformNode)
    self.outputRegistrationTransformNode.SetName('ImageToProbe')

#this runs when that fiducial node is added 
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAdded(self, caller, event, callData):
    # if the node that is created is of type vtkMRMLMarkupsFiducialNODE 
    if type(callData) is slicer.vtkMRMLMarkupsFiducialNode:
      # if there is something in this node 
      if self.fiducialNode is not None:
        # remove the observer 
        self.fiducialNode.RemoveAllMarkups()
        self.fiducialNode.RemoveObserver(self.markupAddedObserverTag) 
      # set the variable to none 
      self.fiducialNode = None
      #ask adam 
      self.fiducialNode = callData
      #sets a markupObserver to notice when a markup gets added
      self.markupAddedObserverTag = self.fiducialNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onMarkupAdded)
      #this runs the function onMarkupAdded
      self.onMarkupAdded(self.fiducialNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent)
		
  
  #This gets called when the markup is added
  def onMarkupAdded(self, fiducialNodeCaller, event):
    #set the location and index to zero because its needs to be initialized
    centroid=[0,0,0]
    self.numFid = self.numFid + 1 
    #This checks if there is not a display node 
    if self.fiducialNode.GetDisplayNode() is None:
      #then creates one if that is the case 
      self.fiducialNode.CreateDefaultDisplayNodes()
    # this sets a variable as the display node
    displayNode = self.fiducialNode.GetDisplayNode()
    # This sets the type to be a cross hair
    displayNode.SetGlyphType(3)
    #This sets the size
    displayNode.SetGlyphScale(2.5)
    #this says that you dont want text
    displayNode.SetTextScale(0)
    #this sets the color
    displayNode.SetSelectedColor(0, 0, 1)
    # this saves the location the markup is place
    # Collect the point in image space
    self.fiducialNode.GetMarkupPoint(self.fiducialNode.GetNumberOfMarkups()-1,0, centroid)	
    self.numFidLabel.setText(str(self.numFid)) 
    #Collect the line in tracker space
    tipToProbeTransform = vtk.vtkMatrix4x4()
    self.TransformSelector.currentNode().GetMatrixTransformToWorld(tipToProbeTransform)
    origin = [tipToProbeTransform.GetElement(0, 3), tipToProbeTransform.GetElement(1,3), tipToProbeTransform.GetElement(2,3)]
    dir = [tipToProbeTransform.GetElement(0, 2), tipToProbeTransform.GetElement(1,2), tipToProbeTransform.GetElement(2,2)]
    self.logic.AddPointAndLine([centroid[0],centroid[1],0], origin, dir)
    print('origin' + str(origin))
    print('dir' + str(dir))
    print('centroid' + str(centroid))
	
    if self.numFid>=1:    
      self.ImageToProbe = self.logic.CalculateRegistration()
      print('Calibration Transformation:') 
      #print('[' + str(self.ImageToProbe.GetElement(0,0)) + ',' + str(self.ImageToProbe.GetElement(0,1)) + ',' + str(self.ImageToProbe.GetElement(0,2)) + ';' + str(self.ImageToProbe.GetElement(1,0)) + ',' str(self.ImageToProbe.GetElement(1,1)) + ',' str(self.ImageToProbe.GetElement(1,2)) + ';' + str(self.ImageToProbe.GetElement(2,0)) + ',' +str(self.ImageToProbe.GetElement(2,1)) + ',' + str(self.ImageToProbe.GetElement(2,2)) + ']' + ';')
      print(self.ImageToProbe)
      print('Tip to probe:')
      print(tipToProbeTransform) 
      print('Error: ' + str(self.logic.GetError()))	
      self.connectorNode.Start()
	  
    if self.numFid>=15: 
      self.outputRegistrationTransformNode.SetMatrixTransformToParent(self.ImageToProbe)
      self.needle.SetAndObserveTransformNodeID(self.TransformSelector.currentNode().GetID()) 

  
  def onConnectButtonClicked(self):
    #creates a connector Node
    if self.manualButton.isChecked()== False:
      if self.connectorNode is None:
        self.connectorNode = slicer.vtkMRMLIGTLConnectorNode()
      #Adds this node to the scene, not there is no need for self here as it is its own node
        slicer.mrmlScene.AddNode(self.connectorNode)
      # Configures the connector
        self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
        if self.imageSelector.currentNode() is not None:
          slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
          # Configure volume reslice driver, transverse
          self.resliceLogic.SetDriverForSlice(self.imageSelector.currentNode().GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
          self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
          slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
      if self.connectorNode.GetState() == 2:
      # Connected, disconnect
        self.connectorNode.Stop()
        self.connectButton.text = "Connect"
        self.freezeButton.text = "Unfreeze" 
        I = slicer.util.array("Image_Probe")
        centroid = self.centroidFinder(I)
        self.numFid = self.numFid + 1 
        self.numFidLabel.setText(str(self.numFid)) 
	    #Collect the line in tracker space
        tipToProbeTransform = vtk.vtkMatrix4x4()
        self.TransformSelector.currentNode().GetMatrixTransformToWorld(tipToProbeTransform)
        origin = [tipToProbeTransform.GetElement(0, 3), tipToProbeTransform.GetElement(1,3), tipToProbeTransform.GetElement(2,3)]
        dir = [tipToProbeTransform.GetElement(0, 2), tipToProbeTransform.GetElement(1,2), tipToProbeTransform.GetElement(2,2)]
        self.logic.AddPointAndLine([centroid[0],centroid[1],0], origin, dir)
        slicer.modules.markups.logic().StartPlaceMode([centroid[0], centroid[1]])
        print('origin' + str(origin))
        print('dir' + str(dir))
        print('centroid' + str(centroid))
	  
        self.ImageToProbe = self.logic.CalculateRegistration()
        print('Calibration Transformation:') 
        print(self.ImageToProbe)
        print('Tip to probe:')
        print(tipToProbeTransform) 
        print('Error: ' + str(self.logic.GetError()))	
        self.connectorNode.Start()
        self.outputRegistrationTransformNode.SetMatrixTransformToParent(self.ImageToProbe)
        self.needle.SetAndObserveTransformNodeID(self.TransformSelector.currentNode().GetID()) 
        slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
        self.connectorNode == 1
      else:
      # This starts the connection
        self.connectorNode.Start()
        self.connectButton.text = "Disconnect"
        self.freezeButton.text = "Freeze"
		
    if self.manualButton.isChecked() == True:
      if self.connectorNode is None:
        self.connectorNode = slicer.vtkMRMLIGTLConnectorNode()
        slicer.mrmlScene.AddNode(self.connectorNode)
        self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
        if self.imageSelector.currentNode() is not None:
          slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
          # Configure volume reslice driver, transverse
          self.resliceLogic.SetDriverForSlice(self.imageSelector.currentNode().GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
          self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
          slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
      if self.connectorNode.GetState() == 2:
      # Csonnected, disconnect
        self.connectorNode.Stop()
        self.connectButton.text = "Connect"
     # self.freezeButton.text = "Unfreeze"
        slicer.modules.markups.logic().StartPlaceMode(0)
        slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
     
      else:
      # This starts the connection
        self.connectorNode.Start()
        self.connectButton.text = "Disconnect"
        self.freezeButton.text = "Freeze"
   
      if self.fiducialNode is not None:
	    self.fiducialNode.RemoveAllMarkups()
  	  
  
  def onFreezeButtonClicked(self):
    print("worked!")

  def onImageChanged(self, index):
      # def onImageChanged(self, newImageNode):
    if self.imageNode is not None:
      # Unparent
      self.imageNode.SetAndObserveTransformNodeID(None)
      return()

    self.imageNode = self.imageSelector.currentNode()
    self.imageSelector.currentNode().SetAndObserveTransformNodeID(self.outputRegistrationTransformNode.GetID())

    slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
    # Configure volume reslice driver, transverse
    self.resliceLogic.SetDriverForSlice(self.imageSelector.currentNode().GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
    self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
    slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
 
 
  def onInputChanged(self, string):
    if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}[^0-9]", self.inputIPLineEdit.text) and self.inputPortLineEdit.text != "" and int(self.inputPortLineEdit.text) > 0 and int(self.inputPortLineEdit.text) <= 65535:
      self.connectButton.enabled = True
      self.freezeButton.enabled = True
      if self.connectorNode is not None:
        self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
    else:
      self.connectButton.enabled = False
   #   self.freezeButton.enabled = False

  def onProbeChanged(self, newProbeNode):
    if self.probeNode is not None:
      # Unparent
      self.probeNode.SetAndObserveTransformNodeID(None)
      return()

    self.probeNode = self.probeTransformSelector.currentNode()
    self.outputRegistrationTransformNode.SetAndObserveTransformNodeID(self.probeTransformSelector.currentNode().GetID())

  # removes the observer    
  def cleanup(self):
    if self.sceneObserverTag is not None:
      slicer.mrmlScene.RemoveObserver(self.sceneObserverTag)
      self.sceneObserverTag = None

    self.connectButton.disconnect('clicked(bool)', self.onConnectButtonClicked)
    self.freezeButton.disconnect('clicked(bool)', self.onConnectButtonClicked)
    self.inputIPLineEdit.disconnect('textChanged(QString)', self.onInputChanged)
    self.inputPortLineEdit.disconnect('textChanged(QString)', self.onInputChanged)
    self.imageSelector.disconnect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)

  def onVisualizeButtonClicked(self):
    if self.fiducialNode is not None:
      self.fiducialNode.RemoveAllMarkups()
    if self.isVisualizing:
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)    
      self.isVisualizing = False
      self.visualizeButton.text = 'Show 3D Scene'
    else:
      self.isVisualizing = True
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
	
    if self.TransformSelector.currentNode() is not None:
      self.visualizeButton.text = 'Show Slices'
    self.connectorNode.InvokeEvent(slicer.vtkMRMLIGTLConnectorNode.DeviceModifiedEvent) 

  def onResetButtonClicked(self):
    if self.fiducialNode is not None:
	  self.fiducialNode.RemoveAllMarkups()

  def fitUltrasoundImageToView(self):
    redWidget = slicer.app.layoutManager().sliceWidget('Red')
    redWidget.sliceController().fitSliceToBackground()
	
  def Reset(self):
    slicer.modules.guideduscalalgo.logic().Reset()
	
  def centroidFinder(self, I_array):
    I = np.squeeze(I_array) 
	
    I_out = sitk.GetImageFromArray(I)

    n = np.histogram(I, bins=256, range=[0,255] )
    otsu_filter = sitk.OtsuThresholdImageFilter()
    inside_value = 1
    outside_value = 0
    otsu_filter.SetOutsideValue(outside_value)
    otsu_filter.SetInsideValue(inside_value)
    otsu_filter.Execute(I_out)
    T = otsu_filter.GetThreshold()

    Tup = ((T/256) + 0.6*(T/256))*256   

    binary_filt = sitk.BinaryThresholdImageFilter()
    binary_filt.SetLowerThreshold(Tup)
    binary_filt.SetUpperThreshold(255)
    binary_filt.SetInsideValue(inside_value)
    binary_filt.SetOutsideValue(outside_value)

    I_bw_im = binary_filt.Execute(I_out)

    I_bw_im= sitk.Cast(I_bw_im, sitk.sitkUInt8)
    conncomp_filt = sitk.BinaryImageToLabelMapFilter()
    conncomp_filt.FullyConnectedOn()
    conncomp_filt.SetInputForegroundValue(1)
    conncomp_filt.SetOutputBackgroundValue(0)
    I_CC = conncomp_filt.Execute(I_bw_im)
    I_CC = sitk.Cast(I_CC, sitk.sitkUInt8)

    I_CC_array = sitk.GetArrayFromImage(I_CC)
    [r,c] = I_CC_array.shape 

    I_CC_out = np.zeros([r,c])

    for i in range(0, r):
        for j in range(0,c): 
            if I_CC_array[i,j] == 1: 
                I_CC_out[i,j] = 1

    I_CC_out_im = sitk.GetImageFromArray(I_CC_out)


    Canny_edge = sitk.CannyEdgeDetectionImageFilter()
    sitk.Cast(I_CC_out_im, sitk.sitkFloat32)
    I_edge=sitk.Cast(Canny_edge.Execute(I_CC_out_im), sitk.sitkUInt8)

    dilate_filt = sitk.BinaryDilateImageFilter()
    dilate_filt.SetKernelType(sitk.sitkBox)
    dilate_filt.SetKernelRadius([16,8])
    I_dil=dilate_filt.Execute(I_edge)
    I_dil_array = sitk.GetArrayFromImage(I_dil)


    [Idx, Idy] = np.where(I_dil_array ==1)
    I_emp = np.zeros([r, c])
    Idc1 = np.zeros(len(Idy))
    Idr1 = np.zeros(len(Idx))

    Idc2 = np.zeros(len(Idy))
    Idr2 = np.zeros(len(Idx))
    counter = 0 
    for i in range(0, c):
        for j in range(0,r): 
            if I_dil_array[j,i] == 1:
                Idc1[counter] = i 
                Idr1[counter] = j
                counter= counter +1
    counter2 = 0             
    for i in range(0, r):
        for j in range(0,c): 
            if I_dil_array[i,j] == 1:
                Idc2[counter2]= j
                Idr2[counter2]= i 
                counter2= counter2 +1
            
    V1len = np.where(Idc1 == Idc1[0])
    V2len = np.where(Idc1 == Idc1[-1])
    Hlen = np.where(Idr2 == Idr2[-1])
 
    vert1 = [Idr1[0:len(V1len[0])],Idc1[0:len(V1len[0])] ]
    vert2 = [Idr1[-len(V2len[0]):],Idc1[-len(V2len[0]):]]
    Hor1= [Idr2[-len(Hlen[0]):],Idc2[-len(Hlen[0]):]]

    Y_avg = int(round((vert1[0][0] + 3* vert1[0][-1] + vert2[0][0] + 3*vert2[0][-1])/8))
    X_avg = int(round((Hor1[1][0] + Hor1[1][-1] +vert1[1][0] +vert2[1][0])/4))
    centroid = [X_avg, Y_avg]
    return centroid 



class GuidedUSCalLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    self.regLogic = slicer.modules.guideduscalalgo.logic()
    self.regLogic.SetLandmarkRegistrationToSimilarity()	
	
  def AddPointAndLine(self, point, lineOrigin, lineDirection):
    self.regLogic.AddPointAndLine(point, lineOrigin, lineDirection)

  def GetCount(self):
    return self.regLogic.GetCount()

  def CalculateRegistration(self):
    return self.regLogic.CalculateRegistration()

  def GetError(self):
    return self.regLogic.GetError()