# NDVI extraction (Python 3.10)

## Install
	-- pip install gdal (need to download corresponding wheel file to download; check https://www.youtube.com/watch?v=8iCWUp7WaTk&t=136s; import using osgeo)
	-- pip install pymodis
	-- pip install pandas
	-- pip install shapely
	-- pip install pyproj



## Usage

Extract NDVI values for all districts of Punjab Province of Pakistan (36 in total) from fiscal year 2006 to fisal year 2014.
A fiscal year of year XXXX lasts from July 3rd/4th of XXXX to June 17th/18th of XXXX+1 

4 files are relevant (Run sequentially in listed order):

	1) NDVI_util.py (contain utility functions to assist pixel coordinate calculations);
	2) tile_pixel_identification.py (for tiles (h24v5), (h24v6), (h23v5), which we know contain all pixels for Punjab, we classify all pixels' belonging to particular district)
	3) NDVI_indexAccess_Implementation.py (download h24v5, h24v6, h23v5 hdf files from MODIS dataset and retrieve pixels obtained from tile_pixel_identification above)
 	4) NDVI_To_Excel.py (convert the result NDVI array to excel file)


For more details please see in-file comments.

## Contact:
If you have additional question, please contact Yuanzhan Gao at yg8ch@virginia.edu




