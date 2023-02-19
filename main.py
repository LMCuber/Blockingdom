# I M P O R T S --------------------------------------------------------------------------------------- #
import atexit
import string
import time
import pickle
import json
import threading
import tkinter.filedialog
from copy import deepcopy
from colorsys import rgb_to_hls, hls_to_rgb
import fantasynames as fnames
import pyengine.pgbasics
from pyengine.pgwidgets import *
from pyengine.pgaudio import *
from settings import *
from prim_data import *
from sounds import *
from world_generation import *


# N O R M A L  F U N C T I O N S ---------------------------------------------------------------------- #
def player_command(command):
    abs_args = command.split()
    args = SmartList(abs_args[1:])
    try:
        if command.startswith("tp "):
            x, y = args[0], args[1]
            pos = int(x), int(y)
            g.player.rect.center = pos
        elif command.startswith("give "):
            args = SmartList(int(arg) if arg.isdigit() else arg for arg in args)
            if args[0] in g.w.blocks:
                block = args[0]
                amount = args.get(1, 1)
                g.player.new_block(block, amount)
            elif args[0] in g.w.tools:
                tool = args[0]
                g.player.new_tool(tool)
            else:
                raise Exception
        elif command.startswith("recipe "):
            if args[0] in cinfo:
                MessageboxError(Window.display, str(cinfo[args[0]]["recipe"]), **g.def_widget_kwargs)
            else:
                MessageboxError(Window.display, "Invalid recipable block name", **g.def_widget_kwargs)
        elif command.startswith("empty"):
            try:
                g.player.inventory[args[0]] = None
                g.player.inventory_amounts[args[0]] = None
            except IndexError:
                g.player.inventory[g.player.blocki] = None
                g.player.inventory_amounts[g.player.blocki] = None
        elif command:
            raise Exception
    except Exception:
        MessageboxError(Window.display, "Invalid or unusable command", **g.def_widget_kwargs)


def mousebuttondown_event():
    g.clicked_when = g.stage
    if g.stage == "play":
        if g.player.main == "tool":
            if "_sword" in g.player.tool and visual.to_swing <= 0:
                if orb_names["purple"] in g.player.tool:
                    visual.to_swing = float("inf")
                    visual.sword_log = [sl for sl in visual.sword_log for _ in range(2)]
                else:
                    visual.to_swing = 220
                visual.angle = -90 if g.mouse[0] < g.player.rect.centerx else 90
            elif bpure(g.player.tool) == "bat":
                visual.anticipate = True
                visual.anim = 1
            visual.ds_last = perf_counter()

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
                                DThread(target=widget.zoom, args=["out destroy"]).start()
                            elif not widget.disabled:
                                widget.disable()

    if g.stage == "home":
        if g.process_messageboxworld:
            for messagebox in all_messageboxes:
                for name, rect in messagebox.close_rects.items():
                    if rect.collidepoint(g.mouse):
                        messagebox.close(name)
                        break
                else:
                    if not messagebox.rect.collidepoint(g.mouse):
                        DThread(target=messagebox.zoom, args=["out"]).start()
                        break

        if g.home_stage == "worlds":
            if not all_messageboxes:
                for button in all_home_world_world_buttons:
                    if button.rect.collidepoint(g.mouse):
                        mb = MessageboxWorld(button.data)
                        group(mb, all_messageboxes)
                        break

    if g.clicked_when == "play":
        if g.midblit is not None:
            if g.midblit == "chest":
                if not chest_rect.collidepoint(g.mouse):
                    stop_midblit()
                else:
                    for rect in chest_rects:
                        if rect.collidepoint(g.mouse):
                            g.chest_pos = [p - 3 for p in rect.topleft]
            elif not crafting_rect.collidepoint(g.mouse):
                    stop_midblit()

        if not g.skin_menu_rect.collidepoint(g.mouse):
            g.skin_menu = False
            for button in pw.skin_buttons:
                button.disable()
        else:
            for button in pw.change_skin_buttons:
                if point_in_mask(g.mouse, button["mask"], button["rect"]):
                    g.skin_indexes[button["name"][2:]] += 1 if button["name"][0] == "n" else -1
                    if g.skin_indexes[button["name"][2:]] > len(g.skins[button["name"][2:]]) - 1:
                        g.skin_indexes[button["name"][2:]] = 0
                    elif g.skin_indexes[button["name"][2:]] < 0:
                        g.skin_indexes[button["name"][2:]] = len(g.skins[button["name"][2:]]) - 1

        if g.player.main == "tool" and is_gun(g.player.tool):
            all_projectiles.add(Projectile(g.player.rect.center, g.mouse, (5, 5), 100, 15, traits=["break"], track_path=g.parabola, tangent=g.tangent))

        try:
            bag_mask.get_at((g.mouse[0] - bag_rect.x, g.mouse[1] - bag_rect.y))
        except IndexError:
            pass
        else:
            g.show_extended_inventory = True


def get_gun_info(name, part):
    ret = ginfo[part][g.mb.gun_attrs[name][part].split("_")[0]]
    return ret


def shake_screen(shake_offset, shake_length):
    g.s_render_offset = shake_offset
    g.screen_shake = shake_length


def is_audio(file_name):
    return file_name.endswith(".mp3") or file_name.endswith(".wav") or file_name.endswith(".ogg")


def get_rand_track(p):
    while True:
        track = choice(os.listdir(p))
        if is_audio(track):
            break
    else:
        raise RuntimeError(f"No audio files found in given directory {p}")
    return path(p, track)


def next_ambient():
    pygame.mixer.music.load(get_rand_track(path("Audio", "Music", "Ambient")))
    try:
        pygame.mixer.music.play(start=rand(0, audio_length(music_path)))
    except wave.Error:
        pygame.mixer.music.play()
    g.last_ambient = music_name


def ipure(str_):
    if non_bg(str_) in g.w.blocks:
        return bpure(str_)
    elif tpure(str_) in tinfo:
        return tpure(str_)


def show_added(item, pre="Added", post=""):
    group(SlidePopup(f"{pre} {bshow(item)} {post}"), all_particles)


def set_entity_screen_attrs(entity):
    """
    try:
        g.w.get_data[entity.screen]
    except IndexError:
        return
    else:
        rects = []
        if not is_drawable(entity):
            iter_ = g.w.get_data[entity.screen]
        else:
            iter_ = [block.name for block in all_blocks]
        for blockindex, blockname in enumerate(iter_):
            if blockname not in walk_through_blocks and not is_bg(blockname):
                if not is_drawable(entity):
                    stmt = entity.layer * L < blockindex < entity.layer * L * 2
                else:
                    stmt = True
                if stmt:
                    horindex = blockindex % HL
                    verindex = (blockindex % L) // HL
                    _x, _y = horindex * 30, verindex * 30
                    _rect = pygame.Rect(_x, _y, 30, 30)
                    rects.append(_rect)
        entity.screen_rects = rects
    """


def externally_update_entities():
    """
    for entity in g.w.entities:
        set_entity_screen_attrs(entity)
        update_entity(entity)
    """


def set_entity_screen_attrs(entity):
    try:
        g.w.get_data[entity.screen]
    except IndexError:
        entity.screen_rects = []
    else:
        rects = []
        data = g.w.get_data[entity.screen][entity.layer * L: entity.layer * 2 * L]
        for blockindex, blockname in enumerate(data):
            horindex = blockindex % HL
            verindex = blockindex // HL
            rect = pygame.Rect(horindex * BS, verindex * BS, BS, BS)
            rects.append(rect)
        entity.screen_rects = rects


def update_entity(entity):
    # settings screen rects if necessary
    if not hasattr(entity, "screen_rects"):
        set_entity_screen_attrs(entity)

    # main
    if entity.screen_rects:
        # off screen?
        if entity.left >= Window.width:
            entity.right = 0
            entity.screen += 1

        if is_drawable(entity):
            tb_taken = 0
            if "mob" in entity.traits:
                # displaying health
                if 0 < entity.hp < entity.max_hp:
                    _w, _h = 30, 7
                    _tl = (entity.centerx - _w / 2, entity.y - 10)
                    pygame.draw.rect(Window.display, entity.bar_rgb[int(entity.hp / entity.max_hp * 100)], (*_tl, entity.hp / entity.max_hp * 100 / (100 / _w), _h))
                    pygame.draw.rect(Window.display, BLACK, (*_tl, _w, _h), 1)
                elif entity.hp <= 0:
                    entity.die()

                # damaging
                if not entity.taking_damage and g.player.main == "tool" and "_sword" in g.player.tool and visual.to_swing > 0 and entity.rect.colliderect(visual.rect):
                    if hasattr(visual, "rect"):
                        offset = (int(visual.rect.x - entity.x), int(visual.rect.y - entity.y))
                        if entity.mask.overlap(visual.mask, offset):
                            tb_taken = 5
            # taking damage
            if tb_taken > 0:
                entity.last_took_damage = ticks()
                entity.take_damage(tb_taken)
                entity.flinch(-2)

        # snow rects
        if pw.show_internals:
            pygame.draw.rect(Window.display, RED, entity.rect, 1)
            write(Window.display, "center", entity.screen + 1, orbit_fonts[15], GREEN, *entity.center)


def is_smither(tool):
    return tool.split("_")[1] == "hammer"


def tool_type(tool):
    return tool.split("_")[0].removesuffix("_en")


def non_bg(name):
    return name.replace("_bg", "")


def non_jt(name):
    return name.replace("_jt", "")


def is_jt(name):
    return "_jt" in name


def non_ck(name):
    return name.replace("_ck", "")


def non_wt(name):
    return non_jt(non_bg(name))


def non_en(name):
    return name.replace("_en", "")


def is_en(name):
    return "_en" in name


def is_ck(name):
    return "_ck" in name


def get_ending(name):
    ending = ""
    if is_bg(name):
        ending += "_bg"
    return ending


def toggle_main():
    if g.player.main == "block":
        g.player.main = "tool"
    elif g.player.main == "tool":
        g.player.main = "block"


def custom_language(lang):
    g.w.language = lang


def all_main_widgets():
    return all_home_sprites.sprites() + all_home_world_world_buttons.sprites() + all_home_world_static_buttons.sprites() + all_home_settings_buttons.sprites()


def is_gun(name):
    return name.removeprefix("enchanted_").split("_")[0] not in oinfo if name is not None else False


def is_gun_craftable():
    return all({k: v for k, v in g.mb.gun_parts.items() if k not in g.extra_gun_parts}.values())


def custom_gun(name):
    if name not in g.w.blocks:
        g.w.tools[name] = SmartSurface.from_surface(g.mb.gun_img.copy())
        g.player.empty_tool = name
        g.mb.gun_attrs[name] = g.mb.gun_parts
        g.player.tool_ammo = get_gun_info(name, "magazine")["size"]
        g.midblit = None
    else:
        MessageboxError(Window.display, "Name collides")


def gwfromperc(amount):
    g.loading_world_perc = amount


def update_block_states():
    for block in all_blocks:
        block.update_state()


def is_clickable(block):
    if g.stage == "freestyle":
        return True
    elif g.stage == "adventure":
        pass


def stop_midblit(args=""):
    g.midblit = None
    g.cannot_place_block = True
    args = args.split("/")
    if "workbench" in args or not args:
        g.mb.craftings = {}


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


def apply(elm, seq, default):
    if is_in(elm, seq):
        return seq[ipure(elm)]
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
        for block in tinfo[gtool(tool)]["blocks"]:
            if block == bpure(name):
                amount = tinfo[gtool(tool)]["blocks"][block] * 1
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
    mb = convert_size(os.path.getsize(path(".game_data", "worlds", button.data["world"] + ".dat")))
    date = button.data["date"]
    button.overwrite(f"{name} | {mb} | {date}")


def tool_type(tool):
    return tool.split("_")[0].removeprefix("enchanted_")


def is_bg(name):
    return "_bg" in name

def utilize_blocks():
    def utilize():
        for block in g.player.reverse_blocks:
            block.utilize()
            block.broken = 0

    if pw.generation_mode.option == "Instant":
        utilize()
    elif pw.generation_mode.option == "Generative":
        Thread(target=utilize).start()


def new_world(worldcode=None):
    def init_world_data(wn):
        _glob.world_name = wn
        start_generating()

    def destroy_ewn():
        ewn.destroy()

    class Global:
        def __init__(self):
            self.world_name = None
            self.world_code = worldcode[:] if worldcode is not None else None

    _glob = Global()

    def create():
        wn = _glob.world_name
        g.set_loading_world(True)
        game_mode = "adventure"  # switching game mode
        if wn is not None:
            if wn not in g.p.world_names:
                g.w.screen = 0
                if _glob.world_code is None:
                    try:
                        open(path(".game_data", "tempfiles", wn + ".txt"), "w").close()
                        os.remove(path(".game_data", "tempfiles", wn + ".txt"))
                    except InvalidFilenameError:
                        MessageboxError(Window.display, "Invalid world name", **g.def_widget_kwargs)
                    else:
                        biome = choice(list(bio.blocks.keys()))
                        if not wn:
                            wn = f"New_World_{g.p.new_world_count}"
                            g.p.new_world_count += 1
                        g.w = World()
                        generate_world(biome="industry")
                        group(WorldButton({"world": wn, "mode": game_mode, "date": date.today().strftime("%m/%d/%Y"), "pos": c1dl(g.p.next_worldbutton_pos)}), all_home_world_world_buttons)
                        g.p.next_worldbutton_pos[1] += g.worldbutton_pos_ydt
                        g.w.mode = game_mode
                        destroy_widgets()
                        g.menu = False
                        g.w.name = wn
                        g.p.world_names.append(wn)
                        init_world("new")
                else:
                    generate_world(_glob.world_code)
            else:
                MessageboxError(Window.display, "A world with the same name already exists.", **g.def_widget_kwargs)
                g.set_loading_world(False)
        destroy_ewn()

    _cr_world_dt = 100 / len(inspect.getsourcelines(create)[0])
    #create = scatter(create, f"g.loading_world_perc += {_cr_world_dt}", globals(), locals())

    def start_generating():
        t = Thread(target=create)
        t.setDaemon(True)
        t.start()

    if g.p.next_worldbutton_pos[1] < g.max_worldbutton_pos[1]:
        ewn = Entry(Window.display, "Enter world name:", init_world_data, **g.def_entry_kwargs)
    else:
        MessageboxError(Window.display, "You have too many worlds. Delete a world to create another one.", **g.def_widget_kwargs)
        g.set_loading_world(False)


def settings():
    if Platform.os == "windows":
        g.home_bg_img = g.bglize(Window.display.copy())
    elif Platform.os == "darwin":
        g.home_bg_img = pygame.Surface(Window.size, pygame.SRCALPHA).convert_alpha()
        g.home_bg_img.blit(Window.display.copy(), (0, 0))
        g.home_bg_img = pygame.transform.scale2x(g.home_bg_img)
    g.menu = True
    for widget in pw.death_screen_widgets:
        widget.disable()
    for widget in pw.iter_menu_widgets:
        widget.enable()


def group(spr, grp):
    try:
        grp.add(spr)
    except AttributeError:
        grp.append(spr)
    if grp in (all_particles,):
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
            for file_ in os.listdir(path(".game_data", "worlds")):
                os.remove(path(".game_data", "worlds", file_))
                open(path(".game_data", "variables.dat"), "w").close()
                open(path(".game_data", "worldbuttons.dat"), "w").close()
            empty_group(all_home_world_world_buttons)
            g.p.world_names.clear()
            g.w.name = None
            g.p.next_worldbutton_pos = g.p.starting_worldbutton_pos[:]
            g.p.new_world_count = 1

        MessageboxOkCancel(Window.display, "Delete all worlds? This cannot be undone.", delete, **g.def_widget_kwargs)
    else:
        MessageboxError(Window.display, "You have no worlds to delete.", **g.def_widget_kwargs)


def cr_block(name, screen=-1, index=None):
    g.w.get_data[screen].insert(index if index is not None else len(g.w.get_data[screen]), name)


def init_world(type_):
    # player inventory and stats
    if type_ == "new":
        g.player = Player()
        if g.w.mode == "adventure":
            g.player.inventory = ["gun-crafter", "prototype_body", "prototype_barrel", "prototype_magazine", "prototype_grip"]
            g.player.inventory_amounts = [10, 10, 10, 10, 10]
            g.player.stats = {
                "lives": {"amount": rand(10, 100), "color": RED, "pos": (32, 20), "last_regen": ticks(), "regen_time": def_regen_time, "icon": "lives"},
                "hunger": {"amount": rand(10, 100), "color": ORANGE, "pos": (32, 40), "icon": "hunger"},
                "thirst": {"amount": rand(10, 100), "color": WATER_BLUE, "pos": (32, 60), "icon": "thirst"},
                "energy": {"amount": rand(10, 100), "color": YELLOW, "pos": (32, 80), "icon": "energy"},
                "oxygen": {"amount": 100, "color": SMOKE_BLUE, "pos": (32, 100), "icon": "o2"},
                "xp": {"amount": 0, "color": LIGHT_GREEN, "pos": (32, 120), "icon": "xp"},
            }
        elif g.w.mode == "freestyle":
            g.player.inventory = ["anvil", "bush", "dynamite", "command-block", "workbench"]
            g.player.inventory_amounts = [float("inf")] * 5
        g.player.tools = ["diamond_sword", "iron_axe"]
        g.player.tool_healths = [100, 100]
        g.player.tool_ammos = [None, None]
        g.player.indexes = {"tool": 0, "block": 0}
    elif type_ == "existing":
        g.player.stats["lives"]["regen_time"] = def_regen_time
        g.player.stats["lives"]["last_regen"] = ticks()

    # dynamic surfaces
    g.bars_bg = pygame.Surface((200, len(g.player.stats.keys()) * (16 + 7))); g.bars_bg.fill(GRAY); g.bars_bg.set_alpha(150)
    # music
    pw.next_piece_command()
    # Go!
    g.stage = "play"
    g.set_loading_world(False)


def generate_world(worldcode=None, biome=None, screens=5):
    # world data (non-gui)
    if worldcode is None:
        g.w.data.clear()
        g.w.magic_data.clear()
        g.w.metadata.clear()
        g.w.biomes.clear()
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
    # mobs gain ground
    # for entity in g.w.entities:
    #     if "mob" in entity.traits:
    #         set_entity_screen_attrs(entity)
    #         while any(entity.rect.colliderect(screen_rect) for screen_rect in entity.screen_rects):
    #             entity.y -= 1


