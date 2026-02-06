import argparse

def main(args):
    fname = args.file_name

    with open(fname, "r") as fin:
        lines = fin.readlines()

    print("named_weights = [")
    for l in lines:
        if l.startswith("launch --rwgt_name="):
            rw_name = l.replace("launch --rwgt_name=", "").replace("\n", "")
            print('    "{}",'.format(rw_name))
    print("]")

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name")
    print("\nFinished with exit code:", main(parser.parse_args()))