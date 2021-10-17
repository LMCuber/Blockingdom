# S T A R T ------------------------------------------------------------------------------------------- #
import time
start = time.time()

# I M P O R T S --------------------------------------------------------------------------------------- #
import atexit
import string
import pickle
import threading
import tkinter.filedialog
from copy import deepcopy
from settings import *
from prim_data import *
from sounds import *
from world_generation import *
from pyengine.pgwidgets import *
from pyengine.pgaudio import *


# S E T U P ------------------------------------------------------------------------------------------- #
root = tkinter.Tk()
root.withdraw()


# N O R M A L  F U N C T I O N S ---------------------------------------------------------------------- #
def user_command(command):
    try:
        if command.startswith("tool"):
            args = command.split()[1:]
            a.tools[args[0]]  # trying
            g.player.tools[g.player.tooli] = args[0]
            g.player.tool_healths[g.player.tooli] = 100
        elif command.startswith("tp"):
            args = command.split()[1:]
            x, y = args[0], args[1]
            pos = list(map(int, (x, y)))
            g.player.rect.center = pos
        elif command.startswith("give"):
            args = SmartList(int(arg) if arg.isdigit() else arg for arg in command.split()[1:])
            block = args[0]  # trying
            if block in g.player.inventory:
                g.player.inventory_amounts[g.player.inventory.index(block)] += args.get(1, 1)
            else:
                g.player.inventory[args.get(2, 1) - 1] = block
                g.player.inventory_amounts[args.get(2, 1) - 1] = args.get(1, 1)
        elif command:
            raise Exception
    except Exception:
        MessageboxError(Window.display, "Invalid or unusable command", **g.def_widget_kwargs)
    
    
def gwperc(amount):
    g.generating_world_perc = amount


def update_block_states():
    for block in all_blocks:
        if non_bg(block.name) != "water":
            moore = all_blocks.moore(block.index, HL, "edges")
            if is_in("water", [block.name for block in moore]):
                for block in moore:
                    if non_bg(block.name) == "water":
                        block.name = "water"
                        break


def is_clickable(block):
    if g.stage == "freestyle":
        return True
    elif g.stage == "adventure":
        pass


def stop_crafting():
    g.crafting = None
    g.craftings = {}


def is_eatable(food):
    eat = False
    if food in finfo:
        for attr in finfo[food]["amounts"]:
            if g.player.stats[attr]["amount"] != 100:
                eat = True
                break
        else:
            g.player.food_pie = {}
    else:
        eat = False
    return eat


def cust_cursor():
    g.cursor_index += 1
    if g.cursor_index == len(g.cursors):
        g.cursor_index = 0


def apply(elm, thing, default):
    if is_in(elm, thing):
        return thing[bpure(elm)]
    else:
        return default


def rand_ore(default="air"):
    rate = randf(0, 100)
    for ore in reversed(oinfo):
        if ore != "stone":
            if rate < oinfo[ore]["chance"]:
                ret = ore
                break
    else:
        ret = default
    return ret


def get_tinfo(tool, name):
    amount = 0
    try:
        for block in tinfo[tpure(tool)]["blocks"]:
            if block == bpure(name):
                amount = tinfo[tpure(tool)]["blocks"][block] * tool_rarity_mults[norm_ore(tool.split("_")[0])]
                raise BreakAllLoops
        raise BreakAllLoops
    except (BreakAllLoops, KeyError):
        return amount


def get_finfo(name):
    eaten = False
    for food in finfo:
        if food == bpure(name):
            eaten = finfo[food]
            return eaten
    return eaten


def chanced(name, delimeter="/"):
    return choice(name.split(delimeter))


def convert_size(size_bytes):
    if size_bytes == 0:
       return "0B"
    else:
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"


def update_button_data(button):
    name = button.data["world"]
    mb = convert_size(os.path.getsize(path("Worlds", button.data["world"] + ".dat")))
    date = button.data["date"]
    button.overwrite(f"{name} | {mb} | {date}")


def non_bg(name):
    return name.replace("_bg", "")


def utilize_blocks():
    for block in all_blocks:
        block.utilize()
        block.broken = 0


def new_world(worldcode=None):
    if worldcode is not None:
        world_code = worldcode[:]
    else:
        world_code = None

    def create(wn):
        g.set_generating_world(True)
        game_mode = "adventure"  # switching game mode
        if g.p.next_worldbutton_pos[1] < g.max_worldbutton_poss[1]:
            if wn is not None:
                if wn not in g.p.world_names:
                    g.w.screen = 0
                    if world_code is None:
                        try:
                            open(path("tempfiles", wn + ".txt"), "w").close()
                            os.remove(path("tempfiles", wn + ".txt"))
                        except InvalidFilenameError:
                            MessageboxError(Window.display, "Invalid world name", pos=DPP)
                        else:
                            biome = choice(list(bio.blocks.keys()))
                            if not wn:
                                wn = f"New_World_{g.p.new_world_count}"
                                g.p.new_world_count += 1
                            g.w = World()
                            generate_world(biome=biome)
                            group(WorldButton({"world": wn, "mode": game_mode, "date": date.today().strftime("%m/%d/%Y")}, g.p.next_worldbutton_pos), all_home_world_world_buttons)
                            g.p.next_worldbutton_pos[1] += g.worldbutton_pos_ydt
                            g.w.mode = game_mode
                            destroy_widgets()
                            g.menu = False
                            g.w.name = wn
                            g.p.world_names.append(wn)
                            init_world("new")
                    else:
                        generate_world(world_code)
                else:
                    MessageboxError(Window.display, "A world with the same name already exists.", **g.def_widget_kwargs)
                    g.set_generating_world(False)
        else:
            MessageboxError(Window.display, "You have too many worlds. Delete a world to create another one.", **g.def_widget_kwargs)
            g.set_generating_world(False)
        ewn.destroy()
    
    def thread_create(world_name):
        t = Thread(target=create, args=[world_name])
        t.setDaemon(True)
        t.start()
       

    if world_code is not None:
        create()

    ewn = Entry(Window.display, thread_create, "Enter world name:", pos=(DPX, DPY - 30), font=orbit_fonts[20])


def settings():
    g.menu = True
    for widget in pw.death_screen_widgets:
        widget.disable()
    for widget in pw.menu_widgets:
        widget.enable()


def group(spr, grp):
    try:
        grp.add(spr)
    except AttributeError:
        grp.append(spr)
    if grp in (all_drops, all_particles):
        all_foreground_sprites.add(spr)


def empty_group(group):
    for spr in group:
        spr.kill()


def hovering(button):
    if button.rect.collidepoint(g.mouse):
        return True


def delete_all_worlds():
    if g.p.world_names:
        def delete():
            for file_ in os.listdir("Worlds"):
                os.remove(path("Worlds", file_))
                open("variables.dat", "w").close()
                open("buttons.dat", "w").close()
            empty_group(all_home_world_world_buttons)
            g.p.world_names.clear()
            g.w.name = None
            g.p.next_worldbutton_pos = g.p.starting_worldbutton_pos[:]
            g.p.new_world_count = 1
        MessageboxOkCancel(Window.display, "Delete all worlds? This cannot be undone.",
                           pos=DPP, command=delete, font=orbit_fonts[20])
    else:
        MessageboxError(Window.display, "You have no worlds to delete.", **g.def_widget_kwargs)


def cr_block(name, screen=-1, index=None):
    g.w.data[screen].insert(index if index is not None else len(g.w.data[screen]), name)


def init_world(type_):
    if type_ == "new":
        g.player = Player()
        if g.w.mode == "adventure":
            g.player.inventory = ["workbench", "anvil", None, None, None]
            g.player.inventory_amounts = [1, 1, None, None, None]
            g.player.stats = {
                "lives": {"amount": 50, "color": RED, "pos": (32, 20), "last_regen": pgticks(), "regen_time": def_regen_time, "icon": "lives"},
                "hunger": {"amount": 50, "color": ORANGE, "pos": (32, 40), "icon": "hunger"},
                "thirst": {"amount": 50, "color": WATER_BLUE, "pos": (32, 60), "icon": "thirst"},
                "energy": {"amount": 50, "color": YELLOW, "pos": (32, 80), "icon": "energy"},
                "o2": {"amount": 100, "color": SMOKE_BLUE, "pos": (32, 100), "icon": "o2"},
                "xp": {"amount": 0, "color": LIGHT_GREEN, "pos": (32, 120), "icon": "xp"},
            }
        elif g.w.mode == "freestyle":
            g.player.inventory = ["anvil", "bush", "dynamite", "command-block", "workbench"]
            g.player.inventory_amounts = [float("inf") for _ in range(5)]
        g.player.tools = ["stone_axe", None]
        g.player.tool_healths = [100, 100]
        g.player.indexes = {"tool": 0, "block": 0}
    elif type_ == "existing":
        g.player.image = pygame.image.fromstring(g.player.image, (g.player.width, g.player.height), "RGBA")
        g.player.images = [pygame.image.fromstring(img, (g.player.width, g.player.height), "RGBA") for img in g.player.images]
        g.player.stats["lives"]["regen_time"] = def_regen_time
        g.player.stats["lives"]["last_regen"] = pgticks()

    # dynamic surfaces
    g.bars_bg = pygame.Surface((210, len(g.player.stats.keys()) * (17 + 7))); g.bars_bg.fill(GRAY); g.bars_bg.set_alpha(150)
    # player
    g.player.rect.center = (500, 500)
    g.player.yvel = 0
    # Go!
    g.stage = "play"
    g.set_generating_world(False)


def generate_world(worldcode=None, biome=None, screens=5):
    # world data (non-gui)
    if worldcode is None:
        g.w.data.clear()
        g.w.biome_names.clear()
        for _ in range(screens):
            generate_screen(biome)
    else:
        g.w.data = worldcode[:]
    # block sprites (gui)
    if not all_blocks:
        yy = -30
        num = -1
        for y in range(16):
            xx = -30
            yy += 30
            for x in range(HL):
                xx += 30
                num += 1
                block = Block(xx, yy, num)
                all_blocks.append(block)
            xx = -30
        for y in range(1):
            xx = -30
            yy += 30
            for x in range(HL):
                xx += 30
                num += 1
                block = Block(xx, yy, num)
                all_blocks.append(block)
            xx = -30
        for y in range(2):
            xx = -30
            yy += 30
            for x in range(HL):
                xx += 30
                num += 1
                block = Block(xx, yy, num)
                all_blocks.append(block)
            xx = -30
        for y in range(1):
            xx = -30
            yy += 30
            for x in range(HL):
                xx += 30
                num += 1
                block = Block(xx, yy, num)
                all_blocks.append(block)
            xx = -30
    else:
        utilize_blocks()


