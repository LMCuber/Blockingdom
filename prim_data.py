import pygame
import itertools
from settings import *
from pyengine.basics import *


black_filter = pygame.Surface((30, 30)); black_filter.set_alpha(200)
avatar_map = dict.fromkeys(((2, 3), (2, 4), (7, 3), (7, 4)), WHITE) | dict.fromkeys(((3, 3), (3, 4), (6, 3), (6, 4)), BLACK)
BLUE = POWDER_BLUE
orb_colors = {"red": RED, "green": GREEN, "blue": BLUE, "yellow": YELLOW, "orange": ORANGE, "purple": PURPLE, "pink": PINK}
rotations2 = {0: 90, 90: 0}
rotations4 = {90: 0, 0: 270, 270: 180, 180: 90}


# C L A S S E S ---------------------------------------------------------------------------------------- #
class Entity:
    # init
    entity_imgs = {}
    # active
    entity_imgs["portal"] = cimgload("Images", "Spritesheets", "portal.png", frames=7)
    entity_imgs["camel"] = img_mult(cimgload("Images", "Mobs", "camel.png"), randf(0.8, 1.2))
    entity_imgs["fluff_camel"] = cimgload("Images", "Mobs", "fluff_camel.png", frames=4)
    entity_imgs["penguin"] = cimgload("Images", "Mobs", "penguin.png", frames=4)
    entity_imgs["penguin_sliding"] = cimgload("Images", "Mobs", "penguin.png", frames=4, rotation=-90)
    #entity_imgs["penguin"] = cimgload("Images", "Mobs", "penguin.png", frames=TODO)

    def __init__(self, img_data, pos, screen, layer, anchor="bottomleft", traits=None, smart_vector=False, **kwargs):
        self.anim = 0
        self.init_images(img_data, "images")
        self.smart_vector = smart_vector
        self.traits = traits if traits is not None else []
        self.species = self.traits[0]
        if not smart_vector:
            self._rect = self.image.get_rect(topleft=(x, y))
            setattr(self.rect, anchor, pos)
        else:
            self.x, self.y = pos
            self.dx = 0
        self.screen = screen
        self.layer = layer
        self.sizes = [image.get_size() for image in self.images]
        self.xvel = 0
        self.yvel = 0
        for k, v in kwargs.items():
            setattr(self, k, v)
        if "camel" in self.traits:
            self.init_images("camel", "h_images")
            self.xvel = 0.2
        if "penguin" in self.traits:
            self.init_images("penguin", "h_images")
            self.init_images("penguin", "images")
            self.init_images("penguin_sliding", "h_sliding_images")
            self.init_images("penguin_sliding", "sliding_images")
            self.penguin_spinning = False
            self.xvel = 0.2
            self.penguin_sliding = False
        self.taking_damage = False
        self.last_took_damage = ticks()
        self.health = 100
        self.dying = False

    @property
    def mask(self):
        return pygame.mask.from_surface(self.image)

    def init_images(self, img_data, name):
        if isinstance(img_data, list):
            iter_ = img_data
        elif isinstance(img_data, pygame.Surface):
            iter_ = [img_data]
        elif isinstance(img_data, str):
            if img_data in Entity.entity_imgs:
                imgs = Entity.entity_imgs[img_data]
                if isinstance(imgs, list):
                    iter_ = imgs
                elif isinstance(imgs, pygame.Surface):
                    iter_ = [imgs]
            else:
                iter_ = [SmartSurface.from_string(img_data)]
        setattr(self, name, [SmartSurface.from_surface(flip(img, "h_" in name, "v_" in name)) for img in iter_])
        self.image = self.images[int(self.anim)]

    def update(self):
        if not self.dying:
            getattr(self, f"{self.species}_animate", self.animate)()
            getattr(self, f"{self.species}_function", lambda: None)()
            self.regenerate()
        self.draw()

    @property
    def xbound(self):
        return 1 if self.xvel >= 0 else -1

    @property
    def ybound(self):
        return 1 if self.yvel >= 0 else -1

    @property
    def rect(self):
        if not self.smart_vector:
            return self._rect
        else:
            return self.image.get_rect(topleft=(self.x, self.y))

    @property
    def right(self):
        return self.x + self.image.get_width()

    @right.setter
    def right(self, value):
        self.x = value - self.image.get_width()

    @property
    def centerx(self):
        return self.x + self.image.get_width() / 2

    @centerx.setter
    def centerx(self, value):
        self.x = value - self.image.get_width() / 2

    @property
    def centery(self):
        return self.y + self.image.get_height() / 2

    @centery.setter
    def centery(self, value):
        self.y = value - self.image.get_height() / 2

    @property
    def center(self):
        return (self.centerx, self.centery)

    @center.setter
    def center(self, value):
        self.centerx = value[0]
        self.centery = value[1]

    @property
    def bottom(self):
        return self.y + self.image.get_height()

    @bottom.setter
    def bottom(self, value):
        self.y = value - self.image.get_height()

    @property
    def width(self):
        return self.image.get_width()

    @property
    def height(self):
        return self.image.get_height()

    def movex(self, amount):
        if not self.dying:
            self.x += amount
            self.dx += amount
            if self.dx >= 30:
                self.dx = 0
                self.index += 1

    def draw(self):
        image = self.image.copy()
        if self.taking_damage:
            #image.fill((255, 0, 0, 125), special_flags=BLEND_RGB_ADD)
            image = color_filter(image)
        if not self.smart_vector:
            Window.display.blit(image, self.rect)
        else:
            Window.display.blit(image, (self.x, self.y))

    def animate(self):
        self.anim += g.p.anim_fps
        try:
            self.images[int(self.anim)]
        except IndexError:
            self.anim = 0
        finally:
            self.image = (self.images if self.xvel >= 0 else self.h_images)[int(self.anim)]

    def penguin_animate(self):
        self.anim += g.p.anim_fps if self.penguin_spinning else 0
        try:
            self.images[int(self.anim)]
        except IndexError:
            self.anim = 0
            self.penguin_spinning = False
        finally:
            if self.penguin_sliding:
                self.image = (self.sliding_images if self.xvel >= 0 else self.h_sliding_images)[int(self.anim)]
            else:
                self.image = (self.images if self.xvel >= 0 else self.h_images)[int(self.anim)]
        if not self.penguin_spinning and not self.penguin_sliding and chance(1 / 500):
            self.penguin_spinning = True
        elif not self.penguin_sliding and not self.penguin_spinning and chance(1 / 1000):
            self.penguin_sliding = True
        elif self.penguin_sliding and chance(1 / 500):
            self.penguin_sliding = False

    def regenerate(self):
        if self.taking_damage and ticks() - self.last_took_damage >= 300:
            self.taking_damage = False

    def die(self):
        self.dying = True
        def t():
            og_img = self.image.copy()
            for i in range(90):
                self.image = SmartSurface.from_surface(pygame.transform.rotozoom(og_img, -i, 1))
                time.sleep(0.0005)
            time.sleep(0.7)
            if self in g.w.entities:
                g.w.entities.remove(self)
        Thread(target=t).start()


