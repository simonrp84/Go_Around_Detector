'''
This script downloads data from the opensky library for a particular airport,
a small perimeter is set up around the airport to catch the approach path

'''

from datetime import datetime, timedelta
from traffic.data import opensky
import multiprocessing as mp
import numpy as np
import os

# Use this line to change the airport to retrieve.
import OS_Airports.VABB as AIRPRT

# Use these lines if you need debug info
# from traffic.core.logging import loglevel
# loglevel('DEBUG')

# This line sets the output directory
outdir = '/gf2/eodg/SRP002_PROUD_ADSBREP/GO_AROUNDS/VABB/INDATA/'

# Setting up the start and end times for the retrieval
start_dt = datetime(2019, 8, 1, 0, 0)
end_dt = datetime(2019, 8, 12, 23, 59)

# Sets the number of simultaneous retrievals
nummer = 6


def get_bounds(rwys):
    '''
    This function computes the boundaries of the retrieval
    'box' based upon the runways selected for processing.
    The box is approx. 0.25 degrees in each direction around
    the airport midpoint.
    '''
    latlist = []
    lonlist = []
    for rwy in rwys:
        latlist.append(rwy.rwy[0])
        lonlist.append(rwy.rwy[1])
        latlist.append(rwy.rwy2[0])
        lonlist.append(rwy.rwy2[1])

    lat_ave = np.nanmean(latlist)
    lon_ave = np.nanmean(lonlist)
    bounds = [lon_ave - 0.45, lat_ave - 0.45,
              lon_ave + 0.45, lat_ave + 0.45]

    return bounds


def getter(init_time, bounds, timer, anam):
    '''
    This function downloads the data, which is done in
    one hour segments. Each hour is downloaded separately
    using multiprocessing for efficiency.
    '''

    try:
        times = init_time + timedelta(hours=timer)
        dtst = times.strftime("%Y%m%d%H%M")
        outf = outdir+'OS_'+dtst+'_'+anam+'.pkl'

        # Check if the file has already been retrieved
        if (os.path.exists(outf)):
            print("Already retrieved", outf)
            return
        # Otherwise use 'traffic' to download
        flights = opensky.history(start=times,
                                  stop=times+timedelta(hours=1),
                                  bounds=bounds,
                                  other_params=" and time-lastcontact<=15 ")
        flights.to_pickle(outf)
    except Exception as e:
        print("There is a problem with this date/time combination:", e, times)

    return


bounds = get_bounds(AIRPRT.rwy_list)

# Loop over timestamps to retrieve all the data.
while True:

    dtst = start_dt.strftime("%Y%m%d%H%M")
    outf = outdir + 'OS_' + dtst+'_' + AIRPRT.icao_name + '.pkl'
    print("Now processing:",
          start_dt.strftime("%Y/%m/%d %H:%M"),
          'for', AIRPRT.airport_name + ' / ' +
          AIRPRT.icao_name)

    # Create processes for each hour, in total 'nummer' hours are
    # processed simultaneously
    processes = [mp.Process(target=getter,
                            args=(start_dt, bounds, i, AIRPRT.icao_name))
                 for i in range(0, nummer)]

    # Start, and then join, all processes
    for p in processes:
        p.start()
    for p in processes:
        p.join()

    # Move on to the next block of times
    start_dt = start_dt + timedelta(hours=nummer)

    # If we have reached the end of the block then exit
    if (start_dt >= end_dt):
        break
