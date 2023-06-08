from osgeo import gdal
import json
from statistics import mean
import glob
from pymodis import downmodis
from datetime import datetime, timedelta
import os
import time

########################################################################################################

# This file contains codes that download hdf files across the 8-years interval; collect the NDVI value
# of selected pixels, and add them to a dictionary with years as sub-dictionary which contains the
# name of each district and the average NDVI values among those pixels (23 elements per list because
# data are collected on a 16-days basis).

# Run time of this program (3/4/2023): ~9600 s
# Run time (3/6/2023): 13974.662083864212 s

########################################################################################################

########################################### PREPARTION #################################################

# STEP 1: List years we are getting
yearList = ["2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014"]

# STEP 2: dates we are getting in the dateset; in 16 days interval and need to account for leap years

# Create list of days interested in for no leap year
org_date = "07-04"
sixteen_inc_list = [org_date]
for i in range(22):
    date_trueForm = datetime.strptime(sixteen_inc_list[i], "%m-%d")
    if i == 11:
        end_date = date_trueForm + timedelta(days=13)
    else:
        end_date = date_trueForm + timedelta(days=16)
    end_date_string = end_date.strftime('%m-%d')
    sixteen_inc_list.append(end_date_string)
sixteen_inc_list_no_leap = ["-" + date for date in sixteen_inc_list]

# Create list of days interested for leap year (prior to leap year, like 2007, 2011)
sixteen_inc_list = [org_date]
for i in range(22):
    date_trueForm = datetime.strptime(sixteen_inc_list[i], "%m-%d")
    if i == 11:
        end_date = date_trueForm + timedelta(days=13)
    elif i == 15:
        end_date = date_trueForm + timedelta(days=15)
    else:
        end_date = date_trueForm + timedelta(days=16)

    end_date_string = end_date.strftime('%m-%d')
    sixteen_inc_list.append(end_date_string)
sixteen_inc_list_leap_prior = ["-" + date for date in sixteen_inc_list]

# Create list of days interested for leap year (2008, 2012...)
org_date_leap = "07-03"
sixteen_inc_list = [org_date_leap]
for i in range(22):
    date_trueForm = datetime.strptime(sixteen_inc_list[i], "%m-%d")
    if i == 11:
        end_date = date_trueForm + timedelta(days=14)
    else:
        end_date = date_trueForm + timedelta(days=16)

    end_date_string = end_date.strftime('%m-%d')
    sixteen_inc_list.append(end_date_string)
sixteen_inc_list_leap = ["-" + date for date in sixteen_inc_list]

# Destination of downloading files from Modis
destination = "Satellite Data/"  # Destination of download
user = "YOUR_OWN_USER_NAME"  # NASA EarthData Username
password = "YOUR_OWN_PWD"  # NASA EarthData Password (Please use your own account and password instead)
product = "MYD13Q1.006"  # Product serialization number
tiles = ["h23v05", "h24v05", "h24v06"]
delta = 1
file_path_23_05 = None  # file path for all h23v05 tile hdf
file_path_24_05 = None  # ... for all h24v05 tile hdf
file_path_24_06 = None  # ... for all h24v06 tile hdf

NDVI_result = {}

start_time = time.time()

