import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#-------------------------------------------------------
#
# NeoGuidance
#
#-------------------------------------------------------
class NeoGuidance(ScriptedLoadableModule):
  #-------------------------------------------------------
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "NeoChord Guidance"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Adam Rankin, Jonathan McLeod (Robarts Research Institute)"]
    self.parent.helpText = """This extensions enables surgical guidance for NeoChord surgical procedures."""
    self.parent.acknowledgementText = """The authors would like to thank the support of the CIHR, the CFI, and Western University."""

#-------------------------------------------------------
#
# NeoGuidanceWidget
#
#-------------------------------------------------------
class NeoGuidanceWidget(ScriptedLoadableModuleWidget):
  #-------------------------------------------------------------------------------
  def _loadPixmap(self, param):
    iconPath = os.path.join(os.path.dirname(slicer.modules.neoguidance.path), 'Resources/Icons/', param+".png")
    return qt.QIcon(iconPath)

  #-------------------------------------------------------
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = NeoGuidanceLogic()

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    self.layout.setContentsMargins(8,8,8,8)

    # Layout within the collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    parametersFormLayout.setContentsMargins(8,8,8,8)

    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.addStretch()
    layout.addWidget(qt.QLabel("Transforms"))
    layout.addStretch()
    parametersFormLayout.addRow(frame)
    
    #
    # 6DOF transform selector
    #
    self.sixDOFTransformSelector = slicer.qMRMLNodeComboBox()
    self.sixDOFTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.sixDOFTransformSelector.selectNodeUponCreation = True
    self.sixDOFTransformSelector.addEnabled = False
    self.sixDOFTransformSelector.removeEnabled = False
    self.sixDOFTransformSelector.noneEnabled = True
    self.sixDOFTransformSelector.showHidden = False
    self.sixDOFTransformSelector.showChildNodeTypes = False
    self.sixDOFTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.sixDOFTransformSelector.setToolTip( "Pick the transform describing the 6DOF sensor." )
    parametersFormLayout.addRow("6DOF Transform: ", self.sixDOFTransformSelector)

    #
    # 6DOFModel to 6DOF transform selector
    #
    self.sixDOFModelTo6DOFTransformSelector = slicer.qMRMLNodeComboBox()
    self.sixDOFModelTo6DOFTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.sixDOFModelTo6DOFTransformSelector.selectNodeUponCreation = True
    self.sixDOFModelTo6DOFTransformSelector.addEnabled = False
    self.sixDOFModelTo6DOFTransformSelector.removeEnabled = False
    self.sixDOFModelTo6DOFTransformSelector.noneEnabled = True
    self.sixDOFModelTo6DOFTransformSelector.showHidden = False
    self.sixDOFModelTo6DOFTransformSelector.showChildNodeTypes = False
    self.sixDOFModelTo6DOFTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.sixDOFModelTo6DOFTransformSelector.setToolTip( "Pick the transform describing the 6DOF model offset." )
    parametersFormLayout.addRow("6DOF Model Transform: ", self.sixDOFModelTo6DOFTransformSelector)

    #
    # 5DOF transform selector
    #
    self.fiveDOFTransformSelector = slicer.qMRMLNodeComboBox()
    self.fiveDOFTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.fiveDOFTransformSelector.selectNodeUponCreation = True
    self.fiveDOFTransformSelector.addEnabled = False
    self.fiveDOFTransformSelector.removeEnabled = False
    self.fiveDOFTransformSelector.noneEnabled = True
    self.fiveDOFTransformSelector.showHidden = False
    self.fiveDOFTransformSelector.showChildNodeTypes = False
    self.fiveDOFTransformSelector.setMRMLScene(slicer.mrmlScene)
    self.fiveDOFTransformSelector.setToolTip("Pick the transform describing the 5DOF sensor.")
    parametersFormLayout.addRow("5DOF Transform: ", self.fiveDOFTransformSelector)

    #
    # 5DOFModel to 5DOFCalculated transform selector
    #
    self.fiveDOFModelTo5DOFCalculatedTransformSelector = slicer.qMRMLNodeComboBox()
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.selectNodeUponCreation = True
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.addEnabled = False
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.removeEnabled = False
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.noneEnabled = True
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.showHidden = False
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.showChildNodeTypes = False
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.setMRMLScene(slicer.mrmlScene)
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.setToolTip("Pick the transform describing the 5DOF model offset.")
    parametersFormLayout.addRow("5DOF Model Transform: ", self.fiveDOFModelTo5DOFCalculatedTransformSelector)

    # Separator
    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.addStretch()
    layout.addWidget(qt.QLabel("Images"))
    layout.addStretch()
    parametersFormLayout.addRow(frame)

    #
    # ICE volume selector
    #
    self.iceVolumeSelector = slicer.qMRMLNodeComboBox()
    self.iceVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.iceVolumeSelector.selectNodeUponCreation = True
    self.iceVolumeSelector.addEnabled = False
    self.iceVolumeSelector.removeEnabled = False
    self.iceVolumeSelector.noneEnabled = True
    self.iceVolumeSelector.showHidden = False
    self.iceVolumeSelector.showChildNodeTypes = False
    self.iceVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.iceVolumeSelector.setToolTip("Pick the volume from the ICE transducer.")
    parametersFormLayout.addRow("ICE Image: ", self.iceVolumeSelector)

    #
    # mask volume selector
    #
    self.maskVolumeSelector = slicer.qMRMLNodeComboBox()
    self.maskVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.maskVolumeSelector.selectNodeUponCreation = True
    self.maskVolumeSelector.addEnabled = False
    self.maskVolumeSelector.removeEnabled = False
    self.maskVolumeSelector.noneEnabled = True
    self.maskVolumeSelector.showHidden = False
    self.maskVolumeSelector.showChildNodeTypes = False
    self.maskVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.maskVolumeSelector.setToolTip( "Pick the volume with the mask image for the ICE transducer." )
    parametersFormLayout.addRow("ICE Mask: ", self.maskVolumeSelector)

    #
    # TEE volume selector
    #
    self.teeVolumeSelector = slicer.qMRMLNodeComboBox()
    self.teeVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.teeVolumeSelector.selectNodeUponCreation = True
    self.teeVolumeSelector.addEnabled = False
    self.teeVolumeSelector.removeEnabled = False
    self.teeVolumeSelector.noneEnabled = True
    self.teeVolumeSelector.showHidden = False
    self.teeVolumeSelector.showChildNodeTypes = False
    self.teeVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.teeVolumeSelector.setToolTip("Pick the volume from the TEE transducer.")
    parametersFormLayout.addRow("TEE Image: ", self.teeVolumeSelector)

    #
    # output volume selector
    #
    self.maskedICEVolumeSelector = slicer.qMRMLNodeComboBox()
    self.maskedICEVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.maskedICEVolumeSelector.selectNodeUponCreation = True
    self.maskedICEVolumeSelector.addEnabled = True
    self.maskedICEVolumeSelector.renameEnabled = True
    self.maskedICEVolumeSelector.removeEnabled = False
    self.maskedICEVolumeSelector.noneEnabled = True
    self.maskedICEVolumeSelector.showHidden = False
    self.maskedICEVolumeSelector.showChildNodeTypes = False
    self.maskedICEVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.maskedICEVolumeSelector.setToolTip("Pick the volume for the masked output.")
    parametersFormLayout.addRow("Masked Output: ", self.maskedICEVolumeSelector)

    # Separator
    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addStretch()
    layout.addWidget(qt.QLabel("Models"))
    layout.addStretch()
    parametersFormLayout.addRow(frame)

    #
    # nose model selector
    #
    self.noseModelSelector = slicer.qMRMLNodeComboBox()
    self.noseModelSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.noseModelSelector.selectNodeUponCreation = True
    self.noseModelSelector.addEnabled = False
    self.noseModelSelector.renameEnabled = False
    self.noseModelSelector.removeEnabled = False
    self.noseModelSelector.noneEnabled = True
    self.noseModelSelector.showHidden = False
    self.noseModelSelector.showChildNodeTypes = False
    self.noseModelSelector.setMRMLScene( slicer.mrmlScene )
    self.noseModelSelector.setToolTip( "Select the nose model." )
    parametersFormLayout.addRow("Nose Model: ", self.noseModelSelector)

    #
    # jaw model selector
    #
    self.jawModelSelector = slicer.qMRMLNodeComboBox()
    self.jawModelSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.jawModelSelector.selectNodeUponCreation = True
    self.jawModelSelector.addEnabled = False
    self.jawModelSelector.renameEnabled = False
    self.jawModelSelector.removeEnabled = False
    self.jawModelSelector.noneEnabled = True
    self.jawModelSelector.showHidden = False
    self.jawModelSelector.showChildNodeTypes = False
    self.jawModelSelector.setMRMLScene( slicer.mrmlScene )
    self.jawModelSelector.setToolTip( "Select the jaw model." )
    parametersFormLayout.addRow("Jaw Model: ", self.jawModelSelector)

    #
    # Actions Area
    #
    actionsCollapsibleButton = ctk.ctkCollapsibleButton()
    actionsCollapsibleButton.text = "Actions"
    self.layout.addWidget(actionsCollapsibleButton)
    
    # Layout within the collapsible button
    actionsFormLayout = qt.QFormLayout(actionsCollapsibleButton)
    actionsFormLayout.setContentsMargins(8,8,8,8)

    #
    # Zero Button
    #
    self.zeroButton = qt.QPushButton("Zero")
    self.zeroButton.toolTip = "Calibrate the jaws to the home position."
    self.zeroButton.enabled = False

    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(qt.QLabel("Zero Jaws:"))
    layout.addStretch()
    layout.addWidget(self.zeroButton)
    actionsFormLayout.addRow(frame)

    #
    # UI Buttons
    #
    self.minUIButton = qt.QPushButton("Minimal UI")
    self.minUIButton.toolTip = "Show minimal UI."
    
    self.normalUIButton = qt.QPushButton("Normal UI")
    self.normalUIButton.toolTip = "Show normal UI."

    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.addStretch()
    layout.addWidget(self.minUIButton)
    layout.addWidget(self.normalUIButton)
    actionsFormLayout.addRow(frame)

    #
    # On/Off Button
    #
    self.onOffButton = qt.QPushButton("Turn On")
    self.onOffButton.toolTip = "Toggle guidance."
    self.onOffButton.enabled = False
    self.onOffButton.icon = self._loadPixmap( "off" )

    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(qt.QLabel("Guidance:"))
    layout.addStretch()
    layout.addWidget(self.onOffButton)
    actionsFormLayout.addRow(frame)

    # connections
    self.zeroButton.connect('clicked(bool)', self.onZeroButtonClicked)
    self.onOffButton.connect('clicked(bool)', self.onOffToggleButtonClicked)
    self.minUIButton.connect('clicked(bool)', self.onMinUIButtonClicked)
    self.normalUIButton.connect('clicked(bool)', self.onNormUIButtonClicked)
    self.sixDOFTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSixDOFSelectorChanged)
    self.fiveDOFTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onFiveDOFSelectorChanged)
    self.maskVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onMaskSelectorChanged)
    self.teeVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onTEEVolumeSelectorChanged)
    self.iceVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onICESelectorChanged)
    self.maskedICEVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onMaskedICEVolumeSelectorChanged)
    self.jawModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onJawModelSelectorChanged)
    self.noseModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onNoseModelSelectorChanged)
    self.sixDOFModelTo6DOFTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.on6DOFModelTo6DOFSelectorChanged)
    self.fiveDOFModelTo5DOFCalculatedTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.on5DOFModelTo5DOFCalculatedSelectorChanged)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh button state
    self.onSelect()

  #-------------------------------------------------------
  def onSixDOFSelectorChanged(self, newNode):
    self.logic.SetSixDOFTransformNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onFiveDOFSelectorChanged(self, newNode):
    self.logic.SetFiveDOFTransformNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def on6DOFModelTo6DOFSelectorChanged(self, newNode):
    self.logic.Set6DOFModelTo6DOFTransformNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def on5DOFModelTo5DOFCalculatedSelectorChanged(self, newNode):
    self.logic.Set5DOFModelTo5DOFCalculatedTransformNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onTEEVolumeSelectorChanged(self, newNode):
    self.logic.SetTEEVolumeNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onMaskSelectorChanged(self, newNode):
    self.logic.SetMaskVolumeNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onICESelectorChanged(self, newNode):
    self.logic.SetICEVolumeNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onMaskedICEVolumeSelectorChanged(self, newNode):
    self.logic.SetMaskedICEVolumeNode(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onJawModelSelectorChanged(self, newNode):
    self.logic.SetJawModel(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def onNoseModelSelectorChanged(self, newNode):
    self.logic.SetNoseModel(newNode)
    self.onSelect()

  #-------------------------------------------------------
  def cleanup(self):
    pass

  #-------------------------------------------------------
  def onSelect(self):
    self.zeroButton.enabled = self.sixDOFTransformSelector.currentNode() and self.fiveDOFTransformSelector.currentNode() and self.maskVolumeSelector.currentNode() and self.iceVolumeSelector.currentNode() and self.maskedICEVolumeSelector.currentNode() and self.noseModelSelector.currentNode() and self.jawModelSelector.currentNode() and self.sixDOFModelTo6DOFTransformSelector.currentNode()
    self.onOffButton.enabled = self.sixDOFTransformSelector.currentNode() and self.fiveDOFTransformSelector.currentNode() and self.maskVolumeSelector.currentNode() and self.iceVolumeSelector.currentNode() and self.maskedICEVolumeSelector.currentNode() and self.noseModelSelector.currentNode() and self.jawModelSelector.currentNode() and self.sixDOFModelTo6DOFTransformSelector.currentNode()

  #-------------------------------------------------------
  def onZeroButtonClicked(self):
    self.logic.ZeroJawsCalibration()

  #-------------------------------------------------------
  def onOffToggleButtonClicked(self):
    if self.onOffButton.text == "Turn On":
      self.onOffButton.text = "Turn Off"
      self.onOffButton.icon = self._loadPixmap( "on" )
      self.logic.GuidanceToggle(True)
    else:
      self.onOffButton.text = "Turn On"
      self.onOffButton.icon = self._loadPixmap( "off" )
      self.logic.GuidanceToggle(False)

  #-------------------------------------------------------
  def onMinUIButtonClicked(self):
    slicer.util.mainWindow().PanelDockWidget.dockWidgetContents.DataProbeCollapsibleWidget.hide()
    slicer.util.mainWindow().DialogToolBar.hide()
    slicer.util.mainWindow().ModuleSelectorToolBar.hide()
    slicer.util.mainWindow().MainToolBar.hide()
    slicer.util.mainWindow().ModuleToolBar.hide()
    slicer.util.mainWindow().MouseModeToolBar.hide()
    slicer.util.mainWindow().CaptureToolBar.hide()
    slicer.util.mainWindow().ViewersToolBar.hide()
    slicer.util.mainWindow().ViewToolBar.hide()
    slicer.util.mainWindow().StatusBar.hide()
    slicer.util.mainWindow().menubar.hide()
    slicer.util.mainWindow().PanelDockWidget.dockWidgetContents.ModulePanel.ScrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.HelpCollapsibleButton.hide()
    slicer.util.mainWindow().PanelDockWidget.dockWidgetContents.LogoLabel.hide()

  #-------------------------------------------------------
  def onNormUIButtonClicked(self):
    slicer.util.mainWindow().PanelDockWidget.dockWidgetContents.DataProbeCollapsibleWidget.show()
    slicer.util.mainWindow().DialogToolBar.show()
    slicer.util.mainWindow().ModuleSelectorToolBar.show()
    slicer.util.mainWindow().MainToolBar.show()
    slicer.util.mainWindow().ModuleToolBar.show()
    slicer.util.mainWindow().MouseModeToolBar.show()
    slicer.util.mainWindow().CaptureToolBar.show()
    slicer.util.mainWindow().ViewersToolBar.show()
    slicer.util.mainWindow().ViewToolBar.show()
    slicer.util.mainWindow().StatusBar.show()
    slicer.util.mainWindow().menubar.show()
    slicer.util.mainWindow().PanelDockWidget.dockWidgetContents.ModulePanel.ScrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.HelpCollapsibleButton.show()
    slicer.util.mainWindow().PanelDockWidget.dockWidgetContents.LogoLabel.show()

#-------------------------------------------------------
#
# NeoGuidanceLogic
#
#-------------------------------------------------------
class NeoGuidanceLogic(ScriptedLoadableModuleLogic):
  #-------------------------------------------------------
  def __init__(self, parent=None):
    ScriptedLoadableModuleLogic.__init__(self, parent)

    self.resliceLogic = slicer.modules.volumereslicedriver.logic()

    # Find or create the 5DOFCalculatedTo6DOF transform
    self.FiveCalculatedToSixTransform = slicer.util.getNode("FiveCalculatedToSixTransform")
    if self.FiveCalculatedToSixTransform == None:
      # Create the node
      self.FiveCalculatedToSixTransform = slicer.vtkMRMLLinearTransformNode()
      self.FiveCalculatedToSixTransform.SetName("FiveCalculatedToSixTransform")
      self.FiveCalculatedToSixTransform.SetHideFromEditors(True)
      slicer.mrmlScene.AddNode(self.FiveCalculatedToSixTransform)

    self.base5DOFTo6DOFZOffset = 0.0
    self.imageObserverTag = None
    self.sixDOFObserverTag = None

    self.iceVolumeNode = None
    self.maskedICEVolumeNode = None
    self.maskVolumeNode = None
    self.sixDOFTransformNode = None
    self.fiveDOFTransformNode = None
    self.sixDOFModelTo6DOFTransformNode = None
    self.fiveDOFModelTo5DOFCalculatedTransformNode = None
    self.jawModelNode = None
    self.noseModelNode = None

    self.guidanceOn = False

    self.imageToStencil = vtk.vtkImageToImageStencil()
    self.imageToStencil.ThresholdByUpper(254)

    self.imageStencil = vtk.vtkImageStencil()
    self.imageStencil.SetStencilConnection(self.imageToStencil.GetOutputPort())
    self.imageStencil.SetBackgroundValue(0)

    self.teeConnectorNode = slicer.util.getNode(self.moduleName + 'TEEServerConnector')
    if self.teeConnectorNode == None:
      self.teeConnectorNode = slicer.vtkMRMLIGTLConnectorNode()
      slicer.mrmlScene.AddNode(self.teeConnectorNode)
      self.teeConnectorNode.SetName(self.moduleName + 'TEEServerConnector')

    self.teeConnectorNode.SetTypeClient("localhost", 18945)
    self.teeConnectorNode.Start()

    self.iceConnectorNode = slicer.util.getNode(self.moduleName + 'ICEServerConnector')
    if self.iceConnectorNode == None:
      self.iceConnectorNode = slicer.vtkMRMLIGTLConnectorNode()
      slicer.mrmlScene.AddNode(self.iceConnectorNode)
      self.iceConnectorNode.SetName(self.moduleName + 'ICEServerConnector')

    self.iceConnectorNode.SetTypeClient("localhost", 18944)
    self.iceConnectorNode.Start()

  #-------------------------------------------------------
  def SetICEVolumeNode(self, iceVolumeNode):
    if self.iceVolumeNode == iceVolumeNode:
      return

    if self.iceVolumeNode != None:
      # Clean up observers, switch node
      self.iceVolumeNode.RemoveObserver(self.imageObserverTag)
      self.iceVolumeNode.SetAndObserveTransformNodeID(None)

    self.iceVolumeNode = iceVolumeNode

    if self.iceVolumeNode != None:
      self.imageObserverTag = self.iceVolumeNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onICEImageModified)
      self.iceVolumeNode.SetAndObserveTransformNodeID(self.FiveCalculatedToSixTransform.GetID())
      self.imageStencil.SetInputDataObject(self.iceVolumeNode.GetImageData())

  #-------------------------------------------------------
  def onICEImageModified(self, imageNode, event):
    if not self.guidanceOn:
      return

    if self.maskedICEVolumeNode == None or self.maskVolumeNode == None:
      return

    self.maskedICEVolumeNode.CopyOrientation(self.iceVolumeNode)
    self.imageStencil.SetInputDataObject(self.iceVolumeNode.GetImageData())
    self.imageStencil.Update()

  #-------------------------------------------------------
  def SetMaskedICEVolumeNode(self, maskedICEVolumeNode):
    if self.maskedICEVolumeNode == maskedICEVolumeNode:
      return

    if self.maskedICEVolumeNode != None:
      self.maskedICEVolumeNode.SetAndObserveTransformNodeID(None)
      self.maskedICEVolumeNode.SetImageDataConnection(None)

    self.maskedICEVolumeNode = maskedICEVolumeNode

    if self.maskedICEVolumeNode != None:
      self.maskedICEVolumeNode.SetAndObserveTransformNodeID(self.FiveCalculatedToSixTransform.GetID())
      self.maskedICEVolumeNode.SetImageDataConnection(self.imageStencil.GetOutputPort())

      # Configure volume reslice driver, transverse
      self.resliceLogic.SetDriverForSlice(maskedICEVolumeNode.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      self.resliceLogic.SetModeForSlice(slicer.modulelogic.vtkSlicerVolumeResliceDriverLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))

      # Set red display to this volume, reformat, and visible on
      slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeRed').SetBackgroundVolumeID(self.maskedICEVolumeNode.GetID())
      slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed').SetSliceVisible(True)
      slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed').SetOrientationToReformat()
      slicer.app.layoutManager().sliceWidget('Red').sliceConroller().fitSliceToBackground()

      # Set threshold to manual, minimum 1, maximum 255
      dispNode = self.maskedICEVolumeNode.GetDisplayNode()
      dispNode.ApplyThresholdOn()
      dispNode.SetThreshold(1,255)

  # -------------------------------------------------------
  def SetJawModel(self, jawModelNode):
    if self.jawModelNode == jawModelNode:
      return

    if self.jawModelNode != None:
      # remove parenting
      self.jawModelNode.SetAndObserveTransformNodeID(None)

    self.jawModelNode = jawModelNode

    if self.jawModelNode != None and self.sixDOFTransformNode != None and self.sixDOFModelTo6DOFTransformNode != None:
      self.ParentJawModel()

  # -------------------------------------------------------
  def SetNoseModel(self, noseModelNode):
    if self.noseModelNode == noseModelNode:
      return

    if self.noseModelNode != None:
      # remove parenting
      self.noseModelNode.SetAndObserveTransformNodeID(None)

    self.noseModelNode = noseModelNode

    if self.noseModelNode != None and self.fiveDOFTransformNode != None and self.sixDOFTransformNode != None and self.fiveDOFModelTo5DOFCalculatedTransformNode != None:
      self.ParentNoseModel()

  #-------------------------------------------------------
  def SetMaskVolumeNode(self, maskVolumeNode):
    self.maskVolumeNode = maskVolumeNode

    if self.maskVolumeNode != None:
      self.imageToStencil.SetInputDataObject(self.maskVolumeNode.GetImageData())
      self.imageToStencil.Update()

  #-------------------------------------------------------
  def SetTEEVolumeNode(self, teeVolumeNode):
    self.teeVolumeNode = teeVolumeNode

  #-------------------------------------------------------
  def SetFiveDOFTransformNode(self, fiveDOFNode):
    self.fiveDOFTransformNode = fiveDOFNode

    if self.noseModelNode != None and self.fiveDOFTransformNode != None and self.sixDOFTransformNode != None and self.fiveDOFModelTo5DOFCalculatedTransformNode != None:
      self.ParentNoseModel()

  #-------------------------------------------------------
  def SetSixDOFTransformNode(self, sixDOFNode):
    if self.sixDOFTransformNode == sixDOFNode:
      return

    if self.sixDOFTransformNode != None:
      # Clean up observers
      self.sixDOFTransformNode.RemoveObserver(self.sixDOFObserverTag)
      self.FiveCalculatedToSixTransform.SetAndObserveTransformNodeID(None)

    # Observe node
    self.sixDOFTransformNode = sixDOFNode

    if self.sixDOFTransformNode != None:
      self.sixDOFObserverTag = self.sixDOFTransformNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSixDOFModified)
      self.FiveCalculatedToSixTransform.SetAndObserveTransformNodeID(self.sixDOFTransformNode.GetID())

      if self.jawModelNode != None and self.sixDOFModelTo6DOFTransformNode != None:
        self.ParentJawModel()

      if self.noseModelNode != None and self.fiveDOFTransformNode != None and self.fiveDOFModelTo5DOFCalculatedTransformNode != None:
        self.ParentNoseModel()

  #-------------------------------------------------------
  def Set6DOFModelTo6DOFTransformNode(self, transformNode):
    if self.sixDOFModelTo6DOFTransformNode == transformNode:
      return

    if self.jawModelNode != None:
      # remove parenting
      self.jawModelNode.SetAndObserveTransformNodeID(None)

    self.sixDOFModelTo6DOFTransformNode = transformNode

    if self.sixDOFModelTo6DOFTransformNode != None and self.jawModelNode != None and self.sixDOFTransformNode != None:
      self.ParentJawModel()

  #-------------------------------------------------------
  def Set5DOFModelTo5DOFCalculatedTransformNode(self, transformNode):
    if self.fiveDOFModelTo5DOFCalculatedTransformNode == transformNode:
      return

    if self.noseModelNode != None:
      # remove parenting
      self.noseModelNode.SetAndObserveTransformNodeID(None)

    self.fiveDOFModelTo5DOFCalculatedTransformNode = transformNode

    if self.fiveDOFModelTo5DOFCalculatedTransformNode != None and self.noseModelNode != None and self.fiveDOFTransformNode != None and self.sixDOFTransformNode != None:
      self.ParentNoseModel()

  #-------------------------------------------------------
  def onSixDOFModified(self, transformNode, event):
    if not self.guidanceOn:
      return

    if self.sixDOFTransformNode == None or self.fiveDOFTransformNode == None:
      return

    fiveDOFToReference = vtk.vtkMatrix4x4()
    self.fiveDOFTransformNode.GetMatrixTransformToParent(fiveDOFToReference)
    sixDOFToReference = vtk.vtkMatrix4x4()
    self.sixDOFTransformNode.GetMatrixTransformToParent(sixDOFToReference)
    referenceToSixDOF = vtk.vtkMatrix4x4()
    referenceToSixDOF.DeepCopy(sixDOFToReference)
    referenceToSixDOF.Invert()

    originFiveDOF = [0.0, 0.0, 0.0, 1.0]
    fiveDOFOriginInRef = [0.0,0.0,0.0,1.0]
    fiveDOFOriginInSixDOF = [0.0, 0.0, 0.0, 1.0]
    fiveDOFToReference.MultiplyPoint(originFiveDOF, fiveDOFOriginInRef)
    referenceToSixDOF.MultiplyPoint(fiveDOFOriginInRef, fiveDOFOriginInSixDOF)
    fiveDOFCalculatedToSixDOF = vtk.vtkMatrix4x4()
    fiveDOFCalculatedToSixDOF.SetElement(2,3, fiveDOFOriginInSixDOF[2] - self.base5DOFTo6DOFZOffset)
    self.FiveCalculatedToSixTransform.SetMatrixTransformToParent(fiveDOFCalculatedToSixDOF)

  #-------------------------------------------------------
  def ZeroJawsCalibration(self):
    if self.sixDOFTransformNode == None or self.fiveDOFTransformNode == None:
      return

    fiveDOFToReference = vtk.vtkMatrix4x4()
    self.fiveDOFTransformNode.GetMatrixTransformToParent(fiveDOFToReference)
    sixDOFToReference = vtk.vtkMatrix4x4()
    self.sixDOFTransformNode.GetMatrixTransformToParent(sixDOFToReference)
    referenceToSixDOF = vtk.vtkMatrix4x4()
    referenceToSixDOF.DeepCopy(sixDOFToReference)
    referenceToSixDOF.Invert()

    originFiveDOF = [0.0, 0.0, 0.0, 1.0]
    fiveDOFOriginInRef = [0.0, 0.0, 0.0, 1.0]
    fiveDOFOriginInSixDOF = [0.0, 0.0, 0.0, 1.0]
    fiveDOFToReference.MultiplyPoint(originFiveDOF, fiveDOFOriginInRef)
    referenceToSixDOF.MultiplyPoint(fiveDOFOriginInRef, fiveDOFOriginInSixDOF)
    self.base5DOFTo6DOFZOffset = fiveDOFOriginInSixDOF[2]

  #-------------------------------------------------------
  def GuidanceToggle(self, onOff):
    self.guidanceOn = not self.guidanceOn

  # -------------------------------------------------------
  def ParentJawModel(self):
    if not self.jawModelNode or not self.sixDOFTransformNode or not self.sixDOFModelTo6DOFTransformNode:
      return

    self.jawModelNode.SetAndObserveTransformNodeID(self.sixDOFModelTo6DOFTransformNode.GetID())
    self.sixDOFModelTo6DOFTransformNode.SetAndObserveTransformNodeID(self.sixDOFTransformNode.GetID())

  #-------------------------------------------------------
  def ParentNoseModel(self):
    if not self.noseModelNode:
      return

    self.noseModelNode.SetAndObserveTransformNodeID(self.fiveDOFModelTo5DOFCalculatedTransformNode.GetID())
    self.fiveDOFModelTo5DOFCalculatedTransformNode.SetAndObserveTransformNodeID(self.FiveCalculatedToSixTransform.GetID())

#-------------------------------------------------------
#
# NeoGuidanceTest
#
#-------------------------------------------------------
class NeoGuidanceTest(ScriptedLoadableModuleTest):
  #-------------------------------------------------------
  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough."""
    slicer.mrmlScene.Clear(0)

  #-------------------------------------------------------
  def runTest(self):
    """Run as few or as many tests as needed here."""
    self.setUp()
    self.test_NeoGuidance1()

  #-------------------------------------------------------
  def test_NeoGuidance1(self):
    self.delayDisplay("Starting the test")

    self.delayDisplay('Test passed!')