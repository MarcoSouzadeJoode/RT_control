
# Standard libraries
import datetime
import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate


# astropy, astroquery methods
from astroquery.jplhorizons import Horizons
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy import units as u
from astropy.time import Time
import astropy


class Ephemeris:
    def __init__(self, name, start, stop, solar_system=False, solar_system_id_type="majorbody", precision=4000):
        self.name = name
        self.start = start
        self.stop = stop
        self.solar_system = solar_system

        self.dt = datetime.timedelta(seconds=1)
        self.start_datetime = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
        self.end_datetime = datetime.datetime.strptime(self.stop, "%Y-%m-%d %H:%M:%S")

        self.duration = (self.end_datetime - self.start_datetime).total_seconds()

        # the precision value (N) is relevant for the Horzions query,
        # which will return N lines of ephemeris between start and end times.

        # you can change the precision value
        # 5000 seems to be the upper limit,
        # and 4000 takes ~ 10 seconds to download

        # there also exist an limit on smallest step size
        # step_size_min = 0.5s.

        self.precision = precision

        if self.precision > self.duration:
            self.precision = int(self.duration)

        # coordinates for RT2 telescope for manual conversion of coordinates from Ra, Dec -> Az El
        self.location = EarthLocation(lat=49.90859805061835 * u.deg, lon=14.779752713599184 * u.deg, height=512 * u.m)

        # location_code for Ondrejov observatory, used in the Horizons query
        self.location_code = "557"

        self.solar_system_id_type = solar_system_id_type

        # generate time based on database requirements
        self.ut_time, self.internal_time = self._time_generation()

        if self.solar_system:
            self.AZ, self.EL = self.jpl_horizons()
        else:
            self.AZ, self.EL = self.simbad()

        self.generate_output_file()

    def _time_generation(self):
        """
        Simbad and JPL horizons require different datetime handling.
        this method distinguishes between internal_time (used for database queries)
        and ut_time, used in the output files.
        """

        time_list = []
        _t = self.start_datetime
        while _t != self.end_datetime:
            time_list.append(_t)
            _t += self.dt

        # a np array with datetime.datetime objects
        _ut_time = np.array(time_list)

        if self.solar_system:
            # generate time dictionary for JPL Horizons
            _internal_time = {"start": self.start, "stop": self.stop, "step": str(self.precision)}
        else:
            # SIMBAD requires astropy.time.core.Time object
            _internal_time = Time(_ut_time)

        return _ut_time, _internal_time

    def simbad(self):
        """
        method for searching in the SIMBAD catalogue (fixed stars and deep sky objects)
        requires:
        * an astropy.time.core.Time object (time series)
        * a recognisable name.

        Returns a tuple of az, el arrays of same dimension as self.ut_time
        """

        # search SIMBAD for name
        try:
            # this branch will try searching in the database,
            # if not found, will report error.

            _dso = SkyCoord.from_name(self.name)

            print("Name resolved")
            print(_dso.ra.to_string(decimal=True), _dso.dec.to_string(decimal=True))

            # _coordinates is quite a complex object, containing information about time,
            # location, AzEl, (pressure, temperature...)

            _coordinates = _dso.transform_to(AltAz(obstime=self.internal_time, location=self.location))

            # formatting
            _az = _coordinates.az.to_string(decimal=True).astype("float")
            _el = _coordinates.alt.to_string(decimal=True).astype("float")

            # returning tuple of arrays, their size is
            return _az, _el

        except astropy.coordinates.name_resolve.NameResolveError:
            print("Name not resolved")

        except:
            print("A different error occured")

    def jpl_horizons(self):
        """A method for searching in the JPL Horizons catalogue.
        Used for solar system bodies.
        Returns tuple of az, el coordinate arrays
        """

        _observation = Horizons(id=self.name, location=self.location_code, epochs=self.internal_time,
                                id_type=self.solar_system_id_type)

        _ephemeris = _observation.ephemerides()

        # we shall be interpolating the Az El values, because it is the simplest solution
        # and does not impact precision
        def horizons_interpolation(time_input_axis, coord, time_output_axis):
            f = scipy.interpolate.interp1d(time_input_axis, coord)
            return f(time_output_axis)

        _julian_start, _julian_stop = _ephemeris["datetime_jd"][0], _ephemeris["datetime_jd"][-1]

        # as we can download only a limited number of ephemeris, we have to interpolate
        # denser time axis is a np linear space of size of int(duration).

        _denser_time_axis = np.linspace(_julian_start, _julian_stop, int(self.duration))
        _interpolated_az = horizons_interpolation(_ephemeris["datetime_jd"], _ephemeris["EL"], _denser_time_axis)
        _interpolated_el = horizons_interpolation(_ephemeris["datetime_jd"], _ephemeris["AZ"], _denser_time_axis)

        return _interpolated_az, _interpolated_el

    def generate_output_file(self):
        # starting date string, used for file name
        start_string = self.start_datetime.strftime("%Y-%m-%d_%H:%M:%S")

        #defining output file name
        output_file_name = f"{self.name}_{start_string}.txt"

        with open(output_file_name, "w+") as output_file:
            # using ut_time (datetime) in each line, NOT internal time
            for index, t in enumerate(self.ut_time):
                output_file.write(f"{t} {self.AZ[index]} {self.EL[index]}\n")


Cassiopeia = Ephemeris(name="Cas A", start="2021-07-13 08:40:00", stop="2021-07-13 9:00:00")
Jupiter = Ephemeris(name="Sun", start="2021-07-13 08:40:00", stop="2021-07-13 9:00:00", solar_system=True)