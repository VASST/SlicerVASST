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

// Qt includes
#include <QtPlugin>

// LapUSVisualization Logic includes
#include <vtkSlicerLapUSVisualizationLogic.h>

// LapUSVisualization includes
#include "qSlicerLapUSVisualizationModule.h"
#include "qSlicerLapUSVisualizationModuleWidget.h"

//-----------------------------------------------------------------------------
#if (QT_VERSION < QT_VERSION_CHECK(5, 0, 0))
#include <QtPlugin>
Q_EXPORT_PLUGIN2(qSlicerLapUSVisualizationModule, qSlicerLapUSVisualizationModule);
#endif

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerLapUSVisualizationModulePrivate
{
public:
  qSlicerLapUSVisualizationModulePrivate();
};

//-----------------------------------------------------------------------------
// qSlicerLapUSVisualizationModulePrivate methods

//-----------------------------------------------------------------------------
qSlicerLapUSVisualizationModulePrivate::qSlicerLapUSVisualizationModulePrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerLapUSVisualizationModule methods

//-----------------------------------------------------------------------------
qSlicerLapUSVisualizationModule::qSlicerLapUSVisualizationModule(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerLapUSVisualizationModulePrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerLapUSVisualizationModule::~qSlicerLapUSVisualizationModule()
{
}

//-----------------------------------------------------------------------------
QString qSlicerLapUSVisualizationModule::helpText() const
{
  return "This is a loadable module that can be bundled in an extension";
}

//-----------------------------------------------------------------------------
QString qSlicerLapUSVisualizationModule::acknowledgementText() const
{
  return "This work was partially funded by NIH grant NXNNXXNNNNNN-NNXN";
}

//-----------------------------------------------------------------------------
QStringList qSlicerLapUSVisualizationModule::contributors() const
{
  QStringList moduleContributors;
  moduleContributors << QString("John Doe (AnyWare Corp.)");
  return moduleContributors;
}

//-----------------------------------------------------------------------------
QIcon qSlicerLapUSVisualizationModule::icon() const
{
  return QIcon(":/Icons/LapUSVisualization.png");
}

//-----------------------------------------------------------------------------
QStringList qSlicerLapUSVisualizationModule::categories() const
{
  return QStringList() << "Examples";
}

//-----------------------------------------------------------------------------
QStringList qSlicerLapUSVisualizationModule::dependencies() const
{
  return QStringList();
}

//-----------------------------------------------------------------------------
void qSlicerLapUSVisualizationModule::setup()
{
  this->Superclass::setup();
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerLapUSVisualizationModule
::createWidgetRepresentation()
{
  return new qSlicerLapUSVisualizationModuleWidget;
}

//-----------------------------------------------------------------------------
vtkMRMLAbstractLogic* qSlicerLapUSVisualizationModule::createLogic()
{
  return vtkSlicerLapUSVisualizationLogic::New();
}
