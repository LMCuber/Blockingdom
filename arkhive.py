# workbench
t = 30
w = 400
h = 210
img = pygame.Surface((w, h))
img.fill(WHITE, (0, 0, w, t))
img.fill(LIGHT_GRAY, (0, t, w / 2, h))
img.fill(GRAY, (w / 2, t, w, h))
workbench_rel_center = (img.get_width() / 2, (img.get_height() + 30) / 2)
write(img, "midtop", "Input", orbit_fonts[20], BLACK, w / 4, 0)
write(img, "midtop", "Output", orbit_fonts[20], BLACK, w / 4 * 3, 0)
workbench_rect = img.get_rect(center=(Window.width / 2, Window.height / 2))
pygame.image.save(img, path("Surfaces", "anvil.png"))

# furnace / anvil
t = 30
w = 400
h = 210
img = pygame.Surface((w, h))
img.fill(LIGHT_GRAY, (0, 0, w, h))
img.fill(GRAY, (0, t, w / 3, h))
img.fill(DARK_GRAY, (w / 3 * 2, t, w, h))
img.fill(WHITE, (0, 0, w, t))
workbench_rel_center = (img.get_width() / 2, (img.get_height() + 30) / 2)
write(img, "midtop", "Input", orbit_fonts[20], BLACK, w / 3 / 2, 0)
write(img, "midtop", "Output", orbit_fonts[20], BLACK, (w / 3 / 2)*5, 0)
write(img, "midtop", "Tool", orbit_fonts[20], BLACK, (w / 2), 0)
workbench_rect = img.get_rect(center=(Window.width / 2, Window.height / 2))
pygame.image.save(img, path("Images", "Surfaces", "anvil.png"))

# magic-table
t = 30
w = 400
h = 210
img = pygame.Surface((w, h))
img.fill((80, 26, 116), (0, 0, w, h))
img.fill(DARK_GRAY, (0, t, w / 3, h))
img.fill(DARK_GRAY, (w / 3 * 2, t, w, h))
img.fill(WHITE, (0, 0, w, t))
workbench_rel_center = (img.get_width() / 2, (img.get_height() + 30) / 2)
write(img, "midtop", "Input", orbit_fonts[20], BLACK, w / 3 / 2, 0)
write(img, "midtop", "Output", orbit_fonts[20], BLACK, (w / 3 / 2)*5, 0)
write(img, "midtop", "Orb", orbit_fonts[20], BLACK, (w / 2), 0)
workbench_rect = img.get_rect(center=(Window.width / 2, Window.height / 2))
pygame.image.save(img, path("Images", "Surfaces", "magic-table.png"))
p = pg_to_pil(img)
p.show()
raise

