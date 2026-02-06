import os

import uproot

from hist_nanogen import serial

# rootdir = "/eos/user/z/zhaom/qqHtoTauTau/130X_mcRun3_2023_realistic_postBPix_v5/251030_193923/0000/"
rootdir = "/eos/user/z/zhaom/qqHtoTauTau/130X_mcRun3_2023_realistic_postBPix_v5/v2/0000/"

# target_files = os.listdir(rootdir)
target_files = ['gen_15.root', 'gen_22.root', 'gen_25.root', 'gen_27.root']

for fname in target_files:
    if fname.endswith(".root"):
        histograms = serial(
            rootdir + fname,
            [
                "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0",
                "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0", 
                "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_10p0_chl3_0p0",
                "cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_100p0_chl3_0p0"
            ],
            {"single", "diobject", "phicp", "lhetau", "weight"}
        )

        with uproot.recreate("histograms/eft_noms/" + fname) as fout:
            for hist_name in histograms:
                fout[hist_name] = histograms[hist_name]
