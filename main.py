#!/usr/bin/env python3

import datetime
import math
from typing import List
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as st
import prettytable as pt


hypotasks = [1, 2]
hypotreatments = ["Hypothesis"]

nanotasks = [1, 2, 3, 4, 5, 6]
nanotreatments = ["Jest","NaNofuzz"]


def parse_time(t: str):
    if(str(t)=="nan"):
        return 0
    
    colons = str(t).count(":")
    if(colons==1):
        m, s = t.split(":")
        return int(m) * 60 + int(s)
    elif(colons==2):
        h, m, s = t.split(":")
        return int(h) * 60 * 60 + int(m) * 60 + int(s)
    else:
        raise ValueError(f"Accepted time formats: m:s or h:m:s (value was:'{t}")
    
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
    # Setup the prettytable
    steps = ["S2","S3","S4","S5","S6","S7"]
    dt = pt.PrettyTable()
    dt.field_names = ["Current Step \ Next Step","S2","S3","S4","S5","S6","S7","Σ"]

    # Create the thisStep rows
    for thisStep in steps:
        rowData = [thisStep]
        rowSum = df["ThisStep"][(df["ThisStep"]==thisStep)].count()

        # Create the nextStep columns
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

def makeNR9table(df: pd.DataFrame):
    print("(NR9) Step Summary by treatment, session (times in hours:minutes:seconds)")
    print(makeStepSummaryTable(df,nanotreatments,["S2","S3","S4","S5","S6","S7"]))
    print("")

def makeHR6table(df: pd.DataFrame):
    print("(HR6) Step Summary by session (times in hours:minutes:seconds)")
    print(makeStepSummaryTable(df,hypotreatments,["S2","S3","S4","S5","S6","S7"]))
    print("")

def makeStepSummaryTable(df: pd.DataFrame, treatments: List[str], steps: List[str]):
    rows = [] # PrettyTable output rows
    data = {} # Accumulated step timings

    # Accumulate the step timing data by treatment, session, and step
    for index, row in df.iterrows():
        thistreatment = row["Treatment"]
        thissession = row["Session"]

        # Init the data structure for this treatment and session
        if(not thistreatment in data):
            data[thistreatment] = {}
        if(not thissession in data[thistreatment]):
            data[thistreatment][thissession] = {}
            for step in steps:
                data[thistreatment][thissession][step] = 0
                data[thistreatment][thissession]["total"] = 0
            
        # Accumulate the step times
        for step in steps:
            time = parse_time(row[step])
            data[thistreatment][thissession][step] += time
            data[thistreatment][thissession]["total"] += time

    # Build the table by treatment, session, and step
    for treatment in treatments:
        sessions = 0
        totals = {"total": 0}
        for step in steps:
            totals[step] = 0

        for session in data[treatment]:
            sessions+=1
            row = [
                treatment, 
                f"{session[0:3]} Task {session[-1]}"
            ]
            for step in steps:
                steptime = data[treatment][session][step]
                sessiontime = data[treatment][session]['total']

                totals[step]+=steptime
                totals["total"]+=steptime
                row.append(
                    f"{str(datetime.timedelta(seconds=steptime))} ({steptime / sessiontime:.0%})"
                )
            rows.append({
                "data": row, 
                "divider": False
            })

        # Add the totals row for this treatment if we output any
        # table rows for this treatment
        if(sessions>0):
            rows[-1]["divider"]=True # Add the divider to the prior row
            row = [
                    "",
                    "Σ"
                ] 
            for step in steps:
                row.append(
                    f"{str(datetime.timedelta(seconds=totals[step]))} ({(totals[step] / totals['total']):.0%})"
                )
            rows.append({
                "data": row,
                "divider": True
            })

    # Create and fill the prettytable
    dt = pt.PrettyTable()
    dt.field_names = ["Treatment","Session"] + steps
    for row in rows:
        dt.add_row(row=row["data"],divider=row["divider"])

    return dt

def makeHR5table(df: pd.DataFrame):
    print("(HR5) Loop Iterations by session")
    print(makeIterationsTable(df,hypotasks,hypotreatments))
    print("")

