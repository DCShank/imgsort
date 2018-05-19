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


def identity(*args):
    if len(args) == 0:
        return
    if len(args) == 1:
        return args[0]
    return args


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

parser.add_argument('-l', action='store_true',
                    help='Print the output of the sort as a list')

parser.add_argument('-r', action='store_true',
                    help=('Rename the images to strings that are sorted the '
                          'same way lexicographically and by the sorting '
                          'methods selected'))

parser.add_argument('-c', '--change-file', dest='change', type=str, nargs='?',
                    default=None, const='change_history.txt',
                    help="Save a text file with the list of renamed images.")

parser.add_argument('-undo', type=str, nargs=1, metavar="CHANGE_LIST_FILE",
                    help=("Undoes the changes from CHANGE_LIST.TXT in the "
                          "selected directory if possible.\nOVERRIDES NORMAL "
                          "SORTING BEHAVIOR. DOES NOT USE INCLUDE/EXCLUDE"))

parser.add_argument('-exclude', type=str, nargs='?', default=None,
                    help="Regular expression for files to exclude")

parser.add_argument('-include', type=str, nargs='?', default=None,
                    help="Regular expression for files to include")


parser.add_argument('-v', '--reversed', dest='rev', action='store_const',
                    const=reversed,
                    default=(lambda x: x),
                    help='Reverses the order of sorting')


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
        next_name = get_next_name(gen, image)
        try:
            image.oldfname = image.filename
            os.rename(image.filename, next_name)
            image.filename = next_name
        except:
            print("Could not rename {}!".format(image.filename))
            # This is unecessary, but I think it makes it clear that we just
            # keep going
            continue


def trychdir(directory):
    """
    Tries to change into the indicated directory, exiting with exit failure
    if it fails.
    """
    try:
        os.chdir(args.directory)
    except NotADirectoryError:
        print("Argument is not a directory!")
        exit(1)
    except:
        print("Could not change into the directory!")
        exit(1)


def undo(change_file, directory):
    try:
        f = open(change_file)
    except:
        print("Could not open the change file")
        exit(1)

    trychdir(directory)

    valid_change_exp = re.compile(r"(\S|\\\w)+ -> (\S|\\\w)+")
    line_num = 0

    for change in f:
        change = change.strip()
        line_num += 1
        if not valid_change_exp.fullmatch(change):
            print("Line {} wasn't a valid file change!".format(line_num))
            print(change)
            continue
        old_name, new_name = change.split(" -> ")
        try:
            os.rename(new_name, old_name)
        except:
            print("Could not rename {} to {}!".format(old_name, new_name))
            continue
    exit(0)


if __name__ == '__main__':
    if len(argv) == 1:
        parser.print_help()
        exit()

    # Parses the arguments, filling args with a bunch of variables
    args = parser.parse_args()

    if args.undo:
        undo(args.undo[0], args.directory)

    # Change the current directory to the selected folder
    trychdir(args.directory)

    # A starting value for names. I arbitrarily decided that I would like a
    # random starting value.
    # Note that because of shoddy work, this will have problems renaming lists
    # of greater than 36^4 images.
    start_num = randint(alph_len**3, alph_len**4/2)

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
        col_sorts = ('hue', 'saturation', 'value', 'brightness')
        if args.primary_sort in col_sorts or args.secondary_sort in col_sorts:
            im.avg_col = average_color(im)  # Store the average with the image
        im.close()  # Closes the images file descriptor and releases memory
        image_list.append(im)

    # Dictionary of functions that take an image and output a sorting key
    sort_keys = {None:         lambda image: (),
                 'dimensions': lambda image: image.size,
                 'resolution': lambda image: image.size,
                 'hue':        lambda image: rgb_to_hsv(*(image.avg_col))[0],
                 'saturation': lambda image: rgb_to_hsv(*(image.avg_col))[1],
                 'value':      lambda image: rgb_to_hsv(*(image.avg_col))[2],
                 'brightness': lambda image: rgb_to_hsv(*(image.avg_col))[2]
                 }

    # Sort the list based on the selected sorts.
    image_list.sort(key=lambda image: (sort_keys[args.primary_sort](image),
                                       sort_keys[args.secondary_sort](image)))

    # If the user wanted the output reversed we do that.
    image_list = args.rev(image_list)

    if args.r:
        if args.change:
            try:
                print(args.change)
                cfile = open(args.change, 'w')
                for image in image_list:
                    out = (im.oldfname.replace(' ', '\\ ') + ' -> ' +
                           im.filename.replace(' ', '\\ ') + '\n')
                    print(out)
                    cfile.write(out)
            except Exception as err:
                print("Could not write the change history file! Aborting.")
                print(err)
                exit(1)
        rename_images(image_list, start_num, 5)

    # List is also the default behavior, so we include that
    if args.l or not (args.l or args.r):
        if args.r:
            # If the files were renamed, we want to indicate both the old file
            # name and the new file name, while still showing them in order.
            print(*map(lambda im: (
                       im.oldfname.replace(' ', '\\ ') + ' -> ' +
                       im.filename.replace(' ', '\\ ')), image_list),
                  sep='\n')
        else:
            print(*map(lambda im: im.filename.replace(' ', '\\ '), image_list),
                  sep='\n')

    exit(0)
