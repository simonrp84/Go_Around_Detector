from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import os


def do_plots(fd, spld, cmap, outdir, app_ylim=True, odpi=300, rwy=None):
    '''
    Creates and saves a series of plots showing relevant data for each
    flight that has been processed. Files are saved in a /YYYMMDD/
    subdirectory of the 'outdir' argument.
    This version saves data with time since first appearance in the
    datastream on the x-axis.
    Inputs:
        -   A dict of flight data, such as that returned by preproc_data()
        -   A fict of splines, such as that returned by create_spline()
        -   A colour map, defined as a dict of classifications -> colors
        -   A string specifying the output directory
        -   (optional) A bool specifying to apply predefined axis limits.
        -   (optional) An int specifying the desired output DPI
        -   (optional) A runway class specifying the landing runway, or None
    Returns:
        -   Nothing
    '''
    colors = [cmap[l] for l in fd['labl']]
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
    if (app_ylim):
        plt.ylim(-0.5, 10.)

    plt.subplot(312)
    plt.plot(fd['time'], spld['rocspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['time'], fd['rocs']/1000., marker='.', c=colors, lw=0)
    plt.ylabel('roc (kfpm)')
    if (app_ylim):
        plt.ylim(-0.5, 10.)

    plt.subplot(313)
    plt.plot(fd['time'], spld['spdspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['time'], fd['spds'], marker='.', c=colors, lw=0)
    plt.ylabel('speed (kts)')
    if (app_ylim):
        plt.ylim(0., 400.)

    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               bbox_to_anchor=(0., -0.33, 1., 0.102),
               loc='upper left',
               ncol=6,
               mode="expand", borderaxespad=0.)

    plt.tight_layout()

    odir = outdir + fd['stop'].strftime("%Y%m%d") + '/'
    if (not os.path.exists(odir)):
        try:
            os.mkdir(odir)
        except:
            None

    timestr = fd['stop'].strftime("%Y%m%d%H%M")
    outf = odir + 'FLT_' + fd['ic24'] + '_'
    outf = outf + fd['call'] + '_'
    outf = outf + timestr + '_TIME.png'
    plt.savefig(outf,
                figsize=fs,
                dpi=odpi,
                bbox_inches='tight',
                pad_inches=0)
    plt.close()


def get_fig_outname(outdir, fd, figtype):
    odir = outdir + fd['stop'].strftime("%Y%m%d") + '/'
    if (not os.path.exists(odir)):
        try:
            os.mkdir(odir)
        except:
            None

    timestr = fd['stop'].strftime("%Y%m%d%H%M")
    outf = odir + 'FLT_' + fd['ic24'] + '_'
    outf = outf + fd['call'] + '_'
    outf = outf + timestr + '_' + figtype + '.png'

    return outf
    
def make_yvals(dists, multis):
    '''
    Return a list of y-values associated with a 6th order polynomial
    and some x values.
    Inputs:
        -   dists: List of x axis coords
        -   multis: Polynomial coefficientsd
    Returns:
        -   A list of y values
    '''
    yvals = (np.power(dists, 6) * multis[0] +
             np.power(dists, 5) * multis[1] +
             np.power(dists, 4) * multis[2] +
             np.power(dists, 3) * multis[3] +
             np.power(dists, 2) * multis[4] +
             np.power(dists, 1) * multis[5] +
             multis[6])

    return yvals

def do_plots_dist(fd, spld, cmap, outdir,
                  app_xlim=True, app_ylim=False, odpi=300, rwy=None, bpos = None):
    '''
    Creates and saves a series of plots showing relevant data for each
    flight that has been processed. Files are saved in a /YYYMMDD/
    subdirectory of the 'outdir' argument.
    This version saves data with distance to detected landing runway on the
    x-axis.
    Inputs:
        -   A dict of flight data, such as that returned by preproc_data()
        -   A fict of splines, such as that returned by create_spline()
        -   A colour map, defined as a dict of classifications -> colors
        -   A string specifying the output directory
        -   (optional) A bool specifying to apply predefined x-axis limits.
        -   (optional) A bool specifying to apply predefined y-axis limits.
        -   (optional) An int specifying the desired output DPI
        -   (optional) A runway class specifying the landing runway, or None
        -   (optional) An int specifying the max array position
    Returns:
        -   Nothing
    '''

    if (bpos == None):
        bpos = len(fd['time'])

    xlims = [-10., 0.1]
    distlist = np.arange(xlims[0], xlims[1] + 0.01, 0.01)
    if (rwy is not None):
        hdglim = [rwy.mainhdg - 5, rwy.mainhdg + 5]
    else:
        hme = np.nanmean(fd['hdgs'])
        hdglim = [hme - 5, hme + 5]
    
    colors = [cmap[l] for l in fd['labl'][0:bpos]]
    fs = (20, 20)
    custom_lines = []
    for color in cmap:
        lin = Line2D([0], [0], color=cmap[color], lw=0, marker='.')
        custom_lines.append(lin)
    
    
    tmprd = np.copy(fd['rdis'])
    pts = (tmprd < xlims[0]).nonzero()
    tmprd[pts] = np.nan
    pts = (tmprd > xlims[1]).nonzero()
    tmprd[pts] = np.nan
    pts = (tmprd == tmprd).nonzero()

#    plt.plot(fd['rdis'], spld['altspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'][0:bpos], fd['alts'][0:bpos]/1000., marker='.', c=colors, lw=0)
    if (rwy is not None):
        yvals1 = make_yvals(distlist, rwy.alts1)
        yvalm = make_yvals(distlist, rwy.altm)
        yvalp1 = make_yvals(distlist, rwy.altp1)
        plt.plot(distlist, yvals1/1000., '-', color='k', lw=0.1)
        plt.plot(distlist, yvalm/1000., '-', color='k', lw=0.1)
        plt.plot(distlist, yvalp1/1000., '-', color='k', lw=0.1)
    plt.ylabel('Altitude (kft)')
    plt.xlabel('Distance to Runway (km)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['alts'][0:bpos]/1000)
        y_max = np.nanmax(fd['alts'][0:bpos]/1000)
        plt.ylim(y_min-0.1, y_max+0.1)
    if (app_ylim):
        plt.ylim(0., 5.)
    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               loc='best',
               #bbox_to_anchor=(0.5, -0.01),
               ncol=6,
               fancybox=False,
               mode="expand")
    plt.tight_layout()
    outf = get_fig_outname(outdir, fd, 'ALT')
    plt.savefig(outf, figsize=fs, dpi=odpi, bbox_inches='tight', pad_inches=0)
    plt.clf()

#    plt.plot(fd['rdis'], spld['rocspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'][0:bpos], fd['rocs'][0:bpos]/1000., marker='.', c=colors, lw=0)
    if (rwy is not None):
        yvals1 = make_yvals(distlist, rwy.rocs1)
        yvalm = make_yvals(distlist, rwy.rocm)
        yvalp1 = make_yvals(distlist, rwy.rocp1)
        plt.plot(distlist, yvals1/1000., '-', color='k', lw=0.1)
        plt.plot(distlist, yvalm/1000., '-', color='k', lw=0.1)
        plt.plot(distlist, yvalp1/1000., '-', color='k', lw=0.1)
    plt.ylabel('Climb Rate (kfpm)')
    plt.xlabel('Distance to Runway (km)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['rocs'][0:bpos]/1000)
        y_max = np.nanmax(fd['rocs'][0:bpos]/1000)
        plt.ylim(y_min-0.1, y_max+0.1)
    if (app_ylim):
        plt.ylim(-1.5, 1.5)
    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               loc='best',
               #bbox_to_anchor=(0.5, -0.01),
               ncol=6,
               fancybox=False,
               mode="expand")
    plt.tight_layout()
    outf = get_fig_outname(outdir, fd, 'ROC')
    plt.savefig(outf, figsize=fs, dpi=odpi, bbox_inches='tight', pad_inches=0)
    plt.clf()

#    plt.plot(fd['rdis'], spld['spdspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'][0:bpos], fd['spds'][0:bpos], marker='.', c=colors, lw=0)
    plt.ylabel('Ground Speed (kts)')
    plt.xlabel('Distance to Runway (km)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['spds'][0:bpos])
        y_max = np.nanmax(fd['spds'][0:bpos])
        plt.ylim(y_min-10, y_max+10)
    if (app_ylim):
        plt.ylim(100., 250.)
    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               loc='best',
               #bbox_to_anchor=(0.5, -0.01),
               ncol=6,
               fancybox=False,
               mode="expand")
    plt.tight_layout()
    outf = get_fig_outname(outdir, fd, 'SPD')
    plt.savefig(outf, figsize=fs, dpi=odpi, bbox_inches='tight', pad_inches=0)
    plt.clf()

#    plt.plot(fd['rdis'], spld['hdgspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'][0:bpos], fd['hdgs'][0:bpos], marker='.', c=colors, lw=0)
    if (rwy is not None):
        yvals1 = make_yvals(distlist, rwy.hdgs1)
        yvalm = make_yvals(distlist, rwy.hdgm)
        yvalp1 = make_yvals(distlist, rwy.hdgp1)
        plt.plot(distlist, yvals1, '-', color='k', lw=0.1)
        plt.plot(distlist, yvalm, '-', color='k', lw=0.1)
        plt.plot(distlist, yvalp1, '-', color='k', lw=0.1)
    plt.ylabel('Heading (deg)')
    plt.xlabel('Distance to Runway (km)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['hdgs'][0:bpos])
        y_max = np.nanmax(fd['hdgs'][0:bpos])
        plt.ylim(y_min-10, y_max+10)
    if (app_ylim):
        plt.ylim(hdglim[0], hdglim[1])
    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               loc='best',
               #bbox_to_anchor=(0.5, -0.01),
               ncol=6,
               fancybox=False,
               mode="expand")
    plt.tight_layout()
    outf = get_fig_outname(outdir, fd, 'HDG')
    plt.savefig(outf, figsize=fs, dpi=odpi, bbox_inches='tight', pad_inches=0)
    plt.clf()

#    plt.plot(fd['rdis'], spld['lonspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'][0:bpos], fd['lons'][0:bpos], marker='.', c=colors, lw=0)
    if (rwy is not None):
        yvals1 = make_yvals(distlist, rwy.lons1)
        yvalm = make_yvals(distlist, rwy.lonm)
        yvalp1 = make_yvals(distlist, rwy.lonp1)
        plt.plot(distlist, yvals1, '-', color='k', lw=0.1)
        plt.plot(distlist, yvalm, '-', color='k', lw=0.1)
        plt.plot(distlist, yvalp1, '-', color='k', lw=0.1)
    plt.ylabel('Longitude (deg)')
    plt.xlabel('Distance to Runway (km)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['lons'][0:bpos])
        y_max = np.nanmax(fd['lons'][0:bpos])
        adder = (y_max - y_min) * 0.2
        plt.ylim(y_min - adder, y_max + adder)
    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               loc='best',
               #bbox_to_anchor=(0.5, -0.01),
               ncol=6,
               fancybox=False,
               mode="expand")
    plt.tight_layout()
    outf = get_fig_outname(outdir, fd, 'LON')
    plt.savefig(outf, figsize=fs, dpi=odpi, bbox_inches='tight', pad_inches=0)
    plt.clf()

#    plt.plot(fd['rdis'], spld['latspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'][0:bpos], fd['lats'][0:bpos], marker='.', c=colors, lw=0)
    if (rwy is not None):
        yvals1 = make_yvals(distlist, rwy.lats1)
        yvalm = make_yvals(distlist, rwy.latm)
        yvalp1 = make_yvals(distlist, rwy.latp1)
        plt.plot(distlist, yvals1, '-', color='k', lw=0.1)
        plt.plot(distlist, yvalm, '-', color='k', lw=0.1)
        plt.plot(distlist, yvalp1, '-', color='k', lw=0.1)
    plt.ylabel('Latitude (deg)')
    plt.xlabel('Distance to Runway (km)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['lats'][0:bpos])
        y_max = np.nanmax(fd['lats'][0:bpos])
        adder = (y_max - y_min) * 0.2
        plt.ylim(y_min - adder, y_max + adder)
    plt.legend(custom_lines,
               ['Ground', 'Climb', 'Cruise', 'Descent', 'Level', 'N/A'],
               loc='best',
               #bbox_to_anchor=(0.5, -0.01),
               ncol=6,
               fancybox=False,
               mode="expand")
    plt.tight_layout()
    outf = get_fig_outname(outdir, fd, 'LAT')
    plt.savefig(outf, figsize=fs, dpi=odpi, bbox_inches='tight', pad_inches=0)
    plt.clf()


def to_numpy(fd, outdir):
    '''
    Save data for a single flight into a numpy pickle file.
    Files are saved in a YYYYMMDD subdirectory.
    Inputs:
        -   fd: Dict containing flight info
        -   outdir: Location to store output
    Returns:
        -   Nothing
    '''
    odir = outdir + fd['stop'].strftime("%Y%m%d") + '/'
    if (not os.path.exists(odir)):
        try:
            os.mkdir(odir)
        except:
            None
    outf = odir + 'FLT_' + fd['ic24'] + '_'
    outf = outf + fd['call'] + '_'
    outf = outf + fd['stop'].strftime("%Y%m%d%H%m") + '.pkl'
    np.save(outf, fd)
