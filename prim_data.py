import pygame
import itertools
from settings import *
from pyengine.basics import *


black_filter = pygame.Surface((30, 30)); black_filter.set_alpha(200)


# F U N C T I O N S ------------------------------------------------------------------------------------ #
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
    return (tool.split("_")[1] if tool is not None else tool) if "_" in tool else tool


# I M A G E S ------------------------------------------------------------------------------------------ #
# constants
STONE_GRAY = (65, 65, 65)
WOOD_BROWN = (87, 44, 0)
DARK_WOOD_BROWN = (80, 40, 0)

class A:
    def __init__(self):
        self.assets = {"blocks": {}, "tools": {}, "icons": {}}
        self.asset_sizes = {}
    
    
a = A()


# images
def load_blocks():
    _bsprs = cimgload("Images", "Spritesheets", "blocks.png")
    block_list = [
        ["air",     "bucket",     "apple",    "bamboo",        "cactus",         "watermelon",       "rock"     ],
        ["chest",   "    ",       "coconut",  "coconut-piece", "command-block",  "wood",             "bush"     ],
        ["       ", "dirt",       "dynamite", "fire",          "      ",         "watermelon-piece", "grass1"   ],
        ["hay",     "    ",       "leaf",     "       ",       "sand",           "workbench",        "grass2"   ],
        ["snow",    "soil",       "stone",    "vine",          "wooden-planks",  "a_wooden-planks",  "stick"    ],
        ["anvil",   "          ", "p_soil",   "blue_barrel",   "red_barrel",     "gun-crafter",       "base-ore"]
    ]
    for y, layer in enumerate(block_list):
        for x, block in enumerate(layer):
            a.assets["blocks"][block] = _bsprs.subsurface(x * 30, y * 30, 30, 30)
    # special one-line blocks
    a.assets["blocks"]["f_soil"] = a.assets["blocks"]["soil"].copy()
    a.assets["blocks"]["sw_soil"] = cfilter(a.assets["blocks"]["soil"].copy(), 150, (30, 12))
    a.assets["blocks"]["sv_soil"] = cfilter(a.assets["blocks"]["soil"].copy(), 150, (30, 12), (68, 95, 35))
    a.assets["blocks"]["sv_wood"] = img_mult(a.assets["blocks"]["wood"].copy(), 1.2)
    a.assets["blocks"]["f_leaf"] = a.assets["blocks"]["leaf"].copy()
    a.assets["blocks"]["sw_leaf"] = cfilter(a.assets["blocks"]["leaf"].copy(), 150, (30, 30))
    a.assets["blocks"]["sk_leaf"] = cfilter(a.assets["blocks"]["leaf"].copy(), 150, (30, 30), PINK)
    a.assets["blocks"]["water"] = pygame.Surface((30, 30), pygame.SRCALPHA); a.assets["blocks"]["water"].fill((17, 130, 177)); a.assets["blocks"]["water"].set_alpha(180)
    a.assets["blocks"]["glass"] = pygame.Surface((30, 30), pygame.SRCALPHA); a.assets["blocks"]["glass"].fill(WHITE, (0, 0, 30, 2)); a.assets["blocks"]["glass"].fill(WHITE, (28, 0, 2, 30)); a.assets["blocks"]["glass"].fill(WHITE, (0, 28, 30, 2)); a.assets["blocks"]["glass"].fill(WHITE, (0, 0, 2, 30))
    a.assets["blocks"]["spike-plant"] = pygame.Surface((30, 30), pygame.SRCALPHA)
    # spike plant
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
            pygame.draw.rect(a.assets["blocks"]["spike-plant"], rgb_mult(GREEN, randf(0.6, 1.4)), (_x, _y, 3, 3))
    pygame.draw.rect(a.assets["blocks"]["spike-plant"], rgb_mult(YELLOW, randf(0.6, 1.4)), (_x, _y, 3, 3))
    # ores
    for name, color in [(oi, oinfo[oi]["color"]) for oi in oinfo]:
        if name != "stone":
            a.assets["blocks"][name] = swap_palette(a.assets["blocks"]["base-ore"], BLACK, color)
    # deleting unneceserry blocks that have been modified anyway
    del a.assets["blocks"]["soil"]
    del a.assets["blocks"]["leaf"]


def load_tools():
    _tsprs = cimgload("Images", "Spritesheets", "tools.png")
    tool_list = [
        ["pickaxe", "axe",    "sickle"],
        ["shovel",  "rake",   "scissors"],
        ["kunai",   "hammer",]
    ]
    tools = {}
    whole_tools = {"stick"}
    for y, layer in enumerate(tool_list):
        for x, tool in enumerate(layer):
            tl = _tsprs.subsurface(x * 30, y * 30, 30, 30)
            for name, color in tool_rarity_colors.items():
                a.assets["tools"][f"{name}_{tool}"] = swap_palette(tl, STONE_GRAY if tool not in whole_tools else WOOD_BROWN, color)
    a.og_tools = {k: v.copy() for k, v in a.assets["tools"].items()}


def load_guns():
    for gun_part in g.tup_gun_parts:
        for gun_filename in os.listdir(path("Images", "Guns", gun_part)):
            gun_name = splitext(gun_filename)[0]
            a.assets["blocks"][f"{gun_name}_{gun_part}"] = cimgload("Images", "Guns", gun_part, gun_filename)
            gun_blocks.append(f"{gun_name}_{gun_part}")
    a.og_blocks = {k: v.copy() for k, v in a.assets["blocks"].items()}
            
            