def generate_screen(biome=None):
    g.w.data.append(SmartList())
    g.w.magic_data.append(SmartList())
    g.w.metadata.append([{} for _ in range(3 * L)])
    screen = -1
    layer = 1
    biome_name = choice(list(bio.blocks.keys())) if biome is None else biome
    g.w.biomes.append(biome_name)
    biome_pack = bio.blocks[g.w.biomes[-1]] + ("stone",)
    # ground
    for _ in range(L):
        cr_block("air")
    # noise generation
    noise = g.noise.linear(bio.heights.get(biome, 4), HL, bio.flatnesses.get(biome, 0))
    # biome (ground)
    for blockindex, blockname in enumerate(g.w.get_data[screen]):
        noise_num = blockindex % HL
        g.w.metadata[screen][layer * L + blockindex]["height"] = noise[noise_num]
        if 512 < blockindex < 540:
            noise_index = blockindex
            noise_height = noise[noise_num]
            if noise_height % 2 == 1:
                # uneven height
                ground_height = (noise_height - 1) // 2
                stone_height = (noise_height - 1) // 2
            else:
                # even height
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
            #ground_height, stone_height = abs(ground_height), abs(stone_height)
            # generate ground and stone
            for _ in range(stone_height):
                g.w.get_data[screen][noise_index] = chanced(biome_pack[2])
                noise_index -= HL
            for _ in range(ground_height):
                g.w.get_data[screen][noise_index] = biome_pack[1]
                noise_index -= HL
            g.w.get_data[screen][noise_index] = biome_pack[0]
    for blockindex, blockname in enumerate(g.w.get_data[screen]):
        try:
            entities = world_modifications(g.w.data, g.w.metadata, screen, layer, g.w.biomes[-1], blockindex, blockname, len(g.w.data) - 1, chest_blocks, Window)
        except IndexError:
            entities = []
        g.w.entities.extend(entities)
    # sky
    for _ in range(L):
        cr_block("air", index=0)
    # underground
    underground = SmartList([wchoice(("stone", "air"), (50, 50)) for _ in range(L)])
    underground.smoothen("stone", "air", 3, 5, HL, itr=3)
    underground = [block if block == "air" else rand_ore("stone") for block in underground]
    underground[0:HL] = ["air"] * HL
    g.w.data[-1].extend(underground)
    # magic world
    magic_0 = ["air"] * L
    magic_1 = SmartList([wchoice(("magic-brick", "air"), (50, 50)) for _ in range(L)])
    magic_1.smoothen("magic-brick", "air", 3, 5, HL, itr=5)
    magic_2 = ["air"] * L
    g.w.magic_data[-1].extend(magic_0)
    g.w.magic_data[-1].extend(magic_1)
    g.w.magic_data[-1].extend(magic_2)


def save_screen():
    if not g.loading_world:  # non-daemonic threaded save screen
        del g.w.get_data[g.w.screen][g.w.abs_blocki: g.w.abs_blocki * 2]
        for index, block in enumerate(all_blocks, g.w.abs_blocki):
            g.w.get_data[g.w.screen].insert(index, block.name)


# S T A T I C  O B J E C T  F U N C T I O N S  -------------------------------------------------------  #
def is_drawable(obj):
    try:
        return g.w.screen == obj.screen and g.w.layer == obj.layer and g.w.dimension == getattr(obj, "dimension", "data")
    except AttributeError:
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
class ExitHandler:
    @staticmethod
    def save(stage):
        # disable unnecessarry widgets
        for widget in pw.death_screen_widgets:
            widget.disable()
        # save home bg image
        pygame.image.save(g.home_bg_img, path("Images", "Background", "home_bg.png"))
        # save world metadata
        g.w.last_epoch = epoch()
        # save world data
        if g.w.screen is not None:
            if g.w.data:
               save_screen()
            if g.w.name is not None:
                with open(path(".game_data", "worlds", g.w.name + ".dat"), "wb") as f:
                    pickle.dump(g.w.data, f)
        # generating world icon
        icon = pygame.Surface(wb_icon_size, pygame.SRCALPHA)
        br = 3
        pygame.draw.rect(icon, (95, 95, 95), (0, 0, wb_icon_size[0], wb_icon_size[1] - 30), 0, 0, br, br, -1, -1)

        y = tlo = 9
        o = 4
        yy = 0
        br = 3
        # biomes_img = pygame.Surface(wb_icon_size)
        # for x, (biome, freq) in enumerate(g.w.biome_freq.items()):
        #     if x == 3:
        #         break
        #     block_img = g.w.blocks[bio.blocks[biome][0]]
        #     x = x * (BS + 12) + tlo
        #     icon.blit(block_img, (x, y))
        #     pygame.draw.rect(icon, YELLOW, (x - o, y - o, BS + o * 2, BS + o * 2), 1, br, br, br, br)
        #     write(icon, "midtop", f"{freq}%", orbit_fonts[12], BLACK, x + 14, y + 33)
        # pygame.gfxdraw.hline(icon, 0, wb_icon_size[0], wb_icon_size[1] - 30, BLACK)
        # block_img = g.w.blocks["soil_f"].copy()
        # icon.blit(block_img, (tlo, tlo))
        # pygame.draw.rect(icon, WHITE, (tlo - o, tlo - o, BS + o * 2, BS + o * 2), 1, 0, br, br, br, br)
        #
        icon.blit(g.player.image, (tlo, tlo))
        # save button data
        for button in all_home_world_world_buttons:
            if button.data["world"] == g.w.name:
                g.player.width, g.player.height = g.player.image.get_size()
                g.player.prepare_deepcopy()
                button.data["player_obj"] = deepcopy(g.player)
                button.data["world_obj"] = deepcopy(g.w)
                button.init_bg(icon, g.player.username)
                button.data["image"] = deepcopy(SmartSurface.from_surface(button.image))
                button.data["username"] = g.player.username
                break
        # save world buttons (pickle)
        with open(path(".game_data", "worldbuttons.dat"), "wb") as f:
            if all_home_world_world_buttons:
                button_attrs = [button.data for button in all_home_world_world_buttons]
                pickle.dump(button_attrs, f)
        # save play (global variable) data
        with open(path(".game_data", "variables.dat"), "wb") as f:
            pickle.dump(g.p, f)
        # cleanup attributes
        g.w.screen = None
        g.w.name = None
        """
        g.mb.craftings = {}
        g.mb.burnings = {}
        g.mb.furnace_log = []
        g.mb.fuels = {}
        g.mb.smithings = {}
        g.mb.smither = None
        g.mb.anvil_log = []
        g.mb.crafting_log = []
        g.mb.gun_parts = {k: None for k in g.mb.gun_parts}
        g.mb.gun_log = []
        """
        # final
        if stage == "quit":
            g.stop()
        elif stage == "home":
            g.w.entities.clear()
            for fgs in all_foreground_sprites.sprites():
                if isinstance(fgs, InfoBox):
                    all_foreground_sprites.remove(fgs)


class World:
    def __init__(self):
        # world-generation / world data related data
        self.data = SmartList()
        self.magic_data = SmartList()
        self.metadata = SmartList()
        self.dimension = "data"
        self.entities = []
        self.mode = None
        self.screen = 0
        self.layer = 1
        self.biomes = []
        self.prev_screen = self.data
        self.name = None
        self.linked = False
        # game settings
        self.show_internals = False
        self.language = "english"
        self.player_model_color = GRAY
        # day-night cycle
        self.hound_round = False
        self.hound_round_chance = 20
        self.def_dnc_colors = [SKY_BLUE] * 180 + lerp(SKY_BLUE, DARK_BLUE, 180) + lerp(DARK_BLUE, BLACK, 180) + [BLACK] * 180
        self.hr_dnc_colors = [SKY_BLUE for _ in range(360)] + lerp(SKY_BLUE, ORANGE, 180) + lerp(ORANGE, BLACK, 180)
        self.set_dnc_colors()
        self.dnc_direc = op.add
        self.dnc_index = 0
        self.dnc_minutes = 5
        self.dnc_vel = self.dnc_minute_vel / 20
        self.dnc_hours = list(range(12, 24)) + list(range(0, 12))
        self.dnc_darkness = 1
        self.wind = [-0.01, 0.002]
         # saved assets
        self.assets = {"blocks": {}, "tools": {}, "icons": {}}
        self.asset_sizes = a.sizes
        for atype, dict_ in a.assets.items():
            if isinstance(dict_, dict):
                for name, img in dict_.items():
                    if isinstance(img, pygame.Surface):
                        self.assets[atype][name] = SmartSurface.from_surface(img)
            elif isinstance(dict_, list):
                setattr(self, atype, [SmartSurface.from_surface(x) for x in dict_])
        """
        for d in self.assets:
            for k, v in self.assets[d].items():
                pygame.image.save(v, path(".game_data", "texture_packs", ".default", d, k + ".png"))
        """
        self.last_epoch = epoch()

    @property
    def player_model(self):
        ret = pygame.Surface([s * g.skin_scale_mult for s in g.player_size])
        ret.fill(self.player_model_color)
        return ret

    @property
    def blocks(self):
        return self.assets["blocks"]

    @property
    def tools(self):
        return self.assets["tools"]

    @property
    def icons(self):
        return self.assets["icons"]

    @property
    def text_color(self):
        return contrast_color(g.w.dnc_color)

    @property
    def dnc_color(self):
        return self.dnc_colors[int(self.dnc_index)]

    @property
    def dnc_length(self):
        for dnct in ("", "def", "hr"):
            with suppress(AttributeError):
                return len(getattr(self, dnct + "_dnc_colors"))

    @property
    def dnc_second_vel(self):
        return self.dnc_length * 2 / g.fps_cap

    @property
    def dnc_minute_vel(self):
        return self.dnc_second_vel / 60

    def set_dnc_colors(self):
        if random.randint(1, self.hound_round_chance) == 1:
            self.dnc_colors = self.hr_dnc_colors.copy()
        else:
            self.dnc_colors = self.def_dnc_colors.copy()

    @property
    def abs_blocki(self):
        return self.layer * L

    @property
    def get_data(self):
        return getattr(self, self.dimension if self.dimension == "data" else self.dimension + "_data")

    @property
    def sdata(self):
        return self.get_data[self.screen]

    @property
    def smetadata(self):
        return self.metadata[self.screen]

    @property
    def sky_color(self):
        if self.dimension == "data":
            if self.layer < 2:
                return self.dnc_color
            else:
                return ALMOST_BLACK
        elif self.dimension == "magic":
            return DARK_PURPLE

    @property
    def biome_freq(self):
        check_biomes = set(g.w.biomes)
        write_biomes = []
        for biome in check_biomes:
            bme = biome
            prc = int(g.w.biomes.count(biome) / len(g.w.biomes) * 100)
            write_biomes.append((bme, prc))
        bfreq = {k: v for (k, v) in write_biomes}
        bfreq = dict(sorted(bfreq.items(), key=lambda x: x[1], reverse=True))
        return bfreq


class Play:
    def __init__(self):
        self.world_names = []
        self.next_worldbutton_pos = [45, 100]
        self.starting_worldbutton_pos = c1dl(self.next_worldbutton_pos)
        self.new_world_count = 0
        self.loaded_world_count = 0
        self.unlocked_skins = []
        self.loading_times = SmartList()
        self.anim_fps = 0.0583
        self.volume = 0.2


g.p = Play()

# load variables
if os.path.getsize(path(".game_data", "variables.dat")) > 0:
    with open(path(".game_data", "variables.dat"), "rb") as f:
        g.p = pickle.load(f)


