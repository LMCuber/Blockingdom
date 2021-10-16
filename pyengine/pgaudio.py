from .imports import *
import pygame
import wave
import random


def pitch_shift(pg_sound, from_=0.7, to=1.3, frame_rate=44_100):
    nchannels = 1
    sample_width = 2
    change_rate = random.uniform(from_, to)
    rate = frame_rate
    frames = pg_sound.get_raw()
    tempfile_path = path("tempfiles", "temp_sound.wav")
    with suppress(FileExistsError):
        os.mkdir("tempfiles")
    with wave.open(tempfile_path, 'wb') as new:
        new.setnchannels(nchannels)
        new.setsampwidth(sample_width)
        new.setframerate(rate * change_rate)
        new.writeframes(frames)
    new_pg_sound = pygame.mixer.Sound(tempfile_path)
    os.remove(tempfile_path)
    return new_pg_sound
