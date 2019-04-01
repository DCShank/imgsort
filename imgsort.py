#!/usr/bin/env python3

try:
    from tqdm import tqdm
except ImportError:
    # If tqdm isn't installed, just make the function return the iterable
    def tqdm(x):
        return x
from PIL import Image
from colorsys import rgb_to_hsv
from sys import argv, exit, stderr
from random import randint
import numpy as np
from pathlib import Path
import os
import re
import string
import argparse


parser = argparse.ArgumentParser(description='Sorts images')

parser.add_argument('directory', type=str,
                    help='The directory containing the images you want to sort'
                    )

parser.add_argument('-p', '--primary_sort', type=str,
                    default='resolution',
                    help='The primary sorting method. Defaults to resolution',
                    choices={'hue', 'saturation', 'value', 'brightness',
                             'resolution', 'dimensions'})

parser.add_argument('-s', '--secondary_sort', type=str,
                    default=None,
                    help='The secondary sorting method used to break ties',
                    choices={'hue', 'saturation', 'value', 'brightness',
                             'resolution', 'dimensions', None})

parser.add_argument('-l', '--list', action='store_true',
                    help='Print the output of the sort as a list')

parser.add_argument('-r', '--rename', action='store_true',
                    help=('Rename the images to strings that are sorted the '
                          'same way lexicographically and by the sorting '
                          'methods selected'))

parser.add_argument('-c', '--change-log', dest='change', type=str, nargs='?',
                    default=None, const='change-log.txt',
                    help='Save a text file with the list of renamed images. '
                         'No effect without rename')

parser.add_argument('-u', '--undo', type=str,
                    metavar='CHANGE_LIST_FILE',
                    help=('Undoes the changes from CHANGE_LIST.TXT in the '
                          'selected directory if possible. OVERRIDES NORMAL '
                          'SORTING BEHAVIOR. DOES NOT USE INCLUDE/EXCLUDE'))

parser.add_argument('-e', '--exclude', type=str, default=None,
                    metavar="EXCLUDE_REGEX",
                    help='Regular expression for files to exclude. '
                         'Excludes files whose whole names match the regex')

parser.add_argument('-i', '--include', type=str, default=None,
                    metavar="INCLUDE_REGEX",
                    help='Regular expression for files to include.'
                         'Includes files whose whole names match the regex')


parser.add_argument('-v', '--reversed', dest='rev', action='store_const',
                    const=reversed,
                    default=(lambda x: x),
                    help='Reverses the order of sorting')


def average_color(im):
    size = im.size[0] * im.size[1]
    if(im.format != 'RGB'):
        im = im.convert('RGB')

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


def int_to_name(n):
    s = ''
    while n > 0:
        (m, q) = divmod(n, alph_len)
        n = m
        s = alph[q] + s
    if s == '':
        s = '0'
    return s


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

    print('Renaming images:', file=stderr)
    for image in tqdm(image_list):
        next_name = get_next_name(gen, image)
        try:
            image.oldfname = image.filename
            os.rename(image.filename, next_name)
            image.filename = next_name
        except OSError:
            print(f'Could not rename {image.filename}!', file=stderr)
            continue


def undo(change_file):
    valid_change_exp = re.compile(r'(\S|\\\w)+ -> (\S|\\\w)+')
    with open(change_file, 'r') as f:
        line_num = 0

        for line in f:
            change = line.strip()
            line_num += 1
            if not valid_change_exp.fullmatch(change):
                print(f"Line {line_num} wasn't a valid file change!",
                      file=stderr)
                print(change, file=stderr)
                continue
            old_name, new_name = change.split(' -> ')
            try:
                os.rename(new_name, old_name)
            except OSError:
                print(f'Could not rename {old_name} to {new_name}!',
                      file=stderr)
                continue


class ImageData(object):
    """ A class to capture the relevant data about an image for sorting """
    def __init__(self, filename, avg_col, size, format):
        self.filename = filename
        self.avg_col = avg_col
        self.size = size
        self.oldfname = filename
        self.format = format