# F U N C T I O N S ------------------------------------------------------------------------------------ #
def color_base(block_type, colors, unplacable=False, sep="-"):
    base_block = a.blocks[f"base-{block_type}"]
    w, h = base_block.get_size()
    for name, color in colors.items():
        colored_block = pygame.Surface((30, 30), pygame.SRCALPHA)
        for y in range(h):
            for x in range(w):
                c = base_block.get_at((x, y))
                if c != (0, 0, 0, 0):
                    rgb = c[:3]
                    if rgb != BLACK:
                        colored_block.set_at((x, y), rgb_mult(color, rgb[0] / 255))
                    else:
                        colored_block.set_at((x, y), BLACK)
        block_name = f"{name}{sep}{block_type}"
        a.blocks[block_name] = colored_block
        if unplacable:
            unplacable_blocks.append(block_name)


def rotate_base(block_type, states=4):
    base_block = a.blocks[f"base-{block_type}"]
    w, h = base_block.get_size()
    if states == 4:
        rotations = [0, 90, 180, 270]
    elif states == 2:
        rotations = [0, 90]
    for r in rotations:
        a.blocks[f"{block_type}_deg{r}"] = rotate(base_block, r)
    a.aliases["blocks"][f"{block_type}_deg0"] = block_type


def get_avatar():
    """
    svg_path = path("tempfiles", "avatar.svg")
    png_path = path("tempfiles", "avatar.jpg")
    with open(svg_path, "wb") as f:
        f.write(requests.get(avatar_url.replace(":mood", mood).replace(":seed", str(random.random()))).content)
    svg = svg2rlg(svg_path)
    renderPM.drawToFile(svg, png_path, fmt="JPG")
    pg_img = cimgload(png_path)
    pg_img = pgscale(pg_img, (30, 30))
    os.remove(svg_path)
    os.remove(png_path)
    """
    """
    png_path = path("tempfiles", "avatar.png")
    with open(png_path, "wb") as f:
        f.write(requests.get(avatar_url.replace(":seed", str(random.random()))).content)
    pil_img = PIL.Image.open(png_path).resize((10, 10), resample=PIL.Image.BILINEAR).resize((30, 30), PIL.Image.NEAREST)
    pg_img = pil_to_pg(pil_img)
    os.remove(png_path)
    """
    img = pygame.Surface((10, 10))
    skin_color = rgb_mult(SKIN_COLOR, randf(0.4, 8))
    hair_color = rand_rgb()
    hair_chance = 1
    img.fill(skin_color)
    for y in range(img.get_height()):
        for x in range(img.get_width()):
            if (x, y) in avatar_map:
                img.set_at((x, y), avatar_map[(x, y)])
            else:
                truthy = False
                try:
                    if chance(1 / hair_chance) and img.get_at((x, y - 1)) == hair_color:
                        truthy = True
                except IndexError:
                    truthy = True
                if truthy:
                    img.set_at((x, y), hair_color)
        hair_chance += 0.1
    img = pgscale(img, (30, 30))
    return img


