from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import os


def do_plots(fd, spld, labels, cmap, outdir, app_ylim = True, odpi=300):
    '''
    Creates and saves a series of plots showing relevant data for each
    flight that has been processed. Files are saved in a /YYYMMDD/
    subdirectory of the 'outdir' argument.
    This version saves data with time since first appearance in the
    datastream on the x-axis.
    Inputs:
        -   A dict of flight data, such as that returned by preproc_data()
        -   A fict of splines, such as that returned by create_spline()
        -   A list of classifications, such as that returned by do_labels()
        -   A colour map, defined as a dict of classifications -> colors
        -   A string specifying the output directory
        -   (optional) A bool specifying to apply predefined axis limits.
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
    outf = outf + timestr + '.png'
    plt.savefig(outf,
                figsize=fs,
                dpi=odpi,
                bbox_inches='tight',
                pad_inches=0)
    plt.close()


def do_plots_dist(fd, spld, labels, cmap, outdir,
                  app_xlim = True, app_ylim = False, odpi=300):
    '''
    Creates and saves a series of plots showing relevant data for each
    flight that has been processed. Files are saved in a /YYYMMDD/
    subdirectory of the 'outdir' argument.
    This version saves data with distance to detected landing runway on the
    x-axis.
    Inputs:
        -   A dict of flight data, such as that returned by preproc_data()
        -   A fict of splines, such as that returned by create_spline()
        -   A list of classifications, such as that returned by do_labels()
        -   A colour map, defined as a dict of classifications -> colors
        -   A string specifying the output directory
        -   (optional) A bool specifying to apply predefined x-axis limits.
        -   (optional) A bool specifying to apply predefined y-axis limits.
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

    xlims = [-10., 3]
    tmprd = np.copy(fd['rdis'])
    pts = (tmprd < xlims[0]).nonzero()
    tmprd[pts] = np.nan
    pts = (tmprd > xlims[1]).nonzero()
    tmprd[pts] = np.nan
    pts = (tmprd == tmprd).nonzero()
    
#    print(tmprd[pts])
#    print(fd['rdis'][pts])
#    print(fd['gals'][pts])
#    print(tmprd[pts])
#    print(tmprd[pts])
#    print(tmprd[pts])

    plt.subplot(311)
    plt.plot(fd['rdis'], spld['galspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'], fd['gals']/1000., marker='.', c=colors, lw=0)
    plt.ylabel('altitude (kft)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['gals'][pts]/1000)
        y_max = np.nanmax(fd['gals'][pts]/1000)
        plt.ylim(y_min-0.1, y_max+0.1)
    if (app_ylim):
        plt.ylim(-0.5, 10.)

    plt.subplot(312)
    plt.plot(fd['rdis'], spld['rocspl']/1000., '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'], fd['rocs']/1000., marker='.', c=colors, lw=0)
    plt.ylabel('roc (kfpm)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['rocs'][pts]/1000)
        y_max = np.nanmax(fd['rocs'][pts]/1000)
        plt.ylim(y_min-0.1, y_max+0.1)
    if (app_ylim):
        plt.ylim(-2.5, 2.5)

    plt.subplot(313)
    plt.plot(fd['rdis'], spld['spdspl'], '-', color='k', lw=0.1)
    plt.scatter(fd['rdis'], fd['spds'], marker='.', c=colors, lw=0)
    plt.ylabel('speed (kts)')
    if (app_xlim):
        plt.xlim(xlims[0], xlims[1])
        y_min = np.nanmin(fd['spds'][pts])
        y_max = np.nanmax(fd['spds'][pts])
        plt.ylim(y_min-10, y_max+10)
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
    outf = outf + timestr + '.png'
    plt.savefig(outf,
                figsize=fs,
                dpi=odpi,
                bbox_inches='tight',
                pad_inches=0)
    plt.close()


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
