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
        maj, min, pat = version.split(".")


# W I N D O W ------------------------------------------------------------------------------------------ #
HL = 27
VL = 20
L = VL * HL
BS = 30
R = 3
CS = 8
MHL = HL * BS / R
MVL = VL * BS / R
wb_icon_size = 132, 90


class Window:
    @classmethod
    def init(cls, size, debug=False, *args, **kwargs):
        cls.center = tuple(s // 2 for s in size)
        cls.update_caption()
        # window
        cls.window = pygame.display.set_mode(size, *args, **kwargs)
        # cls.window = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # cls.window = pygame.display.set_mode((pygame.display.Info().current_w, pygame.display.Info().current_h))
        # display
        cls.display = pygame.Surface(size)
        cls.center = tuple(s // 2 for s in cls.display.get_size())
        cls.size = (cls.width, cls.height) = cls.display.get_size()
        cls.diagonal = hypot(cls.width, cls.width)
        if debug:
            pos = (pygame.display.Info().current_w / 2 - cls.width / 2, 0)
            os.environ["SDL_VIDEO_WINDOW_POS"] = ",".join(str(int(c)) for c in pos)
        center_window()

    @classmethod
    def update_caption(cls):
        """pygame.display.set_caption("\u15FF"   # because
                                   "\u0234"      # because
                                   "\u1F6E"      # because
                                   "\u263E"      # because
                                   "\u049C"      # because
                                   "\u0390"      # because
                                   "\u2135"      # because
                                   "\u0193"      # because
                                   "\u15EB"      # because
                                   "\u03A6"      # because
                                   "\u722A"
                                   "")  # because"""
        pygame.display.set_caption(f"Blockingdom {System.version}")


R = 3
BS = 10 * R
BP = 10
HL = 27
VL = 20
L = VL * HL
Window.init((BP * HL * R, BP * VL * R), debug=False)


# V I S U A L  &  B G  I M A G E S --------------------------------------------------------------------- #
cimgload = partial(imgload, scale=R)
# backgrounds
inventory_img = cimgload("Images", "Background", "inventory.png")
inventory_width = inventory_img.get_width()
extended_inventory_img = cimgload("Images", "Background", "extended_inventory.png", after_func=None)
extended_inventory_rect = extended_inventory_img.get_rect(topleft=(0, 138))
tool_holders_img = cimgload("Images", "Background", "tool_holders.png")
tool_holders_width = tool_holders_img.get_width()
square_border_img = cimgload("Images", "Background", "square_border.png")
pouch_img = cimgload("Images", "Background", "pouch.png")
pouch_icon = cimgload("Images", "Background", "pouch_icon.png")
pouch_width = pouch_img.get_width()
player_hit_chart = cimgload("Images", "Background", "player_hit_chart.png")
lock = cimgload("Images", "Player_Skins", "lock.png")
frame_img = scale3x(cimgload("Images", "Background", "frame.png"))
armor_indicator = cimgload("Images", "Background", "armor_indicator.png")
bag_img = cimgload("Images", "Background", "bag.png")
bag_rect = bag_img.get_rect(topleft=(24, 157))
bag_mask = pygame.mask.from_surface(bag_img)
clouds1_img = cimgload("Images", "Background", "clouds1.png")
cursor_img = pygame.Surface((10, 10), pygame.SRCALPHA)
cursor_img.fill(WHITE, (4, 0, 2, 10))
cursor_img.fill(WHITE, (0, 4, 10, 2))
parallaxes = {"clouds1": clouds1_img}

# visuals
arrow_sprs = cimgload("Images", "Spritesheets", "arrow.png", frames=11)
shower_sprs = cimgload("Images", "Spritesheets", "shower.png", frames=9)
chest_template = cimgload("Images", "Visuals", "chest_template.png")
leaf_img = cimgload("Images", "Visuals", "leaf.png")
right_bar_surf = pygame.Surface((50, 200)); right_bar_surf.fill(LIGHT_GRAY)
death_screen = pygame.Surface(Window.size); death_screen.fill(RED); death_screen.set_alpha(150)
cartridge_img = pygame.Surface((10, 3))
cartridge_img.fill((255, 184, 28))
sky_bg = pygame.transform.rotozoom(pygame.transform.scale(lerp_img(SKY_BLUE, WHITE, Window.height, Window.height), Window.size), 90, 1)
#pygame.display.set_icon(cimgload("Images", "Visuals", f"{Platform.os.lower()}_icon.png"))

# surfaces
workbench_img = imgload("Images", "Surfaces", "workbench.png")
_wbi = get_icon("arrow")
workbench_icon = pygame.transform.scale(_wbi, [s // 2 for s in _wbi.get_size()])
furnace_img = imgload("Images", "Surfaces", "furnace.png")
anvil_img = imgload("Images", "Surfaces", "anvil.png")
gun_crafter_img = imgload("Images", "Surfaces", "gun_crafter.png")
gun_crafter_base = SmartSurface(gun_crafter_img.get_size(), "notalpha")
magic_table_img = imgload("Images", "Surfaces", "magic-table.png")
# crafting and midblit constants
crafting_center = (Window.width / 2, Window.height / 2 + 15)
crafting_x, crafting_y = crafting_center
crafting_rect = workbench_img.get_rect(center=[s // 2 for s in Window.size])
chest_rect = chest_template.get_rect(center=Window.center)
chest_rects = []
chest_indexes = {}
chest_rect_start = [p + 3 for p in chest_rect.topleft]
chest_sx, chest_sy = chest_rect_start
_sx, _sy = chest_sx, chest_sy
i = 0
for y in range(5):
    for x in range(5):
        _x = x * 33 + _sx
        _y = y * 51 + _sy
        chest_rects.append(pygame.Rect(_x, _y, 30, 30))
        chest_indexes[_x, _y] = i
        i += 1
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
gun_crafter_part_poss = {k: (v[0] - rx, v[1] - ry) for k, v in gun_crafter_part_poss.items()}

# F O N T S -------------------------------------------------------------------------------------------- #
# a maximum of two (normal + italic) of them is used; the other ones are experimental
def get_fonts(*p, sys=False):
    if not sys:
        return [pygame.font.Font(path("Fonts", *p), i) for i in range(1, 101)]
    else:
        return [pygame.font.SysFont(p[0], i) for i in range(1, 101)]


exo2_fonts = get_fonts("Exo2", "Exo2-Light.ttf")
iexo2_fonts = get_fonts("Exo2", "Exo2-LightItalic.ttf")
elec_fonts = get_fonts("Electrolize", "Electrolize-Regular.ttf")
awave_fonts = get_fonts("Audiowide", "Audiowide-Regular.ttf")
neuro_fonts = get_fonts("NeuropolX", "neuropol x rg.ttf")
orbit_fonts = get_fonts("Orbitron", "Orbitron-VariableFont_wght.ttf")
#dejavu_fonts = get_fonts("DejaVu", "ttf", "DejaVuSans-ExtraLight.ttf")
#cyber_fonts = get_fonts("Cyberbit", "Cyberbit.ttf")
arial_fonts = get_fonts("arial", sys=True)
cambria_fonts = get_fonts("cambria", sys=True)
helvue_fonts = get_fonts("helveticaneue", sys=True)
#pixel_font = Font("Fonts", "Pixel", "pixel.png")
all_fonts = {x: pygame.font.SysFont(x, 30) for x in pygame.font.get_fonts()}

# G R O U P S ------------------------------------------------------------------------------------------ #
all_blocks =                    SmartList()
all_drops =                     SmartGroup()
all_particles =                 SmartGroup()
all_other_particles =           SmartList()
all_projectiles =               SmartGroup()
all_foreground_sprites =        pygame.sprite.Group()
all_home_sprites =              pygame.sprite.Group()
all_home_world_world_buttons =  pygame.sprite.Group()
all_home_world_static_buttons = pygame.sprite.Group()
all_home_settings_buttons =     pygame.sprite.Group()
all_messageboxes =              pygame.sprite.Group()
all_mobs =                      SmartGroup()
all_rests =                     SmartGroup()

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
        self.def_fps_cap = 120
        self.fps_cap = 120
        self.dt = None
        self.events_locked = False
        self.wg = random.Random()
        self.noise = Noise(self.wg)
        # constants
        self.fppp = 3
        self.player_size = (27, 27)
        self.skin_scale_mult = 5
        self.skin_fppp = 15
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
        self.last_break = ticks()
        self.last_music = None
        self.last_ambient = None
        self.first_music = False
        self.pending_entries = []
        # surfaces
        self.night_sky = pygame.Surface(Window.size)
        self.menu_surf = pygame.Surface(Window.size); self.menu_surf.set_alpha(100)
        self.skin_menu_surf = pygame.Surface((Window.width / 11 * 9, Window.height / 11 * 9)); self.skin_menu_surf.fill(LIGHT_GRAY)
        self.skin_menu_rect = self.skin_menu_surf.get_rect(center=[s / 2 for s in Window.display.get_size()])
        # crafting
        self.midblit = None
        self.chest = None
        self.chest_pos = chest_rect.topleft
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
        # magic table
        self.magic_tool = None
        self.magic_orbs = {}
        self.magic_output = None
        self.magic_log = []
        # skin menu
        self.skin_anim_speed = 0.06
        self.skins = {  # "pos" is topleft (of the player model; not the screen) just like normal pixel systems
            "head": [
                {"name": None},
                {"name": "hat", "frames": 4, "offset": (-2, -1)},
                {"name": "headband", "frames": 8, "offset": (-3, -1)},
                {"name": "grass_hat", "frames": 6, "offset": (-2, -4)},
                {"name": "helicopter", "frames": 7, "offset": (0, -5)},
                {"name": "crown", "frames": 6, "offset": (-1, -3)}
            ],
            "face": [
                {"name": None},
                {"name": "glasses", "frames": 5, "frame_pause": 4, "offset": (0, 2)}
            ],
            "shoulder": [
                {"name": None}
            ],
            "body": [
                {"name": None},
                {"name": "detective", "frames": 6, "offset": (0, 5)}
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
        self.fake_scroll = [0, 0]
        self.scroll = [0, 0]
        self.screenshake = 0
        self.s_render_offset = None
        self.render_offset = [0, 0]
        self.clicked_when = None
        self.typing = False
        self.worldbutton_pos_ydt = wb_icon_size[1] + 5
        self.max_worldbutton_pos = [45, 180 + 6 * self.worldbutton_pos_ydt]
        # static attributes
        self.color_codes = {"b": BLACK, "w": WHITE, "g": GREEN, "u": WATER_BLUE, "y": YELLOW}
        self.ttypes = [("Data Files", "*.dat")]
        self.itypes = [("PNG Image Files", "*.png"), ("JPG Image Files", "*.jpg")]
        self.bar_rgb = bar_rgb
        self.flame_rgb = lerp(RED, WATER_BLUE, 50) + lerp(WATER_BLUE, RED, 50)
        self.def_widget_kwargs = {"pos": DPP, "font": orbit_fonts[20]}
        self.def_entry_kwargs  = {"pos": (DPX, DPY - 50), "font": orbit_fonts[20], "key_font": orbit_fonts[15]}
        self.common_languages = {"EN", "FR", "SP"}
        self.nouns = txt2list(path("List_Files", "nouns.txt")) + [verb for verb in txt2list(path("List_Files", "verbs.txt")) if verb.endswith("ing")]
        self.verbs = [verb for verb in txt2list(path("List_Files", "verbs.txt")) if verb.endswith("e")]
        self.adjectives = txt2list(path("List_Files", "adjectives.txt"))
        self.adverbs = txt2list(path("List_Files", "adverbs.txt"))
        self.profanities = txt2list(path("List_Files", "profanities.txt"))
        self.rhyme_url = r"https://api.datamuse.com/words?rel_rhy="
        self.funny_words_url = r"http://names.drycodes.com/10?nameOptions=funnyWords"
        self.name_url = r"https://api.namefake.com"
        self.random_word_url = r"http://api.wordnik.com/v4/words.json/randomWords?hasDictionaryDef=true&minCorpusCount=0&minLength=5&maxLength=15&limit=1&api_key=a2a73e7b926c924fad7001ca3111acd55af2ffabf50eb4ae5"
        self.achievements = {}
        # dynamic surfaces
        if isfile(path("Images", "Background", "home_bg.png")):
            self.home_bg_img = imgload("Images", "Background", "home_bg.png")
            self.home_bg_img.set_alpha(100)
        else:
            self.home_bg_img = self.bglize(cimgload("Images", "Background", "def_home_bg.png"))
        self.home_bg_size = self.home_bg_img.get_size()
        self.fog_img = SmartSurface(Window.size)
        self.fog_light = scale2x(cimgload("Images", "Background", "fog.png"))
        self.loading_world = False
        self.loading_world_perc = 0
        self.loading_world_text = None
        # dynamic other
        self.cannot_place_block = False
        self.process_messageboxworld = True
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
        return pygame.transform.scale2x(img)

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

    @property
    def chest_index(self):
        return chest_indexes[tuple(p + 3 for p in self.chest_pos)]

    @property
    def cur_chest_item(self):
        return self.chest[self.chest_index]

    @cur_chest_item.setter
    def cur_chest_item(self, value):
        self.chest[self.chest_index] = value

    def skin_data(self, bt):
        return self.skins[bt][self.skin_indexes[bt]]

    def set_loading_world(self, tof):
        self.loading_world = self.events_locked = tof
        self.loading_world_perc = 0


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


def non_bg(name):
    return name.replace("_bg", "")


def non_jt(name):
    return name.replace("_jt", "")


def non_wt(name):
    return non_jt(non_bg(name))


def bpure(str_):
    ret = str_
    if ret is None:
        return ""
    ret = non_wt(ret)
    # ret = ret.replace("gold_", "golden_").replace("wood_", "wooden_")
    if "_en" in ret:
        ret = ret.removesuffix("_en")
    if "_deg" in str_:
        ret = str_.split("_")[0]
    if "_st" in str_:
        ret = str_.split("_")[0]
    if "_f" in str_:
        ret = str_.split("_")[0]
    if "_sv" in str_:
        ret = str_.split("_")[0]
    if "_sw" in str_:
        ret = str_.split("_")[0]
    if "_ck" in str_:
        ret = str_.split("_")[0]
    if "_a" in str_:
        ret = str_.split("_")[0]
    ret = ret.replace("_", " ")
    return ret


def gpure(str_):
    return str_.replace("_", " ")


# L A M B D A S ---------------------------------------------------------------------------------------- #
...

# icons
breaking_sprs = cimgload("Images", "Visuals", "breaking.png", frames=4)
