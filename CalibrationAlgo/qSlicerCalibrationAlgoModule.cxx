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

// CalibrationAlgo Logic includes
#include <vtkSlicerCalibrationAlgoLogic.h>

// CalibrationAlgo includes
#include "qSlicerCalibrationAlgoModule.h"
#include "qSlicerCalibrationAlgoModuleWidget.h"

//-----------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 0, 0))
  #include <QtPlugin>
  Q_EXPORT_PLUGIN2(qSlicerCalibrationAlgoModule, qSlicerCalibrationAlgoModule);
#endif

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerCalibrationAlgoModulePrivate
{
public:
  qSlicerCalibrationAlgoModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerCalibrationAlgoModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerCalibrationAlgoModulePrivate::qSlicerCalibrationAlgoModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerCalibrationAlgoModule methods

//-----------------------------------------------------------------------------
qSlicerCalibrationAlgoModule::qSlicerCalibrationAlgoModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerCalibrationAlgoModulePrivate)
{
  this->setWidgetRepresentationCreationEnabled(false);
}

//-----------------------------------------------------------------------------
qSlicerCalibrationAlgoModule::~qSlicerCalibrationAlgoModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerCalibrationAlgoModule::helpText() const
{
  return "This is a hidden loadable module that contains a point to line registration algorithm";
}

//-----------------------------------------------------------------------------
QString qSlicerCalibrationAlgoModule::acknowledgementText() const
{
  return "The algorithm was written by Elvis Chen (Robarts Research Institute). This extention was created by Leah Groves (Robarts Research Institute), with help from Adam Rankin (Robarts Research Institute)";
}

//-----------------------------------------------------------------------------
QStringList qSlicerCalibrationAlgoModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("Elvis Chen (Robarts Research Intitute)")
                     << QString("Leah Groves (Robarts Research Institute)")
                     << QString("Adam Rankin (Robarts Research Institute)")
                     << QString("Funding through OGS");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerCalibrationAlgoModule::icon() const
{
  return QIcon(":/Icons/CalibrationAlgo.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerCalibrationAlgoModule::categories() const
{
  return QStringList() << "IGT";
}

//-----------------------------------------------------------------------------
QStringList qSlicerCalibrationAlgoModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
void qSlicerCalibrationAlgoModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerCalibrationAlgoModule
::createWidgetRepresentation()
{
  return new qSlicerCalibrationAlgoModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerCalibrationAlgoModule::createLogic()
{
  return vtkSlicerCalibrationAlgoLogic::New();
}
