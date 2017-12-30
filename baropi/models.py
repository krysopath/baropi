from sqlalchemy import Column, Integer, Float, String, TIMESTAMP, func, TIME
from .database import Base
from fractions import Fraction
from math import log10
import matplotlib.dates as mdates


__all__ = [
    'ClimateSample',
    'SentinelSample'
]


class DataModel:
    export_fields = ()

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def mdate(self):
        try:
            return mdates.date2num(self.timestamp)
        except AttributeError as ae:
            return None

    @property
    def fields_of_interest(self):
        fields = self.__table__.columns.keys() + list(self.export_fields)
        return fields

    @property
    def data(self):
        return {
            field: getattr(self, field) for field in self.fields_of_interest
        }

    @property
    def timestamp(self):
        try:
            return self.creation_time.timestamp()
        except AttributeError as ae:
            return None


class SentinelSample(Base, DataModel):
    __tablename__ = 'sentinel'
    id = Column(Integer, primary_key=True)
    temperature = Column(Float)
    total_ram = Column(Float)
    percent_ram = Column(Float)
    used_ram = Column(Float)
    free_ram = Column(Float)
    active_ram = Column(Float)
    inactive_ram = Column(Float)
    avail_ram = Column(Float)
    buffer = Column(Float)
    cached = Column(Float)
    shared = Column(Float)
    freq_current = Column(Float)
    freq_min = Column(Float)
    freq_max = Column(Float)
    disk_total = Column(Float)
    disk_used = Column(Float)
    disk_free = Column(Float)
    extra = Column(String(1024), server_default="")
    creation_time = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        unique=True
    )

    def __repr__(self):
        return "SentinelSample({})".format(self.timestamp)


class ClimateSample(Base, DataModel):
    __tablename__ = 'climate'
    id = Column(Integer, primary_key=True)
    temperature = Column(Float)
    humidity = Column(Float)
    creation_time = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        unique=True
    )
    extra = Column(String(1024), server_default="")

    __T_lteq_0 = Fraction(7.5), Fraction(237.3)
    __T_gt_0_thaw = Fraction(7.6), Fraction(240.7)
    __T_gt_0_freeze = Fraction(9.5), Fraction(265.5)
    __gas_constant = Fraction(8314.3)
    __molecular_weight_steam = Fraction(18.016)

    export_fields = (
        "mdate", "t_Kelvin",
        "moisture_gpm3",
        "dew_point_celsius",
        "steampressure_saturated_hPa",
        "steam_pressure_hPa"

    )

    def __init__(self, *args, **kwargs):
        DataModel.__init__(self, *args, **kwargs)

    @property
    def extra_fields(self):
        return []

    @extra_fields.setter
    def extra_fields(self, e):
        raise RuntimeError(e)

    def __repr__(self):
        return "ClimateSample({})".format(self.timestamp)

    def __str__(self):
        return "\n{}%, {}°C on {} UTC".format(
            self.humidity,
            self.temperature,
            self.timestamp,
        )

    @property
    def mdate(self):
        try:
            return mdates.date2num(self.timestamp)
        except AttributeError as ae:
            return None

    def choose_ab(self):
        if self.t_Celsius <= 0:
            return self.__T_lteq_0
        elif self.t_Celsius > 0:
            return self.__T_gt_0_thaw

    @property
    def a(self):
        return self.choose_ab()[0]

    @property
    def b(self):
        return self.choose_ab()[1]

    @property
    def t_Celsius(self):
        return self.temperature

    @property
    def t_Kelvin(self):
        return self.t_Celsius + Fraction(273.15)

    @property
    def r_percent(self):
        try:
            return self.humidity
        except Exception as e:
            raise e

    @property
    def r_computed(self):
        return 100 * self.steampressure_saturated_hPa / self.steampressure_saturated_hPa

    @property
    def moisture_gpm3(self):
        """absolute air moisture in g/m³"""
        return 10 ** 5 * self.__molecular_weight_steam / self.__gas_constant * self.steam_pressure_hPa / self.t_Kelvin

    @property
    def steampressure_saturated_hPa(self):
        return Fraction(6.1078) * 10 ** Fraction((self.a * self.t_Celsius) / (self.b + self.t_Celsius))

    @property
    def steam_pressure_hPa(self):
        return Fraction(
            self.r_percent / 100
        ) * self.steampressure_saturated_hPa

    @property
    def dew_point_celsius(self):
        def v():
            try:
                return Fraction(
                    log10(
                        self.steam_pressure_hPa / 6.1078
                    )
                )
            except ValueError as ve:
                return float("-inf")

        return float(self.b * v() / (self.a - v()))


class EventRequest(Base, DataModel):
    __tablename__ = 'event_requests'
    id = Column(Integer, primary_key=True)
    event_name = Column(
        String(1024), nullable=False, unique=False)
    location = Column(String(512), nullable=False)
    visitor_count = Column(Integer, nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    requester_name = Column(String(256), nullable=False)
    requester_email = Column(String(128), nullable=False)
    requester_phone = Column(String(128), nullable=False)
    extra = Column(String(1024), server_default="")
    creation_time = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        unique=True
    )
    export_fields = (
        'start', 'end'
    )

    def __repr__(self):
        return "EventRequest({})".format(self.timestamp)

    @property
    def start(self):
        return self.start_time.timestamp()

    @property
    def end(self):
        return self.end_time.timestamp()