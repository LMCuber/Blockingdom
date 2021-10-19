from .imports import *
import tkinter
import sys
import os
import random
import platform
import time
import pycountry
import requests
import json


# constants
INF = "\u221e"  # infinity symbol (unicode)
int_to_word = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
pritn = print  # because I always mess it up when typing fast
prrint = print # because I always mess it up when typing fast


# functions
def copy_func(f):
    g = types.FunctionType(f.__code__, f.__globals__, name=f.__name__,
                           argdefs=f.__defaults__,
                           closure=f.__closure__)
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g
    

def correct(word, words):
    result = [len([char for char in word if char in test_word]) / len(word) for test_word in words]
    return result
    

def rget(url):
    return requests.get(url).text


def test():
    print(rand(0, 999))
    
    
def req2dict(url):
    try:
        return json.loads(requests.get(url).text)
    except:raise


def rel_heat(t, w):
    return round(1.41 - 1.162 * w + 0.98 * t + 0.0124 * w ** 2 + 0.0185 * w * t)


def iso_countries():
    return [country.alpha_2 for country in pycountry.countries]


def linear_noise(average, length, flatness=0):
    noise = []
    avg = average
    noise.append(nordis(avg, 2))
    for _ in range(length - 1):
        # bounds
        if noise[-1] == avg - 2:
            noise.append(choice([noise[-1], noise[-1] + 1] + [noise[-1] for _ in range(flatness)]))
        elif noise[-1] == avg + 2:
            noise.append(choice([noise[-1] - 1, noise[-1]] + [noise[-1] for _ in range(flatness)]))
        # normal
        else:
            n = [-1, 0, 1] + [0 for _ in range(flatness)]
            noise.append(noise[-1] + choice(n))
    return noise



def cform(str_):
    ret = ""
    for index, char in enumerate(str_):
        if char == ".":
            ret += "\N{BULLET}"
        elif char.isdigit() and index > 0 and str_[index - 1] != "+":
            ret += r"\N{SUBSCRIPT number}".replace("number", int_to_word[int(char)]).encode().decode("unicode escape")
        else:
            ret += char
    return ret

    
def get_clipboard():
    return tkinter.Tk().clipboard_get()
    
    
def factorial(num):
    ret = 1
    for i in range(1, num + 1):
        ret *= i
    return ret
            
    
def find(iter, cond, default=None):
    return next((x for x in iter if cond(x)), default)
    

def findi(iter, cond, default=None):
    return next((i for i, x in enumerate(iter) if cond(x)), default)


def matrix(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]

    
def flatten(oglist):
    flatlist = []
    for sublist in oglist:
        try:
            if isinstance(sublist, str):
                raise TypeError("argument to flatten() must be a non-string sequence")
            for item in sublist:
                flatlist.append(item)
        except TypeError:
            flatlist.append(sublist)
    return flatlist
    
    
def safe_file_name(name):
    """ Initializing forbidden characters / names """
    ret, ext = os.path.splitext(name)
    if Platform.os == "Windows":
        fc = '<>:"/\\|?*0'
        fw = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    elif Platform.os == "Darwin":
        fc = ":/"
    elif Platform.os == "Linux":
        fc = "/"
    """ Removing invalid words (Windows) """
    for w in fw:
        if ret.upper() == w:
            ret = ret.replace(w, "").replace(w.lower(), "")
            break
    """ Removing invalid characters """
    ret = "".join([char for char in ret if char not in fc])
    """ Removing invalid trailing characters """
    ret = ret.rstrip(". ")
    """ Adding the extension back """
    ret += ext
    """ Done """
    return ret
    

def nordis(mu, sigma):
    return int(random.gauss(mu, sigma))


def txt2list(path_):
    with open(path_, "r") as f:
        return [line.rstrip("\n") for line in f.readlines()]


def first(itr, val, def_val):
    for i, v in enumerate(itr):
        if v == val:
            return i
    return def_val


def cdict(dict_):
    return {k: v for k, v in dict_.items()}


def c1dl(list_):
    return list_[:]


def c2dl(list_):
    return [elm[:] for elm in list_]
    

def cdil(list_):
    return [{k: v for k, v in elm.items()} for elm in list_]


def solveq(eq, char="x"):
    default = [side.strip() for side in eq.split("=")]
    sides = default[:]
    num = 0
    while True:
        sides = default[:]
        sides = [side.replace(char, "*" + str(num)) for side in sides]
        if eval(sides[0]) == eval(sides[1]):
            break
        else:
            num += 1
    return num


def dis(p1: tuple, p2: tuple) -> int:
    a = p1[0] - p2[0]
    b = p1[1] - p2[1]
    dis = math.sqrt(a ** 2 + b ** 2)
    return dis


