import argparse

import uproot

def main(args):
    with uproot.open("histograms/eft_noms_hists.root") as fin:
        sm_spins, _ = fin["cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_LHEtau_spin"].to_numpy()
        eft_spins, _ = fin["cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_10p0_LHEtau_spin"].to_numpy()
        print("Values")
        print("------")
        print("SM:", sm_spins)
        print("EFT:", eft_spins)
        print()
        print("SM total")
        print("--------")
        print("Aligned:", sm_spins[0] + sm_spins[3])
        print("Antialigned:", sm_spins[1] + sm_spins[2])
        print()
        print("EFT total")
        print("---------")
        print("Aligned:", eft_spins[0] + eft_spins[3])
        print("Antialigned:", eft_spins[1] + eft_spins[2])
        print()
        print("Ratios")
        print("------")
        print("SM:", (sm_spins[1] + sm_spins[2]) / (sm_spins[0] + sm_spins[3]))
        print("EFT:", (eft_spins[1] + eft_spins[2]) / (eft_spins[0] + eft_spins[3]))

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    print("\nFinished with exit code:", main(parser.parse_args()))