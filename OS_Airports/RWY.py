class rwy_data:
    ''' Defines a new runway for an airport. Takes the form:
    Name: Name of the runway, i.e: '01L'
    Mainhdg: Measured heading of the runway, often differs from the name
    Heading: Array of min/max values for aircraft heading: [ -11, 0, 0, 11]
             1st: Min heading, 2nd: Max heading for split
             3rd: Min heading for split, 4th: Max heading
             Split is necessary as some runways cross zero or 180 degrees,
             which makes calculations difficult.
    Rwy: Lat, lon of the runway threshold at the near end: [38.946, -77.474]
    Rwy2: Lat, lon of the runway threshold at the far end: [38.969, -77.474]
    Gate: Lat, lon of a checkpoint ~2.9km prior to the rwy: [38.920, -77.475]
    Then follows a series of numbers to define lines of best fit for approaches
    to a given runway. Each of these are a list containing 6 values for a
    polynomial fit: y = f0 * x^6 + f1 * x^5 ... f6
    '''
    def __init__(self, name, mainhdg, heading, rwy, rwy2, gate,
                 lons1, lonm, lonp1,
                 lats1, latm, latp1,
                 hdgs1, hdgm, hdgp1,
                 gals1, galm, galp1,
                 alts1, altm, altp1,
                 rocs1, rocm, rocp1):
                 
        self.name = name
        self.mainhdg = mainhdg
        self.heading = heading 
        self.rwy = rwy
        self.rwy2 = rwy2
        self.gate = gate
        self.lons1 = lons1
        self.lonm = lonm
        self.lonp1 = lonp1
        self.lats1 = lats1
        self.latm = latm
        self.latp1 = latp1
        self.hdgs1 = hdgs1
        self.hdgm = hdgm
        self.hdgp1 = hdgp1
        self.gals1 = gals1
        self.galm = galm
        self.galp1 = galp1
        self.alts1 = alts1
        self.altm = altm
        self.altp1 = altp1
        self.rocs1 = rocs1
        self.rocm = rocm
        self.rocp1 = rocp1

