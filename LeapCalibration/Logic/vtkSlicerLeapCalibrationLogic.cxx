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
#include "vtkSlicerLeapCalibrationLogic.h"

// MRML includes
#include <vtkMRMLLinearTransformNode.h>
#include <vtkMRMLScalarVolumeNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkMatrix4x4.h>
#include <vtkObjectFactory.h>

// STD includes
#include <cassert>
#include <mutex>
#include <thread>

//----------------------------------------------------------------------------
class vtkSlicerLeapCalibrationLogicInternal : public vtkObject
{
public:
  static vtkSlicerLeapCalibrationLogicInternal* New();
  vtkTypeMacro(vtkSlicerLeapCalibrationLogicInternal, vtkObject);

  vtkSlicerLeapCalibrationLogicInternal()
    : LeftImage(nullptr)
    , RightImage(nullptr)
    , HMDTransform(nullptr)
    , TipTransform(nullptr)
    , SegmentImageThread(std::thread(&vtkSlicerLeapCalibrationLogicInternal::ThreadedSegmentationFunction, this))
    , Calibration(vtkMatrix4x4::New())
    , Run(false)
  {}

  ~vtkSlicerLeapCalibrationLogicInternal()
  {
    this->Calibration->Delete();
    this->Calibration = nullptr;
  }

  void ThreadedSegmentationFunction();

public:
  vtkMRMLScalarVolumeNode*    LeftImage;
  vtkMRMLScalarVolumeNode*    RightImage;
  vtkMRMLLinearTransformNode* HMDTransform;
  vtkMRMLLinearTransformNode* TipTransform;
  vtkMatrix4x4*               Calibration;

  double                      LeapBaselineMm;
  std::atomic_bool            Run;
  std::mutex                  AccessMutex;
  std::thread                 SegmentImageThread;

  vtkSetObjectMacro(LeftImage, vtkMRMLScalarVolumeNode);
  vtkSetObjectMacro(RightImage, vtkMRMLScalarVolumeNode);

  vtkSetObjectMacro(HMDTransform, vtkMRMLLinearTransformNode);
  vtkSetObjectMacro(TipTransform, vtkMRMLLinearTransformNode);
};

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerLeapCalibrationLogic);
vtkStandardNewMacro(vtkSlicerLeapCalibrationLogicInternal)

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogicInternal::ThreadedSegmentationFunction()
{
  while (this->Run)
  {
    this->AccessMutex.lock();
    if (this->LeftImage != nullptr)
    {
      // Segment, report location etc...
      this->InvokeEvent(vtkSlicerLeapCalibrationLogic::LeftImageSegmentedEvent);
    }
    if (this->RightImage != nullptr)
    {
      // Segment, report location etc...
      this->InvokeEvent(vtkSlicerLeapCalibrationLogic::RightImageSegmentedEvent);
    }
    this->AccessMutex.unlock();
  }
}

//----------------------------------------------------------------------------
vtkSlicerLeapCalibrationLogic::vtkSlicerLeapCalibrationLogic()
  : Internal(vtkSlicerLeapCalibrationLogicInternal::New())
{
}

//----------------------------------------------------------------------------
vtkSlicerLeapCalibrationLogic::~vtkSlicerLeapCalibrationLogic()
{
  this->Internal->Delete();
  this->Internal = nullptr;
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
  os << indent << "LeftImage: " << (this->Internal->LeftImage == nullptr) ? "not set" : "set";
  os << indent << "RightImage: " << (this->Internal->RightImage == nullptr) ? "not set" : "set";
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetLeftImage(vtkMRMLScalarVolumeNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetLeftImage(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetRightImage(vtkMRMLScalarVolumeNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetRightImage(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetHMDTransform(vtkMRMLLinearTransformNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetHMDTransform(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetTipTransform(vtkMRMLLinearTransformNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetTipTransform(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetBaselineMm(double _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->LeapBaselineMm = _arg;
  this->Internal->AccessMutex.unlock();
}

//-----------------------------------`-----------------------------------------
void vtkSlicerLeapCalibrationLogic::Start()
{
  this->Internal->AccessMutex.lock();
  if (!this->Internal->Run)
  {
    this->Internal->Run = true;
    this->Internal->SegmentImageThread.join();
  }
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::Stop()
{
  this->Internal->Run = false;
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::Reset()
{
  this->Internal->AccessMutex.lock();
  this->Internal->Calibration->Identity();
  this->Internal->AccessMutex.unlock();
}
