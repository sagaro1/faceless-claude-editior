"""Blender 3D renderer for story storyboards (cartoon / fruit-style characters).

usage:
  blender -b -P story3d.py -- --dir <video/public/myshort> --out <frames_dir> [--scale 1.0] [--frames 0-120] [--stills 30,200]

Reads <dir>/storyboard.json + <dir>/timeline.json + <dir>/bg/*.jpg (same files as the 2D engine).
Character keys: x (frame fraction), s (size: 1 = normal, 2 = close-up), r (roll deg), face L/R, expr, pose, fx.
"""
import json, math, random, re, sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

DIR = Path(arg("--dir"))
OUT = Path(arg("--out"))
SCALE = float(arg("--scale", "1.0"))
FPS = 30

board = json.loads((DIR / "storyboard.json").read_text(encoding="utf-8"))
tl = json.loads((DIR / "timeline.json").read_text(encoding="utf-8"))
words, lines, mouth = tl["words"], tl["lines"], tl["mouth"]
END = lines[-1]["end"] + 0.35

# ---------------------------------------------------------------- time specs (same as Engine.tsx)
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())

def resolve(spec, base):
    if isinstance(spec, (int, float)):
        return base + spec
    m = re.match(r"^(.*?)([+-]\d*\.?\d+)?$", spec)
    head, off = m.group(1), float(m.group(2) or 0)
    if head.startswith("@"):
        return float(head[1:]) + off
    lm = re.match(r"^L(\d+)(e?)$", head)
    if lm:
        ln = lines[int(lm.group(1))]
        return (ln["end"] if lm.group(2) else ln["start"]) + off
    if head.startswith("w:"):
        target = norm(head[2:])
        for w in words:
            if norm(w["text"]) == target and w["start"] >= base - 0.05:
                return w["start"] + off
        raise ValueError(f"word {target} not found after {base:.2f}")
    raise ValueError(spec)

shots = []
for s in board["shots"]:
    t0 = resolve(s["start"], shots[-1]["t0"] if shots else 0)
    shots.append({**s, "t0": t0})
