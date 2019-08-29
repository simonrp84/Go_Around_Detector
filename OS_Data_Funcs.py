from scipy.interpolate import UnivariateSpline as UniSpl
from traffic.core import Traffic

import flightphase as flph
import OS_Consts as CNS
import numpy as np


def get_flight(inf):
    '''
    Load a series of flights from a file using Xavier's 'traffic' library
    Input:
        -   inf, the input filename
    Returns:
        -   a list of flights
    '''
    flist = []
#    try:
    fdata = Traffic.from_file(inf).query("latitude == latitude")
    fdata = fdata.clean_invalid().filter().eval()
#    except:
#        return flist
    for flight in fdata:
        pos = flight.callsign.find(CNS.search_call)
        if (pos < 0):
            continue
        f_data = flight.data
        f_data = f_data.drop_duplicates('timestamp')
        f_data = f_data.drop_duplicates('longitude')
        f_data = f_data.drop_duplicates('latitude')
        f_data = f_data.query('altitude<10000')
        f_data = f_data.dropna()
        flight.data = f_data
        flist.append(flight)
    return flist


def get_future_time(times, c_pos, n_sec):
    '''
    Find the array location that has the time closest to a
    certain amount in the future.
    Inputs:
        -   Times, an array of times in integer/float seconds
        -   c_pos, the position in the array of the initial time
        -   n_sec, the desired time delta to compute
    Returns:
        -   An integer array position (>0) if time is found, or
            -1 if the time is not found
    '''
    c_time = times[c_pos]
    f_time = c_time + n_sec
    diff = (np.abs(times - f_time))
    idx = (diff).argmin()
    if (diff.min() > 20):
        idx = -1

    return idx


def check_good_flight(flight):
    '''
    Checks if the flight callsign matches a series of
    pre-defined 'bad' callsigns. Most of these are
    ground vehicles.
    Input:
        -   A flight produced by the 'traffic' library.
    Returns:
        -   False if callsign matches one of the 'bad' list
        -   True if flight is not matched
    '''
    if (flight.icao24 in CNS.exclude_list):
        return False
    if (flight.callsign[0:7] == 'WILDLIF'):
        return False
    elif (flight.callsign[0:6] == 'AGM000'):
        return False
    elif (flight.callsign[0:7] == 'FOLOWME'):
        return False
    elif (flight.callsign[0:5] == 'RADAR'):
        return False
    elif (flight.callsign[0:7] == 'FIRETEN'):
        return False
    elif (flight.callsign[0:8] == 'DUTYOFIR'):
        return False
    else:
        return True


def check_good_data(flight):
    '''
    Checks that a flight has data suitable for inclusion in the study.
    This discards ground-only flights, as well as those that do not appear
    to be attempting a landing.
    Input:
        -   A flight produced by the 'traffic' library.
    Returns:
        -   True if a flight is suitable, false otherwise.
    '''
    if (np.all(flight.data['geoaltitude'] > 3000)):
        return 'G_HIGH'
    if (np.all(flight.data['altitude'] > 3000)):
        return 'B_HIGH'
    elif (np.all(flight.data['geoaltitude'] < 500)):
        return 'G_LOW'
    elif (np.all(flight.data['groundspeed'] < 50)):
        return 'SLOW'
    elif (np.all(flight.data['onground'])):
        return 'GROUND'
    else:
        return True


