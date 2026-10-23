"""Outils communs pour générer des modèles low poly avec Blender en headless (module bpy).

Principe des couleurs : une seule petite texture « palette » (une case par couleur).
Chaque pièce a ses UV posés au centre de la case de sa couleur. Roblox importe ainsi
toutes les couleurs avec une seule texture, sans avoir besoin de peindre quoi que ce soit.

Échelle : 1 unité Blender = 1 stud Roblox. Les modèles regardent vers -Y et reposent sur z = 0.
"""
import math
import os
import random

import bpy  # doit être importé avant bmesh
import bmesh  # noqa: E402
from mathutils import Euler, Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS = os.path.join(ROOT, "exports")
PREVIEWS = os.path.join(ROOT, "previews")

# Couleurs (sRGB 0-255). L'ordre fixe la case dans la palette : ajouter à la fin seulement.
PALETTE = {
    "laine": (244, 236, 214),
    "laine_ombre": (222, 210, 182),
    "visage_belier": (74, 62, 58),
    "corne": (196, 164, 116),
    "corne_fonce": (150, 118, 80),
    "sabot": (46, 40, 38),
    "oeil_ambre": (255, 190, 40),
    "oeil_noir": (24, 22, 26),
    "fleur_jaune": (255, 214, 64),
    "fleur_rose": (246, 140, 178),
    "fleur_blanche": (255, 255, 250),
    "feuille": (88, 170, 72),
    "feuille_fonce": (52, 120, 58),
    "lievre": (176, 120, 72),
    "lievre_fonce": (130, 86, 52),
    "lievre_creme": (240, 222, 190),
    "rose_oreille": (238, 160, 160),
    "truffe": (214, 104, 120),
    "bois": (122, 84, 50),
    "bois_clair": (168, 124, 80),
    "cloche_or": (232, 180, 52),
    "herbe_sol": (110, 180, 80),
    "oeil_vert": (150, 255, 90),
    "dent": (250, 248, 240),
    "caramel": (226, 140, 58),
    "caramel_fonce": (198, 112, 44),
    "blanc_doux": (250, 244, 234),
    "brun_patte": (92, 56, 44),
    "noir_brillant": (34, 26, 28),
    "joue_rose": (246, 156, 150),
}

GRID = 8          # 8 x 8 cases
CELL_PX = 8       # pixels par case
_PALETTE_KEYS = list(PALETTE.keys())


# --------------------------------------------------------------------------- scène

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.objects):
        for block in list(coll):
            coll.remove(block)


