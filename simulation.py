from phystring import PhyString
from particle import Particle, Particles

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

import os
import math
import time
import random
import time
import datetime

class Simulation:
    """
        Class that wraps the whole simulation thing
    """
    IMG_PREFIX = "QuantumString"
    def __init__(self, dt: float, time_steps: int, string_len: float, string_density: float, string_tension: float, exitation_fx, ic_pos: list, ic_vel: list, particles, log=True):
        """
            Initialisation of the simulation

            :param dt: value of the time step [s]
            :param time_steps: number of time steps
            :param string_len: length of the string [m]
            :param string_c: celerity of the string [m/s]
            :param string_density: linear density of the string [kg/m]
            :param excitation_fx: function corresponding to the condition at the left side of the string
            :param ic_pos: initial condition of the position of the string
            :param ic_vel: initial condition of the velocity of the string
            :param particles: Particles object
            :param log: if True, prints the simulation loading

            :type dt: float
            :type time_steps: int
            :type string_len: float
            :type string_c: float
            :type string_density: float
            :type excitation_fx: function
            :type ic_pos: list
            :type ic_vel: list
            :type particles: Particles object
            :type log: bool

        """
        string_discret = Simulation.compute_string_discret(string_len, string_tension, string_density, dt)
        self.log = log
        self.time_steps = time_steps
        self.dt = dt

        self.s = PhyString(string_len, string_discret, dt, string_density, string_tension, exitation_fx, ic_pos, ic_vel, particles)
    
    def __repr__(self):
        return "[SIMULATION]    Δt={}s, Δx={}m, time steps={}, string steps (nb discretisation)={}; ".format(self.s.dt, self.s.dx, self.time_steps, self.s.nb_linear_steps)

    def run(self, path: str, anim=True, file=True, log=True, dpi=96, res=(320, 240), fdur=12):
        """
            Runs the simulation with options to save it as a animation and/or in a file

            :param path: path for the simulation to be saved
            :type path: str
        """
        dtnow = datetime.datetime.now()
        timestamp = int(dtnow.timestamp())
        print("SIMULATION:") if self.log else None

        if file:
            ffn = "QuantumString-field_{}.txt".format(timestamp)
            pfn = "QuantumString-particles_{}.txt".format(timestamp)
            idtxtfield = "QUANTUM STRING SIMULATION ({}): {} {}\n".format(dtnow.isoformat(), self, self.s)
            idtxtparts = "QUANTUM STRING SIMULATION ({}): {} {}\n".format(dtnow.isoformat(), self, self.s.particles)
            ff = open("{}\\{}".format(path, ffn), "w", encoding="utf-8")
            pf = open("{}\\{}".format(path, pfn), "w", encoding="utf-8")
            ff.write(idtxtfield)
            pf.write(idtxtparts)

        template_anim = Image.new('RGB', res, color=(255, 255, 255))
        if anim:
            """
                draw on the template...
            """

        list_img = []
        for t in range(0, self.time_steps):
            if t > 1: # do not update when the timesteps are lower than 1 bc this corresponds to the two initial fields
                self.s.update()
            f = self.s.field.get_val_time(t)
            pp = self.s.particles.list_pos(tstep=t)
            if anim: # create the images for the animation
                list_img.append(self.instant_img(template_anim.copy(), f, pp, t))
            if file: # append the current field to the file
                fstr = Simulation.list2str(f)
                pstr = Simulation.list2str(pp)
                ff.write("{}\n".format(fstr))
                pf.write("{}\n".format(pstr))
            print("{}/{}".format(t, self.time_steps)) if self.log else None
        if anim:
            print("animation finalisation...") if self.log else None
            self.create_anim(list_img, path, id_img=timestamp, fdur=fdur)
        if file:
            print("output file finalisation...") if self.log else None

    
    @staticmethod
    def compute_string_discret(l: float, T: float, rho: float, dt: float):
        """
            Returns the number of cells needed for the simulation, considering the length, the celerity and the time step
            Follows the equation Δx/Δt = c

            :param l: length of the string [m]
            :param T: tension [kg.m/s²]
            :param rho: linear density [kg/m]
            :param dt: time step [s]

            :return: number n of cells required for the string, such as l = n Δx
            :rtype: int
        """
        c = np.sqrt(T/rho)
        return int(l/c/dt)
    
    @staticmethod
    def list2str(l: list):
        """
            Converts a list to a string in a simple format for our use

            :param l: a list to be converted
            :type l: list

            :return: list converted into string
            :rtype: str
        """
        return str(l).replace("[", "").replace("]", "").replace("\n", "")
    
    def print(self):
        """
            Prints a quick animation of the simulation in the console
        """
        clear_console = lambda: os.system("cls")
        for f in self.s.field.val:
            len_char = self.s.dx # [m]
            nb_char = self.s.nb_linear_steps
            interval = max(f) + 1e-6
            min_val = min(f)
            while interval >= min_val:
                upper = interval
                delta = 0.5*len_char
                mid = upper - delta
                vals_in_row = np.where(np.abs(f - mid) < delta)[0]
                row = [" "]*nb_char
                for i in vals_in_row:
                    row[i] = "."
                interval -= len_char
                print("".join(row), end="\n")
            time.sleep(self.s.dt)
            clear_console()
    
    def instant_img(self, baseimg: Image, field: list, particles_pos: list, tstep: int, yscale=5.0) -> Image:
        """
            Create an image of the current state of the simulation

            :param baseimg: base PIL Image to write onto
            :param field: state of the string
            :param particles_pos: the position (cell) of each particles
            :param tstep: time step corresponding to the state
            :param yscale: scaling factor for vertical axis

            :return: Pillow image of the current state
            :rtype: PIL.Image
        """
        d = ImageDraw.Draw(baseimg)
        (lx, ly) = baseimg.size
        margin = 15
        mass_rad = 1
        (ox, oy) = (margin, int(0.5*ly))
        pix_per_m = int(lx/self.s.length) - margin*2
        n = [i for i in range(0, 2*self.s.nb_linear_steps)]
        n = np.array(n)
        forx = n % 2 == 0
        fory = forx == False
        linx = np.linspace(0, self.s.length, self.s.nb_linear_steps)
        line_vals = np.zeros(shape=2*self.s.nb_linear_steps)
        px = linx*pix_per_m + ox
        py = -field*pix_per_m*yscale + oy
        line_vals[forx] = px
        line_vals[fory] = py

        d.line(list(line_vals), fill=(0, 0, 0))
        d.text((10, 10), "Hello world!", fill=(255, 0, 0))

        for p in particles_pos:
            pos = (px[p], py[p])
            d.ellipse([pos[0] - mass_rad, pos[1] - mass_rad, pos[0] + mass_rad, pos[1] + mass_rad], fill=(255, 0, 0))

        return baseimg
    
    def create_anim(self, list_images: list, path: str, id_img=0, fdur=12):
        """
            Creates a gif out of the images given

            :param list_images: list of the Pillow images
            :param path: path for the gif to be created
            :param id_img: suffix at the end of the name of the image (for identification)

            :type list_images: list
            :type path: str
            :type id_img: int

            :return: path of the animation created
            :rtype: str
        """
        suffix = "" if id_img == 0 else id_img
        pathgif = "{}\\{}-{}.webp".format(path, Simulation.IMG_PREFIX, suffix)
        list_images[0].save(pathgif, duration=[fdur]*len(list_images), save_all=True, append_images=list_images[1:], optimize=False, loop=0)
        return pathgif


