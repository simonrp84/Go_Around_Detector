from scipy.interpolate import UnivariateSpline as UniSpl
from matplotlib.lines import Line2D
from traffic.core import Traffic
import matplotlib.pyplot as plt
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
    alt_sub = df['gals'][0:5]
    if (np.all(alt_sub < CNS.takeoff_thresh_alt)):
        return True
    if (np.nanmean(alt_sub) < 3000):
        if (np.nanmean(alt_sub[0:2]) < np.nanmean(alt_sub[2:5])):
            return True
#    if (np.nanmean(df['rocs'] > 200)):
#        return True

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


def check_ga(fd, labels):
    '''
    Check if a go-around occurred based on some simple tests
    Inputs:
        -   A dict containing flight data
        -   The flight classification labels
    Returns:
        -   True if a go-around is likely to have occured
        -   False otherwise
    '''
    ga_flag = False

    lblen = len(labels)
    cng = np.zeros(lblen, dtype=bool)
    for i in range(1, lblen):
        if (labels[i] != labels[i-1]):
            cng[i] = True
    pts = (cng).nonzero()
    if (np.all(cng == False)):
        return ga_flag
    if (len(pts[0]) > 0):
        pts = pts[0]
    for pt in pts:
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
            alt_sub = fd['gals'][pt:len(fd['gals'])]
            vrt_sub = fd['rocs'][pt:len(fd['rocs'])]
            n_pos = len(fd['gals']) - pt
        else:
            alt_sub = fd['gals'][pt:t_pos]
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
            ga_flag = True

    return ga_flag


def proc_fl(flight, odir_norm, odir_goar, colormap, verbose):
    '''
    The main processing routine, filters, assigns phases and determines
    go-around status for a given flight.
    Inputs:
        -   A 'traffic' flight object
        -   A string specifying the output directory in which to save figures
            for normal (non-go-around) flights
        -   A string specifying the output directory in which to save figures
            for flights designated as possible go-arounds
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
    flight = flight.resample("1s")
    fd = preproc_data(flight)
    if (fd is None):
        if (verbose):
            print("\t-\tBad flight data:", flight.callsign)
        return -1
    takeoff = check_takeoff(fd)
    if (takeoff == True):
        return -1
    labels = do_labels(fd)
    if (np.all(labels == labels[0])):
        if (verbose):
            print("\t-\tNo state change:", flight.callsign)
        return -1

    ga_flag = check_ga(fd, labels)
    if (ga_flag):
#        if (verbose):
        print("\t-\tG/A warning:",
              fd['call'], fd['ic24'], fd['stop'], fd['dura'])
        odir = odir_goar
    else:
        odir = odir_norm

    spldict = create_spline(fd)
    do_plots(fd, spldict, labels, colormap, odir)
    if (verbose):
        print("\t-\tDONE")
    return ga_flag


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
    if (np.nanmean(flight.data['geoaltitude']) > 3000):
        return 'HIGH'
    if (np.all(flight.data['geoaltitude'] > 3000)):
        return 'HIGH'
    elif (np.all(flight.data['geoaltitude'] < 500)):
        return 'LOW'
    elif (np.all(flight.data['groundspeed'] < 50)):
        return 'SLOW'
    elif (np.all(flight.data['onground'])):
        return 'GROUND'
    else:
        return True


def preproc_data(flight):
    '''
    Preprocesses a flight into a format usable by Junzi's classifier

    Input:
        -   A flight produced by the 'traffic' library.
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
    if (not isgd):
        print("Unsuitable flight:", flight.callsign, isgd)
        return None

    f_data = flight.data
    try:
        f_data = f_data.drop_duplicates('last_position')
    except KeyError:
        None
    f_data = f_data.drop_duplicates('timestamp')
    f_data = f_data.drop_duplicates('track')
    f_data = f_data.drop_duplicates('longitude')
    f_data = f_data.drop_duplicates('latitude')
    f_data = f_data.query('altitude<10000')
    f_data = f_data.dropna()

    if(len(f_data) < 5):
        return None
    fdata = {}

    tmp = f_data['timestamp'].values
    ts = (tmp - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
    times = ts.astype(np.int)
    fdata['time'] = times - times[0]
    fdata['lats'] = f_data['latitude'].values
    fdata['lons'] = f_data['longitude'].values
    fdata['alts'] = f_data['altitude'].values
    fdata['spds'] = f_data['groundspeed'].values
    fdata['gals'] = f_data['geoaltitude'].values
    fdata['hdgs'] = f_data['track'].values
    fdata['rocs'] = f_data['vertical_rate'].values
    fdata['ongd'] = f_data['onground'].values
    fdata['call'] = flight.callsign
    fdata['ic24'] = flight.icao24
    fdata['strt'] = flight.start
    fdata['stop'] = flight.stop
    fdata['dura'] = flight.duration

    return fdata


def create_spline(fd):
    '''
    Creates the splines needed for plotting smoothed lines
    on the output graphs
    Input:
        -   A dict of flight data, such as that returned by preproc_data()
    Returns:
        A dict containing:
        -   altspl
        -   spdspl
        -   rocspl
        -   galspl
        -   hdgspl
    '''
    spldict = {}
    spldict['altspl'] = UniSpl(fd['time'], fd['alts'])(fd['time'])
    spldict['spdspl'] = UniSpl(fd['time'], fd['spds'])(fd['time'])
    spldict['rocspl'] = UniSpl(fd['time'], fd['rocs'])(fd['time'])
    spldict['galspl'] = UniSpl(fd['time'], fd['gals'])(fd['time'])
    spldict['hdgspl'] = UniSpl(fd['time'], fd['hdgs'])(fd['time'])

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


def do_plots(fd, spld, labels, cmap, odir, odpi=300):
    '''
    Inputs:
        -   A dict of flight data, such as that returned by preproc_data()
        -   A fict of splines, such as that returned by create_spline()
        -   A list of classifications, such as that returned by do_labels()
        -   A colour map, defined as a dict of classifications -> colors
        -   A string specifying the output directory
        -   (optional) An int specifying the desired output DPI
    Returns:
        -   Nothing
    '''
    colors = [cmap[l] for l in labels]
    fig, ax = plt.subplots(dpi=400)
    fs = (20, 20)
    custom_lines = []
    for color in cmap:
        lin = Line2D([0], [0], color=cmap[color], lw=0, marker='.')
        custom_lines.append(lin)

    plt.subplot(311)
    plt.plot(fd['time'], spld['galspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['time'], fd['gals']/1000., marker='.', c=colors, lw=0)
    plt.ylabel('altitude (kft)')

    plt.subplot(312)
    plt.plot(fd['time'], spld['rocspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['time'], fd['rocs']/1000., marker='.', c=colors, lw=0)
    plt.ylabel('roc (kfpm)')

    plt.subplot(313)
    plt.plot(fd['time'], spld['spdspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['time'], fd['spds'], marker='.', c=colors, lw=0)
    plt.ylabel('speed (kts)')

    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               bbox_to_anchor=(0., -0.33, 1., 0.102),
               loc='upper left',
               ncol=6,
               mode="expand", borderaxespad=0.)

    plt.tight_layout()
    timestr = fd['stop'].strftime("%Y%m%d%H%M")
    plt.savefig(odir + fd['call'] + '_' + timestr + '_STATE.png',
                figsize=fs,
                dpi=odpi,
                bbox_inches='tight',
                pad_inches=0)
    plt.close()
