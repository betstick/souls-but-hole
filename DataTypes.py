from .deserialization import *

import bmesh

class Flver:
	__slots__ = 'name', 'bones', 'materials', 'meshes', 'dummies'

	@staticmethod
	def Deserialize(p):
		self = Flver()

		self.name = ReadString(p)
		self.bones = ReadArray(p, Bone.Deserialize)
		self.materials = ReadArray(p, Material.Deserialize)

		self.meshes = ReadArray(p, Mesh.Deserialize)

		self.dummies = ReadArray(p, Dummy.Deserialize)

		return self

class Dummy:
	__slots__ = 'refid', 'position', 'upward', 'use_upward', 'attach_bone_index', 'parent_bone_index'

	@staticmethod
	def Deserialize(p):
		self = Dummy()
		self.refid = ReadInt(p)
		self.position = ReadFloat3(p)
		self.upward = ReadFloat3(p)
		self.use_upward = ReadBool(p)
		self.attach_bone_index = ReadInt(p)
		self.parent_bone_index = ReadInt(p)
		return self

#MTD lists for applying fixes
metals = ['P_Metal[DSB]_Edge.mtd','C_Metal[DSB].mtd','P_Metal[DSB].mtd']
seath = ['C_5290_Body[DSB][M].mtd','C_5290_Body[DSB].mtd']

class Texture_Entry:
	__slots__ = 'path', 'scale_x', 'scale_y', 'type'

	@staticmethod
	def Deserialize(p):
		self = Texture_Entry()
		self.path = ReadString(p)
		self.scale_x = ReadFloat(p)
		self.scale_y = ReadFloat(p)
		self.type = ReadString(p)
		return self

class Material:
	__slots__ = 'name', 'mtd', 'flags', 'gx_index', 'textures', 'mtd_params'

	@staticmethod
	def Deserialize(p):
		self = Material()
		self.name = ReadString(p)
		self.mtd = ReadString(p)
		self.flags = ReadInt(p)
		self.gx_index = ReadInt(p)
		self.textures = ReadArray(p, Texture_Entry.Deserialize)
		self.mtd_params = ReadArray(p, MtdParam.Deserialize)
		return self

class Vertex:
	__slots__ = 'position', 'bone_indices', 'bone_weights', 'uvs', 'normal', 'normalw', 'colors'

	@staticmethod
	def Deserialize(p):
		self = Vertex()

		self.position = ReadFloat3(p)

		self.bone_indices = ReadInt4(p)
		self.bone_weights = ReadFloat4(p)

		self.uvs = ReadArray(p, ReadFloat3)

		self.normal = ReadFloat3(p)
		self.normalw = ReadFloat(p)

		self.colors = ReadArray(p, ReadFloat4)

		return self

class Faceset:
	__slots__ = 'flags', 'indices', 'lod'

	@staticmethod
	def Deserialize(p):
		self = Faceset()
		self.flags = ReadInt(p)
		self.indices = ReadArray(p, ReadInt3)

		self.lod = 0
		return self

class Mesh:
	__slots__ = 'bone_indices', 'defaultBoneIndex', 'bone_weights', 'material_index', 'vertices', 'facesets', 'bm'

	@staticmethod
	def Deserialize(p):
		self = Mesh()
		self.bone_indices = ReadArray(p, ReadInt)
		self.defaultBoneIndex = ReadInt(p)
		self.material_index = ReadInt(p)
		self.vertices = ReadArray(p, Vertex.Deserialize)
		self.facesets = Faceset.Deserialize(p)

		self.bm = bmesh.new()
		return self

# Needs to be precisely matched to SoulsFormats enum
MTDParamTypeFuncs = [ReadBool, ReadInt, ReadInt2, ReadFloat, ReadFloat2, ReadFloat3, ReadFloat4]

class MtdParam:
	__slots__ = 'name', 'type', 'value'

	@staticmethod
	def Deserialize(p):
		self = MtdParam()
		self.name = ReadString(p)
		self.type = ReadInt(p)
		self.value = MTDParamTypeFuncs[self.type](p)
		return self

class Bone:
	__slots__ = 'name', 'parent_index', 'head_pos', 'tail_pos', 'bInitialized'

	@staticmethod
	def Deserialize(p):
		self = Bone()

		self.name = ReadString(p)
		self.parent_index = ReadInt(p)
		self.head_pos = ReadFloat3(p)
		self.tail_pos = ReadFloat3(p)
		self.bInitialized = ReadBool(p)

		return self