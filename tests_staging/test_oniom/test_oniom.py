#!/usr/bin/env python3

import numpy as np

from pysisyphus.calculators.ONIOM import ONIOM
from pysisyphus.helpers import geom_from_library, geom_from_xyz_file
from pysisyphus.optimizers.RFOptimizer import RFOptimizer


def test_acetaldehyd():
    calc_dict = {
        "high": {
            "type": "g16",
            "route": "b3lyp d95v",
            "pal": 4,
        },
        "low": {
            "type": "g16",
            "route": "hf sto-3g",
            "pal": 4,
        },
    }
    high_inds = (4,5,6)
    oniom = ONIOM(calc_dict, high_inds)

    geom = geom_from_library("acetaldehyd_oniom.xyz", coord_type="redund")
    geom.set_calculator(oniom)

    forces = geom.forces.reshape(-1, 3) # internal forces...
    forces = geom._forces.reshape(-1, 3)
    energy = geom.energy

    # print("energy")
    # print(f"{energy:.8f}")

    forces_str = np.array2string(forces, formatter={"float": lambda f: f"{f: .8f}",})
    # print("forces")
    # print(forces_str)

    from pysisyphus.optimizers.RFOptimizer import RFOptimizer
    rfo = RFOptimizer(geom, trust_max=.3, dump=True, thresh="gau")
    rfo.run()


def test_acetaldehyd_psi4_xtb():
    calc_dict = {
        "high": {
            "type": "pypsi4",
            "method": "scf",
            "basis": "sto-3g",
        },
        "low": {
            "type": "pyxtb",
        },
    }
    high_inds = (4,5,6)
    oniom = ONIOM(calc_dict, high_inds)

    geom = geom_from_library("acetaldehyd_oniom.xyz", coord_type="redund")
    geom.set_calculator(oniom)

    from pysisyphus.optimizers.RFOptimizer import RFOptimizer
    rfo = RFOptimizer(geom, trust_max=.3, dump=True, thresh="gau", line_search=True)
    rfo.run()


def test_oniomext():
    from pysisyphus.calculators.ONIOMext import ONIOMext
    geom = geom_from_library("alkyl17_sto3g_opt.xyz")

    real = set(range(len(geom.atoms)))
    medmin = set((0,1,2,3,4,5,6, 46,47,48,49,50,51,52))
    med = list(real - medmin)
    h1 = list(range(13, 22))
    h2 = list(range(31, 40))

    calcs = {
        "real": {
            "route": "HF/STO-3G",
        },
        "medium": {
            "route": "HF/3-21G",
        },
        "high1": {
            "route": "HF/6-31G",
        },
        "high2": {
            "route": "HF/6-311G",
        },
    }
    for key, calc in calcs.items():
        calc["type"] = "g16"
        calc["pal"] = 2
        calc["mult"] = 1
        calc["charge"] = 0

    models = {
        "med" : {
            # "inds": (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14),
            "inds": med,
            "calc": "medium",
        },
        "h1": {
            # "inds": (4, 5, 6),
            "inds": h1,
            "calc": "high1",
        },
        "h2": {
            # "inds": (10, 11, 12),
            "inds": h2,
            "calc": "high2",
        }
    }

    layers = ["low", "medium", ["high1", "high2"]]

    oniom = ONIOMext(calcs, models, layers, geom)

    assert oniom.layer_num == 3
    # assert len(oniom.calculators) == 7


def test_biaryl_solvated():
    calc_dict = {
        "high": {
            "type": "g16",
            "route": "pm6",
            "pal": 4,
        },
        "low": {
            "type": "xtb",
            "pal": 4,
        },
    }
    high_inds = list(range(30))
    oniom = ONIOM(calc_dict, high_inds)

    geom = geom_from_xyz_file("bare_solvated.xyz")
    geom.set_calculator(oniom)

    opt_kwargs = {
        # "trust_max": .3,
        "dump": True,
        # "thresh": "gau",
        "prefix": "pm6_biaryl_",
        "max_cycles": 200,
    }
    rfo = RFOptimizer(geom, **opt_kwargs)
    rfo.run()


if __name__ == "__main__":
    # test_acetaldehyd()
    test_oniomext()
    # test_acetaldehyd_psi4_xtb()
    # test_biaryl_solvated()
