import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import re
import SimpleITK as sitk
import numpy as np 
import sitkUtils 

if '4.11' in slicer.__path__[0]: 
  try: 
    import cv2
    OPENCV2_AVAIL = True
  except ImportError:
    print("Please ensure that SlicerOpenCV extension is installed.")

  try: 
    from tensorflow.keras.models import load_model
  except ImportError: 
    print("Please run: slicer.util.pip_install('tensorflow') in the python terminal and restart slicer")
    
  try: 
    import clipboard
  except ImportError: 
    print("Please run: slicer.util.pip_install('clipboard') in the python terminal and restart slicer")

# This is the basis of your module and will load the basic module GUI 
class GuidedUSCal(ScriptedLoadableModule):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """ 
  #define some things about your module here 
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title= "US Calibration Module"
    self.parent.categories=["IGT"]
    self.parent.dependencies = ["VolumeResliceDriver", "CreateModels", "PointToLineRegistration"]
    self.parent.contributors=["Leah Groves"]
    self.parent.helpText="""This is a scripted loadable module that performs ultrasound calibration."""
    self.parent.helpText = self.getDefaultModuleDocumentationLink()
  
# This class contains the widget (GUI) portion of the code
class GuidedUSCalWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

    # Set member variables equal to None
    self.tempNode = None 
    self.connectorNode = None
    self.sceneObserverTag = None
    self.logic = GuidedUSCalLogic()
    self.resliceLogic = slicer.modules.volumereslicedriver.logic()
    self.imageNode = None
    self.probeNode = None
    self.sequenceNode = None
    self.sequenceNode2 = None 
    self.sequenceBrowserNode = None
    self.transformNode = None 
    self.dataStack = None 
    self.numFid = 0
    self.sequenceLogic = slicer.modules.sequencebrowser.logic()
    self.counter = 0 
    self.centroid = [0,0,0]
    self.isVisualizing = False
    self.currentMatrix = np.matrix('1,0,0,0;0,1,0,0;0,0,1,0;0,0,0,1', dtype = np.float64)
    slicer.mymod = self
    self.connectCheck = 0 
    self.node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
    self.path = os.path.dirname(os.path.abspath(__file__))
    self.model = load_model(os.path.join(self.path,'Resources\Models\cnn_model_best.keras.h5'))
    self.fiducialNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
    self.fiducialNode.CreateDefaultDisplayNodes()
    self.displayNode = self.fiducialNode.GetDisplayNode()
    self.displayNode.SetGlyphType(7)
    self.displayNode.SetGlyphScale(2)
    self.displayNode.SetTextScale(0)
    self.displayNode.PointLabelsVisibilityOff()
    self.displayNode.SetSelectedColor(0, 0, 1)
    self.defaultDisplayNode = slicer.modules.markups.logic().GetDefaultMarkupsDisplayNode()
    self.defaultDisplayNode.SetGlyphType(7)
    self.defaultDisplayNode.SetGlyphScale(2)
    self.defaultDisplayNode.SetTextScale(0)
    self.defaultDisplayNode.SetSelectedColor(0, 0, 1)
    self.defaultDisplayNode.PointLabelsVisibilityOff()
    self.wResized = self.model.layers[0].output_shape[0][1]
    self.hResized = self.model.layers[0].output_shape[0][2]
    self.tipToProbeTransform = vtk.vtkMatrix4x4()
    self.outputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.outputRegistrationTransformNode)
    self.outputRegistrationTransformNode.SetName('ImageToProbe')
    self.needleModel = slicer.modules.createmodels.logic().CreateNeedle(150, 0.4, 0, False)
    self.imageToProbe = vtk.vtkMatrix4x4()
    self.redoStack = None 
    # This sets the color
  def setup(self):
    # this is the function that implements all GUI 
    ScriptedLoadableModuleWidget.setup(self)
    # This sets the view being used to the red view only 
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
    #This code block creates a collapsible button 
    #This defines which type of button you are using 
    self.usContainer = ctk.ctkCollapsibleButton()
    #This is what the button will say 
    self.usContainer.text = "Ultrasound Information"
    #Thiss actually creates that button
    self.layout.addWidget(self.usContainer)
    #This creates a variable that describes layout within this collapsible button 
    self.usLayout = qt.QFormLayout(self.usContainer)

    #This descirbes the type of widget 
    self.inputIPLineEdit = qt.QLineEdit()
    #This sets a placehoder example of what should be inputted to the line edit 
    self.inputIPLineEdit.setPlaceholderText("127.0.0.1")
    #This is the help tooltip 
    self.inputIPLineEdit.toolTip = "Put the IP address of your ultrasound device here"
    #This is the text that is input inot the line 
    self.IPLabel = qt.QLabel("Server IP:")
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.usLayout.addRow(self.IPLabel, self.inputIPLineEdit)
    #This code block is the exact same as the one above only it asks for the server port 
    self.layout.addWidget(self.usContainer)
    self.inputPortLineEdit = qt.QLineEdit()
    self.inputPortLineEdit.setPlaceholderText("18944")
    self.inputPortLineEdit.setValidator(qt.QIntValidator())
    self.inputPortLineEdit.toolTip = "Put the Port of your ultrasound device here"
    self.portLabel = qt.QLabel("Sever Port:")
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.usLayout.addRow(self.portLabel, self.inputPortLineEdit)
    #This is a push button 
    self.connectButton = qt.QPushButton()
    self.connectButton.setDefault(False)
    #This button says connect 
    self.connectButton.text = "Connect"
    #help tooltip that explains the funciton 
    self.connectButton.toolTip = "Connects to Ultrasound"
    #adds the widget to the layout 
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
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
    self.usLayout.addRow("Tip to Probe: ", self.TransformSelector)
    
    self.calibrationContainer = ctk.ctkCollapsibleButton()
    #This is what the button will say 
    self.calibrationContainer.text = "Calibration Parameters"
    #Thiss actually creates that button
    self.layout.addWidget(self.calibrationContainer)
    #This creates a variable that describes layout within this collapsible button 
    self.calibrationLayout = qt.QFormLayout(self.calibrationContainer)
    
    self.segLabel = qt.QLabel()
    self.calibrationLayout.addRow(qt.QLabel("Type of segmentation:"), self.segLabel)
    
    self.manual = qt.QCheckBox()
    self.manual.text = "Check for manual segmentation"
    self.calibrationLayout.addWidget(self.manual)
    
    self.auto = qt.QCheckBox()
    self.auto.text = "Check for automatic segmentation for ultrasonix L14-5 38"
    self.calibrationLayout.addWidget(self.auto)
    
    self.recordContainer = ctk.ctkCollapsibleButton()
    #This is what the button will say 
    self.recordContainer.text = "Recording Options"
    #Thiss actually creates that button
    #This creates a variable that describes layout within this collapsible button 
    self.recordLayout = qt.QFormLayout(self.recordContainer)
    
    self.RecordButton = qt.QPushButton() 
    self.RecordButton.text = "Start Recording" 
    self.recordLayout.addWidget(self.RecordButton)
    
    self.StopRecordButton = qt.QPushButton() 
    self.StopRecordButton.text = "Stop Recording" 
    self.recordLayout.addWidget(self.StopRecordButton)
    
    self.pathInput = qt.QLineEdit()
    self.pathInput.setPlaceholderText("Enter the path to save files to")
    self.pathText = qt.QLabel("File Path:")
    self.recordLayout.addRow(self.pathText, self.pathInput)
    
    self.SaveRecordButton = qt.QPushButton() 
    self.SaveRecordButton.text = "Save Recording" 
    self.recordLayout.addWidget(self.SaveRecordButton)
    
    # This creates another collapsible button
    self.fiducialContainer = ctk.ctkCollapsibleButton()
    self.fiducialContainer.text = "Registration"

    self.fiducialLayout = qt.QFormLayout(self.fiducialContainer)

    #This is the exact same as the code block below but it freezes the US to capture a screenshot 
    self.freezeButton = qt.QPushButton()
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.freezeButton.text = "Place Fiducial ('f')"
    else:
      self.freezeButton.text = "Place Fiducial"
    self.freezeButton.toolTip = "Freeze the ultrasound image for fiducial placement"
    self.fiducialLayout.addRow(self.freezeButton)
    self.shortcut = qt.QShortcut(qt.QKeySequence('f'), slicer.util.mainWindow())
    self.undoButton = qt.QPushButton()
    self.undoButton.setText("Undo ('u')")
    self.fiducialLayout.addRow(self.undoButton)
    self.uShortcut = qt.QShortcut(qt.QKeySequence('ctrl+u'), slicer.util.mainWindow())
    self.redoButton = qt.QPushButton()
    self.rShortcut = qt.QShortcut(qt.QKeySequence('r'), slicer.util.mainWindow())
    self.redoButton.setText("Redo ('r')")
    self.fiducialLayout.addRow(self.redoButton)
    
    self.numFidLabel = qt.QLabel()
    self.fiducialLayout.addRow(qt.QLabel("Fiducials collected:"), self.numFidLabel)
    
    self.transformTable = ctk.ctkMatrixWidget() 
    self.transformTable.columnCount = 4
    self.transformTable.rowCount = 4 
    self.transformTable.setDecimals(3)
    for i in range (0,4): 
      for j in range(0,4): 
        self.transformTable.setValue(i,j, (self.imageToProbe.GetElement(i,j)))
    
    self.fiducialLayout.addRow(qt.QLabel("Image to probe transform:"))
    self.fiducialLayout.addRow(self.transformTable)
         # Add vertical spacer
    
    self.copyButton = qt.QPushButton()
    self.copyButton.setText('Copy Transform')
    self.copyButton.toolTip = "Copy" 
    self.fiducialLayout.addRow(self.copyButton) 
    
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
    self.layout.addWidget(self.usContainer)
    self.layout.addWidget(self.calibrationContainer)
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.layout.addWidget(self.recordContainer)
    self.layout.addWidget(self.fiducialContainer)

    #self.layout.addWidget(self.transformContainer)
    self.layout.addWidget(self.validationContainer)

     # Add vertical spacer
    self.layout.addStretch(1)

    # Connections
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
      self.freezeButton.connect('clicked(bool)', self.onConnectButtonClicked)
      self.shortcut.connect('activated()', self.onConnectButtonClicked)
    else: 
      self.shortcut.connect('activated()', self.onFiducialClicked)
      self.freezeButton.connect('clicked(bool)', self.onFiducialClicked)
    self.RecordButton.connect('clicked(bool)', self.onRecordButtonClicked)
    self.StopRecordButton.connect('clicked(bool)', self.onStopRecordButtonClicked)
    self.SaveRecordButton.connect('clicked(bool)', self.onSaveRecordButtonClicked)
    self.copyButton.connect('clicked(bool)', self.onCopyButtonClicked)
    self.inputIPLineEdit.connect('textChanged(QString)', self.onInputChanged)
    self.inputPortLineEdit.connect('textChanged(QString)', self.onInputChanged)
    self.imageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)
    self.TransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onTransformChanged)
    self.resetButton.connect('clicked(bool)', self.onResetButtonClicked)
    self.undoButton.connect('clicked(bool)', self.onUndoButtonClicked)
    self.uShortcut.connect('activated()', self.onUndoButtonClicked)
    self.redoButton.connect('clicked(bool)', self.onRedoButtonClicked)
    self.rShortcut.connect('activated()', self.onRedoButtonClicked)
    # Disable buttons until conditions are met
    self.connectButton.setEnabled(True) 
    # if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      # self.freezeButton.setEnabled(False) 
    self.StopRecordButton.setEnabled(False)
    
    self.sceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.onNodeAdded)
  
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAdded(self, caller, event, callData):
    if type(callData) is slicer.vtkMRMLSequenceBrowserNode:
      if self.connectorNode is None:
        self.inputIPLineEdit.hide() 
        self.inputPortLineEdit.hide() 
        self.IPLabel.hide()
        self.portLabel.hide()
        self.recordContainer.hide() 
        self.connectButton.hide() 
        self.connectCheck = 1 
    # if the node that is created is of type vtkMRMLMarkupsFiducialNODE 
    if type(callData) is slicer.vtkMRMLMarkupsFiducialNode:
      # if there is something in this node 
      if self.fiducialNode is not None:
        # remove the observer
        self.fiducialNode.RemoveAllMarkups()
       # self.fiducialNode.RemoveObserver(self.markupAddedObserverTag) 
      if self.manual.isChecked() == True:
        self.fiducialNode = callData
        #sets a markupObserver to notice when a markup gets added
        self.markupAddedObserverTag = self.fiducialNode.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onMarkupAdded)
        #this runs the function onMarkupAdded
        self.onMarkupAdded(self.fiducialNode, slicer.vtkMRMLMarkupsNode.PointModifiedEvent)
  def onConnectButtonClicked(self):
    # Creates a connector Node
    if self.connectorNode is None:
      if self.connectCheck == 1: 
        if self.imageNode or self.transformNode is None: 
          if self.imageNode is None: 
            print('Please select an US volume')
          if self.transformNode is None:
            print('Please select the tip to probe transform')
      else:
        self.connectorNode = slicer.vtkMRMLIGTLConnectorNode()
        # Adds this node to the scene, not there is no need for self here as it is its own node
        slicer.mrmlScene.AddNode(self.connectorNode)
        # Configures the connector
        self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
        self.connectorNode.Start()
    else:
      if self.connectorNode.GetState() == 2:
        # Connected
        self.connectorNode.Stop()
        self.connectButton.text = "Connect"
        self.freezeButton.text = "Unfreeze ('f')" 
        if self.imageSelector.currentNode() or self.TransformSelector.currentNode() is None: 
          if self.imageNode is None: 
            print('Please select an US volume')
          if self.transformNode is None:
            print('Please select the tip to probe transform')
        if self.imageNode is not None and self.transformNode is not None:
          self.numFid = self.numFid + 1 
          self.numFidLabel.setText(str(self.numFid))
          slicer.modules.markups.logic().StartPlaceMode(0)
          slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
      else:
        # This starts the connection
        self.connectorNode.Start()
        self.connectButton.text = "Disconnect"
        self.freezeButton.text = "Place fiducial ('f')"
      if self.fiducialNode is not None:
        self.fiducialNode.RemoveAllMarkups()
  
  def onFiducialClicked(self):
    if self.fiducialNode is not None: 
      self.fiducialNode.RemoveAllMarkups()
    if self.imageNode or self.transformNode is None: 
      if self.imageNode is None: 
        print('Please select an US volume')
      if self.transformNode is None:
        print('Please select the tip to probe transform')
    if self.imageNode is not None and self.transformNode is not None:
      self.numFid = self.numFid+1 
      self.numFidLabel.setText(str(self.numFid))
      if self.manual.isChecked() == True:
        slicer.modules.markups.logic().StartPlaceMode(0)
        self.markupAddedObserverTag = self.fiducialNode.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onMarkupAdded)
        self.onMarkupAdded(self.fiducialNode, slicer.vtkMRMLMarkupsNode.PointModifiedEvent);
      if self.auto.isChecked() == True: 
        self.fiducialNode.RemoveAllMarkups()
        self.I = slicer.util.arrayFromVolume(slicer.util.getNode('Image_Probe'))
        self.shape = self.I.shape
        self.Im = np.resize(self.I, [self.shape[1],self.shape[2]])
        self.Im = np.transpose(self.Im)
        self.Im = np.resize(self.Im, [self.shape[2],self.shape[1],1])
        self.x = self.Im[:,0:self.shape[1]-5]/255
        self.w = self.x.shape[0]
        self.h = self.x.shape[1]
        if self.wResized != 128: 
          self.x = np.resize(self.x, [self.wResized,self.hResized,1])
        else:
          self.x = np.expand_dims(cv2.resize(self.x, (self.wResized, self.hResized)), axis=3)
        slicer.util.updateVolumeFromArray(self.node, self.x)
        self.centroid = self.segment_image(self.Im)
        self.fiducialNode.AddFiducialFromArray([self.centroid[0], self.centroid[1],0])
        self.transformNode.GetMatrixTransformToWorld(self.tipToProbeTransform)
        self.origin = [self.tipToProbeTransform.GetElement(0, 3), self.tipToProbeTransform.GetElement(1,3), self.tipToProbeTransform.GetElement(2,3)]
        self.dir = [self.tipToProbeTransform.GetElement(0, 2), self.tipToProbeTransform.GetElement(1,2), self.tipToProbeTransform.GetElement(2,2)]
        self.logic.AddPointAndLine([self.centroid[0],self.centroid[1],0], self.origin, self.dir)
        self.imageToProbe = self.logic.registrationLogic.CalculateRegistration()
        if self.dataStack is None: 
          self.dataStack = [[self.centroid[0],self.centroid[1], self.origin, self.dir]]
        else: 
          self.dataStack.append([self.centroid[0],self.centroid[1], self.origin, self.dir])
        for i in range (0,4): 
          for j in range(0,4): 
            self.transformTable.setValue(i,j,(self.imageToProbe.GetElement(i,j)))
        slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
        if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:  
          self.connectorNode.Start()
          self.connectButton.text = "Disconnect"
          self.freezeButton.text = "(Place Fiducial ('f'))"
  
  # This gets called when the markup is added
  def onMarkupAdded(self, fiducialNodeCaller, event):
    # Set the location and index to zero because its needs to be initialized
    self.centroid = [0,0,0]
    if self.manual.isChecked() == True:
      # This checks if there is not a display node 
      # Do nothing if markup has not been placed
      if self.fiducialNode.GetNthControlPointPositionStatus(self.fiducialNode.GetNumberOfMarkups()-1) != slicer.vtkMRMLMarkupsNode.PositionDefined:
          return
      # This saves the location the markup is place
      # Collect the point in image space
      self.fiducialNode.GetMarkupPoint(self.fiducialNode.GetNumberOfMarkups()-1, 0, self.centroid)
      self.transformNode.GetMatrixTransformToWorld(self.tipToProbeTransform)
      self.origin = [self.tipToProbeTransform.GetElement(0, 3), self.tipToProbeTransform.GetElement(1,3), self.tipToProbeTransform.GetElement(2,3)]
      self.dir = [self.tipToProbeTransform.GetElement(0, 2), self.tipToProbeTransform.GetElement(1,2), self.tipToProbeTransform.GetElement(2,2)]
      self.logic.AddPointAndLine([self.centroid[0],self.centroid[1],0], self.origin, self.dir)
      self.imageToProbe = self.logic.registrationLogic.CalculateRegistration()
      if self.dataStack is None: 
        self.dataStack = [[self.centroid[0],self.centroid[1], self.origin, self.dir]]
      else: 
        self.dataStack.append([self.centroid[0],self.centroid[1], self.origin, self.dir])
      for i in range (0,4): 
        for j in range(0,4): 
          self.transformTable.setValue(i,j,(self.imageToProbe.GetElement(i,j)))
      slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()

  def onImageChanged(self):
    if self.imageNode is not None:
      # Unparent
      self.imageNode.SetAndObserveTransformNodeID(None)
      self.imageNode = None
    self.imageNode = self.imageSelector.currentNode()
    if self.imageNode is None: 
      print('Please select an US volume')
    else: 
      self.imageNode.GetDisplayNode().SetAutoWindowLevel(0)
      self.imageNode.GetDisplayNode().SetWindowLevelMinMax(0,120)
      self.imageNode.SetName('Image_Probe') 
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
      # Configure volume reslice driver, transverse
      self.resliceLogic.SetDriverForSlice(self.imageNode.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()

  def onTransformChanged(self):
    if self.transformNode is not None: 
      self.transformNode.SetAndObserveTransformNodeID(None) 
      self.transformNode = None 
      self.needleModel.SetAndObserveTransformNodeID(None)
    self.transformNode = self.TransformSelector.currentNode() 
    if self.transformNode is None:
      print('Please select a tip to probe transform')
    else:
      self.needleModel.SetAndObserveTransformNodeID(self.transformNode.GetID()) 
    
  def onInputChanged(self, string):
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}[^0-9]", self.inputIPLineEdit.text) and self.inputPortLineEdit.text != "" and int(self.inputPortLineEdit.text) > 0 and int(self.inputPortLineEdit.text) <= 65535:
        self.connectButton.enabled = True
        if self.connectorNode is not None:
          self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
      else:
        self.connectButton.enabled = True
        
  def onCopyButtonClicked(self):
    self.outputTransform = str(self.imageToProbe.GetElement(0,0))+" "+ str(self.imageToProbe.GetElement(0,1))+" "+str(self.imageToProbe.GetElement(0,2))+" "+str(self.imageToProbe.GetElement(0,3))+ "\r\n"+str(self.imageToProbe.GetElement(1,0))+" "+str(self.imageToProbe.GetElement(1,1))+" "+str(self.imageToProbe.GetElement(1,2))+" "+str(self.imageToProbe.GetElement(1,3)) + "\r\n"+str(self.imageToProbe.GetElement(2,0))+" "+str(self.imageToProbe.GetElement(2,1))+" "+str(self.imageToProbe.GetElement(2,2))+" "+str(self.imageToProbe.GetElement(2,3))
    clipboard.copy(self.outputTransform)

  def onRecordButtonClicked(self):
    if self.connectCheck == 0:
      if self.sequenceBrowserNode is None:
        if self.imageNode is None: 
          print('Please select an US volume')
        else:
          slicer.modules.sequencebrowser.setToolBarVisible(1)
          self.sequenceBrowserNode =slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
          self.sequenceBrowserNode.SetName( slicer.mrmlScene.GetUniqueNameByString( "Recording" ))
          self.sequenceBrowserNode.SetAttribute("Recorded", "True")
          self.sequenceBrowserNode.SetScene(slicer.mrmlScene)
          slicer.mrmlScene.AddNode(self.sequenceBrowserNode)
          self.sequenceBrowserLogic = slicer.modules.sequencebrowser.logic()
          self.modifyFlag = self.sequenceBrowserNode.StartModify()
          self.sequenceNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode")
          self.sequenceNode2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode")
          self.sequenceBrowserNode.AddProxyNode(self.transformNode, self.sequenceNode)
          self.sequenceBrowserNode.AddProxyNode(self.imageNode, self.sequenceNode2)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode, self.transformNode, self.sequenceBrowserNode)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode2, self.imageNode, self.sequenceBrowserNode)
          self.sequenceBrowserNode.EndModify(self.modifyFlag)
          self.RecordButton.text = "Recording"
          self.StopRecordButton.setEnabled(True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode2, True)
          self.sequenceBrowserNode.SetRecordingActive(True)
      else:
        if self.sequenceBrowserNode.GetRecordingActive() == True:
          # self.sequenceBrowserNode.SetRecording(self.sequenceNode, self.sequenceNode2, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode2, True)
          # self.sequenceBrowserNode.SetRecordingActive(True)
        else: 
          print('The Sequence is currently recording')

  def onStopRecordButtonClicked(self): 
    if self.sequenceBrowserNode is not None: 
      if self.sequenceBrowserNode.GetRecordingActive() == True:
        self.RecordButton.text = "Start Recording"
        self.sequenceBrowserNode.SetRecording(self.sequenceNode, False)
        self.sequenceBrowserNode.SetRecording(self.sequenceNode2,False)
        self.sequenceBrowserNode.SetRecordingActive(False)
        self.StopRecordButton.enabled = False 

  def onSaveRecordButtonClicked(self):
    if self.pathInput.text is None: 
      print('Please enter the file path')
    else:
      print('Files saved')
      self.filePath = str(self.pathInput.text)
      slicer.util.saveScene(self.filePath+'/SlicerSceneUSCalibration.mrml')
      slicer.util.saveNode(self.imageNode, str(self.pathInput.text)+'/Image_Probe.nrrd')
      slicer.util.saveNode(self.transformNode,str(self.pathInput.text)+'/NeedleTipToProbe.txt')
      slicer.util.saveNode(self.sequenceNode, str(self.pathInput.text)+'/Sequence.seq.mha')
      slicer.util.saveNode(self.sequenceNode2, str(self.pathInput.text)+'/Sequence_1.seq.nrrd')
  def cleanup(self):
    if self.sceneObserverTag is not None:
      slicer.mrmlScene.RemoveObserver(self.sceneObserverTag)
      self.sceneObserverTag = None

    if self.connectButton is not None:
      self.connectButton.disconnect('clicked(bool)', self.onConnectButtonClicked)
    if self.freezeButton is not None:
      self.freezeButton.disconnect('clicked(bool)', self.onConnectButtonClicked)
    if self.inputIPLineEdit is not None:
      self.inputIPLineEdit.disconnect('textChanged(QString)', self.onInputChanged)
    if self.inputPortLineEdit is not None:
      self.inputPortLineEdit.disconnect('textChanged(QString)', self.onInputChanged)
    if self.imageSelector is not None:
      self.imageSelector.disconnect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)

  def onVisualizeButtonClicked(self):
    if self.fiducialNode is not None:
      self.fiducialNode.RemoveAllMarkups()
    if self.isVisualizing:
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)    
      self.isVisualizing = False
      self.visualizeButton.text = 'Show 3D Scene'
      self.outputRegistrationTransformNode.SetMatrixTransformToParent(None)
    else:
      self.isVisualizing = True
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
      self.visualizeButton.text = 'Show ultrasound stream'
      if self.transformNode is None: 
        print('Please select an US volume')
      else:
        self.imageNode.SetAndObserveTransformNodeID(self.outputRegistrationTransformNode.GetID())
        self.outputRegistrationTransformNode.SetMatrixTransformToParent(self.imageToProbe)
  def onResetButtonClicked(self):
    slicer.mrmlScene.Clear(0)
  
  def segment_image(self,x):
      y = self.model.predict(np.expand_dims(self.x, axis=0)).T
      # Scale predicted coordinates to pixel coordinate
      y[0] = int((y[0] + 1.0) * (self.w/2))
      y[1] = int((y[1] + 1.0) * (self.h/2))
      # Reshape y to a row vector
      y = np.squeeze(y.T, axis=0)
      
      return [y[0],y[1],0]
  
  def onUndoButtonClicked(self):
    self.logic.registrationLogic.Reset() 
    if self.redoStack is None: 
      self.redoStack = [self.dataStack[-1]] 
    else: 
      self.redoStack.append(self.dataStack[-1])
    self.dataStack.pop(-1)
    for i in range(0,len(self.dataStack)):
      self.logic.AddPointAndLine([self.dataStack[i][0],self.dataStack[i][1],0], self.dataStack[i][2], self.dataStack[i][3])
      self.imageToProbe = self.logic.registrationLogic.CalculateRegistration()
    self.numFid = self.numFid -1 
    self.numFidLabel.setText(self.numFid)
    self.fiducialNode.RemoveAllMarkups()
    for i in range (0,4): 
      for j in range(0,4): 
        self.transformTable.setValue(i,j,(self.imageToProbe.GetElement(i,j)))
  def onRedoButtonClicked(self):
    self.logic.registrationLogic.Reset() 
    if self.redoStack is not None:
      self.dataStack.append(self.redoStack[-1])
    else: 
      print('There is nothing to redo')
    self.redoStack.pop(-1)
    for i in range(0,len(self.dataStack)):
      self.logic.AddPointAndLine([self.dataStack[i][0],self.dataStack[i][1],0], self.dataStack[i][2], self.dataStack[i][3])
      self.imageToProbe = self.logic.registrationLogic.CalculateRegistration()
    self.numFid = self.numFid +1 
    self.numFidLabel.setText(self.numFid)
    self.fiducialNode.AddFiducialFromArray([self.dataStack[i][0],self.dataStack[i][1],0]) 
    for i in range (0,4): 
      for j in range(0,4): 
        self.transformTable.setValue(i,j,(self.imageToProbe.GetElement(i,j)))
class GuidedUSCalLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    self.registrationLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.registrationLogic.SetLandmarkRegistrationModeToAnisotropic()
  def AddPointAndLine(self, point, lineOrigin, lineDirection):
    self.registrationLogic.AddPointAndLine(point, lineOrigin, lineDirection)
    
  
