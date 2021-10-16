from pyengine.imports import *


def blocksound(sound):
    return pygame.mixer.Sound(path("Block_Sounds", sound + ".wav"))


pickup_sound = blocksound("pickup")
