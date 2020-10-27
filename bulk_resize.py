#!/usr/bin/env python

"""
Resize a folder of images (including subfolders) to be no
larger than a specified size.
"""
from PIL import Image, ImageFilter
import os, sys
import json
import functools

# need to fix colorspace issues
import io
from PIL import Image
from PIL import ImageCms


supported_ext = ['.jpeg','.jpg','.png']

max_width = 800
max_height = 600

WRITE_IMAGES = True

def convert_to_srgb(img):
    '''Convert PIL image to sRGB color space (if possible)'''
    icc = img.info.get('icc_profile', '')
    if icc:
        io_handle = io.BytesIO(icc)     # virtual file
        src_profile = ImageCms.ImageCmsProfile(io_handle)
        dst_profile = ImageCms.createProfile('sRGB')
        img = ImageCms.profileToProfile(img, src_profile, dst_profile)
    return img

# From https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image
def image_transpose_exif(im):
    """
    Apply Image.transpose to ensure 0th row of pixels is at the visual
    top of the image, and 0th column is the visual left-hand side.
    Return the original image if unable to determine the orientation.

    As per CIPA DC-008-2012, the orientation field contains an integer,
    1 through 8. Other values are reserved.

    Parameters
    ----------
    im: PIL.Image
       The image to be rotated.
    """
    exif_orientation_tag = 0x0112
    exif_transpose_sequences = [                   # Val  0th row  0th col
        [],                                        #  0    (reserved)
        [],                                        #  1   top      left
        [Image.FLIP_LEFT_RIGHT],                   #  2   top      right
        [Image.ROTATE_180],                        #  3   bottom   right
        [Image.FLIP_TOP_BOTTOM],                   #  4   bottom   left
        [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  #  5   left     top
        [Image.ROTATE_270],                        #  6   right    top
        [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  #  7   right    bottom
        [Image.ROTATE_90],                         #  8   left     bottom
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag]]
    except Exception:
        return im
    else:
        return functools.reduce(type(im).transpose, seq, im)

def resizeImage(path, out_dir, max_width=max_width, max_height=max_height):
    im = Image.open(path)
    im = image_transpose_exif(im)  # deal with EXIF rotation metadata
    bn = os.path.basename(path)
    ext = os.path.splitext(bn)[1]
    size = im.size
    # find shrink ratio
    ratio = min(float(max_width) / size[0], float(max_height) / size[1])
    new_image_size = tuple([int(x*ratio) for x in size])
    if WRITE_IMAGES:
        im = convert_to_srgb(im)
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
