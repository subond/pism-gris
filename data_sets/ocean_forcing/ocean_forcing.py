#!/usr/bin/env python
# Copyright (C) 2015 Andy Aschwanden

import numpy as np
from netCDF4 import Dataset as NC

try:
    import pypismtools.pypismtools as ppt
except:
    import pypismtools as ppt

from netcdftime import utime
import dateutil
import numpy as np
from argparse import ArgumentParser                            
    

# Set up the option parser
parser = ArgumentParser()
parser.description = "Script adds ocean forcing to HIRHAM atmosphere/surface forcing file. Sets a constant, spatially-uniform basal melt rate of b_a before time t_a, and b_e after time t_a."
parser.add_argument("FILE", nargs='*')
parser.add_argument("--bmelt_0",dest="bmelt_0", type=float,
                    help="southern basal melt rate, in m yr-1",default=228)
parser.add_argument("--bmelt_1",dest="bmelt_1", type=float,
                    help="northern basal melt rate, in m yr-1",default=10)
parser.add_argument("--lat_0",dest="lat_0", type=float,
                    help="latitude to apply southern basal melt rate",default=69)
parser.add_argument("--lat_1",dest="lat_1", type=float,
                    help="latitude to apply northern basal melt rate",default=81)
parser.add_argument("-m", "--process_mask", dest="mask", action="store_true",
                    help='''
                    Process the mask, no melting on land''', default=False)


options = parser.parse_args()
args = options.FILE

ice_density = 910.

bmelt_0 = options.bmelt_0 * ice_density
bmelt_1 = options.bmelt_1 * ice_density
lat_0 = options.lat_0
lat_1 = options.lat_1
mask = options.mask

infile = args[0]

nc = NC(infile, 'a')
    
lon_0 = -45

p = ppt.get_projection_from_file(nc)

xdim, ydim, zdim, tdim = ppt.get_dims(nc)

# x0, y0 = p(lon_0, lat_0)
# x1, y1 = p(lon_0, lat_1)

# bmelt = a*y + b
a = (bmelt_1 - bmelt_0) / (lat_1 - lat_0)
b = bmelt_0 - a * lat_0
    
x = nc.variables[xdim]
y = nc.variables[ydim]

X, Y = np.meshgrid(x, y)

Lon, Lat = p(X, Y, inverse=True)

# create a new dimension for bounds only if it does not yet exist
if tdim is None:
    time_dim = 'time'
    nc.createDimension(time_dim)
else:
    time_dim = tdim

# create a new dimension for bounds only if it does not yet exist
bnds_dim = "nb2"
if bnds_dim not in nc.dimensions.keys():
    nc.createDimension(bnds_dim, 2)

# variable names consistent with PISM
time_var_name = "time"
bnds_var_name = "time_bnds"

time_units = 'years since 1-1-1'
time_calendar = 'none'

# create time variable
if time_var_name not in nc.variables:
    time_var = nc.createVariable(time_var_name, 'd', dimensions=(time_dim))
else:
    time_var = nc.variables[time_var_name]
time_var.bounds = bnds_var_name
time_var.units = time_units
time_var.standard_name = time_var_name
time_var.axis = "T"
time_var[:] = [1.]

# create time bounds variable
if bnds_var_name not in nc.variables:
    time_bnds_var = nc.createVariable(bnds_var_name, 'd', dimensions=(time_dim, bnds_dim))
else:
    time_bnds_var = nc.variables[bnds_var_name]
time_bnds_var[:, 0] = [0]
time_bnds_var[:, 1] = [1]
    
def def_var(nc, name, units):
    var = nc.createVariable(name, 'f', dimensions=(time_dim, ydim, xdim), zlib=True, complevel=3)
    var.units = units
    return var

var = "shelfbmassflux"
if (var not in nc.variables.keys()):
    bmelt_var = def_var(nc, var, "kg m-2 yr-1")
else:
    bmelt_var = nc.variables[var]
bmelt_var.grid_mapping = "mapping"

var = "shelfbtemp"
if (var not in nc.variables.keys()):
    btemp_var = def_var(nc, var, "deg_C")
else:
    btemp_var = nc.variabels[var]
btemp_var.grid_mapping = "mapping"
    
if mask:
    mask_var = nc.variables['mask'][:]
    nc.variables['mask'].grid_mapping = "mapping"
    land_mask = (mask_var != 0) & (mask_var !=3)


nt = len(time_var[:])
for t in range(nt):
    if time_bnds_var is not None:
        print('Processing from {} to {}'.format(time_bnds_var[t,0], time_bnds_var[t,1]))
    else:
        print('Processing {}'.format(dates[t]))        
    bmelt = a * Lat + b
    bmelt[Lat<lat_0] = a * lat_0 + b
    bmelt[Lat>lat_1] = a * lat_1 + b
    if mask:
        bmelt[land_mask] = 0.
    bmelt_var[t,::] = bmelt
    btemp_var[t,::] = 0
    nc.sync()
        

nc.close()
