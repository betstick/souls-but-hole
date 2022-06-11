from .deserialization import *

import bmesh

class Header:
	def __init__(self, bone_count, mesh_count, mat_count, dummy_count, gxlist_count):
		self.bone_count = bone_count
		self.mesh_count = mesh_count
		self.mat_count = mat_count
		self.dummy_count = dummy_count
		self.gxlist_count = gxlist_count

class Flver:
	@staticmethod
	def Deserialize(p):
		self = Flver()

		self.name = ReadString(p)

		self.headerinfo = Header(ReadInt(p), ReadInt(p), ReadInt(p), ReadInt(p), ReadInt(p))

		#self.skeleton = skeleton.Skeleton(ReadArray(p, skeleton.Bone.Deserialize))
		self.bones = ReadArray(p, Bone.Deserialize)
		self.materials = ReadArray(p, Material.Deserialize)

		self.meshes = ReadArray(p, Mesh.Deserialize)
		for i in range(len(self.meshes)):
			self.meshes[i].name = "m" + str(i)

		self.dummies = ReadArray(p, Dummy.Deserialize)
		for i in range(len(self.dummies)):
			self.dummies[i].index = i

		self.armature = None

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
		#ReadFloat3(p)
		self.position = ReadFloat3(p)
		#ReadInt4(p)
		self.bone_indices = ReadInt4(p)
		#ReadFloat4(p)
		self.bone_weights = ReadFloat4(p)
		#ReadArray(p, ReadFloat3)
		self.uvs = ReadArray(p, ReadFloat3)
		#ReadFloat3(p)
		self.normal = ReadFloat3(p)
		#ReadFloat(p)
		self.normalw = ReadFloat(p)

		self.colors = ReadArray(p, ReadFloat4)
		#self.tangents = []
		#	self.bitangent = None
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

		# transform
		self.translation = ReadFloat3(p)
		self.rotation = ReadFloat3(p)
		self.scale = ReadFloat3(p)

		#relation
		self.parent_index = ReadInt(p)
		self.child_index = ReadInt(p)
		self.next_sibling_index = ReadInt(p)
		self.previous_sibling_index = ReadInt(p)

		return self