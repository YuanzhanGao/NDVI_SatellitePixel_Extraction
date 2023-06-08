from osgeo import ogr
from pyproj import Proj
from NDVI_util import from_ogr_to_shapely, reverse_pixel
import time
from multiprocessing import Process, Manager
import json


# Since Python's structure Global Interpreter Lock (GIL) prevents multithreading, in order
# to boost the performance of our about-to-do CPU intensive work, we will be using Python's
# multiprocessing module which can utilize the full GPU power of your computer to perform
# the reverse calculation of tile pixel's Geo coordinate and check whether the pixel is
# within the boundary of certain districts.

# NOTE!! When I performed the multiprocessing work, I messed up and ended up creating 8 processes
# while my laptop only has 4 physical cores (I mistook logical processor with physical core), which
# in turn decreases my performances; my final performance time on this program is
# about 14079 seconds, which roughly translates to 3.9 hours (still
# better than the single core CPU operation which would be at least 6 hours and definitely much better
# than the pre-optimized algorithm which would take more than 17 hours.

# To learn more about Python's multiprocessing and multithreading modules, I highly recommend checking the
# Stackoverflow post below.
# https://stackoverflow.com/questions/40217873/multiprocessing-use-only-the-physical-cores


def full_tile_pixel_identification(my_district_dic_param, index_start, index_end, h_tile, v_tile, poly_list_param,
                                   MODIS_GRID_param):
    # The original idea of giving ranges to the function is to allow 8 (mistakenly) processes to work on it at the same
    # time;
    for index in range(index_start, index_end):  # pixel_x
        for j in range(4800):  # pixel_y
            # Further optimization ideas: maybe reproduce the whole process in this function instead of calling it
            # from some other functions (reverse_pixel)?
            myPoint = reverse_pixel(h_tile, v_tile, index, j, MODIS_GRID_param)
            # poly_list_param will be a list of list, whose element is of the form (district name(str),
            # polygon_object(shapely.polygon))
            for poly in poly_list_param:
                if myPoint.within(poly[1]):  # If we want to exhaustively include all pixels within certain districts,
                    # use "myPoint.within(poly[1]) or myPoint.intersects(poly[1]), though I am not sure how much
                    # effort will be worth it
                    my_district_dic_param[poly[0]].append((h_tile, v_tile, index, j))
                    break # Break out of the loop once we find where does the point belong to abvoid looping through
                    # all shapefile


# Entry point of the program; mandatory for using the multiprocessing module
if __name__ == '__main__':

    startTime = time.time()  # Start time of the program (for benchmarking purpose)

    shapeFile_path = "Satellite Data/Punjab_district/Punjab_districts.shp"
    shapefile = ogr.Open(shapeFile_path)
    layer = shapefile.GetLayer()

    # Generate the "poly_list_param" parameter that will be passed into the full_tile_pixel_identification() function
    poly_list = []
    for i in range(36):
        district = layer.GetFeature(i)
        district_poly = district.GetGeometryRef()
        shapely_poly = from_ogr_to_shapely(district_poly)
        poly_list.append([district.GetField(3), shapely_poly])

    EARTH_RADIUS = 6371007.181
    # Predefined PyProj projection object to pass as a parameter for full_tile_pixel_identification()
    MODIS_GRID = Proj(f'+proj=sinu +R={EARTH_RADIUS} +nadgrids=@null +wktext')

    ##############################################################################################

    manager = Manager()

    # Creating an empty manager dictionary with contents of manager list so that all child processes can
    # share among each other; if you are advanced you can try to use other shared memory data
    my_district_dic = manager.dict()
    for i in poly_list:
        my_district_dic[i[0]] = manager.list() # Set up empty manager.list so that these lists can be passed
        # among processes as well

    # NOTE!! Ideally you want to create processes equal to the number of PHYSICAL cores on your
    # Computer (mine is 4). Since I created 8 (prior to 3/9/2023), some processes will have to wait before other
    # processes finish, so the total runtime is almost additive. If you have 4 physical cores, each of which has 2
    # logical processor (so 8 in general), which is a classic computer architecture (Check using Task Manager),
    # you should set up 4 (N) or 3 (N-1) processes if your process involves I/O processing.

    # Edit at 3/9/2023: Change to 3 processes
    process1 = Process(target=full_tile_pixel_identification,
                       args=(my_district_dic, 0, 4800, 24, 5, poly_list, MODIS_GRID))
    process2 = Process(target=full_tile_pixel_identification,
                       args=(my_district_dic, 0, 4800, 23, 5, poly_list, MODIS_GRID))
    process3 = Process(target=full_tile_pixel_identification,
                       args=(my_district_dic, 0, 4800, 24, 6, poly_list, MODIS_GRID))

    # Start all processes (use a for loop)
    process1.start()
    process2.start()
    process3.start()

    # All processes need to wait for others to end before main() is terminated (use a for loop)
    process1.join()
    process2.join()
    process3.join()

    # convert the result dictionary and its elements from DictProxy/ListProxy to generic Dict/List objects since
    # Proxy objects are not JSON_serializable.

    my_district_dic = dict(my_district_dic)
    for key in my_district_dic.keys():
        my_district_dic[key] = list(my_district_dic[key])

    # Write the result to a separate file
    with open("district_index_all.json", "w") as fp:
        json.dump(my_district_dic.copy(), fp)

    print(f"Program total run time: {time.time() - startTime}s")