def generate_screen(biome=None):
    g.w.data.append(SmartList())
    screen = -1
    biome_name = choice(list(bio.blocks.keys())) if biome is None else biome
    g.w.biome_names.append(biome_name)
    biome_pack = bio.blocks[g.w.biome_names[-1]] + ("stone",)
    # ground
    for _ in range(L):
        cr_block("air")
    # noise generation
    noise = linear_noise(bio.heights.get(biome, 4), HL, bio.flatnesses.get(biome, 0))
    # biome (ground)
    noise_num = 0
    for blockindex, blockname in enumerate(g.w.data[screen]):
        if 512 < blockindex < 540:
            noise_index = blockindex
            noise_height = noise[noise_num]
            # uneven height
            noise_height % 2
            if noise_height % 2 == 1:
                ground_height = (noise_height - 1) // 2
                stone_height = (noise_height - 1) // 2
            # even height
            else:
                ground_height = noise_height // 2 - 1
                stone_height = noise_height // 2
            # variate stone (so that it is not the same as the ground, which makes it look ugly)
            variation = rand(0, 2)
            if variation == 1:
                if ground_height != 1:
                    stone_height += 1
                    ground_height -= 1
            elif variation == 2:
                if stone_height != 1:
                    ground_height += 1
                    stone_height -= 1
            if stone_height < 1:
                stone_height = 1
            for _ in range(stone_height):
                g.w.data[screen][noise_index] = chanced(biome_pack[2])
                noise_index -= HL
            for _ in range(ground_height):
                g.w.data[screen][noise_index] = biome_pack[1]
                noise_index -= HL
            g.w.data[screen][noise_index] = biome_pack[0]
            noise_num += 1
    for blockindex, blockname in enumerate(g.w.data[screen]):
        entity_map = world_modifications(g.w.data, screen, g.w.biome_names[-1], blockindex, blockname, len(g.w.data) - 1)
        g.w.entities.extend([Entity(**dict_entity) for dict_entity in entity_map])
    # sky
    for _ in range(L):
        cr_block("air", index=0)
    # underground
    underground = [random.choices(("stone", "air"), weights=(60, 40))[0] for _ in range(L)]
    for _ in range(2):
        cop = SmartList(underground[:])
        for index, block in enumerate(cop):
            nei = cop.moore(index, HL)
            if nei.count("stone") <= 3:
                underground[index] = "air"
            elif nei.count("stone") >= 5:
                underground[index] = "stone"
    underground = [block if block == "air" else rand_ore("stone") for block in underground]
    underground[0:HL] = ["air" for _ in range(HL)]
    g.w.data[-1].extend(underground)


def save_screen(daemonic):
    if not daemonic:
        del g.w.data[g.w.screen][g.w.layer_blocki:g.w.layer_blocki * 2]
        for index, block in enumerate(all_blocks, g.w.layer_blocki):
            g.w.data[g.w.screen].insert(index, block.name)


# S T A T I C  O B J E C T  F U N C T I O N S  -------------------------------------------------------  #
def is_drawable(obj):
    if not hasattr(obj, "visible_when") or obj.visible_when is None or (callable(obj.visible_when) and obj.visible_when()):
        return True
    else:
        return False


def is_home():
    return g.stage == "home"


def is_home_settings():
    return is_home() and g.home_stage == "settings"


def is_home_worlds():
    return is_home() and g.home_stage == "worlds"


# N O N - G R A P H I C A L  C L A S S E S ------------------------------------------------------------ #
class MethodHandler:
    @staticmethod
    def save(stage):
        # home bg image
        if g.stage == "play":
            g.home_bg_img = g.bglize(Window.display.copy())
        else:
            pygame.image.save(g.home_bg_img, path("Bg_Images", "home_bg.png"))
        # world data
        if g.w.screen is not None:
            if g.w.data:
               save_screen(g.generating_world)
            if g.w.name is not None:
                with open(path("Worlds", g.w.name + ".dat"), "wb") as f:
                    pickle.dump(g.w.data, f)
        # entities
        for entity in g.w.entities:
            entity.images = [pygame.image.tostring(image, "RGBA") for image in entity.images]
            entity.image = pygame.image.tostring(entity.image, "RGBA")
        # save button data
        for button in all_home_world_world_buttons:
            if button.data["world"] == g.w.name:
                g.player.width, g.player.height = g.player.image.get_size()
                g.player.image = pygame.image.tostring(g.player.image, "RGBA")
                g.player.images = [pygame.image.tostring(img, "RGBA") for img in g.player.images]
                button.data["player_obj"] = deepcopy(g.player)
                button.data["world_obj"] = deepcopy(g.w)
                break
        if toggle_sd.cycles[toggle_sd.cycle] == "data":
            for button in all_home_world_world_buttons:
                update_button_data(button)
        # save world buttons
        with open("buttons.dat", "wb") as f:
            if all_home_world_world_buttons:
                button_attrs = [button.data for button in all_home_world_world_buttons]
                pickle.dump(button_attrs, f)
        # save data
        with open("variables.dat", "wb") as f:
            pickle.dump(g.p, f)
        # cleanup attributes
        g.w.screen = None
        g.w.name = None
        # final
        if stage == "quit":
            g.stop()
        elif stage == "home":
            g.w.entities.clear()


class World:
    def __init__(self):
        # world-generation / world data related data
        self.data = SmartList()
        self.entities = []
        self.mode = None
        self.screen = 1
        self.layer = 1
        self.biome_names = []
        self.prev_screen = self.data
        self.name = None
        self.gun_names = []
        # game settings
        self.show_hitboxes = False
        # day-night cycle
        self.hound_round = False
        self.hound_round_chance = 20
        self.def_dnc_colors = [SKY_BLUE for _ in range(360)] + lerp(SKY_BLUE, DARK_BLUE, 180) + lerp(DARK_BLUE, BLACK, 180)
        self.hr_dnc_colors = [SKY_BLUE for _ in range(360)] + lerp(SKY_BLUE, ORANGE, 180) + lerp(ORANGE, BLACK, 180)
        self.set_dn_colors()
        self.dnc_direc = op.add
        self.dnc_index = 0
        self.dnc_minutes = 5
        self.dnc_vel = self.dnc_len / g.fps_cap / (self.dnc_minutes * 60 / 2)

    def set_dn_colors(self):
        if random.randint(1, self.hound_round_chance) == 1:
            self.dnc_colors = self.hr_dnc_colors.copy()
        else:
            self.dnc_colors = self.def_dnc_colors.copy()
        self.dnc_len = len(self.dnc_colors)

    @property
    def layer_blocki(self):
        return self.layer * L


class Play:
    def __init__(self):
        self.world_names = []
        self.next_worldbutton_pos = [45, 180]
        self.starting_worldbutton_pos = c1dl(self.next_worldbutton_pos)
        self.new_world_count = 0
        self.loaded_world_count = 0
        self.unlocked_skins = []


