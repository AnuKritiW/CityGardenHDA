import hou

# Get the current HDA node (the HDA itself)
hda_node = hou.pwd()

# Create two null nodes in the same context as the HDA
children: hou.Node = hda_node.children()
node_idx = len(children)-1

garden_null = hda_node.createNode("null", f"{hda_node.name()}_Garden")
fireworks_null = hda_node.createNode("null", f"{hda_node.name()}_Fireworks")

# Ensure the HDA has output definitions for the connections
try:
    garden_null.setInput(0, children[node_idx], 0)
    fireworks_null.setInput(0, children[node_idx], 1)
except Exception as e:
    print(f"Error connecting null nodes: {e}")

# Organize the nodes in the network
hda_node.layoutChildren()
