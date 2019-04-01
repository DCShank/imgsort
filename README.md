imgsort
=======

**imgsort** is a tool for sorting images by a variety of features.
Currently sorting by hue, saturation, brightness, and resolution are available.
For a help menu, use `path/to/imgsort.py -h`.

Requires Pillow to run.
```
pip install pillow
```

You may optionally install tqdm for progress bars.
```
pip install tqdm
```

## Example usage

Sort the images by hue and print the list to console:
```
david:~$ ./imgsort.py image_directory/ -p hue -l
red_image.gif
blue_image.png
```

Sort the images by dimensions and rename to be sorted lexicographically:
```
david:~$ ./imgsort.py image_directory/ -p dimensions -r
```

Sort the images by brightness and rename to be sorted lexicographically, excluding images with food in their names.
```
david:~$ ./imgsort.py image_directory/ -p brightness -r -e ".*food.*"
```

### Notes

Options currently include sorting by hue, saturation, brightness, and resolution/dimensions.

Sorting can either be by renaming files or listing the files in order to your stdout.

Sorting by average color based values (hue, saturation, brightness) can take a long time. To sort my directory with 1000+ wallpapers it takes around 2 minutes to sort by hue.

Sorting by average color frequently gives results that don't appear to be 'sorted' from a humans perspective.

When using include/exclude it's recommended that you wrap the regex in quotes.

Most messages are sent to stderr so that when using `-list` you only capture the sorted list with a stdout redirect.