class PlayWidgets:
    def __init__(self):
        # menu widgets
        set_default_fonts(orbit_fonts)
        _def_menu_widget_height = 31
        _menu_widget_kwargs = {"anchor": "center", "template": "menu widget", "font": orbit_fonts[15]}
        self.menu_widgets = [
            Checkbox(Window.display, "Show Stats", self.show_stats_command, checked=True, exit_command=self.checkb_sf_exit_command, **_menu_widget_kwargs),
            Checkbox(Window.display, "Show FPS", self.show_fps_command, **_menu_widget_kwargs),
            Checkbox(Window.display, "Show Time", self.show_time_command, **_menu_widget_kwargs),
            Checkbox(Window.display, "Show Hitboxes", check_command=self.show_hitboxes_command, uncheck_command=self.when_not_show_hitboxes_command, **_menu_widget_kwargs),
            Checkbox(Window.display, "Fog", self.fog_command, pos=(DPX, DPY), **_menu_widget_kwargs),
            Button(Window.display, "Change Skin", self.change_skin_command, height=_def_menu_widget_height, **_menu_widget_kwargs),
            Slider(Window.display, "Animation", 0, 20, g.skin_anim_speed * g.fps_cap, height=60, **_menu_widget_kwargs),
            Slider(Window.display, "Volume", 0, 100, 20, height=60, **_menu_widget_kwargs),
            ToggleButton(Window.display, ("WASD", "ZQSD", "Arrow Keys"), command=self.change_movement_command, **_menu_widget_kwargs),
            Button(Window.display, "Save and Quit", self.save_and_quit_command, height=_def_menu_widget_height, **_menu_widget_kwargs),
        ]
        _y = 140
        for mw in self.menu_widgets:
            mw.set_pos((DPX, _y), "midtop")
            if isinstance(mw, Slider):
                _y += 61
            else:
                _y += 32
        _def_death_screen_widget_kwargs = {"anchor": "center", "disabled": True, "disable_type": "static", "font": orbit_fonts[15]}
        self.death_screen_widgets = [
            Label(Window.display, "Death", (DPX, DPY - 64), **_def_death_screen_widget_kwargs),
            Button(Window.display, "Play Again", command=self.quit_death_screen_command, pos=(DPX, DPY), **_def_death_screen_widget_kwargs)
        ]
        self.death_cause = self.death_screen_widgets[0]
        self.right_bar_widgets = self.menu_widgets[1:5]
        self.show_fps_type = self.menu_widgets[2]
        self.skin_fps = self.menu_widgets[6]
        self.volume = self.menu_widgets[7]
        befriend_iterable(self.menu_widgets)
        # skin menu arrow buttons to change the skin
        self.change_skin_buttons = []
        for bt in g.skins:
            self.change_skin_buttons.append({"name": "p-" + bt, "surf": pygame.transform.rotozoom(triangle(height=30), 90, 1)})
            self.change_skin_buttons[-1]["mask"] = pygame.mask.from_surface(self.change_skin_buttons[-1]["surf"])
        for bt in g.skins:
            self.change_skin_buttons.append({"name": "n-" + bt, "surf": pygame.transform.rotozoom(triangle(height=30), 270, 1)})
            self.change_skin_buttons[-1]["mask"] = pygame.mask.from_surface(self.change_skin_buttons[-1]["surf"])
        sx = 135
        x = sx
        y = 135
        for num, button in enumerate(self.change_skin_buttons):
            button["rect"] = button["surf"].get_rect(center=(x, y))
            if num == 3:
                x = Window.width - sx
                y = sx
            else:
                y += 115
        self.skin_done = Button(Window.display, "Done", self.new_player_skin, pos=(DPX, DPY + 90), width=9 * g.skin_fppp, height=30, bg_color=GRAY, template="menu widget", click_effect=True, special_flags=["static"]) # <- confirm skin button

    # menu widget commands
    @staticmethod
    def show_stats_command():
        if g.stage == "play":
            if g.w.mode == "adventure":
                if not g.skin_menu:
                    Window.display.blit(g.bars_bg, (0, 0))
                    x = 32
                    y = 15
                    for data in g.player.stats.values():
                        if data:
                            pygame.draw.rect(Window.display, BLACK, (x, y, bar_outline_width, bar_outline_height), 0, 3, 3, 3, 3)
                            pygame.draw.rect(Window.display, g.bar_rgb[data["amount"] - 1], (*[p + 2 for p in (x, y)], perc(data["amount"], bar_width), bar_outline_height - 4), 0, 3, 3, 3, 3)
                            Window.display.blit(icons[data["icon"]], (x - 22, y - 3))
                            write(Window.display, "midleft", f"{round(data['amount'])} / 100", orbit_fonts[13], BLACK, x + bar_outline_width + 8, y + 3)
                        y += 20

    @staticmethod
    def show_fps_command():
        if g.stage == "play":
            write(Window.display, "topright", int(g.clock.get_fps()), orbit_fonts[20], BLACK, Window.width - 10, 40)

    @staticmethod
    def show_time_command():
        if g.stage == "play":
            write(Window.display, "topright", f"{int(g.w.dnc_index)} / 722", orbit_fonts[20], BLACK, Window.width - 10, 70)

    @staticmethod
    def checkb_sf_exit_command():
        g.menu = False

    @staticmethod
    def show_hitboxes_command():
        g.w.show_hitboxes = True

    @staticmethod
    def fog_command():
        g.fog_img.fill(BLACK)
        g.fog_img.cblit(g.fog_light, g.player.rect.center)
        Window.display.blit(g.fog_img, (0, 0), special_flags=pygame.BLEND_MULT)

    @staticmethod
    def when_not_show_hitboxes_command():
        g.w.show_hitboxes = False

    def change_skin_command(self):
        g.menu = False
        for widget in self.menu_widgets:
            widget.disable()
        self.skin_done.enable()
        g.skin_menu = True

    @staticmethod
    def new_player_skin():
        longest_sprs_len = max([len(g.skin_data(bt)["sprs"]) for bt in g.skins])
        g.player.images = [pygame.Surface((Window.size), pygame.SRCALPHA) for _ in range(longest_sprs_len)]
        _bg = pygame.Surface(g.player_size); _bg.fill(GRAY)
        for image in g.player.images:
            image = SmartSurface.from_surface(image)
            image.cblit(bg, [s / 2 for s in image.get_size()])
        if not g.player.images:
            g.player.images = [pygame.Surface(g.player_size)]; g.player.images[0].fill(GRAY)
        for anim in range(longest_sprs_len):
            for bt in g.skins:
                if g.skin_data(bt).get("name", True) is not None:
                    try:
                        skin_img = scalex(g.skin_data(bt)["sprs"][anim], 1 / g.skin_scale_mult)
                    except IndexError:
                        skin_img = scalex(g.skin_data(bt)["sprs"][anim % 4], 1 / g.skin_scale_mult)
                    finally:
                        _sp = g.skin_data(bt)["pos"]
                        skin_pos = [s / 2 for s in Window.size]
                        skin_pos[0] -= g.player_size[0] / 2
                        skin_pos[1] -= g.player_size[1] / 2
                        skin_pos[0] += _sp[0] * g.fppp
                        skin_pos[1] += _sp[1] * g.fppp
                        g.player.images[anim].blit(skin_img, skin_pos)
        rects = [pg2pil(image).getbbox() for image in g.player.images]
        x1 = min([rect[0] for rect in rects])
        y1 = min([rect[1] for rect in rects])
        x2 = max([rect[2] for rect in rects])
        y2 = max([rect[3] for rect in rects])
        rect = pil_rect2pg((x1, y1, x2, y2))
        g.player.images = [image.subsurface(rect) for image in g.player.images]
        g.player.rect = g.player.images[0].get_rect(center=g.player.rect.center)
        g.player.width, g.player.height = g.player.images[0].get_size()
        g.skin_menu = False

    @staticmethod
    def change_movement_command(type_):
        if type_ != "Arrow Keys":
            for index, key in enumerate(type_):
                g.keys[list(g.keys.keys())[index]] = getattr(pygame, f"K_{key.lower()}")
        else:
            g.keys["p up"] = pygame.K_UP
            g.keys["p left"] = pygame.K_LEFT
            g.keys["p down"] = pygame.K_DOWN
            g.keys["p right"] = pygame.K_RIGHT

    @staticmethod
    def save_and_quit_command():
        destroy_widgets()
        empty_group(all_drops)
        MethodHandler.save("home")
        g.stage = "home"
        g.menu = False

    # home static widgets
    @staticmethod
    def is_worlds_worlds():
        return g.stage == "home" and g.home_stage == "worlds"

    @staticmethod
    def is_worlds_static():
        return g.stage == "home" and g.home_stage == "static"

    @staticmethod
    def is_home():
        return g.stage == "home"

    # death screen widget commands
    def quit_death_screen_command(self):
        g.player.dead = False
        for widget in self.death_screen_widgets:
            widget.disable()
        g.w.screen, g.w.layer = g.player.spawn_data

    # outer widget commands
    @staticmethod
    def button_lw_command():
        if not all_messageboxes:
            loading_path = tkinter.filedialog.askopenfilename(title="Load a .dat file", filetypes=g.ttypes)
            if loading_path != "":
                with open(loading_path, "rb") as f:
                    worldcode = pickle.load(f)
                new_world(worldcode)

    @staticmethod
    def button_daw_command():
        if not all_messageboxes:
            delete_all_worlds()

    @staticmethod
    def toggle_sd_command():
        if toggle_sd.cycle < len(toggle_sd.cycles) - 1:
            toggle_sd.cycle += 1
        else:
            toggle_sd.cycle = 0
        toggle_sd.overwrite(toggle_sd.cycles[toggle_sd.cycle])
        if toggle_sd.cycles[toggle_sd.cycle] == "data":
            for button in all_home_world_world_buttons:
                update_button_data(button)
        elif toggle_sd.cycles[toggle_sd.cycle] == "name":
            for button in all_home_world_world_buttons:
                button.overwrite(button.data["world"])

    @staticmethod
    def set_home_stage_worlds():
        g.home_stage = "worlds"

    @staticmethod
    def set_home_stage_settings():
        g.home_stage = "settings"


g.w = World()
g.p = Play()
pw = PlayWidgets()


