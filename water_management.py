"""
Python model 'water_management.py'
Translated using PySD
"""

from pathlib import Path
import numpy as np
from scipy import stats

from pysd.py_backend.functions import modulo, xidz, if_then_else
from pysd.py_backend.statefuls import Integ, DelayFixed
from pysd import Component

__pysd_version__ = "3.14.3"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 24,
    "time_step": lambda: 1,
    "saveper": lambda: time_step(),
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(
    name="FINAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def final_time():
    """
    The final time for the simulation.
    """
    return __data["time"].final_time()


@component.add(
    name="INITIAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def initial_time():
    """
    The initial time for the simulation.
    """
    return __data["time"].initial_time()


@component.add(
    name="SAVEPER",
    units="Month",
    limits=(0.0, np.nan),
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time_step": 1},
)
def saveper():
    """
    The frequency with which output is stored.
    """
    return __data["time"].saveper()


@component.add(
    name="TIME STEP",
    units="Month",
    limits=(0.0, np.nan),
    comp_type="Constant",
    comp_subtype="Normal",
)
def time_step():
    """
    The time step for the simulation.
    """
    return __data["time"].time_step()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="Agricultural water use",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"net_agricultural_water_use": 1, "agricultural_water_use_change": 1},
)
def agricultural_water_use():
    return net_agricultural_water_use() * agricultural_water_use_change()


@component.add(
    name="Agricultural water use change",
    limits=(1.0, 1.5, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def agricultural_water_use_change():
    return 1


@component.add(
    name="Deep groundwater inflow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "natural_deep_groundwater_inflow": 1,
        "return_flow": 1,
        "deep_groundwater_return_ratio": 1,
    },
)
def deep_groundwater_inflow():
    return (
        natural_deep_groundwater_inflow()
        + deep_groundwater_return_ratio() * return_flow()
    )


@component.add(
    name="Deep groundwater outflow",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"deep_groundwater_outflow_ratio": 1, "deep_groundwater": 1},
)
def deep_groundwater_outflow():
    return deep_groundwater_outflow_ratio() * deep_groundwater()


@component.add(
    name="Natural deep groundwater inflow",
    units="m3/day",
    comp_type="Constant",
    comp_subtype="Normal",
)
def natural_deep_groundwater_inflow():
    return 10000000000.0 / 30


@component.add(
    name="Deep groundwater outflow ratio",
    limits=(0.0, 0.3, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def deep_groundwater_outflow_ratio():
    return 0.1


@component.add(
    name="Groundwater return ratio", comp_type="Constant", comp_subtype="Normal"
)
def groundwater_return_ratio():
    return 0.7


@component.add(
    name="Groundwater use ratio",
    limits=(0.0, 1.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def groundwater_use_ratio():
    return 0.8


@component.add(name="Area", units="m2", comp_type="Constant", comp_subtype="Normal")
def area():
    return 411 * 1000000.0


@component.add(
    name="Available groundwater",
    units="m3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_available_groundwater": 1},
    other_deps={
        "_integ_available_groundwater": {
            "initial": {"area": 1, "shallow_layer_thickness": 1, "porosity": 1},
            "step": {
                "groundwater_inflow": 1,
                "percolation": 1,
                "seepage_from_deep": 1,
                "evaporation": 1,
                "groundwater_outflow": 1,
                "groundwater_withdrawal": 1,
                "percolation_to_deep": 1,
                "seepage": 1,
            },
        }
    },
)
def available_groundwater():
    return _integ_available_groundwater()


_integ_available_groundwater = Integ(
    lambda: groundwater_inflow()
    + percolation()
    + seepage_from_deep()
    - evaporation()
    - groundwater_outflow()
    - groundwater_withdrawal()
    - percolation_to_deep()
    - seepage(),
    lambda: area() * shallow_layer_thickness() * porosity(),
    "_integ_available_groundwater",
)


@component.add(
    name="Available Surface Water",
    units="Mm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_available_surface_water": 1},
    other_deps={
        "_integ_available_surface_water": {
            "initial": {"area": 1},
            "step": {
                "runoff": 1,
                "seepage": 1,
                "surface_water_inflow": 1,
                "evapotranspiration": 1,
                "percolation": 1,
                "surface_water_outflow": 1,
                "surface_water_withdrawal": 1,
            },
        }
    },
)
def available_surface_water():
    return _integ_available_surface_water()


_integ_available_surface_water = Integ(
    lambda: runoff()
    + seepage()
    + surface_water_inflow()
    - evapotranspiration()
    - percolation()
    - surface_water_outflow()
    - surface_water_withdrawal(),
    lambda: area() * 0.1,
    "_integ_available_surface_water",
)


@component.add(
    name="Seepage",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"seepage_ratio": 1, "available_groundwater": 1},
)
def seepage():
    return seepage_ratio() * available_groundwater()


@component.add(
    name="Seepage from deep",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"seepage_ratio_from_deep": 1, "deep_groundwater": 1},
)
def seepage_from_deep():
    return seepage_ratio_from_deep() * deep_groundwater()


