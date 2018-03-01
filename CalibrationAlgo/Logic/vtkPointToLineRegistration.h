/*====================================================================
Copyright(c) 2018 Adam Rankin


Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files(the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and / or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions :

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
====================================================================*/

// .NAME vtkPointToLineRegistration - class for performing point to line registration
// .SECTION Description
// Performs a point to line registration

#ifndef __PointToLineRegistration_h
#define __PointToLineRegistration_h

class vtkMatrix4x4;
class vtkVector3d;

// VTK includes
#include <vtkObject.h>
#include <vtkSmartPointer.h>
#include <vtkLandmarkTransform.h>

// Local includes
#include "vtkSlicerCalibrationAlgoModuleLogicExport.h"

// STL includes
#include <vector>

class VTK_SLICER_CALIBRATIONALGO_MODULE_LOGIC_EXPORT vtkPointToLineRegistration : public vtkObject
{
  typedef std::pair<vtkVector3d, vtkVector3d> Line;

public:
  static vtkPointToLineRegistration* New();
  vtkTypeMacro(vtkPointToLineRegistration, vtkObject);
  void PrintSelf(ostream& os, vtkIndent indent);

public:
  void AddPoint(double x, double y, double z);
  void AddLine(double originX, double originY, double originZ, double directionI, double directionJ, double directionK);

  void Reset();
  void SetTolerance(double arg);
  double GetTolerance() const;
  unsigned int GetCount() const;

  vtkMatrix4x4* Compute();
  double GetError() const;

  void SetLandmarkRegistrationMode(int arg);
  void SetLandmarkRegistrationModeToRigidBody();
  void SetLandmarkRegistrationModeToAffine();
  void SetLandmarkRegistrationModeToSimilarity();

public:
  vtkPointToLineRegistration();
  ~vtkPointToLineRegistration();

protected:
  int                       LandmarkRegistrationMode;
  std::vector<vtkVector3d>  Points;
  std::vector<Line>         Lines;
  double                    Tolerance;
  double                    Error;
};

#endif
