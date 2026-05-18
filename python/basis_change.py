import argparse
import os
import json
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

import awkward as ak
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema
from coffea import processor
import uproot
import numpy as np

NanoAODSchema.warn_missing_crossrefs = False

class ChainProcessor(processor.ProcessorABC):
    def __init__(self, processors_to_run : list[processor.ProcessorABC]):
        self.processors_to_run = processors_to_run

    def process(self, events):
        result = {}
        for proc in self.processors_to_run:
            new_arrays = proc.process(events)

            for obj_name in new_arrays:
                if obj_name not in result:
                    result[obj_name] = new_arrays[obj_name]
                else:
                    result[obj_name] |= new_arrays[obj_name]

        return result

    def postprocess(self, accumulator):
        pass

class HiggsBasisProcessor(processor.ProcessorABC):
    def process(self, events):
        

        return None

    def postprocess(self, accumulator):
        pass

def main(args):
    inpath = args.inpath
    outpath = args.outfile
    assert outpath.endswith(".root")

    if inpath.endswith(".root"):
        infiles = {inpath : "Events"}
    elif inpath.endswith("/"):
        infiles = {inpath + fname : "Events" for fname in os.listdir(inpath) if fname.endswith(".root")}
        print("Opening:")
        for p in infiles:
            print(p)
    else:
        raise ValueError("inpath should end with .root or /")
    fileset = {
        "signal": {
            "files": infiles,
            "metadata": {"year": 2024, "is_mc": True},
        }
    }

    runner = processor.Runner(
        executor=processor.IterativeExecutor(), # processor.FuturesExecutor(workers=8),
        schema=NanoAODSchema,
        # chunksize=5000
    )

    chainprocessor = HiggsBasisProcessor()
    outdata = runner(fileset, processor_instance=chainprocessor)

    ntuples = {}
    for obj_name in outdata:
        for attr_name in outdata[obj_name]:
            if attr_name == "num":
                ntuples["n{}".format(obj_name)] = outdata[obj_name][attr_name].value
            elif "num" in outdata[obj_name]:
                ntuples["{}_{}".format(obj_name, attr_name)] = ak.unflatten(outdata[obj_name][attr_name].value, outdata[obj_name]["num"].value)
            else:
                ntuples["{}_{}".format(obj_name, attr_name)] = outdata[obj_name][attr_name].value

    with uproot.recreate(outpath) as fout:
        fout.mktree("Events", ntuples) # ["Events"] = ntuples

    return 0

if __name__ == "__main__":
    # python basis_change.py /eos/user/z/zhaom/qqHtoTauTau/140X_mcRun3_2024_realistic_v26/nanoaodsim_v2/0000/ data/basis_change.root
    # python basis_change.py /eos/user/z/zhaom/qqHtoTauTau/140X_mcRun3_2024_realistic_v26/nanoaodsim_v2/0000/nanoaodsim_1.root data/basis_change.root

    parser = argparse.ArgumentParser()
    parser.add_argument("inpath")
    parser.add_argument("outfile")
    print("\nFinished with exit code:", main(parser.parse_args()))
