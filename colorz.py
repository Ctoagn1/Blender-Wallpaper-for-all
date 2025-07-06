"""
A color scheme generator.

Takes an image (local or online) and grabs the most dominant colors
using kmeans.
Also creates bold colors by adding value to the dominant colors.

Finally, outputs the colors to stdout
(one normal and one bold per line, space delimited) and
generates an HTML preview of the color scheme.
"""

import bpy
import os
from tempfile import NamedTemporaryFile
from argparse import ArgumentParser
from colorsys import rgb_to_hsv, hsv_to_rgb
from numpy import array
import random
import math
from collections import Counter
DEFAULT_NUM_COLORS = 6
DEFAULT_MINV = 110
DEFAULT_MAXV = 255
DEFAULT_BOLD_ADD = 50
DEFAULT_FONT_SIZE = 1
DEFAULT_BG_COLOR = '#272727'
DEFAULT_ACCURACY = 100

THUMB_SIZE = (200, 200)
SCALE = 256.0

def distance(c1, c2):
    return math.sqrt(sum((a-b) ** 2 for a, b in zip(c1, c2)))


def mean_color(points):
    n = len(points)
    return tuple(sum(p[i] for p in points) / n for i in range(len(points[0])))


def kmeans(rand, points, weights, k, max_iter=100):
    points = list(points)
    if not rand:
        random.seed(216)
    centers = random.sample(points, k)

    for _ in range(max_iter):
        clusters = [[] for _ in range(k)]
        clusters_weights = [[] for _ in range(k)]
        for p, w in zip(points, weights):
            distances = [distance(p, c) for c in centers]
            cluster_idx = distances.index(min(distances))
            clusters[cluster_idx].append(p)
            clusters_weights[cluster_idx].append(w)
        new_centers = []
        for cluster, wts in zip(clusters, clusters_weights):
            if cluster:
                weighted_sum = [0.0]*len(cluster[0])
                total_w = sum(wts)
                for pt, wt in zip(cluster, wts):
                    for i in range(len(pt)):
                        weighted_sum[i] += pt[i] * wt
                mean = tuple(c/total_w for c in weighted_sum)
                new_centers.append(mean)
            else:
                new_centers.append(random.choice(points))
        if all(distance(a, b) <  1e-3 for a, b in zip(centers, new_centers)):
            break
        centers = new_centers
    return centers
    