@component.add(
    name="Company inflow",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"company": 1, "company_inflow_ratio": 1, "time": 1},
)
def company_inflow():
    return (
        company()
        * company_inflow_ratio()
        * float(
            stats.truncnorm.rvs(
                xidz(0 - 1, 0.3, -np.inf),
                xidz(2 - 1, 0.3, np.inf),
                loc=1,
                scale=0.3,
                size=(),
            )
        )
    )


@component.add(name="Company inflow ratio", comp_type="Constant", comp_subtype="Normal")
def company_inflow_ratio():
    return 0.01


@component.add(
    name="Company outflow",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"company": 1, "company_outflow_ratio": 1, "time": 1},
)
def company_outflow():
    return (
        company()
        * company_outflow_ratio()
        * float(
            stats.truncnorm.rvs(
                xidz(0 - 1, 0.3, -np.inf),
                xidz(2 - 1, 0.3, np.inf),
                loc=1,
                scale=0.3,
                size=(),
            )
        )
    )


@component.add(
    name="Company outflow ratio", comp_type="Constant", comp_subtype="Normal"
)
def company_outflow_ratio():
    return 0.005


@component.add(
    name="Surface water outflow",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"outflow_ratio": 1, "available_surface_water": 1},
)
def surface_water_outflow():
    return outflow_ratio() * available_surface_water()


@component.add(
    name="Deep ground water withdrawal",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "net_water_demand": 1,
        "deep_groundwater_use_ratio": 1,
        "deep_groundwater": 1,
    },
)
def deep_ground_water_withdrawal():
    return float(
        np.minimum(
            net_water_demand() * deep_groundwater_use_ratio(), deep_groundwater()
        )
    )


@component.add(
    name="Deep groundwater",
    units="Mm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_deep_groundwater": 1},
    other_deps={
        "_integ_deep_groundwater": {
            "initial": {"area": 1, "deep_layer_thickness": 1, "deep_porosity": 1},
            "step": {
                "deep_groundwater_inflow": 1,
                "percolation_to_deep": 1,
                "deep_ground_water_withdrawal": 1,
                "deep_groundwater_outflow": 1,
                "seepage_from_deep": 1,
            },
        }
    },
)
def deep_groundwater():
    return _integ_deep_groundwater()


_integ_deep_groundwater = Integ(
    lambda: deep_groundwater_inflow()
    + percolation_to_deep()
    - deep_ground_water_withdrawal()
    - deep_groundwater_outflow()
    - seepage_from_deep(),
    lambda: area() * deep_layer_thickness() * deep_porosity(),
    "_integ_deep_groundwater",
)


@component.add(
    name="Percolation to deep",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"deep_percolation_ratio": 1, "available_groundwater": 1},
)
def percolation_to_deep():
    return deep_percolation_ratio() * available_groundwater()


@component.add(
    name="Deep groundwater return ratio", comp_type="Constant", comp_subtype="Normal"
)
def deep_groundwater_return_ratio():
    return 0.1