if __name__ == '__main__':
    if len(argv) == 1:
        parser.print_help()
        exit(0)

    # Parses the arguments, filling args with a bunch of variables
    args = parser.parse_args()

    # Find the actual path to the file
    if args.undo:
        try:
            args.undo = Path(args.undo).resolve(strict=True)
        except FileNotFoundError:
            print("Undo file could not be found!")
            exit(1)
        except RuntimeError:
            print("Entered an infinite loop along resolution path!")
            exit(1)

    # Change the current directory to the selected folder
    directory = Path(args.directory)
    if not directory.exists():
        print("Directory argument does not exist!", file=stderr)
        exit(1)
    if not directory.is_dir():
        print("Directory argument is not a directory!", file=stderr)
        exit(1)
    try:
        os.chdir(args.directory)
    except NotADirectoryError:
        # We handle this again because there's technically a race condition
        print("Directory argument is not a directory!", file=stderr)
        parser.print_usage()
        exit(1)
    except OSError:
        print('Could not change into the directory!', file=stderr)
        exit(1)

    # If we want to undo, we immediately do that then exit.
    if args.undo:
        undo(args.undo)
        exit(0)

    # A starting value for names. I arbitrarily decided that I would like a
    # random starting value.
    # Note that because of shoddy work, this will have problems renaming lists
    # of greater than about (36^6)/10 images.
    start_num = randint(alph_len**5, alph_len**6/2)

    # Get the list of files in the directory
    f_list = os.listdir()

    # Filter the list by includes and excludes
    if args.include is not None:
        try:
            include_exp = re.compile(args.include)
        except Exception:
            print('Invalid include Regex!', file=stderr)
            parser.print_usage()
            exit(1)
        temp = list(filter(include_exp.fullmatch, f_list))
        f_list = temp

    if args.exclude is not None:
        try:
            exclude_exp = re.compile(args.exclude)
        except Exception:
            print('Invalid exclude Regex!', file=stderr)
            parser.print_usage()
            exit(1)
        temp = list(filter(lambda s: not exclude_exp.fullmatch(s), f_list))
        f_list = temp

    # Check if we need to sort by average color value
    col_sorts = ('hue', 'saturation', 'value', 'brightness')
    col = args.primary_sort in col_sorts or args.secondary_sort in col_sorts

    # Initialize an empty list of image data
    image_list = []
    # Find all the images and do the needed calculations.
    if col:
        print('Finding average colors and gathering image data:',
              file=stderr)
    else:
        print('Gathering image data:', file=stderr)
    for f in tqdm(f_list):
        try:
            with Image.open(f) as im:
                # We've opened an image, now we want to average its colors
                avg_col = None
                # We only want to calculate the average color if we need to!
                if col:
                    avg_col = average_color(im)
                data = ImageData(avg_col=avg_col,
                                 size=[dim for dim in im.size],
                                 filename=im.filename,
                                 format=im.format)
                image_list.append(data)
        except IOError:
            # Handles the case where the file is not an image
            continue

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
    # args.rev is either the identity function or the 'reversed' function
    image_list = args.rev(image_list)

    if args.rename:
        lfile = None
        if args.change:
            try:
                lfile = open(args.change, 'w')
            except OSError as err:
                print('Could not write the rename log file!\n'
                      'Aborting.', file=stderr)
                print(err, file=stderr)
                exit(1)
        rename_images(image_list, start_num, 5)
        if lfile:
            for image in image_list:
                out = (image.oldfname.replace(' ', '\\ ') + ' -> ' +
                       image.filename.replace(' ', '\\ ') + '\n')
                lfile.write(out)
            lfile.close()

    # List is also the default behavior, so we do that if nothing is selected
    if args.list or not (args.list or args.rename):
        if args.rename:
            # If the files were renamed, we want to indicate both the old file
            # name and the new file name, while still showing them in order.
            print(*map(lambda im: (
                       im.oldfname.replace(' ', '\\ ') + ' -> ' +
                       im.filename.replace(' ', '\\ ')), image_list),
                  sep='\n')
        else:
            print(*map(lambda im: im.filename.replace(' ', '\\ '), image_list),
                  sep='\n')
    print('Completed', file=stderr)
    exit(0)
