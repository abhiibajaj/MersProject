# comment for branch
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QTabWidget, QVBoxLayout, \
                            QFileDialog, QGridLayout, QLabel, QComboBox, QCheckBox, QMessageBox, QDesktopWidget
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot
from Mers import *


# pyinstaller MersGUI --> this command from the relevant file location creates executable file

# Move to mers
modificationList = ['4-hydroxynonenal (HNE)', 'Acetylation (K)', 'Beta-methylthiolation', 'Carbamidomethylation',
                    'Carboxylation (E)', 'Carboxymethyl', 'Citrullination', 'Deamidation (NQ)', 'Dimethylation(KR)',
                    'Dioxidation (M)', 'FAD', 'Farnesylation', 'Geranyl-geranyl', 'Guanidination', 'HexNAcylation (N)',
                    'Hexose (NSY)', 'Lipoyl', 'Methylation(KR)', 'Methylation(others)', 'Oxidation (HW)',
                    'Oxidation (M)', 'Palmitoylation', 'Phosphopantetheine', 'Phosphorylation (HCDR)',
                    'Phosphorylation (STY)', 'Propionamide', 'Pyridoxal phosphate', 'S-pyridylethylation',
                    'Sulfation', 'Sulphone', 'Ubiquitin', 'Ubiquitination']


class App(QMainWindow):
    # App serves as the parent class for the embedded MyTableWidget

    # Initialisation of main window class
    def __init__(self):
        super().__init__()
        self.title = 'Peptide Splicer'
        self.left = 500
        self.fastaTest = False
        self.outputPath = ""
        self.statusbar = self.statusBar()

        self.center()

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()

    # center function is called to centre the main window on the screen
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


