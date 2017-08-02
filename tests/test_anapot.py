#!/usr/bin/env python3

import copy

import numpy as np
from pytest import approx

from pysisyphus.AnimPlot import AnimPlot
from pysisyphus.calculators.AnaPot import AnaPot
from pysisyphus.cos.NEB import NEB
from pysisyphus.cos.SimpleZTS import SimpleZTS
from pysisyphus.optimizers.FIRE import FIRE
from pysisyphus.Geometry import Geometry
from pysisyphus.optimizers.SteepestDescent import SteepestDescent

KWARGS = {
    "images": 5,
    "max_cycles": 50,
    "convergence": {
        "max_step_thresh": 1e-3,
        "rms_step_thresh": 1.6e-4,
    },
}


def get_geoms():
    initial = np.array((-1.05274, 1.02776, 0))
    final = np.array((1.94101, 3.85427, 0))
    atoms = ("H")
    geoms = [Geometry(atoms, coords) for coords in (initial, final)]
    return geoms


def run_cos_opt(cos, Opt, images, **kwargs):
    cos.interpolate(images)
    opt = Opt(cos, **kwargs)
    for img in cos.images:
        img.set_calculator(AnaPot())
    opt.run()

    return opt


def animate(opt):
    xlim = (-2, 2.5)
    ylim = (0, 5)
    levels = (-3, 6, 50)
    ap = AnimPlot(AnaPot(), opt, xlim=xlim, ylim=ylim, levels=levels)
    ap.animate()


def test_steepest_descent_neb():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 30
    neb = NEB(get_geoms())
    opt = run_cos_opt(neb, SteepestDescent, **kwargs)

    assert(opt.is_converged)

    return opt


def test_steepest_descent_neb_more_images():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 32
    kwargs["images"] = 15
    neb = NEB(get_geoms())
    opt = run_cos_opt(neb, SteepestDescent, **kwargs)

    assert(opt.is_converged)

    return opt



def test_fire_neb():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 21
    neb = NEB(get_geoms())
    opt = run_cos_opt(neb, FIRE, **kwargs)
    
    assert(opt.rms_steps[-1] == approx(0.006848, rel=1e-4))

    return opt


def test_equal_szts():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 37
    convergence = {
        "max_step_thresh": 1e-3,
        "rms_step_thresh": 3e-4,
    }
    kwargs["convergence"] = convergence
    szts_equal = SimpleZTS(get_geoms(), param="equal")
    opt = run_cos_opt(szts_equal, SteepestDescent, **kwargs)

    assert(opt.is_converged)

    return opt


def test_equal_szts_more_images():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 38
    kwargs["images"] = 10
    convergence = {
        "max_step_thresh": 4e-3,
        "rms_step_thresh": 4e-4,
    }
    kwargs["convergence"] = convergence
    szts_equal = SimpleZTS(get_geoms(), param="equal")
    opt = run_cos_opt(szts_equal, SteepestDescent, **kwargs)

    assert(opt.is_converged)

    return opt


def test_energy_szts():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 42
    szts_energy = SimpleZTS(get_geoms(), param="energy")
    opt = run_cos_opt(szts_energy, SteepestDescent, **kwargs)

    assert(opt.is_converged)

    return opt


def test_energy_szts_more_images():
    kwargs = copy.copy(KWARGS)
    kwargs["max_cycles"] = 43
    kwargs["images"] = 10
    convergence = {
        "max_step_thresh": 4e-3,
        "rms_step_thresh": 3e-4,
    }
    kwargs["convergence"] = convergence
    szts_energy = SimpleZTS(get_geoms(), param="energy")
    opt = run_cos_opt(szts_energy, SteepestDescent, **kwargs)

    assert(opt.is_converged)

    return opt

if __name__ == "__main__":
    # Steepest Descent
    #opt = test_steepest_descent_neb()
    #opt = test_steepest_descent_neb_more_images()

    # FIRE
    #opt = test_fire_neb()

    # SimpleZTS
    #opt = test_equal_szts()
    #opt = test_equal_szts_more_images()
    #opt = test_energy_szts()
    opt = test_energy_szts_more_images()

    animate(opt)