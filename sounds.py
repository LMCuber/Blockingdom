from pyengine.pgbasics import *


def blocksound(sound):
    return pygame.mixer.Sound(path("Audio", "Block_Sounds", sound + ".wav"))


pickup_sound = blocksound("pickup")
