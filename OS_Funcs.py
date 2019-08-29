import pandas as pd
import OS_Util_Funcs as OUF
import OS_Data_Funcs as ODF
import metar_parse as MEP
import numpy as np

# Read METARs from disk
metars = MEP.get_metars('/home/proud/Desktop/GoAround_Paper/VABB_METAR')


def proc(flight, check_rwys, verbose):
    '''
    The main processing routine, filters, assigns phases and determines
    go-around status for a given flight using several different methods
    Inputs:
        -   A 'traffic' flight object
        -   A list storing potential landing runways to check
        -   A boolean specifying whether to use verbose mode
    Returns:
        -   G/A status from each method
    '''

    # Setup the g/a flags for the five test methods
    ga_flag_m1 = False
    ga_flag_m2 = False
    ga_flag_m3 = False
    ga_flag_m4 = False
    ga_flag_m5 = False

    # Check we are looking at a suitable flight
    gd_fl = ODF.check_good_flight(flight)
    if (not gd_fl):
        if (verbose):
            print("\t-\tBad flight call:", flight.callsign)
        return -1
    if (verbose):
        print("\t-\tProcessing:", flight.callsign)

    # Do some preprocessing and check if it is good
    fd = ODF.preproc_data(flight, verbose)
    if (fd is None):
        if (verbose):
            print("\t-\tBad flight data:", flight.callsign, fd)
        return -1

    # We are only interested in landings, so check that a flight is not a
    # takeoff. If it is, discard and return
    takeoff = OUF.check_takeoff(fd)
    if (takeoff):
        return -1

    # Correct barometric altitudes using nearest METAR
    t_alt = fd['alts']
    l_time = fd['strt'] + (fd['dura'] / 2)
    l_time = pd.Timestamp(l_time, tz='UTC')
    bmet, tdiff = ODF.find_closest_metar(l_time, metars)
    if (bmet is not None):
        t_alt = ODF.correct_baro(t_alt, bmet.temp, bmet.pres)
    else:
        print("Warning: No METAR available for alt correction!",
              bmet, tdiff, l_time)
    fd['alts'] = t_alt

    # First, find the minumum altitude position

    tmp_alts = fd['alts']
    pts = (fd['ongd']).nonzero()
    if (len(pts[0]) > 0):
        pts = pts[0]
    for pt in pts:
        if (pt > 3):
            tmp_alts[pt-3] = 40000
            tmp_alts[pt-2] = 40000
            tmp_alts[pt-1] = 40000
            tmp_alts[pt] = 40000

    pt = (np.nanmin(tmp_alts) == tmp_alts).nonzero()
    if (len(pt[0]) > 0):
        pt = pt[0]

    # Get the labels
    labels = ODF.do_labels(fd)
    if (np.all(labels == labels[0])):
        if (verbose):
            print("\t-\tNo state change:", flight.callsign)
        return -1
    fd['labl'] = labels

    # Go-around detection method 1
    ga_flag_m1, gapt1 = OUF.check_ga_meth1(fd, pt, verbose)

    # Go-around detection method 2
    ga_flag_m2, gapt2 = OUF.check_ga_meth2(fd, pt, verbose)

    # Go-around detection method 3
    ga_flag_m3, gapt3 = OUF.check_ga_meth3(fd, pt, verbose)

    # Go-around detection method 4
    ga_flag_m4, gapt4 = OUF.check_ga_meth4(fd, pt, verbose)

    # Go-around detection method 5
    ga_flag_m5, gapt5 = OUF.check_ga_meth5(fd, True)

    garr = [fd['ic24'], l_time, ga_flag_m1,
            ga_flag_m2, ga_flag_m3, ga_flag_m4, ga_flag_m5]

    if (verbose):
        print("\t-\tDONE")
    return garr
