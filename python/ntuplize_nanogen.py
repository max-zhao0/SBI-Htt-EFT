
import os
import json
from concurrent.futures import ThreadPoolExecutor

import awkward as ak
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema
from coffea import processor
import uproot
import numpy as np

NanoAODSchema.warn_missing_crossrefs = False

def check_valid_floats(arr : ak.Array):
    arr = ak.to_numpy(arr)
    if np.any(np.isnan(arr)):
        raise ValueError("NaN detected")
    if np.any(np.isinf(arr)):
        raise ValueError("inf detected")

class SingleObjectProcessor(processor.ProcessorABC):
    def __init__(self, extract_candidates : Callable, candidate_name : str):
        self.extract = extract_candidates
        self.name = candidate_name

    def process(self, events):
        candidates = self.extract(events)
        candidates = candidates[:,:2] # At most 2 of each candidate

        return {
            self.name : {
                "num" : processor.column_accumulator(ak.to_numpy(ak.num(candidates))),
                "pt" : processor.column_accumulator(ak.to_numpy(ak.flatten(candidates.pt))),
                "eta" : processor.column_accumulator(ak.to_numpy(ak.flatten(candidates.eta))),
                "phi" : processor.column_accumulator(ak.to_numpy(ak.flatten(candidates.phi))),
                "mass" : processor.column_accumulator(ak.to_numpy(ak.flatten(candidates.mass))),
            }
        }

    def postprocess(self, accumulator):
        pass

def make_4vector(cand, replace_mass=False):
    if replace_mass and hasattr(cand, "pdgId"):
        masses = ak.where(abs(cand.pdgId) == 15, 1.77686, cand.mass)
    else:
        masses = cand.mass

    return ak.zip({"pt": cand.pt, "eta": cand.eta, "phi": cand.phi, "mass": masses}, with_name="Momentum4D")

class DiobjectProcessor(processor.ProcessorABC):
    def __init__(self, 
        extract_candidates1 : Callable,
        candidate1_name : str,
        extract_candidates2 : Callable = None, 
        candidate2_name : str | None = None,
    ):
        self.extract1 = extract_candidates1
        self.extract2 = extract_candidates2
        self.name = candidate1_name + (candidate1_name if candidate2_name is None else candidate2_name)

    def process(self, events):
        if self.extract2 is None:
            diobject = self.extract1(events)
            both_present = ak.num(diobject) >= 2
            diobject = diobject[both_present]
            candidates1 = ak.singletons(diobject[:,0])
            candidates2 = ak.singletons(diobject[:,1])
        else:
            candidates1 = self.extract1(events)
            candidates2 = self.extract2(events)
            both_present = (ak.num(candidates1) == 1) & (ak.num(candidates2) == 1)
            candidates1 = candidates1[both_present]
            candidates2 = candidates2[both_present]

        events = events[both_present]
        vec1 = make_4vector(candidates1)
        vec2 = make_4vector(candidates2)
        
        vec_sum = vec1 + vec2
        mass = vec_sum.mass
        dR = vec1.deltaR(vec2)
        pt = vec_sum.pt
        absdeltaphi = abs(vec1.deltaphi(vec2))

        return {
            self.name : {
                "num" : processor.column_accumulator(ak.to_numpy(both_present).astype(int)),
                "mass" : processor.column_accumulator(ak.to_numpy(ak.flatten(mass))),
                "dR" : processor.column_accumulator(ak.to_numpy(ak.flatten(dR))),
                "pt" : processor.column_accumulator(ak.to_numpy(ak.flatten(pt))),
                "absdeltaphi" : processor.column_accumulator(ak.to_numpy(ak.flatten(absdeltaphi))),
            }
        }

    def postprocess(self, accumulator):
        pass

