"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import arrow.arrow


class TimeStamp(arrow.arrow.Arrow):
    def __sub__(self, other):
        if isinstance(other, TimeDelta):
            return self.clone().replace(years=-other.years,
                                        months=-other.months,
                                        days=-other.days,
                                        hours=-other.hours,
                                        minutes=-other.minutes,
                                        seconds=-other.seconds,
                                        microseconds=-other.microseconds)
        elif isinstance(other, TimeStamp):
            return TimeDelta(years=self.year-other.year,
                             months=self.month-other.month,
                             days=self.day-other.day,
                             hours=self.hour-other.hour,
                             minutes=self.minute-other.minute,
                             seconds=self.second-other.second,
                             microseconds=self.microsecond-other.microsecond)
        else:
            raise NotImplementedError

    def __add__(self, other):
        if isinstance(other, TimeDelta):
            return self.clone().replace(years=other.years,
                                        months=other.months,
                                        days=other.days,
                                        hours=other.hours,
                                        minutes=other.minutes,
                                        seconds=other.seconds,
                                        microseconds=other.microseconds)
        elif isinstance(other, TimeStamp):
            # return self.clone().replace(years=other.year,
            #                             months=other.month,
            #                             days=other.day,
            #                             hours=other.hour,
            #                             minutes=other.minute,
            #                             seconds=other.second,
            #                             microseconds=other.microsecond)
            raise ValueError
        else:
            raise NotImplementedError


class TimeDelta(object):
    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds

    def __sub__(self, other):
        if isinstance(other, TimeDelta):
            return TimeDelta(years=self.years - other.years,
                             months=self.months - other.months,
                             days=self.days - other.days,
                             hours=self.hours - other.hours,
                             minutes=self.minutes - other.minutes,
                             seconds=self.seconds - other.seconds,
                             microseconds=self.microseconds - other.microseconds)
        else:
            raise NotImplementedError

    def __add__(self, other):
        if isinstance(other, TimeDelta):
            return TimeDelta(years=self.years + other.years,
                             months=self.months + other.months,
                             days=self.days + other.days,
                             hours=self.hours + other.hours,
                             minutes=self.minutes + other.minutes,
                             seconds=self.seconds + other.seconds,
                             microseconds=self.microseconds + other.microseconds)
        else:
            raise NotImplementedError

    def __repr__(self):
        return ':'.join([str(self.years), str(self.months), str(self.days),
                         str(self.hours), str(self.minutes), str(self.seconds),
                         str(self.microseconds)])


timestamp_factory = arrow.ArrowFactory(TimeStamp)
