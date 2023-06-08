from osgeo import ogr
from shapely.geometry import Point
import shapely
import random
import shapely.wkb
from pyproj import Proj
import math


# import pyximport; pyximport.install() # Attempted to use Cython to optimize reverse_pixel's performance;
# in the end did not work out

########################################################################################################

# This file contains utility functions that are needed to identify pixel numbers for each district.

########################################################################################################

def generate_random(number, polygon):
    points = []
    minx, miny, maxx, maxy = polygon.bounds
    while len(points) < number:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            points.append(pnt)
    return points


def from_ogr_to_shapely(ogr_geom):
    # Creating a copy of the input OGR geometry. This is done in order to
    # ensure that when we drop the M-values, we are only doing so in a
    # local copy of the geometry, not in the actual original geometry.
    ogr_geom_copy = ogr.CreateGeometryFromWkb(ogr_geom.ExportToIsoWkb())

    # Generating a new shapely geometry
    shapely_geom = shapely.wkb.loads(bytes(ogr_geom_copy.ExportToIsoWkb()))

    return shapely_geom


def get_tile_and_pixel_indices(latitude, longitude):
    VERTICAL_TILES = 18
    HORIZONTAL_TILES = 36
    EARTH_RADIUS = 6371007.181
    EARTH_WIDTH = 2 * math.pi * EARTH_RADIUS

    TILE_WIDTH = EARTH_WIDTH / HORIZONTAL_TILES
    TILE_HEIGHT = TILE_WIDTH

    MODIS_GRID = Proj(f'+proj=sinu +R={EARTH_RADIUS} +nadgrids=@null +wktext')

    x, y = MODIS_GRID(longitude, latitude)
    h = (EARTH_WIDTH * .5 + x) / TILE_WIDTH
    v = -(EARTH_WIDTH * .25 + y - (VERTICAL_TILES - 0) * TILE_HEIGHT) / TILE_HEIGHT
    pix_h = abs(((int(h) - h) * TILE_WIDTH) / 231.656358263889) - 0.5
    pix_v = abs(((int(v) - v) * TILE_HEIGHT) / 231.656358263889) - 0.5
    return int(h), int(v), int(pix_h), int(pix_v)


# The key to the original optimization of the "reverse_pixel" algorithm is to pass a predefined MODIS_GRID projection
# object to it as a parameter as opposed to generate a new one everything on the fly. This will significantly decrease
# the run time of this algorithm (cut by almost half).

def reverse_pixel(tile_h, tile_v, pixel_x, pixel_y, MODIS_GRID):
    VERTICAL_TILES = 18
    HORIZONTAL_TILES = 36
    EARTH_RADIUS = 6371007.181
    EARTH_WIDTH = 2 * math.pi * EARTH_RADIUS

    TILE_WIDTH = EARTH_WIDTH / HORIZONTAL_TILES
    TILE_HEIGHT = TILE_WIDTH
    pixel_size = 231.656358263889

    # Restore from pixel index to tile index

    original_h = ((pixel_x * pixel_size) / TILE_WIDTH) + tile_h
    original_v = ((pixel_y * pixel_size) / TILE_HEIGHT) + tile_v

    # Restore from tile index to Global Map Coordinates
    x = original_h * TILE_WIDTH - EARTH_WIDTH * 0.5
    y = -(original_v * TILE_HEIGHT) + (VERTICAL_TILES - 0) * TILE_HEIGHT - EARTH_WIDTH * 0.25

    lon, lat = MODIS_GRID(x, y, inverse=True)

    return Point(lon, lat)
