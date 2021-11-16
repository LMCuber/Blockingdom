import pygame
import sys
import random
import inspect
import operator as op
import PIL.Image
import PIL.ImageEnhance
import PIL.ImageDraw
import PIL.ImageFilter
from datetime import date
from pyengine.pgwidgets import *
from pyengine.imports import *
from pyengine.basics import *
from pyengine.pilbasics import *


# N O N - G R A P H I C A L  C L A S S E S  P R E - I N I T I A L I Z E D ------------------------------ #
class BlockNotFoundError(Exception):
    pass
    
      
class System:
    version = "Alpha"
    if version not in ("Alpha", "Beta"):
        maj = version.split(".")[0]
        min = version.split(".")[1]
        pat = version.split(".")[2]
        
    
# W I N D O W ,  S U R F A C E S  A N D  S P R I T E  G R O U P S -------------------------------------- #
class Window:
    width = 810
    height = 600
    size = (width, height)
    center = tuple(s / 2 for s in size)
    pygame.display.set_caption(f"Blockingdom {System.version}")
    window = pygame.display.set_mode((width, height))
    display = SmartSurface(size)
    center_window()
    
    
# V I S U A L  &  B G  I M A G E S --------------------------------------------------------------------- #
cimgload = partial(imgload, scale=3)
# backgrounds
inventory_img = cimgload("Images", "Background", "inventory.png")
tool_holders_img = cimgload("Images", "Background", "tool_holders.png")
square_border_img = cimgload("Images", "Background", "square_border.png")
pouch_img = cimgload("Images", "Background", "pouch.png")
pouch_icon = cimgload("Images", "Background", "pouch_icon.png")
player_hit_chart = cimgload("Images", "Background", "player_hit_chart.png")
lock = cimgload("Images", "Player_Skins", "lock.png")
frame_img = cimgload("Images", "Background", "frame.png")
                         
# visuals
arrow_sprs = cimgload("Images", "Spritesheets", "arrow.png", frames=11)
shower_sprs = cimgload("Images", "Spritesheets", "shower.png", frames=9)
right_bar_surf = pygame.Surface((50, 200)); right_bar_surf.fill(LIGHT_GRAY)
death_screen = pygame.Surface(Window.size); death_screen.fill(RED); death_screen.set_alpha(150)
pygame.display.set_icon(cimgload("Images", "Visuals", "icon.png"))
chest_template = cimgload("Images", "Visuals", "chest_template.png")

