from operator import mod
from sys import stdout
import bpy
import socket
import time

from .. import flver

def request(socket, message):
	socket.sendall(message.encode('utf-8'))
	bool = True
	ret = ""
	while bool:
		msg = (socket.recv(8192)).decode('utf-8')
		if str(msg)[-1] == "#":
			ret += str(msg)[:-1] #slice off the '#', its the null terminator
			bool = False
		else:
			ret += str(msg)
	return ret.split("\n")

def export_asset(context, asset_id, asset_type):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		host="127.0.0.1" #TODO: read from preferences, if they're set
		port=13131

		sock.connect((host, port))

		tag = ""
		if asset_type == "Character":
			tag = "c"
		elif asset_type == "Map":
			tag = "m"
		elif asset_type == "Part":
			tag = "p"
		
		armature = bpy.data.objects[tag + str(asset_id) + "_armature"]

		meshes = []

		for child in armature.children:
			if child.type == "MESH":
				meshes.append(child)

		#model = flver.flver.Flver()

		for mesh in meshes:
			bpy.ops.export_mesh
