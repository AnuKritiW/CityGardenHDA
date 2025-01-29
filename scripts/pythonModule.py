import toolutils

def clearAllTemplateFlags(sopnode):
    # Clear all template flags in the current network
    for child in sopnode.children():
        if hasattr(child, "setTemplateFlag"):
            child.setTemplateFlag(False)

def paintIt(scriptargs, nodeType, operation):
    sopnode = scriptargs['node']
    viewer = toolutils.sceneViewer()

    if nodeType == "palm":
        paint = sopnode.node("attribpaint_travellerspalm")
    elif nodeType == "grass":
        paint = sopnode.node("attribpaint_grasstufts")
    elif nodeType == "orchid":
        paint = sopnode.node("attribpaint_orchids")
    elif nodeType == "skimmia":
        paint = sopnode.node("attribpaint_skimmia")
    else:
        return
        
    # Check if the paint node exists
    if not paint:
        hou.ui.displayMessage(f"Paint node for {nodeType} not found.")
        return
        
    if operation == "paint":
        paint.parm("lmboperation").set(0)
    elif operation == "erase":
        paint.parm("lmboperation").set(2)
    else:
        hou.ui.displayMessage(f"Unknown operation: {operation}")
        return

    paint.setDisplayFlag(True)
    clearAllTemplateFlags(sopnode)
    sopnode.parm("enable_supertrees").set(0)
    
    outputNode = sopnode.node("SCENE_FINAL")
    outputNode.setTemplateFlag(True)
    
    paint.setCurrent(True, True)
    viewer.enterCurrentNodeState()

def enterCurveTool(scriptargs, nodeType, mode, grp=None):
    sopnode = scriptargs['node']
    viewer = toolutils.sceneViewer()
    
    if nodeType == "stone":
        curveNode = sopnode.node("curve_stonePath")
    elif nodeType == "plants" and grp != None:
        if grp == 1:
            curveNode = sopnode.node("curve_area_patch1")
        elif grp == 2:
            curveNode = sopnode.node("curve_area_patch2")
        elif grp == 3:
            curveNode = sopnode.node("curve_area_patch3")
    else:
        return;
    
    if mode == "draw":
        curveNode.parm("mode").set("BUTTONS_curve_mode_draw")
    elif mode == "edit":
        curveNode.parm("mode").set("BUTTONS_curve_mode_select")
    else:
        return
    
    curveNode.setDisplayFlag(True)
    clearAllTemplateFlags(sopnode)
    sopnode.parm("enable_supertrees").set(0)
    
    outputNode = sopnode.node("SCENE_FINAL")
    outputNode.setTemplateFlag(True)
        
    curveNode.setCurrent(True, True)
    viewer.enterCurrentNodeState()
    enableConstructionPlane(viewer)

def enableConstructionPlane(viewer):
    if viewer is not None:
        for viewport in viewer.viewports():
            # Get the construction plane object
            cp = viewer.constructionPlane()
            # Enable the construction plane
            cp.setIsVisible(True)
            viewer = cp.sceneViewer()

def count_plants(scriptargs, grp):
    # Get the HDA node
    node = scriptargs['node']
    grp_str = str(grp)
    
    # List of toggle parameter names
    toggle_names = ["grass_toggle"+grp_str, "traveller_palm_toggle"+grp_str, "orchid_toggle"+grp_str, "skimmia_toggle"+grp_str]
    
    # Count how many toggles are checked
    checked_count = sum([node.parm(toggle).eval() for toggle in toggle_names])
    
    # Update the integer parameter
    node.parm("num_plants"+grp_str).set(checked_count)

def enter_viewerstate():
    scene_viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    
    # Activate the viewer state
    scene_viewer.setCurrentState("city_garden::1.0")
        
def clear_supertrees(scriptargs):
    # Get the HDA node
    sopnode = scriptargs['node']
    node = sopnode.node("add_supertree")
    
    # Clear multiparm instances
    multiparm = node.parm("points")
    if multiparm:
        multiparm.set(0)
    
    # Clear associated string parameters
    group_count = 3  # Number of group parameters to clear
    for i in range(group_count):
        group_name = f"supertree_group{i+1}"
        group_parm = sopnode.parm(group_name)
        if group_parm:
            group_parm.set("")  # Reset the string parameter

def setViewerToRender(scriptargs):
    # Define the target LOP node and the HDA's path
    hda_path = scriptargs['node'].path()
    lop_node_path = f"{hda_path}/lopnet1"
    
    # Navigate the Network Editor to the target LOP node
    pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if pane and hou.node(lop_node_path):
        pane.setPwd(hou.node(lop_node_path))
    else:
        hou.ui.displayMessage(f"Node {lop_node_path} does not exist.")
        return
    
    # Set the viewport to use Karma CPU and Perspective View
    scene_view = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    if scene_view:
        viewport = scene_view.curViewport()
        
        # Set the view to Perspective (if available)
        if viewport.type() != hou.geometryViewportType.Perspective:
            viewport.changeType(hou.geometryViewportType.Perspective)
    else:
        hou.ui.displayMessage("No Scene Viewer pane found.")
        