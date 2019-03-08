#!/usr/bin/env python3

from pathlib import Path
import os

import cloudpickle
from natsort import natsorted
import numpy as np

from pysisyphus.calculators.Gaussian16 import Gaussian16
from pysisyphus.helpers import geom_from_xyz_file
from pysisyphus.Geometry import Geometry
from pysisyphus.helpers import geom_from_library
from pysisyphus.tsoptimizers.dimer import dimer_method


def run():
    np.random.seed(20180325)
    xyz_path = Path("/scratch/Code/parsezmat/")
    xyzs = natsorted(xyz_path.glob("*.xyz"))
    geoms = [geom_from_xyz_file(fn) for fn in xyzs]
    baker_dict = {
        "01_hcn.xyz" : (0, 1, -92.24604),
        "02_hcch.xyz": (0, 1, -76.29343),
        "03_h2co.xyz": (0, 1, -113.05003),
        "04_ch3o.xyz": (0, 2, -113.69365),
        "05_cyclopropyl.xyz": (0, 2, -115.72100),
        "06_bicyclobutane.xyz": (0, 1, -153.90494),
        "07_bicyclobutane.xyz": (0, 1, -153.89754),
        "08_formyloxyethyl.xyz": (0, 2, -264.64757),
        "09_parentdieslalder.xyz": (0, 1, -231.60321),
        "10_tetrazine.xyz": (0, 1, -292.81026),
        "11_trans_butadiene.xyz": (0, 1, -154.05046),
        "12_ethane_h2_abstraction.xyz": (0, 1, -78.54323),
        "13_hf_abstraction.xyz": (0, 1, -176.98453),
        "14_vinyl_alcohol.xyz": (0, 1, -151.91310),
        "15_hocl.xyz": (0, 1, -569.89752),
        "16_h2po4_anion.xyz": (-1, 1, -637.92388),
        "17_claisen.xyz": (0, 1, -267.23859),
        "18_silyene_insertion.xyz": (0, 1, -367.20778),
        "19_hnccs.xyz": (0, 1, -525.43040),
        "20_hconh3_cation.xyz": (+1, 1, -168.24752),
        "21_acrolein_rot.xyz": (0, 1, -189.67574),
        "22_hconhoh.xyz": (0, 1, -242.25529),
        "23_hcn_h2.xyz": (0, 1, -93.31114),
        "24_h2cnh.xyz": (0, 1, -93.33296),
        "25_hcnh2.xyz": (0, 1, -93.28172),
    }
    results_list = list()
    for f, g in zip(xyzs, geoms):
        print(f)
        charge, mult, ref_en = baker_dict[f.name]
        results = run_geom(f.stem, g, charge, mult)
        g0 = results.geom0
        ts_en = g0.energy
        en_diff = ref_en - ts_en
        results_list.append((f.name, ts_en, en_diff, results.converged, results.force_evals))
        print("Results so far:")
        for f_, ts_en, den, conved, evals_ in results_list:
            print(f"\t{f_}: {ts_en:.6f} ({den:.6f}), {conved}, {evals_}")
        print()
        print()
        with open("results_list.pickle", "wb") as handle:
            cloudpickle.dump(results_list, handle)


def run_geom(stem, geom, charge, mult):
    calc_kwargs = {
        "route": "HF/3-21G",
        "pal": 4,
        "mem": 1000,
        "charge": charge,
        "mult": mult,
    }
    def calc_getter():
        return Gaussian16(**calc_kwargs)

    geom.set_calculator(calc_getter())
    geoms = [geom, ]

    dimer_kwargs = {
        "max_step": 0.5,
        # 1e-2 Angstroem
        "dR_base": 0.0189,
        "rot_opt": "lbfgs",
        "angle_tol": 5,
        "f_thresh": 1e-3,
        "max_cycles": 100,
    }
    results = dimer_method(geoms, calc_getter, **dimer_kwargs)
    geom0 = results.geom0
    ts_xyz = geom0.as_xyz()
    ts_fn = f"{stem}_dimer_ts.xyz"
    with open(ts_fn, "w") as handle:
        handle.write(ts_xyz)
    print(f"Wrote dimer result to {ts_fn}")
    return results


if __name__ == "__main__":
    run()