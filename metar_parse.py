from datetime import datetime
from metar import Metar
import pytz


class metobs:
    '''
    A class to store METAR observations:
    temp = temperature in C
    dewp = dewpoint in C
    w_s = wind speed in kts
    w_d = wind direction in deg
    w_g = wind gusts in kts
    cb = boolean specifying CBs near airport
    vis = visibility in km
    pres = pressure in hPa
    '''
    def __init__(self, temp, dewp, w_s, w_d, w_g, cb, vis, pres):
        self.temp = temp
        self.dewp = dewp
        self.w_s = w_s
        self.w_d = w_d
        self.w_g = w_g
        self.cb = cb
        self.vis = vis
        self.pres = pres


def get_metars(inf):
    '''
    A function to parse metars from a file and convert into a
    dict of metobs objets
    Input:
        -   inf: The input file (as a string filename)
    Output:
        -   a dict of metobs read from the file
    '''
    fid = open(inf, 'r')

    met_dict = {}

    for line in fid:
        data = line.rstrip('\n').split(',')
        metdate = datetime.strptime(data[1], '%Y-%m-%d %H:%M')
        metdate = metdate.replace(tzinfo=pytz.UTC)
        mettxt = data[2]
        obs = Metar.Metar(mettxt, strict=False)
        obs.time = metdate
        try:
            temp = obs.temp.value()
        except:
            temp = 15
        try:
            dewp = obs.temp.value()
        except:
            dewp = 10
        try:
            w_s = obs.wind_speed.value()
        except:
            w_s = 0
        try:
            w_g = obs.wind_gust.value()
        except:
            w_g = 0
        try:
            w_d = obs.wind_dir.value()
        except:
            w_d = 0
        try:
            press = obs.press.value()
        except:
            press = 1013.25
        try:
            vis = obs.vis.value()
        except:
            vis = 10000

        cb = False
        try:
            for wx in obs.sky:
                if (wx[2] == "CB"):
                    cb = True
        except:
            None

        cur_obs = metobs(temp, dewp, w_s, w_d, w_g, cb, vis, press)

        met_dict[metdate] = cur_obs

    return met_dict