def get_robot():
    half = pygame.Surface((5, 10))
    color = [rand(0, 255) for _ in range(3)]
    for y in range(half.get_height()):
        for x in range(half.get_width()):
            if chance(1 / 2.7):
                half.set_at((x, y), color)
    ret = pygame.Surface((half.get_width() * 2, half.get_height()))
    ret.blit(half, (0, 0))
    ret.blit(pygame.transform.flip(half, True, False), (ret.get_width() / 2, 0))
    ret = pygame.transform.scale(ret, (30, 30))
    return ret


def get_name():
    ret = ""
    for _ in range(rand(4, 8)):
        if not ret:
            pass


def norm_ore(ore):
    return ore.removesuffix("en")


def cfilter(image, alpha, size, color=BLACK, colorkey=BLACK):
    surf = pygame.Surface((size[0], size[1]))
    surf.fill(color)
    surf.set_alpha(alpha)
    final_surf = image.copy()
    final_surf.blit(surf, (0, 0))
    final_surf.set_colorkey(colorkey)
    return final_surf


def tpure(tool):
    ret = tool.removeprefix("enchanted_")
    return (ret.split("_")[1] if ret is not None else ret) if "_" in ret else ret


def tore(tool):
    return tool.removeprefix("enchanted_").split("_")[0]


# I M A G E S ------------------------------------------------------------------------------------------ #
# constants
STONE_GRAY = (65, 65, 65)
WOOD_BROWN = (87, 44, 0)
DARK_WOOD_BROWN = (80, 40, 0)


class _Assets:
    def __init__(self):
        self.assets = {"blocks": {}, "tools": {}, "icons": {}}
        self.aliases = {"blocks": {}, "tools": {}, "icons": {}}
        self.sizes = {}

    @property
    def blocks(self):
        return self.assets["blocks"]

    @property
    def tools(self):
        return self.assets["tools"]

    @property
    def icons(self):
        return self.assets["icons"]


a = _Assets()


