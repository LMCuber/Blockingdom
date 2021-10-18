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
