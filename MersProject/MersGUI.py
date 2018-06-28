import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QTabWidget, QVBoxLayout, \
                            QFileDialog, QGridLayout, QLabel, QComboBox, QCheckBox, QMessageBox
from PyQt5.QtCore import pyqtSlot
from Mers import *

# pyinstaller MersGUI --> this command from the relevant file location creates executable file
#Move to mers
modificationList = ['4-hydroxynonenal (HNE)', 'Acetylation (K)', 'Beta-methylthiolation', 'Carbamidomethylation',
                 'Carboxylation (E)','Carboxymethyl','Citrullination', 'Deamidation (NQ)','Dimethylation(KR)',
                 'Dioxidation (M)', 'FAD', 'Farnesylation', 'Geranyl-geranyl', 'Guanidination', 'HexNAcylation (N)',
                 'Hexose (NSY)','Lipoyl','Methylation(KR)','Methylation(others)','Oxidation (HW)','Oxidation (M)',
                 'Palmitoylation','Phosphopantetheine','Phosphorylation (HCDR)', 'Phosphorylation (STY)',
                 'Propionamide','Pyridoxal phosphate','S-pyridylethylation','Sulfation','Sulphone','Ubiquitin',
                 'Ubiquitination']

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Peptide Splicer'
        self.left = 500
        self.fastaTest = False
        self.outputPath = ""
        self.statusbar = self.statusBar()



        self.top = 300
        self.width = 300
        self.height = 300
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()


class MyTableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.fasta = None

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self)

        self.pushButton1 = QPushButton("Select File")
        self.pushButton1.clicked.connect(self.showDialog)

        self.pushButton2 = QPushButton("Select Save Location")
        self.pushButton2.clicked.connect(self.outputPath)

        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.layout.addWidget(self.pushButton2)

        self.tab1.setLayout(self.tab1.layout)

        # Create second tab
        self.tab2.layout = QGridLayout(self)
        self.tab2.layout.setSpacing(10)

        # Minimum/maximum values
        self.tab2.minimum = QLabel('Minimum Value : ')
        self.tab2.minimumCombo = QComboBox(self)
        self.tab2.maximum = QLabel('Maximum Value : ')
        self.tab2.maximumCombo = QComboBox(self)

        self.tab2.maxDistance = QLabel('Maximum Distance : ')
        self.tab2.maxDistCombo = QComboBox(self)

        for i in range(0, 26):
            self.tab2.minimumCombo.addItem(str(i))
            self.tab2.maximumCombo.addItem(str(i))
            self.tab2.maxDistCombo.addItem(str(i))
        self.tab2.maxDistCombo.addItem('None')

        # Modifications drop downs and labels
        self.tab2.mod1 = QLabel('Modification 1 : ')
        self.tab2.mod2 = QLabel('Modification 2 : ')
        self.tab2.mod3 = QLabel('Modification 3 : ')
        self.tab2.mod1Combo = QComboBox(self)
        self.tab2.mod2Combo = QComboBox(self)
        self.tab2.mod3Combo = QComboBox(self)

        self.tab2.mod1Combo.addItem("None")
        self.tab2.mod2Combo.addItem("None")
        self.tab2.mod3Combo.addItem("None")
        for modification in modificationList:
            self.tab2.mod1Combo.addItem(modification)
            self.tab2.mod2Combo.addItem(modification)
            self.tab2.mod3Combo.addItem(modification)

        self.tab2.overlap = QCheckBox('Overlap Off', self)
        self.tab2.trans = QCheckBox('Trans', self)
        self.tab2.cis = QCheckBox('Cis', self)
        self.tab2.linear = QCheckBox('Linear', self)

        self.tab2.output = QPushButton('Generate Output!', self)
        self.tab2.output.clicked.connect(self.confirmationFunction)



        # All the labels added
        self.tab2.layout.addWidget(self.tab2.minimum, 1, 3)
        self.tab2.layout.addWidget(self.tab2.maximum, 2, 3)
        self.tab2.layout.addWidget(self.tab2.maxDistance, 3, 3)
        self.tab2.layout.addWidget(self.tab2.mod1, 4, 3)
        self.tab2.layout.addWidget(self.tab2.mod2, 5, 3)
        self.tab2.layout.addWidget(self.tab2.mod3, 6, 3)
        self.tab2.layout.addWidget(self.tab2.overlap, 7, 3)
        self.tab2.layout.addWidget(self.tab2.trans, 8, 3)
        self.tab2.layout.addWidget(self.tab2.cis, 9, 3)
        self.tab2.layout.addWidget(self.tab2.linear, 10, 3)



        self.tab2.layout.addWidget(self.tab2.minimumCombo, 1, 4)
        self.tab2.layout.addWidget(self.tab2.maximumCombo, 2, 4)
        self.tab2.layout.addWidget(self.tab2.maxDistCombo, 3, 4)
        self.tab2.layout.addWidget(self.tab2.mod1Combo, 4, 4)
        self.tab2.layout.addWidget(self.tab2.mod2Combo, 5, 4)
        self.tab2.layout.addWidget(self.tab2.mod3Combo, 6, 4)
        self.tab2.layout.addWidget(self.tab2.output, 11, 4)

        self.tab2.setLayout(self.tab2.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def showDialog(self, parent):

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

    def outputPath(self, parent):

        self.outputPath = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if self.outputPath == '':
            print('')
        else:
            #convert to tool tip later
            QMessageBox.about(self, "Message", 'Valid Path Selected')

    def confirmationFunction(self, parent):

        mined = int(self.tab2.minimumCombo.currentText())
        maxed = int(self.tab2.maximumCombo.currentText())
        overlapFlag = self.tab2.overlap.isChecked()
        transFlag = self.tab2.trans.isChecked()
        linearFlag = self.tab2.linear.isChecked()
        cisFlag = self.tab2.cis.isChecked()
        maxDistance = self.tab2.maxDistCombo.currentText()
        # self.fasta = Fasta(addSequenceList('/Users/nicolaschapman/Documents/UROP/Code/MersProject/Example.fasta'))
        self.fasta = Fasta(addSequenceList('C:/Users/Arpit/Desktop/UROP/Example.fasta'))
        self.outputPath = 'C:/Users/Arpit/Desktop/UROP'
        modList = [self.tab2.mod1Combo.currentText(), self.tab2.mod2Combo.currentText(), self.tab2.mod3Combo.currentText()]
        if self.fasta == None or self.outputPath == "":

            QMessageBox.about(self, "Message", 'Please check that a valid Fasta file and output file location have been selected')
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
                self.output(self,mined, maxed, overlapFlag,transFlag, cisFlag, linearFlag, modList, maxDistance,self.outputPath)


    def output(self, parent, mined, maxed, overlapFlag, transFlag, cisFlag, linearFlag, modList, maxDistance,outputPath):
        start = time.time()

        self.parent().statusbar.showMessage('Processing Data')




        if maxDistance != 'None':
            maxDistance = int(maxDistance)

        self.fasta.generateOutput(mined, maxed, overlapFlag, transFlag, cisFlag, linearFlag, modList, maxDistance,outputPath)
        end = time.time()
        self.parent().statusbar.hide()
        print(end - start)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())