# images
def load_blocks():
    _bsprs = cimgload("Images", "Spritesheets", "blocks.png")
    block_list = [
        ["air",        "bucket",           "apple",     "bamboo",        "cactus",        "watermelon",       "rock"      ],
        ["chest",      "snow",             "coconut",   "coconut-piece", "command-block", "wood",             "bush"      ],
        ["base-pipe",  "dirt",             "dynamite",  "fire",          "magic-brick",   "watermelon-piece", "grass1"    ],
        ["hay",        "base-curved-pipe", "leaf",      "grave",         "sand",          "workbench",        "grass2"    ],
        ["snow-stone", "soil",             "stone",     "vine",          "wooden-planks", "a_wooden-planks",  "stick"     ],
        ["anvil",      "furnace",          "p_soil",    "blue_barrel",   "red_barrel",    "gun-crafter",      "base-ore"  ],
        ["blackstone", "closed-core",      "base-core", "lava",          "base-orb",      "magic-table",      "base-armor"]
    ]
    for y, layer in enumerate(block_list):
        for x, block in enumerate(layer):
            a.blocks[block] = _bsprs.subsurface(x * 30, y * 30, 30, 30)
    # special one-line blocks
    a.blocks["f_soil"] = a.blocks["soil"].copy()
    a.blocks["sw_soil"] = cfilter(a.blocks["soil"].copy(), 150, (30, 12))
    a.blocks["sv_soil"] = cfilter(a.blocks["soil"].copy(), 150, (30, 12), (68, 95, 35))
    a.blocks["sv_wood"] = img_mult(a.blocks["wood"].copy(), 1.2)
    a.blocks["f_leaf"] = a.blocks["leaf"].copy()
    a.blocks["sw_leaf"] = cfilter(a.blocks["leaf"].copy(), 150, (30, 30))
    a.blocks["sk_leaf"] = cfilter(a.blocks["leaf"].copy(), 150, (30, 30), PINK)
    a.blocks["water"] = pygame.Surface((30, 30), pygame.SRCALPHA); a.blocks["water"].fill((17, 130, 177)); a.blocks["water"].set_alpha(180)
    a.blocks["glass"] = pygame.Surface((30, 30), pygame.SRCALPHA); a.blocks["glass"].fill(WHITE, (0, 0, 30, 2)); a.blocks["glass"].fill(WHITE, (28, 0, 2, 30)); a.blocks["glass"].fill(WHITE, (0, 28, 30, 2)); a.blocks["glass"].fill(WHITE, (0, 0, 2, 30))
    # spike plant
    a.blocks["spike-plant"] = pygame.Surface((30, 30), pygame.SRCALPHA)
    for i in range(3):
        _x = nordis(15, 3)
        _y = 30
        while _y != 0:
            _x += choice((-3, 0, 3))
            if _x < 0:
                _x = 0
            elif _x > 27:
                _x = 27
            _y -= 3
            pygame.draw.rect(a.blocks["spike-plant"], rgb_mult(GREEN, randf(0.6, 1.4)), (_x, _y, 3, 3))
    pygame.draw.rect(a.blocks["spike-plant"], rgb_mult(YELLOW, randf(0.6, 1.4)), (_x, _y, 3, 3))
    # portal generator
    a.blocks["portal-generator"] = pygame.Surface((30, 30), pygame.SRCALPHA)
    for y in range(10):
        for x in range(10):
            surf = a.blocks["portal-generator"]
            color = [rand(0, 255) for _ in range(3)]
            rect = (x * 3, y * 3, 3, 3)
            pygame.draw.rect(surf, color, rect)
    # ores
    for name, color in [(oi, oinfo[oi]["color"]) for oi in oinfo]:
        a.blocks[name] = swap_palette(a.blocks["base-ore"], BLACK, color)
        a.blocks[f"{name}-ingot"] = pygame.Surface((30, 30), pygame.SRCALPHA)
        ingot_keys = ("blocks", f"{name}-ingot")
        ingot_img = ndget(a.assets, ingot_keys)
        pygame.draw.polygon(ingot_img, color, ((0, 11), (22, 3), (30, 11), (8, 19)))
        pygame.draw.polygon(ingot_img, rgb_mult(color, 0.9), ((0, 11), (8, 19), (8, 27), (0, 19)))
        pygame.draw.polygon(ingot_img, rgb_mult(color, 0.8), ((8, 19), (30, 11), (30, 19), (8, 27)))
        a.assets[ingot_keys[0]][ingot_keys[1]] = pil_to_pg(pil_pixelate(pg_to_pil(ndget(a.assets, ingot_keys)), (10, 10)))
        unplacable_blocks.append(ingot_keys[-1])
    # deleting unneceserry blocks that have been modified anyway
    del a.blocks["soil"]
    del a.blocks["leaf"]


