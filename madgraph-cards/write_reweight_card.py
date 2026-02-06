import argparse

# python write_reweight_card.py out.dat cHbox,cHDD,ceHRe,ceHIm,chl3,cHW,cHB,cHWB,cHWtil,cHBtil,cHWBtil
def main(args):
    fname = args.filename
    coeffs = args.coefficients.split(",")

    coeff_values = [[0] * len(coeffs)]
    for icoeff in range(len(coeffs)):
        p = [0] * len(coeffs)
        m = list(p)

        p[icoeff] = 1
        m[icoeff] = -1

        coeff_values += [p, m]

    for icoeff in range(len(coeffs) - 1):
        for jcoeff in range(icoeff+1, len(coeffs)):
            pp = [0] * len(coeffs)
            pm = list(pp)
            mp = list(pp)
            mm = list(pp)

            pp[icoeff] = 1
            pp[jcoeff] = 1
            pm[icoeff] = 1
            pm[jcoeff] = -1
            mp[icoeff] = -1
            mp[jcoeff] = 1
            mm[icoeff] = -1
            mm[jcoeff] = -1

            coeff_values += [pp, pm, mp, mm]

    lines = ["change rwgt_dir rwgt\n", "change helicity True\n"]
    print("[")
    for cval_set in coeff_values:
        header = []
        block_lines = []
        for cname, cval in zip(coeffs, cval_set):
            header.append("{}_{:.1f}".format(cname, cval))
            block_lines.append("set {} {:.1f}\n".format(cname, cval))

        rw_name = "_".join(header).replace(".", "p").replace("-", "m")
        lines.append("launch --rwgt_name=" + rw_name + "\n")
        lines += block_lines

        print('    "{}",'.format(rw_name))
    print("]")

    with open(fname, "w") as fout:
        fout.writelines(lines)

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("coefficients")
    print("\nFinished with exit code:", main(parser.parse_args()))