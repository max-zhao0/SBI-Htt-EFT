import argparse

import uproot
import mplhep as hep
import matplotlib.pyplot as plt
import awkward as ak
import hist
import numpy as np

plt.style.use(hep.style.CMS)

def convert_reweight_to_string(reweight : dict[str, float]):
    raise NotImplementedError

def flatten_with_weights(event_data, weights):
    flat_data = ak.flatten(event_data)
    relevant_weights = weights[ak.num(event_data) >= 1]
    assert len(flat_data) == len(relevant_weights)
    return flat_data, relevant_weights

def plot_unweighted(data : dict[str, ak.Array], axis_label : str, outpath : str, bounds, nbins : int = 50, density=True):
    histograms = {}
    for ds in data:
        h_phicp = hist.Hist.new.Reg(
            nbins, *bounds, name="var", label=ds
        ).Double()
        h_phicp.fill(var=data[ds])
        histograms[ds] = h_phicp

    fig, ax = plt.subplots()
    for ids, ds in enumerate(histograms):
        hep.histplot(
            histograms[ds],
            histtype="step",
            ax=ax,
            label=ds,
            color="C{}".format(ids),
            density=density,
        )

    ax.set_xlabel(axis_label)
    ax.set_ylabel("Events Normalized" if density else "Events")

    hep.cms.label(ax=ax, label="Internal", data=True, year=2024, com=13.6)
    ax.legend()

    plt.savefig(outpath)
    plt.close(fig)

def plot_phicp(data : dict[str, tuple], axis_label : str, outpath : str, nbins : int = 10):
    histograms = {}
    for ds in data:
        h_phicp = hist.Hist.new.Reg(
            nbins, -np.pi, np.pi, name="phicp", label=ds
        ).Weight()
        h_phicp.fill(phicp=data[ds][0], weight=data[ds][1])
        histograms[ds] = h_phicp

    fig, ax = plt.subplots()
    for ids, ds in enumerate(histograms):
        hep.histplot(
            histograms[ds],
            histtype="step",
            ax=ax,
            label=ds,
            color="C{}".format(ids),
            density=True,
        )

    ax.set_ylim(0.1592 - 0.04, 0.1592 + 0.04)
    ax.set_xlabel(axis_label)
    ax.set_ylabel("Events Normalized")

    hep.cms.label(ax=ax, label="Internal", data=True, year=2024, com=13.6)
    ax.legend()

    plt.savefig(outpath)
    plt.close(fig)

def plot_phicp_weight_cutoff(phicp, weights, axis_label, cutoff, outpath):
    flat_phicp, relevant_weights = flatten_with_weights(phicp, weights)

    above = relevant_weights >= cutoff
    below = ~above

    flat_phicp_up = flat_phicp[above]
    flat_weights_up = relevant_weights[above]
    flat_phicp_down = flat_phicp[below]
    flat_weights_down = relevant_weights[below]

    data = {
        "weight >= " + str(cutoff) : (flat_phicp_up, flat_weights_up),
        "weight < " + str(cutoff) : (flat_phicp_down, flat_weights_down)
    }
    plot_phicp(data, axis_label, outpath)
    return None

    h_phicp_up = hist.Hist.new.Reg(
        10, -np.pi, np.pi, name="phicp", label="phicp up"
    ).Weight()
    h_phicp_down = hist.Hist.new.Reg(
        10, -np.pi, np.pi, name="phicp", label="phicp down"
    ).Weight()

    h_phicp_up.fill(phicp=flat_phicp_up, weight=flat_weights_up)
    h_phicp_down.fill(phicp=flat_phicp_down, weight=flat_weights_down)

    fig, ax = plt.subplots()

    hep.histplot(
        h_phicp_up,
        histtype="errorbar",
        ax=ax,
        label="weight >= " + str(cutoff),
        color="C0",
        density=True,
    )
    hep.histplot(
        h_phicp_down,
        histtype="errorbar",
        ax=ax,
        label="weight < " + str(cutoff),
        color="C1",
        density=True,
    )

    ax.set_ylim(0.1592 - 0.04, 0.1592 + 0.04)
    ax.set_xlabel(axis_label)
    ax.set_ylabel("Events Normalized")

    hep.cms.label(ax=ax, label="Internal", data=True, year=2024, com=13.6)
    ax.legend()

    plt.savefig(outpath)
    plt.close(fig)