def resize(pixels, width, height, new_width, new_height):
    resized = []

    x_scale = width / new_width
    y_scale = height / new_height 
    
    for y in range(new_height):
        for x in range(new_width):
            startx = int(x * x_scale)
            endx= int((x+1) * x_scale)
            starty = int(y* y_scale)
            endy = int((y+1) * y_scale)

            r_total, g_total, b_total, count = 0, 0, 0, 0

            for yy in range(starty, endy):
                for xx in range(startx, endx):
                    idx = yy*width+xx
                    r,g,b = pixels[idx]
                    r_total += r
                    g_total += g
                    b_total += b
                    count += 1
            
            if count:
                avg = (r_total // count, g_total // count, b_total // count)
            else:
                avg = (0, 0, 0)

            resized.append(pixels[idx])
    return resized


def down_scale(x):
    return x / SCALE


def up_scale(x):
    return int(x * SCALE)


def hexify(rgb):
    return '#%s' % ''.join('%02x' % p for p in rgb)

def get_pixels(img):
    pixels=list(img.pixels)
    rgb_pixels = [(pixels[i], pixels[i+1], pixels[i+2]) for i in range(0, len(pixels), 4)]
    rgb_ints=[(int(r*255), int(g*255), int(b*255)) for (r, g, b) in rgb_pixels]
    return rgb_ints


    
def get_colors(img):
    """
    Returns a list of all the image's colors.
    """
    counter = Counter(img)
    return list(counter.items())


def clamp(color, min_v, max_v):
    """
    Clamps a color such that the value is between min_v and max_v.
    """
    h, s, v = rgb_to_hsv(*map(down_scale, color))
    min_v, max_v = map(down_scale, (min_v, max_v))
    v = min(max(min_v, v), max_v)
    return tuple(map(up_scale, hsv_to_rgb(h, s, v)))


def order_by_hue(colors):
    """
    Orders colors by hue.
    """
    hsvs = [rgb_to_hsv(*map(down_scale, color)) for color in colors]
    hsvs.sort(key=lambda t: t[0])
    return [tuple(map(up_scale, hsv_to_rgb(*hsv))) for hsv in hsvs]


def brighten(color, brightness):
    """
    Adds or subtracts value to a color.
    """
    h, s, v = rgb_to_hsv(*map(down_scale, color))
    return tuple(map(up_scale, hsv_to_rgb(h, s, v + down_scale(brightness))))


def colorz(fd, n=DEFAULT_NUM_COLORS, min_v=DEFAULT_MINV, max_v=DEFAULT_MAXV,
           bold_add=DEFAULT_BOLD_ADD, order_colors=True, randomness=False, accuracy=DEFAULT_ACCURACY):
    """
    Get the n most dominant colors of an image.
    Clamps value to between min_v and max_v.

    Creates bold colors using bold_add.
    Total number of colors returned is 2*n, optionally ordered by hue.
    Returns as a list of pairs of RGB triples.

    For terminal colors, the hue order is:
    red, yellow, green, cyan, blue, magenta
    """
    size = fd.size
    img = get_pixels(fd)
    img = resize(img, size[0], size[1], 200, 200)

    obs = get_colors(img)
    colors_only = [color for color, count in obs]
    counts = [count for color, count in obs]
    clamped = [clamp(color, min_v, max_v) for color in colors_only]
    clusters = kmeans(randomness, array(clamped).astype(float), counts, n, max_iter=accuracy)
    colors = order_by_hue(clusters) if order_colors else clusters
    return list(zip(colors, [brighten(c, bold_add) for c in colors]))


def html_preview(colors, font_size=DEFAULT_FONT_SIZE,
                 bg_color=DEFAULT_BG_COLOR, bg_img=None,
                 fd=None):
    """
    Creates an HTML preview of each color.

    Returns the Python file object for the HTML file.
    """

    fd = fd or NamedTemporaryFile(mode='wt', suffix='.html', delete=False)

    # Initial CSS styling is empty
    style = ""

    # Create the main body
    body = '\n'.join(["""
        <div class="color" style="color: {color}">
            <div>█ {color}</div>
            <div style="color: {color_bold}">
                <strong>█ {color_bold}</strong>
            </div>
        </div>
    """.format(color=hexify(c[0]), color_bold=hexify(c[1])) for c in colors])

    if bg_img:
        # Check if local or online image
        if os.path.isfile(bg_img):
            bg_img = os.path.abspath(bg_img)

        bg_url = "url('%s')" % (
            ('file://%s' % bg_img) if os.path.isfile(bg_img) else bg_img)

        # Add preview box and image to the body
        body = """
            <div id="preview-box" class="box-shadow">
                <img id="preview-image" class="box-shadow" src="{bg_img}" />
                {body}
            </div>
        """.format(**locals())

        # Add blurred background image styling
        style += """
            body:before {{
                content: '';
                position: fixed;
                z-index: -1;
                left: 0;
                right: 0;
                width: 100%;
                height: 100%;
                display: block;

                background-image: {bg_url};
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center center;
                background-attachment: fixed;

                -webkit-filter: blur(2rem);
                -moz-filter: blur(2rem);
                -o-filter: blur(2rem);
                -ms-filter: blur(2rem);
                filter: blur(2rem)
            }}
        """.format(**locals())

    # CSS styling
    style += """
        body {{
            margin: 0;
            background: {bg_color};

            font-family: monospace;
            font-size: {font_size}rem;
            line-height: 1;
        }}

        #main-container {{
            padding: 1rem;
            text-align: center;
        }}

        #preview-box {{
            display: inline-block;
            margin: 3rem;
            padding: 1rem;
            background: {bg_color};
        }}

        #preview-image {{
            width: 100%;
        }}

        .color {{
            display: inline-block;
            margin: 1rem;
        }}

        .box-shadow {{
            -webkit-box-shadow: 0 0 1em 0 rgba(0, 0, 0, 0.75);
            -moz-box-shadow:    0 0 1em 0 rgba(0, 0, 0, 0.75);
            box-shadow:         0 0 1em 0 rgba(0, 0, 0, 0.75);
        }}
    """.format(**locals())

    # Write the file
    fd.write("""
        <!DOCTYPE html>
        <html>
            <head>
                <title>
                    Colorscheme Preview
                </title>
                <meta charset="utf-8">
                <style>
                    {style}
                </style>
            </head>
            <body>
                <div id="main-container">
                    {body}
                </div>
            </body>
        </html>
    """.format(**locals()))

    return fd


def parse_args():
    parser = ArgumentParser(description=__doc__)

    parser.add_argument('image',
                        help="""
                        the image file or url to generate from.
                        """,
                        type=str)

    parser.add_argument('-n',
                        help="""
                        number of colors to generate (excluding bold).
                        Default: %s
                        """ % DEFAULT_NUM_COLORS,
                        dest='num_colors',
                        type=int,
                        default=DEFAULT_NUM_COLORS)

    parser.add_argument('--minv',
                        help="""
                        minimum value for the colors.
                        Default: %s
                        """ % DEFAULT_MINV,
                        type=int,
                        default=DEFAULT_MINV)

    parser.add_argument('--maxv',
                        help="""
                        maximum value for the colors.
                        Default: %s
                        """ % DEFAULT_MAXV,
                        type=int,
                        default=DEFAULT_MAXV)

    parser.add_argument('--bold',
                        help="""
                        how much value to add for bold colors.
                        Default: %s
                        """ % DEFAULT_BOLD_ADD,
                        type=int,
                        default=DEFAULT_BOLD_ADD)

    parser.add_argument('--font-size',
                        help="""
                        what font size to use, in rem.
                        Default: %s
                        """ % DEFAULT_FONT_SIZE,
                        type=int,
                        default=DEFAULT_FONT_SIZE)

    parser.add_argument('--bg-color',
                        help="""
                        what background color to use, in hex format.
                        Default: %s
                        """ % DEFAULT_BG_COLOR,
                        type=str,
                        default=DEFAULT_BG_COLOR)

    parser.add_argument('--no-bg-img',
                        help="""
                        whether or not to use a background in the
                        preview.
                        Default: background image on
                        """,
                        action='store_true',
                        default=False)

    parser.add_argument('--no-preview',
                        help="""
                        whether or not to generate and show the preview.
                        Default: preview on
                        """,
                        action='store_true',
                        default=False)

    return parser.parse_args()
