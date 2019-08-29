from scipy.interpolate import UnivariateSpline as UniSpl
from traffic.core import Traffic
from datetime import timedelta
import pandas as pd

import flightphase as flph
import OS_Output as OSO
import OS_Consts as CNS
import numpy as np


def estimate_rwy(df, rwy_list, verbose):
    '''
    Guesses which runway a flight is attempting to land on
    Inputs:
        -   df, a dict containing flight information
        -   rwy_list, a list of runways to check, defined in OS_Airports
        -   verbose, a bool specifying whether to verbosely print updates
    Returns:
        -   A runway class from the list.
    '''
    b_dist = 999.
    b_rwy = None
    b_pos = -1.

    for run in range(0, 2):
        for rwy in rwy_list:
            dists2 = np.sqrt((df['lats'] - rwy.gate[0]) *
                             (df['lats'] - rwy.gate[0]) +
                             (df['lons'] - rwy.gate[1]) *
                             (df['lons'] - rwy.gate[1]))
            min_d = np.nanmin(dists2)
            if (min_d < b_dist):
                pt2 = (min_d == dists2).nonzero()
                if (len(pt2[0]) > 0):
                    pt2 = pt2[0]
                pt2 = pt2[0]

                if (run == 1):
                    dists2[pt2] = 999.
                    min_d = np.nanmin(dists2)
                    pt2 = (min_d == dists2).nonzero()
                    if (len(pt2[0]) > 0):
                        pt2 = pt2[0]
                    pt2 = pt2[0]
                if (df['gals'][pt2] > CNS.gate_alt):
                    if (verbose):
                        print("Bad geo alt", df['call'],
                              df['gals'][pt2], CNS.gate_alt)
                    continue
                if (df['rocs'][pt2] > CNS.gate_roc):
                    if (verbose):
                        print("Bad rate of climb", df['call'],
                              df['rocs'][pt2], CNS.gate_roc)
                    continue
                if (df['hdgs'][pt2] >= rwy.heading[0] and
                        df['hdgs'][pt2] <= rwy.heading[1]):
                    b_dist = min_d
                    b_rwy = rwy
                    b_pos = pt2
                elif (df['hdgs'][pt2] >= rwy.heading[2] and
                      df['hdgs'][pt2] <= rwy.heading[3]):
                    b_dist = min_d
                    b_rwy = rwy
                    b_pos = pt2
                else:
                    if (verbose):
                        print("Bad heading", df['call'],
                              df['hdgs'][pt2], rwy.heading)
                    continue
    if (b_dist > CNS.gate_dist):
        if (verbose):
            print("too far", df['call'], b_dist, CNS.gate_dist)
        return None, b_pos

    return b_rwy, b_pos


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


def check_takeoff(df):
    '''
    Checks if a flight is taking off. If so, we're not interested
    Input:
        -   df, a dict containing flight data
    Returns:
        -   True if a takeoff, otherwise False
    '''
    lf = len(df['gals'])
    # Check if there's enough data to process
    if (lf < 10):
        return True
    # Check if the first datapoints are all low alt
    # Two options here: geo alt or baro alt.
    # Geo often has false data
    # Baro can be troublesome as it depends on weather
    alt_sub = df['gals'][0:5]
    alt_sub2 = df['alts'][0:5]

    if (np.all(df['ongd'][0:5])):
        if (np.nanmean(alt_sub2 < 3000)):
            return True
    if (np.all(alt_sub < CNS.takeoff_thresh_alt)):
        return True
    if (np.nanmean(alt_sub) < 3000):
        if (np.nanmean(alt_sub2[0:2]) < np.nanmean(alt_sub2[2:5])):
            return True
    if (np.nanmean(df['rocs'][0:5] > 1500)):
        return True

    return False


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


