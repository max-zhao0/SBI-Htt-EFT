import sys
import os
from typing import Callable
import json

import awkward as ak
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema
# from coffea import processor

NanoAODSchema.warn_missing_crossrefs = False

NAMED_WEIGHTS = [
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_m1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_1p0_cHDD_1p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_1p0_cHDD_m1p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_m1p0_cHDD_1p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_m1p0_cHDD_m1p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_m1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_m1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_0p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_0p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_1p0",
    "cHbox_1p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_1p0",
    "cHbox_m1p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_m1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_m1p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_0p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_0p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_0p0_ceHIm_0p0_chl3_1p0",
    "cHbox_0p0_cHDD_1p0_ceHRe_0p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_0p0_ceHIm_0p0_chl3_1p0",
    "cHbox_0p0_cHDD_m1p0_ceHRe_0p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_1p0_ceHIm_1p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_1p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_m1p0_ceHIm_1p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_m1p0_ceHIm_m1p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_1p0_ceHIm_0p0_chl3_1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_1p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_m1p0_ceHIm_0p0_chl3_1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_m1p0_ceHIm_0p0_chl3_m1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_m1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_m1p0_chl3_1p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_m1p0_chl3_m1p0",
    "cHbox_10p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_10p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_10p0_ceHIm_0p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_10p0_chl3_0p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_10p0",
    "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_100p0_chl3_0p0",
]

def main(argv):
    indir = argv[1]
    outfile = argv[2]
    assert indir.endswith("/")
    assert outfile.endswith(".json")

    rw_range = {}

    for file_name in os.listdir(indir):
        if not file_name.endswith(".root"):
            continue

        print("Opening:", file_name)
        events = NanoEventsFactory.from_root(
            {indir + file_name : "Events"},
            schemaclass=NanoAODSchema
        ).events()
    
        for rw_name in NAMED_WEIGHTS:
            weights = getattr(events.LHEWeight, rw_name)
            max_weight = float(ak.max(weights))
            min_weight = float(ak.max(weights))
            
            if rw_name in rw_range:
                if max_weight > rw_range[rw_name][1]:
                    rw_range[rw_name][1] = max_weight
                if min_weight < rw_range[rw_name][0]:
                    rw_range[rw_name][0] = min_weight
            else:
                rw_range[rw_name] = [min_weight, max_weight]

    with open(outfile, "w", encoding='utf-8') as f:
        json.dump(rw_range, f, indent=4, ensure_ascii=False)

    return 0

if __name__ == "__main__":
    print("\nFinished with exit code:", main(sys.argv))