class PlayWidgets:
    def __init__(self):
        # menu widgets
        set_default_fonts(orbit_fonts)
        set_default_tooltip_fonts(orbit_fonts)
        _menu_widget_kwargs = {"anchor": "center", "width": 130, "template": "menu widget", "font": orbit_fonts[15]}
        _menu_button_kwargs = _menu_widget_kwargs | {"height": 31}
        _menu_togglebutton_kwargs = _menu_button_kwargs
        _menu_checkbox_kwargs = _menu_widget_kwargs | {"height": 31}
        _menu_slider_kwargs = _menu_widget_kwargs | {"width": 140, "height": 60}
        self.menu_widgets = {
            "buttons": SmartList([
                Button(Window.display,   "Change Skin",   self.change_skin_command,   tooltip="Allows you to customize your player's appearance", **_menu_button_kwargs),
                Button(Window.display,   "Next Piece",    self.next_piece_command,    tooltip="Plays a different random theme piece",             **_menu_button_kwargs),
                Button(Window.display,   "Config",        self.show_config_command,   tooltip="Configure advanced game parameters",               **_menu_button_kwargs),
                Button(Window.display,   "Flag",          self.flag_command,          tooltip="Whenever teleported, spawn at current position",   **_menu_button_kwargs),
                Button(Window.display,   "Textures",      self.texture_pack_command,  tooltip="Initialize a texture pack for this world",         **_menu_button_kwargs),
                Button(Window.display,   "Save and Quit", self.save_and_quit_command, tooltip="Save and quit world",                              **_menu_button_kwargs),
            ]),
            "togglebuttons": SmartList([
                ToggleButton(Window.display, ("Instant", "Generative"), tooltip="Toggles the visual generation of chunks", **_menu_togglebutton_kwargs),
            ]),
            "checkboxes": SmartList([
                Checkbox(Window.display, "Stats",         self.show_stats_command,    checked=True, exit_command=self.checkb_sf_exit_command, tooltip="Shows the player's stats", **_menu_checkbox_kwargs),
                Checkbox(Window.display, "Time",          self.show_time_command,     tooltip="Shows the in-world time",                                        **_menu_checkbox_kwargs),
                Checkbox(Window.display, "FPS",           self.show_fps_command,      tooltip="Shows the amount of frames per second",                          **_menu_checkbox_kwargs),
                Checkbox(Window.display, "VSync",         self.show_vsync_command,    tooltip="Enables VSync; may or may not work", check_command=self.check_vsync_command, uncheck_command=self.uncheck_vsync_command, **_menu_checkbox_kwargs),
                Checkbox(Window.display, "Biomes",        self.show_biomes_command,   tooltip="Shows the biomes you have visited",                              **_menu_checkbox_kwargs),
                Checkbox(Window.display, "Internals",                                                                                                           **_menu_checkbox_kwargs),
                Checkbox(Window.display, "Fog",           self.fog_command,           tooltip="Fog effect for no reason at all",                                **_menu_checkbox_kwargs),
                Checkbox(Window.display, "Clouds",        lambda_none,                tooltip="Clouds lel what did you expect",                                 **_menu_checkbox_kwargs),
            ]),
            "sliders": SmartList([
                Slider(Window.display,   "FPS Cap",       (30, 60, 90, 120, 240, 500), g.def_fps_cap, tooltip="The framerate cap",                                **_menu_slider_kwargs),
                Slider(Window.display,   "Animation",     range(21),  int(g.p.anim_fps * g.fps_cap),  tooltip="Animation speed of graphics",                      **_menu_slider_kwargs),
                Slider(Window.display,   "Lag",           range(1, 101), 100,                         tooltip="The lag of the camera that fixated on the player", **_menu_slider_kwargs),
                Slider(Window.display,   "Volume",        range(101), int(g.p.volume * 100),          tooltip="Master volume",                                    **_menu_slider_kwargs),
            ]),
        }
        _sy = _y = 190
        _x = 180
        for mw_type in self.menu_widgets:
            for mw in self.menu_widgets[mw_type]:
                mw.set_pos((_x, _y), "midtop")
                _y += mw.height + 1
            _x += mw.width + 15
            _y = _sy
        _death_screen_widget_kwargs = {"anchor": "center", "disabled": True, "disable_type": "static", "font": orbit_fonts[15]}
        self.death_screen_widgets = SmartList([
            Label(Window.display, "Death", (DPX, DPY - 64), **_death_screen_widget_kwargs),
            Button(Window.display, "Play Again", command=self.quit_death_screen_command, pos=(DPX, DPY), **_death_screen_widget_kwargs)
        ])
        self.death_cause =       self.death_screen_widgets.find(lambda x: x.text == "Death")
        self.fps_cap =           self.menu_widgets["sliders"].find(lambda x: x.text == "FPS Cap")
        self.show_stats =        self.menu_widgets["checkboxes"].find(lambda x: x.text == "Stats")
        self.show_internals =    self.menu_widgets["checkboxes"].find(lambda x: x.text == "Internals")
        self.vsync =             self.menu_widgets["checkboxes"].find(lambda x: x.text == "VSync")
        self.clouds =            self.menu_widgets["checkboxes"].find(lambda x: x.text == "Clouds")
        self.generation_mode =   self.menu_widgets["togglebuttons"].find(lambda x: x.text == "Instant")
        self.anim_fps =          self.menu_widgets["sliders"].find(lambda x: x.text == "Animation")
        self.lag =               self.menu_widgets["sliders"].find(lambda x: x.text == "Lag")
        self.volume =            self.menu_widgets["sliders"].find(lambda x: x.text == "Volume")
        self.texture_pack =      self.menu_widgets["buttons"].find(lambda x: x.text == "Textures")
        #
        self.iter_menu_widgets = sum(self.menu_widgets.values(), [])
        befriend_iterable(self.iter_menu_widgets)
        # skin menu arrow buttons to change the skin
        self.change_skin_buttons = []
        for bt in g.skins:
            self.change_skin_buttons.append({"name": "p-" + bt, "surf": rotozoom(triangle(height=30), 90, 1)})
            self.change_skin_buttons[-1]["mask"] = pygame.mask.from_surface(self.change_skin_buttons[-1]["surf"])
        for bt in g.skins:
            self.change_skin_buttons.append({"name": "n-" + bt, "surf": rotozoom(triangle(height=30), 270, 1)})
            self.change_skin_buttons[-1]["mask"] = pygame.mask.from_surface(self.change_skin_buttons[-1]["surf"])
        xo, yo = 40, 100
        sx = g.skin_menu_rect.x + xo
        sy = g.skin_menu_rect.y + yo
        x, y = sx, sy
        for index, button in enumerate(self.change_skin_buttons):
            if index == 4:
                x = Window.width - sx
                y = sy
            button["rect"] = button["surf"].get_rect(center=(x, y))
            y += (g.skin_menu_rect.height - yo * 2) / 3
        _skin_button_kwargs = {"width": 9 * g.skin_fppp, "height": 30, "bg_color": GRAY, "template": "menu widget", "special_flags": ["static"]}
        self.skin_buttons = [
            Button(Window.display, "Color", self.color_skin_button, pos=(DPX, DPY + 90), **_skin_button_kwargs),
            Button(Window.display, "Done", self.new_player_skin, pos=(DPX, DPY + 120), click_effect=True, **_skin_button_kwargs)
        ]

    # menu widget commands
    @staticmethod
    def show_stats_command():
        if g.stage == "play":
            if g.w.mode == "adventure":
                if not g.skin_menu:
                    x = 32
                    y = 15
                    for data in g.player.stats.values():
                        if data:
                            pygame.draw.rect(Window.display, BLACK, (x, y, bar_outline_width, bar_outline_height), 0, 3, 3, 3, 3)
                            pygame.draw.rect(Window.display, bar_rgb[int((data["amount"] - 1) * (99 / 100))] if data["icon"] != "shield" else LIGHT_GRAY, (*[p + 2 for p in (x, y)], bar_width / 100 * data["amount"], bar_outline_height - 4), 0, 3, 3, 3, 3)
                            write(Window.display, "midleft", f"{round(data['amount'])} / 100", orbit_fonts[13], g.w.text_color, x + bar_outline_width + 8, y + 3)

                            Window.display.blit(g.w.icons[data["icon"]], (x - 22, y - (15 - bar_outline_height) / 2))
                            # for i, (at, a) in enumerate(g.player.armor.items()):
                            #     Window.display.blit(g.w.blocks[a if a is not None else f"base-{at}"], (7, y + 9 + i * 7))
                        y += 21
                    y = 155
                    i = 0

    @staticmethod
    def show_fps_command():
        if g.stage == "play":
            write(Window.display, "topright", int(g.clock.get_fps()), orbit_fonts[20], g.w.text_color, Window.width - 10, 26)
            # write(Window.display, "topright", int(g.clock.get_fps()), orbit_fonts[20], BLACK, Window.width - 10, 40)

    @staticmethod
    def show_vsync_command():
        write(Window.display, "midtop", "vsync", orbit_fonts[8], RED, Window.width - 21, -2)

    @staticmethod
    def check_vsync_command():
        Window.init((BS * HL * R, BS * VL * R), debug=True, vsync=1, flags=pygame.SCALED)
        pnp_press_and_release()

    @staticmethod
    def uncheck_vsync_command():
        Window.init((BS * HL * R, BS * VL * R), debug=True)
        pnp_press_and_release()

    @staticmethod
    def show_time_command():
        if g.stage == "play":
            fin = f"{int(g.w.dnc_index)} / {g.w.dnc_length}"
            write(Window.display, "topright", fin, orbit_fonts[20], g.w.text_color, Window.width - 10, 70)

    @staticmethod
    def show_biomes_command():
        if g.stage == "play":
            for y, (biome, prc) in enumerate(g.w.biome_freq.items()):
                write(Window.display, "topleft", f"{biome.capitalize()}: {prc}%", orbit_fonts[13], g.w.text_color, 15, 160 + y * 15)

    @staticmethod
    def checkb_sf_exit_command():
        g.menu = False

    @staticmethod
    def fog_command():
        g.fog_img.fill(BLACK)
        g.fog_img.blit(g.fog_light, g.player.rect.center)
        Window.display.blit(g.fog_img, (0, 0), special_flags=pygame.BLEND_MULT)

    def change_skin_command(self):
        g.menu = False
        for widget in self.iter_menu_widgets:
            widget.disable()
        for button in self.skin_buttons:
            button.enable()
        g.skin_menu = True

    def color_skin_button(self):
        g.pending_entries.append(Entry(Window.display, "Enter RGB or HEX color code", self.color_skin, disabled=True, add=False, **g.def_entry_kwargs))

    @staticmethod
    def color_skin(code):
        try:
            color = pygame.Color(code if "#" in code else [int(cc) for cc in code.replace(",", " ").split(" ") if cc])
        except ValueError:
            MessageboxOk(Window.display, "Invalid color.", **g.def_widget_kwargs)
        else:
            g.w.player_model_color = color

    @staticmethod
    def new_player_skin():
        # finalizing skin
        longest_sprs_len = max([len(g.skin_data(bt)["sprs"]) for bt in g.skins])
        g.player.images = [SmartSurface((Window.size), pygame.SRCALPHA) for _ in range(longest_sprs_len if longest_sprs_len > 0 else 1)]
        _bg = SmartSurface(g.player_size); _bg.fill(g.w.player_model_color)
        for image in g.player.images:
            image.blit(_bg, [s / 2 for s in image.get_size()])
        if not g.player.images:
            g.player.images = [SmartSurface(g.player_size)]; g.player.images[0].fill(GRAY)
        for anim in range(longest_sprs_len):
            for bt in g.skins:
                if g.skin_data(bt).get("name", True) is not None:
                    try:
                        skin_img = scalex(g.skin_data(bt)["sprs"][anim], 1 / g.skin_scale_mult)
                    except IndexError:
                        skin_img = scalex(g.skin_data(bt)["sprs"][anim % 4], 1 / g.skin_scale_mult)
                    finally:
                        _sp = g.skin_data(bt)["offset"]
                        skin_pos = [s / 2 for s in Window.size]
                        skin_pos[0] -= g.player_size[0] / 2
                        skin_pos[1] -= g.player_size[1] / 2
                        skin_pos[0] += _sp[0] * g.fppp + 1
                        skin_pos[1] += _sp[1] * g.fppp + 1
                        g.player.images[anim].blit(skin_img, skin_pos)
        # cropping
        rects = [pg_to_pil(image).getbbox() for image in g.player.images]
        x1 = min([rect[0] for rect in rects])
        y1 = min([rect[1] for rect in rects])
        x2 = max([rect[2] for rect in rects])
        y2 = max([rect[3] for rect in rects])
        rect = pil_rect2pg((x1, y1, x2, y2))
        # image initialization
        p_imgs = [image.subsurface(rect) for image in g.player.images]
        g.player.flip_images(p_imgs)
        g.player.images = g.player.right_images
        g.player.rect = g.player.images[0].get_rect(center=g.player.rect.center)
        g.player.width, g.player.height = g.player.images[0].get_size()
        del g.player.images
        # lasts
        g.skin_menu = False
        for button in iter_buttons():
            if getattr(button, "text", None) == "Color":
                button.destroy()

    @staticmethod
    def change_movement_command(type_):
        if type_ != "Arrow Keys":
            for index, key in enumerate(type_):
                g.ckeys[list(g.ckeys.keys())[index]] = getattr(pygame, f"K_{key.lower()}")
        else:
            g.ckeys["p up"] = K_UP
            g.ckeys["p left"] = K_LEFT
            g.ckeys["p down"] = K_DOWN
            g.ckeys["p right"] = K_RIGHT

    @staticmethod
    def next_piece_command():
        music_path = get_rand_track(path("Audio", "Music", "Background"))
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play()
        g.last_music = os.path.splitext(os.path.split(music_path)[1])[0]

    @staticmethod
    def show_config_command():
        g.opened_file = True
        open_text("config.json")

    @staticmethod
    def flag_command():
        g.w.flag_data["screen"] = g.w.screen
        g.w.flag_data["pos"] = g.player.rect.center
        group(SlidePopup("Flagged coordinates!"), all_slidepopups)

    @staticmethod
    def texture_pack_command():
        def tpc(e):
            p = path(".game_data", "texture_packs")
            if e in os.listdir(p):
                for d in os.listdir(path(p, e)):
                    if d != ".DS_Store":
                        for item in os.listdir(path(p, e, d)):
                            g.w.assets[d][os.path.splitext(item)[0]] = SmartSurface.from_surface(cimgload(path(p, e, d, item)))
            else:
                MessageboxOk(Window.display, "Texture pack does not exist, load it first", **g.def_widget_kwargs)
        entry_tp = Entry(Window.display, "Enter the name of the texture pack ('.default' for default):", tpc, **g.def_entry_kwargs, friends=[pw.texture_pack])

    @staticmethod
    def save_and_quit_command():
        destroy_widgets()
        empty_group(all_drops)
        ExitHandler.save("home")
        g.stage = "home"
        g.menu = False

    # home static widgets
    @staticmethod
    def is_worlds_worlds():
        return g.stage == "home" and g.home_stage == "worlds"

    @staticmethod
    def is_worlds_static():
        return g.stage == "home" and g.home_stage == "settings"

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
    def load_world_command():
        if not all_messageboxes:
            loading_path = choose_file("Load a .dat file")
            if loading_path != "/":
                with open(loading_path, "rb") as f:
                    worldcode = pickle.load(f)
                new_world(worldcode)

    @staticmethod
    def button_daw_command():
        if not all_messageboxes:
            delete_all_worlds()

    @staticmethod
    def show_credits_command():
        g.opened_file = True
        open_text("CREDITS.txt")

    @staticmethod
    def intro_command():
        play_intro()

    @staticmethod
    def custom_textures_command():
        # open_text("TEXTURE_TUTORIAL.txt")
        pth = choose_folder("Choose folder where texture pack is located")
        tex = os.path.basename(os.path.normpath(pth))
        if tex == ".default":
            MessageboxOk(Window.display, "Texture pack cannot have the name '.default'", **g.def_widget_kwargs)
            return
        shutil.copytree(pth, path(".game_data", "texture_packs", tex), dirs_exist_ok=True)
        MessageboxOk(Window.display, "Texture pack loaded succesfully.", **g.def_widget_kwargs)

    @staticmethod
    def download_language_command():
        test_subject = "dirt"
        def download(e):
            e = e.lower()
            def download_language():
                g.set_loading("language", True)
                try:
                    t.init(e)
                    test_subject
                except translatepy.exceptions.UnknownLanguage:
                    MessageboxOk(Window.display, f"Unknown language <{e}>", **g.def_widget_kwargs)
                else:
                    # downloading translations
                    len_translations = len(g.w.all_assets) + len(iter_overwriteables())
                    dictionary = {}
                    for asset in g.w.all_assets:
                        if asset != test_subject:
                            dictionary[asset] = asset.replace("-", " ").replace("_", " ")
                            g.loading_language_perc += 1 / len_translations * 100
                    for widget in iter_overwriteables():
                        dictionary[widget.text] = widget.text
                    for mwidget in all_home:
                        dictionary[mwidget.text] = mwidget.text
                    # german corections
                    if e == "german":
                        dictionary["lives"] = "Leben"
                        dictionary["FPS"] = "FPS"
                    # saving translations to a json file
                    with open(path(".game_data", "languages", f"{e}.json"), "w") as f:
                        json.dump(dictionary, f, indent=4)
                    # if e not in g.p.downloaded_languages:
                    #     g.p.downloaded_languages.append(e)
                g.set_loading("language", False)
            DThread(target=download_language).start()
        Entry(Window.display, "Enter the language to be downloaded:", download, **g.def_entry_kwargs)

    @staticmethod
    def set_home_stage_worlds_command():
        g.home_stage = "worlds"

    @staticmethod
    def set_home_stage_settings_command():
        g.home_stage = "settings"


g.w = World()
pw = PlayWidgets()


# G R A P H I C A L  C L A S S E S S ------------------------------------------------------------------ #
class Scrollable:
    @property
    def rect(self):
        return pygame.Rect(self._rect.x - g.scroll[0], self._rect.y - g.scroll[1], *self._rect.size)


class Player(Scrollable):
    def __init__(self):
        self.images = [SmartSurface(g.player_size) for _ in range(4)]
        for image in self.images:
            image.fill(GRAY)
        # image initialization
        self.direc = "left"
        self.anim = 0
        self.up = True
        self.flip_images(self.images)
        self.animate()
        # rest
        self._rect = self.image.get_rect(center=(Window.width / 2, Window.height / 2))
        self._rect.center = (Window.width / 2, Window.height / 2)
        self.width = self.rect.width
        self.height = self.rect.height
        self.size = (self.width, self.height)
        self.gravity = 0.15
        self.fre_vel = 3
        self.adv_xvel = 2
        self.water_xvel = 1
        self.xvel = 0
        self.yvel = 0
        self.def_jump_yvel = -3.5
        self.jump_yvel = self.def_jump_yvel
        self.water_jump_yvel = self.jump_yvel / 2
        self.fall_effect = 0
        self.jumps_left = 0
        self.dx = 0
        self.dy = 0
        self.block_rects = []
        self.still = True
        self.in_air = True
        self.invisible = False
        self.skin = None
        self.stats = {}
        self.spin_angle = 0

        self.set_moving_mode("adventure")

        self.def_food_pie = {"counter": -90}
        self.food_pie = self.def_food_pie.copy()
        self.achievements = {"steps taken": 0, "steps counting": 0}
        self.armor = dict.fromkeys(("helmet", "chestplate", "leggings"), None)
        self.dead = False
        self.spawn_data = (g.w.screen, g.w.layer)

        self.rand_username()

        self.tools = []
        self.tool_healths = []
        self.tool_ammos = []
        self.inventory = []
        self.inventory_amounts = []
        self.indexes = {}
        self.pouch = 15
        self.broken_blocks = dd(int)
        self.main = "block"

    def update(self):  # player update
        self.animate()
        self.draw()
        self.move_accordingly()
        self.off_screen()
        self.drops()
        #self.update_fall_effect()
        self.update_effects()
        self.achieve()

    def move_accordingly(self):
        if no_widgets(Entry):
            getattr(self, self.moving_mode[0] + "_move")(*self.moving_mode[1:])

    def draw(self):  # player draw
        # pre
        Window.display.blit(self.image, self.rect)
        # post
        if self.armor["helmet"] is not None:
            Window.display.blit(g.w.blocks[self.armor["helmet"]], self.rect)
        if self.armor["chestplate"] is not None:
            Window.display.blit(g.w.blocks[self.armor["chestplate"]], (self.rect.x - 3, self.rect.y + 9))
        if self.armor["leggings"] is not None:
            Window.display.blit(g.w.blocks[self.armor["leggings"]], (self.rect.x, self.rect.y + 21))

    @property
    def reverse_blocks(self):
        yield from reversed(all_blocks)

    @property
    def closest_blocks(self):
        yield from sorted(all_blocks, key=lambda block: distance(self.rect, block.rect))

    @property
    def closest_tool_blocks(self):
        yield from sorted(all_blocks, key=lambda block: distance(visual.rect, block.rect))

    @property
    def angle(self):
        return revnum(degrees(two_pos_to_angle(self.rect.center, g.mouse)))

    @property
    def item(self):
        return self.inventory[self.indexes[self.main]]

    @item.setter
    def item(self, value):
        self.inventory[self.indexes[self.main]] = value

    @property
    def itemi(self):
        return self.indexes[self.main]

    @itemi.setter
    def itemi(self, value):
        self.indexes[self.main] = value

    @property
    def block(self):
        return self.inventory[self.blocki] if self.inventory[self.blocki] is not None else ""

    @block.setter
    def block(self, value):
        self.inventory[self.blocki] = value

    @property
    def blocki(self):
        return self.indexes["block"]

    @blocki.setter
    def blocki(self, value):
        self.indexes["block"] = value

    @property
    def empty_blocki(self):
        return first(self.inventory, None, self.blocki)

    @empty_blocki.setter
    def empty_block(self, value):
        if isinstance(value, tuple):
            ebi = self.empty_blocki
            self.inventory[ebi], self.inventory_amounts[ebi] = value
        else:
            self.inventory[self.empty_blocki] = value

    @property
    def tool(self):
        return self.tools[self.indexes["tool"]]

    @tool.setter
    def tool(self, value):
        self.tools[self.indexes["tool"]] = value

    @property
    def tool_type(self):
        return gtool(self.tool)

    @property
    def tool_ore(self):
        return tore(self.tool)

    @property
    def tooli(self):
        return self.indexes["tool"]

    @tooli.setter
    def tooli(self, value):
        self.indexes["tool"] = value

    @property
    def empty_tooli(self):
        return first(self.tools, None, self.tooli)

    @empty_tooli.setter
    def empty_tool(self, value):
        self.tools[self.empty_tooli] = value

    @property
    def tool_health(self):
        return self.tool_healths[self.tooli]

    @tool_health.setter
    def tool_health(self, value):
        self.tool_healths[self.tooli] = value

    @property
    def tool_ammo(self):
        return self.tool_ammos[self.tooli]

    @tool_ammo.setter
    def tool_ammo(self, value):
        self.tool_ammos[self.tooli] = value

    @property
    def gun(self):
        return self.tools[self.guni]

    @gun.setter
    def gun(self, value):
        self.tools[self.guni] = value

    @property
    def guni(self):
        return first(self.tools, is_gun, None)

    @property
    def amount(self):
        return self.inventory_amounts[self.indexes[self.main]]

    @amount.setter
    def amount(self, value):
        self.inventory_amounts[self.indexes[self.main]] = value

    def new_block(self, name, amount=1):
        if name in self.inventory:
            self.inventory_amounts[self.inventory.index(name)] += amount
        else:
            self.empty_block = name, amount

    def new_empty_block(self, name, amount=1):
        if None in self.inventory:
            self.new_block(name, amount)

    @property
    def lives(self):
        return self.stats["lives"]["amount"]

    @lives.setter
    def lives(self, value):
        self.stats["lives"]["amount"] = value
        if self.lives > 100:
            self.lives = 100

    @property
    def hunger(self):
        return self.stats["hunger"]["amount"]

    @hunger.setter
    def hunger(self, value):
        self.stats["hunger"]["amount"] = value
        if self.hunger > 100:
            self.hunger = 100

    @property
    def thirst(self):
        return self.stats["thirst"]["amount"]

    @thirst.setter
    def thirst(self, value):
        self.stats["thirst"]["amount"] = value
        if self.thirst > 100:
            self.thirst = 100

    @property
    def energy(self):
        return self.stats["energy"]["amount"]

    @energy.setter
    def energy(self, value):
        self.stats["energy"]["amount"] = value
        if self.energy > 100:
            self.energy = 100

    @property
    def oxygen(self):
        return self.stats["oxygen"]["amount"]

    @oxygen.setter
    def oxygen(self, value):
        self.stats["oxygen"]["amount"] = value
        if self.oxygen > 100:
            self.oxygen = 100

    def prepare_deepcopy(self):
        del self.fdi

    def flip_images(self, images):
        images = [SmartSurface.from_surface(img) for img in images]
        self.right_images = images
        self.left_images = [SmartSurface.from_surface(pygame.transform.flip(img, True, False)) for img in images]

    def achieve(self):
        pass

    def set_moving_mode(self, name, *args):
        self.moving_mode = [name, *args]
        if name in ("adventure", "freestyle"):
            self.last_moving_mode = [name, *args]

    def new_tool(self, name):
        self.tool_healths[self.empty_tooli] = 100
        self.empty_tool = name

    def link_worlds(self):
        def m():
            time.sleep(randf(0.5, 1.5))
            if chance(1 / 10):
                text = "The linking has been unsuccesful."
            else:
                text = "The worlds have linked succesfully."
                g.cannot_place_block = True
                g.w.dimension = "magic"
                g.w.linked = True
                utilize_blocks()
                next_ambient()
            MessageboxOk(Window.display, "The worlds have linked succesfully.", **g.def_widget_kwargs)

        Thread(target=m).start()

    def die(self, cause):
        self.dead = True
        pw.death_cause.overwrite(f"{self.username} has died. Cause of death: {cause}")
        for widget in pw.death_screen_widgets:
            widget.enable()

    def use_up_inv(self, index=None, amount=1):
        index = index if index is not None else self.blocki
        self.inventory_amounts[index] -= amount
        if self.inventory_amounts[index] == 0:
            self.inventory[index] = None
            self.inventory_amounts[index] = None

    def take_dmg(self, amount, shake_offset, shake_length, reason=None):
        self.stats["lives"]["amount"] -= amount
        self.stats["lives"]["regen_time"] = def_regen_time
        self.stats["lives"]["last_regen"] = ticks()
        g.s_render_offset = shake_offset
        g.screen_shake = shake_length
        if g.player.stats["lives"]["amount"] <= 0:
            g.player.die(reason)

    def eat(self):
        food = self.block
        self.food_pie["counter"] += get_finfo(self.inventory[self.blocki])["speed"]
        degrees = self.food_pie["counter"]
        pie_size = (30, 30)
        pil_img = PIL.Image.new("RGBA", [s * 4 for s in pie_size])
        pil_draw = PIL.ImageDraw.Draw(pil_img)
        pil_draw.pieslice((0, 0, *[ps * 4 - 1 for ps in pie_size]), -90, degrees, fill=g.w.player_model_color[:3])
        pil_img = pil_img.resize(pie_size, PIL.Image.ANTIALIAS)
        pg_img = pil_to_pg(pil_img)
        self.food_pie["image"] = pg_img
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
        pass

    def drops(self):
        for drop in all_drops:
            if drop.rect.colliderect(self.rect):
                if None in g.player.inventory or drop.name in g.player.inventory:
                    self.new_block(drop.name, drop.drop_amount)
                    drop.kill()
                    pitch_shift(pickup_sound).play()
                    if None not in self.inventory:
                        drop.rect.center = [pos + random.randint(-1, 1) for pos in drop.og_pos]

    def rand_username(self):
        # self.username = f"Player{rand(2, 456)}"
        # self.username = json.loads(requests.get(g.funny_words_url).text)[0].split("_")[0]
        # self.username = json.loads(requests.get(g.funny_words_url).text)[0].split("_")[0]
        # self.username = fnames.dwarf()
        # self.username = shake_str(json.loads(requests.get(g.name_url).text)["name"]).title()
        # self.username = json.loads(requests.get(g.name_url).text)["username"].capitalize()
        # self.username = " ".join([json.loads(requests.get(g.random_word_url).text)[0]["word"] for _ in range(2)]).title()
        self.username = rand_alien_name().title()

    def cust_username(self):
        def set_username(ans):
            if ans is not None and ans != "":
                split_username = ans.split(" ")
                username = " ".join([word if not word in g.profanities else len(word) * "*" for word in split_username])

                self.username = username
            else:
                self.rand_username()
        Entry(Window.display, "Enter your new username:", set_username, **g.def_entry_kwargs, default_text=("random", orbit_fonts[20]))

    def freestyle_move(self):
        keys = pygame.key.get_pressed()
        if g.keys[g.ckeys["p up"]]:
            self.rect.y -= self.fre_vel
        if g.keys[g.ckeys["p down"]]:
            self.rect.y += self.fre_vel
        if g.keys[g.ckeys["p left"]]:
            self.rect.x -= self.fre_vel
        if g.keys[g.ckeys["p right"]]:
            self.rect.x += self.fre_vel

    def get_cols(self):
        return [brect for brect in self.block_rects if self._rect.colliderect(brect)]

    def scroll(self):
        g.scroll[0] += (self._rect.x - g.scroll[0] - Window.width / 2 + self.width / 2) / pw.lag.value
        g.scroll[1] += (self._rect.y - g.scroll[1] - Window.height / 2 + self.height / 2) / pw.lag.value

    def adventure_move(self):
        # scroll
        self.scroll()
        # collisions
        self.yvel += self.gravity
        self._rect.bottom += self.yvel
        cols = self.get_cols()
        if cols:
            if self.yvel > 0:
                self._rect.bottom = cols[0].top
                self.yvel = 0
                self.in_air = False
                self.spin_angle = 0
            else:
                self._rect.top = cols[0].bottom
                self.yvel = 0
        keys = pygame.key.get_pressed()
        xvel = 2
        if keys[g.ckeys["p left"]]:
            self._rect.x -= xvel
            self.direc = "left"
            if self.get_cols():
                self._rect.x += xvel
        if keys[g.ckeys["p right"]]:
            self._rect.x += xvel
            self.direc = "right"
            if self.get_cols():
                self._rect.x -= xvel
        if keys[g.ckeys["p up"]] and 0 < self.yvel < 1 and not self.in_air:
            self.yvel = self.jump_yvel
            self.in_air = True
        if self.in_air:
            self.spin_angle += 5
        self._rect.x += self.xvel
        # other important collisions with blocks
        """
        for block in all_blocks:
            if self.rect.colliderect(block.rect):
                # spike plant
                if bpure(block.name) == "bush":
                    if not self.invisible:
                        self.image.set_alpha(150)
                        self.invisible = True
                if bpure(block.name) == "spike plant":
                    self.take_dmg(0.03, 1, 1, "got spiked")
                elif bpure(block.name) == "lava":
                    self.take_dmg(0.07, 1, 1, "tried to swim in lava")
                # cactus
                if bpure(block.name) == "cactus":
                    self.take_dmg(0.03, 1, 0.5, "got spiked")
        """

    def camel_move(self, camel):
        self.rect.centerx = camel.centerx - 10
        self.rect.centery = camel.centery - 35
        self.energy += 0.001

    def gain_ground(self):
        pass

    def off_screen(self):
        if self._rect.right < 0:
            save_screen()
            self._rect.left = Window.width - 1
            if g.w.screen > 0:
                g.w.screen -= 1
            else:
                g.w.screen = len(g.w.data) - 1
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

        elif self._rect.left > Window.width:
            save_screen()
            self._rect.right = 1
            if g.w.screen == len(g.w.data) - 1:
                generate_screen(random.choice(bio.biomes))
            g.w.screen += 1
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

        elif self._rect.top > Window.height:
            save_screen()
            if g.w.layer <= 1:
                g.w.layer += 1
                self._rect.bottom = 1
                utilize_blocks()
            else:
                if g.w.mode == "adventure":
                    self.die("Fell into the void")
                else:
                    self._rect.y = 400
                    self.yvel = 0
            self.gain_ground()

        elif self._rect.bottom < 0:
            save_screen()
            if g.w.layer >= 1:
                g.w.layer -= 1
                self._rect.top = Window.height - 1
                utilize_blocks()
                self.gain_ground()

    def external_gravity(self):
        pass

    def animate(self):
        self.anim += g.p.anim_fps
        self.fdi = getattr(self, self.direc + "_images")
        try:
            self.fdi[int(self.anim)]
        except IndexError:
            self.anim = 0
        finally:
            self.image = self.fdi[int(self.anim)]