def check_ga(fd, verbose, first_pos=-1):
    '''
    Check if a go-around occurred based on some simple tests
    Inputs:
        -   A dict containing flight data
        -   A boolean for verbose mode. If True, a g/a warning is printed
        -   (optional) An int specifying the first position in array to check
            This is useful for situations with multiple g/a's in one track
    Returns:
        -   True if a go-around is likely to have occurred, false otherwise
        -   An int specifying the array location where g/a occurred, or None
    '''
    ga_flag = False
    bpt = None

    labels = fd['labl']

    lblen = len(labels)
    cng = np.zeros(lblen, dtype=bool)
    for i in range(1, lblen):
        if (labels[i] != labels[i-1]):
            cng[i] = True
    main_pts = (cng).nonzero()
    if (np.all(cng == False)):
        return ga_flag
    if (len(main_pts[0]) > 0):
        main_pts = main_pts[0]
    for pt in main_pts:
        #   Check data is in desired range
        if (pt < first_pos):
            continue
        # First check altitude of state change. G/A will be low alt
        if (fd['gals'][pt] > CNS.ga_st_alt_t):
            continue
        # We only want points where initial state is Descent
        if (labels[pt-1] != "DE"):
            continue
        # And the next state should be level or climbing
        if (labels[pt] != "LVL" and labels[pt] != "CL"):
            continue
        # Now we check future altitudes, some must be > threshold
        # to be defined as a go-around, otherwise it could be
        # bad data on landing
        t_pos = get_future_time(fd['time'], pt, CNS.ga_tcheck)
        if (t_pos < 0):
            lenner = len(fd['alts'])
            r_time = np.nanmean(fd['time'][pt:lenner])
            if (r_time > fd['time'][pt] + (CNS.ga_tcheck * 2.)):
                continue
            alt_sub = fd['alts'][pt:lenner]
            vrt_sub = fd['rocs'][pt:lenner]
            n_pos = len(fd['alts']) - pt
        else:
            alt_sub = fd['alts'][pt:t_pos]
            vrt_sub = fd['rocs'][pt:t_pos]
            n_pos = t_pos - pt

        # Remove dodgy datapoints, sometimes on landing an aircraft
        # will report its position as very high (30+kft)
        pts = (alt_sub > 20000).nonzero()
        alt_sub[pts] = -10000

        alt_test = (alt_sub > CNS.alt_thresh)
        pts_alt = (alt_test).nonzero()
        if (len(pts_alt[0]) > 0):
            pts_alt = pts_alt[0]

        vrt_test = (vrt_sub > CNS.vrt_thresh)
        pts_vrt = (vrt_test).nonzero()
        if (len(pts_vrt[0]) > 0):
            pts_vrt = pts_vrt[0]

        n_pts_alt = len(pts_alt)
        n_pts_vrt = len(pts_vrt)
        alts_p = (n_pts_alt/n_pos)*100.
        vrts_p = (n_pts_vrt/n_pos)*100.

        if (n_pos > 10 and alts_p > 50 and vrts_p > 20):
            if (verbose):
                ga_time = fd['strt'] + timedelta(seconds=int(fd['time'][pt]))
                print("\t-\tG/A warning:",
                      fd['call'],
                      fd['ic24'],
                      ga_time.strftime("%Y-%m-%d %H:%M"))
            ga_flag = True
            bpt = pt

    return ga_flag, bpt


