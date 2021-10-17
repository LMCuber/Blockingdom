from types import SimpleNamespace as EmptyObject, FunctionType
from math import floor, ceil, sqrt, hypot, sin, cos, atan2
from random import randint as rand, uniform as randf
from os.path import join as path, isfile, splitext
from pygame.transform import scale as pgscale
from collections import defaultdict
from pygame.mouse import set_cursor
from contextlib import suppress
from psutil import cpu_percent
from functools import partial
from threading import Thread
from threading import Timer
from itertools import chain
from random import choice
from pprint import pprint
import PIL.ImageFilter
import pygame.gfxdraw
import contextlib
import PIL.Image
import functools
import threading
import platform
import random
import types
import time
import math
import os


pygame.init()
