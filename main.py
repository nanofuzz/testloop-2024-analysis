#!/usr/bin/env python3

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as st


def parse_time(t: str):
    m, s = t.split(":")
    return int(m) * 60 + int(s)


tasks = [1, 2]


def main():
    # NaNofuzz
    # - Step Transcripts (variable) (NR4) 
    #    --(NA4)-> Abstract Step Transitions (NR7)
    #    --(NA5)-> Loop iterations (NR8)
    #    --(NA6)-> Step Summaries (NR9)

    # Hypothesis
    # - Step Transcripts (variable) (HR2) 
    #    --(HA2)-> Abstract Step Transitions (HR4)
    #    --(HA3)-> Loop iterations (HR5)
    #    --(HA4)-> Step Summaries (HR6)

    print("nothing here yet")
    hypodf = pd.read_csv("./hypothesis/data.csv")


if __name__ == "__main__":
    main()
