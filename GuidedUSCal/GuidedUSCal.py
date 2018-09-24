import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import re
import SimpleITK as sitk
import numpy as np 
import sitkUtils 
from  Tkinter import Tk 

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
    self.fiducialNode = None
    self.connectorNode = None
    self.sceneObserverTag = None
    self.numFid = None
    self.logic = GuidedUSCalLogic()
    self.resliceLogic = slicer.modules.volumereslicedriver.logic()
    self.imageNode = None
    self.probeNode = None
    self.sequenceNode = None
    self.sequenceNode2 = None 
    self.sequenceBrowserNode = None
    self.transformNode = None 
    self.numFid = 0
    self.sequenceLogic = slicer.modules.sequencebrowser.logic()

    self.isVisualizing = False
    self.manualOutputRegistrationTransformNode = None
    self.inputRegistrationTransformNode = None
    self.NeedleTipToReferenceTransformNode = None
    self.otsu_filter = sitk.OtsuThresholdImageFilter()
    inside_value = 0
    outside_value = 1
    self.otsu_filter.SetOutsideValue(outside_value)
    self.otsu_filter.SetInsideValue(inside_value)
    self.binary_filt = sitk.BinaryThresholdImageFilter()
    self.binary_filt.SetInsideValue(inside_value)
    self.binary_filt.SetOutsideValue(outside_value)
    self.binary_filt.SetUpperThreshold(255)
    self.dilate_filt = sitk.BinaryDilateImageFilter()
    self.conncomp_filt = sitk.BinaryImageToLabelMapFilter()
    self.conncomp_filt.FullyConnectedOn()
    self.conncomp_filt.SetInputForegroundValue(0)
    self.conncomp_filt.SetOutputBackgroundValue(0)
    self.labelFilt = sitk.LabelShapeStatisticsImageFilter()
    Tk().withdraw()
    self.currentMatrix = np.matrix('1,0,0,0;0,1,0,0;0,0,1,0;0,0,0,1', dtype = np.float64)
    self.ImageToProbeMan = vtk.vtkMatrix4x4()
    slicer.mymod = self
    self.connectCheck = 0 

  def setup(self):
    # this is the function that implements all GUI 
    ScriptedLoadableModuleWidget.setup(self)

    # This sets the view being used to the red view only 
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)

    l = slicer.modules.createmodels.logic()
    self.needleModel = l.CreateNeedle(150, 0.4, 0, False)
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
      self.freezeButton.text = "Freeze"
    else:
      self.freezeButton.text = "Place Fiducial"
    self.freezeButton.toolTip = "Freeze the ultrasound image for fiducial placement"
    self.fiducialLayout.addRow(self.freezeButton)
    self.shortcut = qt.QShortcut(qt.QKeySequence('f'), slicer.util.mainWindow())
    
    self.numFidLabel = qt.QLabel()
    self.fiducialLayout.addRow(qt.QLabel("Fiducials collected:"), self.numFidLabel)

    self.transformTable = qt.QTableWidget() 
    self.transTableItem = qt.QTableWidgetItem()
    self.fidError = qt.QLabel()
    self.transformTable.setRowCount(4)
    self.transformTable.setColumnCount(4)
    self.transformTable.horizontalHeader().hide()
    self.transformTable.verticalHeader().hide()
    self.transformTable.setItem(0,0, qt.QTableWidgetItem("1"))
    self.transformTable.setItem(0,1, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(0,2, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(0,3, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(1,0, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(1,1, qt.QTableWidgetItem("1"))
    self.transformTable.setItem(1,2, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(1,3, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(2,0, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(2,1, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(2,2, qt.QTableWidgetItem("1"))
    self.transformTable.setItem(2,3, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,0, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,1, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,2, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,3, qt.QTableWidgetItem("1"))
    self.transformTable.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.MinimumExpanding)
    self.copyIcon =qt.QIcon(":Icons/Medium/SlicerEditCopy.png")
    self.copyButton = qt.QPushButton()
    self.copyButton.setIcon(self.copyIcon)
    self.copyButton.toolTip = "Copy" 
    self.copyButton.setMaximumWidth(64)
    self.copyHbox = qt.QHBoxLayout()
    self.copyHbox.addWidget(self.copyButton)
    
    self.copyButton.enabled = False 
    if self.numFidLabel >= 2: 
      self.copyButton.enabled = True 
      
    self.fiducialLayout.addRow(qt.QLabel("Image to probe transform:"))
    self.fiducialLayout.addRow(self.transformTable)
         # Add vertical spacer
    self.layout.addStretch(1)
    
         # Add vertical spacer
    self.layout.addStretch(1)
    
    self.fiducialLayout.addRow("Copy:", self.copyHbox)
 

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
    # Disable buttons until conditions are met
    self.connectButton.setEnabled(True) 
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.freezeButton.setEnabled(False) 
    self.StopRecordButton.setEnabled(False)
    
    self.sceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.onNodeAdded)
  
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAdded(self, caller, event, callData):
    # if the node that is created is of type vtkMRMLMarkupsFiducialNODE 
    if type(callData) is slicer.vtkMRMLMarkupsFiducialNode:
      # if there is something in this node 
      if self.fiducialNode is not None:
        # remove the observer
        self.fiducialNode.RemoveAllMarkups()
        self.fiducialNode.RemoveObserver(self.markupAddedObserverTag) 

      self.fiducialNode = callData
      #sets a markupObserver to notice when a markup gets added
      self.markupAddedObserverTag = self.fiducialNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onMarkupAdded)
      #this runs the function onMarkupAdded
      self.onMarkupAdded(self.fiducialNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent)
    if type(callData) is slicer.vtkMRMLSequenceBrowserNode:
      if self.connectorNode is None: 
        self.onSequenceAdded()
        self.connectCheck = 1
  def onConnectButtonClicked(self):
    # Creates a connector Node
    if self.connectorNode is None:
      if self.connectCheck == 1: 
        if self.imageNode or self.transformNode is None: 
          if self.imageNode is None: 
            print('Please select an US volume')
          if self.trandformNode is None:
            print('Please select the tip to probe transform')
        if self.imageNode is not None and self.transformNode is not None:
          if self.fiducialNode is not None: 
            self.fiducialNode.RemoveAllMarkups()
          self.numFid = self.numFid+1 
          self.numFidLabel.setText(str(self.numFid))
          self.manualOutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
          slicer.mrmlScene.AddNode(self.manualOutputRegistrationTransformNode)
          self.manualOutputRegistrationTransformNode.SetName('ImageToProbeMan')
          slicer.modules.markups.logic().StartPlaceMode(0)
          slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
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
        self.freezeButton.text = "Unfreeze" 
        if self.imageSelector.currentNode() or self.TransformSelector.currentNode() is None: 
          if self.imageNode is None: 
            print('Please select an US volume')
          if self.transformNode is None:
            print('Please select the tip to probe transform')
        if self.imageNode is not None and self.transformNode is not None:
          self.numFid = self.numFid + 1 
          self.numFidLabel.setText(str(self.numFid))
          self.manualOutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
          slicer.mrmlScene.AddNode(self.manualOutputRegistrationTransformNode)
          self.manualOutputRegistrationTransformNode.SetName('ImageToProbeMan')
          slicer.modules.markups.logic().StartPlaceMode(0)
          slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
      else:
        # This starts the connection
        self.connectorNode.Start()
        self.connectButton.text = "Disconnect"
        self.freezeButton.text = "Freeze"
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
      self.manualOutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
      slicer.mrmlScene.AddNode(self.manualOutputRegistrationTransformNode)
      self.manualOutputRegistrationTransformNode.SetName('ImageToProbeMan')
      slicer.modules.markups.logic().StartPlaceMode(0)
      slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
  
  # This gets called when the markup is added
  def onMarkupAdded(self, fiducialNodeCaller, event):
    # Set the location and index to zero because its needs to be initialized
    centroid=[0,0,0]
    # This checks if there is not a display node 
    if self.fiducialNode.GetDisplayNode() is None:
      # then creates one if that is the case 
      self.fiducialNode.CreateDefaultDisplayNodes()
    # This sets a variable as the display node
    displayNode = self.fiducialNode.GetDisplayNode()
    # This sets the type to be a cross hair
    displayNode.SetGlyphType(3)
    # This sets the size
    displayNode.SetGlyphScale(2.5)
    # This says that you dont want text
    displayNode.SetTextScale(0)
    # This sets the color
    displayNode.SetSelectedColor(0, 0, 1)
    # This saves the location the markup is place
    # Collect the point in image space
    self.fiducialNode.GetMarkupPoint(self.fiducialNode.GetNumberOfMarkups()-1, 0, centroid)
    tipToProbeTransform = vtk.vtkMatrix4x4()
    self.transformNode.GetMatrixTransformToWorld(tipToProbeTransform)
    origin = [tipToProbeTransform.GetElement(0, 3), tipToProbeTransform.GetElement(1,3), tipToProbeTransform.GetElement(2,3)]
    dir = [tipToProbeTransform.GetElement(0, 2), tipToProbeTransform.GetElement(1,2), tipToProbeTransform.GetElement(2,2)]
    self.logic.AddPointAndLineMan([centroid[0],centroid[1],0], origin, dir)
    self.ImageToProbeMan = self.logic.manualRegLogic.CalculateRegistration()
    self.transformTable.setItem(0,0, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(0,0))))
    self.transformTable.setItem(0,1, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(0,1))))
    self.transformTable.setItem(0,2, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(0,2))))
    self.transformTable.setItem(0,3, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(0,3))))
    self.transformTable.setItem(1,0, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(1,0))))
    self.transformTable.setItem(1,1, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(1,1))))
    self.transformTable.setItem(1,2, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(1,2))))
    self.transformTable.setItem(1,3, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(1,3))))
    self.transformTable.setItem(2,0, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(2,0))))
    self.transformTable.setItem(2,1, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(2,1))))
    self.transformTable.setItem(2,2, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(2,2))))
    self.transformTable.setItem(2,3, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(2,3))))
    self.transformTable.setItem(3,0, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(3,0))))
    self.transformTable.setItem(3,1, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(3,1))))
    self.transformTable.setItem(3,2, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(3,2))))
    self.transformTable.setItem(3,3, qt.QTableWidgetItem(str(self.ImageToProbeMan.GetElement(3,3))))
    self.transformTable.resizeColumnToContents(0)
    self.transformTable.resizeColumnToContents(1)
    self.transformTable.resizeColumnToContents(2)
    self.transformTable.resizeColumnToContents(3)
    print('Mm'+ str(self.experimentNumber)+'{' + str(self.userNumber) + ',' + str(self.numFid) + '}' +'=' '[' + str(self.ImageToProbeMan.GetElement(0,0))+','+ str(self.ImageToProbeMan.GetElement(0,1))+','+str(self.ImageToProbeMan.GetElement(0,2))+','+str(self.ImageToProbeMan.GetElement(0,3))+';'+str(self.ImageToProbeMan.GetElement(1,0))+','+str(self.ImageToProbeMan.GetElement(1,1))+','+str(self.ImageToProbeMan.GetElement(1,2))+','+str(self.ImageToProbeMan.GetElement(1,3))+';'+str(self.ImageToProbeMan.GetElement(2,0))+','+str(self.ImageToProbeMan.GetElement(2,1))+','+str(self.ImageToProbeMan.GetElement(2,2))+','+str(self.ImageToProbeMan.GetElement(2,3))+';'+'0,0,0,1];')
    slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:  
      self.connectorNode.Start()
      self.connectButton.text = "Disconnect"
      self.freezeButton.text = "Freeze"

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
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
      # Configure volume reslice driver, transverse
      self.resliceLogic.SetDriverForSlice(self.imageNode.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()

  def onTransformChanged(self):
    if self.transformNode is not None: 
      self.transformNode.SetAndObserveTransformNodeID(None) 
      self.transformNode = None 
    self.transformNode = self.TransformSelector.currentNode() 
    if self.transformNode is None:
      print('Please select a tip to probe transform')
    else:
      self.needleModel.SetAndObserveTransformNodeID(self.transformNode.GetID()) 
    
  def onInputChanged(self, string):
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}[^0-9]", self.inputIPLineEdit.text) and self.inputPortLineEdit.text != "" and int(self.inputPortLineEdit.text) > 0 and int(self.inputPortLineEdit.text) <= 65535:
        self.connectButton.enabled = True
        self.freezeButton.enabled = True
        if self.connectorNode is not None:
          self.connectorNode.SetTypeClient(self.inputIPLineEdit.text, int(self.inputPortLineEdit.text))
      else:
        self.connectButton.enabled = True
      
  def onCopyButtonClicked(self,numFidLabel):
    if self.numFidLabel >=1:
      self.outputTransform = '[' + str(self.ImageToProbeMan.GetElement(0,0))+','+ str(self.ImageToProbeMan.GetElement(0,1))+','+str(self.ImageToProbeMan.GetElement(0,2))+','+str(self.ImageToProbeMan.GetElement(0,3))+','+str(self.ImageToProbeMan.GetElement(1,3))+';'+str(self.ImageToProbeMan.GetElement(1,0))+','+str(self.ImageToProbeMan.GetElement(1,1))+','+str(self.ImageToProbeMan.GetElement(1,2))+','+str(self.ImageToProbeMan.GetElement(1,3))+';'+str(self.ImageToProbeMan.GetElement(2,0))+','+str(self.ImageToProbeMan.GetElement(2,1))+','+str(self.ImageToProbeMan.GetElement(2,2))+','+str(self.ImageToProbeMan.GetElement(2,3))+']'
    else:
      self.outputTransform = 'Calibration Required' 
    root = Tk()
    root.overrideredirect(1)
    root.withdraw()
    root.clipboard_clear() 
    root.clipboard_append(self.outputTransform)
    root.update()
    root.destroy()
    
  # removes the observer
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
          # self.sequenceBrowserNode.SetRecording(self.sequenceNode, self.sequenceNode2, True)
          # TRYING THIS SEEING IF IT WORKS! 
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
      slicer.util.saveNode(self.transformNode,str(self.pathInput.text)+'/NeedleTipToProbe.h5')
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
      self.manualOutputRegistrationTransformNode.SetMatrixTransformToParent(None)
    else:
      self.isVisualizing = True
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
      self.visualizeButton.text = 'Show ultrasound stream'
      if self.transformNode is None: 
        print('Please select an US volume')
      else:
        if self.manualOutputRegistrationTransformNode is None: 
          self.manualOutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
          slicer.mrmlScene.AddNode(self.manualOutputRegistrationTransformNode)
          self.manualOutputRegistrationTransformNode.SetName('ImageToProbeMan')
        self.imageNode.SetAndObserveTransformNodeID(self.manualOutputRegistrationTransformNode.GetID())
        self.manualOutputRegistrationTransformNode.SetMatrixTransformToParent(self.ImageToProbeMan)

  def onResetButtonClicked(self):
    slicer.mrmlScene.Clear(0)

  def onSequenceAdded(self):
    self.inputIPLineEdit.placeholderText = ""
    self.IPLabel.setText("")
    self.usLayout.removeWidget(self.IPLabel)
    self.usLayout.removeWidget(self.inputIPLineEdit)
    
    self.inputPortLineEdit.placeholderText = ""
    self.portLabel.setText("")
    self.usLayout.removeWidget(self.portLabel)
    self.usLayout.removeWidget(self.inputPortLineEdit)
    
    self.usLayout.removeWidget(self.connectButton)
    
    self.RecordButton.setText("")
    self.recordLayout.removeWidget(self.RecordButton) 
    self.StopRecordButton.setText("")
    self.recordLayout.removeWidget(self.StopRecordButton)
    self.pathText.setText("")
    self.recordLayout.removeWidget(self.pathText)
    self.pathInput.placeholderText = ""
    self.recordLayout.removeWidget(self.pathInput)
    self.SaveRecordButton.setText("")
    self.recordLayout.removeWidget(self.SaveRecordButton)
    self.recordContainer.collapsed = True 
    
    self.freezeButton.enabled = True 
    self.freezeButton.text = "Place fiducial"
    self.connectButton.enabled = True 



class GuidedUSCalLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    self.manualRegLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.autoRegLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.manualRegLogic.SetLandmarkRegistrationModeToSimilarity()
    self.autoRegLogic.SetLandmarkRegistrationModeToSimilarity()

  def AddPointAndLineMan(self, point, lineOrigin, lineDirection):
    self.manualRegLogic.AddPointAndLine(point, lineOrigin, lineDirection)
  
  def AddPointAndLineAuto(self, point, lineOrigin, lineDirection):
    self.autoRegLogic.AddPointAndLine(point, lineOrigin, lineDirection)