def preproc_data(flight, verbose):
    '''
    Preprocesses a flight into a format usable by Junzi's classifier

    Input:
        -   A flight produced by the 'traffic' library.
        -   A bool specifying verbose mode
    Returns:
        A dict containing:
        -   time: The time-since-first-contact for each datapoint
        -   lats: Reported latitude of each datapoint
        -   lons: Reported longitude
        -   alts: Reported barometric altitude
        -   spds: Reported ground speed
        -   gals: Reported geometric altitude
        -   hdgs: Reported track angle
        -   rocs: Reported vertical rate
        -   lpos: Last position report timestamp
        -   ongd: Flag indicating whether aircraft is on ground (True/False)
        -   call: Reported callsign for the flight
        -   ic24: Reported icao24 hex code for the flight
        -   strt: Time of first position in the flight datastream
        -   stop: Time of last position in the flight datastream
        -   dura: Reported duration of the flight
    '''
    isgd = check_good_data(flight)
    if (isgd != True):
        if (verbose):
            print("Unsuitable flight:", flight.callsign, isgd)
        return None

    f_data = flight.data
    try:
        f_data = f_data.drop_duplicates('last_position')
    except KeyError:
        None

    if(len(f_data) < 5):
        return None
    fdata = {}

    tmp = f_data['timestamp'].values
    ts = (tmp - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
    times = ts.astype(np.int)

    # Correct headings into -180 -> 180 range
    hdgs = f_data['track'].values
    pts = (hdgs > 180.).nonzero()
    hdgs[pts] = hdgs[pts] - 360.

    fdata['time'] = times - times[0]
    fdata['lats'] = f_data['latitude'].values
    fdata['lons'] = f_data['longitude'].values
    fdata['alts'] = f_data['altitude'].values
    fdata['spds'] = f_data['groundspeed'].values
    fdata['gals'] = f_data['geoaltitude'].values
    fdata['hdgs'] = hdgs
    fdata['rocs'] = f_data['vertical_rate'].values
    fdata['ongd'] = f_data['onground'].values
    fdata['call'] = flight.callsign
    fdata['ic24'] = flight.icao24
    fdata['strt'] = flight.start
    fdata['stop'] = flight.stop
    fdata['dura'] = flight.duration

    return fdata


def correct_baro(balt, t0, p0):
    '''
    A function to correct barometric altitude values from ISA to actual
    Inputs:
        -   balt: An array of baro altitudes
        -   t0: A float with the surface temperature (C)
        -   p0: A float with the surface pressure (hPa)
    Returns:
        -   An array of corrected baro alts
    '''
    isa_t = 15.0
    isa_p = 1013.25
    # First, compute ISA pressure
    tmp = (balt / 3.28084) / (273.15 + isa_t)
    pres = isa_p * np.power(1 - (0.0065 * tmp), 5.2561)
    # Now correct alt
    t1 = pres / p0
    t2 = 1. / 5.2561
    t3 = np.power(t1, t2)
    t4 = 1 - t3
    t5 = (273.15 + t0) / 0.0065
    alt = (t5 * t4) * 3.28084

    return alt


def create_spline(fd, bpos=None):
    '''
    Creates the splines needed for plotting smoothed lines
    on the output graphs
    Input:
        -   A dict of flight data, such as that returned by preproc_data()
        -   An int speicfying the max array value to use
    Returns:
        A dict containing:
        -   altspl
        -   spdspl
        -   rocspl
        -   galspl
        -   hdgspl
    '''
    spldict = {}
    if (bpos == None):
        bpos = len(fd['time'])
    spldict['altspl'] = UniSpl(fd['time'][0: bpos],
                               fd['alts'][0: bpos])(fd['time'][0: bpos])
    spldict['spdspl'] = UniSpl(fd['time'][0: bpos],
                               fd['spds'][0: bpos])(fd['time'][0: bpos])
    spldict['rocspl'] = UniSpl(fd['time'][0: bpos],
                               fd['rocs'][0: bpos])(fd['time'][0: bpos])
    spldict['galspl'] = UniSpl(fd['time'][0: bpos],
                               fd['gals'][0: bpos])(fd['time'][0: bpos])
    spldict['hdgspl'] = UniSpl(fd['time'][0: bpos],
                               fd['hdgs'][0: bpos])(fd['time'][0: bpos])
    spldict['latspl'] = UniSpl(fd['time'][0: bpos],
                               fd['lats'][0: bpos])(fd['time'][0: bpos])
    spldict['lonspl'] = UniSpl(fd['time'][0: bpos],
                               fd['lons'][0: bpos])(fd['time'][0: bpos])

    return spldict


def do_labels(fd):
    '''
    Perform the fuzzy labelling using Junzi's method.
    Add an additional force label of aircraft with "onground=True" to
    the 'GND' label category.
    Input:
        -   A dict of flight data, such as that returned by preproc_data()
    Returns:
        -   A numpy array containing categorised flight phases.
    '''
    labels = flph.fuzzylabels(fd['time'], fd['gals'],
                              fd['spds'], fd['rocs'], twindow=15)

    pts = (fd['ongd']).nonzero()
    labels[pts] = 'GND'

    return labels


def find_closest_metar(l_time, metars):
    '''
    Finds the best-fitting metar from a dict that matches a specified
    time value
    Inputs:
        -   The time to match (datetime)
        -   A dict of METARS, each as a metobs class
    Returns:
        The best metar (as metobs) and the time difference in seconds
    '''
    tdiff = 1e8
    bmet = None

    timelist = list(metars.keys())
    in_time = l_time.to_pydatetime()
    btim = min(timelist, key=lambda date: abs(in_time-date))
    tdiff = abs((btim - in_time).total_seconds())
    if (tdiff < 3600):
        bmet = metars[btim]
    return bmet, tdiff
