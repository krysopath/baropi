#!/usr/bin/env python3
# coding=utf-8

# !/usr/bin/env python3
# coding=utf-8
from sys import argv
from fractions import Fraction
from math import log10, isinf

"""
Beschreibung:

Die Luft ist ein Gemisch verschiedener Gase. Eines dieser Gase ist der Wasserdampf.
Die Menge an Wasserdampf, die in der Luft enthalten sein kann, ist allerdings begrenzt.
Je wärmer die Luft ist, desto mehr Wasserdampf kann in ihr enthalten sein.

Die relative Luftfeuchtigkeit gibt an, wie viel Prozent des maximalen Wasserdampfgehaltes
die Luft im Augenblick enthält. Da der maximale Wasserdampfgehalt mit steigender Temperatur ansteigt,
fällt die relative Luftfeuchtigkeit mit steigender Temperatur (und umgekehrt).

Die dew_point_celsius ist definiert als die Temperatur, bei der der aktuelle Wasserdampfgehalt
in der Luft der maximale (100% relative Luftfeuchtigkeit) ist. Die dew_point_celsius ist
damit eine von der aktuellen Temperatur unabhängige Größe.
Eine Möglichkeit die dew_point_celsius zu messen ist das Abkühlen von Metall bis sich
die Oberfläche mit Wasserdampf beschlägt. Dann ist die Temperatur des Metalls die dew_point_celsius.

Es gibt keine exakten Formel zur Umrechnung der dew_point_celsius in die relative
Luftfeuchtigkeit. Zur Erstellung meines Taupunktrechners habe ich eine einfache Näherungsformel benutzt.
Eine exakte Umrechnung ist nur mit experimentell ermittelten Tabellen möglich.

Aus Temperatur und relativer Luftfeuchte bzw. Temperatur und Taupunkt lässt sich auch
der absolute Feuchtegehalt der Luft in Gramm Wasserdampf pro Kubikmeter ausrechnen.
Formeln:

Die Grundlage der Berechnungen ist die Näherungsformel für den Sättigungsdampfdruck ( Gleichung 1 ),
die sogenannte Magnusformel. Die relative Luftfeuchtigkeit ist definiert als das Verhältnis
vom augenblicklichen Dampfdruck zum Sättigungsdampfdruck (umgeformte Gleichung 2). Bei
der dew_point_celsius ist definitionsgemäß der Sättigungsdampfdruck gleich dem aktuellen Dampfdruck.
Aus diesen beiden Definitionen folgt unmittelbar Gleichung 3, die Formel zur Berechnung
der relativen Luftfeuchtigkeit aus der dew_point_celsius. Die 4. Gleichung beschreibt
umgekehrt die Berechnung der dew_point_celsius aus der relativen Luftfeuchtigkeit und der
aktuellen Temperatur. Diese 4. Gleichung ist im Grunde nichts anderes als die nach t_Celsius
aufgelöste 1. Gleichung , wobei für den Sättigungsdampfdruck der aktuelle Dampfdruck
(und nicht der aktuelle Sättigungsdampfdruck) eingesetzt wird, so dass die dew_point_celsius
und nicht die normale Temperatur als Ergebnis herauskommt. Aus der allgemeinen Gasgleichung
ergibt sich die 5. Gleichung .

Bezeichnungen:
r_percent = relative Luftfeuchte
t_Celsius = Temperatur in °C
t_Kelvin = Temperatur in Kelvin (t_Kelvin = t_Celsius + 273.15)
TD = dew_point_celsius in °C
DD = Dampfdruck in hPa
SDD = Sättigungsdampfdruck in hPa

Parameter:
a = 7.5, b = 237.3 für t_Celsius >= 0
a = 7.6, b = 240.7 für t_Celsius < 0 über Wasser (Taupunkt)
a = 9.5, b = 265.5 für t_Celsius < 0 über Eis (Frostpunkt)

R* = 8314.3 J/(kmol*K) (universelle Gaskonstante)
mw = 18.016 kg/kmol (Molekulargewicht des Wasserdampfes)
moisture_gpm3 = absolute Feuchte in g Wasserdampf pro m3 Luft

Formeln:

    SDD(t_Celsius) = 6.1078 * 10^((a*t_Celsius)/(b+t_Celsius))
    DD(r_percent,t_Celsius) = r_percent/100 * SDD(t_Celsius)
    r_percent(t_Celsius,TD) = 100 * SDD(TD) / SDD(t_Celsius)
    TD(r_percent,t_Celsius) = b*v/(a-v) mit v(r_percent,t_Celsius) = log10(DD(r_percent,t_Celsius)/6.1078)

    moisture_gpm3(r_percent,t_Kelvin) = 10^5 * mw/R* * DD(r_percent,t_Celsius)/t_Kelvin; moisture_gpm3(TD,t_Kelvin) = 10^5 * mw/R* * SDD(TD)/t_Kelvin

"""


