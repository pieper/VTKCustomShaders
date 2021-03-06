#!/usr/bin/env python
'''
=========================================================================

  Program:   Visualization Toolkit
  Module:    TestGPURayCastUserShader.py

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http:#www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================
'''


import sys
print(sys.argv)

import vtk
import vtk.test.Testing
from vtk.util.misc import vtkGetDataRoot
VTK_DATA_ROOT = vtkGetDataRoot()

'''
  Prevent .pyc files from being created.
  Stops the vtk source being polluted
  by .pyc files.
'''
sys.dont_write_bytecode = True

# Disable object factory override for vtkNrrdReader
vtk.vtkObjectFactory.SetAllEnableFlags(False, "vtkNrrdReader", "vtkPNrrdReader")

dataRoot = vtkGetDataRoot()
reader = vtk.vtkNrrdReader()
if len(sys.argv) > 1:
    fileName = sys.argv[1]
else:
    fileName = "/Users/pieper/data/multivolume/Cardiac-resampled-cropped/00rc.nrrd"
reader.SetFileName(fileName)
reader.Update()

volumeProperty = vtk.vtkVolumeProperty()
volumeProperty.ShadeOn()
volumeProperty.SetInterpolationType(vtk.VTK_LINEAR_INTERPOLATION)

range = reader.GetOutput().GetScalarRange()

# Prepare 1D Transfer Functions
ctf = vtk.vtkColorTransferFunction()
ctf.AddRGBPoint(0, 0.0, 0.0, 0.0)
ctf.AddRGBPoint(510, 0.4, 0.4, 1.0)
ctf.AddRGBPoint(640, 1.0, 1.0, 1.0)
ctf.AddRGBPoint(range[1], 0.9, 0.1, 0.1)

pf = vtk.vtkPiecewiseFunction()
pf.AddPoint(0, 0.00)
pf.AddPoint(510, 0.00)
pf.AddPoint(640, 0.5)
pf.AddPoint(range[1], 0.4)

volumeProperty.SetScalarOpacity(pf)
volumeProperty.SetColor(ctf)
volumeProperty.SetShade(1)

mapper = vtk.vtkGPUVolumeRayCastMapper()
mapper.SetInputConnection(reader.GetOutputPort())
mapper.SetUseJittering(1)

# Modify the shader to color based on the depth of the translucent voxel
mapper.AddShaderReplacement(
    vtk.vtkShader.Fragment,  # Replace in the fragment shader
    "//VTK::Base::Dec",      # Source string to replace
    True,                    # before the standard replacements
    "//VTK::Base::Dec"       # We still want the default
    "\n bool l_updateDepth;"
    "\n vec3 l_opaqueFragPos;",
    False                    # only do it once i.e. only replace the first match
)
mapper.AddShaderReplacement(
    vtk.vtkShader.Fragment,
    "//VTK::Base::Init",
    True,
    "//VTK::Base::Init\n"
    "\n l_updateDepth = true;"
    "\n l_opaqueFragPos = vec3(0.0);",
    False
)
mapper.AddShaderReplacement(
    vtk.vtkShader.Fragment,
    "//VTK::Base::Impl",
    True,
    "//VTK::Base::Impl"
    "\n    if(!g_skip && g_srcColor.a > 0.0 && l_updateDepth)"
    "\n      {"
    "\n      l_opaqueFragPos = g_dataPos;"
    "\n      l_updateDepth = false;"
    "\n      }",
    False
)

# mapper.AddShaderReplacement( vtk.vtkShader.Fragment, "//VTK::RenderToImage::Exit", True, "fragOutput0 = vec4(1., 1., 0., 1.)", False);
        
mapper.AddShaderReplacement( vtk.vtkShader.Fragment, "//VTK::RenderToImage::Exit", True,
    """
    //VTK::RenderToImage::Exit
      if (l_opaqueFragPos == vec3(0.0))
        {
        fragOutput0 = vec4(0.0);
        }
      else
        {
        vec4 depthValue = in_projectionMatrix * in_modelViewMatrix *
                          in_volumeMatrix[0] * in_textureDatasetMatrix[0] *
                          vec4(l_opaqueFragPos, 1.0);
        depthValue /= depthValue.w;
        vec3 colorStart = vec3(0., 1., .5);
        vec3 colorEnd = vec3(1., 0., .0);
        float depthRange = gl_DepthRange.far - gl_DepthRange.near;
        float depthRatio = 0.5 * depthRange * depthValue.z + 0.5 * depthRange;
        float fullDepth = gl_DepthRange.far + gl_DepthRange.near;
        fragOutput0 = vec4( mix(colorStart, colorEnd, depthRatio) * depthRange, 1.0);
        fragOutput0 = colorEnd;
        };
    """,
    False
)

volume = vtk.vtkVolume()
volume.SetMapper(mapper)
volume.SetProperty(volumeProperty)

renWin = vtk.vtkRenderWindow()
renWin.SetMultiSamples(0)
renWin.SetSize(800, 800)

ren = vtk.vtkRenderer()
renWin.AddRenderer(ren)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

ren.AddVolume(volume)
ren.GetActiveCamera().Elevation(-60.0)
ren.ResetCamera()
ren.GetActiveCamera().Zoom(1.3)

renWin.Render()
iren.Start()
