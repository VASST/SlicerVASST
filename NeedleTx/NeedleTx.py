import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#-------------------------------------------------------
#
# NeedleTx
#
#-------------------------------------------------------
class NeedleTx(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "NeedleTx" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Golafsoun Ameri, Adam Rankin (Robarts Research Institute)"]
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#-------------------------------------------------------
#
# NeedleTxWidget
#
#-------------------------------------------------------
class NeedleTxWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    # Create 3 models, create 3 model nodes, create 3 model display nodes, add everything to scene and link
    # TODO : above
    # Set up main frame.

    pass

  def setupScene(self): #applet specific
    # logging.debug('setupScene')
    self.navigationView = self.VIEW_TRIPLE_3D

    # # ReferenceToRas is needed for ultrasound initialization, so we need to
    # # set it up before calling Guidelet.setupScene().
    # self.referenceToRas = slicer.util.getNode('ReferenceToRas')
    # if not self.referenceToRas:
      # self.referenceToRas=slicer.vtkMRMLLinearTransformNode()
      # self.referenceToRas.SetName("ReferenceToRas")
      # m = self.logic.readTransformFromSettings('ReferenceToRas', self.configurationName)
      # if m is None:
        # # By default ReferenceToRas is tilted 15deg around the patient LR axis as the reference
        # # sensor is attached to the sternum, which is not horizontal.
        # m = self.logic.createMatrixFromString('0 0 -1 0 0.258819 -0.965926 0 0 -0.965926 -0.258819 0 0 0 0 0 1')
      # self.referenceToRas.SetMatrixTransformToParent(m)
      # slicer.mrmlScene.AddNode(self.referenceToRas)

  def OnTimerTimeout(self):
    if self.imageData == None:
      return

    # To update graph, grab latest data
    for i in range(self.imageDimensions[0]):
      self.signalArray.SetComponent(i, 0, self.imageData.GetScalarComponentAsDouble(i, 0, 0, 0))

    # And one of these is the magical call to update the window
    self.table.Modified()
    self.line.Update()
    self.view.Update()

    # However, I'm 99% sure this one is always necessary
    self.view.GetInteractor().Render()
    
    # Code here to check the value of transform 1, 2, and 3
    # if -1.0, hide model
    #mat = vtk.vtkMatrix4x4()
    #transform1Node = self.firstPeakTransformSelector.currentNode()
    #transform1Node.GetMatrix(mat)
    #if mat.GetElement(2,3) < 0:
      #self.firstPeakModelDisplayNode.SetVisibility(0)
    #else:
      #self.firstPeakModelDisplayNode.SetVisibility(1)
    # transform 2
    # transform 3

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.imageData = None

    # Add a Qt timer, that fires every X ms (16.7ms = 60 FPS, 33ms = 30FPS)
    # Connect the timeout() signal of the qt timer to a function in this class that you will write
    self.timer = qt.QTimer()
    self.timer.connect('timeout()', self.OnTimerTimeout)
    self.timer.start(16.7)

    self.table = vtk.vtkTable()
    self.chart = vtk.vtkChartXY()
    self.line = self.chart.AddPlot(0)
    #self.chart.RecalculateBounds() 
    self.view = vtk.vtkContextView()

    # Instantiate and connect widgets ...
    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # transform first peak selector
    #
    self.firstPeakTransformSelector = slicer.qMRMLNodeComboBox()
    self.firstPeakTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.firstPeakTransformSelector.selectNodeUponCreation = True
    self.firstPeakTransformSelector.addEnabled = False
    self.firstPeakTransformSelector.removeEnabled = False
    self.firstPeakTransformSelector.noneEnabled = True
    self.firstPeakTransformSelector.showHidden = False
    self.firstPeakTransformSelector.showChildNodeTypes = False
    self.firstPeakTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.firstPeakTransformSelector.setToolTip( "Pick the transform for the first peak." )
    parametersFormLayout.addRow("First Peak Transform: ", self.firstPeakTransformSelector)
    
    #
    # transform second peak selector
    #
    self.secondPeakTransformSelector = slicer.qMRMLNodeComboBox()
    self.secondPeakTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.secondPeakTransformSelector.selectNodeUponCreation = True
    self.secondPeakTransformSelector.addEnabled = False
    self.secondPeakTransformSelector.removeEnabled = False
    self.secondPeakTransformSelector.noneEnabled = True
    self.secondPeakTransformSelector.showHidden = False
    self.secondPeakTransformSelector.showChildNodeTypes = False
    self.secondPeakTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.secondPeakTransformSelector.setToolTip( "Pick the transform for the second peak." )
    parametersFormLayout.addRow("Second Peak Transform: ", self.secondPeakTransformSelector)
    
    #
    # transform third peak selector
    #
    self.thirdPeakTransformSelector = slicer.qMRMLNodeComboBox()
    self.thirdPeakTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.thirdPeakTransformSelector.selectNodeUponCreation = True
    self.thirdPeakTransformSelector.addEnabled = False
    self.thirdPeakTransformSelector.removeEnabled = False
    self.thirdPeakTransformSelector.noneEnabled = True
    self.thirdPeakTransformSelector.showHidden = False
    self.thirdPeakTransformSelector.showChildNodeTypes = False
    self.thirdPeakTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.thirdPeakTransformSelector.setToolTip( "Pick the transform for the third peak." )
    parametersFormLayout.addRow("Third Peak Transform: ", self.thirdPeakTransformSelector)

    #
    # volume selector
    #
    self.imageSelector = slicer.qMRMLNodeComboBox()
    self.imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.imageSelector.selectNodeUponCreation = True
    self.imageSelector.addEnabled = False
    self.imageSelector.removeEnabled = False
    self.imageSelector.noneEnabled = True
    self.imageSelector.showHidden = False
    self.imageSelector.showChildNodeTypes = False
    self.imageSelector.setMRMLScene( slicer.mrmlScene )
    self.imageSelector.setToolTip( "Pick the image that is the oscilloscope signal." )
    parametersFormLayout.addRow("Signal Volume: ", self.imageSelector)

    #
    # threshold value
    #
    #self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    #self.imageThresholdSliderWidget.singleStep = 0.1
    #self.imageThresholdSliderWidget.minimum = -100
    #self.imageThresholdSliderWidget.maximum = 100
    #self.imageThresholdSliderWidget.value = 0.5
    #self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    #parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    #self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    #self.enableScreenshotsFlagCheckBox.checked = 0
    #self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    #parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.runButton = qt.QPushButton("Run")
    self.runButton.toolTip = "Start visualization."
    self.runButton.enabled = True
    parametersFormLayout.addRow(self.runButton)

    # connections
    self.runButton.connect('clicked(bool)', self.onRunButton)
    self.imageSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.OnInputVolumeSelect)
    self.firstPeakTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onFirstPeakSelect)
    self.secondPeakTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSecondPeakSelect)
    self.thirdPeakTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onThirdPeakSelect)
    #self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

  def onFirstPeakSelect(self):
    # unparent any existing relationship
    # Since we have model nodes created in the constructor (__init__)
    # we can now parent the model to the new transform node that was just selected
    # (don't forget to check if they chose "None")
    pass

  def onSecondPeakSelect(self):
    # unparent any existing relationship
    # Since we have model nodes created in the constructor (__init__)
    # we can now parent the model to the new transform node that was just selected
    # (don't forget to check if they chose "None")
    pass

  def onThirdPeakSelect(self):
    # unparent any existing relationship
    # Since we have model nodes created in the constructor (__init__)
    # we can now parent the model to the new transform node that was just selected
    # (don't forget to check if they chose "None")
    pass

  def OnInputVolumeSelect(self):
    pass

  def cleanup(self):
    pass

  def onRunButton(self):
    self.imageNode = slicer.util.getNode('Image_NeedleTip')
    self.imageData = self.imageNode.GetImageData()

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
    self.line.SetInputData(self.table,0,1)
    self.line.SetColor(0,255,0,255)
    self.line.SetWidth(1.0)

    inc = 1000* 1480/(2*420e6) # distance in mm. The delay distance is added to the increments.  (2e-6*1480/2) +
    distanceDelay = 1000* 2e-6*1480/2
    for i in range(self.imageDimensions[0]):
      self.distanceArray.SetComponent(i,0, distanceDelay+inc*i)
    ###
    #inc = 0 # number of elements- test
    #for i in range(self.imageDimensions[0]):
    #  self.distanceArray.SetComponent(i,0, inc)
    #  inc = inc +1

    self.view.GetRenderer().SetBackground(1.0,1.0,1.0)
    self.view.GetRenderWindow().SetSize(400,300)
    self.view.GetScene().AddItem(self.chart)
    self.view.GetRenderWindow().SetMultiSamples(0)

    self.view.GetInteractor().Initialize()

#
# NeedleTxLogic
#

class NeedleTxLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    return True


#-------------------------------------------------------
#
# NeedleTxTest
#
#-------------------------------------------------------	
class NeedleTxTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_NeedleTx1()

  def test_NeedleTx1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = NeedleTxLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')

