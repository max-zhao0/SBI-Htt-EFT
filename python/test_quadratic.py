import argparse
import pickle
import itertools

import uproot
import numpy as np
import pylhe

def extract_coefficients(rw_name : str):
    coeffs = []
    words = rw_name.split("_")
    for i in range(len(words)):
        if words[i].startswith("c"):
            coeffs.append(float(words[i+1].replace("p", ".").replace("m", "-")))
    return np.array(coeffs)

def extract_short_coefficients(rw_name : str):
    coeffs = {}
    if rw_name == "SM":
        return coeffs

    words = rw_name.split("_")
    for i in range(len(words)):
        if words[i].startswith("c"):
            coeffs[words[i]] = float(words[i+1].replace("p", ".").replace("m", "-"))
    
    return coeffs

def from_root(fname : str, max_events : int, rwcard_name : str = None):
    max_events = max_events if np.isfinite(max_events) else None
    with uproot.open(fname) as infile:
        if "LHEReweightingWeight" in infile["Events"].keys():
            assert rwcard_name is not None
            weights = np.array(list(infile["Events/LHEReweightingWeight"].array(library="np", entry_stop=max_events)))

            with open(rwcard_name, "rb") as rwfile:
                data = pickle.load(rwfile, encoding="latin1")
                rw_dict = data["rw_dict"]

                n_coeffs = extract_coefficients(next(iter(rw_dict.keys()))).shape[0]
                coefficients = np.zeros((len(rw_dict), n_coeffs)) - 99
                for rw_name in rw_dict:
                    coefficients[rw_dict[rw_name]] = extract_coefficients(rw_name)
        
        else:
            raise NotImplementedError

    return coefficients, weights

def from_lhe(fname : str, max_events : int, short_rw_names : bool = False):
    event_collection = pylhe.LHEFile.fromfile(fname).events
    rw_idx = None
    weights = []
    for event_no, event in enumerate(event_collection):
        if event_no > max_events:
            break

        if rw_idx is None:
            rw_idx = {}

            if short_rw_names:
                rw_dict = {}
                coefficient_names = {}
                for irw, rw_name in enumerate(event.weights.keys()):
                    if not (rw_name.startswith("c") or rw_name == "SM"):
                        continue

                    rw_coeffs = extract_short_coefficients(rw_name)
                    coefficient_names |= rw_coeffs
                    rw_dict[rw_name] = rw_coeffs
                    rw_idx[rw_name] = irw

                coeff_idx = {coeff : icoeff for icoeff, coeff in enumerate(coefficient_names)}
                coefficients = np.zeros((len(rw_dict), len(coeff_idx))) - 99
                for rw_name in rw_idx:
                    coeff_arr = np.zeros(len(coeff_idx))
                    for coeff_name in rw_dict[rw_name]:
                        coeff_arr[coeff_idx[coeff_name]] = rw_dict[rw_name][coeff_name]
                    coefficients[rw_idx[rw_name]] = coeff_arr
            else:
                rw_dict = {}
                for irw, rw_name in enumerate(event.weights.keys()):
                    if not rw_name.startswith("c"):
                        continue

                    rw_idx[rw_name] = irw
                    rw_dict[rw_name] = extract_coefficients(rw_name)
                
                n_coeffs = extract_coefficients(next(iter(rw_dict.keys()))).shape[0]
                coefficients = np.zeros((len(rw_dict), n_coeffs)) - 99
                for rw_name in rw_idx:
                    coefficients[rw_idx[rw_name]] = rw_dict[rw_name]

        weight_arr = np.zeros(len(rw_idx)) - 99
        for rw_name in rw_idx:
            weight_arr[rw_idx[rw_name]] = event.weights[rw_name]
        weights.append(weight_arr)

    return coefficients, np.array(weights)

def main(args):
    fname = args.filename
    nevents = args.nevents if args.nevents > 0 else np.inf
    rwcard_name = args.rwcard
    short_rw_names = args.short_rw_names
    assert rwcard_name is None or rwcard_name.endswith(".pkl")

    if fname.endswith(".root"):
        coefficients, weights = from_root(fname, nevents, rwcard_name=rwcard_name)
    elif ".lhe" in fname:
        coefficients, weights = from_lhe(fname, nevents, short_rw_names=short_rw_names)
    else:
        raise Exception("Must input root or lhe file")

    print(coefficients.shape)
    print(weights.shape)
    # coefficients = np.random.normal(size=coefficients.shape)
    # weights = np.random.normal(size=weights.shape)

    coefficients_wSM = np.concatenate([coefficients, np.ones((coefficients.shape[0], 1))], axis=1)
    coefficients_quadratic = np.einsum("bi,bj->bij", coefficients_wSM, coefficients_wSM)
    upper_idx = np.triu_indices(coefficients_quadratic.shape[1])
    coefficients_uppertri = coefficients_quadratic[:,upper_idx[0],upper_idx[1]]

    bf, residuals, rank, _ = np.linalg.lstsq(coefficients_uppertri, weights.transpose())
    print("Bestfit shape:", bf.shape)
    print("Mean residual: {:.4e} / {} = {:.4e}".format(np.sum(residuals), len(residuals), np.mean(residuals)))
    print("Rank:", rank)

    return 0

if __name__ == "__main__":
    # python test_quadratic.py data/NanoAOD_ZH.root -n 500 -r data/SMEFTsim_VH_reweight_card.pkl
    # python test_quadratic.py data/quadratic_test/unweighted_events.lhe.gz -s
    # python test_quadratic.py ../genproductions_mg35x_gh/bin/MadGraph5_aMCatNLO/unpacked/cmsgrid_final.lhe
    # python test_quadratic.py ../genproductions_mg35x_gh/bin/MadGraph5_aMCatNLO/VBF_v3/unpacked/cmsgrid_final.lhe
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-n", "--nevents", default=-1, type=int)
    parser.add_argument("-r", "--rwcard")
    parser.add_argument("-s", "--short-rw-names", action='store_true')
    print("\nFinished with exit code:", main(parser.parse_args()))