def proc_fl(flight, check_rwys, odirs, colormap, metars, do_save, verbose):
    '''
    The main processing routine, filters, assigns phases and determines
    go-around status for a given flight.
    Inputs:
        -   A 'traffic' flight object
        -   A list storing potential landing runways to check
        -   A 4-element list specifying various output directories:
            -   normal plot output
            -   go-around plot output
            -   normal numpy data output
            -   go-around numpy data output
        -   A dict of colours used for flightpath labelling
        -   A dict of METARs used for correcting barometric altitude
        -   A boolean specifying whether to save data or not
        -   A boolean specifying whether to use verbose mode
    Returns:
        -   Nothing
    '''

    gd_fl = check_good_flight(flight)
    if (not gd_fl):
        if (verbose):
            print("\t-\tBad flight call:", flight.callsign)
        return -1
    if (verbose):
        print("\t-\tProcessing:", flight.callsign)
    flight2 = flight.resample("1s")
    fd = preproc_data(flight, verbose)
    fd2 = preproc_data(flight2, verbose)
    if (fd is None):
        if (verbose):
            print("\t-\tBad flight data:", flight.callsign, fd)
        return -1
    if (fd2 is None):
        if (verbose):
            print("\t-\tBad flight data:", flight.callsign, fd2)
        return -1
    takeoff = check_takeoff(fd)
    if (takeoff == True):
        return -1
    labels = do_labels(fd)
    if (np.all(labels == labels[0])):
        if (verbose):
            print("\t-\tNo state change:", flight.callsign)
        return -1
    fd['labl'] = labels

    rwy, posser = estimate_rwy(fd2, check_rwys, verbose)
    if (rwy is None):
        if (verbose):
            print('WARNING: Cannot find runway for flight '
                  + fd['call'] + ' ' + fd['ic24'])
        pt = (np.nanmin(fd['alts']) == fd['alts']).nonzero()
        if (len(pt[0]) > 0):
            pt = pt[0]
        pt = pt[0]
        fd['rwy'] = "None"
        r_dis = np.sqrt((fd['lats'] - fd['lats'][pt]) *
                        (fd['lats'] - fd['lats'][pt]) +
                        (fd['lons'] - fd['lons'][pt]) *
                        (fd['lons'] - fd['lons'][pt]))
    else:
        fd['rwy'] = rwy.name
        r_dis = np.sqrt((fd['lats'] - rwy.rwy[0]) *
                        (fd['lats'] - rwy.rwy[0]) +
                        (fd['lons'] - rwy.rwy[1]) *
                        (fd['lons'] - rwy.rwy[1]))
    r_dis = r_dis * 112.
    pt = (np.nanmin(r_dis) == r_dis).nonzero()
    if (len(pt[0]) > 0):
        pt = pt[0]
    pt = pt[0]
    r_dis[0:pt] = r_dis[0:pt] * -1
    fd['rdis'] = r_dis
    
    # Correct barometric altitudes
    t_alt = fd['alts']
    l_time = fd['strt'] + (fd['dura'] / 2)
    l_time = pd.Timestamp(l_time, tz='UTC')
    bmet, tdiff = find_closest_metar(l_time, metars)
    if (bmet is not None):
        t_alt = correct_baro(t_alt, bmet.temp, bmet.pres)
    else:
        print("Warning: No METAR available for alt correction!",
              bmet, tdiff, l_time)
    fd['alts'] = t_alt

    ga_flag, gapt = check_ga(fd, True)
            
    if (do_save):
        spldict = create_spline(fd, bpos = gapt)
        if (ga_flag):
            odir_pl = odirs[1]
            odir_np = odirs[3]
        else:
            odir_pl = odirs[0]
            odir_np = odirs[2]
#        OSO.do_plots(fd, spldict, colormap, odir_pl, rwy=rwy)
        if (ga_flag):
            OSO.do_plots_dist(fd, spldict, colormap, odir_pl, rwy=rwy, bpos = gapt)
    if (rwy != None):
        garr = [ga_flag, fd['ic24'], fd['call'], l_time, rwy.name, bmet]
    else:
        garr = [ga_flag, fd['ic24'], fd['call'], l_time, 'None', bmet]
#        OSO.to_numpy(fd, odir_np)
    if (verbose):
        print("\t-\tDONE")
    return garr


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


def create_spline(fd, bpos = None):
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
    spldict['altspl'] = UniSpl(fd['time'][0: bpos], fd['alts'][0: bpos])(fd['time'][0: bpos])
    spldict['spdspl'] = UniSpl(fd['time'][0: bpos], fd['spds'][0: bpos])(fd['time'][0: bpos])
    spldict['rocspl'] = UniSpl(fd['time'][0: bpos], fd['rocs'][0: bpos])(fd['time'][0: bpos])
    spldict['galspl'] = UniSpl(fd['time'][0: bpos], fd['gals'][0: bpos])(fd['time'][0: bpos])
    spldict['hdgspl'] = UniSpl(fd['time'][0: bpos], fd['hdgs'][0: bpos])(fd['time'][0: bpos])
    spldict['latspl'] = UniSpl(fd['time'][0: bpos], fd['lats'][0: bpos])(fd['time'][0: bpos])
    spldict['lonspl'] = UniSpl(fd['time'][0: bpos], fd['lons'][0: bpos])(fd['time'][0: bpos])

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
