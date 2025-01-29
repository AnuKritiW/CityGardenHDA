"""
State:          City garden::1.0
State type:     city_garden::1.0
Description:    City garden::1.0
Author:         s5647918
Date Created:   November 28, 2024 - 17:46:06
"""

# Usage: This sample adds points to the construction plane.
# 
# If you embedded the state in a SOP HDA:
# 1) Dive in the HDA and add a SOP Add node
# 2) Open the Add node property page and promote the Number of Points parm (Alt+MMB)
# 3) LMB in the viewer to add points.
# 
# If you created a file python state:
# 1) Create an empty geometry and dive in.
# 2) Create an Embedded HDA: Subnetwork, RMB, Create Digital Asset..., Operator Name: test, Save To Library: Embedded, Accept.
# 3) Dive in the Embedded HDA and add a SOP Add node
# 4) Open the Add node property page and promote the Number of Points parm (Alt+MMB)
# 5) Set Node Default State: test in Type Operator Properties, Accept.
# 6) LMB in the viewer to add points.

import hou
import viewerstate.utils as su

class State(object):
    MSG = "LMB to add/remove points to the construction plane."

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer

        self.pressed = False
        self.index = 0    
        self.node = None

    def pointCount(self):
        """ This is how you get the number of instances 
            in a multiparm. 
        """
        try:
            multiparm = self.node.parm("points")
            return multiparm.evalAsInt()
        except:
            return 0

    def start(self):
        if not self.pressed:
            self.scene_viewer.beginStateUndo("Add point")
            self.index = self.pointCount()
            multiparm = self.node.parm("points")
            multiparm.insertMultiParmInstance(self.index)

        self.pressed = True

    def finish(self):
        if self.pressed:
            self.scene_viewer.endStateUndo()
        self.pressed = False


    def onEnter(self, kwargs):
        self.node = kwargs["node"]

        if not self.node:
            raise

        # Check if the toggle parameter is enabled
        enable_add_points = self.node.parm("enable_supertrees").evalAsInt()
        if not enable_add_points:
            # hou.ui.setStatusMessage("Add Points viewer state is disabled.", severity=hou.severityType.Warning)
            self.scene_viewer.setPromptMessage("Add Points viewer state is disabled.")
            return
            
        self.scene_viewer.setPromptMessage( State.MSG )

    def onInterrupt(self,kwargs):
        self.finish()

    def onResume(self, kwargs):
        self.scene_viewer.setPromptMessage( State.MSG )
        
    def remove_index_from_string(self, current_value, index):
        """Remove a specific index from a space-separated string."""
        indices = current_value.split()
        updated_indices = [i for i in indices if i != str(index)]
        return " ".join(updated_indices)
        
    
    def remap_groups(self, removed_point):
        """
        Remap group indices to adjust for a removed point and update Houdini parameters.
    
        Parameters:
            removed_point (int): The index of the point that was removed.
        """
        def expand_ranges(range_string):
            """Expand a range string into a list of individual indices."""
            result = []
            parts = range_string.split()
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    result.extend(range(start, end + 1))
                else:
                    result.append(int(part))
            return sorted(result)
    
        # Retrieve and expand group ranges
        groups = {
            1: expand_ranges(self.node.parm("supertree_group1").evalAsString()),
            2: expand_ranges(self.node.parm("supertree_group2").evalAsString()),
            3: expand_ranges(self.node.parm("supertree_group3").evalAsString()),
        }
    
        # Adjust indices for each group
        remapped_groups = {}
        for group, indices in groups.items():
            remapped_indices = []
            for idx in indices:
                if idx < removed_point:
                    remapped_indices.append(idx)  # Indices below the removed point remain the same
                elif idx > removed_point:
                    remapped_indices.append(idx - 1)  # Indices above the removed point shift down
            remapped_groups[group] = remapped_indices
    
        # Set the remapped indices back into the Houdini parameters
        for group, indices in remapped_groups.items():
            self.node.parm(f"supertree_group{group}").set(" ".join(map(str, indices)))

    def onMouseEvent(self, kwargs):
        """ Find the position of the point to add by 
            intersecting the construction plane. 
        """
        if not self.node.parm("enable_supertrees").evalAsInt():
            return False  # Ignore mouse events when Add Points is disabled
        
        ui_event = kwargs["ui_event"]
        device = ui_event.device()
        origin, direction = ui_event.ray()
        
        position = su.cplaneIntersection(self.scene_viewer, origin, direction)
        
        operation = self.node.parm("operation").evalAsString()  # Evaluates the current menu selection ('Add' or 'Remove')
        grpIdx = self.node.parm("groupIndex").eval()
        
        # Create/move point if LMB is down
        if device.isLeftButton():
        
            if operation == "Add":
                self.start()
                # set the point position
                self.node.parm("usept%d" % self.index).set(1)
                self.node.parmTuple("pt%d" % self.index).set(position)
                
            elif operation == "Remove" or operation == "Select":
                # Retrieve the collision geometry
                
                # Get the Copy to Points node
                copy_to_points_node = self.node.node("OUT_COLLISSION_GEO")  # Adjust the path if necessary
                collision_geo = copy_to_points_node.geometry()
                
                # Output parameters for the intersection
                p = hou.Vector3()  # Intersection point
                n = hou.Vector3()  # Surface normal at the intersection
                uvw = hou.Vector3()  # UVW coordinates at the intersection
                
                # Check for intersection with the collision geometry
                bbox_intersected = collision_geo.intersect(origin, direction, p, n, uvw)
                
                if bbox_intersected != -1:
                    prim = collision_geo.iterPrims()[bbox_intersected]
                    prim_id = prim.attribValue("id")
                    
                    if operation == "Remove":
                        self.node.parm("points").removeMultiParmInstance(prim_id)
                        self.remap_groups(prim_id)
                else:
                    self.finish()
                
            else:
                self.finish()
        else:
            if not device.isLeftButton() and self.pressed:
                if operation == "Add":
                    grpName = "supertree_group"+str(grpIdx+1);
                    current_value = self.node.parm(grpName).evalAsString()
                    new_value = current_value + " " + f"{self.index}" if current_value else f"{self.index}"
                    self.node.parm(grpName).set(new_value)
                self.finish()
                self.pressed = False
        
        return True
        
def createViewerStateTemplate():
    """ Mandatory entry point to create and return the viewer state 
        template to register. """

    state_typename = kwargs["type"].definition().sections()["DefaultState"].contents()
    state_label = "City garden::1.0"
    state_cat = hou.sopNodeTypeCategory()

    template = hou.ViewerStateTemplate(state_typename, state_label, state_cat)
    template.bindFactory(State)
    template.bindIcon(kwargs["type"].icon())

    return template