###########################Implementation Start ##########################################
for year in yearList:
    year_processing_time = time.time()
    if year not in NDVI_result.keys():
        NDVI_result[year] = {}
        print(f"We are processing year {year} right now...")
        print("\n")

    if year in ["2007", "2011"]:
        day_list = [year + sixteen_inc_list_leap_prior[i] for i in
                    range(0, int(len(sixteen_inc_list_leap_prior) / 2) + 1)] + [
                       str(int(year) + 1) + sixteen_inc_list_leap_prior[i]
                       for i in range(int(len(sixteen_inc_list_leap_prior) / 2) + 1, len(sixteen_inc_list_leap_prior))]

    elif year in ["2008", "2012"]:
        day_list = [year + sixteen_inc_list_leap[i] for i in
                    range(0, int(len(sixteen_inc_list_leap) / 2) + 1)] + [
                       str(int(year) + 1) + sixteen_inc_list_leap[i] for i in
                       range(int(len(sixteen_inc_list_leap) / 2) + 1, len(sixteen_inc_list_leap))]

    else:
        day_list = [year + sixteen_inc_list_no_leap[i] for i in
                    range(0, int(len(sixteen_inc_list_no_leap) / 2) + 1)] + [
                       str(int(year) + 1) + sixteen_inc_list_no_leap[i] for i in
                       range(int(len(sixteen_inc_list_no_leap) / 2) + 1, len(sixteen_inc_list_no_leap))]

    for date in day_list:  # for each 16-day interval
        print(f"Processing time interval {date} ...")

        modis_down = downmodis.downModis(destinationFolder=destination, password=password, user=user, path="MOLA",
                                         product=product, tiles=tiles, today=date, delta=delta)

        print("Downloading tiles for the time interval!")
        modis_down.connect()
        modis_down.downloadsAllDay()  # download all Modis files for this particular time interval
        print("Download complete!")

        MODIS_files = glob.glob(destination + '*.hdf')  # get all .hdf files in the destination

        # Process file names as needed
        for file in MODIS_files:
            file = file.split("\\")
            if file[1][17:23] == "h23v05":
                file_path_23_05 = file[0] + "/" + file[1]
            elif file[1][17:23] == "h24v05":
                file_path_24_05 = file[0] + "/" + file[1]
            else:
                file_path_24_06 = file[0] + "/" + file[1]

        # Read gdal files and convert them into numpy array
        sds_23_05 = gdal.Open(file_path_23_05, gdal.GA_ReadOnly).GetSubDatasets()
        sds_24_05 = gdal.Open(file_path_24_05, gdal.GA_ReadOnly).GetSubDatasets()
        sds_24_06 = gdal.Open(file_path_24_06, gdal.GA_ReadOnly).GetSubDatasets()

        vi_src_23_05 = gdal.Open(sds_23_05[0][0])
        vi_array_23_05 = vi_src_23_05.ReadAsArray()

        vi_src_24_05 = gdal.Open(sds_24_05[0][0])
        vi_array_24_05 = vi_src_24_05.ReadAsArray()

        vi_src_24_06 = gdal.Open(sds_24_06[0][0])
        vi_array_24_06 = vi_src_24_06.ReadAsArray()

        # open pixel index dictionary
        with open('district_index_all.json', 'r') as fp:
            district_index = json.load(fp)

        district_counter = 0

        for key in district_index.keys():
            print(f"Processing the {district_counter}th district,{key}, now...")
            if key not in NDVI_result[year].keys():  # If this is a district never encountered before, we assign a
                # new empty list to it
                NDVI_result[year][key] = []
                print(f"New District {key} detected, creating a new list for it...")
            NDVI_value = []
            for position in district_index[key]:
                if position[0] == 23 and position[1] == 5:
                    NDVI_value.append(vi_array_23_05[position[3]][position[2]])
                elif position[0] == 24 and position[1] == 5:
                    NDVI_value.append(vi_array_24_05[position[3]][position[2]])
                elif position[0] == 24 and position[1] == 6:
                    NDVI_value.append(vi_array_24_06[position[3]][position[2]])

            # take average of the all NDVI values for that particular day interval
            average = mean(NDVI_value)
            print(f"The average NDVI value for {key} for the period {date} is {average}.")
            NDVI_result[year][key].append(int(average))

            district_counter += 1

        # Close all gdal files so that os.unlink can delete them
        sds_23_05 = None
        sds_24_05 = None
        sds_24_06 = None
        vi_src_23_05 = None
        vi_src_24_05 = None
        vi_src_24_06 = None
        vi_array_23_05 = None
        vi_array_24_05 = None
        vi_array_24_06 = None

        # Delete all folders for that time interval to clean up
        print(f"Processing for {date} is finished. Deleting files for {date}...")
        for filename in os.listdir(destination):
            file_path = os.path.join(destination, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    year_processing_time = time.time() - year_processing_time
    print(f"Took {year_processing_time} seconds to process year {year}")

print("Dumping final result into a json file ...")
with open("NDVI_result_3_6.json", "w") as fp:
    json.dump(NDVI_result, fp)

whole_program_time = time.time() - start_time
print(f"The whole program ran {whole_program_time} seconds")
