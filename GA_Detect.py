from traffic.core import Traffic
from datetime import timedelta
import multiprocessing as mp
from OS_Airports import VABB
import OS_Data_Funcs as ODF
import OS_Funcs as OSF
import glob


def main(start_n):

    # Total number of aircraft seen
    tot_n_ac = 0

    # Of which go-arounds
    tot_n_ga = 0

    top_dir = '/gf2/eodg/SRP002_PROUD_ADSBREP/GO_AROUNDS/VABB/'
    # indir stores the opensky data
    indir = top_dir + 'INDATA/'

    files = glob.glob(indir+'*.pkl')
    files.sort()

    # A file to store info on go-arounds detected with each method
    ga_fid = open('/home/proud/Desktop/GA_Data.csv', 'w')
    ga_fid.write('ICAO24, Time, GAF1, GAF2, GAF3, GAF4, GAF5\n')

    fli_len = len(files)

    # Number of files to open in one go
    n_files_proc = 55

    pool_proc = 56

    f_data = []
    pool = mp.Pool(processes=pool_proc)

    for main_count in range(start_n, fli_len, n_files_proc):
        print("Processing batch starting with "
              + str(main_count + 1).zfill(5) + " of "
              + str(fli_len).zfill(5))
        p_list = []
        # First we load several files at once
        for j in range(0, n_files_proc):
            if (main_count+j < fli_len):
                p_list.append(pool.apply_async(ODF.get_flight,
                                               args=(files[main_count+j],)))

        for p in p_list:
            t_res = p.get()
            for fli in t_res:
                f_data.append(fli)
        if(len(f_data) < 1):
            continue
        traf_arr = Traffic.from_flights(f_data)
        p_list = []
        f_data = []
        if (len(traf_arr) == 1):
            end_time = traf_arr.end_time + timedelta(minutes=10)
            print("Extending timespan due to single aircraft")
        else:
            end_time = traf_arr.end_time

        # Now we process the results
        for flight in traf_arr:
            if (flight.stop + timedelta(minutes=5) < end_time):
                p_list.append(pool.apply_async(OSF.proc, args=(flight,
                                                               VABB.rwy_list,
                                                               False,)))
            else:
                f_data.append(flight)

        for p in p_list:
            t_res = p.get()
            if (t_res != -1):
                tot_n_ac += 1
                gafs = t_res[2:7]
                if any(gaf for gaf in gafs):
                    ga_fid.write(str(t_res[0]) + ',' +
                                 t_res[1].strftime("%Y%m%d %H:%M:%S") + ',' +
                                 str(t_res[2]) + ',' +
                                 str(t_res[3]) + ',' +
                                 str(t_res[4]) + ',' +
                                 str(t_res[5]) + ',' +
                                 str(t_res[6]) + '\n')
        print("\t-\tHave processed " + str(tot_n_ac) + " aircraft.")


# Use this to start processing from a given file number.
# Can be helpful if processing fails at some point.
init_num = 0

main(init_num)
