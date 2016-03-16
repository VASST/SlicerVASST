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
#include <QDebug>

// SlicerQt includes
#include "qSlicerLapUSVisualizationModuleWidget.h"
#include "ui_qSlicerLapUSVisualizationModuleWidget.h"

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_ExtensionTemplate
class qSlicerLapUSVisualizationModuleWidgetPrivate: public Ui_qSlicerLapUSVisualizationModuleWidget
{
public:
  qSlicerLapUSVisualizationModuleWidgetPrivate();
};

//-----------------------------------------------------------------------------
// qSlicerLapUSVisualizationModuleWidgetPrivate methods

//-----------------------------------------------------------------------------
qSlicerLapUSVisualizationModuleWidgetPrivate::qSlicerLapUSVisualizationModuleWidgetPrivate()
{
}

//-----------------------------------------------------------------------------
// qSlicerLapUSVisualizationModuleWidget methods

//-----------------------------------------------------------------------------
qSlicerLapUSVisualizationModuleWidget::qSlicerLapUSVisualizationModuleWidget(QWidget* _parent)
  : Superclass( _parent )
  , d_ptr( new qSlicerLapUSVisualizationModuleWidgetPrivate )
{
}

//-----------------------------------------------------------------------------
qSlicerLapUSVisualizationModuleWidget::~qSlicerLapUSVisualizationModuleWidget()
{
}

//-----------------------------------------------------------------------------
void qSlicerLapUSVisualizationModuleWidget::setup()
{
  Q_D(qSlicerLapUSVisualizationModuleWidget);
  d->setupUi(this);
  this->Superclass::setup();
}