for i, s in enumerate(shots):
    s["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else END
    for c in s["chars"]:
        c["keys"] = sorted([{**k, "time": resolve(k["t"], s["t0"])} for k in c["track"]], key=lambda k: k["time"])

def ease(p):
    p = min(max(p, 0), 1)
    return 2 * p * p if p < 0.5 else 1 - (-2 * p + 2) ** 2 / 2

def track_num(keys, field, t, dflt):
    ks = [k for k in keys if field in k]
    if not ks:
        return dflt, 0
    if t <= ks[0]["time"]:
        return ks[0][field], 0
    for a, b in zip(ks, ks[1:]):
        if a["time"] <= t < b["time"]:
            p = ease((t - a["time"]) / max(1e-3, b["time"] - a["time"]))
            return a[field] + (b[field] - a[field]) * p, (b[field] > a[field]) - (b[field] < a[field])
    return ks[-1][field], 0

def track_step(keys, field, t, base):
    v, since = None, base
    for k in keys:
        if k["time"] <= t and field in k:
            v, since = k[field], k["time"]
    return v, since

def mouth_at(speaker, t):
    for c in mouth.get(speaker, []):
        if c["start"] <= t < c["end"]:
            return c["value"]
    return None

# ---------------------------------------------------------------- scene setup
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = int(arg("--samples", "8"))
scene.eevee.use_shadows = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 1, 4
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.resolution_percentage = int(100 * SCALE)
scene.render.fps = FPS
scene.render.use_lock_interface = True
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 92
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.frame_start, scene.frame_end = 0, int(math.ceil(END * FPS))

world = bpy.data.worlds.new("W") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.7, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

def link(o):
    scene.collection.objects.link(o)
    return o

def light(kind, energy, loc, rot, size=1.0, color=(1, 1, 1)):
    d = bpy.data.lights.new(kind, kind)
    d.energy, d.color = energy, color
    if kind == "SUN":
        d.angle = math.radians(12)
    else:
        d.size = size
    o = link(bpy.data.objects.new(kind, d))
    o.location, o.rotation_euler = loc, [math.radians(a) for a in rot]
    return o

light("SUN", 3.2, (0, 0, 10), (50, 0, -30), color=(1, 0.96, 0.9))
light("AREA", 400, (-4, -2, 3), (70, 0, -60), size=4, color=(0.85, 0.9, 1))
light("AREA", 600, (3, 6, 4), (-60, 0, 150), size=3, color=(1, 0.95, 0.85))   # rim

# ---------------------------------------------------------------- materials
def mat(name, color, rough=0.4, coat=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m

def hexc(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)

def fruit_mat(kind):
    """Fruit skin + purple rage that rises from the bottom (threshold node driven per frame)."""
    m = bpy.data.materials.new(f"skin_{kind}")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.32
    bsdf.inputs["Coat Weight"].default_value = 0.6
    coord = N.new("ShaderNodeTexCoord")
    if kind == "watermelon":
        wave = N.new("ShaderNodeTexWave")
        wave.wave_type, wave.bands_direction = "BANDS", "X"
        wave.inputs["Scale"].default_value = 2.2
        wave.inputs["Distortion"].default_value = 7
        wave.inputs["Detail"].default_value = 3
        L.new(coord.outputs["Object"], wave.inputs["Vector"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*hexc("#1f6b25"), 1)
        ramp.color_ramp.elements[1].color = (*hexc("#7fd15a"), 1)
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.45, 0.6
        L.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        skin = ramp.outputs["Color"]
    else:
        bsdf.inputs["Coat Weight"].default_value = 0.15
        bsdf.inputs["Roughness"].default_value = 0.55
        # diamond scales: rotated checker-ish grid via voronoi on a stretched, rotated space
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, math.radians(45), 0)
        L.new(coord.outputs["Object"], mp.inputs["Vector"])
        vor = N.new("ShaderNodeTexVoronoi")
        vor.feature = "F1"
        vor.distance = "MANHATTAN"
        vor.inputs["Scale"].default_value = 9
        vor.inputs["Randomness"].default_value = 0.15
        L.new(mp.outputs["Vector"], vor.inputs["Vector"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*hexc("#ffcf3f"), 1)
        ramp.color_ramp.elements[1].color = (*hexc("#c77d14"), 1)
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.32, 0.5
        L.new(vor.outputs["Distance"], ramp.inputs["Fac"])
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25
        bump.invert = True
        L.new(vor.outputs["Distance"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        skin = ramp.outputs["Color"]
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(coord.outputs["Object"], sep.inputs["Vector"])
    thr = N.new("ShaderNodeValue")
    thr.name = "rage"
    thr.outputs[0].default_value = -99
    mr = N.new("ShaderNodeMapRange")
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
    L.new(thr.outputs[0], sub.inputs[0]); sub.inputs[1].default_value = 0.06
    L.new(sub.outputs[0], mr.inputs["From Min"]); L.new(thr.outputs[0], mr.inputs["From Max"])
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1, 0
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(mr.outputs["Result"], mix.inputs["Factor"])
    L.new(skin, mix.inputs["A"])
    mix.inputs["B"].default_value = (*hexc("#7b2fa3"), 1)
    L.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m

M = {
    "white": mat("white", (0.95, 0.95, 0.95), 0.15, 0.8),
    "black": mat("black", (0.01, 0.01, 0.012), 0.1, 1.0),
    "ink": mat("ink", hexc("#2a2230"), 0.5),
    "mouth": mat("mouth", hexc("#5a1726"), 0.5),
    "tongue": mat("tongue", hexc("#ff6b81"), 0.4),
    "glove": mat("glove", (0.93, 0.93, 0.93), 0.35),
    "shoe_w": mat("shoe_w", hexc("#d62828"), 0.3, 0.5),
    "shoe_p": mat("shoe_p", hexc("#e64980"), 0.3, 0.5),
    "leaf": mat("leaf", hexc("#2f9e44"), 0.45),
    "leaf2": mat("leaf2", hexc("#51cf66"), 0.45),
    "gold": mat("gold", hexc("#ffd43b"), 0.2, 1.0),
    "steam": mat("steam", (0.95, 0.95, 0.97), 0.8, 0, 0.6),
    "sweat": mat("sweat", hexc("#7fd3ff"), 0.05, 1.0),
    "spark": mat("spark", hexc("#ffd23f"), 0.3, 0, 4.0),
    "stem": mat("stem", hexc("#3e7a1f"), 0.5),
}

def shadow_mat():
    m = bpy.data.materials.new("contact")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"])
    out = N["Material Output"]
    coord = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (-1, -1, 0)
    mp.inputs["Scale"].default_value = (2, 2, 1)
    g = N.new("ShaderNodeTexGradient"); g.gradient_type = "SPHERICAL"
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
    ramp.color_ramp.elements[1].position = 0.7
    tr = N.new("ShaderNodeBsdfTransparent")
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0, 0, 0, 1)
    mix = N.new("ShaderNodeMixShader")
    L.new(coord.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], g.inputs["Vector"])
    L.new(g.outputs["Fac"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return m

# ---------------------------------------------------------------- mesh helpers
def sphere(name, r, loc, material, scale=(1, 1, 1), parent=None, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.active_object
    o.name, o.scale = name, scale
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    if parent:
        o.parent = parent
    return o

def cone(name, r, depth, loc, rot, material, parent):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.005, depth=depth, location=loc, rotation=rot, vertices=24)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    o.parent = parent
    return o

def tube(name, n, radius, material, parent):
    """NURBS curve with bevel: rubber-hose limbs, brows, mouth line."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = radius, 6
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(n - 1)
    sp.use_endpoint_u, sp.order_u = True, min(3, n)
    o = link(bpy.data.objects.new(name, cu))
    o.data.materials.append(material)
    o.parent = parent
    return o

def set_tube(o, pts):
    for p, v in zip(o.data.splines[0].points, pts):
        p.co = (*v, 1)

def empty(name, parent=None):
    o = link(bpy.data.objects.new(name, None))
    o.parent = parent
    return o

# ---------------------------------------------------------------- characters
SPEAKER = {"watermelon": "WATERMELON", "pineapple": "PINEAPPLE"}
BODY = {"watermelon": dict(r=0.78, sc=(1.05, 1.0, 0.98), cz=1.32, shoe="shoe_w"),
        "pineapple": dict(r=0.62, sc=(1.0, 0.95, 1.28), cz=1.38, shoe="shoe_p")}

class Char:
    def __init__(self, kind):
        b = BODY[kind]
        self.kind, self.b = kind, b
        self.root = empty(f"{kind}_root")
        self.rig = empty(f"{kind}_rig", self.root)   # bob / crouch / lean
        self.skin = fruit_mat(kind)
        self.body = sphere(f"{kind}_body", b["r"], (0, 0, b["cz"]), self.skin, b["sc"], self.rig, seg=64)
        r, cz = b["r"], b["cz"]
        hz = r * b["sc"][2]
        self.top = cz + hz
        fy = lambda x, z: -math.sqrt(max(0.01, (r * b["sc"][1]) ** 2 * (1 - (x / (r * b["sc"][0])) ** 2 - ((z - cz) / hz) ** 2)))
        ez = cz + 0.18 * hz / r * 0.75
        self.eyes, self.pupils, self.brows = [], [], []
        for side in (-1, 1):
            ex = side * 0.24
            ey = fy(ex, ez) + 0.06
            e = sphere(f"{kind}_eye{side}", 0.15, (ex, ey, ez), M["white"], (1, 0.6, 1.1), self.rig)
            p = sphere(f"{kind}_pupil{side}", 0.075, (ex, ey - 0.085, ez), M["black"], (1, 0.5, 1.1), self.rig)
            br = tube(f"{kind}_brow{side}", 2, 0.028, M["ink"], self.rig)
            self.eyes.append(e); self.pupils.append(p); self.brows.append((br, ex, ey, ez))
        self.ez = ez
        mz = cz - 0.12 * hz / r * 1.3 - 0.05
        self.my = fy(0, mz) - 0.01
        self.mz = mz
        self.mouth_line = tube(f"{kind}_mline", 3, 0.025, M["ink"], self.rig)
        self.mouth_open = sphere(f"{kind}_mopen", 0.16, (0, self.my, mz), M["mouth"], (1, 0.35, 0.6), self.rig)
        self.tongue = sphere(f"{kind}_tongue", 0.09, (0, self.my - 0.02, mz - 0.04), M["tongue"], (1, 0.5, 0.45), self.rig)
        # limbs
        self.arms = [tube(f"{kind}_arm{s}", 3, 0.045, M["ink"], self.rig) for s in (-1, 1)]
        self.hands = [sphere(f"{kind}_hand{s}", 0.11, (0, 0, 0), M["glove"], parent=self.rig) for s in (-1, 1)]
        self.legs = [tube(f"{kind}_leg{s}", 3, 0.05, M["ink"], self.root) for s in (-1, 1)]
        self.feet = [sphere(f"{kind}_foot{s}", 0.13, (0, 0, 0), M[b["shoe"]], (1, 1.5, 0.6), self.root) for s in (-1, 1)]
        self.shadow = None
        # decorations
        if kind == "pineapple":
            for n, (ang, tilt, h) in enumerate([(0, 0, 0.6), (60, 25, 0.5), (120, 25, 0.48), (180, 25, 0.5), (240, 25, 0.48), (300, 25, 0.5),
                                               (30, 45, 0.4), (150, 45, 0.4), (270, 45, 0.4)]):
                a, tl_ = math.radians(ang), math.radians(tilt)
                cone(f"leaf{n}", 0.09, h, (math.sin(a) * 0.08, math.cos(a) * 0.08, self.top + h * 0.4),
                     (-math.cos(a) * tl_, math.sin(a) * tl_, 0), M["leaf" if n % 2 else "leaf2"], self.rig)
            bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.025, location=(0, 0, self.top - 0.02))
            tiara = bpy.context.active_object; tiara.data.materials.append(M["gold"]); tiara.parent = self.rig
            for side in (-1, 1):  # lashes
                lash = tube(f"lash{side}", 2, 0.015, M["ink"], self.rig)
                set_tube(lash, [(side * 0.33, fy(side * 0.3, ez) + 0.02, ez + 0.12), (side * 0.42, fy(side * 0.3, ez), ez + 0.2)])
        else:
            st = tube("stem", 3, 0.04, M["stem"], self.rig)
            set_tube(st, [(0, 0, self.top - 0.05), (0.03, 0, self.top + 0.12), (0.14, 0, self.top + 0.2)])
        # fx
        self.steam = [sphere(f"steam{n}", 0.13, (0, 0, 0), M["steam"], parent=self.rig, seg=16) for n in range(6)]
        self.sweat = sphere("sweat", 0.07, (0, 0, 0), M["sweat"], (0.8, 0.8, 1.3), self.rig, seg=16)
        self.sparks = []
        for n in range(4):
            bpy.ops.mesh.primitive_ico_sphere_add(radius=0.07, subdivisions=1)
            sp = bpy.context.active_object; sp.data.materials.append(M["spark"]); sp.parent = self.rig
            self.sparks.append(sp)
        self.alarm = [tube(f"alarm{n}", 2, 0.03, M["ink"], self.rig) for n in range(3)]
        self.all = [o for o in bpy.data.objects if o.name.startswith(kind) or self._is_child(o)]

    def _is_child(self, o):
        p = o.parent
        while p:
            if p == self.root:
                return True
            p = p.parent
        return False

    def objects(self):
        return [o for o in bpy.data.objects if self._is_child(o) or o == self.root]

    def show(self, vis):
        for o in self.objects():
            o.hide_render = not vis
        if self.shadow:
            self.shadow.hide_render = not vis

    # ------------------------------------------------------------ per-frame pose
    def pose(self, t, st, talk):
        b, r, cz = self.b, self.b["r"], self.b["cz"]
        expr, pose, fx = st["expr"], st["pose"], st["fx"]
        walking = st["walking"]
        crouch = 0.35 if pose == "crouch" else 0
        bob = -crouch + (abs(math.sin(t * 11)) * 0.07 if walking else math.sin(t * 3 + len(self.kind)) * 0.025)
        self.rig.location = (0, 0, bob)
        self.rig.rotation_euler = (0, math.radians(6 if walking else 0) * (1 if st["dir"] >= 0 else -1), 0)
        # --- eyes / brows by expression
        lid = {"smug": 0.5, "laugh": 0.12, "shocked": 1.3, "angry": 0.75, "happy": 0.35, "determined": 0.8, "worried": 1.05, "crazy": 1.2}.get(expr, 1.0)
        blink = (int(t * FPS) % 100) < 3
        for n, (e, p) in enumerate(zip(self.eyes, self.pupils)):
            l = 0.08 if blink else lid * (0.65 if expr == "crazy" and n == 1 else 1)
            e.scale = (1, 0.6, 1.1 * l)
            p.scale = (1 if expr != "shocked" else 0.7, 0.5, 1.1 * min(l, 1.0) * (0.7 if expr == "shocked" else 1))
            p.hide_render = e.hide_render or l < 0.2
        brow = {"angry": (-0.08, 25), "determined": (-0.04, 15), "worried": (0.06, -20), "shocked": (0.12, 0), "smug": (0.02, -8),
                "laugh": (0.07, 0), "happy": (0.05, 0), "crazy": (0.1, 10)}.get(expr, (0.02, 0))
        for side, (o, ex, ey, ez) in zip((-1, 1), self.brows):
            lift, ang = brow
            if expr == "smug" and side == 1:
                lift += 0.06
            a = math.radians(ang) * side
            z = ez + 0.25 + lift
            dx, dz = 0.11 * math.cos(a), 0.11 * math.sin(a)
            set_tube(o, [(ex - dx, ey - 0.03, z + dz), (ex + dx, ey - 0.03, z - dz)])
        # --- mouth
        openness = {"A": 0, "X": 0, "B": 0.25, "C": 0.55, "D": 1.0, "E": 0.6, "F": 0.35, "G": 0.2, "H": 0.5}.get(talk, 0) if talk else 0
        base_open = {"shocked": 0.6, "laugh": 0.85, "crazy": 0.6}.get(expr, 0)
        op = max(openness, base_open)
        width = 0.55 if talk in ("E", "F") else 1.0
        if op > 0.05:
            self.mouth_line.hide_render = True
            self.mouth_open.hide_render = self.tongue.hide_render = False
            self.mouth_open.scale = (width * (1.15 if expr in ("laugh", "crazy") else 1), 0.35, 0.18 + 0.6 * op)
            self.tongue.scale = (width, 0.5, 0.2 + 0.35 * op)
        else:
            self.mouth_open.hide_render = self.tongue.hide_render = True
            self.mouth_line.hide_render = False
            smile = {"smug": 0.6, "happy": 1.0, "laugh": 1.0, "worried": -0.6, "angry": -0.7, "determined": -0.1}.get(expr, 0.2)
            w = 0.2
            set_tube(self.mouth_line, [(-w, self.my + 0.02, self.mz + (0.04 if expr == "smug" else 0)),
                                       (0, self.my - 0.02, self.mz - 0.09 * smile),
                                       (w, self.my + 0.02, self.mz + 0.06 * max(smile, 0))])
        # --- arms (shoulder -> elbow -> hand), body-local coords, -y is toward camera
        sh = [(-r * b["sc"][0] * 0.95, -0.05, cz - 0.05), (r * b["sc"][0] * 0.95, -0.05, cz - 0.05)]
        sw = math.sin(t * 11) * 0.25 if walking else math.sin(t * 2.5) * 0.04
        hands = [(-1.05, -0.1 + sw, 0.85), (1.05, -0.1 - sw, 0.85)]
        pt = st["poseT"]
        shake = math.sin(t * 24) * 0.08
        if pose in ("reach", "give"):
            hands[1] = (1.3, -0.7, cz - 0.1)
        elif pose == "point":
            hands[1] = (1.25, -0.5, cz + 0.75)
        elif pose == "slam":
            k = min(1, pt / 0.16); hands[1] = (1.1, -0.6, cz + 0.8 - 1.1 * k)
        elif pose in ("handsUp", "shout"):
            hands = [(-1.15, -0.2, cz + 0.95 + shake), (1.15, -0.2, cz + 0.95 - shake)]
        elif pose == "wave":
            hands[1] = (1.2 + math.sin(pt * 14) * 0.15, -0.2, cz + 0.85)
        elif pose == "fist":
            hands = [(-0.75, -0.75, cz + 0.05 + shake), (0.75, -0.75, cz + 0.05 - shake)]
        elif pose == "hip":
            hands[0] = (-r * b["sc"][0] - 0.05, -0.05, cz - 0.45)
        for s, (arm, hand, s0, h) in enumerate(zip(self.arms, self.hands, sh, hands)):
            side = -1 if s == 0 else 1
            out = 0.35 if pose == "hip" and s == 0 else 0.18
            elbow = ((s0[0] + h[0]) / 2 + side * out, (s0[1] + h[1]) / 2, (s0[2] + h[2]) / 2 - 0.12)
            set_tube(arm, [s0, elbow, h])
            hand.location = h
        # --- legs (root-local: not affected by bob except hips)
        hip_z = cz - r * b["sc"][2] * 0.85 + bob
        for s, (leg, foot) in enumerate(zip(self.legs, self.feet)):
            side = -1 if s == 0 else 1
            phase = math.sin(t * 11 + (0 if s == 0 else math.pi)) if walking else 0
            lift = max(0, math.cos(t * 11 + (0 if s == 0 else math.pi))) * 0.15 if walking else 0
            fpos = (side * 0.3, -0.05 + phase * 0.3, 0.08 + lift)
            knee = (side * (0.42 if crouch else 0.32), -0.15 - crouch * 0.6, (hip_z + fpos[2]) / 2)
            set_tube(leg, [(side * 0.25, 0, hip_z + 0.05), knee, fpos])
            foot.location = (fpos[0], fpos[1] - 0.06, fpos[2])
        # --- fx
        fxT = st["fxT"]
        rage = min(1, fxT / 0.9) if fx == "purple" else (1 if fx == "steam" else 0)
        bottom, top = cz - r * b["sc"][2], cz + r * b["sc"][2]
        self.skin.node_tree.nodes["rage"].outputs[0].default_value = (bottom - 0.1 + (top - bottom + 0.3) * rage) if rage > 0 else -99
        for n, o in enumerate(self.steam):
            on = fx == "steam"
            o.hide_render = not on
            if on:
                side = -1 if n < 3 else 1
                k = n % 3
                rise = (t * 0.6 + k * 0.33) % 1
                o.location = (side * (0.55 + 0.12 * k), -0.1, self.top + 0.05 + rise * 0.5)
                s_ = (0.7 + 0.5 * abs(math.sin(t * 7 + n))) * (1 - rise * 0.5)
                o.scale = (s_, s_, s_)
        self.sweat.hide_render = fx != "sweat"
        if fx == "sweat":
            d = (t * 0.8) % 1
            self.sweat.location = (r * 0.75, -r * 0.55, self.ez + 0.25 - d * 0.5)
        for n, o in enumerate(self.sparks):
            on = fx == "sparkle"
            o.hide_render = not on
            if on:
                a = n * math.pi / 2 + 0.6
                o.location = (math.cos(a) * (r + 0.35), -0.3, cz + math.sin(a) * (r * b["sc"][2] + 0.3))
                s_ = 0.4 + 0.9 * abs(math.sin(t * 6 + n * 1.7))
                o.scale = (s_, s_, s_)
        for n, o in enumerate(self.alarm):
            on = fx == "alarm"
            o.hide_render = not on
            if on:
                pop = min(1, fxT / 0.15)
                a = math.radians(-40 + 40 * n)
                x0, z0 = math.sin(a) * 0.35, self.top + 0.15
                set_tube(o, [(x0, -0.2, z0), (x0 + math.sin(a) * 0.3 * pop, -0.2, z0 + math.cos(a) * 0.3 * pop)])

chars = {k: Char(k) for k in ("watermelon", "pineapple")}
smat = shadow_mat()
for c in chars.values():
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.01))
    sh = bpy.context.active_object
    sh.data.materials.append(smat)
    sh.scale = (1.9, 1.2, 1)
    sh.parent = c.root
    c.shadow = sh

# ---------------------------------------------------------------- camera + backdrops
cam_data = bpy.data.cameras.new("cam")
cam_data.lens, cam_data.sensor_fit, cam_data.sensor_height = 28, "VERTICAL", 36
cam = link(bpy.data.objects.new("cam", cam_data))
scene.camera = cam
CAM_Z, BACK_Y, TILT = 0.7, 13.0, 10.0   # low camera, tilted up -> feet land low in frame, like the reference
VFOV = 2 * math.atan(18 / 28)
HALF_W = math.tan(VFOV / 2) * 1080 / 1920  # half-width per metre of depth

backdrops = {}
for bg in sorted({s["bg"] for s in shots}):
    img = bpy.data.images.load(str((DIR / "bg" / f"{bg}.jpg").resolve()))
    m = bpy.data.materials.new(f"bg_{bg}")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"])
    tex = N.new("ShaderNodeTexImage"); tex.image = img
    em = N.new("ShaderNodeEmission")
    L.new(tex.outputs["Color"], em.inputs["Color"]); L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    size = 2 * BACK_Y * math.tan(VFOV / 2) * 1.65
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, BACK_Y, CAM_Z + math.tan(math.radians(TILT)) * BACK_Y),
                                     rotation=(math.pi / 2 - math.radians(TILT), 0, 0))
    p = bpy.context.active_object
    p.name = f"bg_{bg}"
    p.data.materials.append(m)
    p.visible_shadow = False
    backdrops[bg] = p

# ---------------------------------------------------------------- per-frame update
DEPTH = 4.5

def shot_at(t):
    for s in shots:
        if s["t0"] <= t < s["t1"]:
            return s
    return shots[-1]

def update(scn, *_):
    t = scn.frame_current / FPS
    s = shot_at(t)
    p = ease((t - s["t0"]) / max(1e-3, s["t1"] - s["t0"]))
    cam_spec = s.get("cam") if isinstance(s.get("cam"), dict) else {}
    lerp = lambda key, d: (cam_spec[key][0] + (cam_spec[key][1] - cam_spec[key][0]) * p) if key in cam_spec else d
    zoom, pan, rot = lerp("zoom", 1), lerp("pan", 0), lerp("rot", 0)
    shake = cam_spec.get("shake", 0) * max(0.25, 1 - (t - s["t0"]) / 0.6)
    random.seed(int(t * FPS))
    jx, jz = (random.random() - 0.5) * 0.06 * shake, (random.random() - 0.5) * 0.06 * shake
    cam.location = (-pan / 1080 * DEPTH * 2 * HALF_W + jx, -(zoom - 1) * -3.2, CAM_Z + jz)
    cam.rotation_euler = (math.radians(90 + TILT), math.radians(rot), 0)
    for bg, o in backdrops.items():
        o.hide_render = bg != s["bg"]
    active = {c["id"]: c for c in s["chars"]}
    for cid, ch in chars.items():
        spec = active.get(cid)
        if not spec:
            ch.show(False)
            continue
        keys = spec["keys"]
        x, xm = track_num(keys, "x", t, 0.5)
        size, _ = track_num(keys, "s", t, 1)
        roll, _ = track_num(keys, "r", t, 0)
        vis, _ = track_num(keys, "vis", t, 1)
        expr, _ = track_step(keys, "expr", t, s["t0"])
        pose, pose_since = track_step(keys, "pose", t, s["t0"])
        fx, fx_since = track_step(keys, "fx", t, s["t0"])
        face, _ = track_step(keys, "face", t, s["t0"])
        st = dict(expr=expr or "neutral", pose=pose or "idle", poseT=t - pose_since, fx=fx, fxT=t - fx_since,
                  walking=xm != 0, dir=xm)
        ch.show(vis > 0.05)
        d = DEPTH / size
        ch.root.location = ((x - 0.5) * 2 * HALF_W * d, d, 0)
        turn = 0.0
        if xm:
            turn = 55 * xm          # face the walking direction
        elif face == "L":
            turn = -22
        elif face == "R":
            turn = 22
        ch.root.rotation_euler = (0, math.radians(roll), math.radians(turn))
        ch.pose(t, st, mouth_at(SPEAKER[cid], t))

bpy.app.handlers.frame_change_pre.clear()
bpy.app.handlers.frame_change_pre.append(update)

# ---------------------------------------------------------------- render
OUT.mkdir(parents=True, exist_ok=True)
stills = arg("--stills")
if stills:
    for sec in [float(v) for v in stills.split(",")]:
        f = int(sec * FPS)
        scene.frame_set(f)
        scene.render.filepath = str(OUT / f"still_{f:04d}.jpg")
        bpy.ops.render.render(write_still=True)
    print("stills done")
else:
    rng = arg("--frames")
    if rng:
        a, b_ = rng.split("-")
        scene.frame_start, scene.frame_end = int(a), int(b_)
    scene.render.filepath = str(OUT / "f_")
    bpy.ops.render.render(animation=True)
    print("animation done")
