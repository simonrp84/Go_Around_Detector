class rwy_data:
    ''' Defines a new runway for an airport. Takes the form:
    Name: Name of the runway, i.e: '01L'
    Heading: Array of min/max values for aircraft heading: [ -11, 0, 0, 11]
             1st: Min heading, 2nd: Max heading for split
             3rd: Min heading for split, 4th: Max heading
             Split is necessary as some runways cross zero or 180 degrees,
             which makes calculations difficult.
    Rwy: Lat, lon of the runway threshold at the near end: [38.946, -77.474]
    Rwy2: Lat, lon of the runway threshold at the far end: [38.969, -77.474]
    Gate: Lat, lon of a checkpoint ~2.9km prior to the rwy: [38.920, -77.475]
    '''
    def __init__(self, name, heading, rwy, rwy2, gate):
        self.name = name
        self.heading = heading 
        self.rwy = rwy
        self.rwy2 = rwy2
        self.gate = gate

