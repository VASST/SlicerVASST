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

// Local includes
#include "vtkPointToLineRegistration.h"

// VTK includes
#include <vtkLandmarkTransform.h>
#include <vtkMatrix4x4.h>
#include <vtkObjectFactory.h>
#include <vtkPoints.h>
#include <vtkVector.h>

// OpenCV includes
#include <opencv2/core.hpp>

//----------------------------------------------------------------------------

namespace
{
  void Matrix4x4ToOpenCV(vtkMatrix4x4* matrix, cv::Mat& R, cv::Mat& t)
  {
    for (int i = 0; i < 3; ++i)
    {
      for (int j = 0; j < 3; ++j)
      {
        R.at<double>(i, j) = matrix->GetElement(i, j);
      }
      t.at<double>(i, 0) = matrix->GetElement(i, 3);
    }
  }

  void OpenCVToMatrix4x4(cv::Mat& R, cv::Mat& t, vtkMatrix4x4* matrix)
  {
    for (int i = 0; i < 3; ++i)
    {
      for (int j = 0; j < 3; ++j)
      {
        matrix->SetElement(i, j, R.at<double>(i, j));
      }
      matrix->SetElement(i, 3, t.at<double>(i, 0));
    }
  }
}

//----------------------------------------------------------------------------

vtkStandardNewMacro(vtkPointToLineRegistration);

//----------------------------------------------------------------------------
vtkPointToLineRegistration::vtkPointToLineRegistration()
  : Tolerance(1e-4)
  , Error(0.0)
{
}

//----------------------------------------------------------------------------
vtkPointToLineRegistration::~vtkPointToLineRegistration()
{
}

//----------------------------------------------------------------------------
void vtkPointToLineRegistration::PrintSelf(ostream& os, vtkIndent indent)
{
  os << indent << "Tolerance: " << this->Tolerance << std::endl;
  os << indent << "Error: " << this->Error << std::endl;
}

//----------------------------------------------------------------------------
void vtkPointToLineRegistration::AddPoint(double x, double y, double z)
{
  vtkVector3d p;
  p.SetX(x);
  p.SetY(y);
  p.SetZ(z);
  this->Points.push_back(p);
}

//----------------------------------------------------------------------------
void vtkPointToLineRegistration::AddLine(double originX, double originY, double originZ, double directionI, double directionJ, double directionK)
{
  vtkVector3d origin;
  origin.SetX(originX);
  origin.SetY(originY);
  origin.SetZ(originZ);
  vtkVector3d dir;
  dir.SetX(directionI);
  dir.SetY(directionJ);
  dir.SetZ(directionK);
  this->Lines.push_back(Line(origin, dir));
}

//----------------------------------------------------------------------------
void vtkPointToLineRegistration::Reset()
{
  this->Points.clear();
  this->Lines.clear();
}

//----------------------------------------------------------------------------
void vtkPointToLineRegistration::SetTolerance(double arg)
{
  this->Tolerance = arg;
}

//----------------------------------------------------------------------------
double vtkPointToLineRegistration::GetTolerance() const
{
  return this->Tolerance;
}

//----------------------------------------------------------------------------
unsigned int vtkPointToLineRegistration::GetCount() const
{
  return this->Points.size();
}