def _palette_image(model_name):
    size = GRID * CELL_PX
    img = bpy.data.images.new(f"{model_name}_palette", size, size, alpha=False)
    px = [0.0] * (size * size * 4)
    for idx, key in enumerate(_PALETTE_KEYS):
        r, g, b = (c / 255 for c in PALETTE[key])  # image 8 bits : valeurs sRGB directes
        cx, cy = idx % GRID, idx // GRID
        for y in range(cy * CELL_PX, (cy + 1) * CELL_PX):
            for x in range(cx * CELL_PX, (cx + 1) * CELL_PX):
                i = (y * size + x) * 4
                px[i:i + 4] = (r, g, b, 1.0)
    img.pixels = px
    tex_dir = os.path.join(EXPORTS, model_name)
    os.makedirs(tex_dir, exist_ok=True)
    img.filepath_raw = os.path.join(tex_dir, f"{model_name}_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def palette_material(model_name):
    img = _palette_image(model_name)
    mat = bpy.data.materials.new(f"{model_name}_Palette")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.85
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _uv_for(color):
    idx = _PALETTE_KEYS.index(color)
    cx, cy = idx % GRID, idx // GRID
    return ((cx + 0.5) / GRID, (cy + 0.5) / GRID)


# --------------------------------------------------------------------------- construction

class Model:
    """Regroupe les pièces d'un modèle et les exporte ensemble."""

    def __init__(self, name):
        self.name = name
        self.material = palette_material(name)
        self.parts = []
        self.collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(self.collection)

    def _finish(self, name, bm, color, jitter=0.0, seed=0):
        if jitter:
            rng = random.Random(f"{self.name}:{name}:{seed}")
            for v in bm.verts:
                v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter
        uv_layer = bm.loops.layers.uv.new("UVMap")
        uv = _uv_for(color)
        for face in bm.faces:
            face.smooth = False
            for loop in face.loops:
                loop[uv_layer].uv = uv
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(self.material)
        obj = bpy.data.objects.new(name, mesh)
        self.collection.objects.link(obj)
        self.parts.append(obj)
        return obj

    @staticmethod
    def _matrix(loc, rot, scale):
        sx, sy, sz = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
        rot = Euler(tuple(math.radians(a) for a in rot), "XYZ").to_matrix().to_4x4()
        return Matrix.Translation(Vector(loc)) @ rot @ Matrix.Diagonal((sx, sy, sz, 1.0))

    def ico(self, name, color, loc, scale=1.0, rot=(0, 0, 0), subdiv=1, jitter=0.0, seed=0):
        """Sphère low poly (icosphère). subdiv=1 -> 80 faces, subdiv=0 -> 20 faces."""
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0,
                                   matrix=self._matrix(loc, rot, scale))
        return self._finish(name, bm, color, jitter, seed)

    def box(self, name, color, loc, scale=1.0, rot=(0, 0, 0), bevel=0.0):
        """Boîte de taille 2*scale (comme le cube Blender). bevel adoucit les arêtes en 1 segment."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        if bevel:
            bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=bevel,
                            segments=1, affect="EDGES", profile=0.5)
        bmesh.ops.transform(bm, matrix=self._matrix(loc, rot, scale), verts=bm.verts)
        return self._finish(name, bm, color)

    def beam(self, name, color, p1, p2, half_w, half_d=None, bevel=0.0):
        """Boîte allongée entre deux points (bras, bâton...) : style « blocs »."""
        p1, p2 = Vector(p1), Vector(p2)
        d = p2 - p1
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        if bevel:
            bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=bevel / max(half_w, 1e-3),
                            segments=1, affect="EDGES", profile=0.5)
        hd = half_d if half_d is not None else half_w
        mat = (Matrix.Translation((p1 + p2) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
               @ Matrix.Diagonal((half_w, hd, d.length / 2, 1.0)))
        bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
        return self._finish(name, bm, color)

    def cone(self, name, color, loc, r1, r2, depth, rot=(0, 0, 0), sides=6, scale=1.0, jitter=0.0):
        """Cône / cylindre centré sur loc, axe Z. r2=0 -> pointe."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides,
                              radius1=r1, radius2=r2, depth=depth)
        bmesh.ops.transform(bm, matrix=self._matrix(loc, rot, scale), verts=bm.verts)
        return self._finish(name, bm, color, jitter)

    def tube(self, name, color, points, radii, sides=6, ring_scale=(1.0, 1.0), up=(0, 0, 1)):
        """Tube qui suit une suite de points (cornes, oreilles, bras, bâton...).

        radii : un rayon par point (0 au bout -> pointe).
        ring_scale : aplatit la section (ex. (1, 0.4) pour une oreille plate).
        up : direction de référence de l'aplatissement.
        """
        pts = [Vector(p) for p in points]
        n = len(pts)
        if isinstance(radii, (int, float)):
            radii = [radii] * n
        bm = bmesh.new()
        rings = []
        normal = None
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            if normal is None:
                ref = Vector(up)
                if abs(t.dot(ref)) > 0.95:
                    ref = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
                normal = t.cross(ref).normalized()
            else:  # transport parallèle : pas de vrille le long du tube
                normal = (normal - t * normal.dot(t)).normalized()
            binormal = t.cross(normal)
            r = radii[i]
            if r < 1e-4:
                rings.append([bm.verts.new(p)])
                continue
            ring = []
            for k in range(sides):
                a = 2 * math.pi * k / sides
                off = normal * math.cos(a) * ring_scale[0] + binormal * math.sin(a) * ring_scale[1]
                ring.append(bm.verts.new(p + off * r))
            rings.append(ring)
        for ra, rb in zip(rings, rings[1:]):
            if len(ra) == 1 and len(rb) == 1:
                continue
            if len(ra) == 1 or len(rb) == 1:
                tip, ring = (ra[0], rb) if len(ra) == 1 else (rb[0], ra)
                for k in range(sides):
                    bm.faces.new((ring[k], ring[(k + 1) % sides], tip))
                continue
            for k in range(sides):
                k2 = (k + 1) % sides
                bm.faces.new((ra[k], ra[k2], rb[k2], rb[k]))
        for ring in (rings[0], rings[-1]):
            if len(ring) > 2:
                bm.faces.new(ring)
        return self._finish(name, bm, color)

    def join(self, name, objs):
        """Fusionne plusieurs pièces en une seule (= un seul MeshPart dans Roblox)."""
        bm = bmesh.new()
        for o in objs:
            bm.from_mesh(o.data)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(self.material)
        for o in objs:
            self.parts.remove(o)
            old = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(old)
        obj = bpy.data.objects.new(name, mesh)
        self.collection.objects.link(obj)
        self.parts.append(obj)
        return obj

    def scale_about(self, objs, factor, pivot, offset=(0, 0, 0)):
        """Agrandit des pièces autour d'un point (pour ajuster les proportions)."""
        mat = (Matrix.Translation(Vector(pivot) + Vector(offset)) @ Matrix.Scale(factor, 4)
               @ Matrix.Translation(-Vector(pivot)))
        for o in objs:
            o.data.transform(mat)

    def mirror(self, obj, axis=0):
        """Duplique une pièce en miroir (axe X par défaut). _L <-> _R dans le nom."""
        name = obj.name.replace("_L", "_R") if "_L" in obj.name else obj.name + "_M"
        mesh = obj.data.copy()
        mesh.name = name
        scale = [1, 1, 1]
        scale[axis] = -1
        mesh.transform(Matrix.Diagonal((*scale, 1.0)))
        mesh.flip_normals()
        new = bpy.data.objects.new(name, mesh)
        self.collection.objects.link(new)
        self.parts.append(new)
        return new

    # ----------------------------------------------------------------------- sortie

    def stats(self):
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in self.parts)
        return {"pieces": len(self.parts), "triangles": tris}

    def export(self):
        """Exporte en FBX (texture intégrée) et GLB dans exports/<nom>/."""
        out = os.path.join(EXPORTS, self.name)
        os.makedirs(out, exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        objs = self.parts
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(out, f"{self.name}.fbx"),
            use_selection=True, object_types={"MESH"},
            apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
            mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True,
            axis_forward="-Z", axis_up="Y",
        )
        bpy.ops.export_scene.gltf(
            filepath=os.path.join(out, f"{self.name}.glb"),
            export_format="GLB", use_selection=True, export_apply=True,
        )
        return out


