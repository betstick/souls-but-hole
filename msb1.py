import bpy
import mathutils
import numpy
import bmesh
from collections import defaultdict
from mathutils import Vector
from mathutils import Matrix
from os.path import exists
import math

from .DataTypes import *
from .deserialization import *

class MSB1:
	__slots__ = 'events', 'models', 'parts', 'regions'

	@staticmethod
	def Deserialize(p):
		self = MSB1()

		self.events = MSB1Events.Deserialize(p)
		self.models = MSB1Models.Deserialize(p)
		self.parts = MSB1Parts.Deserialize(p)
		self.regions = ReadArray(p, Region.Deserialize)

		return self

class MSB1Events:
	__slots__ = 'environments', 'generators', 'lights', 'map_offsets', 'messages', 'navmeshes', 'obj_acts', 'psuedo_multiplayers', 'sfxs', 'sounds', 'spawn_points', 'treasures', 'wind_sfxs'

	@staticmethod
	def Deserialize(p):
		self = MSB1Events()

		self.environments = ReadArray(p, EventEnvironment.Deserialize)
		self.generators = ReadArray(p, EventGenerator.Deserialize)
		self.lights = ReadArray(p, EventLight.Deserialize)
		self.map_offsets = ReadArray(p, EventMapOffset.Deserialize)
		self.messages = ReadArray(p, EventMessage.Deserialize)
		self.navmeshes = ReadArray(p, EventNavmesh.Deserialize)
		self.obj_acts = ReadArray(p, EventObjAct.Deserialize)
		self.psuedo_multiplayers = ReadArray(p, EventPseudoMultiplayer.Deserialize)
		self.sfxs = ReadArray(p, EventSFX.Deserialize)
		self.sounds = ReadArray(p, EventSound.Deserialize)
		self.spawn_points = ReadArray(p, EventSpawnPoint.Deserialize)
		self.treasures = ReadArray(p, EventTreasure.Deserialize)
		self.wind_sfxs = ReadArray(p, EventWindSFX.Deserialize)

		return self

class MSB1Models:
	__slots__ = 'collisions', 'enemies', 'map_pieces', 'navmeshes', 'objects', 'players'

	@staticmethod
	def Deserialize(p):
		self = MSB1Models()

		self.collisions = ReadArray(p, ModelCollision.Deserialize)
		self.enemies = ReadArray(p, ModelEnemy.Deserialize)
		self.map_pieces = ReadArray(p, ModelMapPiece.Deserialize)
		self.navmeshes = ReadArray(p, ModelNavmesh.Deserialize)
		self.objects = ReadArray(p, ModelObject.Deserialize)
		self.players = ReadArray(p, ModelPlayer.Deserialize)

		return self

class MSB1Parts:
	__slots__ = 'collisions', 'connect_collisions', 'dummy_enemies', 'dummy_objects', 'enemies', 'map_pieces', 'navmeshes', 'objects', 'players'

	@staticmethod
	def Deserialize(p):
		self = MSB1Parts()

		self.collisions = ReadArray(p, PartCollision.Deserialize)
		self.connect_collisions = ReadArray(p, PartConnectCollision.Deserialize)
		self.dummy_enemies = ReadArray(p, PartDummyEnemy.Deserialize)
		self.dummy_objects = ReadArray(p, PartDummyObject.Deserialize)
		self.enemies = ReadArray(p, PartEnemy.Deserialize)
		self.map_pieces = ReadArray(p, PartMapPiece.Deserialize)
		self.navmeshes = ReadArray(p, PartNavmesh.Deserialize)
		self.objects = ReadArray(p, PartObject.Deserialize)
		self.players = ReadArray(p, PartPlayer.Deserialize)

		return self

class EventEnvironment:
	__slots__ = 'unk_t00', 'unk_t04', 'unk_t08', 'unk_t0C', 'unk_t10', 'unk_t14', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventEnvironment()

		self.unk_t00 = ReadInt(p)
		self.unk_t04 = ReadFloat(p)
		self.unk_t08 = ReadFloat(p)
		self.unk_t0C = ReadFloat(p)
		self.unk_t10 = ReadFloat(p)
		self.unk_t14 = ReadFloat(p)
		
		self.event = Event.Deserialize(p)

		return self