def valtok(dict_, value):
    keys = list(dict_.keys())
    values = list(dict_.values())
    return keys[values.index(value)]


def print_error(e):
    print(type(e).__name__ + ": ", *e.args)


# decorators
def merge(*funcs): # non-syntatic-sugar decorator
    def wrapper():
        for func in funcs:
            func()
            
    return wrapper


def delay(secs):
    def decorator(func):
        def wrapper():
            Thread(target=thread).start()

        def thread():
            time.sleep(secs)
            func()

        return wrapper

    return decorator


# classes
class Platform:
    os = platform.system()


class BreakAllLoops(Exception):
    pass


class Infinity:
    def __init__(self): self.def_val = "∞"
    def __lt__(self, other): return False if not isinstance(other, type(self)) else False
    def __le__(self, other): return False if not isinstance(other, type(self)) else False
    def __gt__(self, other): return True if not isinstance(other, type(self)) else False
    def __ge__(self, other): return True if not isinstance(other, type(self)) else False
    def __str__(self): return self.def_val
    def __repr__(self): return self.def_val
    def __add__(self, other): return self.def_val
    def __sub__(self, other): return self.def_val
    def __mul__(self, other): return self.def_val
    def __truediv__(self, other): return self.def_val
    def __floordiv__(self, other): return self.def_val
    def __pow__(self, other): return self.def_val
        

class TranslatorString(str):
    def __or__(self, other):
        return other
        

t = TranslatorString()
        
        
class SmartList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def moore(self, index, hl=None, area="edgescorners"):
        neighbors = []
        HL = int(sqrt(len(self))) if hl is None else hl
        indexes = []
        if "edges" in area:
            indexes.extend((                index - HL,
                            index - 1,                  index + 1,
                                            index + HL,           ))
        if "corners" in area:
            indexes.extend((index - HL - 1,             index + HL + 1,
                            
                            index + HL - 1,             index + HL + 1))
        for i in indexes:
            with suppress(IndexError):
                neighbors.append(self[i])
        return neighbors
        
    def get(self, index, default):
        return self[index] if index < len(self) else default
    
    def extendbeginning(self, itr):
        for val in itr:
            self.insert(0, val)
        
    @property
    def mean(self):
        return sum(self) / len(self)
    
    @property
    def median(self):
        return sorted(self)[len(self) // 2]
    
    @property
    def mode(self):
        freqs = dict.fromkeys(self, 0)
        for elem in self:
            freqs[elem] += 1
        max_ = max(freqs.values())
        for elem in freqs:
            if freqs[elem] == max_:
                return elem
            
            
class SmartDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __getattr__(self, attr):
        return self[attr]
        
        
class PseudoRandomNumberGenerator:
    def _last(self, num):
        return int(str(num)[-1])
        
    def trand(self):
        return int(self._last(time.time()) + self._last(cpu_percent()) / 2) / 10
import numpy as np

# context managers
class AttrExs:
    def __init__(self, obj, attr, def_val):
        self.obj = obj
        self.attr = attr
        self.def_val = def_val
    
    def __enter__(self):
        if not hasattr(self.obj, self.attr):
            setattr(self.obj, self.attr, self.def_val)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        return isinstance(exc_type, Exception)
        
        
class SuppressPrint:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
        

# constants
InvalidFilenameError = FileNotFoundError


def millis(seconds):
    """ Converts seconds to milliseconds, really nothing interesting here """
    return seconds * 1000


def perc(part, whole, max_=100):
    """ Returns the percentage, as in a percent of b and max being 100 (percent - cent - century - 100 ;)) """
    return whole / max_ * part


def relval(a, b, val):
    """ Returns the appropiate value based on the weight of the first value, i.e. with a=80, b=120 and val=50, it will return 75 """


def lget(l, i, d=None):
    """ Like a dict's get() method, but with indexes (l = list, i = index, d = default) """
    l[i] if i < len(l) else d if d is not None else None


def roundn(num, base=1):
    """ Returns the rounded value of a number with a base to round to """
    return base * round(num / base)


def chance(chance_):
    """ Returns True based on chance from a float-friendly scale of 0 to 1, i.e. 0.7 has a higher chance of returning True than 0.3 """
    return random.random() < chance_



def isdunder(str_):
    """ Returns whether a string is a dunder attribute (starts and ends with a double underscore (dunderscore)) """
    return str_.startswith("__") and str_.endswith("__")


def hmtime():
    """ Returns the current time in this format: f"{hours}:{minutes}" """
    return time.strfime("%I:%M")


def revnum(num):
    """ Returns the reverse of a number, i.e. 1 == -1 and -1 == 1 (0 != -0; 0 == 0) """
    return -num if num > 0 else abs(num)
    