#!/usr/bin/env python3

from PIL import Image
import numpy as np
import os as os
from sys import argv, exit
from random import randint
import colorsys
import string


def average_color(im):
    size = im.size[0] * im.size[1]
    if(im.format != "RGB"):
        im = im.convert("RGB")

    # Make a numpy array of the pixels
    pixel_matrix = np.asarray(im)
    # Reduces the pixel matrix to a color sum (triple of rgb sums)
    color_sums = np.add.reduce(np.add.reduce(pixel_matrix))
    # Initialize an empty array for the colors
    colors = []
    for color_sum in color_sums:
        # Append the averaged color value to the colors
        colors.append(int(color_sum//size))
    return tuple(colors)


def rename_images(image_list, start_val=1, int_str_func=str, step=1):
    if step<0:
        step = -step
    current_num = start_val
    for image in image_list:
        # Start by finding a name that hasn't been taken in the folder
        new_name = int_str_func(current_num) + "." + image.format.lower()
        # We don't ever want to overwrite a file so we find an unusued name
        while os.path.isfile(new_name):
            current_num += step
            new_name = int_str_func(current_num) + "." + image.format.lower()
        os.rename(image.filename, new_name)

        current_num += step


alph = string.digits + string.ascii_uppercase + string.ascii_lowercase
alph_len = len(alph)
reverse_alph = dict({(alph[i], i) for i in range(alph_len)})


def name_to_int(name):
    val = 0
    for letter in name:
        val *= alph_len
        val += reverse_alph[letter]
    return val


def int_to_name(n):
    s = ""
    while n > 0:
        (m, q) = divmod(n, alph_len)
        n = m
        s = alph[q] + s
    if s == "":
        s = "0"
    return s


def name_add(name, val):
    return int_to_name(name_to_int(name) + val)


if __name__ == '__main__':
    # Change the current directory to the selected folder
    try:
        os.chdir(argv[1])
    except NotADirectoryError:
        print("Argument is not a folder!")
        exit()

    f_list = os.listdir()

    image_list = []

    for f in f_list:
        try:
            im = Image.open(f)
        except OSError:
            continue
        # We've opened an image, now we want to average its colors and move on
        im.avg_col = average_color(im)  # Store the averages with their images
        im.close()  # Closes the images file descriptor and releases memory
        image_list.append(im)

    image_list.sort(key=lambda image: colorsys.rgb_to_hsv(*(image.avg_col)))

    # We pick a starting number. This isn't strictly necessary but I felt it
    # would be nicer than a fixed starting point
    start_num = randint(alph_len**8, alph_len**9/2)
    rename_images(image_list, start_num, int_str_func=int_to_name, step=377)