class EventGenerator:
	__slots__ = 'gen_type', 'initial_spawn_count', 'limit_num', 'max_gen_num', 'max_interval', 'max_num', 'min_gen_num', 'min_interval', 'spawn_part_names', 'spawn_point_names', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventGenerator()

		self.gen_type = ReadSByte(p)
		self.initial_spawn_count = ReadInt(p)
		self.limit_num = ReadSShort(p)
		self.max_gen_num = ReadSShort(p)
		self.max_interval = ReadFloat(p)
		self.max_num = ReadUByte(p)
		self.min_gen_num = ReadSShort(p)
		self.min_interval = ReadFloat(p)
		self.spawn_part_names = ReadArray(p, ReadString)
		self.spawn_point_names = ReadArray(p, ReadString)

		self.event = Event.Deserialize(p)

		return self

class EventLight:
	__slots__ = 'point_light_id', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventLight()

		self.point_light_id = ReadInt(p)
		self.event = Event.Deserialize(p)

		return self

class EventMapOffset:
	__slots__ = 'degree', 'position', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventMapOffset()

		self.degree = ReadFloat(p)
		self.position = ReadFloat3(p)
		
		self.event = Event.Deserialize(p)

		return self

class EventMessage:
	__slots__ = 'hidden', 'message_id', 'unk_t02', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventMessage()

		self.hidden = ReadBool(p)
		self.message_id = ReadSShort(p)
		self.unk_t02 = ReadSShort(p)

		self.event = Event.Deserialize(p)

		return self

class EventNavmesh:
	__slots__ = 'navmesh_region_name', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventNavmesh()

		self.navmesh_region_name = ReadString(p)
		self.event = Event.Deserialize(p)

		return self

class EventObjAct:
	__slots__ = 'event_flag_id', 'obj_act_entity_id', 'obj_act_param_id', 'obj_act_part_name', 'obj_act_state', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventObjAct()

		self.event_flag_id = ReadInt(p)
		self.obj_act_entity_id = ReadInt(p)
		self.obj_act_entity_id = ReadSShort(p)
		self.obj_act_part_name = ReadString(p)
		self.obj_act_state = ReadUShort(p)

		self.event = Event.Deserialize(p)

		return self

class EventPseudoMultiplayer:
	__slots__ = 'activate_goods_id', 'event_flag_id', 'host_entity_id', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventPseudoMultiplayer()

		self.activate_goods_id = ReadInt(p)
		self.event_flag_id = ReadInt(p)
		self.host_entity_id = ReadInt(p)

		self.event = Event.Deserialize(p)

		return self

class EventSFX:
	__slots__ = 'ffx_id', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventSFX()

		self.ffx_id = ReadInt(p)
		self.event = Event.Deserialize(p)

		return self

class EventSound:
	__slots__ = 'sound_id', 'sound_type', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventSound()

		self.sound_id = ReadInt(p)
		self.sound_type = ReadInt(p)

		self.event = Event.Deserialize(p)

		return self

class EventSpawnPoint:
	__slots__ = 'spawn_point_name', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventSpawnPoint()

		self.spawn_point_name = ReadString(p)
		self.event = Event.Deserialize(p)

		return self

class EventTreasure:
	__slots__ = 'in_chest', 'item_lots', 'start_disabled', 'treasure_part_name', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventTreasure()

		self.in_chest = ReadBool(p)
		self.item_lots = ReadArray(p, ReadInt)
		self.start_disabled = ReadBool(p)
		self.treasure_part_name = ReadString(p)

		self.event = Event.Deserialize(p)

		return self

class EventWindSFX:
	__slots__ = 'unk_t0c', 'unk_t1c', 'wind_swing_cycle0', 'wind_swing_cycle1', 'wind_swing_cycle2', 'wind_swing_cycle3', 'wing_swing_pow0', 'wing_swing_pow1', 'wing_swing_pow2', 'wing_swing_pow3', 'wind_vec_max', 'wind_vec_min', 'event'

	@staticmethod
	def Deserialize(p):
		self = EventWindSFX()

		self.unk_t0c = ReadFloat(p)
		self.unk_t1c = ReadFloat(p)
		self.wind_swing_cycle0 = ReadFloat(p)
		self.wind_swing_cycle1 = ReadFloat(p)
		self.wind_swing_cycle2 = ReadFloat(p)
		self.wind_swing_cycle3 = ReadFloat(p)
		self.wing_swing_pow0 = ReadFloat(p)
		self.wing_swing_pow1 = ReadFloat(p)
		self.wing_swing_pow2 = ReadFloat(p)
		self.wing_swing_pow3 = ReadFloat(p)
		self.wind_vec_max = ReadFloat3(p)
		self.wind_vec_min = ReadFloat3(p)

		self.event = Event.Deserialize(p)

		return self

