#!/usr/bin/env python
# Copyright (C) 2016 Andy Aschwanden

import numpy as np
import pylab as plt
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
from netCDF4 import Dataset as NC
from argparse import ArgumentParser



# set up the option parser
parser = ArgumentParser()
parser.description = "Generating synthetic outlet glacier."
parser.add_argument("FILE", nargs='*')
parser.add_argument("-g", "--grid", dest="grid_spacing", type=int,
                    help="horizontal grid resolution", default=1000)
parser.add_argument("-f", "--format", dest="fileformat", type=str.upper,
                    choices=[
                        'NETCDF4', 'NETCDF4_CLASSIC', 'NETCDF3_CLASSIC', 'NETCDF3_64BIT'],
                    help="file format out output file", default='netcdf3_64bit')

options = parser.parse_args()
args = options.FILE
fileformat = options.fileformat.upper()
grid_spacing = options.grid_spacing

if len(args) == 0:
    nc_outfile = 'og' + str(grid_spacing) + 'm.nc'
elif len(args) == 1:
    nc_outfile = args[0]
else:
    print('wrong number arguments, 0 or 1 arguments accepted')
    parser.print_help()
    import sys
    sys.exit(0)

# Domain extend
x_min, x_max = 0, 250e3
y_min, y_max = -25e3, 25e3

# Number of grid points
nx = (x_max - x_min) / grid_spacing + 1
ny = (y_max - y_min) / grid_spacing + 1

x = np.linspace(x_min, x_max, nx)
y = np.linspace(y_min, y_max, ny)

# Ellipsoid center
x0 = 125e3
y0 = 0
z0 = -1000

# Ellipsoid parameters
a = 100e3
b = 5e3
c = 750

[X,Y] = np.meshgrid(x,y);
Ze = -c * np.sqrt(1-((np.array(X, dtype=np.complex) - x0) / a)**2 - ((np.array(Y, dtype=np.complex) -y0)/ b)**2);
Ze = np.real(Ze) + z0

# That works because outside the area of the ellipsoid the sqrt is purely imaginary (hence the 'real' command).
# Rotating this around the y-axis is not really complicated, per se. Rotation around an angle alpha would give you the following:

alpha= 0.75
Xp = np.cos(np.deg2rad(alpha)) * X - np.sin(np.deg2rad(alpha)) * Ze
Yp = Y
Zp = np.sin(np.deg2rad(alpha)) * X + np.cos(np.deg2rad(alpha)) * Ze

# The only problem is now that Xp, Yp is no longer a regular grid, so you need to interpolate back onto the original grid:

Zpi = griddata(np.ndarray.flatten(Xp), np.ndarray.flatten(Yp), np.ndarray.flatten(Zp), X, Y, interp='linear')
# Remove mask
Zpi.masked = False
Zpi[:, 0] = Zpi[:, 1]
Zpi[:, -1] = Zpi[:, -2]

nc = NC(nc_outfile, 'w', format=fileformat)

nc.createDimension("x", size=x.shape[0])
nc.createDimension("y", size=y.shape[0])

var = 'x'
var_out = nc.createVariable(var, 'd', dimensions=("x"))
var_out.axis = "X"
var_out.long_name = "X-coordinate in Cartesian system"
var_out.standard_name = "projection_x_coordinate"
var_out.units = "meters"
var_out[:] = x

var = 'y'
var_out = nc.createVariable(var, 'd', dimensions=("y"))
var_out.axis = "Y"
var_out.long_name = "Y-coordinate in Cartesian system"
var_out.standard_name = "projection_y_coordinate"
var_out.units = "meters"
var_out[:] = y

var = 'topg'
var_out = nc.createVariable(
    var,
    'f',
    dimensions=(
        "y",
        "x"))
var_out.units = "meters"
var_out.standard_name = 'bedrock_altitude'
var_out[:] = Zpi

#nc.close()

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.plot_surface(X, Y, Zpi)
# plt.show()
