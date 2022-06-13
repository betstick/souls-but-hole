from .deserialization import *

import bmesh

class Flver:
	@staticmethod
	def Deserialize(p):
		self = Flver()

		self.name = ReadString(p)
		self.bones = ReadArray(p, Bone.Deserialize)
		self.materials = ReadArray(p, Material.Deserialize)

		self.meshes = ReadArray(p, Mesh.Deserialize)
		for i in range(len(self.meshes)):
			self.meshes[i].name = "m" + str(i)

		self.dummies = ReadArray(p, Dummy.Deserialize)
		for i in range(len(self.dummies)):
			self.dummies[i].index = i

		return self

class Dummy:
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
	@staticmethod
	def Deserialize(p):
		self = Texture_Entry()
		self.path = ReadString(p)
		self.scale_x = ReadFloat(p)
		self.scale_y = ReadFloat(p)
		self.type = ReadString(p)
		return self

class Material:
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
	@staticmethod
	def Deserialize(p):
		self = Faceset()
		self.flags = ReadInt(p)
		self.indices = ReadArray(p, ReadInt3)

		self.lod = 0
		return self

class Mesh:
	@staticmethod
	def Deserialize(p):
		self = Mesh()
		self.name = ""
		self.full_name = ""
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
	@staticmethod
	def Deserialize(p):
		self = MtdParam()
		self.name = ReadString(p)
		self.type = ReadInt(p)
		self.value = MTDParamTypeFuncs[self.type](p)
		return self

class Bone:
	@staticmethod
	def Deserialize(p):
		self = Bone()

		self.name = ReadString(p)
		self.parent_index = ReadInt(p)
		self.head_pos = ReadFloat3(p)
		self.tail_pos = ReadFloat3(p)
		self.bInitialized = ReadBool(p)

		return self