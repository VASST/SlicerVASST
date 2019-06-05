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

// .NAME vtkSlicerLeapCalibrationLogic - slicer logic class for multithreaded calibration of Leap motion hand tracker images
// .SECTION Description
// This class manages the logic associated with reading, saving,
// and changing propertied of the volumes

#ifndef __vtkSlicerLeapCalibrationLogic_h
#define __vtkSlicerLeapCalibrationLogic_h

// Local includes
#include "vtkSlicerLeapCalibrationModuleLogicExport.h"

// Slicer includes
#include <vtkSlicerModuleLogic.h>

// STD includes
#include <cstdlib>

class vtkMRMLLinearTransformNode;
class vtkMRMLScalarVolumeNode;
class vtkMRMLVideoCameraNode;
class vtkSlicerLeapCalibrationLogicInternal;

/// \ingroup Slicer_QtModules_ExtensionTemplate
class VTK_SLICER_LEAPCALIBRATION_MODULE_LOGIC_EXPORT vtkSlicerLeapCalibrationLogic : public vtkSlicerModuleLogic
{
public:
  enum LeapLogicEventType
  {
    LeftImageSegmentedEvent =   vtkCommand::UserEvent + 0x00072800,
    RightImageSegmentedEvent =  vtkCommand::UserEvent + 0x00072801,
    CalibrationChangedEvent =   vtkCommand::UserEvent + 0x00072802,
  };

public:
  static vtkSlicerLeapCalibrationLogic* New();
  vtkTypeMacro(vtkSlicerLeapCalibrationLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent);

  void SetLeftImageNode(vtkMRMLScalarVolumeNode*);
  void SetRightImageNode(vtkMRMLScalarVolumeNode*);
  void SetLeftCameraNode(vtkMRMLVideoCameraNode*);
  void SetRightCameraNode(vtkMRMLVideoCameraNode*);
  void SetTipToHMDTransformNode(vtkMRMLLinearTransformNode*);

  void SetBaselineMm(double);

  void Start();
  void Stop();
  void Reset();

protected:
  vtkSlicerLeapCalibrationLogic();
  virtual ~vtkSlicerLeapCalibrationLogic();

protected:
  vtkSlicerLeapCalibrationLogicInternal*    Internal;

private:
  vtkSlicerLeapCalibrationLogic(const vtkSlicerLeapCalibrationLogic&); // Not implemented
  void operator=(const vtkSlicerLeapCalibrationLogic&); // Not implemented
};

#endif