@component.add(
    name="Deep groundwater use ratio",
    limits=(0.0, 1.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def deep_groundwater_use_ratio():
    return 0


@component.add(name="Deep layer thickness", comp_type="Constant", comp_subtype="Normal")
def deep_layer_thickness():
    return 100


@component.add(
    name="Deep percolation ratio",
    limits=(0.0, 0.4, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def deep_percolation_ratio():
    return 0.02


@component.add(name="Deep porosity", comp_type="Constant", comp_subtype="Normal")
def deep_porosity():
    return 0.1


@component.add(
    name="Porosity",
    limits=(0.0, 0.5, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def porosity():
    return 0.05


@component.add(
    name="Surface water return flow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"surface_water_return_ratio": 1, "return_flow": 1},
)
def surface_water_return_flow():
    return surface_water_return_ratio() * return_flow()


@component.add(
    name="Surface water return ratio", comp_type="Constant", comp_subtype="Normal"
)
def surface_water_return_ratio():
    return 0.2


@component.add(
    name="Runoff",
    units="m3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"area": 1, "precipitation": 1},
)
def runoff():
    return area() * precipitation() * 0.001


@component.add(
    name="Groundwater level",
    units="m",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"available_groundwater": 1, "area": 1, "porosity": 1},
)
def groundwater_level():
    return available_groundwater() / area() / porosity() - 17


@component.add(
    name="Groundwater outflow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"groundwater_outflow_ratio": 1, "available_groundwater": 1},
)
def groundwater_outflow():
    return groundwater_outflow_ratio() * available_groundwater()


@component.add(
    name="Seepage ratio",
    limits=(0.0, 0.1, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def seepage_ratio():
    return 0.03


@component.add(
    name="Domestic water use",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"domestic_water_demand": 1},
)
def domestic_water_use():
    return domestic_water_demand()


@component.add(
    name="Shallow layer thickness", comp_type="Constant", comp_subtype="Normal"
)
def shallow_layer_thickness():
    return 10


@component.add(
    name="Outflow ratio",
    limits=(0.0, 1.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def outflow_ratio():
    return 0.4


@component.add(
    name="Groundwater withdrawal",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "net_water_demand": 1,
        "groundwater_use_ratio": 1,
        "available_groundwater": 1,
    },
)
def groundwater_withdrawal():
    return float(
        np.minimum(
            net_water_demand() * groundwater_use_ratio(), available_groundwater()
        )
    )


@component.add(
    name="Groundwater outflow ratio",
    limits=(0.0, 1.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def groundwater_outflow_ratio():
    return 0.4


@component.add(
    name="Percolation",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"percolation_ratio": 1, "available_surface_water": 1},
)
def percolation():
    return percolation_ratio() * available_surface_water()


@component.add(
    name="Surface water use ratio",
    limits=(0.0, 1.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def surface_water_use_ratio():
    return 0.2


@component.add(
    name="Surface water withdrawal",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "net_water_demand": 1,
        "surface_water_use_ratio": 1,
        "available_surface_water": 1,
    },
)
def surface_water_withdrawal():
    return float(
        np.minimum(
            net_water_demand() * surface_water_use_ratio(), available_surface_water()
        )
    )


@component.add(
    name="Groundwater return flow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"groundwater_return_ratio": 1, "return_flow": 1},
)
def groundwater_return_flow():
    return groundwater_return_ratio() * return_flow()


@component.add(
    name="Net agricultural water use",
    units="Mm3/day",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time": 2},
)
def net_agricultural_water_use():
    return if_then_else(
        modulo(time(), 12) >= 4,
        lambda: if_then_else(
            modulo(time(), 12) <= 9,
            lambda: 2.4 * 100000000.0 / 365 * 1.9,
            lambda: 2.4 * 100000000.0 / 365 * 0.1,
        ),
        lambda: 2.4 * 100000000.0 / 365 * 0.1,
    )


@component.add(
    name="Population outflow ratio",
    limits=(0.0, 0.1, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def population_outflow_ratio():
    return 0.02


@component.add(
    name="Population outflow",
    units="people/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"population": 1, "population_outflow_ratio": 1, "time": 1},
)
def population_outflow():
    return (
        population()
        * population_outflow_ratio()
        * float(
            stats.truncnorm.rvs(
                xidz(0 - 1, 0.3, -np.inf),
                xidz(2 - 1, 0.3, np.inf),
                loc=1,
                scale=0.3,
                size=(),
            )
        )
    )


@component.add(
    name="Population inflow",
    units="people/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"population": 1, "population_inflow_ratio": 1, "time": 1},
)
def population_inflow():
    return (
        population()
        * population_inflow_ratio()
        * float(
            stats.truncnorm.rvs(
                xidz(0 - 1, 0.3, -np.inf),
                xidz(2 - 1, 0.3, np.inf),
                loc=1,
                scale=0.3,
                size=(),
            )
        )
    )


@component.add(
    name="Seepage ratio from deep",
    limits=(0.0, 0.1, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def seepage_ratio_from_deep():
    return 0.01


@component.add(
    name="Industrial water use",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"industrial_water_demand": 1},
)
def industrial_water_use():
    return industrial_water_demand()


@component.add(
    name="Net water demand",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agricultural_water_use": 1,
        "domestic_water_use": 1,
        "industrial_water_use": 1,
    },
)
def net_water_demand():
    return agricultural_water_use() + domestic_water_use() + industrial_water_use()


@component.add(
    name="Population inflow ratio",
    limits=(0.0, 0.1, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def population_inflow_ratio():
    return 0.01


@component.add(
    name="Percolation ratio",
    limits=(0.0, 1.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def percolation_ratio():
    return 0.3


@component.add(
    name="Precipitation",
    units="mm/day",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"time": 1},
)
def precipitation():
    return np.interp(
        time(),
        [
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
            6.0,
            7.0,
            8.0,
            9.0,
            10.0,
            11.0,
            12.0,
            13.0,
            14.0,
            15.0,
            16.0,
            17.0,
            18.0,
            19.0,
            20.0,
            21.0,
            22.0,
            23.0,
            24.0,
        ],
        [
            32.9,
            32.4,
            81.0,
            111.0,
            143.3,
            175.1,
            254.5,
            234.0,
            230.3,
            158.3,
            73.9,
            41.3,
            32.9,
            32.4,
            81.0,
            111.0,
            143.3,
            175.1,
            254.5,
            234.0,
            230.3,
            158.3,
            73.9,
            41.3,
        ],
    )


@component.add(
    name="Temperature",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"time": 1},
)
def temperature():
    return np.interp(
        time(),
        [
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
            6.0,
            7.0,
            8.0,
            9.0,
            10.0,
            11.0,
            12.0,
            13.0,
            14.0,
            15.0,
            16.0,
            17.0,
            18.0,
            19.0,
            20.0,
            21.0,
            22.0,
            23.0,
            24.0,
        ],
        [
            0.9,
            1.5,
            4.9,
            10.2,
            15.5,
            19.1,
            22.8,
            23.8,
            20.1,
            14.5,
            8.5,
            3.3,
            0.9,
            1.5,
            4.9,
            10.2,
            15.5,
            19.1,
            22.8,
            23.8,
            20.1,
            14.5,
            8.5,
            3.3,
        ],
    )


@component.add(
    name="Actual land area for crop X",
    units="ha",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"expected_land_area_for_crop_x": 1, "delayed_delivery_rate": 1},
)
def actual_land_area_for_crop_x():
    return float(
        np.maximum(
            0,
            0.8
            * expected_land_area_for_crop_x()
            * float(np.minimum(delayed_delivery_rate(), 1)),
        )
    )


@component.add(
    name="Industrial return flow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"industrial_water_use": 1},
)
def industrial_return_flow():
    return 0.1 * industrial_water_use()


@component.add(
    name="Industrial water demand",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"company": 1, "per_capita_industrial_water_demand": 1},
)
def industrial_water_demand():
    return company() * per_capita_industrial_water_demand()


@component.add(
    name="Company",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_company": 1},
    other_deps={
        "_integ_company": {
            "initial": {},
            "step": {"company_inflow": 1, "company_outflow": 1},
        }
    },
)
def company():
    return _integ_company()


_integ_company = Integ(
    lambda: company_inflow() - company_outflow(), lambda: 5000, "_integ_company"
)


@component.add(
    name="Natural groundwater inflow",
    units="m3/Month",
    comp_type="Constant",
    comp_subtype="Normal",
)
def natural_groundwater_inflow():
    return 2000000000.0 / 30


@component.add(
    name="Surface water inflow",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"surface_water_return_flow": 1},
)
def surface_water_inflow():
    return surface_water_return_flow()


@component.add(
    name="Evapotranspiration",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"available_surface_water": 1, "temperature": 1},
)
def evapotranspiration():
    return 0.05 * available_surface_water() * (1 + 0.01 * (temperature() - 15))


@component.add(
    name="Per capita industrial water demand",
    units="m3/day",
    comp_type="Constant",
    comp_subtype="Normal",
)
def per_capita_industrial_water_demand():
    return 0.022 * 1000000.0 / 30


@component.add(
    name="Expected water requirement for crop X",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "delayed_expected_land_area_for_crop_x": 1,
        "delayed_irrigation_water_requirement_for_crop_x": 1,
    },
)
def expected_water_requirement_for_crop_x():
    return (
        0.01 * delayed_expected_land_area_for_crop_x()
        + delayed_irrigation_water_requirement_for_crop_x()
    )


@component.add(
    name="Water Supply",
    units="Mm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_water_supply": 1},
    other_deps={
        "_integ_water_supply": {
            "initial": {},
            "step": {
                "water_supply_inflow": 1,
                "agricultural_water_use": 1,
                "domestic_water_use": 1,
                "industrial_water_use": 1,
            },
        }
    },
)
def water_supply():
    return _integ_water_supply()


_integ_water_supply = Integ(
    lambda: water_supply_inflow()
    - agricultural_water_use()
    - domestic_water_use()
    - industrial_water_use(),
    lambda: 0,
    "_integ_water_supply",
)


@component.add(
    name="Delayed delivery rate",
    comp_type="Stateful",
    comp_subtype="DelayFixed",
    depends_on={"_delayfixed_delayed_delivery_rate": 1},
    other_deps={
        "_delayfixed_delayed_delivery_rate": {
            "initial": {},
            "step": {"delivery_rate": 1},
        }
    },
)
def delayed_delivery_rate():
    return _delayfixed_delayed_delivery_rate()


_delayfixed_delayed_delivery_rate = DelayFixed(
    lambda: delivery_rate(),
    lambda: 1,
    lambda: 1,
    time_step,
    "_delayfixed_delayed_delivery_rate",
)


@component.add(
    name="Delayed expected land area for crop X",
    comp_type="Stateful",
    comp_subtype="DelayFixed",
    depends_on={"_delayfixed_delayed_expected_land_area_for_crop_x": 1},
    other_deps={
        "_delayfixed_delayed_expected_land_area_for_crop_x": {
            "initial": {},
            "step": {"expected_land_area_for_crop_x": 1},
        }
    },
)
def delayed_expected_land_area_for_crop_x():
    return _delayfixed_delayed_expected_land_area_for_crop_x()


_delayfixed_delayed_expected_land_area_for_crop_x = DelayFixed(
    lambda: expected_land_area_for_crop_x(),
    lambda: 1,
    lambda: 70000,
    time_step,
    "_delayfixed_delayed_expected_land_area_for_crop_x",
)


@component.add(
    name="Delayed irrigation water requirement for crop X",
    comp_type="Stateful",
    comp_subtype="DelayFixed",
    depends_on={"_delayfixed_delayed_irrigation_water_requirement_for_crop_x": 1},
    other_deps={
        "_delayfixed_delayed_irrigation_water_requirement_for_crop_x": {
            "initial": {},
            "step": {"irrigation_water_requirement_for_crop_x": 1},
        }
    },
)
def delayed_irrigation_water_requirement_for_crop_x():
    return _delayfixed_delayed_irrigation_water_requirement_for_crop_x()


_delayfixed_delayed_irrigation_water_requirement_for_crop_x = DelayFixed(
    lambda: irrigation_water_requirement_for_crop_x(),
    lambda: 1,
    lambda: 0,
    time_step,
    "_delayfixed_delayed_irrigation_water_requirement_for_crop_x",
)


@component.add(
    name="Delayed net benefit from crop X",
    comp_type="Stateful",
    comp_subtype="DelayFixed",
    depends_on={"_delayfixed_delayed_net_benefit_from_crop_x": 1},
    other_deps={
        "_delayfixed_delayed_net_benefit_from_crop_x": {
            "initial": {},
            "step": {"net_benefit_from_crop_x": 1},
        }
    },
)
def delayed_net_benefit_from_crop_x():
    return _delayfixed_delayed_net_benefit_from_crop_x()


_delayfixed_delayed_net_benefit_from_crop_x = DelayFixed(
    lambda: net_benefit_from_crop_x(),
    lambda: 1,
    lambda: 75000,
    time_step,
    "_delayfixed_delayed_net_benefit_from_crop_x",
)


@component.add(
    name="Delivery rate",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "net_agricultural_water_use": 1,
        "expected_agricultural_water_requirement": 1,
    },
)
def delivery_rate():
    return float(
        np.minimum(
            1,
            net_agricultural_water_use()
            / (expected_agricultural_water_requirement() + 1e-06),
        )
    )


@component.add(
    name="Expected land area for crop X",
    units="ha",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"delayed_net_benefit_from_crop_x": 1},
)
def expected_land_area_for_crop_x():
    return float(
        np.maximum(
            0, 11806 * (1 + 0.01 * (delayed_net_benefit_from_crop_x() - 100000000.0))
        )
    )


@component.add(
    name="Return flow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agricultural_return_flow": 1,
        "domestic_return_flow": 1,
        "industrial_return_flow": 1,
    },
)
def return_flow():
    return (
        agricultural_return_flow() + domestic_return_flow() + industrial_return_flow()
    )


@component.add(
    name="Irrigation water requirement for crop X",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"temperature": 1, "precipitation": 1, "actual_land_area_for_crop_x": 1},
)
def irrigation_water_requirement_for_crop_x():
    return (
        0.1
        * float(np.maximum(temperature() - 25, 0))
        * float(np.maximum(2 - precipitation(), 0))
        * actual_land_area_for_crop_x()
    )


@component.add(
    name="Population",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_population": 1},
    other_deps={
        "_integ_population": {
            "initial": {},
            "step": {"population_inflow": 1, "population_outflow": 1},
        }
    },
)
def population():
    return _integ_population()


_integ_population = Integ(
    lambda: population_inflow() - population_outflow(),
    lambda: 113676,
    "_integ_population",
)


@component.add(
    name="Agricultural return flow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agricultural_water_use": 1},
)
def agricultural_return_flow():
    return 0.3 * agricultural_water_use()


@component.add(
    name="Domestic return flow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"domestic_water_use": 1},
)
def domestic_return_flow():
    return 0.2 * domestic_water_use()


@component.add(
    name="Benefit from crop X",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"actual_land_area_for_crop_x": 1},
)
def benefit_from_crop_x():
    return 500 * actual_land_area_for_crop_x()


@component.add(
    name="Cultivation cost for crop X",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"actual_land_area_for_crop_x": 1},
)
def cultivation_cost_for_crop_x():
    return 200 * actual_land_area_for_crop_x()