class Visual:
    def __init__(self):
        # misc
        self.following = True
        self.tool_range = 50
        self.moused = True
        # sword
        self.angle = 0
        self.to_swing = 0
        # domineering sword
        self.ds_last = perf_counter()
        self.init_ds()
        # grappling hook
        self.grapple_line = []
        # scope
        bw = 5
        self.scope_border_size = (80, 80)
        self.scope_border_img = pygame.Surface(self.scope_border_size, pygame.SRCALPHA)
        pygame.gfxdraw.aacircle(self.scope_border_img, *[s // 2 for s in self.scope_border_size], self.scope_border_size[0] // 2 - 1, BLACK)
        self.scope_inner_size = [s - bw - 5 for s in self.scope_border_size]
        self.scope_inner_img = pygame.Surface(self.scope_inner_size, pygame.SRCALPHA)
        pygame.draw.circle(self.scope_inner_img, DARK_GRAY, [s // 2 for s in self.scope_inner_size], self.scope_inner_size[0] // 2, bw, True, False, False, False)
        self.scope_angle = 0
        self.scope_inner_base = SmartSurface(self.scope_inner_size, pygame.SRCALPHA)
        self.reloading = False
        self.scope_yoffset = 12

    @property
    def facing_right(self):
        return g.mouse[0] > g.player.rect.centerx

    @property
    def sign(self):
        return 1 if self.facing_right else -1

    @property
    def mask(self):
        return pygame.mask.from_surface(self.image)

    def draw(self):
        Window.display.blit(self.image, self.rect)

    def update(self):  # visual update
        if g.stage == "play":
            if g.player.main == "block":
                if g.player.block:
                    self.og_img = g.w.blocks[g.player.block]
                    self.image = scale(self.og_img, [s // 2 for s in self.og_img.get_size()])
                    self.rect = self.image.get_rect()
                    if g.player.direc == "left":
                        self.rect.right = g.player.rect.left - 5
                    elif g.player.direc == "right":
                        self.rect.left = g.player.rect.right + 5
                    self.rect.centery = g.player.rect.centery
                    self.draw()

            elif g.player.main == "tool":
                if g.player.tool is not None:
                    self.following = True
                    self.og_img = g.w.tools[g.player.tool]
                    self.image = self.og_img.copy()
                    self.rect = self.image.get_rect()
                    if orb_names["white"] in g.player.tool:
                        self.following = False
                    if g.player.tool == "diamond_sword":
                        self.following = False
                        self.rect.center = g.player.rect.center
                    if "_" in g.player.tool:
                        # keyboard weapon
                        if self.following:
                            self.rect.center = g.mouse
                            # left
                            if g.player.rect.centerx - g.mouse[0] >= self.tool_range:
                                self.rect.centerx = g.player.rect.centerx - self.tool_range
                            # right
                            if g.mouse[0] - g.player.rect.centerx >= self.tool_range:
                                self.rect.centerx = g.player.rect.centerx + self.tool_range
                            # up
                            if g.player.rect.centery - g.mouse[1] >= self.tool_range:
                                self.rect.centery = g.player.rect.centery - self.tool_range
                            # down
                            if g.mouse[1] - g.player.rect.centery >= self.tool_range:
                                self.rect.centery = g.player.rect.centery + self.tool_range
                        glow_rect = pygame.Rect(*self.rect.topleft, 2, 2)
                        glow_rect.topleft = g.mouse

                        # controller weapon
                        if not self.moused:
                            if g.player.direc == "left":
                                self.rect.centerx = g.player.rect.centerx - 30
                            elif g.player.direc == "right":
                                self.rect.centerx = g.player.rect.centerx + 30
                            self.rect.centery = g.player.rect.centery
                            if g.player.tool_type not in unflipping_tools:
                                self.image, self.rect = rot_center(flip(self.og_img, True, g.player.direc == "left"), self.angle + 180 if g.player.direc == "left" else -self.angle, *self.rect.center)
                        if g.player.tool_type == "grappling-hook":
                            if self.rect.center != g.mouse:
                                self.image, self.rect = rot_center(self.og_img, -degrees(two_pos_to_angle(self.rect.center, g.mouse)) - 135, *self.rect.center)

                    if bpure(g.player.tool) == "bat":
                        if self.anticipate:
                            self.angle += (80 - self.angle) / 10
                            self.anticipation += 1
                            self.image, self.rect = rot_center(self.og_img, self.angle, self.rect.centerx, self.rect.centery)
                        #
                        self.rect.center = g.player.rect.center
                        if self.to_swing > 0:
                            try:
                                self.anim += 0.4
                                self.og_img = g.w.sprss["bat"][int(self.anim)]
                            except IndexError:
                                self.to_swing = 0
                            self.image, self.rect = rot_center(self.og_img, self.angle, self.rect.centerx, self.rect.centery)

                    if "_sword" in g.player.tool:
                        if self.to_swing <= 0:
                            for entity in g.w.entities:
                                if "mob" in entity.traits:
                                    entity.cooldown = False
                            # majestic
                            if orb_names["purple"] in g.player.tool:
                                group(SparkParticle(glow_rect, "circle-2", rot=0, speed=0), all_other_particles)
                                self.sword_log.append(glow_rect.center)
                                self.following = False
                                if len(self.sword_log) >= 30:
                                    del self.sword_log[0]
                            if orb_names["white"] in g.player.tool:
                                self.changeable = True
                                self.rect.center = g.player.rect.center
                                self.angle = -degrees(two_pos_to_angle(self.rect.center, g.mouse)) + 45 + 180
                                self.image, self.rect = rot_center(self.og_img, self.angle, *self.rect.center)
                                self.draw()
                                for entity in g.w.entities:
                                    if "mob" in entity.traits:
                                        entity.ray_cooldown = False
                                self.refl_line = None

                    elif "_bow" in g.player.tool:
                        self.og_img = g.w.tools[f"{g.player.tool}{int(self.bow_index)}"]
                        self.angle = -degrees(two_pos_to_angle(self.rect.center, g.mouse)) + 45 + 270
                        self.image, self.rect = rot_center(self.og_img, self.angle, *self.rect.center)
                        if orb_names["green"] in g.player.tool:
                            if len(self.bow_rt) < 2 or self.bow_index < 3:
                                ray_trace_bow()

                    if g.player.tool_type not in unflipping_tools:
                        self.image, self.rect = rot_center(self.image, self.angle, *self.rect.center)
                        self.image = flip(self.image, self.facing_right, False)

                    if is_en(g.player.tool):
                        if visual.to_swing > 0 or g.player.tool_type in unrotatable_tools or visual.bow_index > 0:
                            if chance(1 / 3):
                                group(SparkParticle(self.rect.center, "circle-4", rot=randf(-1, 1) / 100, color=getattr(pyengine.pgbasics, {v: k for k, v in orb_names.items()}[g.player.tool.split("_")[0]].upper())), all_other_particles)

                    if g.mouses[0]:
                        if g.player.tool == "diamond_sword":
                            if perf_counter() - self.ds_last >= (2 * pi) / self.ds_freq:
                                self.init_ds()
                                self.ds_last = perf_counter()
                            offset = trig_wave(perf_counter() * self.ds_freq, self.ds_width, self.ds_height, self.ds_theta, self.ds_xo, self.ds_yo)
                            self.rect.center = (g.mouse[0] + offset[0], g.mouse[1] + offset[1])

                    self.draw()

                if is_gun(g.player.tool):
                    if "scope" in g.mb.gun_attrs[g.player.tool]:
                        attr = ginfo["scope"][g.mb.gun_attrs[g.player.tool]["scope"].split("_")[0]]
                        color = attr[0]
                        block_radar = attr[1]
                        start_pos = g.player.rect.center
                        vel = list(two_pos_to_vel(g.player.rect.center, g.mouse, 10))
                        while math.hypot(vel[0], vel[1]) < math.hypot(Window.width, Window.height):
                            vel[0] *= 2
                            vel[1] *= 2
                        end_pos = [int(p + v) for p, v in zip(start_pos, vel)]
                        if block_radar:
                            for block in g.player.closest_blocks:
                                if block.name != "air":
                                    if block.rect.clipline(start_pos, end_pos):
                                        pygame.draw.rect(Window.display, GREEN, block.rect, 1)
                                        break
                        pygame.draw.aaline(Window.display, color, start_pos, end_pos)

                if self.grapple_line:
                    pygame.draw.aaline(Window.display, BROWN, *self.grapple_line)

    def init_ds(self):
        self.ds_freq = 25
        self.ds_width = gauss(100, 50)
        self.ds_height = gauss(100, 50)
        self.ds_theta = randf(0, 2 * pi)

    def swing_sword(self):
        def swing():
            time.sleep(0.4)
            self.to_swing = 220
            self.angle = -90 if g.mouse[0] < g.player.rect.centerx else 90
            shake_screen(5, 5)
        DThread(target=swing).start()

    def start_reloading(self):
        self.stop_reloading()
        self.reloading = True

    def stop_reloading(self):
        self.scope_angle = 0
        self.scope_inner_base = SmartSurface(self.scope_inner_size, pygame.SRCALPHA)
        self.reloading = False


class Block(Scrollable):
    def __init__(self, x, y, index):
        # metadata
        self.metadata = {}
        self.rock_width = 6 * R
        self.layer_index = index
        self.init_rock()
        self.utilize()
        # essential attrs
        self._rect = self.image.get_rect()
        self._rect.x = x
        self._rect.y = y
        self.width, self.height = self.rect.size
        self.broken = 0
        self.light = 1
        # crafting
        self.chest = None
        self.craftings = {}
        self.midblit_by_what = None  # list -> int (later)
        self.crafting_log = []
        self.craftable_index = 0
        self.craftables = SmartOrderedDict()
        # furnace
        self.burnings = SmartOrderedDict()
        self.furnace_log = []
        self.fuels = SmartOrderedDict()
        self.furnace_outputs = {}
        self.fuel_index = 0
        self.fuel_health = None
        # anvil
        self.smithings = {}
        self.smither = None
        self.smithable_index = 0
        self.smithables = SmartOrderedDict()
        self.anvil_log = []
        # gun crafter
        self.gun_parts = dict.fromkeys(g.tup_gun_parts, None)
        self.gun_attrs = {}
        self.gun_img = None
        self.gun_log = []
        # magic table
        self.magic_tool = None
        self.magic_orbs = {}
        self.magic_output = None
        self.magic_log = []
        # altar
        self.offerings = {}
        # jump pad
        self.energy = 10
        # lasts
        self.wheat_growth_time = 4

    @property
    def mask(self):
        return pygame.mask.from_surface(self.image)

    @property
    def abs_index(self):
        return self.layer_index + g.w.abs_blocki

    def update(self):
        #self.dynamic_methods()
        #self.check_not_hovering()
        self.draw()

    def check_not_hovering(self):
        if not is_in(self.name, tool_blocks):
            if not self.rect.collidepoint(g.mouse):
                self.broken = 0

    def draw(self):  # block draw
        """
        factor = hypot(g.mouse[0] - self.rect.centerx, g.mouse[1] - self.rect.centery)
        self.image = darken(self.og_img, 0.2)
        """
        Window.display.blit(self.image, self.rect)

    def try_breaking(self, type_="normal"):
        last_name = self.name
        drops = []
        eval_drop_pos = "[p + rand(-5, 5) for p in self.rect.center]"
        drop_pos = eval(eval_drop_pos)

        if bpure(self.name) == "leaf":
            if chance(1 / 200):
                group(LeafParticle(self.rect.center, g.w.wind), all_other_particles)

        if type_ == "normal":
            if non_bg(self.name) not in ore_blocks:
                breaking_time = apply(self.name, block_breaking_times, 500)
                if ticks() - g.last_break >= breaking_time:
                    self.broken += 1
                    if self.broken >= 5:
                        if is_in(self.name, dif_drop_blocks):
                            drops.append(Drop(dif_drop_blocks[non_bg(self.name)]["block"], drop_pos))
                        else:
                            drops.append(Drop(non_bg(self.name), drop_pos))
                    g.last_break = ticks()

        elif type_ == "tool":
            if get_tinfo(g.player.tool, self.name):
                self.broken += get_tinfo(g.player.tool, self.name)
                if chance(1 / 20):
                    group(BreakingBlockParticle(self.name, (self.rect.centerx, self.rect.top + rand(-2, 2))), all_particles)

            if self.broken >= 5:
                # block itself
                if is_in(self.name, dif_drop_blocks):
                    drops.append(Drop(dif_drop.blocks[non_bg(self.name)]["block"], drop_pos, self.name))
                else:
                    drops.append(Drop(non_bg(self.name), drop_pos))
                g.player.tool_healths[g.player.tooli] -= (11 - oinfo[tore(g.player.tool)]["mohs"]) / 8

        elif type_ == "freestyle":
            self.set("air")
            update_block_states()

        if self.broken >= 5:
            # extra drops
            if bpure(self.name) == "leaf":
                if chance(1 / 20):
                    drops.append(Drop("apple", drop_pos))
            elif bpure(self.name) == "chest":
                for name, amount in g.w.metadata[g.w.screen][self.abs_index]["chest"]:
                    if name is not None:
                        drops.append(Drop(name, drop_pos, amount))
                        drop_pos = eval(eval_drop_pos)
            # tiring
            pass
            # final
            g.player.broken_blocks[non_bg(self.name)] += 1
            data = g.w.get_data[g.w.screen]
            self.set("air")
            self.broken = 0
            update_block_states()

        if type_ in ("normal", "tool"):
            for drop in drops:
                group(drop, all_drops)

        if self.name != last_name:
            externally_update_entities()

    def bglized(self, name):
        return img_mult(g.w.blocks[name], 0.7)

    def bglize(self):
        self.image = img_mult(self.image, 0.7)

    def init_rock(self):
        self.metadata["rock"] = {"xoffset": rand(0, BS - self.rock_width), "hflip": not random.getrandbits(1)}

    def utilize(self):  # block utilize
        # inits
        self.name = g.w.get_data[g.w.screen][self.abs_index]
        if non_bg(self.name) != "rock":
            self.init_rock()
        # special cases
        if non_bg(self.name) == "rock":
            self.image = pygame.Surface((BS * 2, BS * 2), pygame.SRCALPHA)
            md = self.metadata["rock"]
            img = pygame.transform.flip(g.w.blocks["rock"], md["hflip"], False)
            md["xoffset"] = 0
            self.image.blit(img, (md["xoffset"], 0))
        else:
            # default
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            self.image.blit(g.w.blocks[non_bg(self.name)], (0, 0))
        # darkening _bg images
        if is_bg(self.name):
            self.image = darken(self.image, 0.6)
        # defaults again
        self.og_img = self.image.copy()
        self.update_state()
        # experimentals
        #self.image = scale2x(self.image)
        #self.image = rotate(self.image, rand(0, 360))

    def update_state(self):
        if non_bg(self.name) != "water":
            moore = all_blocks.moore(self.layer_index, HL, (2, 4, 6, 8))
            if is_in("water", [block.name for block in moore]):
                for block in moore:
                    if non_bg(block.name) == "water":
                        block.name = "water"
                        break
        self.last_wheat_growth = epoch()
        self.wheat_genetics = {"var": randf(-2, 2)}

    def dynamic_methods(self):
        if "dirt" in self.name:
            if all_blocks[self.layer_index - HL].name in walk_through_blocks:
                with AttrExs(self, "last_dirt", ticks()):
                    if ticks() - self.last_dirt >= 5000:
                        self.name = bio.blocks[g.w.biomes[g.w.screen]][0] + ("_bg" if "_bg" in self.name else "")

        if "wheat" in self.name:
            stage = int(self.name[-1])
            neis = g.w.get_data[g.w.screen].moore(self.abs_index, HL)
            speed = 1
            if bpure(neis[6]) == "soil":
                if stage < 4:
                    if not hasattr(self, "last_wheat_growth"):
                        self.last_wheat_growth = epoch()
                        self.wheat_genetics = {"var": randf(-2, 2)}
                    for i in (5, 7):
                        if bpure(neis[i]) == "water":
                            speed += 1
                    growth = int((epoch() - (self.last_wheat_growth + self.wheat_genetics["var"])) / (self.wheat_growth_time / speed))
                    if growth > 0:
                        self.set(f"wheat-st{min(stage + growth, 4)}")
                        self.last_wheat_growth = epoch()

    def set(self, name):
        g.w.get_data[g.w.screen][self.abs_index] = name
        self.utilize()

    def trigger(self):
        nwt = non_wt(self.name)
        ending = get_ending(self.name)
        if nwt in ("workbench", "furnace", "anvil", "gun-crafter", "magic-table", "altar"):
            g.midblit = non_bg(self.name)
            g.mb = self
            if nwt in ("workbench", "furnace", "gun-crafter"):
                g.player.main = "block"

        elif nwt == "water":
            if g.player.block == "bucket":
                g.player.new_block("water", 1)
                self.set("air")

        elif nwt == "portal-generator":
            pos = [roundn(p, 30) for p in g.player.rect.center]
            g.w.entities.append(Entity("portal", pos, g.w.screen, 1, traits=["portal"]))
            self.set("air")

        elif nwt == "dynamite":
            exploded_indexes = [
                                self.layer_index - 28, self.layer_index - HL, self.layer_index - 26,
                                self.layer_index - 1,  self.layer_index,      self.layer_index + 1,
                                self.layer_index + 26, self.layer_index + HL, self.layer_index + 28
                              ]
            for block in all_blocks:
                if block.layer_index != self.layer_index and block.layer_index in exploded_indexes and block.name == "dynamite":
                    block.trigger()
                elif block.layer_index in exploded_indexes:
                    block.set("air")
                    update_block_states()

        elif nwt == "command-block":
            def set_command(cmd):
                self.cmd = cmd
            Entry(Window.display, "Enter your command:", set_command, **g.def_entry_kwargs)

        elif nwt == "chest":
            g.midblit = "chest"
            g.chest = g.w.smetadata[self.abs_index]["chest"]

        elif "pipe" in self.name:
            rp = int(nwt.split("_deg")[1])
            if "curved" in nwt:
                self.set(f"curved-pipe_deg{rotations4[rp]}{ending}")
            else:
                self.set(f"pipe_deg{rotations2[rp]}{ending}")

        elif "stairs" in self.name:
            if "_deg" in self.name:
                rp = int(nwt.split("_deg")[1])
            else:
                rp = 0
            base_name = self.name.split("_deg")[0]
            name = f"{base_name}_deg{rotations4[rp]}{ending}"
            self.set(name)

        elif nwt in ("bed", "right-bed"):
            if g.w.dnc_index >= 540:
                g.w.dnc_index = nordis(50, 50)
                g.player.hunger -= 10
                g.player.energy = 100
            else:
                group(SlidePopup("You can only sleep when it's past 9 o'clock or your energy level is below 20", center=(Window.center, 0.5)), all_slidepopups)

        elif nwt == "closed-door":
            self.set("open-door" + ending)

        elif nwt == "open-door":
            self.set("closed-door" + ending)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, angle_data, speed, size, pierce=False):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(self.image, *[s // 2 for s in self.image.get_size()], size[0] // 2, BLACK)
        self.w, self.h = self.image.get_size()
        self.x, self.y = pos
        angle, angle_var = angle_data
        angle = radians(degrees(angle) + rand(-angle_var, angle_var))
        self.xvel, self.yvel = angle_to_vel(angle, speed)
        self.pierce = pierce

    @property
    def rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

    def collision(self):
        for block in g.player.closest_blocks:
            if block.name != "air":
                if block.rect.clipline((self.x, self.y), (self.last_x, self.last_y)):
                    block.set("air")
                    if not self.pierce:
                        self.kill()
                        break
        else:
            if self.x - self.w <= 0 or self.x >= Window.width or self.y - self.h <= 0 or self.y >= Window.height:
                self.kill()

    def draw(self):
        Window.display.blit(self.image, (self.x, self.y))

    def update(self):
        self.last_x = self.x
        self.last_y = self.y
        self.x += self.xvel
        self.y += self.yvel
        self.collision()
        self.draw()


class Drop(pygame.sprite.Sprite):
    def __init__(self, name, pos, extra=None):
        pygame.sprite.Sprite.__init__(self)
        self.name = name
        if extra is None:
            self.drop_amount = 1
        elif isinstance(extra, str):
            self.drop_amount = dif_drop_blocks[ipure(extra)]
        elif isinstance(extra, int):
            self.drop_amount = extra
        self.image = g.w.blocks[self.name].copy()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.image = scale(self.image, (self.width // 3, self.height // 3))
        self.rect = self.image.get_rect(center=pos)
        self.og_pos = self.rect.center
        self.screen = g.w.screen
        self.layer = g.w.layer

    def update(self):
        if is_drawable(self):
            Window.display.blit(self.image, self.rect)

    def kill(self):
        all_drops.remove(self)


class Hovering:
    __slots__ = ("image", "rect", "faulty", "show", "AWHITE", "ARED")

    def __init__(self):
        self.AWHITE = (255, 255, 255, 120)
        self.ARED = (255, 0, 0, 120)
        self.image = pygame.Surface((30, 30)).convert_alpha()
        self.image.fill(self.AWHITE)
        self.rect = self.image.get_rect()
        self.faulty = False
        self.show = True

    def draw(self):
        Window.display.blit(self.image, self.rect)

    def update(self):
        if not g.menu:
            self.faulty = False
            self.show = True
            if g.player.main == "block":
                for block in all_blocks:
                    if block.rect.collidepoint(g.mouse):
                        if g.player.item not in unplacable_blocks and g.player.item not in finfo:
                            if g.w.mode == "adventure":
                                if abs(g.player.rect.x - block.rect.x) // 30 > 3 or abs(g.player.rect.y - block.rect.y) // 30 > 3:
                                    self.faulty = True
                            if block.rect.collidepoint(g.mouse):
                                self.rect.center = block.rect.center
                        else:
                            self.show = False
                if self.faulty:
                    self.image.fill(self.ARED)
                else:
                    self.image.fill(self.AWHITE)
            else:
                self.show = False
        if self.show:
            self.draw()

    def update(self):
        if not g.menu:
            self.rect.topleft = [floorn(p, BS) for p in g.mouse]
        if self.show:
            self.draw()


class SlidePopup(pygame.sprite.Sprite):
    def __init__(self, text):
        pygame.sprite.Sprite.__init__(self)
        self.font = orbit_fonts[12]
        self.image = pygame.Surface(self.font.size(text), pygame.SRCALPHA)
        write(self.image, "center", text, self.font, BLACK, *[s / 2 for s in self.image.get_size()])
        self.rect = self.image.get_rect(center=(Window.width - 110, 100))
        self.alpha = 255

    def update(self):
        self.rect.y -= 1
        self.alpha -= 2
        self.image.set_alpha(self.alpha)
        if self.alpha <= 0:
            self.kill()


class BreakingBlockParticle(pygame.sprite.Sprite):
    def __init__(self, name, pos):
        pygame.sprite.Sprite.__init__(self)
        try:
            self.image = g.w.blocks[non_bg(name)]
            self.width = self.image.get_width()
            self.height = self.image.get_height()
            self.image = scale(self.image, (self.width // 4, self.height // 4))
        except AttributeError:
            self.image = name.copy()
        self.rect = self.image.get_rect(center=pos)
        self.xvel = rand(-2, 2)
        self.yvel = -3
        self.start_time = ticks()

    def update(self):
        self.yvel += 0.3
        self.rect.x += self.xvel
        self.rect.y += self.yvel
        if ticks() - self.start_time >= 200:
            self.kill()


class SparkParticle:
    def __init__(self, pos, diameter):
        self.image = circle(diameter // 2, rgb_mult(PURPLE, randf(0.8, 1.2)))
        self.x, self.y = pos
        self.radius = diameter // 2
        self.angle = rand(-360, 360)
        self.direc = randf(-1, 1) / 100
        self.speed = 0.5

    @property
    def xvel(self):
        return angle_to_vel(self.angle, self.speed)[0]

    @property
    def yvel(self):
        return angle_to_vel(self.angle, self.speed)[1]

    def update(self):
        #pygame.gfxdraw.filled_circle(Window.display, int(self.x), int(self.y), int(self.radius), WHITE)
        self.x += self.xvel
        self.y += self.yvel
        self.angle += self.direc
        self.radius -= 0.07
        Window.display.blit(self.image, (self.x, self.y))
        if self.radius <= 0:
            all_other_particles.remove(self)


class LeafParticle:
    def __init__(self, pos, wind):
        self.image = leaf_img
        self.og_img = self.image.copy()
        self.width, self.height = self.image.get_size()
        self.x, self.y = pos
        self.wind = tuple(wind)
        self.xvel = randf(-0.1, 0.1)
        self.yvel = randf(-0.1, 0.1)
        self.angle = 0
        self.avel = randf(-3, 3)

    def update(self):
        self.xvel += self.wind[0]
        self.yvel += self.wind[1]
        self.x += self.xvel
        self.y += self.yvel
        if self.x + self.width <= 0 or self.x >= Window.width or self.y + self.height <= 0 or self.y >= Window.height:
            all_other_particles.remove(self)
        self.angle += self.avel
        self.image = pygame.transform.rotozoom(self.og_img, self.angle, 1)
        Window.display.blit(self.image, (self.x, self.y))


class FollowParticle:
    def __init__(self, img, start_pos, end_pos):
        self.image = img
        self.x, self.y = start_pos
        self.end_x, self.end_y = [int(p) for p in end_pos]
        self.xvel, self.yvel = two_pos_to_vel(start_pos, end_pos)

    def draw(self):
        Window.display.blit(self.image, (self.x, self.y))

    def update(self):
        self.x += self.xvel
        self.y += self.yvel
        if int(self.x) == self.end_x and int(self.y) == self.end_y:
            all_other_particles.remove(self)
        self.draw()


class InfoBox(pygame.sprite.Sprite):
    def __init__(self, texts, pos=None, index=0):
        # init
        pygame.sprite.Sprite.__init__(self)
        self.padding = 20
        self.index = index
        text = texts[self.index]
        self.og_text = text
        self.texts = texts
        self.text = ""
        self.pos = pos if pos is not None else (Window.width / 2, Window.height / 2 - 100)
        self.font = orbit_fonts[16]
        # self image
        self.image = pygame.Surface([s + self.padding for s in self.font.size(text)], pygame.SRCALPHA).convert_alpha()
        br = 10
        pygame.draw.rect(self.image, LIGHT_GRAY, (0, 0, *self.image.get_size()), 0, br)
        pygame.draw.rect(self.image, DARK_GRAY, (0, 0, *self.image.get_size()), 3, br)
        self.rect = self.image.get_rect(topleft=self.pos)
        self.width, self.height = self.rect.size
        # continue image
        self.con_image = pygame.Surface((80, 30), pygame.SRCALPHA).convert_alpha()
        br = 10
        pygame.draw.rect(self.con_image, LIGHT_GRAY, (0, 0, *self.con_image.get_size()), 0, br)
        pygame.draw.rect(self.con_image, DARK_GRAY, (0, 0, *self.con_image.get_size()), 3, br)
        self.con_rect = self.con_image.get_rect(topright=(self.rect.right, self.rect.bottom))
        # rest
        self.alpha = 0
        self.bg_alpha = ceil(255 / 4)
        self.last_init = float("inf")
        self.can_skip = False
        self.show()

    def update(self):
        Window.display.blit(self.image, self.rect)
        text_surf, text_rect = write(Window.display, "topleft", self.text, self.font, BLACK, *[p + self.padding / 2 for p in self.rect.topleft], blit=False)
        # text_surf.set_alpha(self.alpha * (255 / self.bg_alpha))
        Window.display.blit(text_surf, text_rect)
        if epoch() - self.last_init >= 1:
            # self.con_image.set_alpha(self.alpha)
            Window.display.blit(self.con_image, self.con_rect)
            text_surf, text_rect = write(Window.display, "topleft", "[SPACE]", orbit_fonts[12], BLACK, *[p + self.padding / 2 for p in self.con_rect.topleft], blit=False)
            # text_surf.set_alpha(self.alpha * (255 / self.bg_alpha))
            Window.display.blit(text_surf, text_rect)

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.can_skip:
                    with suppress(IndexError):
                        group(InfoBox(self.texts, self.pos, self.index + 1), all_foreground_sprites)
                    all_foreground_sprites.remove(self)

    def show(self):
        def _show():
            for _ in range(self.bg_alpha):
                # self.image.set_alpha(self.alpha)
                time.sleep(WOOSH_TIME * 6)
                self.alpha += 1
            self.characterize()
            self.can_skip = True
        DThread(target=_show).start()

    def characterize(self):
        def _characterize():
            for char in self.og_text:
                self.text += char
                time.sleep(WOOSH_TIME * 30)
            self.last_init = epoch()
        DThread(target=_characterize).start()


class WorldButton(pygame.sprite.Sprite):
    def __init__(self, data, text_color=BLAC):
        # init
        pygame.sprite.Sprite.__init__(self)
        self.data = data.copy()
        self.text_color = text_color
        w, h = orbit_fonts[20].size(str(data["world"]))
        w, h = 120, g.worldbutton_pos_ydt - 5
        w, h = MHL / 2, MVL / 2
        w, h = wb_icon_size
        # image
        #self.image = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        #pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        #pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        #self.image.set_colorkey(BLACK)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        br = 3
        pygame.draw.rect(self.image, (110, 110, 110), (0, wb_icon_size[1] - 30, wb_icon_size[0], 30), 0, 0, -1, -1, br, br)
        write(self.image, "bottomleft", data["world"], orbit_fonts[20], self.text_color, 5, self.image.get_height() - 3)
        # rest
        self.rect = self.image.get_rect(topleft=data["pos"])
        if "bg" in self.data:
            self.init_bg(SmartSurface.from_string(self.data["bg"], self.data["bg_size"]), self.data["username"])

    def init_bg(self, bg, username):
        bgw, bgh = bg.get_size()
        self.image.blit(bg, (0, 0))
        write(self.image, "midtop", username, orbit_fonts[11], BLACK, bgw / 2, 3)
        self.data["bg"] = deepcopy(SmartSurface.from_surface(bg))
        self.data["bg_size"] = bg.get_size()

    def overwrite(self, inputtext, name=False):
        if name:
            g.p.world_names.remove(self.data["world"])
            g.p.world_names.append(inputtext)
            self.data["world"] = inputtext
        w, h = orbit_fonts[20].size(str(inputtext))
        self.image = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA).convert_alpha()
        pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        write(self.image, "center", inputtext, orbit_fonts[20], self.text_color, *[s / 2 for s in self.image.get_size()])
        self.rect = self.image.get_rect(topleft=self.rect.topleft)


class StaticWidget:
    def __init__(self, grp, visible_when):
        group(self, grp)
        self.visible_when = visible_when


class StaticButton(pygame.sprite.Sprite, StaticWidget):
    def __init__(self, text, pos, group, bg_color=WHITE, text_color=BLAC, anchor="center", size="icon", shape="crect", sharp_width=0, command=None, visible_when=None):
        pygame.sprite.Sprite.__init__(self)
        StaticWidget.__init__(self, group, visible_when)
        if size == "world":
            tw, th = 225, 24
        else:
            tw, th = orbit_fonts[20].size(text)
        w, h = tw + 10, th + 10
        if shape == "sharp":
            w += 50 + sharp_width
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image.set_colorkey(BLACK)
        # pygame.draw.rect(self.image, bg_color, (0, 0, *self.image.get_size()), 0, 10, 10, 10, 10)
        # pygame.draw.rect(self.image, DARK_BROWN, (0, 0, *self.image.get_size()), 2, 10, 10, 10, 10)
        color = (80, 80, 80)
        br = 6
        if shape == "rect":
            self.image.fill(color)
        elif shape == "crect":
            pygame.draw.rect(self.image, color, (0, 0, *self.image.get_size()), 0, br, br, br, br)
        elif shape == "sharp":
            sw = 50
            pygame.draw.polygon(self.image, (100, 100, 100), [(0, 0), (w, 0), (w, h), (sw, h)])
            pygame.gfxdraw.aapolygon(self.image, [(0, 0), (w - 1, 0), (w - 1, h - 1), (sw, h - 1)], color)
        self.text_color = text_color
        if shape == "sharp":
            wx = w / 2 + sw / 2
            wy = h / 2
        else:
            wx, wy = w / 2, h / 2
        write(self.image, "center", text, orbit_fonts[20], self.text_color, wx, wy)
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
        write(self.image, "topleft", text, orbit_fonts[20], self.text_color, 5, 5)


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
        self.image.cblit(rotozoom(triangle(12), 180, 1), (w - 20, h / 2))
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
        self.image = SmartSurface((300, 200)).convert_alpha()
        bg_color = list(DARKISH_GREEN) + [130]
        self.image.fill(bg_color)
        self.rect = self.image.get_rect(topleft=(Window.width / 2 - 150, Window.height / 2 - 100))
        self.text_height = orbit_fonts[20].size("J")[1]
        self.box_size = (self.rect.width / 2 - 15, self.text_height + 10)
        box = pygame.Surface(self.box_size).convert_alpha()
        self.box_writing_pos = (box.get_width() / 2, box.get_height() / 2)
        pygame.draw.rect(self.image, DARKISH_GREEN, (0, 0, *self.image.get_size()), 4)
        self.close_rects = {}
        # close boxes
        write(self.image, "midtop", "?", orbit_fonts[30], BLACK, self.rect.width / 2, 5)
        w, h = self.image.get_size()
        self.get_box("Info", (10, h - 90), "bottomleft")
        self.get_box("Download", (10, h - 50), "bottomleft")
        self.get_box("Rename", (w - 10, h - 50), "bottomright")
        self.get_box("Open", (10, h - 10), "bottomleft")
        self.get_box("Delete", (w - 10, h - 10), "bottomright")
        # animation
        Thread(target=self.zoom, args=["in"]).start()

    @property
    def path(self):
        return path(".game_data", "worlds", self.data["world"] + ".dat")

    def get_box(self, text, pos, anchor):
        box = pygame.Surface(self.box_size).convert_alpha()
        box_size = box.get_size()
        self.close_rects[text.lower()] = box.get_rect(**{anchor: [m + p for m, p in zip(self.rect.topleft, pos)]})
        pygame.draw.rect(box, CREAM, (0, 0, *self.box_size))
        pygame.draw.rect(box, LIGHT_GRAY, (0, 0, *self.box_size), 4)
        write(box, "center", text, orbit_fonts[20], BLACK, *self.box_writing_pos)
        self.image.cblit(box, pos, anchor)

    def zoom(self, type_):
        og_img = self.image.copy()
        og_size = og_img.get_size()
        if type_ == "in":
            for i in range(20):
                size = [round((fromperc((i + 1) * 5, s))) for s in og_size]
                self.image = scale(og_img, size)
                self.rect = self.image.get_rect()
                self.rect.center = (Window.width / 2, Window.height / 2)
                time.sleep(WOOSH_TIME)
        elif type_ == "out":
            for i in reversed(range(20)):
                size = [round(fromperc((i + 1) * 5, s)) for s in og_size]
                self.image = scale(og_img, size)
                self.rect = self.image.get_rect()
                self.rect.center = (Window.width / 2, Window.height / 2)
                time.sleep(WOOSH_TIME)
            self.kill()

    def get_info(self, key=None):
        with open(path(".game_data", "worldbuttons.dat"), "rb") as f:
            button_attrs = pickle.load(f)
            for attr in button_attrs:
                if attr["world"] == self.data["world"]:
                    w = attr["world_obj"]
                    return w.info[key] if key is not None else w.info

    def set_info(self, key, value):
        with open(path(".game_data", "worldbuttons.dat"), "rb") as f:
            button_attrs = pickle.load(f)
            for attr in button_attrs:
                if attr["world"] == self.data["world"]:
                    w = attr["world_obj"]
                    setattr(w["info"], key, value)
                    break

    def close(self, option):
        if option == "info":
            MessageboxOk(Window.display, "\n", **g.def_widget_kwargs)

        elif option == "download":
            with open(self.path, "rb") as f:
                world_data = pickle.load(f)
            dir_ = tkinter.filedialog.asksaveasfilename()
            name = dir_.split(".")[0]
            with open(name + ".dat", "wb") as f:
                pickle.dump(world_data, f)

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
                                os.rename(path(".game_data", "worlds", self.data["world"] + ".dat"), path(".game_data", "worlds", ans_rename + ".dat"))
                                for button in all_home_world_world_buttons:
                                    if button.data["world"] == self.data["world"]:
                                        button.overwrite(ans_rename, True)
                                        button.data["world_obj"].name = ans_rename
                                        break
                        else:
                            MessageboxError(Window.display, "A world with the same name already exists.", **g.def_widget_kwargs)
                    else:
                        MessageboxError(Window.display, "World name is invalid.", **g.def_widget_kwargs)

            Entry(Window.display, "Rename world to:", rename, **g.def_entry_kwargs)

        elif option == "open":
            with open(self.path, "rb") as f:
                # world assets
                world_data = pickle.load(f)
                g.w = self.data["world_obj"]
                with suppress(BreakAllLoops):
                    for atype, dict_ in g.w.assets.items():
                        for name, string in dict_.items():
                            try:
                                g.w.assets[atype][name] = SmartSurface.from_string(string, g.w.asset_sizes[name])
                            except TypeError:
                                raise BreakAllLoops
                # world entities
                for entity in g.w.entities:
                    entity.images = [SmartSurface.from_string(entity.image, entity.sizes[i]) for i, image in enumerate(entity.images)]
                    entity.image = entity.images[int(entity.anim)]
                    #entity.init_mask()
                # player
                g.player = self.data["player_obj"]
                g.player.left_images = [SmartSurface.from_string(img, g.player.size) for img in g.player.left_images]
                g.player.right_images = [SmartSurface.from_string(img, g.player.size) for img in g.player.right_images]
                with suppress(IndexError):
                    mm1 = g.player.moving_mode[1]
                    if isinstance(mm1, Entity):
                        g.player.moving_mode[1] = SmartSurface.from_string(mm1)
                # world
                generate_world(world_data)
                init_world("existing")
                # general
                destroy_widgets()
                g.menu = False

        elif option == "delete":
            delete_file(path(".game_data", "worlds", self.data["world"] + ".dat"))
            g.p.world_names.remove(self.data["world"])
            for button in all_home_world_world_buttons:
                if button.rect.y > self.data["pos"][1]:
                    button.rect.y -= g.worldbutton_pos_ydt
                    button.data["pos"][1] -= g.worldbutton_pos_ydt
                elif button.data == self.data:
                    button.kill()
            g.p.next_worldbutton_pos[1] -= g.worldbutton_pos_ydt

        elif g.debug:
            raise ValueError(f"'{option}'")

        self.kill()


# I N I T I A L I Z I N G  S P R I T E S -------------------------------------------------------------- #
g.player = Player()
visual = Visual()
hov = Hovering()

button_cnw = StaticButton("Create New World", (45, Window.height - 160), all_home_world_static_buttons, LIGHT_BROWN, anchor="topleft", size="world", command=new_world, visible_when=pw.is_worlds_worlds)
button_lw = StaticButton("Load World", (45, Window.height - 120), all_home_world_static_buttons, LIGHT_BROWN, anchor="topleft", size="world", command=pw.load_world_command, visible_when=pw.is_worlds_worlds)
button_daw = StaticButton("Delete All Worlds", (45, Window.height - 80), all_home_world_static_buttons, LIGHT_BROWN, anchor="topleft", size="world", command=pw.button_daw_command, visible_when=pw.is_worlds_worlds)
button_c = StaticButton("Credits", (35, 130), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", command=pw.show_credits_command, visible_when=pw.is_worlds_static)
button_i = StaticButton("Intro", (35, 170), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", command=pw.intro_command, visible_when=pw.is_worlds_static)
button_ct = StaticButton("Custom Textures", (35, 210), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", command=pw.custom_textures_command, visible_when=pw.is_worlds_static)
button_dl = StaticButton("Download Language", (35, 250), all_home_settings_buttons, LIGHT_BROWN, anchor="topleft", command=pw.download_language_command, visible_when=pw.is_worlds_static)
button_s = StaticButton("Settings", (Window.width - 40, 50), all_home_sprites, GRAY, shape="sharp", sharp_width=40, anchor="midright", command=pw.set_home_stage_settings_command, visible_when=pw.is_home)
button_w = StaticButton("Worlds", (Window.width - 40, 90), all_home_sprites, GRAY, shape="sharp", anchor="midright", command=pw.set_home_stage_worlds_command, visible_when=pw.is_home)

# L O A D I N G  T H E  G A M E ----------------------------------------------------------------------- #
# load buttons
if os.path.getsize(path(".game_data", "worldbuttons.dat")) > 0:
    with open(path(".game_data", "worldbuttons.dat"), "rb") as f:
        attrs = pickle.load(f)
        for attr in attrs:
            group(WorldButton(attr), all_home_world_world_buttons)

# debugging stuff
late_rects = []
late_pixels = []
late_lines = []
late_imgs = []
last_qwe = perf_counter()


# M A I N  L O O P ------------------------------------------------------------------------------------ #
def main(debug):
    with nullcontext() if debug else redirect_stdout(open(os.devnull, "w")):
        # # cursors
        # set_cursor_when(pygame.SYSTEM_CURSOR_ARROW, lambda: g.mb.crafting is not None)
        # set_cursor_when(pygame.SYSTEM_CURSOR_CROSSHAIR, lambda: g.stage == "play")
        # set_cursor_when(pygame.SYSTEM_CURSOR_ARROW, lambda: g.stage != "play")
        # lasts
        last_rain_partice = ticks()
        last_snow_particle = ticks()
        last_gunfire = ticks()
        last_s = ticks()
        # dynamic stuff
        music_count = None
        # static stuff
        t = GoogletransTranslator()
        # counts
        g.stage = "home"
        # end signals
        pass
        # loop
        running = True
        pritn()
        loading_time = round(perf_counter(), 2)
        g.p.loading_times.append(loading_time)
        pritn(f"Loaded in: {loading_time}s")
        pritn(f"Average loading time: {round(g.p.loading_times.mean, 2)}s")
        pritn()
        pygame.display.set_caption("\u15FF"   # because
                                   "\u0234"   # because
                                   "\u1F6E"   # because
                                   "\u263E"   # because
                                   "\u049C"   # because
                                   "\u0390"   # because
                                   "\u2135"   # because
                                   "\u0193"   # because
                                   "\u15EB"   # because
                                   "\u03A6"   # because
                                   "\u722A")  # because
        # game loop
        while running:
            # fps cap
            g.dt = g.clock.tick(pw.fps_cap.value) / (1000 / 120)
            #t.init(g.w.language)

            # global dynamic variables
            g.p.anim_fps = pw.anim_fps.value / g.fps_cap
            g.process_messageboxworld = True

            # music
            if g.stage == "play":
                volume = pw.volume.value / 100
            elif g.stage == "home":
                volume = 0
            set_volume(volume)
            g.p.volume = volume
            if not pygame.mixer.music.get_busy():
                pw.next_piece_command()

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # mechanical events
                if not g.events_locked:
                    process_widget_events(event, g.mouse)
                    for fgs in all_foreground_sprites:
                        if hasattr(fgs, "process_event") and callable(fgs.process_event):
                            fgs.process_event(event)

                    if event.type == KEYDOWN:
                        # debugging
                        if event.key == K_SPACE:
                            #group(FollowParticle(g.w.blocks["soil_f"], g.mouse, g.player.rect.center), all_other_particles)
                            pass

                        if event.key == K_q:
                            group(InfoBox(["Hey, another fellow traveler!", "ok you can go now"]), all_foreground_sprites)

                        # actual gameplay events
                        if g.stage == "play":
                            if no_widgets(Entry):
                                if event.key == pygame.K_TAB:
                                    toggle_main()

                                if g.midblit == "workbench":
                                    if event.key == K_SPACE:
                                        if g.player.block :
                                            if g.player.block in g.mb.craftings:
                                                g.mb.craftings[g.player.block] += 1 if g.mod != K_OSC else g.player.amount - g.mb.craftings[g.player.block]
                                                g.mb.crafting_log.append(g.player.block)
                                            else:
                                                g.mb.craftings[g.player.block] = 1 if g.mod != K_OSC else g.player.amount
                                                g.mb.crafting_log.append(g.player.block)
                                            g.player.use_up_inv()
                                            show_added(g.mb.crafting_log[-1])

                                    elif event.key == K_ENTER:
                                        for craftable, amount in g.mb.craftables.items():
                                            if g.player.stats["xp"]["amount"] >= cinfo[craftable].get("xp", 0):
                                                if g.player.stats["energy"]["amount"] - cinfo[craftable].get("energy", 0) >= 0:
                                                    g.player.stats["energy"]["amount"] -= cinfo[craftable].get("energy", 0)
                                                    if craftable in g.w.blocks:
                                                        g.player.new_block(craftable, amount)
                                                    else:
                                                        g.player.new_tool(craftable)
                                                    stop_midblit("workbench")

                                    elif event.key == K_BACKSPACE:
                                        if g.mb.crafting_log:
                                            if None in g.player.inventory:
                                                g.mb.craftings[g.mb.crafting_log[-1]] -= 1
                                                if g.mb.craftings[g.mb.crafting_log[-1]] == 0:
                                                    del g.mb.craftings[g.mb.crafting_log[-1]]
                                                g.player.new_block(g.mb.crafting_log[-1])
                                                del g.mb.crafting_log[-1]

                                elif g.midblit == "furnace":
                                    if event.key == K_SPACE:
                                        if g.player.block:
                                            if g.player.block not in fuinfo:
                                                if g.player.block in g.burnings:
                                                    if g.player.amount - g.burnings[g.player.block] > 0:
                                                        g.burnings[g.player.block] += 1 if g.mod != K_OSC else g.player.amount - g.mb.craftings[g.player.block]
                                                else:
                                                    g.burnings[g.player.block] = 1 if g.mod != K_OSC else g.player.amount
                                                g.furnace_log.append(g.player.block)
                                                show_added(g.furnace_log[-1])
                                            else:
                                                if g.player.block in g.fuels:
                                                    if g.player.amount - g.fuels[g.player.block] > 0:
                                                        g.fuels[g.player.block] += 1 if g.mod != K_OSC else g.player.amount - g.mb.craftings[g.player.block]
                                                else:
                                                    g.fuels[g.player.block] = 1 if g.mod != K_OSC else g.player.amount
                                                g.furnace_log.append(g.player.block)
                                            if not g.fuels:
                                                g.fuel_health = 100
                                            g.player.use_up_inv()

                                    elif event.key == K_BACKSPACE:
                                        if g.furnace_log:
                                            if None in g.player.inventory:
                                                g.player.new_block(g.furnace_log[-1], 1)
                                                if g.furnace_log[-1] not in fuinfo:
                                                    g.burnings[g.furnace_log[-1]] -= 1
                                                    if g.burnings[g.furnace_log[-1]] == 0:
                                                        del g.burnings[g.furnace_log[-1]]
                                                else:
                                                    g.fuels[g.furnace_log[-1]] -= 1
                                                    if g.fuels[g.furnace_log[-1]] == 0:
                                                        g.fuels.delval(g.furnace_log[-1])
                                                del g.furnace_log[-1]

                                elif g.midblit == "anvil":
                                    if event.key == K_SPACE:
                                        if g.player.main == "tool":
                                            if g.player.tool is not None:
                                                if is_smither(g.player.tool):
                                                    g.smither = g.player.tool
                                                    g.anvil_log.append(g.player.tool)
                                        elif g.player.main == "block":
                                            if g.player.block:
                                                if g.player.block not in g.smithings:
                                                    g.smithings[g.player.block] = 1
                                                else:
                                                    g.smithings[g.player.block] += 1
                                                g.player.use_up_inv()
                                                g.anvil_log.append(g.player.block)

                                    elif event.key == K_BACKSPACE:
                                        if g.anvil_log:
                                            if not is_smither(g.anvil_log):
                                                if None in g.player.inventory:
                                                    g.player.new_block(g.anvil_log[-1])
                                                    del g.anvil_log[-1]
                                            else:
                                                if None in g.player.tools:
                                                    g.player.empty_tool = g.anvil_log[-1]
                                                    del g.anvil_log[-1]

                                    elif event.key == K_ENTER:
                                         if g.smithable is not None:
                                            if g.player.stats["xp"]["amount"] >= ainfo[g.smithable].get("xp", 0):
                                                if g.player.stats["energy"]["amount"] - ainfo[g.smithable].get("energy", 0) >= 0:
                                                    g.player.stats["energy"]["amount"] -= ainfo[g.smithable].get("energy", 0)
                                                    if smithable in g.w.blocks:
                                                        g.player.new_block(g.smithable, g.mb.craft_by_what)
                                                    else:
                                                        g.player.new_tool(g.smithable)

                                elif g.midblit == "gun-crafter":
                                    if event.key == K_SPACE:
                                        if g.player.block in gun_blocks:
                                            g.mb.gun_parts[g.player.block.split("_")[1]] = g.player.block
                                            g.mb.gun_log.append(g.player.block.split("_")[1])
                                            g.player.use_up_inv(g.player.blocki, 1)
                                            show_added(g.mb.gun_log[-1])

                                    elif event.key == K_ENTER:
                                        if is_gun_craftable():
                                            """
                                            g.mb.gun_img = Window.display.subsurface(*crafting_abs_pos, *crafting_eff_size)
                                            g.mb.gun_img = real_colorkey(g.mb.gun_img, LIGHT_GRAY)
                                            g.mb.gun_img = crop_transparent(g.mb.gun_img)
                                            g.mb.gun_img = scalex(g.mb.gun_img, 0.7)
                                            g.mb.gun_img = gun_crafter_base
                                            """
                                            g.mb.gun_img = pygame.Surface((20, 20))
                                            Entry(Window.display, "Custom gun name:", custom_gun, **g.def_entry_kwargs, input_required=True)

                                    elif event.key == K_BACKSPACE:
                                        pass

                                elif g.midblit == "magic-table":
                                    if event.key == K_SPACE:
                                        if g.player.main == "tool":
                                            if g.player.tool is not None:
                                                g.magic_tool = g.player.tool
                                            show_added(g.magic_tool)
                                        elif g.player.main == "block":
                                            if g.player.block:
                                                if g.player.block.endswith("-orb"):
                                                    if g.player.block in g.magic_orbs:
                                                        g.magic_orbs[g.player.block] += 1
                                                    else:
                                                        g.magic_orbs[g.player.block] = 1
                                                    show_added(g.player.block)
                                                    g.player.use_up_inv(g.player.blocki)

                                    elif event.key == K_ENTER:
                                        _r = []
                                        _g = []
                                        _b = []
                                        for name, amount in g.magic_orbs.items():
                                            color = getattr(pyengine.pgbasics, name.removesuffix("-orb").upper())
                                            _r.append(color[0])
                                            _g.append(color[1])
                                            _b.append(color[2])
                                        color = (sum(_r) / len(_r), sum(_g) / len(_g), sum(_b) / len(_b))
                                        filter = pygame.Surface((30, 30))
                                        filter.fill(color)
                                        filter.set_alpha(125)
                                        tool_name = f"enchanted_{g.player.tool}"
                                        g.w.tools[tool_name] = g.w.tools[g.player.tool].copy()
                                        g.w.tools[tool_name].blit(filter, (0, 0), special_flags=BLEND_RGB_MULT)
                                        g.player.tool = tool_name
                                        g.player.tool_health = 100
                                        stop_midblit("magic")
                                        #g.w.tools[tool_name] = SmartSurface.from_surface(pil_to_pg(PIL.ImageEnhance.Contrast(pg_to_pil(g.w.tools[g.player.tool].copy())).enhance(1.2)))

                                elif g.midblit == "chest":
                                    if g.player.main == "block":
                                        if event.key == K_BACKSPACE:
                                            if None in g.player.inventory:
                                                if g.cur_chest_item != (None, None):
                                                    g.cur_chest_item[1] -= 1
                                                    g.player.new_block(g.cur_chest_item[0])
                                                    if g.cur_chest_item[1] == 0:
                                                        g.cur_chest_item = (None, None)
                                        elif event.key == K_SPACE:
                                            if g.player.amount is not None and g.player.amount > 0:
                                                if g.cur_chest_item[0] in g.player.inventory:
                                                    g.cur_chest_item[1] += 1
                                                    g.player.use_up_inv()
                                                elif g.cur_chest_item[0] is None:
                                                    g.cur_chest_item[0] = g.player.block
                                                    g.cur_chest_item[1] += 1
                                                    g.player.use_up_inv()

                                elif event.key in (K_SPACE, K_TAB):
                                    toggle_main()

                                if event.key == K_c:
                                    Entry(Window.display, "Enter your command:", player_command, **g.def_entry_kwargs)

                                elif event.key == K_p:
                                    g.player.cust_username()

                                elif event.key == K_l:
                                    Entry(Window.display, "Enter language:", custom_language, **g.def_entry_kwargs)

                                elif event.key == K_s:
                                    if g.w.mode == "freestyle":
                                        if ticks() - last_s <= 200:
                                            if g.player.moving_mode == ["freestyle"]:
                                                g.player.set_moving_mode("adventure")
                                            elif g.player.moving_mode == ["adventure"]:
                                                g.player.set_moving_mode("freestyle")
                                            last_s = ticks()
                                        else:
                                            for block in all_blocks:
                                                if is_in(block.name, functionable_blocks):
                                                    if hov.rect.topleft == block.rect.topleft:
                                                        if not hov.faulty:
                                                            block.trigger()
                                                            break
                                        last_s = ticks()

                                elif event.key == K_r:
                                    if is_gun(g.player.tool):
                                        if g.player.tool_ammo < get_gun_info(g.player.tool, "magazine")["size"]:
                                            visual.start_reloading()

                                elif event.key == K_ESCAPE:
                                    if not g.midblit:
                                        settings()
                                    else:
                                        stop_midblit()

                                elif event.key == K_ENTER:
                                    for messagebox in all_messageboxes:
                                        messagebox.close("open")

                                elif g.player.main == "block" and pygame.key.name(event.key) in ("1", "2", "3", "4", "5"):
                                    g.player.indexes["block"] = int(pygame.key.name(event.key)) - 1
                                elif g.player.main == "tool" and pygame.key.name(event.key) in ("1", "2"):
                                    g.player.indexes["tool"] = int(pygame.key.name(event.key)) - 1

                    elif event.type == pygame.KEYUP:
                        if event.key == g.ckeys["p up"]:
                            if g.player.yvel < 0:
                                g.player.yvel /= 3

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            mousebuttondown_event()

                        elif event.button == 3:
                            if g.stage == "play":
                                if g.player.main == "block":
                                    if any(g.player.block.endswith(x) for x in {"helmet", "chestplate", "leggings"}):
                                        armor = g.player.block.split("_")[-1]
                                        g.player.armor[armor] = g.player.block

                                for block in all_blocks:
                                    if block.rect.collidepoint(g.mouse):
                                        if not hov.faulty:
                                            block.trigger()

                                for entity in g.w.entities:
                                    if no_widgets(Entry):
                                        if entity.rect.collidepoint(g.mouse):
                                            if is_drawable(entity):
                                                if "portal" in entity.traits and is_drawable(entity):
                                                    if not g.w.linked:
                                                        MessageboxOkCancel(Window.display, "Are you sure you want to link worlds?", g.player.link_worlds, ok="Yes", no_ok="No", **g.def_widget_kwargs)
                                                elif "camel" in entity.traits:
                                                    if g.player.moving_mode[0] != "camel":
                                                        g.player.set_moving_mode("camel", entity)
                                                    else:
                                                        g.player.set_moving_mode(g.player.last_moving_mode[0])

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            g.first_affection = None
                            g.clicked_when = None
                            for block in all_blocks:
                                block.broken = 0

                            if g.stage == "play":
                                g.player.food_pie = g.player.def_food_pie.copy()

                        elif event.button == 3:
                            pass

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

                    """
                    elif event.type == pygame.MOUSEMOTION:
                        for block in all_blocks:
                            block.check_not_hovering()
                    """

                    if g.stage == "home":
                        for spr in all_main_widgets():
                            if hasattr(spr, "process_event") and callable(spr.process_event):
                                spr.process_event(event)
                                g.process_messageboxworld = False

            # pending
            for entry in g.pending_entries[:]:
                entry.enable()
                g.pending_entries.remove(entry)

            # play loop
            if g.stage == "play":
                if not g.menu:
                    if g.mouses[0]:
                        if g.clicked_when == "play" and not g.cannot_place_block:
                            if not g.menu:
                                if g.player.main == "tool":
                                    if g.player.tool is not None:
                                        if all(not x in g.player.tool for x in ["_sword", "_grappling-hook"]):
                                            visual.angle += 3
                                            if visual.angle > 90:
                                                visual.angle = -90

                                for block in g.player.closest_tool_blocks:
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
                                                        if not (block.rect.colliderect(g.player.rect) if g.str_mod != "_bg" else False) and g.player.block not in unplacable_blocks:
                                                            if g.player.block:
                                                                block.set(g.player.block + g.str_mod)
                                                                if g.w.mode == "adventure":
                                                                    g.player.use_up_inv(g.player.itemi)
                                                                # metadata
                                                                if non_bg(block.name) == "chest":
                                                                    g.w.metadata[g.w.screen][block.abs_index]["chest"] = {}
                                                        externally_update_entities()
                                                elif stmt:
                                                    if g.first_affection is None:
                                                        g.first_affection = "break"
                                                    if g.first_affection == "break":
                                                        if g.w.mode == "adventure":
                                                            if non_bg(block.name) not in unbreakable_blocks:
                                                                block.try_breaking()
                                                        elif g.w.mode == "freestyle":
                                                            block.try_breaking("freestyle")
                                                else:
                                                    block.broken = 0

                                    elif g.player.main == "tool":
                                        if gtool(g.player.tool) in tinfo:
                                            if hasattr(visual, "rect"):
                                                if block.rect.colliderect(visual.rect):
                                                    block.try_breaking("tool")
                                                    break

                                        elif is_gun(g.player.tool):
                                            if not visual.reloading:
                                                if g.player.tool_ammo > 0:
                                                    if ticks() - last_gunfire >= 80:
                                                        pos = g.player.rect.center
                                                        angle = two_pos_to_angle(g.player.rect.center, g.mouse)
                                                        angle_var = 10
                                                        speed = 20
                                                        size = (5, 5)
                                                        pierce = False
                                                        group(Projectile(pos, [angle, angle_var], speed, size, pierce), all_projectiles)
                                                        group(BreakingBlockParticle(cartridge_img, visual.rect.center), all_particles)
                                                        g.player.tool_ammo -= 1
                                                        last_gunfire = ticks()

                    else:
                        g.cannot_place_block = False

                # filling
                Window.display.fill(g.w.sky_color)
                # Window.display.blit(sky_bg, (0, 0))

                # menu filling
                if g.menu or g.skin_menu:
                    Window.display.blit(g.menu_surf, (0, 0))

                # day-night cycle
                g.w.dnc_index = g.w.dnc_direc(g.w.dnc_index, fromperc(g.dt * 100, g.w.dnc_vel))
                if g.w.dnc_index >= len(g.w.dnc_colors) - 1:
                    g.w.dnc_index = len(g.w.dnc_colors) - 1
                    g.w.dnc_direc = op.sub
                elif g.w.dnc_index <= 0:
                    g.w.dnc_index = 0
                    g.w.dnc_direc = op.add
                    g.w.set_dnc_colors()
                    if g.w.hound_round_chance > 1:
                        g.w.hound_round_chance -= 1

                # block stuff

                g.player.block_rects = []
                for block in all_blocks:
                    if block.name != "air":
                        block.update()
                        if pw.show_internals:
                            pygame.draw.rect(Window.display, GREEN, block.rect, 1)
                            pygame.draw.rect(Window.display, GREEN, g.player.rect, 1)
                        if is_hard(block.name):
                            g.player.block_rects.append(block._rect)
                    elif non_bg(block.name) == "magic-table":
                        _h = round(sin(ticks() / 150) * 10)
                        _yo = round(sin(ticks() / 280) * 5)
                        _m15 = block.rect.y - 20
                        _color = g.flame_rgb[_h * 5 - 1]
                        pygame.gfxdraw.aaellipse(Window.display, block.rect.x + block.rect.width // 2, _m15 + _yo, 10, abs(_h), _color)
                        pygame.gfxdraw.aaellipse(Window.display, block.rect.x + block.rect.width // 2, _m15 + _yo, abs(_h), 10, _color)

                # death screen
                if g.player.dead:
                    Window.display.blit(death_screen, (0, 0))

                # projectiles
                all_projectiles.update()

                # foregorund sprites (also the player)
                g.player.update()
                all_foreground_sprites.draw(Window.display)
                all_foreground_sprites.update()

                # drops
                for drop in all_drops:
                    drop.update()

                # other particles
                for oparticle in all_other_particles:
                    oparticle.update()

                # entities
                """
                for entity in g.w.entities:
                    update_entity(entity)
                    entity.update(g.dt)
                """

                # mobs
                all_mobs.update()

                # visual block and tool
                visual.update()

                # hovering
                hov.update()

                if pw.show_internals:
                    pygame.draw.rect(Window.display, GREEN, visual.rect, 1)

                for block in all_blocks:
                    if int(block.broken) > 0:
                        Window.display.blit(breaking_sprs[int(block.broken) - 1], (block.rect.x, block.rect.y))

                # P L A Y  B L I T S -------------------------------------------------------------------------- #
                # hotbar init
                hotbar_xo = -3
                tool_holders_x, tool_holders_y = (Window.width / 2 - 132 + hotbar_xo, 7)
                inventory_x, inventory_y = (Window.width / 2 + 21 + hotbar_xo, 7)
                pouch_x, pouch_y, = (Window.width / 2 + 240 + hotbar_xo, 7)
                inventory_font_size = 15

                # blitting background
                Window.display.blit(tool_holders_img, (tool_holders_x, tool_holders_y))
                Window.display.blit(inventory_img, (inventory_x, inventory_y))
                Window.display.blit(pouch_img, (pouch_x, pouch_y))

                # blitting tools
                x = tool_holders_x + 3
                y = tool_holders_y + 3
                for index, tool in enumerate(g.player.tools):
                    if tool is not None:
                        tool_img = g.w.tools[tool]
                        xo, yo = [(BS - s) / 2 for s in tool_img.get_size()]
                        Window.display.blit(tool_img, (x + xo, y + yo))
                        if gtool(tool) in tinfo:
                            th = int(g.player.tool_healths[index])
                            if "_bow" in tool:
                                _surf = write(Window.display, "center", th, orbit_fonts[14], g.w.text_color, x, y + 27)
                            else:
                                if th < 100:
                                    pygame.draw.rect(Window.display, bar_rgb[int(th * (99 / 100))], (x, y + 35, fromperc(th, 30), 5))
                        if g.player.main == "tool" and index == g.player.tooli:
                            if is_gun(tool):
                                write(Window.display, "center", f"{BULLET}", helvue_fonts[22], g.w.text_color, g.mouse[0] - visual.scope_yoffset, g.mouse[1] - 30)
                                write(Window.display, "center", g.player.tool_ammo, orbit_fonts[16], g.w.text_color, g.mouse[0] + visual.scope_yoffset, g.mouse[1] - 30)
                    # border if selected
                    if g.player.main == "tool":
                        if index == g.player.tooli:
                            Window.display.blit(square_border_img, (x - 3, y - 3))
                    x += 33

                # blitting blocks
                x = inventory_x + 3
                y = inventory_y + 3
                for index, block in enumerate(g.player.inventory):
                    if block is not None:
                        block_img = g.w.blocks[block]
                        Window.display.blit(block_img, (x, y))
                    # border if selected
                    if g.player.main == "block":
                        if index == g.player.blocki:
                            Window.display.blit(square_border_img, (x - 3, y - 3))
                    x += 33

                # blitting pouch
                x = pouch_x + 3
                y = pouch_y + 3
                Window.display.blit(pouch_icon, (x, y))

                # hovering
                hov.update()

                # P L A Y  B L I T S -------------------------------------------------------------------------- #
                # player username
                write(Window.display, "center", g.player.username, orbit_fonts[12], g.w.text_color, g.player.rect.centerx, g.player.rect.centery - 30)

                # sizes
                inventory_width = inventory_img.get_width()
                hotbar_width = tool_holders_img.get_width() + 30 + inventory_width + 30 + pouch_img.get_width()

                # writing main item names
                yo = 72
                if g.player.main == "block" and g.player.block:
                    x = inventory_x + inventory_width / 2
                    if g.player.block in gun_blocks:
                        block = gpure(g.player.block).upper()
                    else:
                        block = bshow(g.player.block).upper()
                    write(Window.display, "center", t | block, orbit_fonts[15], g.w.text_color, x, y + yo)
                elif g.player.main == "tool" and g.player.tool:
                    x = tool_holders_x + tool_holders_width / 2
                    tool = tshow(g.player.tool).upper()
                    write(Window.display, "center", t | tool, orbit_fonts[inventory_font_size], g.w.text_color, x, y + yo)

                # selected block
                x = inventory_x + inventory_width / 10 + 1
                y = inventory_y + 18
                for index, block in enumerate(g.player.inventory):
                    if block is not None:
                        if g.player.inventory_amounts[index] != float("inf"):
                            write(Window.display, "center", g.player.inventory_amounts[index], orbit_fonts[inventory_font_size], g.w.text_color, x, y + 24)
                        else:
                            write(Window.display, "center", INF, arial_fonts[18], g.w.text_color, x, y + 27)
                    x += 33

                # pouch icon
                x = pouch_x + pouch_width / 2 - 1
                write(Window.display, "center", g.player.pouch, orbit_fonts[inventory_font_size], g.w.text_color, x, y + 24)

                # workbench
                if g.midblit == "workbench":
                    Window.display.blit(workbench_img, crafting_rect)
                    x = crafting_rect.x + 30 / 2 + 25
                    y = crafting_rect.y + 30 + 30 / 2 + 10
                    sy = y
                    xo = 30 + 5
                    yo = 30 + 10
                    for crafting_block in g.mb.craftings:
                        # crafting material
                        pygame.draw.aaline(Window.display, BLACK, (x + 30 / 2, y), crafting_center)
                        Window.display.blit(g.w.blocks[crafting_block], (x, y))
                        write(Window.display, "midright", g.mb.craftings[crafting_block], orbit_fonts[inventory_font_size], BLACK, x - 20, y)
                        y += yo
                        if (y - sy) / yo == 5:
                            y = sy
                            x += xo
                        # calculating receiving material
                        g.mb.craftables = SmartOrderedDict()
                        for craftable in cinfo:
                            g.mb.midblit_by_what = []
                            enough = 0
                            truthy = True
                            for crafting_block in g.mb.craftings:
                                try:
                                    if cinfo[craftable]["recipe"][crafting_block] > g.mb.craftings[crafting_block]:
                                        truthy = False
                                        break
                                except KeyError:
                                    truthy = False
                                    break
                            if truthy:
                                if g.player.stats["energy"]["amount"] - cinfo[craftable].get("energy", float("-inf")) >= 0:
                                    for recipe_block in cinfo[craftable]["recipe"]:
                                        if g.mb.craftings.get(recipe_block, float("-inf")) >= cinfo[craftable]["recipe"][recipe_block]:
                                            enough += 1
                                            g.mb.midblit_by_what.append(g.mb.craftings[recipe_block] // cinfo[craftable]["recipe"][recipe_block] * cinfo[craftable].get("amount", 1))
                                    if enough == len(cinfo[craftable]["recipe"]):
                                        g.mb.craftables[craftable] = g.mb.midblit_by_what
                        # blitting images
                        _x = crafting_center[0] + crafting_rect.width / 4
                        _y = crafting_center[1]
                        for index, craftable in enumerate(g.mb.craftables):
                            if len(g.mb.craftables) >= 2 and index == g.mb.craftable_index:
                                Window.display.blit(square_border_img, (_x, _y))
                            g.mb.midblit_by_what = g.mb.craftables[craftable]
                            pygame.draw.aaline(Window.display, BLACK, crafting_center, (_x, _y))
                            if craftable in g.w.blocks:
                                Window.display.blit(g.w.blocks[craftable], (_x, _y))
                            elif craftable in g.w.tools:
                                Window.display.blit(g.w.tools[craftable], (_x, _y))
                            g.mb.midblit_by_what = min(g.mb.midblit_by_what)
                            g.mb.craftables[craftable] = g.mb.midblit_by_what
                            write(Window.display, "midbottom", g.mb.midblit_by_what, orbit_fonts[15], BLACK, _x, _y + yo)
                            _x += yo
                    # arrow
                    if g.midblit == "workbench":
                        Window.display.blit(workbench_icon, crafting_center)

                # furnace
                elif g.midblit == "furnace":
                    Window.display.blit(furnace_img, crafting_rect)
                    x = crafting_rect.x + 30 / 2 + 25
                    y = crafting_rect.y + 30 + 30 / 2 + 10
                    sy = y
                    xo = 30 + 5
                    yo = 30 + 10
                    for burning in g.mb.burnings:
                        if g.mb.fuels:
                            pygame.draw.aaline(Window.display, BLACK, (x + 30 / 2, y), crafting_rect.center)
                        Window.display.blit(g.w.blocks[burning], (x, y))
                        write(Window.display, "midright", g.mb.burnings[burning], orbit_fonts[15], BLACK, x - 20, y)
                        y += yo
                        if (y - sy) / yo == 5:
                            y = sy
                            x += xo
                    x, y = crafting_rect.center
                    for fuel in g.mb.fuels:
                        if g.mb.burnings:
                            g.mb.fuel_index += fueinfo.get(fuel, {"index": 0.01})["index"] * (g.player.oxygen / 100)
                            g.mb.fuel_health -= fueinfo.get(fuel, {"sub": 0.2})["sub"]
                            if g.mb.fuel_health <= 0:
                                g.mb.fuel_health = 100
                                g.mb.fuels[fuel] -= 1
                                if g.mb.fuels[fuel] == 0:
                                    g.mb.fuels.delindex(-1)
                                    break
                        Window.display.blit(g.w.blocks[fuel], (x, y))
                        write(Window.display, "midbottom", g.mb.fuels[fuel], orbit_fonts[15], BLACK, x, y + 41)
                    if g.mb.fuel_index > 0:
                        # arrow (burning)
                        try:
                            arrow_sprs[int(g.mb.fuel_index)]
                        except IndexError:
                            g.mb.fuel_index = 0
                            search = fuinfo[g.mb.burnings.getindex(-1)] if g.mb.burnings.getindex(-1) in fuinfo else g.mb.burnings.getindex(-1) + "_ck"
                            if search in g.mb.furnace_outputs:
                                g.mb.furnace_outputs[search] += 1
                            else:
                                g.mb.furnace_outputs[search] = 1
                            if g.mb.burnings[-1] > 1:
                                g.mb.burnings[list(g.mb.burnings.keys())[-1]] -= 1
                            else:
                                g.mb.burnings.delindex(-1)
                        finally:
                            Window.display.blit(arrow_sprs[int(g.mb.fuel_index)], (x, y + 55))
                    if g.mb.fuels:
                        # shower (fuel)
                        try:
                            shower_surf = shower_sprs[int(8 - g.mb.fuel_health / 12.5)]
                        except IndexError:
                            g.mb.fuel_health = 100
                            shower_surf = shower_sprs[0]
                            g.mb.fuels.delindex(0)
                        finally:
                            Window.display.blit(shower_surf, (x + 25, y))
                    x = crafting_rect.centerx + crafting_rect.width / 3
                    y = crafting_rect.centery
                    for foutput in g.mb.furnace_outputs:
                        Window.display.blit(g.w.blocks[foutput], (x, y))
                        write(Window.display, "midbottom", g.mb.furnace_outputs[foutput], orbit_fonts[15], BLACK, x, y + 41)
                        y += yo

                # anvil
                elif g.midblit == "anvil":
                    Window.display.blit(anvil_img, crafting_rect)
                    x = crafting_rect.x + 30 / 2 + 25
                    y = crafting_rect.y + 30 + 30 / 2 + 10
                    sy = y
                    xo = 30 + 5
                    yo = 30 + 10
                    for smithing_block in g.mb.smithings:
                        # crafting material
                        pygame.draw.aaline(Window.display, BLACK, (x + 30 / 2, y), crafting_center)
                        Window.display.blit(g.w.blocks[smithing_block], (x, y))
                        write(Window.display, "midright", g.mb.smithings[smithing_block], orbit_fonts[15], BLACK, x - 20, y)
                        y += yo
                        if (y - sy) / yo == 5:
                            y = sy
                            x += xo
                        # calculating receiving material
                        g.mb.smithables = SmartOrderedDict()
                        for smithable in ainfo:
                            g.mb.midblit_by_what = []
                            enough = 0
                            truthy = True
                            for smithing_block in g.mb.smithings:
                                try:
                                    if ainfo[smithable]["recipe"][smithing_block] > g.mb.smithings[smithing_block]:
                                        truthy = False
                                        break
                                except KeyError:
                                    truthy = False
                                    break
                            if truthy:
                                if g.player.stats["energy"]["amount"] - ainfo[smithable].get("energy", float("-inf")) >= 0:
                                    for recipe_block in ainfo[smithable]["recipe"]:
                                        if g.mb.smithings.get(recipe_block, float("-inf")) >= ainfo[smithable]["recipe"][recipe_block]:
                                            enough += 1
                                            g.mb.midblit_by_what.append(g.mb.smithings[recipe_block] // ainfo[smithable]["recipe"][recipe_block] * ainfo[smithable].get("amount", 1))
                                    if enough == len(ainfo[smithable]["recipe"]):
                                        g.mb.smithables[smithable] = g.mb.midblit_by_what
                        # blitting images
                        _x = crafting_center[0] + crafting_rect.width / 3
                        _y = crafting_center[1]
                        for index, smithable in enumerate(g.mb.smithables):
                            if len(g.mb.smithables) >= 2 and index == g.mb.smithable_index:
                                Window.display.blit(square_border_img, (_x, _y))
                            g.mb.midblit_by_what = g.mb.smithables[smithable]
                            pygame.draw.aaline(Window.display, BLACK, crafting_center, (_x, _y))
                            if smithable in g.w.blocks:
                                Window.display.blit(g.w.blocks[smithable], (_x, _y))
                            elif smithable in g.w.tools:
                                Window.display.blit(g.w.tools[smithable], (_x, _y))
                            g.mb.midblit_by_what = min(g.mb.midblit_by_what)
                            g.mb.smithables[smithable] = g.mb.midblit_by_what
                            write(Window.display, "midbottom", g.mb.midblit_by_what, orbit_fonts[15], BLACK, _x, _y + yo)
                            _x += yo
                    if g.mb.smither is not None:
                        Window.display.blit(g.w.tools[g.mb.smither], crafting_center)

                # gun crafter
                elif g.midblit == "gun-crafter":
                    gun_crafter_base.blit(gun_crafter_img, (0, 0))
                    for part, name in g.mb.gun_parts.items():
                        pos = gun_crafter_part_poss[part]
                        if name is not None:
                            gun_crafter_base.cblit(g.w.blocks[name], pos)
                        elif part not in g.extra_gun_parts:
                            write(gun_crafter_base, "center", "?", orbit_fonts[20], BLACK, *pos)
                            #pygame.gfxdraw.aacircle(Window.display, *pos, 5, BLACK)
                            #pygame.draw.circle(Window.display, BLACK, pos, 5)
                    Window.display.blit(gun_crafter_base, crafting_rect)
                    if is_gun_craftable():
                        write(Window.display, "center", "Gun is ready to craft", orbit_fonts[18], BLACK, crafting_rect.centerx, crafting_rect.centery + 30)

                # magic table
                elif g.midblit == "magic-table":
                    Window.display.blit(magic_table_img, crafting_rect)
                    yo = 30 + 10
                    x = crafting_x
                    y = crafting_y - yo
                    tx = crafting_x - crafting_rect.width / 3
                    ty = crafting_y
                    for magic_orb in g.mb.magic_orbs:
                        if g.mb.magic_tool is not None:
                            pygame.draw.aaline(Window.display, BLACK, (tx, ty), (x, y))
                        Window.display.blit(g.w.blocks[magic_orb], (x, y))
                        y += yo
                    if g.mb.magic_tool is not None:
                        Window.display.blit(g.w.tools[g.mb.magic_tool], (tx, ty))

                # altar
                elif g.midblit == "altar":
                    Window.display.blit(altar_img, crafting_rect)
                    x = crafting_rect.x + 30 / 2 + 25
                    y = crafting_rect.y + 30 + 30 / 2 + 10
                    sy = y
                    xo = 30 + 5
                    yo = 30 + 10
                    for offering in g.mb.offerings:
                        Window.display.blit(g.w.blocks[offering], (x, y))
                        write(Window.display, "midright", g.mb.offerings[offering], orbit_fonts[15], BLACK, x - 20, y)

                # chest
                elif g.midblit == "chest":
                    Window.display.blit(chest_template, chest_rect)
                    ogx, ogy = chest_rect_start
                    x, y = ogx, ogy
                    row = 0
                    for name, amount in g.chest:
                        if name is not None:
                            write(Window.display, "center", amount, orbit_fonts[15], g.w.text_color, x + 14, y + 39)
                            Window.display.blit(g.w.blocks[name], (x, y))
                        x += 33
                        if row == 4:
                            x = ogx
                            y += 51
                            row = -1
                        row += 1
                    Window.display.blit(square_border_img, g.chest_pos)
                    for rect in chest_rects:
                        if rect.collidepoint(g.mouse):
                            with suppress(IndexError, AttributeError):
                                write(Window.display, "center", bshow(g.chest[chest_indexes[rect.topleft]][0]), orbit_fonts[15], g.w.text_color, crafting_rect.centerx, 150)

                if g.mod == 1:
                    if no_widgets(Entry):
                        if g.player.main == "block" and g.player.block:
                            write(Window.display, "center", "[BACKGROUND]", orbit_fonts[13], g.w.text_color, Window.width / 2 + 20 + hotbar_xo, 110)
                write(Window.display, "midright", f"| Sector {g.w.screen + 1} |", orbit_fonts[15], g.w.text_color, Window.width - 10, 20)


                # applyping regeneration (player bars)
                if g.w.mode == "adventure":
                    if g.player.stats["lives"]["amount"] + 1 <= 100:
                        if ticks() - g.player.stats["lives"]["last_regen"] >= g.player.stats["lives"]["regen_time"]:
                            g.player.stats["lives"]["amount"] += 1
                            g.player.stats["lives"]["regen_time"] -= 0.5
                            g.player.stats["lives"]["last_regen"] = ticks()

                    # player food chart
                    if "image" in g.player.food_pie and "rect" in g.player.food_pie:
                        g.player.food_pie["rect"].midbottom = (g.player.rect.centerx, g.player.rect.top - 25)
                        Window.display.blit(g.player.food_pie["image"], g.player.food_pie["rect"])
                        if pw.show_internals:
                            pygame.draw.rect(Window.display, GREEN, g.player.food_pie["rect"], 1)

                # skin menu filling
                if g.skin_menu:
                    # background (filling)
                    Window.display.blit(g.skin_menu_surf, (Window.width / 2, Window.height / 2))
                    Window.display.blit(g.w.player_model, (Window.width / 2, Window.height / 2))
                    # skins (showcase)
                    for bt in g.skins:
                        if g.skin_data(bt)["sprs"]:
                            try:
                                g.skin_anims[bt] += g.skin_anim_speed
                                skin_img = g.skin_data(bt)["sprs"][int(g.skin_anims[bt])]
                                skin_pos = g.skin_data(bt)["offset"]
                                Window.display.blit(skin_img, (g.player_model_pos[0] + skin_pos[0] * g.skin_fppp, g.player_model_pos[1] + skin_pos[1] * g.skin_fppp))
                            except IndexError:
                                g.skin_anims[bt] = 0
                                g.skin_anims[bt] += g.skin_anim_speed
                                skin_img = g.skin_data(bt)["sprs"][int(g.skin_anims[bt])]
                                skin_pos = g.skin_data(bt)["offset"]
                                Window.display.blit(skin_img, (g.player_model_pos[0] + skin_pos[0] * g.skin_fppp, g.player_model_pos[1] + skin_pos[1] * g.skin_fppp))

                    # buttons (arrows)
                    for button in pw.change_skin_buttons:
                        Window.display.blit(button["surf"], button["rect"].center)

            # home loop
            elif g.stage == "home":
                Window.display.fill(GRAY)
                #write(Window.display, "center", "Blockingdom", orbit_fonts[50], BLACK, Window.width // 2, 58)
                sp = 0.1
                xo = (Window.width / 2 - g.mouse[0]) * sp
                yo = (Window.height / 2 - g.mouse[1]) * sp - 200
                #Window.display.blit(g.home_bg_img, (Window.width / 2 - g.home_bg_size[0] / 2 + xo, Window.height / 2 - g.home_bg_size[1] / 2 + yo))
                if Platform.os == "windows":
                    Window.display.blit(g.menu_surf, (0, 0))
                #Window.display.blit(frame_img, (0, 0))
                all_home_sprites.draw(Window.display)
                all_home_sprites.update()

                if g.home_stage == "worlds":
                    write(Window.display, "topleft", "Worlds:", orbit_fonts[30], BLACK, 35, 50)
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
                if g.loading_world:
                    pygame.draw.rect(Window.display, BLACK, (Window.width / 2 - 100, Window.height / 2 - 15, 200, 30), 3)
                    pygame.draw.rect(Window.display, LIGHT_GREEN, (Window.width / 2 - 98, Window.height / 2 - 13, g.loading_world_perc * 2 - 4, 26))
                    write(Window.display, "center", f"{int(g.loading_world_perc)}%", orbit_fonts[20], BLACK, *Window.center)

            # skin menu filling
            if g.skin_menu:
                # background (filling)
                Window.display.cblit(g.skin_menu_surf, (Window.width / 2, Window.height / 2))
                Window.display.cblit(g.w.player_model, (Window.width / 2, Window.height / 2))
                # skins (showcase)
                for bt in g.skins:
                    if g.skin_data(bt)["sprs"]:
                        try:
                            g.skin_anims[bt] += g.skin_anim_speed
                            skin_img = g.skin_data(bt)["sprs"][int(g.skin_anims[bt])]
                            skin_pos = g.skin_data(bt)["offset"]
                            Window.display.blit(skin_img, (g.player_model_pos[0] + skin_pos[0] * g.skin_fppp, g.player_model_pos[1] + skin_pos[1] * g.skin_fppp))
                        except IndexError:
                            g.skin_anims[bt] = 0
                            g.skin_anims[bt] += g.skin_anim_speed
                            skin_img = g.skin_data(bt)["sprs"][int(g.skin_anims[bt])]
                            skin_pos = g.skin_data(bt)["offset"]
                            Window.display.blit(skin_img, (g.player_model_pos[0] + skin_pos[0] * g.skin_fppp, g.player_model_pos[1] + skin_pos[1] * g.skin_fppp))

                # buttons (arrows)
                for button in pw.change_skin_buttons:
                    Window.display.cblit(button["surf"], button["rect"].center)

            # late stuff (for debugging)
            for rect in late_rects:
                pygame.draw.rect(Window.display, RED, rect, 1)
            for pixel in late_pixels:
                Window.display.set_at((int(pixel[0]), int(pixel[1])), pixel[2])
            for line in late_lines:
                pygame.draw.aaline(Window.display, RED, line[0], line[1])
            for img in late_imgs:
                Window.display.blit(img, (100, 100))

            # updating the widgets
            updating_buttons = [button for button in iter_buttons() if not button.disabled]
            updating_worldbuttons = [worldbutton for worldbutton in all_home_world_world_buttons if is_drawable(worldbutton)]
            updating_settingsbuttons = [settingsbutton for settingsbutton in all_home_settings_buttons if is_drawable(settingsbutton) and not isinstance(settingsbutton, StaticOptionMenu)]
            updating_static_buttons = [static_button for static_button in all_home_world_static_buttons if is_drawable(static_button)]
            update_button_behavior(updating_worldbuttons + updating_buttons + updating_settingsbuttons + updating_static_buttons + [button_s, button_w, button_c])
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

        #profiler.print_stats()
        ExitHandler.save("quit")

if __name__ == "__main__":
    main(debug=True)
    #import cProfile; cProfile.run("main(debug=True)", sort="cumtime")