def makeNR8table(df: pd.DataFrame):
    print("(NR8) Loop Iterations by treatment, session")
    print(makeIterationsTable(df,nanotasks,nanotreatments))
    print("")

def makeIterationsTable(df: pd.DataFrame, tasks: List[int], treatments: List[str]):
    # To add a divider above the "mean" lines, we need to add a divider to the 
    # preceding row. To do this, we buffer the table rows here so that we can
    # change the divider flag if needed.
    rows = []

    # Function to add the "mean" summary row at the end of each treatment
    def addSummaryRow():
        nonlocal sessions, seconds, loops, dt, rows
        rows[-1]["divider"]=True # Add a divider to the previous row
        rows.append({
            "data": 
                [
                    "",
                    "Mean",
                    f"{(seconds/sessions):.0f}",
                    f"{(loops/sessions):.1f}",
                    f"{seconds/loops:.0f}"
                ], 
            "divider": True
        })
        # Reset the summary accumulators
        sessions = 0
        seconds = 0
        loops = 0

    # Does the dataset have multiple interventions (if not, we don't want
    # to look for the non-existent column)
    hasIntervention:bool = len(treatments)-1

    # Create and define the prettytable
    dt = pt.PrettyTable()
    dt.field_names = ["Treatment","Session","Session Length (seconds)","Loop Iterations","Mean Seconds per Iteration"]

    # Initialize the summary data for each treatment
    sessions = 0
    seconds = 0
    loops = 0

    # Loop over each treatment in the dataset
    for treatment in range(len(treatments)):
        # If we're processing a new treatment and have processed sessions since we
        # last wrote a summary row, then write a summary row.
        if(sessions > 0):
            addSummaryRow()

        # Loop over each participant
        for index, row in df.iterrows():
            # Loop over each participant session
            for task in tasks:
                tasktreatment = hasIntervention and row[f"Intervention{task}"]
                elapsedSeconds: int = parse_time(row[f"Elapsed{task}"])
                iterations: int = row[f"Iterations{task}"]

                if(tasktreatment == treatment and not(math.isnan(iterations))):
                    # Accumulate summary data for each tretment 
                    sessions+=1
                    seconds+=elapsedSeconds
                    loops+=iterations

                    rows.append({
                        "data": [
                            treatments[tasktreatment],
                            f"{row['ID']} Task {task}",
                            elapsedSeconds,
                            int(iterations),
                            f"{elapsedSeconds/iterations:.0f}"
                        ],
                        "divider": False
                    })

    # Create the summary row for the last treatment processed
    if(sessions > 0):
        addSummaryRow()

    # Copy the rows from the buffer into the prettytable
    for row in rows:
        dt.add_row(
            row=row["data"],
            divider=row["divider"]
        )
    return dt

def makeNR5table(df: pd.DataFrame):
    print("(NR5) Inter-rater Reliability")
    calcirr(df, "Author 3","Author 2")  #!!! SWAP
    print("")
    
def makeHR3table(df: pd.DataFrame):
    print("(HR3) Inter-rater Reliability")
    calcirr(df, "Author 1","Author 3")
    print("")
    