def plot_lhetau_spin_ratio(spinid, weights, weight_values, axis_label, outpath="lhetau_spin_ratio1.png"):
    spinid = ak.flatten(spinid)
    ratios = [np.sum(w[spinid == 0]) / np.sum(w[spinid == 3]) for w in weights]
    
    lamb_p = np.sum(spinid == 0)
    lamb_m = np.sum(spinid == 3)
    sigma_r = np.sqrt(lamb_p * (1 + lamb_p / lamb_m)) / lamb_m

    fig, ax = plt.subplots()

    ticks = np.arange(len(ratios))
    # ax.errorbar(ticks, ratios, yerr=sigma_r, fmt="o")
    ax.scatter(ticks, ratios)

    ax.set_xticks(ticks, weight_values)
    ax.set_xlim(-0.2, ticks[-1]+0.2)
    ax.set_xlabel(axis_label)

    # ax.hlines(1, -0.2, ticks[-1]+0.2, color="r")
    ax.set_ylim(1.00441+25e-7, 1.00441+34e-7)
    ax.set_ylabel("LHEtau spin ++/--")

    hep.cms.label(ax=ax, label="Internal", data=True, year=2023, com=13.6, loc=1)

    plt.savefig(outpath)
    plt.close(fig)

def main(args):
    inpath = "/eos/user/z/zhaom/htautau/SBI-Htt-EFT/python/data/ntuples_big.root"

    with uproot.open(inpath) as fin:
        if False:
            cutoff = 35
            plot_phicp_weight_cutoff(
                phicp=fin["Events;1"]["GenDressedElectronGenVisTauAngles_phicp"].array(),
                weights=fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_100p0_chl3_0p0"].array(),
                axis_label=r"$e\tau$ $\phi_{CP}$",
                cutoff=cutoff,
                outpath="etau_phicp_ceHIm_100_cutoff_{}.png".format(cutoff)
            )
            plot_phicp_weight_cutoff(
                phicp=fin["Events;1"]["GenDressedMuGenVisTauAngles_phicp"].array(),
                weights=fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_100p0_chl3_0p0"].array(),
                axis_label=r"$\mu\tau$ $\phi_{CP}$",
                cutoff=cutoff,
                outpath="mutau_phicp_ceHIm_100_cutoff_{}.png".format(cutoff)
            )
            plot_phicp_weight_cutoff(
                phicp=fin["Events;1"]["GenVisTauGenVisTauAngles_phicp"].array(),
                weights=fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_100p0_chl3_0p0"].array(),
                axis_label=r"$\tau\tau$ $\phi_{CP}$",
                cutoff=cutoff,
                outpath="tautau_phicp_ceHIm_100_cutoff_{}.png".format(cutoff)
            )

        if False:
            plot_lhetau_spin_ratio(
                spinid = fin["Events;1"]["LHETau_spinid"].array(),
                weights = [
                    fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_0p0_chl3_0p0"].array(),
                    fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_1p0_chl3_0p0"].array(),
                    fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_10p0_chl3_0p0"].array(),
                    fin["Events;1"]["LHEWeight_cHbox_0p0_cHDD_0p0_ceHRe_0p0_ceHIm_100p0_chl3_0p0"].array(),
                ],
                weight_values = [0, 1, 10, 100],
                axis_label = "ceHIm"
            )

        if True:
            labels = [
                ("GenDressedElectronGenVisTauAngles", r"$e\tau$", "etau"),
                ("GenDressedMuGenVisTauAngles", r"$\mu\tau$", "mutau"),
                ("GenVisTauGenVisTauAngles", r"$\tau\tau$", "tautau"),
            ]
            for branch_name, axis, prefix in labels:
                plot_phicp(
                    {
                        r"$\theta$" + " = {}".format(theta) : flatten_with_weights(
                            fin["Events;1"][branch_name + "_phicp"].array(),
                            fin["Events;1"]["TauSpinner_weight_cp_{}".format(theta.replace(".", "p"))].array()
                        ) for theta in ["0", "0.25","0.5"]
                    },
                    axis_label=axis + r" $\phi_{CP}$",
                    outpath=prefix + "_phicp.png"
                )

        if True:
            labels = {
                ("TauSpinner_weight_cp_" + theta.replace(".", "p"), r"$\theta = $" + theta) for theta in ["0", "0.5"]
            }
            plot_unweighted(
                {
                    axis : fin["Events;1"][branch].array() for branch, axis in labels
                },
                axis_label="Event weights",
                outpath="TauSpinner_weights.png",
                bounds=(0.1, 2.1)
            )

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    print("\nFinished with exit code:", main(parser.parse_args()))