@component.add(
    name="Evaporation",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"precipitation": 1, "temperature": 2, "available_groundwater": 1},
)
def evaporation():
    return 0.05 * precipitation() * (
        1 + 0.02 * (temperature() - 15)
    ) + 0.03 * available_groundwater() * (1 + 0.01 * (temperature() - 15))


@component.add(
    name="Expected agricultural water requirement",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"expected_water_requirement_for_crop_x": 1},
)
def expected_agricultural_water_requirement():
    return expected_water_requirement_for_crop_x()


@component.add(
    name="Per capita domestic water demand",
    units="m3/day",
    comp_type="Constant",
    comp_subtype="Normal",
)
def per_capita_domestic_water_demand():
    return 300


@component.add(
    name="Groundwater inflow",
    units="Mm3/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"groundwater_return_flow": 1, "natural_groundwater_inflow": 1},
)
def groundwater_inflow():
    return groundwater_return_flow() + natural_groundwater_inflow()


@component.add(
    name="Water supply inflow",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "deep_ground_water_withdrawal": 1,
        "groundwater_withdrawal": 1,
        "surface_water_withdrawal": 1,
    },
)
def water_supply_inflow():
    return (
        deep_ground_water_withdrawal()
        + groundwater_withdrawal()
        + surface_water_withdrawal()
    )


@component.add(
    name="Net benefit from crop X",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"benefit_from_crop_x": 1, "cultivation_cost_for_crop_x": 1},
)
def net_benefit_from_crop_x():
    return benefit_from_crop_x() - cultivation_cost_for_crop_x()


@component.add(
    name="Domestic water demand",
    units="m3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "per_capita_domestic_water_demand": 1,
        "population": 1,
        "temperature": 1,
    },
)
def domestic_water_demand():
    return (
        per_capita_domestic_water_demand()
        * population()
        * (1 + 0.01 * (temperature() - 15))
    )
