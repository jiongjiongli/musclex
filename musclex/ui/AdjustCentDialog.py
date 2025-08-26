"""
Copyright 1999 Illinois Institute of Technology

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL ILLINOIS INSTITUTE OF TECHNOLOGY BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Except as contained in this notice, the name of Illinois Institute
of Technology shall not be used in advertising or otherwise to promote
the sale, use or other dealings in this Software without prior written
authorization from Illinois Institute of Technology.
"""

import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QPushButton,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
)
from PySide6.QtCore import Qt


class AdjustCentDialog(QDialog):
    def __init__(self, parent, img, center):
        super().__init__(parent)
        self.setWindowTitle("Adjust Center")
        self.img = img
        self.center = center
        x, y = self.center

        self.imageFigure = plt.figure()
        self.imageAxes = self.imageFigure.add_subplot(111)
        self.imageAxes.set_aspect('equal', adjustable="box")
        self.imageCanvas = FigureCanvas(self.imageFigure)

        self.imageAxes.imshow(self.img, cmap="gray")
        self.imageAxes.set_xlim((0, self.img.shape[1]))
        self.imageAxes.set_ylim((0, self.img.shape[0]))
        self.vline = self.imageAxes.axvline(x, color='y')
        self.hline = self.imageAxes.axhline(y, color='y')

        self.xInput = QLineEdit(f"{x:.2f}")
        self.yInput = QLineEdit(f"{y:.2f}")
        self.updateBtn = QPushButton("Update Center")
        self.updateBtn.clicked.connect(self.updateCenterFromInput)

        # Update center immediately when losing focus or pressing enter, without closing dialog
        self.xInput.returnPressed.connect(self.updateCenterFromInput)
        self.yInput.returnPressed.connect(self.updateCenterFromInput)
        self.xInput.editingFinished.connect(self.updateCenterFromInput)
        self.yInput.editingFinished.connect(self.updateCenterFromInput)

        self.inputLayout = QHBoxLayout()
        self.inputLayout.addWidget(QLabel("X:"))
        self.inputLayout.addWidget(self.xInput)
        self.inputLayout.addWidget(QLabel("Y:"))
        self.inputLayout.addWidget(self.yInput)
        self.inputLayout.addWidget(self.updateBtn)

        # Output boxes to show actual center values
        self.xOutput = QLineEdit(f"{x:.2f}")
        self.yOutput = QLineEdit(f"{y:.2f}")
        self.xOutput.setReadOnly(True)
        self.yOutput.setReadOnly(True)

        self.outputLayout = QHBoxLayout()
        self.outputLayout.addWidget(QLabel("Actual X:"))
        self.outputLayout.addWidget(self.xOutput)
        self.outputLayout.addWidget(QLabel("Actual Y:"))
        self.outputLayout.addWidget(self.yOutput)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn, Qt.Horizontal, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.imageCanvas)
        self.layout.addLayout(self.inputLayout)
        self.layout.addLayout(self.outputLayout)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.createConnections()

    def createConnections(self):
        self.imageFigure.canvas.mpl_connect('button_press_event', self.imageClicked)
        # self.imageFigure.canvas.mpl_connect('motion_notify_event', self.imageOnMotion)
        # self.imageFigure.canvas.mpl_connect('button_release_event', self.imageReleased)
        # self.imageFigure.canvas.mpl_connect('scroll_event', self.imgScrolled)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            return

        super().keyPressEvent(event)

    def imageClicked(self, event):
        if event.inaxes != self.imageAxes:
            return

        self.center = (event.xdata, event.ydata)
        self.refreshCenter()

    def refreshCenter(self):
        x, y = self.center

        # Remove old lines
        self.vline.remove()
        self.hline.remove()

        # Draw new lines
        self.vline = self.imageAxes.axvline(x, color='y')
        self.hline = self.imageAxes.axhline(y, color='y')

        # Update input output
        self.xInput.setText(f"{x:.2f}")
        self.yInput.setText(f"{y:.2f}")
        self.xOutput.setText(f"{x:.2f}")
        self.yOutput.setText(f"{y:.2f}")

        self.imageCanvas.draw_idle()

    def updateCenterFromInput(self):
        try:
            x = float(self.xInput.text())
            y = float(self.yInput.text())
            self.center = (x, y)
            self.refreshCenter()
        except ValueError:
            raise


