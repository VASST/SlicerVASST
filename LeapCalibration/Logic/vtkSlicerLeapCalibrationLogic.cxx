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

// SlicerVideoCamera includes
#include <vtkMRMLVideoCameraNode.h>

// VTK includes
#include <vtkImageData.h>
#include <vtkMatrix4x4.h>
#include <vtkObjectFactory.h>

// STD includes
#include <cassert>
#include <mutex>
#include <thread>

// VASSTAlgorithm includes
#include <vtkPointToLineRegistration.h>

// OpenCV includes
#include <opencv2/imgproc.hpp>

//----------------------------------------------------------------------------

namespace
{
  static const uint32_t MIN_SEGMENTED_IMAGE_TO_CALIBRATE = 4;
}

//----------------------------------------------------------------------------
class vtkSlicerLeapCalibrationLogicInternal : public vtkObject
{
public:
  static vtkSlicerLeapCalibrationLogicInternal* New();
  vtkTypeMacro(vtkSlicerLeapCalibrationLogicInternal, vtkObject);

  vtkSlicerLeapCalibrationLogicInternal()
    : LeftImageNode(nullptr)
    , RightImageNode(nullptr)
    , LeftCameraNode(nullptr)
    , RightCameraNode(nullptr)
    , TipToHMDTransformNode(nullptr)
    , SegmentImageThread(std::thread(&vtkSlicerLeapCalibrationLogicInternal::ThreadedSegmentationFunction, this))
    , Calibration(vtkMatrix4x4::New())
    , Run(false)
    , SegmentedImageCount(0)
    , Registration(vtkPointToLineRegistration::New())
  {}

  ~vtkSlicerLeapCalibrationLogicInternal()
  {
    this->Calibration->Delete();
    this->Calibration = nullptr;
    this->Registration->Delete();
    this->Registration = nullptr;
  }

  void ThreadedSegmentationFunction();

  bool SegmentImage(vtkImageData* image, vtkMRMLVideoCameraNode* camNode, double originOffsetMm);

public:
  vtkMRMLScalarVolumeNode*    LeftImageNode;
  vtkMRMLScalarVolumeNode*    RightImageNode;
  vtkMRMLVideoCameraNode*     LeftCameraNode;
  vtkMRMLVideoCameraNode*     RightCameraNode;
  vtkMRMLLinearTransformNode* TipToHMDTransformNode;
  vtkMatrix4x4*               Calibration;

  vtkPointToLineRegistration* Registration;

  uint32_t                    SegmentedImageCount;

  double                      LeapBaselineMm;
  std::atomic_bool            Run;
  std::mutex                  AccessMutex;
  std::thread                 SegmentImageThread;

  vtkSetObjectMacro(LeftImageNode, vtkMRMLScalarVolumeNode);
  vtkSetObjectMacro(RightImageNode, vtkMRMLScalarVolumeNode);
  vtkSetObjectMacro(LeftCameraNode, vtkMRMLVideoCameraNode);
  vtkSetObjectMacro(RightCameraNode, vtkMRMLVideoCameraNode);

  vtkSetObjectMacro(TipToHMDTransformNode, vtkMRMLLinearTransformNode);
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
    if (this->LeftImageNode != nullptr && this->LeftCameraNode != nullptr && this->TipToHMDTransformNode != nullptr)
    {
      if (SegmentImage(this->LeftImageNode->GetImageData(), this->LeftCameraNode, -this->LeapBaselineMm / 2))
      {
        this->InvokeEvent(vtkSlicerLeapCalibrationLogic::LeftImageSegmentedEvent);
      }
    }
    this->AccessMutex.unlock();

    std::this_thread::sleep_for(std::chrono::milliseconds(1));

    this->AccessMutex.lock();
    if (this->RightImageNode != nullptr && this->RightCameraNode != nullptr && this->TipToHMDTransformNode != nullptr)
    {
      if (SegmentImage(this->RightImageNode->GetImageData(), this->RightCameraNode, -this->LeapBaselineMm / 2))
      {
        this->InvokeEvent(vtkSlicerLeapCalibrationLogic::RightImageSegmentedEvent);
      }
    }
    this->AccessMutex.unlock();

    std::this_thread::sleep_for(std::chrono::milliseconds(1));

