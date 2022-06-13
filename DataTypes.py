from .deserialization import *

import bmesh

class Flver:
	@staticmethod
	def Deserialize(p):
		self = Flver()

		self.name = ReadString(p)

		self.bones = [Bone.Deserialize(p) for i in range(struct.unpack("i", p.read(4))[0])]

		self.meshes = [Mesh.Deserialize(p) for i in range(struct.unpack("i", p.read(4))[0])]
		for i in range(len(self.meshes)):
			self.meshes[i].name = "m" + str(i)

		self.dummies = ReadArray(p, Dummy.Deserialize)
		for i in range(len(self.dummies)):
			self.dummies[i].index = i

		self.materials = [Material.Deserialize(p) for i in range(struct.unpack("i", p.read(4))[0])]
		
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
		
		self.position = struct.unpack("fff", p.read(12))
		
		self.bone_indices = struct.unpack("iiii", p.read(16))
		self.bone_weights = struct.unpack("ffff", p.read(16))

		self.uvs = [struct.unpack("fff", p.read(12)) for i in range(struct.unpack("i", p.read(4))[0])]

		self.normal = mathutils.Vector((struct.unpack("fff", p.read(12))))
		self.normalw = struct.unpack("f", p.read(4))[0]

		self.colors = [struct.unpack("ffff", p.read(16)) for i in range(struct.unpack("i", p.read(4))[0])]
		
		#self.tangents = []
		#self.bitangent = None
		return self

class Faceset:
	@staticmethod
	def Deserialize(p):
		self = Faceset()
		self.flags = ReadInt(p)
		self.indices = [struct.unpack("i", p.read(4)) for i in range(struct.unpack("i", p.read(4))[0])]
		
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
		self.vertices = [Vertex.Deserialize(p) for i in range(struct.unpack("i", p.read(4))[0])]
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
		self.translation = struct.unpack("fff", p.read(12))
		print(self.translation)
		self.rotation = struct.unpack("fff", p.read(12))
		self.scale = struct.unpack("fff", p.read(12))

		#relation
		self.parent_index = struct.unpack("i", p.read(4))[0]
		self.child_index = struct.unpack("i", p.read(4))[0]
		self.next_sibling_index = struct.unpack("i", p.read(4))[0]
		self.previous_sibling_index = struct.unpack("i", p.read(4))[0]

		return self