class Moullier:
    __T_lteq_0 = Fraction(7.5), Fraction(237.3)
    __T_gt_0_thaw = Fraction(7.6), Fraction(240.7)
    __T_gt_0_freeze = Fraction(9.5), Fraction(265.5)
    __gas_constant = Fraction(8314.3)
    __molecular_weight_steam = Fraction(18.016)

    def __init__(self, T, r, *args, **kwargs):
        self._r = r
        self._T = T

    def __repr__(self):
        return """
Kelvin: {} °K
Sättigungsdampfdruck: {} hPa
Dampfdruck: {} hPa
dew_point_celsius: {} °C
relative: {} %
absolute: {} g/m³""".format(
            float(self.TK),
            float(self.Saettigungsdampfdruck_hPa),
            float(self.Dampfdruck_hPa),
            float(self.Taupunkttemperatur),
            self.r,
            self.AF
        )

    def choose_ab(self):
        if self.T <= 0:
            return self.__T_lteq_0
        elif self.T > 0:
            return self.__T_gt_0_thaw

    @property
    def a(self):
        return self.choose_ab()[0]

    @property
    def b(self):
        return self.choose_ab()[1]

    @property
    def T(self):
        return self._T

    @property
    def TK(self):
        return self.T + Fraction(273.15)

    @T.setter
    def T(self, x):
        if -20 <= x <= 60:
            self._T = Fraction(x)
        else:
            raise ValueError("constraint: -20 <= t_Celsius <= 60")

    @property
    def r(self):
        try:
            return self._r
        except Exception as e:
            raise e
            return 100 * self.steampressure_saturated_hPa / self.steampressure_saturated_hPa

    @r.setter
    def r(self, x):
        if 0 <= x <= 100:
            self._r = Fraction(x)
        else:
            raise ValueError("constraint: 0 <= t_Celsius <= 100")

    @property
    def AF(self):
        try:
            return 10 ** 5 * self.__molecular_weight_steam / self.__gas_constant * self.Dampfdruck_hPa / self.TK
            # return 10**5 * self.__molecular_weight_steam / self.__gas_constant * self.steampressure_saturated_hPa/self.t_Kelvin
        except Exception as e:
            raise e

    @property
    def Saettigungsdampfdruck_hPa(self):
        return Fraction(6.1078) * 10 ** Fraction((self.a * self.T) / (self.b + self.T))

    @property
    def Dampfdruck_hPa(self):
        return Fraction(
            self.r / 100
        ) * self.Saettigungsdampfdruck_hPa

    @property
    def Taupunkttemperatur(self):
        def v():
            try:
                return Fraction(
                    log10(
                        self.Dampfdruck_hPa / 6.1078
                    )
                )
            except ValueError as ve:
                return float("-inf")

        return self.b * v() / (self.a - v())


if __name__ == "__main__":
    m = Moullier(25, 60)

    print("a:", float(m.a), "b:", float(m.b), "t_Celsius:", m.T, "r_percent:", m.r)
    print(m)