def calcirr(df: pd.DataFrame, rater1: str, rater2: str):
    irr = {}
    sessions = {}
    steps = ["S1","S2","S3","S4","S5","S6","S7"]
    for step in steps:
        irr[step] = {
            "YY": 0, # Count of: YES, YES (agreement)
            "YN": 0, # Count of: YES, NO  (disagreement)
            "NY": 0, # Count of: NO , YES (disagreement)
            "NN": 0, # Count of: NO , NO  (agreement)
        }

    # First tally the number of agreements and disagreements we have for
    # the judgements from the first rater
    for index, row in df.iterrows():
        # Count the number of records for each session and rater
        if(row["Session"] not in sessions):
            sessions[row["Session"]] = {}
            sessions[row["Session"]][rater1] = 0
            sessions[row["Session"]][rater2] = 0
        sessions[row["Session"]][row["Rater"]]+=1

        # Select records only of the first rater (we find rater 2's below)
        if(row["Rater"]==rater1):
            # Retrieve the corresponding judgement from the second rater
            matchrow = df[(df["Rater"]==rater2) & (df["Session"]==row["Session"]) & (df["Treatment"]==row["Treatment"]) & (df["Time (Recording)"]==row["Time (Recording)"])]

            if(len(matchrow)==0): # No record to compare against
                raise ValueError(f"No '{rater2}' IRR step record found corresponding to: {row}")
            elif(len(matchrow)>1): # Too many records match
                raise ValueError(f"Duplicate step records found: {matchrow}")
            else:
                for step in steps:
                    if(row[step]=="X"):
                        if(matchrow[step].item()=="X"):
                            irr[step]["YY"]+=1 
                        else:
                            irr[step]["YN"]+=1 
                    else:
                        if(matchrow[step].item()=="X"):
                            irr[step]["NY"]+=1 
                        else:
                            irr[step]["NN"]+=1 

    # Ensure the number of observations for rated sessions is the same
    for session in sessions:
        if(sessions[session][rater1] > 0 and sessions[session][rater1] != sessions[session][rater2]):
            raise ValueError(f"Inconsistent number of records for session {session}: '{rater1}' has {sessions[session][rater1]} but '{rater2}' has {sessions[session][rater2]}.")

    # Calculate Cohen's Kappa for each step
    for step in steps:
        # N = Count of total cases
        irr[step]["N"] = irr[step]["YY"] + irr[step]["YN"] + irr[step]["NY"] + irr[step]["NN"]

        # O = Observed cases w/agreement
        irr[step]["O"] = irr[step]["YY"] + irr[step]["NN"]

        # E = Expected agreement
        irr[step]["E"] = (
            (#               YY agreement row total * YY agreement column total           / total number of cases
                (irr[step]["YY"] + irr[step]["YN"]) * (irr[step]["YY"] + irr[step]["NY"]) / irr[step]["N"]
            ) + (#           NN agreement row total * NN agreement column total           / total number of cases
                (irr[step]["NY"] + irr[step]["NN"]) * (irr[step]["YN"] + irr[step]["NN"]) / irr[step]["N"]
            )
        )

        # K = Cohen's Kappa (O-E)/(N-E)
        if(irr[step]["N"]==irr[step]["E"]):
            irr[step]["K"] = 1 # Avoid divide by zero when E=N (e.g., perfect agreement)
        else:
            irr[step]["K"] = (irr[step]["O"] - irr[step]["E"]) / (irr[step]["N"] - irr[step]["E"]) 

    # Print the results table
    dt = pt.PrettyTable()
    dt.field_names = ["Step","N","O","E","K","","YY","YN","NY","NN"]
    for step in steps:
        dt.add_row([step,irr[step]["N"],irr[step]["O"],f"{irr[step]['E']:.3f}",f"{irr[step]['K']:.3f}","",irr[step]["YY"],irr[step]["YN"],irr[step]["NY"],irr[step]["NN"]])
    print(dt)

def main():
    print("")
    print("NANOFUZZ USER STUDY SECONDARY ANALYSES")
    print("--------------------------------------")
    print("")

    nanostepfixdf = pd.read_csv("./nanofuzz/NR3-StepTranscripts.csv")
    makeNR5table(nanostepfixdf)

    nanosteptrandf = pd.read_csv("./nanofuzz/NR7-StepTransitions.csv")
    makeNR7table(nanosteptrandf)

    nanodf = pd.read_csv("./nanofuzz/data.csv")
    makeNR8table(nanodf)

    nanostepdf = pd.read_csv("./nanofuzz/NR4-StepTranscripts.csv")
    makeNR9table(nanostepdf)

    print("")
    print("HYPOTHESIS USER STUDY DATA ANALYSES")
    print("-----------------------------------")
    print("")

    hypodf = pd.read_csv("./hypothesis/data.csv")
    makeHD3HD6table(hypodf)

    hypostepfixdf = pd.read_csv("./hypothesis/HR1-StepTranscripts.csv")
    makeHR3table(hypostepfixdf)

    hyposteptrandf = pd.read_csv("./hypothesis/HR4-StepTransitions.csv")
    makeHR4table(hyposteptrandf)
    makeHR5table(hypodf)

    hypostepdf = pd.read_csv("./hypothesis/HR2-StepTranscripts.csv")
    makeHR6table(hypostepdf)

if __name__ == "__main__":
    main()
