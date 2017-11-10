#!/usr/bin/env python3

from PIL import Image
import numpy as np
import os as os
from sys import argv, exit
from random import randint
import colorsys


def average_color(im):
    size = im.size[0] * im.size[1]

    # Make a numpy array of the pixels
    pixel_matrix = np.asarray(im)
    # Reduces the pixel matrix to a color sum
    color_sums = np.add.reduce(np.add.reduce(pixel_matrix))
    # Initialize an empty array for the colors
    colors = []
    for color_sum in color_sums:
        # Append the averaged color value to the colors
        colors.append(int(color_sum//size))
    return tuple(colors)


if __name__ == '__main__':
    # Start by changing the current directory to the seleceted folder
    try:
        os.chdir(argv[1])
    except:
        print("Argument is not a folder!")
        exit()

    f_list = os.listdir()

    # This will store a list of tuples of images and their average colors.
    # (average_color, image_info)
    image_list = []

    for f in f_list:
        try:
            im = Image.open(f)
        except:
            continue
        # Later on I should consider changing this to add the original f
        # directory because there could be problems with number of files open
        try:
            # We need to convert every image to RGB, but that erases the name
            # and file format. We store and reset them.
            form = im.format
            name = im.filename
            im = im.convert("RGB")
            im.filename = name
            im.format = form
            # Get the average color. This is what we're using to sort
            av_col = average_color(im)
            image_list.append((av_col, im))
        except:
            continue

    image_list.sort(key=lambda tup: colorsys.rgb_to_hsv(*(tup[0])))

    # We pick a starting number. This isn't strictly necessary but I felt it
    # would be nicer than a fixed starting point
    current_num = randint(10000000, 99999999)
    for (rgb, image) in image_list:
        # Start by finding a name that hasn't been taken in the folder
        new_name = str(current_num) + "." + image.format.lower()
        # We don't ever want to overwrite a file so we find an unusued name
        while os.path.isfile(new_name):
            current_num += 1
            new_name = str(current_num) + "." + image.format.lower()
        os.rename(image.filename, new_name)

        current_num += 1
