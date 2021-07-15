
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

import socket
import threading

# SERVER

PORT = 6060
# first message to the server is 64 bytes long
HEADER = 64
FORMAT = "utf-8"

# on my device, this returns "marco-Aspire-V3-772"
SERVER_NAME = socket.gethostname()
SERVER = socket.gethostbyname(SERVER_NAME)
print(f"Server {SERVER}, Server name: {SERVER_NAME}")

ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)





class Ephemeris:
    """
    A class for generating:
        * Az, El ephemeris files for solar system objects
        * Ra, Dec values for deep sky objects

    Parameters:
        * name (string): recognisable by SIMBAD or JPL Horizons,
        * start (string): in the "%Y-%m-%d %H:%M:%S" format
        * stop (string): in the same format
        * solar_system (bool): is the object a solar system object?
        * solar_system_id_type (string): is it a "majorbody" or a "minorbody"?
        * precision (int): number of requested lines for the Horizons query

    Returns:
         * "%Y-%m-%d %H:%M:%S AZ EL\n" containing file for SSOs,
         * internal time, RA, DEC for DSOs for later conversion.
    """
    def __init__(self, name, start, stop, solar_system=False, solar_system_id_type="majorbody"):
        self.name = name
        self.start = start
        self.stop = stop
        self.solar_system = solar_system

        self.generated_file = False

        self.dt = datetime.timedelta(seconds=1)
        self.start_datetime = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
        self.end_datetime = datetime.datetime.strptime(self.stop, "%Y-%m-%d %H:%M:%S")

        self.duration = (self.end_datetime - self.start_datetime).total_seconds()
        print(self.duration)
        if self.duration <= 0:
            print("Duration of selected interval is negative. Please choose again.\n"
                  "the program will not continue with any calculations.")
        else:
            # the precision value (N) is relevant for the Horzions query,
            # which will return N lines of ephemeris between start and end times.

            # you can change the precision value
            # 5000 seems to be the upper limit,
            # and 4000 takes ~ 10 seconds to download

            # there also exist an limit on smallest step size
            # step_size_min = 0.5s.

            self.precision = 4000

            if self.precision > self.duration > 0:
                self.precision = int(self.duration)

            # location_code for Ondrejov observatory, used in the Horizons query
            self.location_code = "557"

            # major or minor body!
            self.solar_system_id_type = solar_system_id_type

            # generate time based on database requirements
            self.ut_time, self.internal_time = self._time_generation()

            if self.solar_system:
                self.AZ, self.EL = self.jpl_horizons()
                self.outfilename = self.generate_output_file()
            else:
                self.RA, self.DEC = self.simbad()

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
        A method for searching in the SIMBAD catalogue (fixed stars and deep sky objects).

        Parameters (contained in self):
            * an astropy.time.core.Time object (time series)
            * a recognisable name.

        Returns:
            * tuple of (RA, DEC) coordinates
        """
        print("Simbad branch.")

        # search SIMBAD for name
        try:
            # this branch will try searching in the database,
            # if not found, will report error.

            _dso = SkyCoord.from_name(self.name)
            _ra, _dec = _dso.ra.to_string(decimal=True), _dso.dec.to_string(decimal=True)

            print(f"Name resolved: {self.name}")
            print(_ra, _dec)

            return _ra, _dec

        except astropy.coordinates.name_resolve.NameResolveError:
            print("Name not resolved")

    def jpl_horizons(self):
        """A method for searching in the JPL Horizons catalogue.
        Used for solar system bodies.
        Returns tuple of az, el coordinate arrays
        """
        print("JPL Horizons branch")

        id_types = ["majorbody", "smallbody", "designation", "name", "asteroid_name", "comet_name"]

        for id_type in id_types:
            try:
                planet_id_dict = {"mercury": 199, "venus": 299, "moon": 301, "mars": 499, "jupiter": 599, "saturn": 699,
                                  "uranus": 799, "neptune": 899}

                if self.name.lower() in planet_id_dict.keys():
                    planet_id = planet_id_dict[self.name.lower()]
                    _observation = Horizons(id=planet_id, location=self.location_code, epochs=self.internal_time, id_type=id_type)
                else:
                    _observation = Horizons(id=self.name, location=self.location_code, epochs=self.internal_time,
                                            id_type=id_type)
                break
            except ValueError:
                print(f"Selected body is not of id_type {id_type}")

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

        # defining output file name
        output_file_name = f"{self.name}_{start_string}.txt"

        with open(output_file_name, "w+") as output_file:
            # using ut_time (datetime) in each line, NOT internal time
            for index, t in enumerate(self.ut_time):
                output_file.write(f"{t} {self.AZ[index]} {self.EL[index]}\n")

            self.generated_file = True
            return output_file_name


class Conversion:
    """
    A class for converting from RA, DEC + t-> AZ, EL (t)
    Parameters:
        * RA: right ascension in decimal degrees (not 17h58m80s but a number like 237.8799)
        * DEC: declination in decimal degrees (not 50°30'45" but a number like 15.37955)
        * times: times as the Astropy.time.core.Time objects, in an np.array()
    Returns:
        * file containing ephemeris as "YYYY-mm-dd HH:MM:SS AZ EL\n"
    """
    def __init__(self, RA, DEC, start, stop, name=None):

        # in ICRS reference frame
        self.RA = RA
        self.DEC = DEC

        self.generated_file = False

        self.dt = datetime.timedelta(seconds=1)
        self.start_datetime = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        self.end_datetime = datetime.datetime.strptime(stop, "%Y-%m-%d %H:%M:%S")

        self.duration = (self.end_datetime - self.start_datetime).total_seconds()
        print(self.duration)

        if self.duration <= 0:
            print("Duration is smaller than 0.")
        else:
            time_list = []
            _t = self.start_datetime
            while _t != self.end_datetime:
                time_list.append(_t)
                _t += self.dt

            # a np array with datetime.datetime objects
            self.ut_time = np.array(time_list)
            self.internal_time = Time(self.ut_time)

            if name:
                self.name = name
            else:
                self.name = str(RA) + "_" + str(DEC)

            # SkyCoord object, defaults to ICRS
            self.DSO = SkyCoord(RA, DEC, unit="deg")

            # coordinates for RT2 telescope for manual conversion of coordinates from Ra, Dec -> Az El
            self.location = EarthLocation(lat=49.90859805061835 * u.deg, lon=14.779752713599184 * u.deg, height=512 * u.m)


            self.AZ, self.EL = self.convert()
            self.outfilename = self.generate_output_file()

    def convert(self):
        """Transforming coordinates using the SkyCoord package."""
        _coordinates = self.DSO.transform_to(AltAz(obstime=self.internal_time, location=self.location))
        _az = _coordinates.az.to_string(decimal=True).astype("float")
        _el = _coordinates.alt.to_string(decimal=True).astype("float")
        return _az, _el

    def generate_output_file(self):
        # starting date string, used for file name
        start_string = str(self.ut_time[0])
        print(start_string)

        # defining output file name
        output_file_name = f"{self.name}_{start_string}.txt"

        with open(output_file_name, "w+") as output_file:
            # using ut_time (datetime) in each line, NOT internal time
            for index, t in enumerate(self.ut_time):
                output_file.write(f"{t} {self.AZ[index]} {self.EL[index]}\n")
            self.generated_file = True
            return output_file_name


# TODO: transfer RA, DEC from search tool in Ephemeris object to Conversion object
# TODO: start thinking about socket communication
# TODO: mechanism for deciding if SSO is a major or minor body
# TODO: --

# Jupiter = Ephemeris(name="Jupiter Barycenter", start="2021-07-13 08:40:00",
#                     stop="2021-07-13 9:00:00", solar_system=True)

#Quasar = Ephemeris(name="3C273", start="2021-07-13 08:40:00", stop="2021-07-13 9:00:00")
#Vega = Conversion(280, 38, start="2021-07-13 08:40:00", stop="2021-07-13 9:00:00", name="Vega")

DSO = Ephemeris(name="Cyg A", start="2021-07-14 08:40:00", stop="2021-07-14 9:00:00", solar_system=False)
DSOConverter = Conversion(DSO.RA, DSO.DEC, start="2021-07-14 08:40:00", stop="2021-07-21 9:00:00", name="CygALong")


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)

            if msg == DISCONNECT_MESSAGE:
                connected = False

            print(f"SIGNED MESSAGE: [{addr}] : {msg}")

            results = message_parsing(msg)
            print(results)
    conn.close()


def message_parsing(msg):
    parts = msg.split("\n")
    request_type = parts[0]

    if request_type == "resolve_request":
        solar_system_b = parts[4] == "True"
        EPH = Ephemeris(name=parts[1], start=parts[2], stop=parts[3], solar_system=solar_system_b)
        if solar_system_b:
            if EPH.generated_file:
                return f"output file generated\n{EPH.outfilename}"
            else:
                return "file generation failed"
        else:
            return f"coordinates solved\n{EPH.RA}\n{EPH.DEC}"

    if request_type == "pushing_ra_dec":
        CNV = Conversion(RA=float(parts[1]), DEC=float(parts[2]), start=parts[3], stop=parts[4], name=parts[5])
        if CNV.generated_file:
            return f"output file generated\n{CNV.outfilename}"
        else:
            return "file generation failed"


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    server.send(send_length)
    server.send(message)


#print("[STARTING] server is starting")
#start()
