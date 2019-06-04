/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

// LeapCalibration Logic includes
#include <vtkSlicerLeapCalibrationLogic.h>

// LeapCalibration includes
#include "qSlicerLeapCalibrationModule.h"
#include "qSlicerLeapCalibrationModuleWidget.h"

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerLeapCalibrationModulePrivate
{
public:
  qSlicerLeapCalibrationModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerLeapCalibrationModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerLeapCalibrationModulePrivate::qSlicerLeapCalibrationModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerLeapCalibrationModule methods

//-----------------------------------------------------------------------------
qSlicerLeapCalibrationModule::qSlicerLeapCalibrationModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerLeapCalibrationModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerLeapCalibrationModule::~qSlicerLeapCalibrationModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerLeapCalibrationModule::helpText() const
{
  return "This module collects spherical stylus tips in the left and right leap images (sent over OpenIGTLink using the Plus library) and uses those to perform a point to line calibration between an HMD and the Leap coordinate system.";
}

//-----------------------------------------------------------------------------
QString qSlicerLeapCalibrationModule::acknowledgementText() const
{
  return "This work was funded by BrainsCAN.";
}

//-----------------------------------------------------------------------------
QStringList qSlicerLeapCalibrationModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("Adam Rankin (Robarts Research Institute)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerLeapCalibrationModule::icon() const
{
  return QIcon(":/Icons/LeapCalibration.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerLeapCalibrationModule::categories() const
{
  return QStringList() << "IGT";
}

//-----------------------------------------------------------------------------
QStringList qSlicerLeapCalibrationModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
void qSlicerLeapCalibrationModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerLeapCalibrationModule
::createWidgetRepresentation()
{
  return new qSlicerLeapCalibrationModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerLeapCalibrationModule::createLogic()
{
  return vtkSlicerLeapCalibrationLogic::New();
}
