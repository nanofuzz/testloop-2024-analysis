#!/usr/bin/env python3

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as st
import prettytable as pt


def parse_time(t: str):
    m, s = t.split(":")
    return int(m) * 60 + int(s)

hypotasks = [1, 2]

def makeNR7table(df: pd.DataFrame):
    print("(NR7) Abstract Step Transitions: NaNofuzz")
    print(makeStepTransitionTable(df[df["Session"].str.slice(-1)=="A"]))
    print("")

    print("(NR7) Abstract Step Transitions: Jest")
    print(makeStepTransitionTable(df[df["Session"].str.slice(-1)=="J"]))
    print("")

    print("(NR7) Abstract Step Transitions: Jest + NaNofuzz")
    print(makeStepTransitionTable(df))
    print("")

def makeHD3HD6table(df: pd.DataFrame):
    print("(HD3-HD6) Raw Task Data")
    for task in hypotasks:
        dt = pt.PrettyTable()
        dt.field_names = ["Task", "Participant", "(HD3) Bugs Elicited", "(HD4) Bug Desc. Accuracy", "(HD5) Confidence)", "(HD6) Time (mm:ss)"]
        for index, row in df.iterrows():
            dt.add_row([task,row["ID"],row[f"TestCases{task}"], row[f"Accuracy{task}"],row[f"Confidence{task}"],row[f"Elapsed{task}"]])
        print(dt)
    print("")

def makeHR4table(df: pd.DataFrame):
    print("(HR4) Abstract Step Transitions")
    print(makeStepTransitionTable(df))
    print("")

def makeStepTransitionTable(df: pd.DataFrame):
    steps = ["S2","S3","S4","S5","S6","S7"]
    dt = pt.PrettyTable()
    dt.field_names = ["Current Step \ Next Step","S2","S3","S4","S5","S6","S7","Σ"]
    for thisStep in steps:
        rowData = [thisStep]
        rowSum = df["ThisStep"][(df["ThisStep"]==thisStep)].count()
        for nextStep in steps:
            value = df["ThisStep"][(df["ThisStep"]==thisStep) & (df["NextStep"]==nextStep)].count()
            rowData.append("--" if value==0 else f"{value} ({value/rowSum:.2%})")
        rowData.append(f"{rowSum} (100%)") # Sum column
        dt.add_row(rowData,divider=(thisStep=="S7"))

    # Summary row
    rowSum = df["NextStep"].count()
    rowData = ["Σ"]
    for nextStep in steps:
        value = df["NextStep"][(df["NextStep"]==nextStep)].count()
        rowData.append("--" if value==0 else f"{value}")
    rowData.append(f"{rowSum}") # Sum column
    dt.add_row(rowData)

    return dt

def makeHR5table(df: pd.DataFrame):
    print("(HR5) Loop Iterations by session")
    print(makeIterationsTable(df))
    print("")


def makeIterationsTable(df: pd.DataFrame):
    dt = pt.PrettyTable()
    dt.field_names = ["Session","Session Length (seconds)","Loop Iterations","Mean Seconds per Iteration"]

    for index, row in df.iterrows():
        for task in hypotasks:
            elapsedSeconds = parse_time(row[f"Elapsed{task}"])
            iterations = row[f"Iterations{task}"]
            dt.add_row([
                f"{row['ID']} Task {task}",
                elapsedSeconds,
                iterations,
                f"{elapsedSeconds/iterations:.0f}"
                ])
    return dt




def main():
    # NaNofuzz
    # - Step Transcripts (variable) (NR4) 
    #    --(NA5)-> Loop iterations (NR8)
    #    --(NA6)-> Step Summaries (NR9)

    print("")
    print("* * * NANOFUZZ USER STUDY SECONDARY ANALYSES * * *")
    print("--------------------------------------------------")
    print("")

    nanosteptrandf = pd.read_csv("./nanofuzz/NR7-StepTransitions.csv")
    makeNR7table(nanosteptrandf)

    #makeNA5table(hypodf)




    # Hypothesis
    # - Step Transcripts (variable) (HR2) 
    #    --(HA4)-> Step Summaries (HR6)

    print("")
    print("* * * HYPOTHESIS USER STUDY DATA ANALYSES * * *")
    print("-----------------------------------------------")
    print("")

    hypodf = pd.read_csv("./hypothesis/data.csv")
    makeHD3HD6table(hypodf)

    hyposteptrandf = pd.read_csv("./hypothesis/HR4-StepTransitions.csv")
    makeHR4table(hyposteptrandf)

    makeHR5table(hypodf)


if __name__ == "__main__":
    main()