# G R A P H I C A L  C L A S S E S S ------------------------------------------------------------------ #
class Player:
    def __init__(self):
        self.images = [pygame.Surface(g.player_size) for _ in range(4)]
        for image in self.images:
            image.fill(GRAY)
        self.anim = 0
        self.update_animation()
        self.rect = self.image.get_rect(center=(Window.width / 2, Window.height / 2))
        self.rect.center = (Window.width / 2, Window.height / 2)
        self.width = self.rect.width
        self.height = self.rect.height
        self.gravity = 0.15
        self.fre_vel = 3
        self.adv_xvel = 2
        self.water_xvel = 1
        self.yvel = 0
        self.def_jump_yvel = -4.5
        self.jump_yvel = self.def_jump_yvel
        self.water_jump_yvel = self.jump_yvel / 2
        self.fall_effect = 0
        self.dx = 0
        self.dy = 0
        self.direc = "left"
        self.still = True
        self.in_air = True
        self.invisible = False
        self.skin = None
        self.stats = {}
        self.moving_mode = "adventure"
        self.def_food_pie = {"counter": -90}
        self.food_pie = self.def_food_pie.copy()
        self.achievements = {"steps taken": 0, "steps counting": 0}
        self.dead = False
        self.spawn_data = (g.w.screen, g.w.layer)

        self.rand_username()

        self.tools = []
        self.tool_healths = []
        self.tool_ammos = []
        self.inventory = []
        self.inventory_amounts = []
        self.indexes = {}
        self.pouch = 0
        self.broken_blocks = defaultdict(int)
        self.main = "block"

    def function(self):
        self.draw()
        self.dx = 0
        self.dy = 0
        if no_entries():
            getattr(self, self.moving_mode + "_move")()
        self.update_move()
        self.external_gravity()
        self.off_screen()
        self.drops()
        self.update_fall_effect()
        self.update_animation()
        self.update_effects()

    @property
    def lives(self):
        return self.stats["lives"]["amount"]

    @property
    def item(self):
        return self.inventory[self.indexes[self.main]]

    @property
    def itemi(self):
        return self.indexes[self.main]

    @property
    def block(self):
        return self.inventory[self.indexes["block"]]

    @property
    def blocki(self):
        return self.indexes["block"]

    @property
    def tool(self):
        return self.tools[self.indexes["tool"]]

    @property
    def tooli(self):
        return self.indexes["tool"]

    @property
    def amount(self):
        return self.inventory_amounts[self.indexes[self.main]]

    def draw(self):
        Window.display.blit(self.image, self.rect)
        
    def interact_with_npcs(self):
        pass # TODO

    def die(self, cause):
        self.dead = True
        pw.death_cause.overwrite(f"{self.username} has died. Cause of death: {cause}")
        for widget in pw.death_screen_widgets:
            widget.enable()

    def use_up_inv(self, index, amount=1):
        self.inventory_amounts[index] -= amount
        if self.inventory_amounts[index] == 0:
            self.inventory[index] = None
            self.inventory_amounts[index] = None

    def take_dmg(self, amount, scrsh_offset, scrsh_length):
        self.stats["lives"]["amount"] -= amount
        self.stats["lives"]["regen_time"] = def_regen_time
        self.stats["lives"]["last_regen"] = pgticks()
        g.screen_shake = scrsh_length
        g.s_render_offset = scrsh_offset

    def heal(self, amount):
        self.stats["lives"]["amount"] += amount

    def eat(self):
        food = g.player.inventory[self.indexes["block"]]
        self.food_pie["counter"] += get_finfo(self.inventory[self.indexes["block"]])["speed"]
        degrees = self.food_pie["counter"]
        pie_size = (40, 40)
        pil_img = PIL.Image.new("RGBA", [s * 4 for s in pie_size])
        pil_draw = PIL.ImageDraw.Draw(pil_img)
        pil_draw.pieslice((0, 0, *[ps - 1 for ps in pie_size]), -90, degrees, fill=GRAY)
        pil_img = pil_img.resize(pie_size, PIL.Image.ANTIALIAS)
        del pil_draw
        self.food_pie["image"] = pil2pg(pil_img)
        self.food_pie["rect"] = self.food_pie["image"].get_rect()
        if self.food_pie["counter"] >= 270:
            for attr in finfo[food]["amounts"]:
                if self.stats[attr]["amount"] < 100:
                    self.stats[attr]["amount"] += finfo[food]["amounts"][attr]
                if self.stats[attr]["amount"] > 100:
                    self.stats[attr]["amount"] = 100
            self.use_up_inv(self.blocki)
            self.food_pie = self.def_food_pie.copy()

    def update_fall_effect(self):
        for block in all_blocks:
            if self.rect.colliderect(block.rect):
                if bpure(block.name) == "water":
                    self.fall_effect /= 5
                    break
        else:
            self.fall_effect = self.yvel

    def update_effects(self):
        self.jump_yvel = self.def_jump_yvel / 3 * 1.8 + perc(self.stats["energy"]["amount"], self.def_jump_yvel / 3 * 1.2)

    def drops(self):
        for drop in all_drops:
            if drop.rect.colliderect(self.rect):
                if drop.name in self.inventory:
                    index = self.inventory.index(drop.name)
                    self.inventory_amounts[index] += drop.drop_amount
                    drop.kill()
                    pitch_shift(pickup_sound).play()
                elif self.inventory.count(None) > 0:
                    add_index = first(self.inventory, None, self.indexes["block"])
                    self.inventory[add_index] = drop.name
                    self.inventory_amounts[add_index] = drop.drop_amount
                    drop.kill()
                    pitch_shift(pickup_sound).play()
                else:
                    drop.rect.center = [pos + random.randint(-1, 1) for pos in drop.og_pos]

    def rand_username(self):
        self.username = f"Player{rand(0, 9)}{rand(0, 9)}"

    def cust_username(self):
        def set_username(ans):
            if ans is not None and ans != "":
                split_username = ans.split(" ")
                username = " ".join([word if not word in g.profanities else len(word) * "*" for word in split_username])

                self.username = username
            else:
                self.rand_username()
        Entry(Window.display, set_username, "Enter your new username:", pos=DPP, default_text=("random", orbit_fonts[20]))

    def movex(self, xvel):
        self.dx += xvel
        if xvel > 0:
            self.direc = "right"
        else:
            self.direc = "left"
        self.still = False

    def movey(self, yvel):
        self.dy += yvel

    def freestyle_move(self):
        keys = pygame.key.get_pressed()
        if keys[g.keys["p up"]]:
            self.movey(-self.fre_vel)
        if keys[g.keys["p down"]]:
            self.movey(self.fre_vel)
        if keys[g.keys["p left"]]:
            self.movex(-self.fre_vel)
        if keys[g.keys["p right"]]:
            self.movex(self.fre_vel)

    def adventure_move(self):
        # jumping
        keys = pygame.key.get_pressed()
        if keys[g.keys["p up"]]:
            if not self.in_air and self.yvel <= 0:
                self.yvel = self.jump_yvel
                self.in_air = True

        # xvel
        if keys[g.keys["p left"]]:
            self.movex(-self.adv_xvel)
        elif keys[g.keys["p right"]]:
            self.movex(self.adv_xvel)
        else:
            self.still = True

        # yvel
        self.yvel += self.gravity
        self.dy += self.yvel
        for block in all_blocks:
            if block.name not in walk_through_blocks and "_bg" not in block.name:
                # x-collision
                if block.rect.colliderect(self.rect.x + self.dx, self.rect.y, self.width, self.height):
                    self.dx = 0

                # y-collision
                if block.rect.colliderect(self.rect.x, self.rect.y + self.dy, self.width, self.height):
                    if self.yvel < 0:
                        self.dy = block.rect.bottom - self.rect.top
                        self.yvel = 0
                    elif self.yvel >= 0:
                        if g.w.mode == "adventure":
                            if self.yvel >= 8 and self.fall_effect != 0:
                                self.take_dmg(round(self.yvel * 5 / fall_damage_blocks.get(block.name, 1)), 5, 30)
                                if g.player.stats["lives"]["amount"] <= 0:
                                    g.player.die("fell from high ground")
                        self.dy = block.rect.top - self.rect.bottom
                        self.yvel = 0
                        self.in_air = False

        # other important collisions with blocks
        for block in all_blocks:
            if self.rect.colliderect(block.rect):
                # spike plant
                if bpure(block.name) == "bush":
                    if not self.invisible:
                        self.image.set_alpha(150)
                        self.invisible = True
                if bpure(block.name) == "spike-plant":
                    self.take_dmg(0.03, 1, 1)

        else:
            if self.invisible:
                self.invisible = False
                self.image.set_alpha(255)

        if self.rect.bottom < 0:
            utilize_blocks()

    def gain_ground(self):
        while any(ground_cols := [self.rect.colliderect(block.rect) and block.name not in walk_through_blocks for block in all_blocks]):
            self.rect.y -= 1

    def off_screen(self):
        if self.rect.right < 0:
            save_screen(g.generating_world)
            self.rect.left = Window.width - 1
            if g.w.screen > 0:
                g.w.screen -= 1
            else:
                g.w.screen = len(g.w.data) - 1
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

        elif self.rect.left > Window.width:
            save_screen(g.generating_world)
            self.rect.right = 1
            if g.w.screen < len(g.w.data) - 1:
                g.w.screen += 1
            else:
                generate_screen(random.choice(bio.biomes))
                g.w.screen += 1
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

        elif self.rect.top > Window.height:
            save_screen(g.generating_world)
            self.rect.top = 1
            self.dy = 0
            self.yvel = 0
            g.w.layer += 1
            if g.w.layer > 2:
                g.player.die("fell into the void")
            else:
                empty_group(all_drops)
                utilize_blocks()
                self.gain_ground()

        elif self.rect.bottom < 0:
            save_screen(g.generating_world)
            self.rect.top = Window.height - 1
            g.w.layer -= 1
            if g.w.layer < 0:
                g.w.layer = 0
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

    def update_move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        adx = abs(self.dx) + floor(abs(self.dy))
        self.achievements["steps taken"] += adx
        self.achievements["steps counting"] += adx
        if self.achievements["steps counting"] >= 10_000:
            # TODO: hunger
            self.stats["hunger"]["amount"] -= nordis(5, 5)
            self.achievements["steps counting"] = 0

    def external_gravity(self):
        pass

    def update_animation(self):
        self.anim += pw.skin_fps.value / g.fps_cap
        try:
            self.image = self.images[int(self.anim)]
        except IndexError:
            self.anim = 0
            self.image = self.images[int(self.anim)]


