import airports.RWY as RWY

vabb_rwy_09 = RWY.rwy_data('09',
                   [80., 90., 90., 100.],
                   [19.088441, 72.849415],
                   [19.088789, 72.875840],
                   [19.088200, 72.821867])
                   
vabb_rwy_27 = RWY.rwy_data('27',
                   [-100., -90., -90., -80.],
                   [19.088789, 72.875840],
                   [19.088441, 72.849415],
                   [19.089381, 72.903396])

rwy_list = [vabb_rwy_09, vabb_rwy_27]

airport_name = 'Mumbai'
icao_name = 'VABB'
iata_name = 'BOM'