    this->AccessMutex.lock();
    if (SegmentedImageCount >= MIN_SEGMENTED_IMAGE_TO_CALIBRATE)
    {
      this->Calibration->DeepCopy(this->Registration->Compute());
      this->InvokeEvent(vtkSlicerLeapCalibrationLogic::CalibrationChangedEvent);
    }
    this->AccessMutex.unlock();
  }
}

//----------------------------------------------------------------------------
bool vtkSlicerLeapCalibrationLogicInternal::SegmentImage(vtkImageData* image, vtkMRMLVideoCameraNode* camNode, double originOffsetMm)
{
  // Segment, report location etc...
  int cvType = 0;
  switch (image->GetNumberOfScalarComponents())
  {
    case 1:
      cvType = CV_8UC1;
      break;
    case 3:
      cvType = CV_8UC3;
      break;
    case 4:
      cvType = CV_8UC4;
      break;
  }
  cv::Mat leftImage(image->GetDimensions()[0], image->GetDimensions()[1], cvType, image->GetScalarPointer());
  if (image->GetNumberOfScalarComponents() > 1)
  {
    cv::cvtColor(leftImage, leftImage, cv::COLOR_BGR2GRAY);
  }

  // undistort image
  cv::Mat intrin(3, 3, CV_64F, camNode->GetIntrinsicMatrix()->GetData());
  cv::Mat dist(1, 5, CV_64F, camNode->GetDistortionCoefficients()->GetVoidPointer(0));
  cv::Mat undistImage;
  cv::undistort(leftImage, undistImage, intrin, dist, intrin);

  std::vector<cv::Vec3d> circles;
  cv::HoughCircles(undistImage, circles, cv::HOUGH_GRADIENT, 0.125, 1, 100.0, 6.0); // values empirically determined from experimentation
  if (circles.size() > 0)
  {
    // Calculate ray from position
    cv::Vec3d circle = circles[0];
    std::cerr << "circle: " << circle[0] << ", " << circle[1] << std::endl;

    // Origin - always +-baseline, 0, 0
    cv::Vec3d origin_sen(originOffsetMm, 0.0, 0.0);

    std::cerr << origin_sen << std::endl;
    std::cerr << intrin << std::endl;
    std::cerr << dist << std::endl;

    // Calculate the direction vector for the given pixel
    // Find the inverse of the videoCamera intrinsic param matrix
    cv::Mat intrinInv = intrin.inv(cv::DECOMP_NORMAL);
    // Calculate direction vector by multiplying the inverse of the intrinsic param matrix by the pixel
    cv::Mat directionVec_sen = intrinInv * circle / cv::norm((intrinInv * circle), cv::NORM_L2);

    // And add it to the list!
    this->Registration->AddLine(origin_sen[0], origin_sen[1], origin_sen[2], directionVec_sen.at<double>(0, 0), directionVec_sen.at<double>(0, 1), directionVec_sen.at<double>(0, 2));

    // Grab stylus tip pose (tip to HMD)
    vtkNew<vtkMatrix4x4> tipToHMD;
    this->TipToHMDTransformNode->GetMatrixTransformToParent(tipToHMD);
    this->Registration->AddPoint(tipToHMD->GetElement(0, 3), tipToHMD->GetElement(1, 3), tipToHMD->GetElement(2, 3));

    return true;
  }

  return false;
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
  os << indent << "LeftImage: " << (this->Internal->LeftImageNode == nullptr) ? "not set" : "set";
  os << indent << "RightImage: " << (this->Internal->RightImageNode == nullptr) ? "not set" : "set";
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetLeftImageNode(vtkMRMLScalarVolumeNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetLeftImageNode(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetRightImageNode(vtkMRMLScalarVolumeNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetRightImageNode(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetLeftCameraNode(vtkMRMLVideoCameraNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetLeftCameraNode(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetRightCameraNode(vtkMRMLVideoCameraNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetRightCameraNode(_arg);
  this->Internal->AccessMutex.unlock();
}

//----------------------------------------------------------------------------
void vtkSlicerLeapCalibrationLogic::SetTipToHMDTransformNode(vtkMRMLLinearTransformNode* _arg)
{
  this->Internal->AccessMutex.lock();
  this->Internal->SetTipToHMDTransformNode(_arg);
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
  this->Internal->Registration->Reset();
  this->Internal->SegmentedImageCount = 0;
  this->Internal->AccessMutex.unlock();
}
