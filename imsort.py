#!/usr/bin/env python3

from PIL import Image
import numpy as np
import os as os
from sys import argv, exit
from random import randint
from colorsys import rgb_to_hsv
import re
import string
import argparse


parser = argparse.ArgumentParser(description="Sort images")

parser.add_argument('directory', type=str, nargs='?',
                    help='The directory containing the images you want to sort'
                    )

parser.add_argument('-primary_sort', type=str, nargs='?', default='resolution',
                    help='The primary sorting method.',
                    choices={'hue', 'saturation', 'value', 'brightness',
                             'resolution', 'dimensions'})

parser.add_argument('-secondary_sort', type=str, nargs='?', default=None,
                    help='The secondary sorting method used to break ties',
                    choices={'hue', 'saturation', 'value', 'brightness',
                             'resolution', 'dimensions', None})

parser.add_argument('-output', type=str, nargs='?', default='list',
                    help='The desired output of the program',
                    choices={'rename', 'list'})

parser.add_argument('-exclude', type=str, nargs='?', default=None,
                    help="Regular expression for files to exclude")

parser.add_argument('-include', type=str, nargs='?', default=None,
                    help="Regular expression for files to include")


parser.add_argument('-r', '--reversed', dest='rev', action='store_const',
                    const=reversed,
                    default=(lambda x: x), help='Reverses the output')


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


alph = string.digits + string.ascii_lowercase
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


def num_gen(start_val, step):
    current_val = start_val
    while True:
        yield current_val
        current_val += step


def get_next_name(num_gen, image):
    while True:
        new_name = (
                    int_to_name(next(num_gen))
                    + '_' + str(image.size[0]) + 'x' + str(image.size[1])
                    + '.' + image.format.lower()
                    )
        if not os.path.isfile(new_name):
            return new_name


def rename_images(image_list, start_val=1, step=1):
    # Make sure that step is a positive integer
    if step == 0:
        step += 1
    step = abs(step)

    gen = num_gen(start_val, step)

    for image in image_list:
        os.rename(image.filename, get_next_name(gen, image))


if __name__ == '__main__':
    if len(argv) == 1:
        parser.print_help()
        exit()

    args = parser.parse_args()

    # Change the current directory to the selected folder
    try:
        os.chdir(args.directory)
    except NotADirectoryError:
        print("Argument is not a folder!")
        exit(1)

    # A starting value for names. I arbitrarily decided that I would like a
    # random starting value.
    start_num = randint(alph_len**3, alph_len**4/2)

    # Dictionary of functions that take an image and output a sorting key
    sort_keys = {None:         lambda image: (),
                 'dimensions': lambda image: image.size,
                 'resolution': lambda image: image.size,
                 'hue':        lambda image: rgb_to_hsv(*(image.avg_col))[0],
                 'saturation': lambda image: rgb_to_hsv(*(image.avg_col))[1],
                 'value':      lambda image: rgb_to_hsv(*(image.avg_col))[2],
                 'brightness': lambda image: rgb_to_hsv(*(image.avg_col))[2]
                 }

    # Can select output function based on input arguments
    # Start num and 99 were selected arbitrarily. This is bad practice, sorry.
    out_funcs = {'list': lambda ims: print(*map(lambda im: im.filename, ims),
                                           sep='\n'),
                 'rename': lambda images: rename_images(images, start_num, 5)}

    # Get the list of files in the directory
    f_list = os.listdir()

    # Filter the list by includes and excludes
    if args.include is not None:
        try:
            include_exp = re.compile(args.include)
            temp = list(filter(include_exp.fullmatch, f_list))
            f_list = temp
        except:
            print("Invalid include Regex!")
            parser.print_usage()
            exit(1)

    if args.exclude is not None:
        try:
            exclude_exp = re.compile(args.exclude)
            temp = list(filter(lambda s: not exclude_exp.fullmatch(s), f_list))
            f_list = temp
        except:
            print("Invalid exclude Regex!")
            parser.print_usage()
            exit(1)

    # Initialize an empty list of images.
    image_list = []
    # Find all the images and do the needed calculations.
    for f in f_list:
        try:
            im = Image.open(f)
        except OSError:
            continue
        # We've opened an image, now we want to average its colors and move on
        # We only want to calculate the average color if we need to!
        col_sorts = ('hue', 'saturation', 'value')
        if args.primary_sort in col_sorts or args.secondary_sort in col_sorts:
            im.avg_col = average_color(im)  # Store the average with the image
        im.close()  # Closes the images file descriptor and releases memory
        image_list.append(im)

    # Sort the list based on the selected sorts.
    image_list.sort(key=lambda image: (sort_keys[args.primary_sort](image),
                                       sort_keys[args.secondary_sort](image)))

    # If the user wanted the output reversed we do that.
    image_list = args.rev(image_list)

    # Do the requested output effect.
    out_funcs[args.output](image_list)
    exit(0)