class RestString(Simulation):
    """
        Abstraction of Simulation: the initial field is at rest
    """
    def __init__(self, dt: float, time_steps: int, string_len: float, string_density: float, string_tension: float, exitation_fx, particles, log=True):
        string_discret = Simulation.compute_string_discret(string_len, string_tension, string_density, dt) # number of cells in the string
        ic_pos = [0]*string_discret
        ic_vel = ic_pos.copy()
        super().__init__(dt, time_steps, string_len, string_density, string_tension, exitation_fx, ic_pos, ic_vel, particles, log=log)

class FreeString(RestString):
    """
        Abstraction of RestString: the system is particle free
    """
    def __init__(self, dt: float, time_steps: int, string_len: float, string_density: float, string_tension: float, exitation_fx, log=True):
        string_discret = Simulation.compute_string_discret(string_len, string_tension, string_density, dt)
        particles = Particles(string_discret, [])
        super().__init__(dt, time_steps, string_len, string_density, string_tension, exitation_fx, particles, log=log)

class CenterFixed(RestString):
    """
        Abstraction of RestString: the system has a single particle in the center of the string
    """
    def __init__(self, dt: float, time_steps: int, string_len: float, string_density: float, string_tension: float, exitation_fx, mass_particle: float, pulsation_particle: float, log=True):
        string_discret = Simulation.compute_string_discret(string_len, string_tension, string_density, dt)
        center_string = math.floor(string_discret*0.5)
        p = Particle(center_string, 0.0, mass_particle, pulsation_particle, True, string_discret)
        particles = Particles(string_discret, [p])
        super().__init__(dt, time_steps, string_len, string_density, string_tension, exitation_fx, particles, log=log)