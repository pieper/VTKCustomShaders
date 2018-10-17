if True:
  slicer.mrmlScene.Clear(0)
  loadScene('/Users/pieper/data/2018-06-28-Scene.mrb')

layoutManager = slicer.app.layoutManager()
renderWindow = layoutManager.threeDWidget(0).threeDView().renderWindow()
renderer = renderWindow.GetRenderers().GetItemAsObject(0)
mapper = renderer.GetVolumes().GetItemAsObject(0).GetMapper()

def onFiducialMoved():
    p=[0]*3
    fn=slicer.util.getNode('vtkMRMLMarkupsFiducialNode1')
    fn.GetNthFiducialPosition(0,p)
    mapper.GetFragmentCustomUniforms().SetUniform3f( "fiducial", p )
    mapper.Modified()

fn=slicer.util.getNode('vtkMRMLMarkupsFiducialNode1')
fn.AddObserver(fn.PointModifiedEvent, lambda caller,event: onFiducialMoved())

defaultFiducial=[0]*3
mapper.GetFragmentCustomUniforms().AddUniform3f( "fiducial", defaultFiducial )

croppingImplShaderCode = """
    vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
    g_skip = length(texCoordRAS.xyz - fiducial) < 50.;
"""

mapper.AddShaderReplacement(
        vtk.vtkShader.Fragment,
        "//VTK::Cropping::Impl",
        True,
        croppingImplShaderCode,
        False)

renderWindow.Render()

