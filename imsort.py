#!/usr/bin/env python3

from PIL import Image
import numpy as np
import os as os
from sys import argv, exit
from random import randint
from colorsys import rgb_to_hsv
import string
import argparse


parser = argparse.ArgumentParser(description="Sort images")

parser.add_argument('directory', type=str, nargs='?',
                    default='.',
                    help='The directory containing the images you want to sort'
                    )

parser.add_argument('-primary_sort', type=str, nargs='?', default='color',
                    help='The primary sorting method.',
                    choices={'color', 'resolution', 'dimensions'})

parser.add_argument('-secondary_sort', type=str, nargs='?', default=None,
                    help='The secondary sorting method used to break ties',
                    choices={'color', 'resolution', 'dimensions', None})

parser.add_argument('-output', type=str, nargs='?', default='list',
                    help='The desired output of the program',
                    choices={'rename', 'list'})


parser.add_argument('--reversed', dest='rev', action='store_const',
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
    args = parser.parse_args()

    # Change the current directory to the selected folder
    try:
        os.chdir(args.directory)
    except NotADirectoryError:
        print("Argument is not a folder!")
        exit()

    # A starting value for names. I arbitrarily decided that I would like a
    # random starting value.
    start_num = randint(alph_len**3, alph_len**4/2)

    # This whole function look up table could probably be moved to the
    # the parsing section.
    # Can select sort keys based on input arguments
    sort_funcs = {None: lambda image: (),
                  'dimensions': lambda image: image.size,
                  'resolution': lambda image: image.size,
                  'color': lambda image: rgb_to_hsv(*(image.avg_col))}

    # Can select output function based on input arguments
    # Start num and 99 were selected arbitrarily. This is bad practice, sorry.
    out_funcs = {'list': lambda ims: print(*map(lambda im: im.filename, ims),
                                           sep='\n'),
                 'rename': lambda images: rename_images(images, start_num, 5)}

    # Get the list of files in the directory
    f_list = os.listdir()

    # Initialize an empty list of images.
    image_list = []
    # Find all the images and do the needed calculations.
    for f in f_list:
        try:
            im = Image.open(f)
        except OSError:
            continue
        # We've opened an image, now we want to average its colors and move on
        if 'color' == args.primary_sort or 'color' == args.secondary_sort:
            im.avg_col = average_color(im)  # Store the average with the image
        im.close()  # Closes the images file descriptor and releases memory
        image_list.append(im)

    # Sort the list based on the selected sorts.
    image_list.sort(key=lambda image: (sort_funcs[args.primary_sort](image) +
                                       sort_funcs[args.secondary_sort](image)))

    # If the user wanted the output reversed we do that.
    image_list = args.rev(image_list)

    # Do the requested output effect.
    out_funcs[args.output](image_list)
