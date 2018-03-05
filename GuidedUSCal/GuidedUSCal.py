import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import re

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
    self.customLayoutId = 85683

    self.isVisualizing = False
    self.outputRegistrationTransformNode = None
    self.inputRegistrationTransformNode = None

  def setup(self):
    # this is the function that implements all GUI 
    ScriptedLoadableModuleWidget.setup(self)

    slicer.mymod = self
     #This sets the view being used to the red view only 
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
    #l=slicer.modules.createmodels.logic()
    #self.needle = l.CreateNeedle(180, 0.75, 0, False)

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

    self.guidedButton = qt.QCheckBox()
    self.guidedButton.text = "Select to turn guidance off"
    self.guidedButton.toolTip = "This allows the user to select if they want to use the guidance"
    self.usLayout.addRow(self.guidedButton)
   
    # This creates another collapsible button
    self.fiducialContainer = ctk.ctkCollapsibleButton()
    self.fiducialContainer.text = "Registration"
    self.fiducialLayout = qt.QFormLayout(self.fiducialContainer)
	
	 #add combo box for linear transform node 
    self.strawTransformSelector = slicer.qMRMLNodeComboBox()
    self.strawTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.strawTransformSelector.selectNodeUponCreation = True
    self.strawTransformSelector.addEnabled = False
    self.strawTransformSelector.removeEnabled = False
    self.strawTransformSelector.noneEnabled = True
    self.strawTransformSelector.showHidden = False
    self.strawTransformSelector.showChildNodeTypes = False
    self.strawTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.strawTransformSelector.setToolTip( "Pick the transform representing the straw line." )
    self.fiducialLayout.addRow("Straw transform: ", self.strawTransformSelector)

    self.probeTransformSelector = slicer.qMRMLNodeComboBox()
    self.probeTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.probeTransformSelector.selectNodeUponCreation = True
    self.probeTransformSelector.addEnabled = False
    self.probeTransformSelector.removeEnabled = False
    self.probeTransformSelector.noneEnabled = True
    self.probeTransformSelector.showHidden = False
    self.probeTransformSelector.showChildNodeTypes = False
    self.probeTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.probeTransformSelector.setToolTip( "Pick the transform representing the probe line." )
    self.fiducialLayout.addRow("Probe transform: ", self.probeTransformSelector)
	
	   #This is the exact same as the code block below but it freezes the US to capture a screenshot 
    self.freezeButton = qt.QPushButton()
    self.freezeButton.text = "Freeze"
    self.freezeButton.toolTip = "Freeze the ultrasound image for fiducial placement"
    self.fiducialLayout.addRow(self.freezeButton)

    # This is another push button 
    self.fiducialButton = qt.QPushButton("Place Fiducial")  
    self.fiducialButton.toolTip = "Creates a fiducial to be placed on the straw"
    self.fiducialLayout.addRow(self.fiducialButton)
    #When clicked it runs the function onFaducialButtonClicked
    self.fiducialButton.connect('clicked(bool)', self.onFiducialButtonClicked)

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
    self.inputIPLineEdit.connect('textChanged(QString)', self.onInputChanged)
    self.inputPortLineEdit.connect('textChanged(QString)', self.onInputChanged)
    self.guidedButton.connect('stateChanged(int)', self.onGuidedButtonClicked)
    #self.guidedButton.connect('clicked(0)', self.onGuidedOffButtonClicked)
    self.imageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)
    #self.strawTransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)
    #self.probeTransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onProbeChanged)
    self.resetButton.connect('clicked(bool)', self.onResetButtonClicked)

    # Disable buttons until conditions are met
    self.connectButton.setEnabled(False) 
    self.freezeButton.setEnabled(False) 

    #This adds an observer to scene to listen for mrml node 
    self.sceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.onNodeAdded)

    # else if self.guidedButton.toggled(False):
    #   slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)

    layoutLogic = slicer.app.layoutManager().layoutLogic()
    customLayout = (
      "<layout type=\"horizontal\" split=\"false\" >"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Red\">"
      "   <property name=\"orientation\" action=\"default\">Reformat</property>"
      "   <property name=\"viewlabel\" action=\"default\">R</property>"
      "   <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "   <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      "</layout>")
    layoutLogic.GetLayoutNode().AddLayoutDescription(self.customLayoutId, customLayout)

    self.outputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.outputRegistrationTransformNode)
    self.outputRegistrationTransformNode.SetName('ImageToProbe')
	
    self.NeedleTipToReferenceTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.NeedleTipToReferenceTransformNode)

  #This is the function that runs when the connect button is clicked  
  def onConnectButtonClicked(self):
    #creates a connector Node
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
    else:
      # This starts the connection
      self.connectorNode.Start()
      self.connectButton.text = "Disconnect"
      self.freezeButton.text = "Freeze"

  def onGuidedButtonClicked(self):
    if self.guidedButton.isChecked():
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
    else:
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutSideBySideView)
      slicer.app.layoutManager().sliceWidget('yellow')

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
 
  #This is the function that runs once the fiducial button is pressed
  def onFiducialButtonClicked(self):
    # this line creates the logic for the markup (crosshair) that is being placed 
    #startPlaceMode(0) means only one markup gets place
    slicer.modules.markups.logic().StartPlaceMode(0)
    slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
	 
    if self.fiducialNode is not None:
	    self.fiducialNode.RemoveAllMarkups()
	  
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

  def onInputChanged(self, string):
    if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}[^0-9]", self.inputIPLineEdit.text) and self.inputPortLineEdit.text != "" and int(self.inputPortLineEdit.text) > 0 and int(self.inputPortLineEdit.text) <= 65535:
      self.connectButton.enabled = True
      self.freezeButton.enabled = True
      if self.connectorNode is not None:
        self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
    else:
      self.connectButton.enabled = False
      self.freezeButton.enabled = False

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
      #if self.strawTransformSelector.currentNode() is not None:
        #self.strawTransformSelector.currentNode().SetAttribute('IGTLVisible', 'false')
      self.isVisualizing = False
      self.visualizeButton.text = 'Show 3D Scene'
    else:
      self.isVisualizing = True
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
  
      #self.NeedleTipToReferenceTransformNode.SetAndObserveTransformNodeID(self.strawTransformSelector.currentNode().GetID())
      # self.NeedleTipToReferenceTransformNode.SetMatrixTransformToParent(self.needle)
      #if self.strawTransformSelector.currentNode() is not None:
        #self.strawTransformSelector.currentNode().SetAttribute('IGTLVisible', 'true')
      self.visualizeButton.text = 'Show Slices'
    
    self.connectorNode.InvokeEvent(slicer.vtkMRMLIGTLConnectorNode.DeviceModifiedEvent) 

  def onResetButtonClicked(self):
    if self.fiducialNode is not None:
	  self.fiducialNode.RemoveAllMarkups()

  #This gets called when the markup is added
  def onMarkupAdded(self, fiducialNodeCaller, event):
    #set the location and index to zero because its needs to be initialized
    centroid=[0,0,0]
    ImageToProbe = vtk.vtkMatrix4x4()
    MarkupIndex = 0
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
    #print(centroid) 	
    self.numFidLabel.setText(str(self.numFid)) 
    #Collect the line in tracker space
    strawTransform = vtk.vtkMatrix4x4()
    self.strawTransformSelector.currentNode().GetMatrixTransformToWorld(strawTransform)
    origin = [strawTransform.GetElement(0, 3), strawTransform.GetElement(1,3), strawTransform.GetElement(2,3)]
    dir = [strawTransform.GetElement(0, 2), strawTransform.GetElement(1,2), strawTransform.GetElement(2,2)]
    self.logic.AddPointAndLine([centroid[0],centroid[1],0], origin, dir)
    print('origin' + str(origin))
    print('dir' + str(dir))
    print('centroid' + str(centroid))
	
	
    if self.numFid>=5:    
      self.ImageToProbe = self.logic.CalculateRegistration()
      print(self.ImageToProbe)	  
      print('Error: ' + str(self.logic.GetError()))
    
    if self.numFid>= 15: 
      self.outputRegistrationTransformNode.SetMatrixTransformToParent(self.ImageToProbe)	
	
	
  def Reset(self):
    slicer.modules.guideduscalalgo.logic().Reset()
	

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