class Visual:
    def __init__(self):
        self.angle = 0
    
    def function(self):
        if g.player.main == "block":
            if g.player.block is not None:
                self.og_img = a.blocks[g.player.block]
                self.image = pygame.transform.scale(self.og_img, [s // 2 for s in self.og_img.get_size()])
                self.rect = self.image.get_rect()
                if g.player.direc == "left":
                    self.rect.right = g.player.rect.left - 5
                elif g.player.direc == "right":
                    self.rect.left = g.player.rect.right + 5
                self.rect.centery = g.player.rect.centery
                Window.display.blit(self.image, self.rect)
        elif g.player.main == "tool":
            if g.player.tool is not None:
                self.og_img = a.tools[g.player.tool]
                self.image = self.og_img.copy()
                self.rect = self.image.get_rect()
                if g.player.direc == "left":
                    self.image = pygame.transform.rotozoom(self.og_img.copy(), self.angle, 1)
                elif g.player.direc == "right":
                    self.image = pygame.transform.rotozoom(pygame.transform.flip(self.og_img, True, False), self.angle, 1)
                self.rect.center = g.mouse
                if abs(g.player.rect.centerx - g.mouse[0]) >= g.tool_range:
                    self.rect.x += g.player.rect.centerx - g.mouse[0] + (g.tool_range if g.mouse[0] > g.player.rect.centerx else -g.tool_range)
                if abs(g.player.rect.centery - g.mouse[1]) >= g.tool_range:
                    self.rect.y += g.player.rect.centery - g.mouse[1] + (g.tool_range if g.mouse[1] > g.player.rect.centery else -g.tool_range)
                Window.display.blit(self.image, self.rect)


class Block:
    def __init__(self, x, y, index):
        self.index = index
        self.utilize()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.broken = 0
        self.last_break = pgticks()
        self.light = 1

    @property
    def layer_index(self):
        return self.index + g.w.layer_blocki

    def update(self):
        self.dynamic_methods()
        self.check_not_hovering()
        self.draw()

    def dynamic_methods(self):
        if "dirt" in self.name:
            if all_blocks[self.index - HL].name in practically_no_blocks:
                with AttrExs(self, "last_dirt", pgticks()):
                    if pgticks() - self.last_dirt >= 5000:
                        self.name = bio.blocks[g.w.biome_names[g.w.screen]][0] + ("_bg" if "_bg" in self.name else "")


    def check_not_hovering(self):
        if not is_in(self.name, tool_blocks):
            if not self.rect.collidepoint(g.mouse):
                self.broken = 0


    def draw(self):
        Window.display.blit(self.image, self.rect)

    def try_breaking(self, type_="normal"):
        drops = []
        if type_ == "normal":
            if non_bg(self.name) not in oinfo:
                breaking_time = apply(self.name, block_breaking_times, 500)
                if pgticks() - self.last_break >= breaking_time:
                    self.broken += 1
                    if self.broken >= 5:
                        if is_in(self.name, dif_drop_blocks):
                            drops.append(Drop(dif_drop_blocks[non_bg(self.name)]["block"], self.rect.centerx + rand(-5, 5), self.rect.centery + rand(-5, 5), self.name))
                        else:
                            drops.append(Drop(non_bg(self.name), self.rect.centerx + rand(-5, 5), self.rect.centery + rand(-5, 5), self.name))
                    self.last_break = pgticks()

        elif type_ == "tool":
            if get_tinfo(g.player.tool, self.name):
                self.broken += get_tinfo(g.player.tool, self.name)
                if chance(1 / 20):
                    group(BreakingBlockParticle(self.name, (self.rect.centerx, self.rect.top + rand(-2, 2))), all_particles)

            if self.broken >= 5:
                # block itself
                if is_in(self.name, dif_drop_blocks):
                    drops.append(Drop(dif_drop.blocks[non_bg(self.name)]["block"], self.rect.centerx + rand(-5, 5), self.rect.centery + rand(-5, 5), self.name))
                else:
                    drops.append(Drop(non_bg(self.name), self.rect.centerx + rand(-5, 5), self.rect.centery + rand(-5, 5), self.name))
                g.player.tool_healths[g.player.tooli] -= (11 - oinfo[g.player.tool.split("_")[0]]["moh"]) / 8
                # extra drops
                if "leaf" in self.name and chance(1 / 20):
                    drops.append(Drop("apple", self.rect.centerx + rand(-5, 5), self.rect.centery + rand(-5, 5), self.name))

        if self.broken >= 5:
            g.player.broken_blocks[non_bg(self.name)] += 1
            data = g.w.data[g.w.screen]
            self.name = "air"
            self.image = a.blocks[self.name].copy()
            self.broken = 0
            update_block_states()

        if type_ in ("normal", "tool"):
            for drop in drops:
                group(drop, all_drops)

    def utilize(self):
        self.name = g.w.data[g.w.screen][self.layer_index]
        self.image = a.blocks[non_bg(self.name)].copy()
        if self.name.endswith("_bg"):
            self.image = img_mult(self.image, 0.7)
        #self.image = pygame.transform.scale2x(self.image)
        #self.image = pygame.transform.rotate(self.image, rand(0, 360))

    def function(self):
        if "dynamite" in self.name:
            exloded_indexes = [
                                self.index - 28, self.index - HL, self.index - 26,
                                self.index - 1,  self.index,      self.index + 1,
                                self.index + 26, self.index + HL, self.index + 28
                              ]
            for block in all_blocks:
                if block.index != self.index and block.index in exloded_indexes and block.name == "dynamite":
                    block.function()
                elif block.index in exloded_indexes:
                    block.name = "air"
                    block.image = a.blocks["air"].copy()
                    update_block_states()
        elif "command-block" in self.name:
            def set_command(cmd):
                self.cmd = cmd
            Entry(Window.display, set_command, "Enter your command:", pos=DPP)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, size, mouse, speed):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface(size)
        self.w, self.h = self.image.get_size()
        self.x, self.y = pos
        self.xvel, self.yvel = pos_mouse_to_vel(pos, mouse, 15)
    
    def draw(self):
        Window.display.blit(self.image, (self.x, self.y))

    def update(self):
        self.x += self.xvel
        self.y += self.yvel
        if self.x - self.w <= 0 or self.x >= Window.width or self.y - self.h <= 0 or self.y >= Window.height:
            all_projectiles.remove(self)


class Drop(pygame.sprite.Sprite):
    def __init__(self, name, x, y, prev):
        pygame.sprite.Sprite.__init__(self)
        self.name = name
        self.drop_amount = apply(prev, dif_drop_blocks, 1)
        self.image = a.blocks[self.name].copy()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.image = pygame.transform.scale(self.image, (self.width // 3, self.height // 3))
        self.rect = self.image.get_rect(center=(x, y))
        self.og_pos = self.rect.center


class Hovering:
    __slots__ = ["image", "rect", "faulty", "show"]

    def __init__(self):
        self.image = pygame.Surface((30, 30))
        self.image.fill(WHITE)
        self.image.set_alpha(120)
        self.rect = self.image.get_rect()

    def function(self):
        self.faulty = False
        self.show = True
        if g.player.main == "block":
            for block in all_blocks:
                if block.rect.collidepoint(g.mouse):
                    if g.player.item not in finfo:
                        if g.w.mode == "adventure":
                            if abs(g.player.rect.x - block.rect.x) // 30 > 3 or abs(g.player.rect.y - block.rect.y) // 30 > 3:
                                self.faulty = True
                            if block.rect.collidepoint(g.mouse):
                                self.rect.center = block.rect.center
                    else:
                        self.show = False
            if self.faulty:
                self.image.fill(RED)
            else:
                self.image.fill(WHITE)
        else:
            self.show = False
        if self.show:
            Window.display.blit(self.image, self.rect)


class BreakingBlockParticle(pygame.sprite.Sprite):
    def __init__(self, name, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = a.blocks[non_bg(name)]
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.image = pygame.transform.scale(self.image, (self.width // 4, self.height // 4))
        self.rect = self.image.get_rect(center=pos)
        self.xvel = rand(-2, 2)
        self.yvel = -3
        self.start_time = pgticks()

    def update(self):
        self.yvel += 0.3
        self.rect.x += self.xvel
        self.rect.y += self.yvel
        if pgticks() - self.start_time >= 200:
            self.kill()


class Entity:
    def __init__(self, images, pos, screen, anchor="bottomleft", *args, **kwargs):
        self.images = images
        self.anim = 0
        self.image = self.images[int(self.anim)]
        self.rect = self.image.get_rect()
        setattr(self.rect, anchor, [p * 30 for p in pos])
        self.screen = screen
        self.sizes = [image.get_size() for image in self.images]
        for k, v in kwargs.items():
            setattr(self, k, v)
        
    def is_drawable(self):
        return g.w.screen == self.screen

    def update(self):
        if self.is_drawable():
            self.animate()
            self.draw()

    def draw(self):
        Window.display.blit(self.image, self.rect)

    def animate(self):
        self.anim += pw.skin_fps.value / g.fps_cap
        try:
            self.image = self.images[int(self.anim)]
        except IndexError:
            self.anim = 0
            self.image = self.images[int(self.anim)]


class Mob:
    def __init__(self, mobtype):
        self.image = pygame.Surface((50, 50))
        self.image.fill((0, 100, 0))
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.bottom = Window.height - 3 * 30
        self.screen = 0
        self.mob_type = mobtype

        self.mob_poss = {"bird": (Window.width / 2, 100)}
        self.rect.center = self.mob_poss[self.mob_type]

    def bird(self):
        self.rect.x += rand(2, 2)

    def draw(self):
        Window.display.blit(self.image, self.rect)

    def function(self):
        getattr(self, self.mob_type)()
        if self.screen == g.w.screen:
            self.draw()
        if self.rect.left >= Window.width:
            if self.screen < len(g.w.data) - 1:
                self.screen += 1
            else:
                self.screen = 0
            self.rect.right = 0
        elif self.rect.right < 0:
            if self.screen > 0:
                self.screen -= 1
            else:
                self.screen = len(g.w.data) - 1
            self.rect.left = Window.width


class WorldButton(pygame.sprite.Sprite):
    def __init__(self, data, pos, text_color=BLACK, colorkey=None):
        pygame.sprite.Sprite.__init__(self)
        self.data = data.copy()
        w, h = orbit_fonts[20].size(str(data["world"]))
        self.image = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
        #self.image.fill(LIGHT_BROWN)
        pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        if colorkey is not None:
            self.image.set_colorkey(colorkey)
        write(self.image, "center", data["world"], orbit_fonts[20], BLACK, *[s / 2 for s in self.image.get_size()])
        #pxlfont.render(self.image, data["world"], [s / 2 for s in self.image.get_size()])
        self.rect = self.image.get_rect(topleft=pos)
        self.data["pos"] = pos[:]

    def overwrite(self, inputtext, name=False):
        if name:
            g.p.world_names.remove(self.data["world"])
            g.p.world_names.append(inputtext)
            self.data["world"] = inputtext
        w, h = orbit_fonts[20].size(str(inputtext))
        self.image = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
        pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        write(self.image, "center", inputtext, orbit_fonts[20], BLACK, *[s / 2 for s in self.image.get_size()])
        self.rect = self.image.get_rect(topleft=self.rect.topleft)


class StaticWidget:
    def __init__(self, grp, visible_when):
        group(self, grp)
        self.visible_when = visible_when


class StaticButton(pygame.sprite.Sprite, StaticWidget):
    def __init__(self, text, pos, group, bg_color=WHITE, text_color=BLACK, anchor="center", size="icon", icon=None, command=None, visible_when=None):
        pygame.sprite.Sprite.__init__(self)
        StaticWidget.__init__(self, group, visible_when)
        if size == "world":
            tw, th = 225, 24
        else:
            tw, th = orbit_fonts[20].size(text)
        if icon:
            tw += 35
        w, h = tw + 10, th + 10
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, bg_color, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        self.text_color = text_color
        if not icon:
            write(self.image, "center", text, orbit_fonts[20], self.text_color, tw / 2 + 5, th / 2 + 5)
        else:
            write(self.image, "midright", text, orbit_fonts[20], self.text_color, tw + 5, th / 2 + 5)
            self.image.blit(get_icon(icon), (0, 0))
        self.rect = self.image.get_rect()
        self.command = command
        setattr(self.rect, anchor, pos)

    def process_event(self, event):
        if is_left_click(event):
            if is_drawable(self):
                if self.rect.collidepoint(g.mouse):
                    self.command()


class StaticToggleButton(pygame.sprite.Sprite, StaticWidget):
    def __init__(self, cycles, pos, group, bg_color=WHITE, text_color=BLACK, anchor="center", command=None, visible_when=None):
        pygame.sprite.Sprite.__init__(self)
        StaticWidget.__init__(self, group, visible_when)
        self.cycles = cycles
        self.cycle = 0
        w, h = [5 + size + 5 for size in orbit_fonts[20].size(str(self.cycles[self.cycle]))]
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        #self.image.fill(bg_color)
        pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        self.text_color = text_color
        write(self.image, "topleft", self.cycles[self.cycle], orbit_fonts[20], self.text_color, 5, 5)
        self.rect = self.image.get_rect()
        self.command = command
        setattr(self.rect, anchor, pos)

    def process_event(self, event):
        if is_left_click(event):
            if is_drawable(self):
                if self.rect.collidepoint(g.mouse):
                    self.command()

    def overwrite(self, text):
        w, h = [5 + size + 5 for size in orbit_fonts[20].size(str(self.cycles[self.cycle]))]
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        write(self.image, "topleft", text, orbit_fonts[16], self.text_color, 5, 5)


class StaticOptionMenu(pygame.sprite.Sprite, StaticWidget):
    def __init__(self, options, default, pos, group, bg_color=WHITE, text_color=BLACK, anchor="center", visible_when=None):
        pygame.sprite.Sprite.__init__(self)
        StaticWidget.__init__(self, group, visible_when)
        self.options = options
        self.default = default
        w, h = orbit_fonts[20].size(str(default))
        self.image = SmartSurface((w + 40, h + 10), pygame.SRCALPHA)
        w, h = self.image.get_size()
        pygame.draw.rect(self.image, bg_color, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        write(self.image, "midleft", default, orbit_fonts[20], BLACK, 5, h / 2)
        self.image.cblit(pygame.transform.rotozoom(triangle(12), 180, 1), (w - 20, h / 2))
        self.og_img = self.image.copy()
        self.rects = []
        self.rect = self.image.get_rect()
        setattr(self.rect, anchor, pos)
        y = self.rect.y
        for option in options:
            self.rects.append(pygame.Rect(self.rect.x, y, w, h))
            y += h
        self.surf = pygame.Surface((w, h * (len(options) + 5)), pygame.SRCALPHA)
        pygame.draw.rect(self.surf, bg_color, (0, 0, *self.surf.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.surf, DARK_BROWN, (0, 0, *self.surf.get_size()), 2, 10, 10, 10, 10)
        self.opened = False

    def process_event(self, event):
        if is_left_click(event):
            if self.rect.collidepoint(g.mouse):
                self.opened = not self.opened

    def update(self):
        if self.opened:
            self.image = self.surf
        else:
            self.image = self.og_img
            if self.rect.collidepoint(g.mouse):
                self.image.set_alpha(150)
            else:
                self.image.set_alpha(255)


class MessageboxWorld(pygame.sprite.Sprite):
    def __init__(self, data):
        pygame.sprite.Sprite.__init__(self)
        # initialization
        self.data = data
        self.image = pygame.Surface((300, 200))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(Window.width / 2 - 150, Window.height / 2 - 100))
        self.text_height = orbit_fonts[20].size("J")[1]
        self.box_size = (self.rect.width / 2 - 15, self.text_height + 10)
        box = pygame.Surface(self.box_size)
        self.box_writing_pos = (box.get_width() / 2, box.get_height() / 2)
        # question mark
        write(self.image, "center", "?", orbit_fonts[30], BLACK, self.rect.width / 2, 60)
        # open world
        self.open_rect = box.get_rect(bottomleft=(self.rect.left + 20, self.rect.bottom - 20))
        box.fill(WHITE)
        write(box, "center", "Open", orbit_fonts[20], BLACK, *self.box_writing_pos)
        self.image.blit(box, (10, 150))
        # delete world
        self.delete_rect = box.get_rect(bottomright=(self.rect.right - 20, self.rect.bottom - 20))
        box.fill(WHITE)
        write(box, "center", "Delete", orbit_fonts[20], BLACK, *self.box_writing_pos)
        self.image.blit(box, (self.rect.width - self.delete_rect.width - 10, 150))
        # rename world
        self.rename_rect = box.get_rect(bottomright=(self.rect.right - 20, self.rect.bottom - 60))
        box.fill(WHITE)
        write(box, "center", "Rename", orbit_fonts[20], BLACK, *self.box_writing_pos)
        self.image.blit(box, (self.rect.width - self.rename_rect.width - 10, 110))
        # download world
        self.download_rect = box.get_rect(bottomleft=(self.rect.left + 20, self.rect.bottom - 60))
        box.fill(WHITE)
        write(box, "center", "Download", orbit_fonts[20], BLACK, *self.box_writing_pos)
        self.image.blit(box, (10, 110))
        # animation
        Thread(target=self.zoom, args=["in"]).start()

    def zoom(self, type_):
        og_img = self.image.copy()
        og_size = og_img.get_size()
        if type_ == "in":
            for i in range(20):
                size = [round((perc((i + 1) * 5, s))) for s in og_size]
                self.image = pygame.transform.scale(og_img, size)
                self.rect = self.image.get_rect()
                self.rect.center = (Window.width / 2, Window.height / 2)
                time.sleep(WOOSH_TIME)
        elif type_ == "out":
            for i in reversed(range(20)):
                size = [round(perc((i + 1) * 5, s)) for s in og_size]
                self.image = pygame.transform.scale(og_img, size)
                self.rect = self.image.get_rect()
                self.rect.center = (Window.width / 2, Window.height / 2)
                time.sleep(WOOSH_TIME)
            self.kill()

    def close(self, option):
        if option == "open":
            with open(path("Worlds", self.data["world"] + ".dat"), "rb") as f:
                # setup
                world_data = pickle.load(f)
                g.w = self.data["world_obj"]
                for entity in g.w.entities:
                    entity.images = [pygame.image.fromstring(image, entity.sizes[i], "RGBA") for i, image in enumerate(entity.images)]
                    entity.image = pygame.image.fromstring(entity.image, entity.sizes[int(entity.anim)], "RGBA")
                destroy_widgets()
                g.menu = False
                # player
                g.player = deepcopy(self.data["player_obj"])
                generate_world(world_data)
                init_world("existing")

        elif option == "delete":
            os.remove(path("Worlds", self.data["world"] + ".dat"))
            g.p.world_names.remove(self.data["world"])
            for button in all_home_world_world_buttons:
                if button.rect.y > self.data["pos"][1]:
                    button.rect.y -= g.worldbutton_pos_ydt
                    button.data["pos"][1] -= g.worldbutton_pos_ydt
                elif button.data == self.data:
                    button.kill()
            g.p.next_worldbutton_pos[1] -= g.worldbutton_pos_ydt

        elif option == "rename":
            def rename(ans_rename):
                if ans_rename is not None:
                    if ans_rename != "":
                        if ans_rename not in g.p.world_names:
                            try:
                                open(path("tempfiles", ans_rename + ".txt"), "w").close()
                                os.remove(path("tempfiles", ans_rename + ".txt"))
                            except Exception:
                                MessageboxError(Window.display, "World name is invalid.", **g.def_widget_kwargs)
                            else:
                                os.rename(path("Worlds", self.data["world"] + ".dat"), path("Worlds", ans_rename + ".dat"))
                                for button in all_home_world_world_buttons:
                                    if button.data["world"] == self.data["world"]:
                                        button.overwrite(ans_rename, True)
                                        button.data["world_obj"].name = ans_rename
                                        if toggle_sd.cycles[toggle_sd.cycle] == "data":
                                            update_button_data(button)
                                        break
                        else:
                            MessageboxError(Window.display, "A world with the same name already exists.", **g.def_widget_kwargs)
                    else:
                        MessageboxError(Window.display, "World name is invalid.", **g.def_widget_kwargs)

            Entry(Window.display, rename, "Rename world to:", pos=DPP)

        elif option == "download":
            with open(path("Worlds", self.data["world"] + ".dat"), "rb") as f:
                world_data = pickle.load(f)
            dir_ = tkinter.filedialog.asksaveasfilename()
            name = dir_.split(".")[0]
            with open(name + ".dat", "wb") as f:
                pickle.dump(world_data, f)

        self.kill()


# I N I T I A L I Z I N G  S P R I T E S -------------------------------------------------------------- #
g.player = Player()
visual = Visual()
hov = Hovering()

button_cnw = StaticButton("Create New World", (45, Window.height - 160), all_home_world_static_buttons, LIGHT_BROWN, anchor="topleft", size="world", command=new_world, visible_when=pw.is_worlds_worlds)
button_lw = StaticButton("Load World", (45, Window.height - 120), all_home_world_static_buttons, LIGHT_BROWN, anchor="topleft", size="world", command=pw.button_lw_command, visible_when=pw.is_worlds_worlds)
button_daw = StaticButton("Delete All Worlds", (45, Window.height - 80), all_home_world_static_buttons, LIGHT_BROWN, text_color=RED, anchor="topleft", size="world", command=pw.button_daw_command, visible_when=pw.is_worlds_worlds)
toggle_sd = StaticToggleButton(("name", "data"), (175, 131), all_home_world_static_buttons, LIGHT_BROWN, anchor="topleft", command=pw.toggle_sd_command, visible_when=pw.is_worlds_worlds)
button_c = StaticButton("Cursor", (35, 130), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", icon="cursor", command=cust_cursor, visible_when=pw.is_worlds_static)
button_kb = StaticButton("Key Bindings", (35, 170), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", visible_when=pw.is_worlds_static)
button_tp = StaticButton("Custom Textures", (35, 210), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", visible_when=pw.is_worlds_static)
button_l = StaticOptionMenu(g.common_languages, "EN", (35, 250), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", visible_when=pw.is_worlds_static)
button_s = StaticButton("Settings", (580, 150), all_home_sprites, GRAY, icon="settings", command=pw.set_home_stage_settings, visible_when=pw.is_home)
button_w = StaticButton("Worlds", (580, 190), all_home_sprites, GRAY, command=pw.set_home_stage_worlds, visible_when=pw.is_home)
# L O A D I N G  T H E  G A M E ----------------------------------------------------------------------- #
# load buttons
if os.path.getsize("buttons.dat") > 0:
    with open("buttons.dat", "rb") as f:
        attrs = pickle.load(f)
        for attr in attrs:
            group(WorldButton(attr, attr["pos"]), all_home_world_world_buttons)
# load variables
if os.path.getsize("variables.dat") > 0:
    with open("variables.dat", "rb") as f:
        g.p = pickle.load(f)


# M A I N  L O O P ------------------------------------------------------------------------------------ #
def main():
    # cursors
    set_cursor_when(pygame.SYSTEM_CURSOR_ARROW, lambda: g.crafting is not None)
    set_cursor_when(pygame.SYSTEM_CURSOR_CROSSHAIR, lambda: g.stage == "play")
    set_cursor_when(pygame.SYSTEM_CURSOR_ARROW, lambda: g.stage != "play")
    # lasts
    last_rain_partice = pgticks()
    last_snow_particle = pgticks()
    last_space = pgticks()
    # testing
    first_music = False
    music_count = None
    # counts
    g.stage = "home"
    # really start
    #atexit.register(MethodHandler.save, "quit")  # in case of a fatal bug / crash the game autosaves
    if platform.system() == "Windows":
        # windows signals
        pass
    # loop
    running = True
    print()
    print("Started in", round(time.time() - start, 2), "seconds")
    while running:
        # fps cap
        dt = g.clock.tick(g.fps_cap) / 1000 * 120

        # music
        if not pygame.mixer.music.get_busy():
            if first_music:
                music_count = pygame.time.get_ticks()
            else:
                music_count = float("-inf")
            if pgticks() - music_count >= 5000:
                pygame.mixer.music.load(path("Music", random.choice(os.listdir("Music"))))
                pygame.mixer.music.play()
                if first_music:
                    first_music = False

        # event loop
        for event in pygame.event.get():
            # 'x' button
            if event.type == pygame.QUIT:
                running = False
            
            # mechanical events
            if not g.events_locked:
                process_widget_events(event, g.mouse)
                
                if event.type == pygame.KEYDOWN:
                    if g.stage == "play":
                        if no_entries():
                            if event.key == g.keys["switch inventory"]:
                                if g.stage == "play":
                                    if not g.crafting:
                                        if g.player.main == "block":
                                            g.player.main = "tool"
                                        elif g.player.main == "tool":
                                            g.player.main = "block"

                            if g.crafting == "workbench":
                                if event.key == g.keys["add craft"]:
                                    if g.player.block is not None:
                                        if g.player.block in g.craftings:
                                            if g.player.amount - g.craftings[g.player.block] > 0:
                                                g.craftings[g.player.block] += 1 if g.mod != CTRL else g.player.amount - g.craftings[g.player.block]
                                                g.crafting_log.append(g.player.block)
                                        else:
                                            g.craftings[g.player.block] = 1 if g.mod != CTRL else g.player.amount
                                            g.crafting_log.append(g.player.block)

                                elif event.key == ENTER:
                                     if g.craftable is not None:
                                        if g.player.stats["xp"]["amount"] >= cinfo[craftable].get("xp", 0):
                                            if g.player.stats["energy"]["amount"] - cinfo[craftable].get("energy", 0) >= 0:
                                                for crafting in g.craftings:
                                                    g.player.use_up_inv(g.player.inventory.index(crafting), g.craftings[crafting])
                                                g.player.stats["energy"]["amount"] -= cinfo[craftable].get("energy", 0)
                                                if craftable in a.blocks:
                                                    if g.craftable in g.player.inventory:
                                                        g.player.inventory_amounts[g.player.inventory.index(g.craftable)] += g.craft_by_what
                                                    else:
                                                        index = findi(g.player.inventory, lambda x: x is None, g.player.blocki)
                                                        g.player.inventory[index] = g.craftable
                                                        g.player.inventory_amounts[index] = g.craft_by_what
                                                else:
                                                    index = findi(g.player.tools, lambda x: x is None, g.player.tooli)
                                                    g.player.tools[index] = g.craftable
                                                stop_crafting()

                                elif event.key == pygame.K_BACKSPACE:
                                    if g.crafting_log:
                                        g.craftings[g.crafting_log[-1]] -= 1
                                        if g.craftings[g.crafting_log[-1]] == 0:
                                            del g.craftings[g.crafting_log[-1]]
                                        del g.crafting_log[-1]

                            if event.key == pygame.K_c:
                                Entry(Window.display, user_command, "Enter your command:", pos=DPP)

                            elif event.key == pygame.K_p:
                                g.player.cust_username()

                            elif event.key == pygame.K_s:
                                if g.w.mode == "freestyle":
                                    if pgticks() - last_space <= 200:
                                        if g.player.moving_mode == "freestyle":
                                            g.player.moving_mode = "adventure"
                                        elif g.player.moving_mode == "adventure":
                                            g.player.moving_mode = "freestyle"
                                    else:
                                        for block in all_blocks:
                                            if is_in(block.name, functionable_blocks):
                                                if hov.rect.topleft == block.rect.topleft:
                                                    if not hov.faulty:
                                                        block.function()
                                                        break
                                    last_space = pgticks()

                            elif event.key == pygame.K_ESCAPE:
                                if not g.crafting:
                                    settings()
                                else:
                                    stop_crafting()

                            elif event.key == ENTER:
                                for messagebox in all_messageboxes:
                                    messagebox.close("open")

                            elif g.player.main == "block" and pygame.key.name(event.key) in ("1", "2", "3", "4", "5"):
                                g.player.indexes["block"] = int(pygame.key.name(event.key)) - 1
                            elif g.player.main == "tool" and pygame.key.name(event.key) in ("1", "2"):
                                g.player.indexes["tool"] = int(pygame.key.name(event.key)) - 1

                elif event.type == pygame.KEYUP:
                    if event.key == g.keys["p up"]:
                        if g.player.yvel < 0:
                            g.player.yvel /= 3

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        g.clicked_when = g.stage

                        for widget in iter_widgets():
                            if widget.visible_when is None:
                                if widget.disable_type != "static":
                                    if "static" not in widget.special_flags:
                                        if not widget.rect.collidepoint(g.mouse):
                                            faulty = True
                                            for friend in widget.friends:
                                                if friend.rect.collidepoint(g.mouse):
                                                    faulty = False
                                                    break
                                            else:
                                                faulty = True
                                            if faulty:
                                                if not widget.disable_type:
                                                    Thread(target=widget.zoom, args=["out destroy"]).start()
                                                elif not widget.disabled:
                                                    widget.disable()
                                        else:
                                            if isinstance(widget, MessageboxOkCancel):
                                                widget.okcancel(g.mouse)
                                            elif isinstance(widget, MessageboxError):
                                                widget.error(g.mouse)
                                            elif isinstance(widget, Checkbox):
                                                widget.toggle(g.mouse)

                        for messagebox in all_messageboxes:
                            if messagebox.open_rect.collidepoint(g.mouse):
                                messagebox.close("open")
                                break
                            elif messagebox.delete_rect.collidepoint(g.mouse):
                                messagebox.close("delete")
                                break
                            elif messagebox.rename_rect.collidepoint(g.mouse):
                                messagebox.close("rename")
                                break
                            elif messagebox.download_rect.collidepoint(g.mouse):
                                messagebox.close("download")
                                break
                            elif not messagebox.rect.collidepoint(g.mouse):
                                Thread(target=messagebox.zoom, args=["out"]).start()
                                break

                        if not all_messageboxes:
                            for button in all_home_world_world_buttons:
                                if button.rect.collidepoint(g.mouse):
                                    mb = MessageboxWorld(button.data)
                                    group(mb, all_messageboxes)
                                    break

                        if g.clicked_when == "play":
                            if not g.crafting_rect.collidepoint(g.mouse):
                                stop_crafting()

                            if not g.skin_menu_rect.collidepoint(g.mouse):
                                g.skin_menu = False
                                pw.skin_done.disable()
                            else:
                                for button in pw.change_skin_buttons:
                                    if point_in_mask(g.mouse, button["mask"], button["rect"]):
                                        g.skin_indexes[button["name"][2:]] += 1 if button["name"][0] == "n" else -1
                                        if g.skin_indexes[button["name"][2:]] > len(g.skins[button["name"][2:]]) - 1:
                                            g.skin_indexes[button["name"][2:]] = 0
                                        elif g.skin_indexes[button["name"][2:]] < 0:
                                            g.skin_indexes[button["name"][2:]] = len(g.skins[button["name"][2:]]) - 1

                            if g.player.main == "tool":
                                all_projectiles.add(Projectile(g.player.rect.center, (5, 5), g.mouse, 20))

                    elif event.button == 3:
                        if g.stage == "play":
                            for block in all_blocks:
                                if block.rect.collidepoint(g.mouse):
                                    if not hov.faulty:
                                        if bpure(block.name) == "workbench":
                                            g.crafting = "workbench"
                                            g.player.main = "block"
                                            break
                                        elif bpure(block.name) == "anvil":
                                            g.crafting = "anvil"
                                            g.player.main = "block"
                                            break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        g.first_affection = None
                        g.clicked_when = None
                        for block in all_blocks:
                            block.broken = 0
                        if g.stage == "play":
                            g.player.food_pie = g.player.def_food_pie.copy()

                elif event.type == pygame.MOUSEWHEEL:
                    if g.stage == "play":
                        if g.player.main == "block":
                            main = "block"
                            max_index = 5
                        elif g.player.main == "tool":
                            main = "tool"
                            max_index = 2

                        if event.y > 0:
                            if g.player.indexes[main] > 0:
                                g.player.indexes[main] -= 1
                            else:
                                g.player.indexes[main] = max_index - 1
                        elif event.y < 0:
                            if g.player.indexes[main] < max_index - 1:
                                g.player.indexes[main] += 1
                            else:
                                g.player.indexes[main] = 0

                elif event.type == pygame.MOUSEMOTION:
                    for block in all_blocks:
                        block.check_not_hovering()

                if g.stage == "home":
                    for spr in all_home_sprites.sprites() + all_home_world_world_buttons.sprites() + all_home_world_static_buttons.sprites() + all_home_settings_buttons.sprites():
                        with suppress(AttributeError, TypeError):
                            spr.process_event(event)

        # play loop
        if g.stage == "play":
            set_volume(pw.volume.value / 100)
            
            if not g.menu:
                if g.mouses[0]:
                    if g.clicked_when == "play":
                        if not g.menu:
                            if g.player.main == "tool":
                                if g.player.tool is not None:
                                    if g.player.direc == "left":
                                        visual.angle += 3
                                        if visual.angle > 90:
                                            visual.angle = -90
                                    elif g.player.direc == "right":
                                        visual.angle -= 3
                                        if visual.angle < -90:
                                            visual.angle = 90

                            for block in all_blocks:
                                if g.player.main == "block":
                                    if hov.rect.topleft == block.rect.topleft:
                                        # check whether the block is a food
                                        if g.player.amount is not None and is_in(g.player.block, finfo):
                                            if is_eatable(g.player.block):
                                                if g.player.amount > 0:
                                                    g.player.eat()
                                        else:
                                            # ok then, the block is not a food
                                            if g.w.mode == "adventure":
                                                stmt = not hov.faulty
                                            elif g.w.mode == "freestyle":
                                                stmt = True
                                            if block.name == "air" and stmt:
                                                if g.first_affection is None:
                                                    g.first_affection = "place"
                                                if g.first_affection == "place":
                                                    if not block.rect.colliderect(g.player.rect) if g.str_mod != "_bg" else True:
                                                        if g.player.block is not None:
                                                            block.name = g.player.block + g.str_mod
                                                            if g.w.mode == "adventure":
                                                                g.player.use_up_inv(g.player.itemi)
                                                            block.image = a.blocks[non_bg(block.name)].copy()
                                                            if "_bg" in block.name:
                                                                block.image = img_mult(block.image, 0.8)
                                            elif stmt:
                                                if g.first_affection is None:
                                                    g.first_affection = "break"
                                                if g.first_affection == "break":
                                                    if g.w.mode == "adventure":
                                                        if non_bg(block.name) not in unbreakable_blocks:
                                                            block.try_breaking()
                                                    elif g.w.mode == "freestyle":
                                                        block.name = "air"
                                                        block.image = a.blocks["air"].copy()
                                                        update_block_states()
                                            else:
                                                block.broken = 0

                                elif g.player.main == "tool":
                                    if tpure(g.player.tool) in tinfo:
                                        if is_in(block.name, tool_blocks):
                                            if hasattr(visual, "rect"):
                                                if block.rect.colliderect(visual.rect):
                                                    block.try_breaking("tool")
                                                    break

            # filling
            Window.display.fill(g.w.dnc_colors[int(g.w.dnc_index)])

            # menu filling
            if g.menu or g.skin_menu:
                Window.display.blit(g.menu_surf, (0, 0))

            # day-night cycle
            g.w.dnc_index = g.w.dnc_direc(g.w.dnc_index, perc(dt * 100, g.w.dnc_vel))
            if g.w.dnc_index >= len(g.w.dnc_colors) - 1:
                g.w.dnc_index = len(g.w.dnc_colors) - 1
                g.w.dnc_direc = op.sub
            elif g.w.dnc_index <= 0:
                g.w.dnc_index = 0
                g.w.dnc_direc = op.add
                g.w.set_dn_colors()
                if g.w.hound_round_chance > 1:
                    g.w.hound_round_chance -= 1

            # right bar surf
            if any([widget.checked for widget in pw.right_bar_widgets if isinstance(widget, Checkbox)]):
                pass
                #Window.display.blit(right_bar_surf, (Window.width - right_bar_surf.get_width(), 0))

            # blocks
            for block in all_blocks:
                if block.name != "air":
                    block.update()
                    if g.w.show_hitboxes:
                        pygame.draw.rect(Window.display, GREEN, block.rect, 1)
                        pygame.draw.rect(Window.display, GREEN, g.player.rect, 1)

            # entities
            for entity in g.w.entities:
                entity.update()

            # death sreen
            if g.player.dead:
                Window.display.blit(death_screen, (0, 0))

            # particles from the engine
            draw_and_update_particles()
            
            # projectiles
            all_projectiles.function()

            # foregorund sprites (so also the player)
            g.player.function()
            all_foreground_sprites.draw(Window.display)
            all_foreground_sprites.update()

            # visual tool and block
            visual.function()
            
            # mobs
            all_mobs.function()

            # hovering
            if not g.menu:
                hov.function()

            for block in all_blocks:
                if int(block.broken) > 0:
                    Window.display.blit(breaking_sprs[int(block.broken) - 1], (block.rect.x, block.rect.y))

            # P L A Y  B L I T S -------------------------------------------------------------------------- #
            # player username
            write(Window.display, "center", g.player.username, orbit_fonts[12], BLACK, g.player.rect.centerx, g.player.rect.centery - 30)

            # workbench image
            if g.crafting == "workbench":
                Window.display.blit(workbench_img, g.crafting_rect)

            # workbench blocks
            x = g.crafting_rect.x + 30 / 2 + 25
            y = g.crafting_rect.y + 30 + 30 / 2 + 10
            sy = y
            xo = 30 + 5
            yo = 30 + 10
            for crafting_block in g.craftings:
                # crafting material
                pygame.draw.aaline(Window.display, BLACK, (x + 30 / 2, y), crafting_center)
                Window.display.cblit(a.blocks[crafting_block], (x, y))
                write(Window.display, "midright", g.craftings[crafting_block], orbit_fonts[15], BLACK, x - 20, y)
                y += yo
                if (y - sy) / yo == 5:
                    y = sy
                    x += xo
                # recieving material
                enough = 0
                g.craft_by_what = []
                try:
                    for craftable in cinfo:
                        #if sorted(cinfo[craftable]["recipe"]) == sorted(g.craftings):
                        #if cinfo[craftable]["recipe"] == g.craftings:
                        truthy = True
                        for crafting_block in g.craftings:
                            try:
                                if cinfo[craftable]["recipe"][crafting_block] > g.craftings[crafting_block]:
                                    truthy = False
                                    break
                            except KeyError:
                                truthy = False
                                break
                        if truthy:
                            if g.player.stats["energy"]["amount"] - cinfo[craftable]["energy"] >= 0:
                                for recipe_block in cinfo[craftable]["recipe"]:
                                    if g.craftings[recipe_block] >= cinfo[craftable]["recipe"][recipe_block]:
                                        enough += 1
                                        g.craft_by_what.append(g.craftings[recipe_block] // cinfo[craftable]["recipe"][recipe_block] * cinfo[craftable].get("amount", 1))
                                    if enough == len(cinfo[craftable]["recipe"]):
                                        g.craftable = craftable
                                        raise BreakAllLoops
                                    else:
                                        g.craftable = None
                except BreakAllLoops:
                    pygame.draw.aaline(Window.display, BLACK, crafting_center, (crafting_center[0] + g.crafting_rect.width / 4, crafting_center[1]))
                    if craftable in a.blocks:
                        Window.display.cblit(a.blocks[craftable], (crafting_center[0] + g.crafting_rect.width / 4, crafting_center[1]))
                    elif craftable in a.tools:
                        blit_center(Window.display, a.tools[craftable], (crafting_center[0] + g.crafting_rect.width / 4, crafting_center[1]))
                    g.craft_by_what = min(g.craft_by_what)
                    write(Window.display, "midbottom", g.craft_by_what, orbit_fonts[15], BLACK, crafting_center[0] + g.crafting_rect.width / 4, crafting_center[1] + 40)

            # player item
            if g.crafting == "workbench":
                Window.display.cblit(workbench_icon, crafting_center)

            if g.player.main == "block" and g.player.block is not None:
                if g.player.block not in oinfo:
                    item = bpure(g.player.block).upper()
                else:
                    item = oinfo[g.player.block]["cform"]
            elif g.player.main == "tool" and g.player.tool is not None:
                item = g.player.tool.replace("_", " ").upper()
            else:
                item = None
            if item is not None:
                write(Window.display, "center", item, orbit_fonts[15], BLACK, Window.width / 2 + 20, 90)
            if g.mod == 1:
                if no_entries():
                    if g.player.main == "block" and g.player.block:
                        write(Window.display, "center", "(BACKGROUND)", orbit_fonts[15], BLACK, Window.width / 2 + 30, 105)
            write(Window.display, "center", "| " + str(g.w.screen + 1) + " |", orbit_fonts[20], BLACK, Window.width - 25, 20)

            # H O T B A R --------------------------------------------------------------------------------- #
            Window.display.cblit(tool_holders_img, (Window.width / 2 - 96 - 35, 20), "midtop")
            Window.display.cblit(inventory_img, (Window.width / 2 + 20, 20), "midtop")
            Window.display.cblit(pouch_img, (Window.width / 2 + 20 + 96 + 40, 20), "midtop")
            
            # selected tool name
            x = 258
            y = 38
            for index, tool in enumerate(g.player.tools):
                if tool is not None:
                    Window.display.cblit(a.tools[tool], (x, y))
                if tpure(tool) in tinfo:
                    th = g.player.tool_healths[index]
                    if th < 100:
                        pygame.draw.rect(Window.hotbar, g.health_bar_colors[int(th)], (x, 40, perc(th, 30), y))
                elif tpure(tool) in g.w.gun_names:
                    pass
                # border if selected
                if g.player.main == "tool":
                    if index == g.player.tooli:
                        Window.display.cblit(square_border_img, (x, y))
                x += 33
                
            # selected block name
            x = 359
            y = 38
            for index, block in enumerate(g.player.inventory):
                if block is not None:
                    Window.display.cblit(a.blocks[block], (x, y))
                    write(Window.display, "center", inf(g.player.inventory_amounts[index]), orbit_fonts[15], BLACK, x, y + 25)
                # border if selected
                if g.player.main == "block":
                    if index == g.player.blocki:
                        Window.display.cblit(square_border_img, (x, y))
                x += 33
            
            # pouch icon
            Window.display.cblit(pouch_icon, (546 + 15, y))
            write(Window.display, "center", g.player.pouch, orbit_fonts[15], BLACK, 546 + 15, y + 25)

            # P L A Y E R  B A R S ------------------------------------------------------------------------ #
            # applyping regeneration
            if g.w.mode == "adventure":
                if g.player.stats["lives"]["amount"] + 1 <= 100:
                    if pgticks() - g.player.stats["lives"]["last_regen"] >= g.player.stats["lives"]["regen_time"]:
                        g.player.stats["lives"]["amount"] += 1
                        g.player.stats["lives"]["regen_time"] -= 0.2
                        g.player.stats["lives"]["last_regen"] = pgticks()

                # g.player food chart
                if "image" in g.player.food_pie and "rect" in g.player.food_pie:
                    g.player.food_pie["rect"].midbottom = (g.player.rect.centerx, g.player.rect.top - 25)
                    Window.display.blit(g.player.food_pie["image"], g.player.food_pie["rect"])

        # home loop
        elif g.stage == "home":
            set_volume(0)
                
            Window.display.fill(DARK_BROWN)
            write(Window.display, "center", "Blockingdom", orbit_fonts[50], BLACK, Window.width // 2, 58)
            Window.display.blit(frame_img, (0, 0))
            Window.display.blit(g.home_bg_img, (0, 120))

            all_home_sprites.draw(Window.display)
            all_home_sprites.update()

            if g.home_stage == "worlds":
                write(Window.display, "topleft", "Worlds:", orbit_fonts[30], BLACK, 35, 125)
                all_home_world_world_buttons.draw(Window.display)
                all_home_world_world_buttons.update()
                all_home_world_static_buttons.draw(Window.display)
                all_home_world_static_buttons.update()

            elif g.home_stage == "settings":
                all_home_settings_buttons.draw(Window.display)
                all_home_settings_buttons.update()

            all_messageboxes.draw(Window.display)
            all_messageboxes.update()
            
            # generating world loading bar
            if g.generating_world:
                pygame.draw.rect(Window.display, BLACK, (Window.width / 2 - 100, Window.height / 2 - 15, 200, 30), 3)
                pygame.draw.rect(Window.display, LIGHT_GREEN, (Window.width / 2 - 98, Window.height / 2 - 13, g.generating_world_perc * 2 - 4, 26))
            
        # skin menu filling
        if g.skin_menu:
            # backkground (filling)
            Window.display.cblit(skin_menu_surf, (Window.width / 2, Window.height / 2))
            Window.display.cblit(g.player_model, (Window.width / 2, Window.height / 2))
            # skins (showcase)
            for bt in g.skins:
                if g.skin_data(bt)["sprs"]:
                    try:
                        g.skin_anims[bt] += g.skin_anim_speed
                        skin_img = g.skin_data(bt)["sprs"][int(g.skin_anims[bt])]
                        skin_pos = g.skin_data(bt)["pos"]
                        Window.display.blit(skin_img, (g.player_model_pos[0] + skin_pos[0] * g.skin_fppp, g.player_model_pos[1] + skin_pos[1] * g.skin_fppp))
                    except IndexError:
                        g.skin_anims[bt] = 0
                        g.skin_anims[bt] += g.skin_anim_speed
                        skin_img = g.skin_data(bt)["sprs"][int(g.skin_anims[bt])]
                        skin_pos = g.skin_data(bt)["pos"]
                        Window.display.blit(skin_img, (g.player_model_pos[0] + skin_pos[0] * g.skin_fppp, g.player_model_pos[1] + skin_pos[1] * g.skin_fppp))

            # buttons (arrows)
            for button in pw.change_skin_buttons:
                Window.display.cblit(button["surf"], button["rect"].center)
            # lines (for clarity)

        # updating the widgets
        updating_buttons = [button for button in iter_buttons() if not button.disabled]
        updating_worldbuttons = [worldbutton for worldbutton in all_home_world_world_buttons if is_drawable(worldbutton)]
        updating_settingsbuttons = [settingsbutton for settingsbutton in all_home_settings_buttons if is_drawable(settingsbutton) and not isinstance(settingsbutton, StaticOptionMenu)]
        updating_static_buttons = [static_button for static_button in all_home_world_static_buttons if is_drawable(static_button)]
        update_button_behavior(updating_worldbuttons + updating_buttons + updating_settingsbuttons + updating_static_buttons + [button_s, button_w])
        draw_and_update_widgets()

        # screen shake (offsetting the render)
        if g.screen_shake > 0:
            g.screen_shake -= 1
            g.render_offset = (rand(-g.s_render_offset, g.s_render_offset), rand(-g.s_render_offset, g.s_render_offset))
        else:
            g.render_offset = (0, 0)

        # blitting the Window.display surface to the main window
        Window.window.blit(Window.display, g.render_offset)

        # refreshing the window
        pygame.display.update()

    MethodHandler.save("quit")


if __name__ == "__main__":
    #import cProfile; cProfile.run("main()")
    main()
