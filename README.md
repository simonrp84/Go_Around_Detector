# Automatically detect aircraft go-arounds
This tool enables the automatic detection of go-around events in aircraft position data, and currently supports positions supplied from the `OpenSky network` interface. Multiprocessing is used to speed up the data throughput.

The tool will produce graphics showing the flight path and phase for every detected landing aircraft. Normal landings can be stored in one subdirectory, potential go-arounds in another.

Requires:
 Xavier Olive's `Traffic` library: https://github.com/xoolive/traffic
 
 Junzi Sun's `flight-data-processor` library: https://github.com/junzis/flight-data-processor

Usage:
First you must download aircraft data, which can be done using the `OpenSky_Get_Data` script. You can then point `GA_Detect` at the download location to scan for go-arounds.
This tool is in very early development, so has manual tweaks that would ideally be changeable via a config file or directly via the command line call. The most important of these tweaks are listed below:

### `OpenSky_Get_Data.py`:

Use the script's `--outdir` option so the the output directory. This defaults to `INDATA` in your current working directory.

Use `--n-jobs` to specify the number of concurrent retrievals from the OpenSky database. I have found that six works well, but this may be different for you.

The airport region to retrieve data for is specified with the `--airport` option.  The default is `VABB`, which will import Mumbai airport (VABB). You should create your own airport definition in the `./airports` directory.

The border region around the airport is manually specified (as `0.45 deg`) in `get_bounds()`. You may wish to change this.

Running the script without parameters defaults to downloading data for
the ``VABB`` airport between 2019-08-10 and 2019-08-21 and saving that
data into the `INDATA` directory in your working directory.  Thus,
these two calls are equivalent:

```bash
python OpenSky_Get_Data.py  # does the same thing as the next command:
python OpenSky_Get_Data.py \
    --airport=VABB --start-dt=2019-08-10 --end-dt=2019-08-21 \
    --outdir=INDATA --n-jobs=1
```

### In `GA_Detect.py`
The directory structure is set at the beginning of `main()`. You will probably want to adjust this to your own requirements.

`n_files_proc` specifies how many files to process simultaneously. This should be changed to the optimal value for your hardware.

`pool_proc` specifies the number of multiprocessing threads to use. I have found that this can be set slightly higher than the number of cores available, as cores are not fully utilised anyway.