def load_tools():
    _tsprs = cimgload("Images", "Spritesheets", "tools.png")
    tool_list = [
        ["pickaxe", "axe",    "sickle"],
        ["shovel",  "rake",   "scissors"],
        ["kunai",   "hammer", "sword"]
    ]
    tools = {}
    whole_tools = {"stick"}
    for y, layer in enumerate(tool_list):
        for x, tool in enumerate(layer):
            tl = _tsprs.subsurface(x * 30, y * 30, 30, 30)
            for name, color in tool_rarity_colors.items():
                a.tools[f"{name}_{tool}"] = swap_palette(tl, STONE_GRAY if tool not in whole_tools else WOOD_BROWN, color)
    a.og_tools = {k: v.copy() for k, v in a.tools.items()}


def load_guns():
    for gun_part in g.tup_gun_parts:
        for gun_filename in os.listdir(path("Images", "Guns", gun_part)):
            gun_name = splitext(gun_filename)[0]
            a.blocks[f"{gun_name}_{gun_part}"] = cimgload("Images", "Guns", gun_part, gun_filename)
            gun_blocks.append(f"{gun_name}_{gun_part}")
    a.og_blocks = {k: v.copy() for k, v in a.blocks.items()}


def load_icons():
    icon_sprs = cimgload("Images", "Spritesheets", "icons.png")
    icon_list = [
        ["lives", "hunger", "thirst", "energy", "o2", "xp"]
    ]
    for y, layer in enumerate(icon_list):
        for x, tool in enumerate(layer):
            a.icons[tool] = icon_sprs.subsurface(x * 15, y * 15, 15, 15)
    a.icons["armor"] = a.blocks["base-armor"].subsurface((0, 15, 30, 15))
    a.og_icons = {k: v.copy() for k, v in a.icons.items()}


def load_sizes():
    for atype, dict_ in a.assets.items():
        for name, img in dict_.items():
            a.sizes[name] = img.get_size()


tool_tiringnesses = {"sickle": 1}
tool_rarity_colors = {"wood": DARK_WOOD_BROWN, "stone": STONE_GRAY, "iron": LIGHT_GRAY, "gold": GOLD_YELLOW, "emerald": LIGHT_GREEN}
tool_rarity_mults = {}
mult = 1
for r in tool_rarity_colors:
    tool_rarity_mults[r] = mult
    mult *= 1.18

# B L O C K  D A T A ----------------------------------------------------------------------------------- #
# ore info
oinfo = {
    "talc":      {"moh": 1,  "color": MINT},
    "gypsum":    {"moh": 2,  "color": LIGHT_GRAY},
    "gold":      {"moh": 3,  "color": GOLD_YELLOW},     "coal": {"moh": 3, "color": BLACK},
    "iron":      {"moh": 4,  "color": LIGHT_GRAY},
    "palladium": {"moh": 5,  "color": (190, 173, 210)}, "obisidian": {"moh": 5, "color": (20, 20, 20)},
    "titanium":  {"moh": 6,  "color": (210, 210, 210)}, "uranium":   {"moh": 6, "color": MOSS_GREEN},
    "quartz":    {"moh": 7,  "color": LIGHT_PINK},
    "topaz":     {"moh": 8,  "color": (30, 144, 255)},  "emerald":   {"moh": 8, "color": LIGHT_GREEN},
    "corundum":  {"moh": 9,  "color": (176, 223, 230)},
    "diamond":   {"moh": 10, "color": POWDER_BLUE}
}
ore_blocks = list(oinfo.keys())
ore_colors = {ore: data["color"] for ore, data in oinfo.items()}

