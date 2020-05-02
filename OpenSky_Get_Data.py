"""
This script downloads data from the opensky library for a particular airport,
a small perimeter is set up around the airport to catch the approach path
"""

from datetime import datetime, timedelta, timezone
from importlib import import_module
import multiprocessing as mp
import os

import click
import numpy as np
from traffic.data import opensky

# Use these lines if you need debug info
# from traffic.core.logging import loglevel
# loglevel('DEBUG')


def get_bounds(rwys):
    """
    This function computes the boundaries of the retrieval
    'box' based upon the runways selected for processing.
    The box is approx. 0.25 degrees in each direction around
    the airport midpoint.
    """
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


def getter(init_time, bounds, timer, anam, outdir):
    """
    This function downloads the data, which is done in
    one hour segments. Each hour is downloaded separately
    using multiprocessing for efficiency.
    """
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


@click.command()
@click.option('--airport', default='VABB')
@click.option('--start-dt', default='2019-08-10')
@click.option('--end-dt', default='2019-08-21')
@click.option('--outdir', default='INDATA/')
@click.option('--n-jobs', default=1)
def main(airport, start_dt, end_dt, outdir, n_jobs):
    os.makedirs(outdir, exist_ok=True)
    airport = import_module('OS_Airports.' + airport)
    bounds = get_bounds(airport.rwy_list)
    start_dt = datetime.strptime(start_dt, '%Y-%m-%d').replace(
        tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_dt, '%Y-%m-%d').replace(
        tzinfo=timezone.utc)
    hours = int((end_dt - start_dt).total_seconds() / 60 / 60 + 0.5)

    pool = mp.Pool(n_jobs)

    pool.starmap(getter, [
        (start_dt, bounds, hour, airport.icao_name, outdir)
        for hour in range(hours)
        ])


if __name__ == '__main__':
    main()
