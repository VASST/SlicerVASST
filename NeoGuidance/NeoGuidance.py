import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# NeoGuidance
#
class NeoGuidance(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "NeoChord Guidance"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Adam Rankin, Jonathan McLeod (Robarts Research Institute)"]
    self.parent.helpText = """This extensions enables surgical guidance for NeoChord surgical procedures."""
    self.parent.acknowledgementText = """NSERC, etc..."""

#
# NeoGuidanceWidget
#
class NeoGuidanceWidget(ScriptedLoadableModuleWidget):
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
    self.fiveDOFTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.fiveDOFTransformSelector.setToolTip( "Pick the transform describing the 5DOF sensor." )
    parametersFormLayout.addRow("5DOF Transform: ", self.fiveDOFTransformSelector)

    frame = qt.QWidget()
    layout = qt.QHBoxLayout(frame)
    layout.setContentsMargins(0,0,0,0)
    layout.addStretch()
    layout.addWidget(qt.QLabel("Images"))
    layout.addStretch()
    parametersFormLayout.addRow(frame)

    #
    # input volume selector
    #
    self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.inputVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputVolumeSelector.selectNodeUponCreation = True
    self.inputVolumeSelector.addEnabled = False
    self.inputVolumeSelector.removeEnabled = False
    self.inputVolumeSelector.noneEnabled = True
    self.inputVolumeSelector.showHidden = False
    self.inputVolumeSelector.showChildNodeTypes = False
    self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.inputVolumeSelector.setToolTip( "Pick the volume from the ICE transducer." )
    parametersFormLayout.addRow("ICE Image: ", self.inputVolumeSelector)

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
    # output volume selector
    #
    self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.outputVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputVolumeSelector.selectNodeUponCreation = True
    self.outputVolumeSelector.addEnabled = True
    self.outputVolumeSelector.renameEnabled = True
    self.outputVolumeSelector.removeEnabled = False
    self.outputVolumeSelector.noneEnabled = True
    self.outputVolumeSelector.showHidden = False
    self.outputVolumeSelector.showChildNodeTypes = False
    self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.outputVolumeSelector.setToolTip( "Pick the volume for the masked output. Will be transformed." )
    parametersFormLayout.addRow("Masked Output: ", self.outputVolumeSelector)

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
    actionsFormLayout.addRow("Zero Jaws: ", self.zeroButton)

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
    layout.addWidget(self.minUIButton)
    layout.addWidget(self.normalUIButton)
    actionsFormLayout.addRow(frame)

    # connections
    self.zeroButton.connect('clicked(bool)', self.onZeroButtonClicked)
    self.minUIButton.connect('clicked(bool)', self.onMinUIButtonClicked)
    self.normalUIButton.connect('clicked(bool)', self.onNormUIButtonClicked)
    self.sixDOFTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.sixDOFTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.maskVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.zeroButton.enabled = self.sixDOFTransformSelector.currentNode() and self.fiveDOFTransformSelector.currentNode() and self.maskVolumeSelector.currentNode()

  def onZeroButtonClicked(self):
    pass

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

#
# NeoGuidanceLogic
#
class NeoGuidanceLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    # TODO : trasnform hierarchy needs to be managed when nodes are selected/deselected

    # Find or create the 6DOFCalculatedTo5DOF transform
    self.SixCalculatedToFiveTransform = slicer.util.getNode("sixCalculatedToFiveTransform")
    if self.SixCalculatedToFiveTransform == None:
      # Create the node
      self.SixCalculatedToFiveTransform = slicer.vtkMRMLLinearTransformNode()
      self.SixCalculatedToFiveTransform.SetName("sixCalculatedToFiveTransform")
      slicer.mrmlScene.AddNode(self.SixCalculatedToFiveTransform)

    self.baseSixDOFTo5DOFZOffset = 0.0
    self.imageObserverTag = None
    self.fiveDOFObserverTag = None

    self.imageToStencil = vtk.vtkImageToImageStencil()
    self.imageToStencil.ThresholdByUpper(254)

    self.imageStencil = vtk.vtkImageStencil()
    self.imageStencil.SetStencilConnection(self.imageToStencil.GetOutputPort())
    self.imageStencil.SetBackgroundValue(0)

  def SetInputVolumeNode(self, inputVolumeNode):
    if self.inputVolumeNode != inputVolumeNode:
      # Clean up observers, switch node
      self.inputVolumeNode.RemoveObserver(self.imageObserverTag)
      self.inputVolumeNode = outputVolumeNode
      self.imageObserverTag = self.inputVolumeNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onImageModified)

    self.imageStencil.SetInputDataObject(self.inputVolumeNode.GetImageData())

  def onImageModified(imageNode, event):
    if self.outputVolumeNode == None or self.maskVolumeNode == None:
      return

    self.outputVolumeNode.CopyOrientation(self.inputVolumeNode)
    self.imageStencil.SetInputDataObject(self.inputVolumeNode.GetImageData())
    self.imageStencil.Update()
      
  def SetOutputVolumeNode(self, outputVolumeNode):
    pass

  def SetMaskVolumeNode(self, maskVolumeNode):
    self.maskVolumeNode = maskVolumeNode
    self.imageToStencil.SetInputDataObject(self.maskVolumeNode)
    self.imageToStencil.Update()

  def SetSixDOFTransformNode(self, sixDOFNode):
    self.sixDOFTransformNode = sixDOFNode

  def SetFiveDOFTransformNode(self, fiveDOFNode):
    if self.fiveDOFTransformNode != fiveDOFNode:
      # Clean up observers, switch node
      self.fiveDOFTransformNode.RemoveObserver(self.fiveDOFObserverTag)
      self.fiveDOFTransformNode = fiveDOFNode
      self.fiveDOFObserverTag = self.fiveDOFTransformNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onFiveDOFModified)

  def onFiveDOFModified(transformNode, event):
    if self.sixDOFTransformNode == None or self.fiveDOFTransformNode == None:
      return

    fiveDOFToReference = vtk.vtkMatrix4x4()
    fiveDOFTransformNode.GetMatrixTransformToParent(fiveDOFToReference)
    sixDOFToReference = vtk.vtkMatrix4x4()
    sixDOFTransformNode.GetMatrixTransformToParent(sixDOFToReference)
    referenceToFiveDOF = vtk.vtkMatrix4x4()
    referenceToFiveDOF.DeepCopy(fiveDOFToReference)
    referenceToFiveDOF.Invert();

    originSixDOF = [0.0, 0.0, 0.0, 1.0]
    sixDOFOriginInRef = [0.0,0.0,0.0,1.0]
    sixDOFOriginInFiveDOF = [0.0, 0.0, 0.0, 1.0]
    sixDOFToReference.MultiplyPoint(originSixDOF, sixDOFOriginInRef)
    referenceToFiveDOF.MultiplyPoint(sixDOFOriginInRef, sixDOFOriginInFiveDOF)
    sixDOFCalculatedToFiveDOF = vtk.vtkMatrix4x4()
    sixDOFCalculatedToFiveDOF.SetElement(2,3, sixDOFOriginInFiveDOF[2] - baseSixDOFTo5DOFZOffset)
    self.SixCalculatedToFiveTransform.SetMatrixTransformToParent(sixDOFCalculatedToFiveDOF)

  def zeroJawsCalibration():
    if self.sixDOFTransformNode == None or self.fiveDOFTransformNode == None:
      return

    fiveDOFToReference = vtk.vtkMatrix4x4()
    fiveDOFTransformNode.GetMatrixTransformToParent(fiveDOFToReference)
    sixDOFToReference = vtk.vtkMatrix4x4()
    sixDOFTransformNode.GetMatrixTransformToParent(sixDOFToReference)
    referenceToFiveDOF = vtk.vtkMatrix4x4()
    referenceToFiveDOF.DeepCopy(fiveDOFToReference)
    referenceToFiveDOF.Invert();

    originSixDOF = [0.0, 0.0, 0.0, 1.0]
    sixDOFOriginInRef = [0.0,0.0,0.0,1.0]
    sixDOFOriginInFiveDOF = [0.0, 0.0, 0.0, 1.0]
    sixDOFToReference.MultiplyPoint(originSixDOF, sixDOFOriginInRef)
    referenceToFiveDOF.MultiplyPoint(sixDOFOriginInRef, sixDOFOriginInFiveDOF)
    self.baseSixDOFTo5DOFZOffset = sixDOFOriginInFiveDOF[2]

#
# NeoGuidanceTest
#
class NeoGuidanceTest(ScriptedLoadableModuleTest):
  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough."""
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here."""
    self.setUp()
    self.test_NeoGuidance1()

  def test_NeoGuidance1(self):
    self.delayDisplay("Starting the test")

    self.delayDisplay('Test passed!')