block_breaking_times = {"stone": 1000, "sand": 200, "hay": 150, "soil": 200, "dirt": 200, "watermelon": 500}
block_breaking_amounts = {"stone": 0.01, "sand": 0.01, "hay": 0.07, "soil": 0.05, "dirt": 0.05, "watermelon": 0.01}
tinfo = {
    "axe":
        {"blocks": {"wood": 0.03, "bamboo": 0.024, "coconut": 0.035, "cactus": 0.04, "barrel": 0.01, "workbench": 0.02, "wooden-planks": 0.035}},

    "pickaxe":
        {"blocks": {"snow-stone": 0.036, "stone": 0.02, "blackstone": 0.015}, "grave": 0.015},

    "shovel":
        {"blocks": {"soil": 0.16, "dirt": 0.06, "sand": 0.2}},

    "sickle":
        {"blocks": {"hay": 0.10}},

    "scissors":
        {"blocks": {"leaf": 0.04, "vine": 0.02}}
}
fin_mult = 1 / 0.015873
for mult, ore in enumerate(oinfo, 50):
    tinfo["pickaxe"]["blocks"][ore] = (11 - oinfo[ore]["moh"]) * 0.003 * (1 - (1 / mult * fin_mult - 1) * 2.3)
tool_blocks = set(itertools.chain.from_iterable([list(tinfo[tool]["blocks"].keys()) for tool in tinfo]))

# B L O C K  C L A S S I F I C A T I O N S ------------------------------------------------------------- #
walk_through_blocks = ["air", "fire", "water", "vine", "spike-plant", "grass1", "grass2"]
unbreakable_blocks = ["air", "fire", "water"]
item_blocks = ["dynamite"]
unbreakable_blocks = ["air", "water"]
functionable_blocks = ["dynamite", "command-block"]
climbable_blocks = ["vine"]
dif_drop_blocks = {"coconut": [{"block": "coconut-piece", "amount": 2}],
                   "watermelon": [{"block": "watermelon-piece", "amount": 2}]}
fall_damage_blocks = {"hay": 10}
gun_blocks = []
burnable_blocks = []

finfo = {
    "apple":
        {"amounts": {"thirst": 3, "hunger": 3}, "speed": 2},
    "coconut-piece":
        {"amounts": {"thirst": 4, "hunger": 2}, "speed": 1},
    "watermelon":
        {"amounts": {"thirst": 6, "hunger": 4}, "speed": 0.8},
    "chicken":
        {"amounts": {"hunger": 6}, "speed": 1.2}
}

fuinfo = {
    "coal": {"index": 0.02, "sub": 0.1}
}

# crafting info
cinfo = {
    "wooden-planks": {"recipe": {"wood": 1}, "amount": 2, "energy": 5},
    "sand brick": {"recipe": {"sand": 1}, "energy": 7},
    "anvil": {"recipe": {"stone": 1}, "energy": 10},
    "portal-generator": {"recipe": {"water": 1}}
}

# mob info
minfo = {
    "penguin": {True: "", False: {"chicken": 3}}
}


c = 2
for ore in oinfo:
    oinfo[ore]["chance"] = c
    c /= 1.5

# [0] = color, [1] = block-radar
ginfo = {
    "scope": {"prototype": (GREEN + (150,), True)}
}

ainfo = {}

unplacable_blocks = [*gun_blocks, "bucket"]

# loading assets
load_blocks()
load_tools()
load_guns()
load_icons()

# - initializations after asset loading -
# tool crafts
for tool in a.tools:
    o, n = tool.split("_")
    if n == "axe":
        o = norm_ore(o) + ("-ingot" if o != "wood" else "")
        ainfo[tool] = {"recipe": {o: 2, "stick": 1}, "energy": 8}

# transparent blocks
transparent_blocks = []
for name, img in a.blocks.items():
    with suppress(BreakAllLoops):
        for y in range(img.get_height()):
            for x in range(img.get_width()):
                if img.get_at((x, y)) == (0, 0, 0, 0):
                    transparent_blocks.append(name)
                    raise BreakAllLoops

# colored blocks
color_base("orb", orb_colors, unplacable=True)
color_base("armor", ore_colors, unplacable=True)

# rotations
rotate_base("pipe", 2)
rotate_base("curved-pipe", 4)

# chest blocks
chest_blocks = [block for block in a.blocks if block is not None and block not in ("air",)]

# loading sizes
load_sizes()

# last second initializations
oinfo["stone"] = {"moh": 3}
