from operator import mod
from sys import stdout
import bpy
import socket
import time

def scrub_mesh_weights(context):
	meshes = []

	for obj in bpy.context.selected_objects:
		if obj.type == "MESH":
			meshes.append(obj)

	#for some reason, this is extremely fast?
	#removes 0 weighted verts from vertex_groups
	for mesh in meshes:
		for v in mesh.data.vertices:
			if len(v.groups) > 4:
				v.select = True
			else:
				v.select = False
			for g in v.groups:
				if g.weight == 0.0:
					mesh.vertex_groups[g.group].remove([v.index])

	#removes vertex groups from meshes that have no vertices
	for mesh in meshes:
		#keep track of vertex groups that are actually in use
		used_vertex_groups = set()

		for v in mesh.data.vertices:
			for g in v.groups:
				used_vertex_groups.add(mesh.vertex_groups[g.group].name)

		#removes vertex groups by name that aren't in the list
		for g in mesh.vertex_groups:
			if g.name not in used_vertex_groups:
				mesh.vertex_groups.remove(mesh.vertex_groups[g.name])

def select_overweighted_verts(context):
	meshes = []

	for obj in bpy.context.selected_objects:
		if obj.type == "MESH":
			meshes.append(obj)

	#selects all verts with more than 4 groups
	for mesh in meshes:
		for v in mesh.data.vertices:
			if len(v.groups) > 4:
				v.select = True
			else:
				v.select = False