class PhiCPProcessor(processor.ProcessorABC):
    def __init__(self, 
        extract_candidates1 : Callable,
        candidate1_name : str, 
        extract_candidates2 : Callable = None, 
        candidate2_name : str | None = None,
        verbosity : int = 1
    ):
        self.extract1 = extract_candidates1
        self.extract2 = extract_candidates2
        self.name = candidate1_name + (candidate1_name if candidate2_name is None else candidate2_name)
        self.verbosity = verbosity

    def match_gentau(self, events, cand):
        if hasattr(cand, "genPartIdxMother"):
            # Handles GenVisTau
            taus = events.GenPart[cand.genPartIdxMother]
            return taus

        elif hasattr(cand, "pdgId"):
            # Handles GenDressedLepton. Have to iteratively follow ancestry.
            pdg_matches = events.GenPart[events.GenPart.pdgId == ak.flatten(cand.pdgId)]
            p_pdg_matches = make_4vector(pdg_matches)
            p_cand = make_4vector(cand)

            dR = ak.flatten(p_cand).deltaR(p_pdg_matches)

            pointer = pdg_matches[ak.singletons(ak.argmin(dR, axis=1))]
            not_tau = (pointer.genPartIdxMother != -1) & (abs(events.GenPart[pointer.genPartIdxMother].pdgId) == 15)
            niter = 0
            while ak.any(not_tau):
                niter += 1
                if niter > 20:
                    raise Exception("Maximum depth reached searching for candidate ancestry")

                pointer = ak.where(not_tau, events.GenPart[pointer.genPartIdxMother], pointer)
                not_tau = (pointer.genPartIdxMother != -1) & (abs(events.GenPart[pointer.genPartIdxMother].pdgId) == 15)

            return pointer

        raise ValueError("Invalid object to match to taus")

    def process(self, events):
        if self.extract2 is None:
            diobject = self.extract1(events)
            both_present = ak.num(diobject) == 2
            diobject = diobject[both_present]
            candidates1 = ak.singletons(diobject[:,0])
            candidates2 = ak.singletons(diobject[:,1])
        else:
            candidates1 = self.extract1(events)
            candidates2 = self.extract2(events)
            both_present = (ak.num(candidates1) == 1) & (ak.num(candidates2) == 1)
            candidates1 = candidates1[both_present]
            candidates2 = candidates2[both_present]

        events = events[both_present]
        assert len(events) == len(candidates1) == len(candidates2)
        assert ak.all(ak.num(candidates1) == 1) and ak.all(ak.num(candidates2) == 1)

        tau1 = self.match_gentau(events, candidates1)
        tau2 = self.match_gentau(events, candidates2)
        assert len(tau1) == len(tau2) == len(events)
        assert ak.max(ak.num(tau1)) <= 1 and ak.max(ak.num(tau2)) <= 1

        both_found = (ak.num(tau1) == 1) & (ak.num(tau2) == 1)
        both_valid = (abs(tau1.pdgId) == 15) & (abs(tau2.pdgId) == 15)
        opposite_sign = tau1.pdgId + tau2.pdgId == 0
        assert len(both_found) == len(both_valid) == len(opposite_sign)
        both_matched = ak.flatten(both_found & both_valid & opposite_sign)

        match_rate = ak.sum(both_matched) / len(both_matched)
        # if self.verbosity >= 1:
        #     print("Match rate:", match_rate)
        assert match_rate > 0.9

        tau1 = tau1[both_matched]
        tau2 = tau2[both_matched]
        candidates1 = candidates1[both_matched]
        candidates2 = candidates2[both_matched]

        cand2_is_pos = tau2.pdgId > 0

        ptau1 = make_4vector(tau1)
        ptau2 = make_4vector(tau2)
        pvis1 = make_4vector(candidates1)
        pvis2 = make_4vector(candidates2)

        pH = ptau1 + ptau2

        ptau1_rf = ptau1.boostCM_of_p4(pH).to_3D()
        ptau2_rf = ptau2.boostCM_of_p4(pH).to_3D()
        pvis1_rf = pvis1.boostCM_of_p4(pH).to_3D()
        pvis2_rf = pvis2.boostCM_of_p4(pH).to_3D()
        
        ptau_pos_rf = ak.where(cand2_is_pos, ptau2_rf, ptau1_rf)
        ptau_neg_rf = ak.where(cand2_is_pos, ptau1_rf, ptau2_rf)
        pvis_pos_rf = ak.where(cand2_is_pos, pvis2_rf, pvis1_rf)
        pvis_neg_rf = ak.where(cand2_is_pos, pvis1_rf, pvis2_rf)

        npos = ptau_pos_rf.cross(pvis_pos_rf).unit()
        nneg = pvis_neg_rf.cross(ptau_neg_rf).unit()

        ptau_pos_norm = ptau_pos_rf.unit()
        num = nneg.cross(ptau_pos_norm).dot(npos)
        den = npos.dot(nneg)

        phicp = np.arctan2(num, den)

        present_idx = ak.where(both_present)[0]
        filtered_idx = present_idx[both_matched]
        filtered_mask = np.zeros(len(both_present)).astype(int)
        filtered_mask[filtered_idx] = 1

        return {
            self.name + "Angles" : {
                "num" : processor.column_accumulator(filtered_mask),
                "phicp" : processor.column_accumulator(ak.to_numpy(ak.flatten(phicp))),
            }
        }

    def postprocess(self, accumulator):
        pass