# gun <^>
gun_crafter = pygame.Surface((400, 210))
gun_crafter.fill(LIGHT_GRAY)
gun_crafter.fill(WHITE, (0, 0, 400, 30))
write(gun_crafter, "midtop", "Gun Crafter", orbit_fonts[20], BLACK, 200, 0)
h = 70
b = 1
pygame.draw.rect(gun_crafter, GRAY,      (gun_crafter.get_width() // 2 - 59, h + 12, 30, 30))
pygame.draw.rect(gun_crafter, DARK_GRAY, (gun_crafter.get_width() // 2 - 59, h + 12, 30, 30), b)
pygame.draw.rect(gun_crafter, GRAY,      (gun_crafter.get_width() // 2 - 29, h, 60, 30))
pygame.draw.rect(gun_crafter, DARK_GRAY, (gun_crafter.get_width() // 2 - 29, h, 60, 30), b)
pygame.draw.rect(gun_crafter, GRAY,      (gun_crafter.get_width() // 2 + 15, h, 30, 30))
pygame.draw.rect(gun_crafter, DARK_GRAY, (gun_crafter.get_width() // 2 + 15, h, 30, 30), b)
pygame.draw.rect(gun_crafter, GRAY,      (gun_crafter.get_width() // 2 - 30, h + 30, 30, 30))
pygame.draw.rect(gun_crafter, DARK_GRAY, (gun_crafter.get_width() // 2 - 30, h + 30, 30, 30), b)
pygame.draw.rect(gun_crafter, GRAY,      (gun_crafter.get_width() // 2, h + 30, 30, 30))
pygame.draw.rect(gun_crafter, DARK_GRAY, (gun_crafter.get_width() // 2, h + 30, 30, 30), b)
pygame.image.save(gun_crafter, "Images\Surfaces\gun_crafter.png")
gun_crafter_img = gun_crafter.copy()

# visuals
class VisualBlock:
    __slots__ = ["og_img", "image", "rect"]

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


class VisualTool:
    __slots__ = ["og_img", "image", "rect", "angle"]

    def __init__(self):
        self.angle = 0

    def function(self):
        if g.player.main == "tool":
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

# hotbar
Window.hotbar = pygame.Surface((Window.width, 54), pygame.SRCALPHA)
Window.hotbar.blit(tool_holders_img, (0, 0))
Window.hotbar.blit(inventory_img, (78, 0))
#Window.hotbar.blit(pouch_img, (256, 0))

x = 3
i = 0
for tool in g.player.tools:
    if tool is not None:
        Window.hotbar.blit(a.tools[tool], (x, 3))
    if tpure(tool) in tinfo:
        th = g.player.tool_healths[i]
        if th < 100:
            pygame.draw.rect(Window.hotbar, g.health_bar_colors[int(th)], (x, 40, perc(th, 30), 3))
    elif tpure(tool) in g.w.gun_names:
        pass
    x += 33
    i += 1

x = 81
i = 0
i = 0
    if block is not None:
for block in g.player.inventory:
        Window.hotbar.blit(a.blocks[block], (x, 3))
        write(Window.hotbar, "center", inf(g.player.inventory_amounts[i]), orbit_fonts[15], BLACK, x + 15, 43)
    x += 33
    i += 1

if g.player.main == "block":
    Window.hotbar.blit(selected_item_img, (selected_block_poss[g.player.indexes["block"]]))
elif g.player.main == "tool":
    Window.hotbar.blit(selected_item_img, (selected_tool_poss[g.player.indexes["tool"]]))

hbr_width_dbt = Window.hotbar.get_width() / 2
Window.display.blit(Window.hotbar, (Window.width / 2 - hbr_width_dbt, 15))

selected_tool_poss = []
x = 0
for i in range(2):
    selected_tool_poss.append((x, 0))
    x += 33
selected_block_poss = []
x = 78
for i in range(5):
    selected_block_poss.append((x, 0))
    x += 33

# player
class Player:
    def __init__(self):
        self.images = [SmartSurface(g.player_size) for _ in range(4)]
        for image in self.images:
            image.fill(GRAY)
        self.anim = 0
        self.animate()
        self.rect = self.image.get_rect(center=(Window.width / 2, Window.height / 2))
        self.rect.center = (Window.width / 2, Window.height / 2)
        self.width = self.rect.width
        self.height = self.rect.height
        self.gravity = 0.15
        self.fre_vel = 3
        self.adv_xvel = 2
        self.water_xvel = 1
        self.yvel = 0
        self.def_jump_yvel = -3.5
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

        self.set_moving_mode("adventure")

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
        if no_widgets(Entry):
            getattr(self, self.moving_mode[0] + "_move")(*self.moving_mode[1:])
        self.update_move()
        self.external_gravity()
        self.off_screen()
        self.drops()
        self.update_fall_effect()
        self.animate()
        self.update_effects()
        self.achieve()

    def draw(self):
        Window.display.blit(self.image, self.rect)

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
        return self.inventory[self.indexes["block"]]

    @block.setter
    def block(self, value):
        self.inventory[self.indexes["block"]] = value

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
            self.inventory_amounts[self.empty_blocki], self.inventory[self.empty_blocki] = reversed(value)
        else:
            self.inventory[self.empty_blocki] = value

    @property
    def tool(self):
        return self.tools[self.indexes["tool"]]

    @tool.setter
    def tool(self, value):
        self.tools[self.indexes["tool"]] = value

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

    def achieve(self):
        for ac, cond in g.achievements:
            print(ac, cond)

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

    def take_dmg(self, amount, scrsh_offset, scrsh_length, reason=None):
        self.stats["lives"]["amount"] -= amount
        self.stats["lives"]["regen_time"] = def_regen_time
        self.stats["lives"]["last_regen"] = ticks()
        g.screen_shake = scrsh_length
        g.s_render_offset = scrsh_offset
        if g.player.stats["lives"]["amount"] <= 0:
            g.player.die(reason)

    def eat(self):
        food = self.block
        self.food_pie["counter"] += get_finfo(self.inventory[self.indexes["block"]])["speed"]
        degrees = self.food_pie["counter"]
        pie_size = (40, 40)
        pil_img = PIL.Image.new("RGBA", [s * 4 for s in pie_size])
        pil_draw = PIL.ImageDraw.Draw(pil_img)
        pil_draw.pieslice((0, 0, *[ps - 1 for ps in pie_size]), -90, degrees, fill=GRAY)
        pil_img = pil_img.resize(pie_size, PIL.Image.ANTIALIAS)
        del pil_draw
        self.food_pie["image"] = pil_to_pg(pil_img)
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
        #self.username = f"Player{rand(2, 456)}"
        #self.username = json.loads(requests.get(g.funny_words_url).text)[0].split("_")[0]
        #self.username = fnames.dwarf()
        #self.username = shake_str(json.loads(requests.get(g.name_url).text)["name"]).title()
        self.username = json.loads(requests.get(g.name_url).text)["username"].capitalize()
        #self.username = " ".join([json.loads(requests.get(g.random_word_url).text)[0]["word"] for _ in range(2)]).title()

    def cust_username(self):
        def set_username(ans):
            if ans is not None and ans != "":
                split_username = ans.split(" ")
                username = " ".join([word if not word in g.profanities else len(word) * "*" for word in split_username])

                self.username = username
            else:
                self.rand_username()
        Entry(Window.display, "Enter your new username:", set_username, pos=DPP, default_text=("random", orbit_fonts[20]))

    def movex(self, xvel):
        self.dx += xvel
        if xvel > 0:
            self.direc = "right"
        else:
            self.direc = "left"
        self.still = False

    def movey(self, yvel):
        self.dy += self.yvel
        print(round(self.dy, 2), self.rect.y)

    def freestyle_move(self):
        keys = pygame.key.get_pressed()
        if g.keys[g.ckeys["p up"]]:
            self.movey(-self.fre_vel)
        if g.keys[g.ckeys["p down"]]:
            self.movey(self.fre_vel)
        if g.keys[g.ckeys["p left"]]:
            self.movex(-self.fre_vel)
        if g.keys[g.ckeys["p right"]]:
            self.movex(self.fre_vel)

    def adventure_move(self):
        # jumping
        keys = pygame.key.get_pressed()
        if g.keys[g.ckeys["p up"]]:
            if not self.in_air and self.yvel <= 0:
                self.yvel = self.jump_yvel
                self.in_air = True

        # xvel
        self.still = True
        if g.keys[g.ckeys["p left"]]:
            self.movex(-self.adv_xvel)
        if g.keys[g.ckeys["p right"]]:
            self.movex(self.adv_xvel)

        # yvel
        self.yvel += self.gravity
        self.movey(self.yvel)

        # collisions
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
                                self.take_dmg(round(self.yvel * 5 / fall_damage_blocks.get(block.name, 1)), 5, 30, "fell from high ground")
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
                if bpure(block.name) == "spike plant":
                    self.take_dmg(0.03, 1, 1, "got spiked")
                elif bpure(block.name) == "lava":
                    self.take_dmg(0.07, 1, 1, "tried to swim in lava")
                # cactus
                if bpure(block.name) == "cactus":
                    self.take_dmg(0.03, 1, 0.5, "got spiked")

        else:
            if self.invisible:
                self.invisible = False
                self.image.set_alpha(255)

        if self.rect.bottom < 0:
            utilize_blocks()

    def camel_move(self, camel):
        self.rect.centerx = camel.centerx - 10
        self.rect.centery = camel.centery - 35
        self.energy += 0.001

    def gain_ground(self):
        while any(self.rect.colliderect(block.rect) and bpure(block.name) not in walk_through_blocks and not is_bg(block.name) for block in all_blocks):
            self.rect.y -= 1

    def off_screen(self):
        if self.rect.right < 0:
            save_screen()
            self.rect.left = Window.width - 1
            if g.w.screen > 0:
                g.w.screen -= 1
            else:
                g.w.screen = len(g.w.data) - 1
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

        elif self.rect.left > Window.width:
            save_screen()
            self.rect.right = 1
            if g.w.screen == len(g.w.data) - 1:
                generate_screen(random.choice(bio.biomes))
            g.w.screen += 1
            empty_group(all_drops)
            utilize_blocks()
            self.gain_ground()

        elif self.rect.top > Window.height:
            save_screen()
            if g.w.layer <= 1:
                g.w.layer += 1
                self.rect.bottom = 1
                utilize_blocks()
            else:
                g.player.die("Fell into the void")

        elif self.rect.bottom < 0:
            save_screen()
            if g.w.layer >= 1:
                g.w.layer -= 1
                self.rect.top = Window.height - 1
                utilize_blocks()
                self.gain_ground()

    def update_move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        adx = abs(self.dx) + int(abs(self.dy))
        self.achievements["steps taken"] += adx
        self.achievements["steps counting"] += adx
        if self.achievements["steps counting"] >= 10_000:
            # TODO: hunger
            self.stats["hunger"]["amount"] -= nordis(5, 5)
            self.achievements["steps counting"] = 0

    def external_gravity(self):
        pass

    def animate(self):
        self.anim += g.p.anim_fps
        try:
           self.images[int(self.anim)]
        except IndexError:
            self.anim = 0
        finally:
            self.image = self.images[int(self.anim)]
