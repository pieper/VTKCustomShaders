
slicer.mrmlScene.Clear(0)
loadScene('/Users/pieper/data/2018-06-28-Scene.mrb')

layoutManager = slicer.app.layoutManager()
renderWindow = layoutManager.threeDWidget(0).threeDView().renderWindow()
renderer = renderWindow.GetRenderers().GetItemAsObject(0)
mapper = renderer.GetVolumes().GetItemAsObject(0).GetMapper()

@vtk.calldata_type(vtk.VTK_OBJECT)
def shaderCallback(vtkObject, event, callData):
    p=[0]*3
    fn=slicer.util.getNode('vtkMRMLMarkupsFiducialNode1')
    fn.GetNthFiducialPosition(0,p)
    callData.SetUniform3f( "fiducial", p )
    slicer.modules.shaderProgram = callData

mapper.AddObserver(vtk.vtkCommand.UpdateShaderEvent, shaderCallback)

slicer.modules.shaderProgram = None
def onFiducialMoved():
    if slicer.modules.shaderProgram:
        p=[0]*3
        fn=slicer.util.getNode('vtkMRMLMarkupsFiducialNode1')
        fn.GetNthFiducialPosition(0,p)
        slicer.modules.shaderProgram.SetUniform3f( "fiducial", p )
        mapper.Modified()

fn=slicer.util.getNode('vtkMRMLMarkupsFiducialNode1')
fn.AddObserver(fn.PointModifiedEvent, lambda caller,event: onFiducialMoved())

mapper.AddShaderReplacement(
        vtk.vtkShader.Fragment,
        "//VTK::Cropping::Dec", True,
        """
            uniform vec3 fiducial;
        """,
        False)

croppingImplShaderCode = """
    vec4 fiducialTexCoord = in_inverseTextureDatasetMatrix[0] * in_inverseVolumeMatrix[0] * vec4(fiducial,1.0);
    g_skip = length(g_dataPos - fiducialTexCoord.xyz) < 0.3;
"""

mapper.AddShaderReplacement(
        vtk.vtkShader.Fragment,
        "//VTK::Cropping::Impl",
        True,
        croppingImplShaderCode,
        False)

rw.Render()
