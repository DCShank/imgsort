#!/usr/bin/env python3

from PIL import Image
import numpy as np
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
    im = Image.open("test_image.jpg")
    final = average_color(im)
    print(final)
    print(colorsys.rgb_to_hsv(*final))
