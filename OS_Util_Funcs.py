from datetime import timedelta

import OS_Data_Funcs as ODF
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


def check_ga_meth1(fd, bpos, verbose):
    '''
        Simple check based on +ve rate of climb within one minute
        after minimum alt, consistent for 3 reports
    '''

    bpos = int(bpos[0])
    times = fd['time']
    time = float(times[bpos])
    le = len(times)
    times = times[bpos:le]
    rocs = fd['rocs'][bpos:le]
    ongd = fd['ongd'][bpos:le]

    pts = (times < time + CNS.ga_tcheck).nonzero()
    rocs = rocs[pts]
    ongd = ongd[pts]

    nabove = 0
    ga_flag = False

    for i in range(0, len(rocs)):
        if (rocs[i] > 0 and ongd[i] != True):
            nabove = nabove + 1
        else:
            nabove = 0
    if (nabove > 2):
        ga_flag = True
    else:
        bpos = None
        ga_flag = False

    return ga_flag, bpos


def check_ga_meth2(fd, bpos, verbose):
    '''
        Simple check based on increasing altitude reports
        within one minute after minimum alt, consistent for 3 reports
    '''

    bpos = int(bpos[0])
    times = fd['time']
    time = float(times[bpos])
    le = len(times)
    times = times[bpos:le]
    alts = fd['alts'][bpos:le]
    ongd = fd['ongd'][bpos:le]

    pts = (times < time + CNS.ga_tcheck * 2).nonzero()
    alts = alts[pts]
    ongd = ongd[pts]

    nabove = 0
    ga_flag = False

    for i in range(1, len(alts)):
        if (alts[i] >= alts[i-1] and ongd[i] != True):
            nabove = nabove + 1
        else:
            nabove = 0
    if (nabove > 2):
        ga_flag = True
    else:
        bpos = None
        ga_flag = False

    return ga_flag, bpos


def check_ga_meth3(fd, bpos, verbose):
    '''
        This check combines both methods 1 and 2 in an attempt
        to remove some false-positives
    '''

    bpos = int(bpos[0])
    times = fd['time']
    time = float(times[bpos])
    le = len(times)
    times = times[bpos:le]
    alts = fd['alts'][bpos:le]
    ongd = fd['ongd'][bpos:le]
    rocs = fd['rocs'][bpos:le]

    pts = (times < time + CNS.ga_tcheck).nonzero()
    alts = alts[pts]
    ongd = ongd[pts]
    rocs = rocs[pts]

    nabove1 = 0
    nabove2 = 0
    ga_flag = False

    for i in range(1, len(alts)):
        if (alts[i] >= alts[i-1] and ongd[i] != True):
            nabove1 = nabove1 + 1
        else:
            nabove1 = 0

    for i in range(0, len(rocs)):
        if (rocs[i] > 0 and ongd[i] != True):
            nabove2 = nabove2 + 1
        else:
            nabove2 = 0

    if (nabove1 > 2 and nabove2 > 2):
        ga_flag = True
    else:
        bpos = None
        ga_flag = False

    return ga_flag, bpos


def check_ga_meth4(fd, bpos, verbose):
    '''
        Simple check based on ground speed after minimum altitude
        position. For a g/a we expect reasonably high (>100kt) speed
        while for a landing the speed will decrease
    '''

    bpos = int(bpos[0])
    times = fd['time']
    time = float(times[bpos])
    le = len(times)
    times = times[bpos:le]
    gspd = fd['spds'][bpos:le]
    alts = fd['alts'][bpos:le]
    ongd = fd['ongd'][bpos:le]

    pts = (times < time + CNS.ga_tcheck).nonzero()
    gspd = gspd[pts]
    ongd = ongd[pts]
    alts = alts[pts]

    nabove = 0
    ga_flag = False

    for i in range(0, len(gspd)):
        if (gspd[i] > 120 and not ongd[i] != True):
            nabove = nabove + 1

    if (nabove > 4 and np.nanmax(alts) > 500):
        ga_flag = True
    else:
        bpos = None
        ga_flag = False

    return ga_flag, bpos


def check_ga_meth5(fd, verbose, first_pos=-1):
    '''
    Check if a go-around occurred based on some more advanced tests
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
        t_pos = ODF.get_future_time(fd['time'], pt, CNS.ga_tcheck)
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
