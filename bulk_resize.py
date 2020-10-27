#!/usr/bin/env python

"""
Resize a folder of images (including subfolders) to be no
larger than a specified size.
"""
from PIL import Image, ImageFilter
import os, sys
import json
import functools

supported_ext = ['.jpeg','.jpg','.png']

max_width = 800
max_height = 600

WRITE_IMAGES = True

def resizeImage(path, out_dir, max_width=max_width, max_height=max_height):
    im = Image.open(path)
    bn = os.path.basename(path)
    ext = os.path.splitext(bn)[1]
    size = im.size
    # find shrink ratio
    ratio = min(float(max_width) / size[0], float(max_height) / size[1])
    new_image_size = tuple([int(x*ratio) for x in size])
    if WRITE_IMAGES:
        # jpeg's cant have alpha but somehow it is happening... drop alpha and warn
        if ext.lower() in ['.jpeg', '.jpg'] and im.mode == "RGBA":
            print "WARNING: found JPG with alpha channel???  dropping channel %s" % path
            im = im.convert("RGB")
        new_im = im.resize(new_image_size, Image.LANCZOS)
        new_im.save(os.path.join(out_dir, bn), optimize=True)
    else:
        print 'WARNING: RESIZE DISABLED!'
    return ratio


if len(sys.argv) < 3:
    print "usage: %s inDir outDir [max_width max_height]" % sys.argv[0]
    print "    default max_width=%d  max_height=%d" % (max_width, max_height)
    sys.exit(1)

inDir = sys.argv[1]
outBase = sys.argv[2]
if len(sys.argv) > 3:
    max_width = int(sys.argv[3])
if len(sys.argv) > 4:
    max_height = int(sys.argv[4])

for dirpath, dirnames, filenames in os.walk(inDir):
    for filename in [f for f in filenames if os.path.splitext(f)[1].lower() in supported_ext]:
        infn = os.path.join(dirpath, filename)
        outdir = os.path.join(outBase, dirpath)
        print 'Found:', infn
        try:
            os.makedirs(outdir)
        except OSError:
            pass
        resizeImage(infn, outdir, max_width, max_height)