# MyTableWidget class is the child of the App class. It holds the tabs where most of the GUI functionality occurs
class MyTableWidget(QWidget):

    # Initialisation of table child
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.fasta = None

        # Initialisation of two tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs to table class (self)
        self.tabs.addTab(self.tab1, "Select File and Path")
        self.tabs.addTab(self.tab2, "Input Parameters")

        # Creation of tab layout and widgets within tab
        self.tab1.layout = QVBoxLayout(self)

        self.pushButton1 = QPushButton("Select File")
        self.pushButton1.clicked.connect(self.uploadFasta)

        self.pushButton2 = QPushButton("Select Save Location")
        self.pushButton2.clicked.connect(self.outputPath)

        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.layout.addWidget(self.pushButton2)

        self.tab1.setLayout(self.tab1.layout)

        # Create second tab layout and widgets within each tab
        self.tab2.layout = QGridLayout(self)
        self.tab2.layout.setSpacing(10)

        # Minimum/maximum Combo boxes and connector functions
        self.tab2.minimum = QLabel('Minimum Peptide Length : ')
        self.tab2.minimumCombo = QComboBox(self)
        self.tab2.minimumCombo.activated[str].connect(self.minChanged)
        self.tab2.maximum = QLabel('Maximum Peptide Length : ')
        self.tab2.maximumCombo = QComboBox(self)
        self.tab2.maximumCombo.activated[str].connect(self.maxChanged)

        # Max distance combo box
        self.tab2.maxDistance = QLabel('Maximum Distance : ')
        self.tab2.maxDistCombo = QComboBox(self)

        # Adding values to the max/min/maxDist combos
        self.tab2.maxDistCombo.addItem('None')
        for i in range(2, 26):
            self.tab2.minimumCombo.addItem(str(i))
            self.tab2.maximumCombo.addItem(str(i))
            self.tab2.maxDistCombo.addItem(str(i))

        # Modifications combo boxes and labels
        self.tab2.mod1 = QLabel('Modification 1 : ')
        self.tab2.mod2 = QLabel('Modification 2 : ')
        self.tab2.mod3 = QLabel('Modification 3 : ')
        self.tab2.mod1Combo = QComboBox(self)
        self.tab2.mod2Combo = QComboBox(self)
        self.tab2.mod3Combo = QComboBox(self)

        # Adding values to modification combo boxes
        self.tab2.mod1Combo.addItem("None")
        self.tab2.mod2Combo.addItem("None")
        self.tab2.mod3Combo.addItem("None")
        for modification in modificationList:
            self.tab2.mod1Combo.addItem(modification)
            self.tab2.mod2Combo.addItem(modification)
            self.tab2.mod3Combo.addItem(modification)

        # initialise overlap, trans, cis and linear check boxes
        self.tab2.overlap = QCheckBox('Overlap Off', self)
        self.tab2.trans = QCheckBox('Trans', self)
        self.tab2.trans.stateChanged.connect(self.disableMaxDist) # connect trans check box to relevant function
        self.tab2.cis = QCheckBox('Cis', self)
        self.tab2.linear = QCheckBox('Linear', self)

        # create generate output push button
        self.tab2.output = QPushButton('Generate Output!', self)
        self.tab2.output.clicked.connect(self.confirmationFunction)

        # Add charge state check boxes
        self.tab2.chargeLabel = QLabel('Charge states (z): ')
        self.tab2.plusOne = QCheckBox('+1', self)
        self.tab2.plusTwo = QCheckBox('+2', self)
        self.tab2.plusThree = QCheckBox('+3', self)
        self.tab2.plusFour = QCheckBox('+4', self)
        self.tab2.plusFive = QCheckBox('+5', self)

        # All the labels added to grid layout of tab2
        self.tab2.layout.addWidget(self.tab2.minimum, 1, 3)
        self.tab2.layout.addWidget(self.tab2.maximum, 2, 3)
        self.tab2.layout.addWidget(self.tab2.maxDistance, 3, 3)
        self.tab2.layout.addWidget(self.tab2.mod1, 4, 3)
        self.tab2.layout.addWidget(self.tab2.mod2, 5, 3)
        self.tab2.layout.addWidget(self.tab2.mod3, 6, 3)
        self.tab2.layout.addWidget(self.tab2.overlap, 7, 3)
        self.tab2.layout.addWidget(self.tab2.linear, 8, 3)
        self.tab2.layout.addWidget(self.tab2.cis, 9, 3)
        self.tab2.layout.addWidget(self.tab2.trans, 10, 3)
        self.tab2.layout.addWidget(self.tab2.chargeLabel, 11, 3)

        # all dynamic elements added to the grid layout of tab 2
        self.tab2.layout.addWidget(self.tab2.minimumCombo, 1, 4, 1, 3)
        self.tab2.layout.addWidget(self.tab2.maximumCombo, 2, 4, 1, 3)
        self.tab2.layout.addWidget(self.tab2.maxDistCombo, 3, 4, 1, 3)
        self.tab2.layout.addWidget(self.tab2.mod1Combo, 4, 4, 1, 3)
        self.tab2.layout.addWidget(self.tab2.mod2Combo, 5, 4, 1, 3)
        self.tab2.layout.addWidget(self.tab2.mod3Combo, 6, 4, 1, 3)
        self.tab2.layout.addWidget(self.tab2.plusOne, 11, 4)
        self.tab2.layout.addWidget(self.tab2.plusTwo, 11, 5)
        self.tab2.layout.addWidget(self.tab2.plusThree, 11, 6)
        self.tab2.layout.addWidget(self.tab2.plusFour, 12, 4)
        self.tab2.layout.addWidget(self.tab2.plusFive, 12, 5)
        self.tab2.layout.addWidget(self.tab2.output, 13, 5, 1, 2)

        # set layout
        self.tab2.setLayout(self.tab2.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    # called from the Upload Fasta File button. Opens a window to select a file, and check if the file ends in fasta
    def uploadFasta(self):

        fname = QFileDialog.getOpenFileName(self, 'Open File', '/home')
        print(fname)
        self.fastaTest = fname[0][-5:]
        if self.fastaTest == 'fasta':
            self.fasta = Fasta(addSequenceList(fname[0]))
            print(fname[0])
            QMessageBox.about(self, "Message", 'Fasta file successfully imported!')
        elif fname[0] == '':
            print('')
        else:
            print(fname[0])
            QMessageBox.about(self, "Message", 'Please select a Fasta file!')

    # called from the Select Output Path button. Opens a window to select a file location to save the output to.
    def outputPath(self):

        self.outputPath = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if self.outputPath == '':
            print('')
        else:
            # convert to tool tip later
            QMessageBox.about(self, "Message", 'Valid Path Selected')

    def confirmationFunction(self):

        """
        called on click of generate output button on tab2. Checks to ensure all input values are relevant and outputs
        message box summarising the inputs of the user. When yes is clicked on the message box, the output function is
        called which begins generating results
        """

        mined = int(self.tab2.minimumCombo.currentText())
        maxed = int(self.tab2.maximumCombo.currentText())
        overlapFlag = self.tab2.overlap.isChecked()
        transFlag = self.tab2.trans.isChecked()

        cisFlag = self.tab2.cis.isChecked()
        maxDistance = self.tab2.maxDistCombo.currentText()
        linearFlag = self.tab2.linear.isChecked()

        plusOneFlag = self.tab2.plusOne.isChecked()
        plusTwoFlag = self.tab2.plusTwo.isChecked()
        plusThreeFlag = self.tab2.plusThree.isChecked()
        plusFourFlag = self.tab2.plusFour.isChecked()
        plusFiveFlag = self.tab2.plusFive.isChecked()

        chargeFlags = [plusOneFlag, plusTwoFlag, plusThreeFlag, plusFourFlag, plusFiveFlag]

        # self.fasta = Fasta(addSequenceList('/Users/nicolaschapman/Documents/UROP/Code/MersProject/Example.fasta'))
        # self.outputPath = '/Users/nicolaschapman/Desktop/Mers Output'
        self.fasta = Fasta(addSequenceList('C:/Users/Arpit/Desktop/UROP/Example.fasta'))
        self.outputPath = 'C:/Users/Arpit/Desktop/UROP'
        modList = [self.tab2.mod1Combo.currentText(), self.tab2.mod2Combo.currentText(),
                   self.tab2.mod3Combo.currentText()]

        if self.fasta is None or self.outputPath == "":

            QMessageBox.about(self, "Message", 'Please check that a valid Fasta file and output '
                                               'file location have been selected')
        else:
            reply = QMessageBox.question(self, 'Message', 'Do you wish to confirm the following input?\n' +
                                         'Minimum Length: ' + str(mined) + '\n' +
                                         'Maximum Length: ' + str(maxed) + '\n' +
                                         'Overlap Flag: ' + str(overlapFlag) + '\n' +
                                         'Trans Flag: ' + str(transFlag) + '\n' +
                                         'Linear Flag: ' + str(linearFlag) + '\n' +
                                         'Cis Flag: ' + str(cisFlag) + '\n' +
                                         'Mod List: ' + str(modList) + '\n' +
                                         'Maximum Distance: ' + str(maxDistance) + '\n',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                print(chargeFlags)
                self.output(self, mined, maxed, overlapFlag, transFlag, cisFlag, linearFlag, modList,
                            maxDistance, self.outputPath, chargeFlags)

    # called when trans is selected, it disables the use of the max distance function
    def disableMaxDist(self, state):

        if state == Qt.Checked:
            index = self.tab2.maxDistCombo.findText('None')
            self.tab2.maxDistCombo.setCurrentIndex(index)
            self.tab2.maxDistCombo.setEnabled(False)
        else:
            self.tab2.maxDistCombo.setEnabled(True)

    # called by confirmation function, it runs the generateOutput function from Mers.py while outputing small
    # bits of information to the user via a statusbar in the GUI
    def output(self, parent, mined, maxed, overlapFlag, transFlag, cisFlag, linearFlag, modList,
               maxDistance, outputPath, chargeFlags):
        start = time.time()

        self.parent().statusbar.showMessage('Processing Data')

        if maxDistance != 'None':
            maxDistance = int(maxDistance)

        self.fasta.generateOutput(mined, maxed, overlapFlag, transFlag, cisFlag, linearFlag, modList,
                                  maxDistance, outputPath, chargeFlags)
        end = time.time()
        self.parent().statusbar.hide()
        print(end - start)

    # called when minimumCombo value changes. It alters the values available in max and maxDistance combos to
    # ensure a realistic input
    def minChanged(self, text):

        # current Max Value
        maxValue = int(self.tab2.maximumCombo.currentText())

        # Current Max Distance - convert 'None' to 0 so it can be used as a comparator later.
        maxDistValue = self.tab2.maxDistCombo.currentText()
        if maxDistValue == 'None':
            maxDistInt = 0
        else:
            maxDistInt = int(maxDistValue)

        # Clear combo box values, add 'None' option back to maxDistCombo
        self.tab2.maximumCombo.clear()
        self.tab2.maxDistCombo.clear()
        self.tab2.maxDistCombo.addItem('None')

        # Creates new values in combo box which are greater than the min
        for i in range(int(text)-1, 26):
            self.tab2.maximumCombo.addItem(str(i+1))
        # Restores current value if it is greater than the min
        if maxValue >= int(text):
            indexMax = self.tab2.maximumCombo.findText(str(maxValue))
            self.tab2.maximumCombo.setCurrentIndex(indexMax)

        for i in range(int(text)-1, 26):
            self.tab2.maxDistCombo.addItem(str(i+1))
        if maxDistInt >= int(text):
            print(maxDistValue)
            indexDist = self.tab2.maxDistCombo.findText(str(maxDistValue))
            self.tab2.maxDistCombo.setCurrentIndex(indexDist)

    # essentially the same as minChanges except it is called by a maxDistance change
    def maxChanged(self, text):

        # current Min Value
        minValue = int(self.tab2.minimumCombo.currentText())

        # Current Max Distance - convert 'None' to 0 so it can be used as a comparator later.
        maxDistValue = self.tab2.maxDistCombo.currentText()
        if maxDistValue == 'None':
            maxDistInt = 0
        else:
            maxDistInt = int(maxDistValue)

        # Clear combo box values, add 'None' option back to maxDistCombo
        self.tab2.minimumCombo.clear()
        self.tab2.maxDistCombo.clear()
        self.tab2.maxDistCombo.addItem('None')

        # Creates new values in combo box which are less than than the max
        for i in range(2, int(text)+1):
            self.tab2.minimumCombo.addItem(str(i))
        # Restores current value if it is less than the max
        if minValue <= int(text):
            indexMin = self.tab2.minimumCombo.findText(str(minValue))
            self.tab2.minimumCombo.setCurrentIndex(indexMin)

        for i in range(int(text)-1, 26):
            self.tab2.maxDistCombo.addItem(str(i+1))
        if maxDistInt >= int(text):
            print(maxDistValue)
            indexDist = self.tab2.maxDistCombo.findText(str(maxDistValue))
            self.tab2.maxDistCombo.setCurrentIndex(indexDist)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