class ModelCollision:
	__slots__ = 'name', 'sib_path'

	@staticmethod
	def Deserialize(p):
		self = ModelCollision()

		self.name = ReadString(p)
		self.sib_path = ReadString(p)

		return self

class ModelEnemy:
	__slots__ = 'name', 'sib_path'

	@staticmethod
	def Deserialize(p):
		self = ModelEnemy()

		self.name = ReadString(p)
		self.sib_path = ReadString(p)

		return self

class ModelMapPiece:
	__slots__ = 'name', 'sib_path'

	@staticmethod
	def Deserialize(p):
		self = ModelMapPiece()

		self.name = ReadString(p)
		self.sib_path = ReadString(p)

		return self

class ModelNavmesh:
	__slots__ = 'name', 'sib_path'

	@staticmethod
	def Deserialize(p):
		self = ModelNavmesh()

		self.name = ReadString(p)
		self.sib_path = ReadString(p)

		return self

class ModelObject:
	__slots__ = 'name', 'sib_path'

	@staticmethod
	def Deserialize(p):
		self = ModelObject()

		self.name = ReadString(p)
		self.sib_path = ReadString(p)

		return self

class ModelPlayer:
	__slots__ = 'name', 'sib_path'

	@staticmethod
	def Deserialize(p):
		self = ModelPlayer()

		self.name = ReadString(p)
		self.sib_path = ReadString(p)

		return self

class PartCollision:
	__slots__ = 'disable_bonefire_entity_id', 'disable_start', 'env_light_map_spot_index', 'hit_filter_id', 'lock_cam_param_id1', 'lock_cam_param_id2', 'map_name_id', 'nvm_groups', 'play_region_id', 'reflect_plane_height', 'sound_space_type', 'part'

	@staticmethod
	def Deserialize(p):
		self = PartCollision()
		
		self.disable_bonefire_entity_id = ReadInt(p)
		self.disable_start = ReadSShort(p)
		self.env_light_map_spot_index = ReadSShort(p)
		self.hit_filter_id = ReadUByte(p)
		self.lock_cam_param_id1 = ReadSShort(p)
		self.lock_cam_param_id2 = ReadSShort(p)
		self.map_name_id = ReadSShort(p)
		self.nvm_groups = ReadArray(p, ReadUInt)
		self.play_region_id = ReadInt(p)
		self.reflect_plane_height = ReadFloat(p)
		self.sound_space_type = ReadUByte(p)

		self.part = Part.Deserialize(p)

		return self

class PartConnectCollision:
	__slots__ = 'collision_name', 'map_id', 'part'

	@staticmethod
	def Deserialize(p):
		self = PartConnectCollision()
		
		self.collision_name = ReadString(p)
		self.map_id = ReadArray(p, ReadUByte)

		self.part = Part.Deserialize(p)

		return self

class PartDummyObject:
	__slots__ = 'object_base'

	@staticmethod
	def Deserialize(p):
		self = PartDummyObject()
		self.object_base = ObjectBase.Deserialize(p)
		return self

class PartDummyEnemy:
	__slots__ = 'enemy_base'

	@staticmethod
	def Deserialize(p):
		self = PartDummyEnemy()
		self.enemy_base = EnemyBase.Deserialize(p)
		return self

class PartEnemy:
	__slots__ = 'enemy_base'

	@staticmethod
	def Deserialize(p):
		self = PartEnemy()
		self.enemy_base = EnemyBase.Deserialize(p)
		return self

class PartMapPiece:
	__slots__ = 'part'

	@staticmethod
	def Deserialize(p):
		self = PartMapPiece()
		self.part = Part.Deserialize(p)
		return self

class PartNavmesh:
	__slots__ = 'nvm_groups', 'part'

	@staticmethod
	def Deserialize(p):
		self = PartNavmesh()
		self.nvm_groups = ReadArray(p, ReadUInt)
		self.part = Part.Deserialize(p)
		return self

class PartObject:
	__slots__ = 'part'

	@staticmethod
	def Deserialize(p):
		self = PartObject()
		self.part = ObjectBase.Deserialize(p)
		return self

