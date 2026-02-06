import argparse

import uproot
import matplotlib.pyplot as plt
import mplhep as hep

def main(args):
    infile = args.infile
    outdir = args.outdir
    assert infile.endswith(".root")
    assert outdir.endswith("/")

    plt.style.use(hep.style.CMS)

    with uproot.open(infile) as fin:
        for key in fin.keys():
            if "_weight_values" in key and fin[key].classname.startswith("TH1"):
                rw_name = key[:-2].replace("_weight_values", "")
                rw_name = rw_name.replace("_", " ")
                rw_name = rw_name.replace(" 0p0 ", "=0,")
                rw_name = rw_name.replace(" 0p0", "=0")
                rw_name = rw_name.replace(" 100p0", "=100")
                rw_name = rw_name.replace(" 10p0", "=10")
                rw_name = rw_name.replace(" 1p0", "=1")

                fig, ax = plt.subplots()

                hep.histplot(
                    *fin[key].to_numpy(),
                    histtype="step",
                    ax=ax,
                    label=rw_name,
                    color="C0",
                    density=False,
                )

                ax.set_xlabel("weight values")
                ax.set_ylabel("Events")
                ax.legend()
                ax.set_yscale("log")

                hep.cms.label(ax=ax, label="Internal", data=True, year=2023, com=13.6)

                plt.savefig(outdir + "{}_weight_values.png".format(key[:-2]))
                plt.close(fig)

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outdir")
    print("\nFinished with exit code:", main(parser.parse_args()))
