from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from TransPlaceholder import *
import csv
from MonoAminoAndMods import *
import multiprocessing
from multiprocessing import Queue
import time
import sys
# import h5py
import json
import logging
from MGFMain import *
import atexit

TRANS = "Trans"
LINEAR = "Linear"
CIS = "Cis"

logging.basicConfig(level = logging.DEBUG, format = '%(message)s')
#logging.disable(logging.INFO)

mgfData = None

class Fasta:

    """
    Class that represents the input from a fasta file
    """

    def __init__(self, inputFile):
        self.inputFile = inputFile
        #self.entries = len(seqDict)
        self.allProcessList = []

    def generateOutput(self, mined, maxed, overlapFlag, transFlag, cisFlag, linearFlag, csvFlag, modList,
                       maxDistance, outputPath, chargeFlags, mgfObj:

        """
        Function that literally combines everything to generate output
        """
        self.allProcessList = []

        if transFlag:
            finalPeptide = combinePeptides(self.seqDict)
            transProcess = multiprocessing.Process(target=transOutput, args=(finalPeptide, mined, maxed, overlapFlag,
                                                                             modList, outputPath, chargeFlags))
            #allProcessList.append(transProcess)
            self.allProcessList.append(transProcess)
            # combined = {'combined': combined}
            # with open('output.txt', 'wb') as file:
            # file.write(json.dumps(combined))  # use `json.loads` to do the reverse

        if cisFlag:
            cisProcess = multiprocessing.Process(target=cisAndLinearOutput, args=(self.inputFile, CIS, mined, maxed,
                                                                                  overlapFlag, csvFlag, modList,
                                                                                  maxDistance,
                                                                                  outputPath, chargeFlags, mgfObj, modTable))
            self.allProcessList.append(cisProcess)
            cisProcess.start()

        if linearFlag:

            linearProcess = multiprocessing.Process(target=cisAndLinearOutput, args=(self.inputFile, LINEAR, mined,
                                                                                     maxed, overlapFlag, csvFlag,
                                                                                     modList, maxDistance,
                                                                                     outputPath, chargeFlags, mgfObj, modTable))
            self.allProcessList.append(linearProcess)
            linearProcess.start()

        for process in self.allProcessList:
            process.join()


def cisAndLinearOutput(inputFile, spliceType, mined, maxed, overlapFlag, csvFlag,
                       modList, maxDistance, outputPath, chargeFlags, mgfObj, childTable):

    """
    Process that is in charge for dealing with cis and linear. Creates sub processes for every protein to compute
    their respective output
    """



    finalPath = None

    # Open the csv file if the csv file is selected
    if csvFlag:
        finalPath = getFinalPath(outputPath, spliceType)
        open(finalPath, 'w')

    num_workers = multiprocessing.cpu_count()

    # Don't need all processes for small file?
    # if len(seqDict) < num_workers:
    #     num_workers = len(seqDict)

    # Used to lock write access to file
    lockVar = multiprocessing.Lock()

    toWriteQueue = multiprocessing.Queue()
    pool = multiprocessing.Pool(processes=num_workers, initializer=processLockInit, initargs=(lockVar, toWriteQueue,
                                                                                              mgfObj, childTable))

    writerProcess = multiprocessing.Process(target=writer, args=(toWriteQueue, outputPath))
    writerProcess.start()

    #for key, value in seqDict.items():
    with open(inputFile, "rU") as handle:
        for record in SeqIO.parse(handle, 'fasta'):
            seq = str(record.seq)
            seqId = record.name


            seqId = seqId.split('|')[1]
            logging.info(spliceType + " process started for: " + seq[0:5])
            # Start the processes for each protein with the targe function being genMassDict
            pool.apply_async(genMassDict, args=(spliceType, seqId, seq, mined, maxed, overlapFlag,
                                                csvFlag, modList, maxDistance, finalPath, chargeFlags))


    pool.close()
    pool.join()

    toWriteQueue.put('stop')
    writerProcess.join()
    logging.info("All " + spliceType + " !joined")


def genMassDict(spliceType, protId, peptide, mined, maxed, overlapFlag, csvFlag, modList,
                maxDistance, finalPath, chargeFlags):

    """
    Compute the peptides for the given protein
    """
    start = time.time()

    # Get the initial peptides and their positions
    combined, combinedRef = outputCreate(spliceType, peptide, mined, maxed, overlapFlag, maxDistance)

    # Convert it into a dictionary that has a mass
    massDict = combMass(combined, combinedRef)
    # Apply mods to the dictionary values and update the dictionary

    massDict = applyMods(massDict, modList)

    # Add the charge information along with their masses
    chargeIonMass(massDict, chargeFlags)

    # Get the positions in range form, instead of individuals (0,1,2) -> (0-2)
    massDict = editRefMassDict(massDict)

    # If there is an mgf file AND there is a charge selected
    if mgfData is not None and True in chargeFlags:
        #fulfillPpmReq(mgfObj, massDict)
        matchedPeptides = generateMGFList(protId, mgfData, massDict, modList)
        genMassDict.toWriteQueue.put(matchedPeptides)

    if mgfData is None:
        allPeptides = getAllPep(massDict)
        genMassDict.toWriteQueue.put(allPeptides)

    # If csv is selected, write to csv file
    if csvFlag:
        logging.info("Writing locked :(")
        lock.acquire()

        writeToCsv(massDict, protId, finalPath, chargeFlags)
        lock.release()
        logging.info("Writing released!")

    end = time.time()

    logging.info(peptide[0:5] + ' took: ' + str(end-start) + ' for ' + spliceType)

def getAllPep(massDict):

    allPeptides = set()
    for key, value in massDict.items():
        if not key.isalpha():
            alphaKey = modToPeptide(key)
        else:
            alphaKey = key
        allPeptides.add(alphaKey)
    return allPeptides

def writer(queue, outputPath):
    seenPeptides = {}
    saveHandle = str(outputPath) + "/NewOutput1.fasta"
    print(saveHandle)
    with open(saveHandle, "w") as output_handle:
        while True:
            matchedPeptides = queue.get()



            if matchedPeptides == 'stop':
                logging.info("ALL LINEAR COMPUTED, STOP MESSAGE SENT")
                break


            for key, value in matchedPeptides.items():
                if key not in seenPeptides.keys():
                    seenPeptides[key] = [value]
                else:
                    seenPeptides[key].append(value)



        logging.info("Writing to fasta")
        SeqIO.write(createSeqObj(seenPeptides), output_handle, "fasta")


def fulfillPpmReq(mgfObj, massDict):
    """
    Assumption there are charges. Get the peptides that match, and writes them to the output fasta file
    """

    matchedPeptides = generateMGFList(mgfObj, massDict)

    lock.acquire()
    logging.info("Writing to fasta")
    with open("OutputMaster.fasta", "a") as output_handle:
        SeqIO.write(createSeqObj(matchedPeptides), output_handle, "fasta")

    lock.release()
    logging.info("Writing complete")


def createSeqObj(matchedPeptides):
    """
    Given the set of matchedPeptides, converts all of them into SeqRecord objects and passes back a generator
    """
    count = 1
    seqRecords = []
    for sequence, value in matchedPeptides.items():

        finalId = "ipd|pep"+str(count)+';'

        for protein in value:
            finalId+=protein+';'

        yield SeqRecord(Seq(sequence), id=finalId, description="")

        count += 1

    return seqRecords


def outputCreate(spliceType, peptide, mined, maxed, overlapFlag, maxDistance):

    # Splits eg: ['A', 'AB', 'AD', 'B', 'BD']
    # SplitRef eg: [[0], [0,1], [0,2], [1], [1,2]]
    # Produces splits and splitRef arrays which are passed through combined
    splits, splitRef = splitDictPeptide(spliceType, peptide, mined, maxed)
    combined, combinedRef = None, None

    if spliceType == CIS:

        # get the linear set to ensure no linear peptides are added to cis set. ( Redoing is a little redundant,
        # need to find something better )
        combineLinear, combineLinearRef = splitDictPeptide(LINEAR, peptide, mined, maxed)

        combineLinearSet = set(combineLinear)

        # combined eg: ['ABC', 'BCA', 'ACD', 'DCA']
        # combinedRef eg: [[0,1,2], [1,0,2], [0,2,3], [3,2,0]]
        # pass splits through combined overlap peptide and then delete all duplicates

        combined, combinedRef = combineOverlapPeptide(splits, splitRef, mined, maxed, overlapFlag, maxDistance,
                                                      combineLinearSet)
    elif spliceType == LINEAR:

        # Explicit change for high visibility regarding what's happening
        combined, combinedRef = splits, splitRef

    combined, combinedRef = removeDupsQuick(combined, combinedRef)

    return combined, combinedRef


def applyMods(combineModlessDict, modList):

    """
    Calls the genericMod function and accesses the modification table to
    append modified combinations to the end of the combination dictionary
    """

    modNo = 0
    for mod in modList:
        # Keep track of which modification is taking place
        modNo += 1

        # Don't need to worry about it if no modification!
        if mod != 'None':
            # Get the list of modifications taking place
            aminoList = finalModTable[mod]
           
            # Go through each character in the modification one by one
            for i in range(0, len(aminoList) - 1):

                char = aminoList[i]
                massChange = aminoList[-1]
                # get the dictionary of mods and their mass
                modDict = genericMod(combineModlessDict, char, massChange, str(modNo))
                # Add it to the current list!
                combineModlessDict.update(modDict)
    return combineModlessDict


def genericMod(combineModlessDict, character, massChange, modNo):

    """
    From the modless dictionary of possible combinations, this function returns a
    dictionary containing all the modifications that arise from changing character. The
    key of the output is simply the modified peptide, and the value is the mass which
    results as set by massChange
    """
    # A, B, C  convert to ai, bi, ci where i is the modNo
    modDict = {}

    # Go through each combination and mod it if necessary
    for string in combineModlessDict.keys():

        currentMass = combineModlessDict[string][0]
        currentRef = combineModlessDict[string][1]

        # Only need to mod it if it exists (ie : A in ABC)
        if character in string:

            numOccur = string.count(character)
            # Generate all permutations with the mods
            for j in range(0, numOccur):
                temp = string
                for i in range(0, numOccur - j):
                    newMass = currentMass + (i + 1) * massChange
                    temp = nth_replace(temp, character, character.lower() + modNo, j + 1)

                    modDict[temp] = [newMass, currentRef]

    return modDict


def splitDictPeptide(spliceType, peptide, mined, maxed):

    """
    Inputs: peptide string, max length of split peptide.
    Outputs: all possible splits that could be formed that are smaller in length than the maxed input
    """

    # Makes it easier to integrate with earlier iteration where linearFlag was being passed as an external flag
    # instead of spliceType
    linearFlag = spliceType == LINEAR
    length = len(peptide)

    # splits will hold all possible splits that can occur
    splits = []
    # splitRef will hold a direct reference to the characters making up each split string: for starting peptide ABC,
    # the split AC = [0,2]
    splitRef = []

    # embedded for loops build all possible splits
    for i in range(0, length):

        character = peptide[i]
        toAdd = ""
        # add and append first character and add and append reference number which indexes this character

        toAdd += character
        ref = list([i+1])
        temp = list(ref)  # use list because otherwise shared memory overwrites

        # linear flag to ensure min is correct for cis and trans
        if linearFlag and minSize(toAdd, mined):

            # Don't need to continue this run as first amino acid is unknown X
            if 'X' in toAdd or 'U' in toAdd:
                continue
            else:
                splits.append(toAdd)
                splitRef.append(temp)

        elif not linearFlag and 'X' not in toAdd and 'U' not in toAdd:
            splits.append(toAdd)
            splitRef.append(temp)

        # iterates through every character after current and adds it to the most recent string if max size
        # requirement is satisfied
        for j in range(i + 1, length):
            toAdd += peptide[j]
            if linearFlag:
                ref.append(j+1)
                if maxSize(toAdd, maxed):
                    if minSize(toAdd, mined):

                        # All future splits will contain X if an X is found in the current run, hence break
                        if 'X' in toAdd or 'U' in toAdd:
                            break
                        splits.append(toAdd)
                        temp = list(ref)
                        splitRef.append(temp)
                else:
                    break

            else:
                if maxSize(toAdd, maxed-1):
                    # All future splits will contain X if an X is found in the current run, hence break
                    if 'X' in toAdd or 'U' in toAdd:
                        break
                    splits.append(toAdd)
                    ref.append(j+1)
                    temp = list(ref)
                    splitRef.append(temp)
                else:
                    break

    return splits, splitRef


def combineOverlapPeptide(splits, splitRef, mined, maxed, overlapFlag, maxDistance, combineLinearSet=None):

    """
    Input: splits: list of splits, splitRef: list of the character indexes for splits, mined/maxed: min and max
    size requirements, overlapFlag: boolean value true if overlapping combinations are undesired.
    Output: all combinations of possible splits which meets criteria
    """

    # initialise combinations array to hold the possible combinations from the input splits
    combModless = []
    combModlessRef = []
    # iterate through all of the splits and build up combinations which meet min/max/overlap criteria
    for i in range(0, len(splits)):

        # toAdd variables hold temporary combinations for insertion in final matrix if it meets criteria
        toAddForward = ""

        toAddReverse = ""

        for j in range(i + 1, len(splits)):
            # create forward combination of i and j
            toAddForward += splits[i]
            toAddForward += splits[j]
            addForwardRef = splitRef[i] + splitRef[j]
            toAddReverse += splits[j]
            toAddReverse += splits[i]
            addReverseRef = splitRef[j] + splitRef[i]

            # max, min and max distance checks combined into one function for clarity for clarity
            if combineCheck(toAddForward, mined, maxed, splitRef[i], splitRef[j], maxDistance):

                # V. messy, need a way to get better visual
                if overlapFlag:
                    if overlapComp(splitRef[i], splitRef[j]):
                        if linearCheck(toAddForward, combineLinearSet):
                            combModless.append(toAddForward)
                            combModlessRef.append(addForwardRef)
                        if linearCheck(toAddReverse, combineLinearSet):
                            combModless.append(toAddReverse)
                            combModlessRef.append(addReverseRef)

                else:
                    if linearCheck(toAddForward, combineLinearSet):
                        combModless.append(toAddForward)
                        combModlessRef.append(addForwardRef)
                    if linearCheck(toAddReverse, combineLinearSet):
                        combModless.append(toAddReverse)
                        combModlessRef.append(addReverseRef)

            elif maxDistCheck(splitRef[i], splitRef[j], maxDistance):
                break

            toAddForward = ""
            toAddReverse = ""

    return combModless, combModlessRef


def chargeIonMass(massDict, chargeFlags):

    """
    chargeFlags: [True, False, True, False, True]
    """

    for key, value in massDict.items():
        chargeAssoc = {}
        for z in range(0, len(chargeFlags)):

            if chargeFlags[z]:
                chargeMass = massCharge(value[0], z+1)  # +1 for actual value
                chargeAssoc[z+1] = chargeMass
        value.append(chargeAssoc)


def massCharge(predictedMass, z):
    chargeMass = (predictedMass + (z * 1.00794))/z
    return chargeMass


def writeToCsv(massDict, header, finalPath, chargeFlags):

    chargeHeaders = getChargeIndex(chargeFlags)

    with open(finalPath, 'a', newline='') as csv_file:

        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow([header, ' ', ' '])
        headerRow = ['Peptide', 'Mass', 'Positions']

        for chargeIndex in chargeHeaders:

            headerRow.append('+' + str(chargeIndex+1))

        writer.writerow(headerRow)
        for key, value in massDict.items():
            infoRow = [key, value[0], value[1]]
            for chargeIndex in chargeHeaders:
                chargeMass = value[2][chargeIndex+1]
                infoRow.append(str(chargeMass))
            writer.writerow(infoRow)
            # BREAK FOR TESTING!!!!!
            # break;


def getChargeIndex(chargeFlags):
    chargeHeaders = [i for i, e in enumerate(chargeFlags) if e]
    return chargeHeaders


def maxDistCheck(ref1, ref2, maxDistance):
    if maxDistance == 'None':
        return True
    valid = ref2[-1] - ref1[0]

    if valid > maxDistance:
        return False
    return True


def maxSize(split, maxed):

    """
    ensures length of split is smaller than or equal to max
    """

    if len(split) > maxed:
        return False
    return True


def minSize(split, mined):

    """
    ensures length of split is greater than min
    """

    if len(split) < mined:
        return False
    return True


def combineCheck(split, mined, maxed, ref1, ref2, maxDistance='None'):
    booleanCheck = maxSize(split, maxed) and minSize(split, mined) and maxDistCheck(ref1, ref2, maxDistance)
    return booleanCheck


def linearCheck(toAdd, combinedLinearSet):
    if toAdd in combinedLinearSet:
        return False
    return True


def overlapComp(ref1, ref2):

    """
    checks if there is an intersection between two strings. Likely input it the splitRef data.
    Outputs True if no intersection
    overlapComp needs to delete paired reference number if being applied to the splits output
    """

    S1 = set(ref1)
    S2 = set(ref2)
    if len(S1.intersection(S2)) == 0:
        return True
    return False


def addSequenceList(input_file):

    """
    input_file is the file path to the fasta file.
    The function reads the fasta file into a dictionary with the format {proteinRef: protein}
    """

    fasta_sequences = SeqIO.parse(open(input_file), 'fasta')
    sequenceDictionary = {}
    for fasta in fasta_sequences:
        name, sequence = fasta.id, str(fasta.seq)


        name = name.split('|')[1]

        sequenceDictionary[name] = sequence
    return sequenceDictionary


def combinePeptides(seqDict):

    """
    combines an array of strings into one string. Used for ultimately segments from multiple peptides
    """

    dictlist = []
    for key, value in seqDict.items():
        dictlist.append(value)

    finalPeptide = ''.join(dictlist)
    return finalPeptide


def removeDupsQuick(seq, seqRef):

    seen = set()
    seen_add = seen.add
    initial = []
    initialRef = []
    # initial = [x for x in seq if not (x in seen or seen_add(x))]
    for i in range(0, len(seq)):
        if not (seq[i] in seen or seen_add(seq[i])):
            initial.append(seq[i])
            initialRef.append(seqRef[i])

    return initial, initialRef


def combMass(combine, combineRef):
    massDict = {}
    for i in range(0, len(combine)):
        totalMass = 0
        for j in range(0, len(combine[i])):
            totalMass += monoAminoMass[combine[i][j]]
        totalMass += H20_MASS
        massRefPair = [totalMass, combineRef[i]]
        massDict[combine[i]] = massRefPair
    return massDict


def changeRefToDash(ref):
    newRef = []
    for i in range(0,len(ref)):
        refVal = ref[i]
        # check if last element reached and thus input is linear
        if i == len(ref)-1:
            newLinRef = str(ref[0]) + ' - ' + str(ref[-1])
            newRef = [newLinRef]
            return newRef
        # otherwise, check if the next element is still sequential, and if so continue for loop
        if refVal + 1 == ref[i+1]:
            continue
        else:
            if i == 0:
                newStrRef1 = str(ref[0])
            else:
                newStrRef1 = str(ref[0]) + "-" + str(ref[i])
            if i + 1 == len(ref) - 1:
                newStrRef2 = str(ref[-1])
            else:
                newStrRef2 = str(ref[i+1]) + "-" + str(ref[-1])

            newRef = [newStrRef1, newStrRef2]
            return newRef


def editRefMassDict(massDict):
    for key, value in massDict.items():
        refNew = changeRefToDash(value[1])
        value[1] = refNew
    return massDict


def getFinalPath(outputPath, spliceType):
    finalPath = str(outputPath) + '/' + spliceType + '.csv'
    return finalPath


def nth_replace(string, old, new, n=1, option='only nth'):

    # https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
    """
    This function replaces occurrences of string 'old' with string 'new'.
    There are three types of replacement of string 'old':
    1) 'only nth' replaces only nth occurrence (default).
    2) 'all left' replaces nth occurrence and all occurrences to the left.
    3) 'all right' replaces nth occurrence and all occurrences to the right.
    """

    if option == 'only nth':
        left_join = old
        right_join = old
    elif option == 'all left':
        left_join = new
        right_join = old
    elif option == 'all right':
        left_join = old
        right_join = new
    else:
        print("Invalid option. Please choose from: 'only nth' (default), 'all left' or 'all right'")
        return None
    groups = string.split(old)
    nth_split = [left_join.join(groups[:n]), right_join.join(groups[n:])]
    return new.join(nth_split)


def processLockInit(lockVar, toWriteQueue, mgfObj, childTable):

    """
    Designed to set up a global lock for a child processes (child per protein)
    """

    global lock
    lock = lockVar
    global mgfData
    mgfData = mgfObj
    global finalModTable
    finalModTable = childTable
    genMassDict.toWriteQueue = toWriteQueue




