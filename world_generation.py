import io
import random
import requests
import PIL.Image
from prim_data import a, Entity, get_avatar
from settings import *
from pyengine.basics import *
from pyengine.pgbasics import *
from pyengine.pilbasics import pil2pg


HL = 27
VL = 20
L = VL * HL

avatar_url = r"https://avatars.dicebear.com/api/pixel-art-neutral/:seed.svg?mood[]=:mood"
quote_url = "https://inspirobot.me/api?generate=true"


def get_chest_insides(block_names):
    chest_inventory = []
    chest_amounts = []
    for _ in range(nordis(5, 2)):
        chest_inventory.append(choice(block_names))
        chest_amounts.append(nordis(2, 1) + 1)
    return [list(x) for x in zip(chest_inventory, chest_amounts)]


def get_quote():
    img_url = requests.get(quote_url).text
    img_io = requests.get(img_url).content
    pil_img = PIL.Image.open(io.BytesIO(img_io))
    pil_img = pil_img.resize([s // 2 for s in pil_img.size])
    quote = image_to_string(pil_img)
    quote = "".join([char for char in quote])
    return quote
    
    
def destroy_group(grp):
    for spr in grp:
        spr.kill()


def is_transparent(image):
    if image.get_at((0, 0))[3] == 0:
        return True
    else:
        return False


def rand_block(*args):
    blocklist = []
    chancelist = []
    for arg in args:
        if type(arg) == str:
            blocklist.append(arg)
        elif type(arg) == int or type(arg) == float:
            chancelist.append(arg)
    arr = []
    item = -1
    for i in range(len(chancelist)):
        item += 1
        for i in range(chancelist[item]):
            arr.append(blocklist[item])
    chance = arr[rand(0, 99)]
    return chance


class Biome:
    def __init__(self):
        self.heights = {"forest": 5, "desert": 5, "beach": 3, "mountain": 10, "industry": 2, "wasteland": 3}
        self.blocks = {"forest":   ("f_soil", "dirt"),  "desert":    ("sand", "sand"),
                       "beach":    ("sand", "sand"),    "mountain":  ("snow", "stone"),
                       "swamp":    ("sw_soil", "dirt"), "prairie":   ("hay", "dirt"),
                       "jungle":   ("f_soil", "dirt"),  "savanna":   ("sv_soil", "dirt"),
                       "industry": ("p_soil", "dirt"),  "wasteland": ("dirt", "dirt")}
        self.tree_heights = {"swamp": 4, "jungle": 8, "savanna": 10, "beach": 6}
        self.tree_chances = {"forest": 8, "beach": 16, "swamp": 7, "jungle": 6, "savanna": 20}
        self.wood_types = {"savanna": "sv_wood"}
        self.water_chances = {"forest": 3, "beach": 3, "swamp": 5, "jungle": 4, "savanna": 100}
        self.flatnesses = {"forest": 1, "industry": 10, "beach": 10}
        self.biomes = list(self.blocks.keys())

bio = Biome()


def fromdict(dict_, el, exc, sf=None):
    try:
        try:
            return dict_[el] + sf
        except TypeError:
            return dict_[el]
    except KeyError:
        return exc


def get_leaf_type(blockname):
    try:
        type_ = blockname.split("_")[0]
        a.blocks[type_ + "leaf"]
        return type_ + "_leaf_bg"
    except Exception:
        return "f_leaf_bg"


def world_modifications(data, metadata, screen, layer, biome, blockindex, blockname, abs_screen, block_names, Window):
    horindex = blockindex % HL
    verindex = blockindex // HL
    block_pos = (horindex * 30, verindex * 30)
    block_x, block_y = block_pos
    entities = []
    if "soil" in blockname:
        if 2 <= horindex <= HL - 3:
            if biome in bio.tree_chances:
                tree_chance = chance(1 / bio.tree_chances[biome])
            else:
                tree_chance = 0
            if tree_chance:
                tree_index = blockindex - HL
                tree_height = bio.tree_heights.get(biome, nordis(6, 2))
                wood_type = fromdict(bio.wood_types, biome, exc="wood_bg", sf="_bg")
                leaf_type = get_leaf_type(blockname)
                if biome != "savanna":
                    for i in range(tree_height):
                        data[screen][tree_index] = wood_type
                        tree_index -= HL
                    if biome == "forest" or biome == "swamp":
                        data[screen][tree_index - 2]      = leaf_type
                        data[screen][tree_index - 1]      = leaf_type
                        data[screen][tree_index]          = leaf_type
                        data[screen][tree_index + 1]      = leaf_type
                        data[screen][tree_index + 2]      = leaf_type
                        data[screen][tree_index - HL + 1] = leaf_type
                        data[screen][tree_index - HL]     = leaf_type
                        data[screen][tree_index - HL - 1] = leaf_type
                        data[screen][tree_index - HL * 2] = leaf_type
                    elif biome == "jungle":
                        data[screen][tree_index + HL - 2]     = leaf_type
                        data[screen][tree_index + HL + 2]     = leaf_type
                        data[screen][tree_index - 2]          = leaf_type
                        data[screen][tree_index - 1]          = leaf_type
                        data[screen][tree_index]              = leaf_type
                        data[screen][tree_index + 1]          = leaf_type
                        data[screen][tree_index + 2]          = leaf_type
                        data[screen][tree_index - HL - 1]     = leaf_type
                        data[screen][tree_index - HL]         = leaf_type
                        data[screen][tree_index - HL + 1]     = leaf_type
                        data[screen][tree_index - HL + 2]     = leaf_type
                        data[screen][tree_index - HL * 2 - 2] = leaf_type
                        data[screen][tree_index - HL * 2 - 1] = leaf_type
                        data[screen][tree_index - HL * 2]     = leaf_type
                        data[screen][tree_index - HL * 2 + 1] = leaf_type
                        data[screen][tree_index - HL * 3 - 1] = leaf_type
                        data[screen][tree_index - HL * 3]     = leaf_type
                        data[screen][tree_index - HL * 4 - 1] = leaf_type
                else:
                    for i in range(tree_height):
                        data[screen][tree_index]     = wood_type
                        data[screen][tree_index + 1] = wood_type
                        tree_index -= HL
                    data[screen][tree_index + HL - 1] = leaf_type
                    data[screen][tree_index]          = leaf_type
                    data[screen][tree_index + 1]      = leaf_type
                    data[screen][tree_index + HL + 2] = leaf_type

                # vines
                if biome in ("swamp", "jungle"):
                    vine_height = nordis(tree_height // 2, 2)
                    vine_index = choice((tree_index + HL - 2,
                                                tree_index + HL - 1,
                                                tree_index + HL + 1,
                                                tree_index + HL + 2))
                    for i in range(vine_height):
                        data[screen][vine_index] = "vine"
                        vine_index += HL
                
                    # bamboo
                if biome == "jungle":
                    if chance(1 / 7):
                        bamboo_height = nordis(8, 2)
                        bamboo_index = blockindex - HL
                        for i in range(bamboo_height):
                            data[screen][bamboo_index] = "bamboo_bg"
                            bamboo_index -= HL
             
        if biome == "jungle":
            if 0 <= horindex <= HL - 3:
                # portal
                if chance(1 / 20):
                    e = Entity("portal", block_pos, abs_screen, 1, sort="portal")
                    entities.append(e)
               
        if biome == "forest":
            # watermelons
            if chance(1 / 40):
                data[screen][blockindex - HL] = "watermelon_bg"
        
        if biome == "industry":
            # barrels
            if chance(1 / 40):
                barrel_indexes = [blockindex - HL, blockindex - HL * 2]
                barrel_type = "red_barrel_bg" if chance(1 / 5) else "blue_barrel_bg"
                for bi in barrel_indexes:
                    data[screen][bi] = barrel_type
            # npc
            if chance(1 / 50):
                e = Entity(get_avatar(), (horindex * 30, verindex * 30), abs_screen, 1, name="Joe", script=None, sort="npc")
                entities.append(e)

    if biome == "desert":
        if "sand" in data[screen][blockindex]:         
            if data[screen][blockindex - HL] == "air":
                # camels
                if chance(1 / 50):
                    camel = Entity("camel", block_pos, abs_screen, 1, "bottomleft", sort="camel", parent="passive", smart_vector=True)
                    entities.append(camel)
                    
                # cacti
                if chance(1 / 20):
                    cactus_height = nordis(4, 2)
                    cactus_index = blockindex - HL
                    for i in range(cactus_height):
                        data[screen][cactus_index] = "cactus_bg"
                        cactus_index -= HL
                 
                # temples
                if chance(1 / 5):
                    upp_blocks = [data[screen][blockindex - HL], data[screen][blockindex - 28],
                            data[screen][blockindex - 29], data[screen][blockindex - 26],
                            data[screen][blockindex - 25]]
                    nei_blocks = [data[screen][blockindex - 2], data[screen][blockindex - 1],
                            data[screen][blockindex + 1], data[screen][blockindex + 2]]
                    if upp_blocks.count("air") == len(upp_blocks) and nei_blocks.count("sand") == len(nei_blocks):
                        data[screen][blockindex - HL]  = "chest_bg"
                        data[screen][blockindex - 28]  = "sand_bg"
                        data[screen][blockindex - 29]  = "sand"
                        data[screen][blockindex - 26]  = "sand_bg"
                        data[screen][blockindex - 25]  = "sand"
                        data[screen][blockindex - 54]  = "sand_bg"
                        data[screen][blockindex - 55]  = "sand"
                        data[screen][blockindex - 53]  = "sand"
                        data[screen][blockindex - 81]  = "sand"
                        metadata[screen][layer * L + blockindex - HL]["chest"] = get_chest_insides(block_names)

    elif biome == "beach":
        if "sand" in data[screen][blockindex] and "air" in data[screen][blockindex - HL]:
            if not is_in("wood", (data[screen][blockindex - HL - 1], data[screen][blockindex - HL + 1])):
                if 4 <= horindex <= HL - 2:
                    if biome in bio.tree_chances:
                        tree_chance = chance(1 / bio.tree_chances[biome])
                    else:
                        tree_chance = 0
                    if tree_chance:
                        tree_height = bio.tree_heights["beach"]
                        pairs = []
                        pairs.append(rand(1, tree_height - 1))
                        pairs.append(tree_height - pairs[-1])
                        
                        tree_index = blockindex - HL
                        for i in range(pairs[0]):
                            data[screen][tree_index] = "wood_bg"
                            tree_index -= HL
                        tree_index -= 1
                        for i in range(pairs[1]):
                            data[screen][tree_index] = "wood_bg"
                            tree_index -= HL

                        leaves = [tree_index + HL - 2, tree_index - 1, tree_index + 2,
                                  tree_index, tree_index - HL - 3, tree_index - HL - 1,
                                  tree_index - HL, tree_index - HL + 1, tree_index - HL * 2 - 2,
                                  tree_index - HL * 2, tree_index - HL * 3 + 1]
                        for leaf in leaves:
                            data[screen][leaf] = "f_leaf_bg"
                        for leaf in leaves:
                            if chance(1 / 12):
                                data[screen][leaf] = "coconut"
            
            # rocks
            if biome == "beach":
                if 1 <= horindex <= HL - 1:
                    if chance(1 / 25):
                        data[screen][blockindex - HL] = "rock_bg"

    if blockname == bio.blocks[biome][0]:
        if data[screen][blockindex - HL] == "air":
            if 2 <= horindex <= HL - 1:
                if data[screen][blockindex - 1] == "air" or data[screen][blockindex + 1] == "air":
                    if biome in bio.water_chances:
                        water_chance = chance(1 / bio.water_chances[biome])
                    else:
                        water_chance = 0
                    if water_chance:
                        # check whether water can flow horizontally
                        check_xindex = blockindex
                        faulty = True
                        for i in range(HL - horindex - 1):
                            check_xindex += 1
                            if data[screen][check_xindex] != "air":
                                faulty = False
                                break
                        if not faulty:
                            water_xindex = blockindex + 1
                            while data[screen][water_xindex] == "air":
                                data[screen][water_xindex] = "water"
                                water_yindex = water_xindex + HL
                                while data[screen][water_yindex] == "air":
                                    data[screen][water_yindex] = "water"
                                    water_yindex += HL
                                water_xindex += 1

    return entities
