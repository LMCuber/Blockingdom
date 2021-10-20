import PIL.Image
import PIL.ImageFilter
import PIL.ImageColor
import PIL.ImageDraw
import pygame


# shapes
...

# functions
def round_corners(pil_img, radius):
    circle = PIL.Image.new('L', (radius * 2, radius * 2), 0)
    draw = PIL.ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
    alpha = PIL.Image.new('L', pil_img.size, 255)
    w, h = pil_img.size
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
    pil_img.putalpha(alpha)
    return pil_img


def hex_to_rgb(value):
    return PIL.ImageColor.getcolor(value, "RGB")


def pil_rot(pil_img, angle):
    return pil_img.rotate(angle, PIL.Image.NEAREST, expand=1)
    
    
def pil_blur(pil_img, radius=2):
    return pil_img.filter(PIL.ImageFilter.GaussianBlur(radius=radius))


def pil2pg(pil_img):
    data = pil_img.tobytes()
    size = pil_img.size
    mode = pil_img.mode
    return pygame.image.fromstring(data, size, mode).convert_alpha()
    
    
def pil_rect2pg(pil_rect):
    return (pil_rect[0], pil_rect[1], pil_rect[2] - pil_rect[0], pil_rect[3] - pil_rect[1])


def pil_pixelate(pil_img, size):
    small = pil_img.resize(size, resample=PIL.Image.BILINEAR)
    result = small.resize(pil_img.size, PIL.Image.NEAREST)
    return result
    