def load_icons():
    a.assets["icons"] = {}
    icon_sprs = cimgload("Images", "Spritesheets", "icons.png")
    icon_list = [
        ["lives", "hunger", "thirst", "energy", "o2", "xp"]
    ]
    for y, layer in enumerate(icon_list):
        for x, tool in enumerate(layer):
            a.assets["icons"][tool] = icon_sprs.subsurface(x * 15, y * 15, 15, 15)
    a.og_icons = {k: v.copy() for k, v in a.assets["icons"].items()}


def load_asset_sizes():
    for atype, dict_ in a.assets.items():
        for name, img in dict_.items():
            a.asset_sizes[name] = img.get_size()
            

tool_rarity_colors = {"wood": DARK_WOOD_BROWN, "stone": STONE_GRAY, "iron": LIGHT_GRAY, "gold": GOLD_YELLOW, "emerald": LIGHT_GREEN}
tool_rarity_mults = {}
mult = 1
for r in tool_rarity_colors:
    tool_rarity_mults[r] = mult
    mult *= 1.18

# B L O C K  D A T A ----------------------------------------------------------------------------------- #
# ore info
oinfo = {
    "talc":      {"moh": 1,  "cform": "Mg3Si4O10",      "color": MINT},
    "gypsum":    {"moh": 2,  "cform": "CaSO4.2H2O",     "color": LIGHT_GRAY},
    "stone":     {"moh": 3,  "cform": None,             "color": None},            "gold":      {"moh": 3,  "cform": "Au",           "color": GOLD_YELLOW},
    "iron":      {"moh": 4,  "cform": "Fe",             "color": LIGHT_GRAY},
    "palladium": {"moh": 5,  "cform": "Pd",             "color": (190, 173, 210)}, "obisidian": {"moh": 5, "cform": "SiO2",          "color": (20, 20, 20)},
    "titanium":  {"moh": 6,  "cform": "FeTiO3",         "color": (210, 210, 210)}, "uranium":   {"moh": 6, "cform": "U",             "color": MOSS_GREEN},
    "quartz":    {"moh": 7,  "cform": "SiO2",           "color": LIGHT_PINK},
    "topaz":     {"moh": 8,  "cform": "Al2(F,OH)2SiO4", "color": (30, 144, 255)},  "emerald":   {"moh": 8, "cform": "Be3Al2(SiO3)6", "color": LIGHT_GREEN},
    "corundum":  {"moh": 9,  "cform": "Al2O3",          "color": (176, 223, 230)},
    "diamond":   {"moh": 10, "cform": "C",              "color": POWDER_BLUE}
}
ore_blocks = list(oinfo.keys())
ore_blocks.remove("stone")

block_breaking_times = {"stone": 1000, "sand": 200, "hay": 150, "soil": 200, "dirt": 200, "watermelon": 500}
tinfo = {
    "axe":
        {"blocks": {"wood": 0.03, "bamboo": 0.024, "coconut": 0.035, "cactus": 0.04, "barrel": 0.01, "workbench": 0.02}},
    
    "pickaxe":
        {"blocks": {"snow": 0.036, "stone": 0.02, "coal": 0.01}},
    
    "shovel":
        {"blocks": {"soil": 0.16, "dirt": 0.06, "sand": 0.2}},

    "sickle":
        {"blocks": {"hay": 0.10}},

    "scissors":
        {"blocks": {"leaf": 0.04, "vine": 0.02}}
}
breaking = 0.008
for ore in oinfo:
    if ore != "stone":
        tinfo["pickaxe"]["blocks"][ore] = breaking
        breaking /= 1.5
tool_blocks = set(itertools.chain.from_iterable([list(tinfo[tool]["blocks"].keys()) for tool in tinfo]))

# B L O C K  C L A S S I F I C A T I O N S ------------------------------------------------------------- #
walk_through_blocks = ["air", "fire", "water", "vine", "spike-plant", "grass1", "grass2"]
unbreakable_blocks = ["air", "fire", "water"]
item_blocks = ["dynamite"]
unbreakable_blocks = ["air", "water"]
functionable_blocks = ["dynamite", "command-block"]
climbable_blocks = ["vine"]
practically_no_blocks = ["air", "water"]
dif_drop_blocks = {"coconut": {"block": "coconut-piece", "amount": 2},
                   "watermelon": {"block": "watermelon-piece", "amount": 2}}
fall_damage_blocks = {"hay": 10}
gun_blocks = []
finfo = {
    "apple":
        {"amounts": {"thirst": 3, "hunger": 7}, "speed": 2},
    "coconut-piece":
        {"amounts": {"thirst": 4, "hunger": 4}, "speed": 1},
    "watermelon":
        {"amounts": {"thirst": 6, "hunger": 5}, "speed": 0.8}
}

# loading assets
load_blocks()
load_tools() 
load_guns()
load_icons()
load_asset_sizes()

# crafting info
cinfo = {
    "wooden-planks": {"recipe": {"wood": 1}, "amount": 2, "energy": 5},
    "sand brick": {"recipe": {"sand": 1}, "energy": 7},
    "anvil": {"recipe": {"stone": 1}, "energy": 10}
}

for tool in a.assets["tools"]:
    o, n = tool.split("_")
    if n == "axe":
        cinfo[tool] = {"recipe": {norm_ore(o): 2, "stick": 1}, "energy": 8}

chance = 2
for ore in oinfo:
    if ore != "stone":
        oinfo[ore]["chance"] = chance
        chance /= 1.5

# [0] = color, [1] = block-radar
ginfo = {
    "scope": {"prototype": (GREEN + (150,), True)}
}

unplacable_blocks = [*gun_blocks]