class LHETauProcessor(processor.ProcessorABC):
    def __init__(self, 
        extract_candidates : Callable,
        candidate_name : str = "LHETau"
    ):
        self.extract = extract_candidates
        self.name = candidate_name

    def process(self, events):
        candidates = self.extract(events)
        both_present = ak.num(candidates) == 2
        candidates = candidates[both_present]
        events = events[both_present]

        lhetau1 = candidates[:,0]
        lhetau2 = candidates[:,1]

        up_up = (lhetau1.spin > 0) & (lhetau2.spin > 0)
        up_down = (lhetau1.spin > 0) & (lhetau2.spin < 0)
        down_up = (lhetau1.spin < 0) & (lhetau2.spin > 0)
        down_down = (lhetau1.spin < 0) & (lhetau2.spin < 0)

        spin_idx = ak.Array(np.zeros(len(lhetau1)))
        spin_idx = ak.where(up_up, 0, spin_idx)
        spin_idx = ak.where(up_down, 1, spin_idx)
        spin_idx = ak.where(down_up, 2, spin_idx)
        spin_idx = ak.where(down_down, 3, spin_idx)

        check_valid_floats(spin_idx)

        return {
            self.name : {
                "num" : processor.column_accumulator(ak.to_numpy(both_present).astype(int)),
                "spinid" : processor.column_accumulator(ak.to_numpy(spin_idx)),
            }
        }

    def postprocess(self, accumulator):
        pass

class WeightProcessor(processor.ProcessorABC):
    def process(self, events):
        lhe_values = {}
        for rw_name in dir(events.LHEWeight):
            if "cHbox" in rw_name: # Needed to filter out random dunder methods/attributes and only get actual weight collections
                lhe_values[rw_name] = processor.column_accumulator(ak.to_numpy(getattr(events.LHEWeight, rw_name)))

        tauspinner_values = {}
        for rw_name in dir(events.TauSpinner):
            if "weight" in rw_name:
                tauspinner_values[rw_name] = processor.column_accumulator(ak.to_numpy(getattr(events.TauSpinner, rw_name)))

        return {"LHEWeight" : lhe_values, "TauSpinner" : tauspinner_values}

    def postprocess(self, accumulator):
        pass

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

