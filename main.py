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
    
def makeHD3HD6table(df: pd.DataFrame):
    dt = pt.PrettyTable()
    dt.field_names = ["Task", "Participant", "Bugs Elicited", "Bug Desc. Accuracy", "Confidence", "Time (mm:ss)"]
    for task in hypotasks:
        for index, row in df.iterrows():
            dt.add_row([task,row["ID"],row[f"TestCases{task}"], row[f"Accuracy{task}"],row[f"Confidence{task}"],row[f"Elapsed{task}"]],divider=(index == df.index[-1]))
    return dt

def makeStepTransitionTable(dt: pt.PrettyTable | None, treatment: str, df: pd.DataFrame):
    # Setup the prettytable
    steps = ["S2","S3","S4","S5","S6","S7"]
    if(dt==None):
        dt = pt.PrettyTable()
        dt.field_names = ["Treatment","Current \ Next Step","S2","S3","S4","S5","S6","S7","Σ"]

    # Create the thisStep rows
    for thisStep in steps:
        rowData = [treatment,thisStep]
        rowSum = df["ThisStep"][(df["ThisStep"]==thisStep)].count()

        # Create the nextStep columns
        for nextStep in steps:
            value = df["ThisStep"][(df["ThisStep"]==thisStep) & (df["NextStep"]==nextStep)].count()
            rowData.append("--" if value==0 else f"{value} ({value/rowSum:.2%})")

        rowData.append(f"{rowSum} (100%)") # Sum column
        dt.add_row(rowData,divider=(thisStep==steps[-1]))

    # Summary row
    rowSum = df["NextStep"].count()
    rowData = ["","Σ"]
    for nextStep in steps:
        value = df["NextStep"][(df["NextStep"]==nextStep)].count()
        rowData.append("--" if value==0 else f"{value}")
    rowData.append(f"{rowSum}") # Sum column
    dt.add_row(rowData,divider=True)

    return dt

def makeStepSummaryTable(dt: pt.PrettyTable | None, df: pd.DataFrame, treatments: List[str], steps: List[str]):
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
    if(dt==None):
        dt = pt.PrettyTable()
        dt.field_names = ["Treatment","Session"] + steps

    for row in rows:
        dt.add_row(row=row["data"],divider=row["divider"])

    return dt

def makeIterationsTable(dt: pt.PrettyTable | None, df: pd.DataFrame, tasks: List[int], treatments: List[str]):
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
    if(dt==None):
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

def calcirr(dt: pt.PrettyTable | None, dataset: str, df: pd.DataFrame, rater1: str, rater2: str):
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

    # Build the results table
    breakRow = False
    if(dt==None):
        dt = pt.PrettyTable()
        dt.field_names = ["Dataset","Step","N","O","E","K","","YY","YN","NY","NN"]

    for step in steps:
        dt.add_row([dataset,step,irr[step]["N"],irr[step]["O"],f"{irr[step]['E']:.3f}",f"{irr[step]['K']:.3f}","",irr[step]["YY"],irr[step]["YN"],irr[step]["NY"],irr[step]["NN"]],divider=(step==steps[-1]))

    return dt

def main():
    print("")
    print("EXTRACTING THE ABSTRACT STEPS (§5)")
    print("----------------------------------")
    print("(R1) Coding Guide. See paper")

    print("")
    print("(R2) Abstract Steps. See paper")

    print("")
    print("APPLYING THE ABSTRACT STEPS (§6)")
    print("--------------------------------")

    print("(R3) Step transcripts (fixed intervals). See:")
    print("     ./nanofuzz/R3-StepTranscripts.csv")
    print("     ./hypothesis/R3-StepTranscripts.csv")

    print("")
    print("(R4) Step transcripts (variable intervals). See:")
    print("     ./nanofuzz/R4-StepTranscripts.csv")
    print("     ./hypothesis/R4-StepTranscripts.csv")

    print("")
    print("(R5) Inter-rater Reliability of Coding, by dataset and step")
    r5Table = calcirr(None,"Jest, NaNo",pd.read_csv("./nanofuzz/R3-StepTranscripts.csv"), "Author 3","Author 2")
    r5Table = calcirr(r5Table,"Hypothesis",pd.read_csv("./hypothesis/R3-StepTranscripts.csv"), "Author 1","Author 3")
    print(r5Table)

    print("")
    print("(R6) Abstract Step Transitions by treatment, current, next step")
    df = pd.read_csv("./nanofuzz/R6-StepTransitions.csv")
    r6Table = makeStepTransitionTable(None,"Jest",df[df["Session"].str.slice(-1)=="J"])
    r6Table = makeStepTransitionTable(r6Table,"NaNofuzz",df[df["Session"].str.slice(-1)=="A"])
    df = pd.read_csv("./hypothesis/R6-StepTransitions.csv")
    r6Table = makeStepTransitionTable(r6Table,"Hypothesis",df)
    print(r6Table)

    print("")
    print("(R7) Loop Iterations by treatment, session")
    r7Table = makeIterationsTable(None,pd.read_csv("./nanofuzz/data.csv"),nanotasks,nanotreatments)
    r7Table = makeIterationsTable(r7Table,pd.read_csv("./hypothesis/data.csv"),hypotasks,hypotreatments)
    print(r7Table)

    print("")
    print("(R8) Step Summary by treatment, session, step (times in hours:minutes:seconds)")
    r8Table=makeStepSummaryTable(None,pd.read_csv("./nanofuzz/R4-StepTranscripts.csv"),nanotreatments,["S2","S3","S4","S5","S6","S7"])
    r8Table=makeStepSummaryTable(r8Table,pd.read_csv("./hypothesis/R4-StepTranscripts.csv"),hypotreatments,["S2","S3","S4","S5","S6","S7"])
    print(r8Table)

    print("")
    print("Task Data for Hypothesis Study (mentioned in discussion)")
    print(makeHD3HD6table(pd.read_csv("./hypothesis/data.csv")))

if __name__ == "__main__":
    main()
