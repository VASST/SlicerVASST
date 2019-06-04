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

#ifndef __qSlicerLeapCalibrationModuleWidget_h
#define __qSlicerLeapCalibrationModuleWidget_h

// Slicer includes
#include <qSlicerAbstractModuleWidget.h>

// Local includes
#include "qSlicerLeapCalibrationModuleExport.h"

class qSlicerLeapCalibrationModuleWidgetPrivate;
class vtkMRMLNode;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class Q_SLICER_QTMODULES_LEAPCALIBRATION_EXPORT qSlicerLeapCalibrationModuleWidget :
  public qSlicerAbstractModuleWidget
{
  Q_OBJECT

public:

  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerLeapCalibrationModuleWidget(QWidget* parent = 0);
  virtual ~qSlicerLeapCalibrationModuleWidget();

public slots:
  void updateUI();
  void onStartStopButtonClicked();
  void onResetButtonClicked();
  void onBaselineChanged(double);

protected:
  QScopedPointer<qSlicerLeapCalibrationModuleWidgetPrivate> d_ptr;

  virtual void setup();

private:
  Q_DECLARE_PRIVATE(qSlicerLeapCalibrationModuleWidget);
  Q_DISABLE_COPY(qSlicerLeapCalibrationModuleWidget);
};

#endif
