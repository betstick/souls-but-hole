from multiprocessing import dummy
from bpy.utils import register_class, unregister_class
if 'bpy' not in locals():
    import bpy
    from . import (
        flver,
        material,
        mesh,
        skeleton,
        util,
        from_dummy,
        mtd
    )
else:
    import imp
    imp.reload(flver)
    imp.reload(skeleton)
    imp.reload(material)
    imp.reload(mesh)
    imp.reload(util)
    imp.reload(from_dummy)
    imp.reload(mtd)

#none of these actually need to be registered with bpy
"""classes = (
    flver.Flver,
    flver.Header,
    material.Texture_Entry,
    material.Material,
    mesh.Mesh,
    mesh.Vertex,
    mesh.Faceset,
    skeleton.Skeleton,
    skeleton.Bone,
    normals.VertexNormalWeight,
    normals.Cache,
    normals.LinkedFaceAreaCache,
    normals.Vec3,
)

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)"""