//----------------------------------------------------------------------------
/*!
* Point to line registration
*
* use ICP to solve the following registration problem:
*
* O + a * D = R * X + t
*
* INPUTS: X - copied from this->Points
*         O - copied from this->Lines.first (origin)
*         D - copied from this->Lines.second (direction)
*
* OUTPUTS: 4x4 rotation + translation
*/
vtkMatrix4x4* vtkPointToLineRegistration::Compute()
{
  vtkMatrix4x4* matrix = vtkMatrix4x4::New();
  matrix->Identity();

  if (this->Points.size() != this->Lines.size())
  {
    return matrix;
  }

  // assume column vector
  int n = this->Points.size();
  cv::Mat e = cv::Mat::ones(1, n, CV_64F);
  double outError = std::numeric_limits<double>::infinity();
  cv::Mat E_old = cv::Mat::ones(3, n, CV_64F);
  E_old = E_old * 1000.f;
  cv::Mat E(3, n, CV_64F);

  cv::Mat O = cv::Mat(3, this->Points.size(), CV_64F);
  cv::Mat X = cv::Mat(3, this->Points.size(), CV_64F);
  cv::Mat Y = cv::Mat(3, this->Points.size(), CV_64F);
  cv::Mat D = cv::Mat(3, this->Points.size(), CV_64F);
  for (std::vector<vtkVector3d>::size_type i = 0; i < this->Points.size(); ++i)
  {
    X.at<double>(0, i) = this->Points[i].GetX();
    X.at<double>(1, i) = this->Points[i].GetY();
    X.at<double>(2, i) = this->Points[i].GetZ();

    O.at<double>(0, i) = this->Lines[i].first.GetX();
    O.at<double>(1, i) = this->Lines[i].first.GetY();
    O.at<double>(2, i) = this->Lines[i].first.GetZ();

    D.at<double>(0, i) = this->Lines[i].second.GetX();
    D.at<double>(1, i) = this->Lines[i].second.GetY();
    D.at<double>(2, i) = this->Lines[i].second.GetZ();

    Y.at<double>(0, i) = this->Lines[i].first.GetX() + this->Lines[i].second.GetX();
    Y.at<double>(1, i) = this->Lines[i].first.GetY() + this->Lines[i].second.GetY();
    Y.at<double>(2, i) = this->Lines[i].first.GetZ() + this->Lines[i].second.GetZ();
  }

  cv::Mat d(1, n, CV_64F);
  cv::Mat tempM;
  cv::Mat R = cv::Mat::eye(3, 3, CV_64F);
  cv::Mat t = cv::Mat::zeros(3, 1, CV_64F);

  vtkNew<vtkLandmarkTransform> landmarkRegistration;
  landmarkRegistration->SetModeToRigidBody();

  vtkNew<vtkPoints> source;
  vtkNew<vtkPoints> target;
  vtkNew<vtkMatrix4x4> result;
  while (outError > this->Tolerance)
  {
    source->Reset();
    target->Reset();
    for (int i = 0; i < X.cols; ++i)
    {
      source->InsertNextPoint(X.at<double>(0, i), X.at<double>(1, i), X.at<double>(2, i));
      target->InsertNextPoint(Y.at<double>(0, i), Y.at<double>(1, i), Y.at<double>(2, i));
    }
    landmarkRegistration->SetSourceLandmarks(source);
    landmarkRegistration->SetTargetLandmarks(target);
    landmarkRegistration->Update();
    landmarkRegistration->GetMatrix(result.GetPointer());
    Matrix4x4ToOpenCV(result, R, t);

    tempM = (R * X) + (t * e) - O;
    for (std::vector<vtkVector3d>::size_type i = 0; i < this->Points.size(); ++i)
    {
      d.at<double>(0, i) = tempM.at<double>(0, i) * D.at<double>(0, i) + tempM.at<double>(1, i) * D.at<double>(1, i) + tempM.at<double>(2, i) * D.at<double>(2, i);
    }

    for (int i = 0; i < n; i++)
    {
      for (int j = 0; j < 3; j++)
      {
        Y.at<double>(j, i) = O.at<double>(j, i) + d.at<double>(0, i) * D.at<double>(j, i);
      }
    }

    E = Y - (R * X) - (t * e);
    outError = cv::norm(E - E_old);
    E.copyTo(E_old);
  }

  // compute the Euclidean distance between points and lines
  outError = 0.0;
  for (int i = 0; i < E.cols; i++)
  {
    outError += std::sqrt(E.at<double>(0, i) * E.at<double>(0, i) + E.at<double>(1, i) * E.at<double>(1, i) + E.at<double>(2, i) * E.at<double>(2, i));
  }
  this->Error = outError / E.cols;

  OpenCVToMatrix4x4(R, t, matrix);

  return matrix;
}

//----------------------------------------------------------------------------
double vtkPointToLineRegistration::GetError() const
{
  return this->Error;
}
