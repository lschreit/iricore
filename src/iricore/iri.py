import os
from ctypes import *
from datetime import datetime
from typing import Iterable

import numpy as np
from numpy.ctypeslib import as_ctypes

cfd = os.path.dirname(os.path.abspath(__file__))
iri2016 = np.ctypeslib.load_library("libiri2016", cfd)
iri2020 = np.ctypeslib.load_library("libiri2020", cfd)

IRI_VERSIONS = ['16', '20']

def IRI(dt: datetime, alt_range: [float, float, float], lats: Iterable[float], lons: Iterable[float],
        replace_missing: float = np.nan, version=16) -> dict:
    if version == 16:
        iricore = iri2016
    elif version == 20:
        iricore = iri2020
    else:
        raise ValueError(f"Available IRI versions: " + ", ".join(IRI_VERSIONS))
    lats = np.asarray(lats)
    lons = np.asarray(lons)

    if not len(lats) == len(lons):
        raise ValueError("Lengths of latitude and longitude arrays must be equal.")

    jf = np.ones(50, dtype=np.int32, order="F")
    jf[[3, 4, 5, 11, 21, 22, 25, 27, 28, 29, 32, 33, 34, 35, 36]] = 0
    jmag = False
    iyyyy = c_int(dt.year)
    mmdd = c_int(100 * dt.month + dt.day)
    dhour = c_float(dt.hour + dt.minute / 60 + dt.second / 3600 + 25.)
    glat = as_ctypes(np.array(lats, dtype=np.float32, order="F"))
    glon = as_ctypes(np.array(lons, dtype=np.float32, order="F"))
    gsize = c_int(len(lats))
    heibeg = c_float(alt_range[0])
    heiend = c_float(alt_range[1])
    heistp = c_float(alt_range[2])
    oarr = np.zeros(100, dtype=np.float32, order="F")
    iri_res = np.zeros((20, 1000, len(lats)), dtype=np.float32, order='F')

    iricore.iricore_(as_ctypes(jf), byref(c_bool(jmag)), glat, glon, byref(gsize), byref(iyyyy), byref(mmdd),
                     byref(dhour), byref(heibeg), byref(heiend), byref(heistp), as_ctypes(oarr),
                     iri_res.ctypes.data_as(POINTER(c_float)))

    iri_res = np.ascontiguousarray(iri_res)
    ne = iri_res[0].transpose()
    te = iri_res[3].transpose()
    nalts = int((alt_range[1] - alt_range[0]) / alt_range[2]) + 1
    ne = ne.reshape((len(lats), -1))[:, :nalts]
    te = te.reshape((len(lats), -1))[:, :nalts]
    res = {
        'ne': np.where(ne < 0, replace_missing, ne),
        'te': np.where(te < 0, replace_missing, te),
    }
    return res