# surfaces
workbench_img = imgload("Images", "Surfaces", "workbench.png")
_wbi = get_icon("arrow")
workbench_icon = pygame.transform.scale(_wbi, [s // 2 for s in _wbi.get_size()])
furnace_img = imgload("Images", "Surfaces", "furnace.png")
anvil_img = imgload("Images", "Surfaces", "anvil.png")
gun_crafter_img = imgload("Images", "Surfaces", "gun_crafter.png")
# crafting and midblit constants
crafting_center = (Window.width / 2, Window.height / 2 + 15)
crafting_rect = workbench_img.get_rect(center=[s // 2 for s in Window.size])
chest_rect = chest_template.get_rect(center=Window.center)
w, h = gun_crafter_img.get_size()
rx, ry = 205, 195
crafting_abs_pos = (rx, ry + 30)
crafting_eff_size = (400, 180)
gun_crafter_part_poss = {"stock": (rx + w // 2 - 32, ry + h // 2 - 9),
                         "body": (rx + w // 2, ry + h // 2 - 15),
                         "scope": (rx + w // 2 + 1, ry + h // 2 - 24),
                         "barrel": (rx + w // 2 + 33, ry + h // 2 - 14),
                         "silencer": (rx + w // 2 + 50, ry + h // 2 - 14),
                         "grip": (rx + w // 2 - 6, ry + h // 2),
                         "magazine": (rx + w // 2 + 19, ry + h // 2 + 3)}

# F O N T S -------------------------------------------------------------------------------------------- #
# a maximum of two (normal + italic) of them is used; the other ones are experimental
exo2_fonts = [pygame.font.Font(path("Fonts", "Exo2", "Exo2-Light.ttf"), i) for i in range(1, 101)]
iexo2_fonts = [pygame.font.Font(path("Fonts", "Exo2", "Exo2-LightItalic.ttf"), i) for i in range(1, 101)]
elec_fonts = [pygame.font.Font(path("Fonts", "Electrolize", "Electrolize-Regular.ttf"), i) for i in range(1, 101)]
awave_fonts = [pygame.font.Font(path("Fonts", "Audiowide", "Audiowide-Regular.ttf"), i) for i in range(1, 101)]
pixel_font = Font("pixel_font")
neuro_fonts = [pygame.font.Font(path("Fonts", "NeuropolX", "neuropol x rg.ttf"), i) for i in range(1, 101)]
orbit_fonts = [pygame.font.Font(path("Fonts", "Orbitron", "Orbitron-VariableFont_wght.ttf"), i) for i in range(1, 101)]

# G R O U P S ------------------------------------------------------------------------------------------ #
# Group() refers to my custom group, while pygame.sprite.Group() refers to the built-in pygame group
all_blocks =                    SmartList()
all_drops =                     pygame.sprite.Group()
all_particles =                 SmartGroup()
all_projectiles =               SmartGroup()
all_foreground_sprites =        pygame.sprite.Group()
all_home_sprites =              pygame.sprite.Group()
all_home_world_world_buttons =  pygame.sprite.Group()
all_home_world_static_buttons = pygame.sprite.Group()
all_home_settings_buttons =     pygame.sprite.Group()
all_messageboxes =              pygame.sprite.Group()
all_mobs =                      SmartGroup()

# C O N S T A N T S ------------------------------------------------------------------------------------ #
vowels = {"a", "e", "i", "o", "u"}
consonants = {"b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "y", "z"}
skin_to_rgb = {
               "g": (0, 150, 0), "u": (42, 157, 244), "y": (255, 255, 0),
               "r": (255, 0, 0), "b": BLACK, "w": (255, 255, 255), "p": PINK
              }
builtin_skins = {}
DPX = 810 // 2
DPY = 600 // 2
DPP = (DPX, DPY)

bar_outline_width = 80
bar_outline_height = 9
bar_width = bar_outline_width - 4

def_regen_time = millis(5)


class Game:
    def __init__(self):
        """ The game class has all types of global attributes related to the game, as well as the player and the 'w' object that represents a world & its data """
        # 'global' variables
        self.ckeys = {"p up": K_w, "p left": K_a, "p down": K_s, "p right": K_d}
        # initialization
        self.clock = pygame.time.Clock()
        self.fps_cap = 120
        self.dt = None
        self.events_locked = False
        self.noise = Noise()
        # constants
        self.fppp = 3
        self.player_size = (27, 27)
        self.skin_scale_mult = 5
        self.skin_fppp = 15
        self.player_model = pygame.Surface([s * self.skin_scale_mult for s in self.player_size]); self.player_model.fill(GRAY)
        self.player_model_pos = (338, 233)
        self.tool_range = 30
        self.player_commands = {"tool", "tp", "give"}
        # in-game attributes
        self.stage = "home"
        self.home_stage = None
        self.menu = False
        self.skin_menu = False
        self.first_affection = None
        self.opened_file = False
        # surfaces
        self.night_sky = pygame.Surface(Window.size)
        self.menu_surf = pygame.Surface(Window.size); self.menu_surf.set_alpha(100)
        self.skin_menu_surf = pygame.Surface((Window.width / 11 * 9, Window.height / 11 * 9)); self.skin_menu_surf.fill(LIGHT_GRAY)
        self.skin_menu_rect = self.skin_menu_surf.get_rect(center=[s / 2 for s in Window.display.get_size()])
        # crafting
        self.midblit = None
        self.chest = None
        self.craftings = {}
        self.craftable = None
        self.craft_by_what = None  # list -> int (later)
        self.crafting_log = []
        # furnace
        self.burnings = {}
        self.furnace_log = []
        self.fuels = SmartOrderedDict()
        self.fuel_index = 0
        self.fuel_health = None
        # anvil
        self.smithings = {}
        self.anvil_log = []
        self.smither = None
        # gun crafter
        self.tup_gun_parts = os.listdir(path("Images", "Guns"))
        self.extra_gun_parts = ("scope", "silencer")
        self.tup_gun_parts = tuple(gun_part.lower() for gun_part in self.tup_gun_parts)
        self.gun_parts = dict.fromkeys(self.tup_gun_parts, None)
        self.gun_attrs = {}
        self.gun_img = None
        self.gun_log = []
        # skin menu
        self.skin_anim_speed = 0.06
        self.skins = {  # "pos" is topleft (of the player model; not the screen) just like normal pixel systems
            "head": [
                {"name": None},
                {"name": "hat", "frames": 4, "pos": (-2, -1)},
                {"name": "headband", "frames": 8, "pos": (-3, -1)},
                {"name": "grass_hat", "frames": 6, "pos": (-2, -4)},
                {"name": "helicopter", "frames": 7, "pos": (0, -5)},
                {"name": "crown", "frames": 6, "pos": (-1, -3)}
            ],
            "face": [
                {"name": None},
                {"name": "glasses", "frames": 5, "frame_pause": 4, "pos": (0, 2)}
            ],
            "shoulder": [
                {"name": None}
            ],
            "body": [
                {"name": None},
                {"name": "detective", "frames": 6, "pos": (0, 5)}
            ]
        }
        self.skin_bts = list(self.skins.keys())
        self.skin_indexes = dict.fromkeys(self.skin_bts, 0)
        self.skin_anims = dict.fromkeys(self.skin_bts, 0)
        for bt in self.skins:
            for index, data in enumerate(self.skins[bt]):
                if data["name"] is not None:
                    self.skins[bt][index]["sprs"] = [scalex(img, self.skin_scale_mult) for img in cimgload("Images", "Player_Skins", data["name"] + ".png", frames=data["frames"], frame_pause=data.get("frame_pause", 0))]
                    del self.skins[bt][index]["name"]
                else:
                    self.skins[bt][index]["sprs"] = []
        # spritesheets
        self.portal_sprs = cimgload("Images", path("Spritesheets", "portal.png"), frames=7)
        # rendering
        self.screenshake = 0
        self.s_render_offset = None
        self.render_offset = [0, 0]
        self.clicked_when = None
        self.typing = False
        self.worldbutton_pos_ydt = 40
        self.max_worldbutton_pos = [45, 180 + 6 * self.worldbutton_pos_ydt]
        # static attributes
        self.color_codes = {"b": BLACK, "w": WHITE, "g": GREEN, "u": WATER_BLUE, "y": YELLOW}
        self.ttypes = [("Data Files", "*.dat")]
        self.itypes = [("PNG Image Files", "*.png"), ("JPG Image Files", "*.jpg")]
        self.bar_rgb = bar_rgb()
        self.def_widget_kwargs = {"pos": DPP, "font": orbit_fonts[20]}
        self.common_languages = {"EN", "FR", "SP"}
        self.nouns = txt2list(path("List_Files", "nouns.txt")) + [verb for verb in txt2list(path("List_Files", "verbs.txt")) if verb.endswith("ing")]
        self.verbs = [verb for verb in txt2list(path("List_Files", "verbs.txt")) if verb.endswith("e")]
        self.adjectives = txt2list(path("List_Files", "adjectives.txt"))
        self.adverbs = txt2list(path("List_Files", "adverbs.txt"))
        self.profanities = txt2list(path("List_Files", "profanities.txt"))
        self.rhyme_url = r"https://api.datamuse.com/words?rel_rhy="
        # dynamic surfaces
        if isfile(path("Background", "home_bg.png")):
            self.home_bg_img = cimgload("Images", "Background", "home_bg.png")
            self.home_bg_img.set_alpha(30)
        else:
            self.home_bg_img = self.bglize(cimgload("Images", "Background", "def_home_bg.png"))
        self.home_bg_img_size = self.home_bg_img.get_size()
        self.fog_img = SmartSurface(Window.size)
        self.fog_light = scale2x(cimgload("Images", "Background", "fog.png"))
        self.loading_world = False
        self.loading_world_perc = 0
        self.loading_world_text = None
        # dynamic other
        self.cannot_place_block = False
        # rendering
        self.screen_shake = 0
        self.render_offset = (0, 0)
        self.render_scale = 3
      
    @staticmethod
    def stop():
        pygame.quit()
        sys.exit()

    @staticmethod
    def bglize(img):
        ret = pil2pg(pil_blur(pg2pil(pgscale(img, (Window.width, Window.height - 120))), 10))
        ret.set_alpha(30)
        return ret

    @property
    def mouse(self):
        return pygame.mouse.get_pos()
    
    @property
    def mouses(self):
        return pygame.mouse.get_pressed()
        
    @property
    def keys(self):
        return pygame.key.get_pressed()

    @property
    def mod(self):
        return pygame.key.get_mods()
    
    @property
    def str_mod(self):
        return "_bg" if self.mod == 1 else ""
        
    def skin_data(self, bt):
        return self.skins[bt][self.skin_indexes[bt]]
    
    def set_loading_world(self, tof):
        self.loading_world = self.events_locked = tof
        self.loading_world_perc = 0
    
    def handle_opened_file(self):
        with open("config.json") as f:
            try:
                print(json.load(f))
            except json.decoder.JSONDecodeError:
                MessageboxError(Window.display, "Invalid data in config.json", pos=DPP)
        self.opened_file = False


g = Game()


# F U N C T I O N S ----------------------------------------------------------------------------------- #
def is_in(elm, seq):
    if isinstance(seq, dict):
        itr = iter(seq.keys())
    elif isinstance(seq, (list, tuple, set)):
        itr = iter(seq)
    else:
        raise ValueError(f"Iterable must be a dict, list, tuple or set; not {type(seq)} ({seq}).")
    if bpure(elm) in itr:
        return True
    else:
        return False


def bpure(str_):
    ret = str_.removesuffix("_bg")
    ret = ret.replace("-", " ")
    return ret.split("_")[1] if "_" in ret else ret
        
        
def gpure(str_):
    return str_.replace("_", " ")


# L A M B D A S ---------------------------------------------------------------------------------------- #
inf = lambda num: INF if num == float("inf") else num

# icons

breaking_sprs = cimgload("Images", "Visuals", "breaking.png", frames=4)