def main(args):
    inpath = args.inpath
    outpath = args.outfile
    categories = set(args.categories.split(","))

    if args.decaymodes != "all":
        raise NotImplementedError
    assert outpath.endswith(".root")

    if inpath.endswith(".root"):
        infiles = {inpath : "Events"}
    elif inpath.endswith("/"):
        infiles = {inpath + fname : "Events" for fname in os.listdir(inpath) if fname.endswith(".root")}
    else:
        raise ValueError("inpath should end with .root or /")
    fileset = {
        "signal": {
            "files": infiles,
            "metadata": {"year": 2023, "is_mc": True},
        }
    }

    extract_gen_taus = lambda ev: ev.GenPart[(abs(ev.GenPart.pdgId) == 15) & (ev.GenPart.hasFlags(['isPrompt', 'isLastCopy']))]
    extract_dressed_elec = lambda ev: ev.GenDressedLepton[ev.GenDressedLepton.hasTauAnc & (abs(ev.GenDressedLepton.pdgId) == 11)]
    extract_dressed_mu = lambda ev: ev.GenDressedLepton[ev.GenDressedLepton.hasTauAnc & (abs(ev.GenDressedLepton.pdgId) == 13)]
    extract_tauh = lambda ev: ev.GenVisTau
    extract_gen_jets = lambda ev: ev.GenJet
    extract_lhetaus = lambda ev: ev.LHEPart[abs(ev.LHEPart.pdgId) == 15]
    # extract_reweights = {rw_name : (lambda ev, name=rw_name: getattr(ev.LHEWeight, name)) for rw_name in reweight_names}

    runner = processor.Runner(
        executor=processor.FuturesExecutor(workers=8), # , pool=ThreadPoolExecutor
        schema=NanoAODSchema,
        chunksize=5_000
    )
    
    processors_to_run = []

    if "single" in categories:
        gen_tau_processor = SingleObjectProcessor(extract_gen_taus, candidate_name="GenTau")
        dressed_elec_processor = SingleObjectProcessor(extract_dressed_elec, candidate_name="GenDressedElectron")
        dressed_mu_processor = SingleObjectProcessor(extract_dressed_mu, candidate_name="GenDressedMu")
        tauh_processor = SingleObjectProcessor(extract_tauh, candidate_name="GenVisTau")
        gen_jet_processor = SingleObjectProcessor(extract_gen_jets, candidate_name="GenJet")

        processors_to_run += [
            gen_tau_processor,
            dressed_elec_processor,
            dressed_mu_processor,
            tauh_processor,
            gen_jet_processor,
        ]

    if "diobject" in categories:
        gengen_processor = DiobjectProcessor(extract_gen_taus, "GenTau")
        mutau_processor = DiobjectProcessor(extract_dressed_mu, "GenDressedMu", extract_tauh, "GenVisTau")
        etau_processor = DiobjectProcessor(extract_dressed_elec, "GenDressedElectron", extract_tauh, "GenVisTau")
        tautau_processor = DiobjectProcessor(extract_tauh, "GenVisTau")
        dijet_processor = DiobjectProcessor(extract_gen_jets, "GenJet")

        processors_to_run += [
            gengen_processor,
            mutau_processor,
            etau_processor,
            tautau_processor,
            dijet_processor,
        ]

    if "phicp" in categories:
        mutau_CP_processor = PhiCPProcessor(extract_dressed_mu, "GenDressedMu", extract_tauh, "GenVisTau")
        etau_CP_processor = PhiCPProcessor(extract_dressed_elec, "GenDressedElectron", extract_tauh, "GenVisTau")
        tautau_CP_processor = PhiCPProcessor(extract_tauh, "GenVisTau")

        processors_to_run += [
            mutau_CP_processor,
            etau_CP_processor,
            tautau_CP_processor,
        ]

    if "lhetau" in categories:
        lhetau_spin_processor = LHETauProcessor(extract_lhetaus)

        processors_to_run += [
            lhetau_spin_processor,
        ]

    if "weight" in categories:
        weight_processor = WeightProcessor()

        processors_to_run += [
            weight_processor,
        ]

    chainprocessor = ChainProcessor(processors_to_run)
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
        fout["Events"] = ntuples

    return 0

if __name__ == "__main__":
    # python ntuplize_nanogen.py /eos/user/z/zhaom/qqHtoTauTau/130X_mcRun3_2023_realistic_postBPix_v5/unpolarized_v0/0000/ data/eft_unpolarized.root
    # python ntuplize_nanogen.py data/eft_tauspinner_nanogen.root data/eft_tauspinner_ntuples.root
    parser = argparse.ArgumentParser()
    parser.add_argument("inpath")
    parser.add_argument("outfile")
    parser.add_argument("-c", "--categories", default="single,diobject,phicp,lhetau,weight")
    parser.add_argument("-d", "--decaymodes", default="all")
    print("\nFinished with exit code:", main(parser.parse_args()))
