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
#include "vtkSlicerCalibrationAlgoLogic.h"
#include "vtkPointToLineRegistration.h"

// MRML includes
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkIntArray.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>

// STD includes
#include <cassert>

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerCalibrationAlgoLogic);

//----------------------------------------------------------------------------
vtkSlicerCalibrationAlgoLogic::vtkSlicerCalibrationAlgoLogic()
  : PointToLineRegistration(vtkSmartPointer<vtkPointToLineRegistration>::New())
{
}

//----------------------------------------------------------------------------
vtkSlicerCalibrationAlgoLogic::~vtkSlicerCalibrationAlgoLogic()
{
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::AddPointAndLine(double point[3], double lineOrigin[3], double lineDirection[3])
{
  this->PointToLineRegistration->AddPoint(point[0], point[1], point[2]);
  PointToLineRegistration->AddLine(lineOrigin[0], lineOrigin[1], lineOrigin[2], lineDirection[0], lineDirection[1], lineDirection[2]);
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::Reset()
{
  this->PointToLineRegistration->Reset();
}

//----------------------------------------------------------------------------
vtkMatrix4x4* vtkSlicerCalibrationAlgoLogic::CalculateRegistration()
{
  return this->PointToLineRegistration->Compute();
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::SetTolerance(double arg)
{
  this->PointToLineRegistration->SetTolerance(arg);
}

//----------------------------------------------------------------------------
double vtkSlicerCalibrationAlgoLogic::GetTolerance() const
{
  return this->PointToLineRegistration->GetTolerance();
}

//----------------------------------------------------------------------------
unsigned int vtkSlicerCalibrationAlgoLogic::GetCount() const
{
  return this->PointToLineRegistration->GetCount();
}

//----------------------------------------------------------------------------
double vtkSlicerCalibrationAlgoLogic::GetError() const
{
  return this->PointToLineRegistration->GetError();
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::SetLandmarkRegistrationMode(int arg)
{
  this->PointToLineRegistration->SetLandmarkRegistrationMode(arg);
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::SetLandmarkRegistrationModeToRigidBody()
{
  this->PointToLineRegistration->SetLandmarkRegistrationModeToRigidBody();
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::SetLandmarkRegistrationModeToAffine()
{
  this->PointToLineRegistration->SetLandmarkRegistrationModeToAffine();
}

//----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::SetLandmarkRegistrationModeToSimilarity()
{
  this->PointToLineRegistration->SetLandmarkRegistrationModeToSimilarity();
}

//---------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::SetMRMLSceneInternal(vtkMRMLScene* newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndBatchProcessEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//-----------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::RegisterNodes()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic::UpdateFromMRMLScene()
{
  assert(this->GetMRMLScene() != 0);
}

//---------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic
::OnMRMLSceneNodeAdded(vtkMRMLNode* vtkNotUsed(node))
{
}

//---------------------------------------------------------------------------
void vtkSlicerCalibrationAlgoLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* vtkNotUsed(node))
{
}