class PartPlayer:
	__slots__ = 'part'

	@staticmethod
	def Deserialize(p):
		self = PartPlayer()
		self.part = Part.Deserialize(p)
		return self

class Region:
	__slots__ = 'entity_id', 'name', 'position', 'rotation', 'shape'

	@staticmethod
	def Deserialize(p):
		self = Region()

		self.entity_id = ReadInt(p)
		self.name = ReadString(p)
		self.position = ReadFloat3(p)
		self.rotation = ReadFloat3(p)

		self.shape = Shape.Deserialize(p)

		return self

class Event:
	__slots__ = 'entity_id', 'event_id', 'name', 'part_name', 'region_name'
	
	@staticmethod
	def Deserialize(p):
		self = Event()
		
		self.entity_id = ReadInt(p)
		self.event_id = ReadInt(p)
		self.name = ReadString(p)
		self.part_name = ReadString(p)
		self.region_name = ReadString(p)

		return self

class ObjectBase:
	__slots__ = 'break_term', 'collision_name', 'init_anim_id', 'net_sync_type', 'unk_t0e', 'unk_t10', 'part'
	
	@staticmethod
	def Deserialize(p):
		self = ObjectBase()

		self.break_term = ReadSByte(p)
		self.collision_name = ReadString(p)
		self.init_anim_id = ReadSShort(p)
		self.net_sync_type = ReadSByte(p)
		self.unk_t0e = ReadSShort(p)
		self.unk_t10 = ReadInt(p)

		self.part = Part.Deserialize(p)

		return self

class EnemyBase:
	__slots__ = 'chara_init_id', 'collision_name', 'damage_anim_id', 'init_anim_id', 'move_point_names', 'npc_param_id', 'platoon_id', 'point_move_type', 'talk_id', 'think_param_id', 'part'

	@staticmethod
	def Deserialize(p):
		self = EnemyBase()

		self.chara_init_id = ReadInt(p)
		self.collision_name = ReadString(p)
		self.damage_anim_id = ReadInt(p)
		self.init_anim_id = ReadInt(p)
		self.move_point_names = ReadArray(p, ReadString)
		self.npc_param_id = ReadInt(p)
		self.platoon_id = ReadUShort(p)
		self.point_move_type = ReadUByte(p)
		self.talk_id = ReadInt(p)
		self.think_param_id = ReadInt(p)

		self.part = Part.Deserialize(p)

		return self

class Part:
	__slots__ = 'disable_point_light_effect', 'disp_groups', 'dof_id', 'draw_by_reflect_cam', 'draw_groups','draw_only_reflect_cam', 'entity_id', 'fog_id', 'is_shadow_dest', 'is_shadow_only', 'is_shadow_src', 'lantern_id', 'lens_flare_id', 'light_id', 'lod_param_id', 'model_name', 'name', 'position', 'rotation', 'scale', 'scatter_id', 'shadow_id', 'sib_path', 'tone_correct_id', 'tone_map_id', 'use_depth_bias_float'

	@staticmethod
	def Deserialize(p):
		self = Part()

		self.disable_point_light_effect = ReadBool(p)
		self.disp_groups = ReadArray(p, ReadUInt)
		self.dof_id = ReadUByte(p)
		self.draw_by_reflect_cam = ReadBool(p)
		self.draw_groups = ReadArray(p, ReadUInt)
		self.draw_only_reflect_cam = ReadBool(p)
		self.entity_id = ReadInt(p)
		self.fog_id = ReadUByte(p)
		self.is_shadow_dest = ReadBool(p)
		self.is_shadow_only = ReadBool(p)
		self.is_shadow_src = ReadBool(p)
		self.lantern_id = ReadUByte(p)
		self.lens_flare_id = ReadUByte(p)
		self.light_id = ReadUByte(p)
		self.lod_param_id = ReadUByte(p)
		self.model_name = ReadString(p)
		self.name = ReadString(p)
		self.position = ReadFloat3(p)
		self.rotation = ReadFloat3(p)
		self.scale = ReadFloat3(p)
		self.scatter_id = ReadUByte(p)
		self.shadow_id = ReadUByte(p)
		self.sib_path = ReadString(p)
		self.tone_correct_id = ReadUByte(p)
		self.tone_map_id = ReadUByte(p)
		self.use_depth_bias_float = ReadBool(p)

		return self

class Shape:
	__slots__ = 'unk'

	@staticmethod
	def Deserialize(p):
		self = Shape()

		self.unk = ReadString(p)

		return self