# --------------------------------------------------------------------------- aperçu

def render_previews(model, views=((35, "avant"), (215, "arriere")), size=900, samples=48, fond="prairie"):
    """Rend des images PNG du modèle (le sol n'est pas exporté).

    fond : "prairie" (îlot d'herbe, ciel bleu) ou "studio" (gris clair, lumière douce).
    """
    studio = fond == "studio"
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"

    world = bpy.data.worlds.new("Ciel")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1) if studio else (0.55, 0.75, 0.95, 1)
    bg.inputs["Strength"].default_value = 1.1 if studio else 0.9
    scene.world = world

    # sol (hors du modèle exporté)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=1)
    bmesh.ops.scale(bm, vec=(1, 1, 1), verts=bm.verts)
    ground_mesh = bpy.data.meshes.new("Sol")
    bm.to_mesh(ground_mesh)
    bm.free()
    gmat = bpy.data.materials.new("Sol")
    gmat.use_nodes = True
    r, g, b = (_srgb_to_linear(c / 255) for c in ((228, 228, 228) if studio else PALETTE["herbe_sol"]))
    gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (r, g, b, 1)
    gmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    ground_mesh.materials.append(gmat)
    ground = bpy.data.objects.new("Sol", ground_mesh)
    scene.collection.objects.link(ground)

    # cadrage automatique sur la boîte englobante du modèle
    pts = [o.matrix_world @ Vector(c) for o in model.parts for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    radius = (hi - lo).length / 2
    ground.scale = (radius * (6 if studio else 1.4),) * 3

    sun_data = bpy.data.lights.new("Soleil", "SUN")
    sun_data.energy = 2.2 if studio else 3.5
    sun_data.angle = math.radians(25 if studio else 8)
    sun = bpy.data.objects.new("Soleil", sun_data)
    sun.rotation_euler = Euler((math.radians(50), 0, math.radians(-35)))
    scene.collection.objects.link(sun)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 50
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    os.makedirs(PREVIEWS, exist_ok=True)
    paths = []
    dist = radius * 2.7
    for angle, label in views:
        a = math.radians(angle - 90)  # 0° = face (-Y)
        cam.location = center + Vector((math.cos(a) * dist, math.sin(a) * dist, radius * 0.9))
        direction = center - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(PREVIEWS, f"{model.name}_{label}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths
