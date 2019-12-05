"""Some constants to use during go-around detection.

These may need to be tuned to suit individual airports and/or situations.
"""
# The threshold altitude used to determine if a go-around occurred,
# check if points in a given time window (below) after a state change
# are above this altitude
alt_thresh = 500.

# The threshold vertical rate used to determine if a go-around occurred,
# check if points in a given time window (below) after a state change
# contain vertical rates above this threshold
vrt_thresh = 200.

# This sets a time in the future to check, to ensure the aircraft
# is actually going around and not landing (sometimes status changes
# from 'descent' to 'level' rather than 'ground' for a landing
ga_tcheck = 120.


# Takeoff threshold
takeoff_thresh_alt = 600.


# The gate maximum altitude for landing, flights above this are not
# considered for a given runway
gate_alt = 4000


# The rate of climb threshold for the gate, flights greater than this
# are not considered for a given runway
gate_roc = 150


# The threshold distance between the aircraft and the gate, aircraft
# further than this are not considered for a given runway
gate_dist = 1. / 112.


# The threshold altitude for the state change, if change occurs above
# this altitude then it's probably not a go-around
ga_st_alt_t = 2500.


# This is a list of icao24 addresses to exclude, for example general
# aviation aircraft or helicopters.
exclude_list = ['800b7b', '800b7c', '800b7d', '800d5f', '800b87', ]


# This variable allows you to select a single callsign to process
# To keep all aircraft use '', otherwise enter your own, i.e: 'IGO366'
search_call = ''
