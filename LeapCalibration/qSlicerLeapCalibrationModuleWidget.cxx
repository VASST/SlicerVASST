/*==============================================================================

  Program: 3D Slicer

  Portions (c) Adam Rankin, Robarts Research Institute, 2019

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

// Qt includes
#include <QDebug>

// Local includes
#include "vtkSlicerLeapCalibrationLogic.h"
#include "qSlicerLeapCalibrationModuleWidget.h"
#include "ui_qSlicerLeapCalibrationModuleWidget.h"

// Slicer includes
#include <qMRMLNodeComboBox.h>
#include <vtkMRMLLinearTransformNode.h>
#include <vtkMRMLNode.h>
#include <vtkMRMLScalarVolumeNode.h>

// SlicerVideoCamera includes
#include <vtkMRMLVideoCameraNode.h>

// VTK includes
#include <vtkSmartPointer.h>

// STL includes
#include <atomic>


//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerLeapCalibrationModuleWidgetPrivate: public Ui_qSlicerLeapCalibrationModuleWidget
{
public:
  qSlicerLeapCalibrationModuleWidgetPrivate();

public:
  std::atomic_bool                                Started;
  vtkSmartPointer<vtkSlicerLeapCalibrationLogic>  Logic;
};

//-----------------------------------------------------------------------------
// qSlicerLeapCalibrationModuleWidgetPrivate methods

//-----------------------------------------------------------------------------
qSlicerLeapCalibrationModuleWidgetPrivate::qSlicerLeapCalibrationModuleWidgetPrivate()
  : Started(false)
  , Logic(vtkSmartPointer<vtkSlicerLeapCalibrationLogic>::New())
{
}

//-----------------------------------------------------------------------------
// qSlicerLeapCalibrationModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerLeapCalibrationModuleWidget::qSlicerLeapCalibrationModuleWidget(QWidget* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerLeapCalibrationModuleWidgetPrivate)
{

}

//-----------------------------------------------------------------------------
qSlicerLeapCalibrationModuleWidget::~qSlicerLeapCalibrationModuleWidget()
{
  Q_D(qSlicerLeapCalibrationModuleWidget);

  disconnect(d->MRMLNodeComboBox_LeftImage, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  disconnect(d->MRMLNodeComboBox_RightImage, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  disconnect(d->MRMLNodeComboBox_LeftCamera, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  disconnect(d->MRMLNodeComboBox_RightCamera, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  disconnect(d->MRMLNodeComboBox_TipToHMDTransform, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  disconnect(d->PushButton_StartStop, &QPushButton::clicked, this, &qSlicerLeapCalibrationModuleWidget::onStartStopButtonClicked);
  disconnect(d->PushButton_Reset, &QPushButton::clicked, this, &qSlicerLeapCalibrationModuleWidget::onResetButtonClicked);
  disconnect(d->DoubleSpinBox_Baseline, static_cast<void (QDoubleSpinBox::*)(double)>(&QDoubleSpinBox::valueChanged), this, &qSlicerLeapCalibrationModuleWidget::onBaselineChanged);
}

//-----------------------------------------------------------------------------
void qSlicerLeapCalibrationModuleWidget::setup()
{
  Q_D(qSlicerLeapCalibrationModuleWidget);
  d->setupUi(this);
  this->Superclass::setup();

  connect(d->MRMLNodeComboBox_LeftImage, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  connect(d->MRMLNodeComboBox_RightImage, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  connect(d->MRMLNodeComboBox_LeftCamera, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  connect(d->MRMLNodeComboBox_RightCamera, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  connect(d->MRMLNodeComboBox_TipToHMDTransform, static_cast<void (qMRMLNodeComboBox::*)(vtkMRMLNode*)>(&qMRMLNodeComboBox::currentNodeChanged), this, &qSlicerLeapCalibrationModuleWidget::updateUI);
  connect(d->PushButton_StartStop, &QPushButton::clicked, this, &qSlicerLeapCalibrationModuleWidget::onStartStopButtonClicked);
  connect(d->PushButton_Reset, &QPushButton::clicked, this, &qSlicerLeapCalibrationModuleWidget::onResetButtonClicked);
  connect(d->DoubleSpinBox_Baseline, static_cast<void (QDoubleSpinBox::*)(double)>(&QDoubleSpinBox::valueChanged), this, &qSlicerLeapCalibrationModuleWidget::onBaselineChanged);
}


//----------------------------------------------------------------------------
void qSlicerLeapCalibrationModuleWidget::updateUI()
{
  Q_D(qSlicerLeapCalibrationModuleWidget);

  d->Logic->SetLeftImageNode(vtkMRMLScalarVolumeNode::SafeDownCast(d->MRMLNodeComboBox_LeftImage->currentNode()));
  d->Logic->SetRightImageNode(vtkMRMLScalarVolumeNode::SafeDownCast(d->MRMLNodeComboBox_RightImage->currentNode()));
  d->Logic->SetLeftCameraNode(vtkMRMLVideoCameraNode::SafeDownCast(d->MRMLNodeComboBox_LeftCamera->currentNode()));
  d->Logic->SetRightCameraNode(vtkMRMLVideoCameraNode::SafeDownCast(d->MRMLNodeComboBox_RightCamera->currentNode()));
  d->Logic->SetTipToHMDTransformNode(vtkMRMLLinearTransformNode::SafeDownCast(d->MRMLNodeComboBox_TipToHMDTransform->currentNode()));

  d->PushButton_StartStop->setEnabled(false);
  if (((d->MRMLNodeComboBox_LeftImage->currentNode() != nullptr && d->MRMLNodeComboBox_LeftCamera->currentNode() != nullptr) ||
       d->MRMLNodeComboBox_RightImage->currentNode() != nullptr && d->MRMLNodeComboBox_RightCamera->currentNode() != nullptr) &&
      d->MRMLNodeComboBox_TipToHMDTransform->currentNode() != nullptr)
  {
    d->PushButton_StartStop->setEnabled(true);
  }
}

//----------------------------------------------------------------------------
void qSlicerLeapCalibrationModuleWidget::onStartStopButtonClicked()
{
  Q_D(qSlicerLeapCalibrationModuleWidget);

  if (!d->Started)
  {
    d->Started = true;
    d->PushButton_StartStop->setText("Stop");
    d->Logic->Start();
    d->CollapsibleButton_Inputs->setEnabled(false);
  }
  else
  {
    d->Started = false;
    d->PushButton_StartStop->setText("Start");
    d->Logic->Stop();
    d->CollapsibleButton_Inputs->setEnabled(true);
  }
}

//----------------------------------------------------------------------------
void qSlicerLeapCalibrationModuleWidget::onResetButtonClicked()
{
  Q_D(qSlicerLeapCalibrationModuleWidget);

  d->Logic->Reset();
}

//----------------------------------------------------------------------------
void qSlicerLeapCalibrationModuleWidget::onBaselineChanged(double _arg)
{
  Q_D(qSlicerLeapCalibrationModuleWidget);

  d->Logic->SetBaselineMm(_arg);
}