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
from matplotlib.colors import LogNorm, Normalize, ListedColormap

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QPushButton,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QFrame,
    QScrollArea,
    QGroupBox,
    QLineEdit,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from .DoubleZoomViewer import DoubleZoom


class AdjustCentDialog(QDialog):
    def __init__(self,
                parent,
                img,
                center,
                isLogScale,
                vmin,
                vmax
        ):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle("Adjust Center")
        self.img = img
        self.center = center
        self.isLogScale = isLogScale
        self.vmin = vmin
        self.vmax = vmax
        x, y = self.center

        self.imageFigure = plt.figure()
        self.imageAxes = self.imageFigure.add_subplot(111)
        self.imageAxes.set_aspect('equal', adjustable="box")
        self.imageCanvas = FigureCanvas(self.imageFigure)

        if isLogScale:
            self.imageAxes.imshow(
                self.img,
                cmap="gray",
                norm=LogNorm(vmin=max(1, vmin), vmax=vmax),
            )
        else:
            self.imageAxes.imshow(
                self.img,
                cmap="gray",
                norm=Normalize(vmin=vmin, vmax=vmax),
            )

        self.imageAxes.set_facecolor('black')

        self.imageAxes.set_xlim((0, self.img.shape[1]))
        self.imageAxes.set_ylim((0, self.img.shape[0]))
        self.vline = self.imageAxes.axvline(x, color='y')
        self.hline = self.imageAxes.axhline(y, color='y')

        self.xInput = QLineEdit(f"{x:.2f}")
        self.yInput = QLineEdit(f"{y:.2f}")
        # self.updateBtn = QPushButton("Update Center")
        # self.updateBtn.clicked.connect(self.updateCenterFromInput)

        # Update center immediately when losing focus or pressing enter, without closing dialog
        self.xInput.returnPressed.connect(self.updateCenterFromInput)
        self.yInput.returnPressed.connect(self.updateCenterFromInput)
        self.xInput.editingFinished.connect(self.updateCenterFromInput)
        self.yInput.editingFinished.connect(self.updateCenterFromInput)

        self.setCenterGroup = QGroupBox("Set Center")
        self.setCenterLayout = QGridLayout(self.setCenterGroup)

        # self.xInputLayout = QHBoxLayout()
        # self.xInputLayout.addWidget(QLabel("X:"))
        # self.xInputLayout.addWidget(self.xInput)

        # self.yInputLayout = QHBoxLayout()
        # self.yInputLayout.addWidget(QLabel("Y:"))
        # self.yInputLayout.addWidget(self.yInput)

        centerLayoutRowIndex = 0
        self.setCenterLayout.addWidget(QLabel("X (Current coords): "), centerLayoutRowIndex, 0, 1, 2)
        self.setCenterLayout.addWidget(self.xInput, centerLayoutRowIndex, 2, 1, 2)
        self.setCenterLayout.addWidget(QLabel("px"), centerLayoutRowIndex, 4, 1, 1)
        centerLayoutRowIndex += 1
        self.setCenterLayout.addWidget(QLabel("Y (Current coords): "), centerLayoutRowIndex, 0, 1, 2)
        self.setCenterLayout.addWidget(self.yInput, centerLayoutRowIndex, 2, 1, 2)
        self.setCenterLayout.addWidget(QLabel("px"), centerLayoutRowIndex, 4, 1, 1)
        # self.setCenterLayout.addLayout(self.xInputLayout)
        # self.setCenterLayout.addLayout(self.yInputLayout)

        # self.setCenterLayout.addWidget(self.updateBtn)

        # # Output boxes to show actual center values
        # self.xOutput = QLineEdit(f"{x:.2f}")
        # self.yOutput = QLineEdit(f"{y:.2f}")
        # self.xOutput.setReadOnly(True)
        # self.yOutput.setReadOnly(True)

        # self.outputLayout = QHBoxLayout()
        # self.outputLayout.addWidget(QLabel("Actual X:"))
        # self.outputLayout.addWidget(self.xOutput)
        # self.outputLayout.addWidget(QLabel("Actual Y:"))
        # self.outputLayout.addWidget(self.yOutput)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn, Qt.Horizontal, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout = QVBoxLayout(self)

        self.imageLayout = QHBoxLayout()
        self.imageLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addLayout(self.imageLayout)

        self.optionsLayout = QVBoxLayout()

        self.displayOptGrpBx = QGroupBox("Display Options")
        self.dispOptLayout = QGridLayout(self.displayOptGrpBx)
        self.doubleZoom = QCheckBox("Double Zoom")

        self.dispOptLayoutRowIndex = 0
        self.dispOptLayout.addWidget(self.doubleZoom, self.dispOptLayoutRowIndex, 0, 1, 4)
        self.dispOptLayoutRowIndex += 1

        self.optionsLayout.addWidget(self.displayOptGrpBx)
        self.optionsLayout.addSpacing(10)
        self.optionsLayout.addWidget(self.setCenterGroup)
        self.optionsLayout.addStretch()

        self.imageLayout.addWidget(self.imageCanvas)

        self.scroll_areaImg = QScrollArea()
        self.imageLayout.addWidget(self.scroll_areaImg)

        self.scroll_areaImg.setWidgetResizable(True)

        self.frameOfKeys = QFrame()
        self.frameOfKeys.setFixedWidth(500)
        self.frameOfKeys.setLayout(self.optionsLayout)
        self.scroll_areaImg.setWidget(self.frameOfKeys)
        self.scroll_areaImg.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # self.mainLayout.addLayout(self.outputLayout)
        self.mainLayout.addWidget(self.buttonBox)
        # self.mainLayout.setAlignment(Qt.AlignCenter)
        self.mainLayout.setAlignment(self.buttonBox, Qt.AlignCenter)

        self.doubleZoomGUI = DoubleZoom(self.imageFigure, dontShowMessage=True)

        # pixels
        # self.imageCanvas.setMinimumSize(800, 600)
        # self.imageCanvas.setSizePolicy(
        #     QSizePolicy.Expanding, QSizePolicy.Expanding
        # )

        self.setMinimumSize(700, 500)
        self.resize(1200, 1000 // 4 * 3)

        self.imageFigure.tight_layout()
        self.imageCanvas.draw()

        self.createConnections()

    def createConnections(self):
        self.imageFigure.canvas.mpl_connect('button_press_event', self.imageClicked)
        self.imageFigure.canvas.mpl_connect('motion_notify_event', self.imageOnMotion)
        # self.imageFigure.canvas.mpl_connect('button_release_event', self.imageReleased)
        # self.imageFigure.canvas.mpl_connect('scroll_event', self.imgScrolled)
        self.doubleZoom.stateChanged.connect(self.doubleZoomChecked)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            return

        super().keyPressEvent(event)

    def imageClicked(self, event):
        x = event.xdata
        y = event.ydata

        if event.inaxes == self.imageAxes:
            print("imageAxes clicked!")
            if self.doubleZoom.isChecked():
                # print(f"doubleZoomMode: {self.doubleZoomGUI.doubleZoomMode}")
                if self.doubleZoomGUI.doubleZoomMode:
                    # set self.doubleZoomMode = False
                    self.doubleZoomGUI.mouseClickBehavior(x, y)

                    self.center = (x, y)
                    self.refreshCenter(updateText=True)

            else:
                self.center = (x, y)
                self.refreshCenter(updateText=True)

        elif event.inaxes == self.doubleZoomGUI.axes:
            print("doubleZoomGUI clicked!")
            if self.doubleZoom.isChecked():
                # if not self.doubleZoomGUI.doubleZoomMode:
                x, y = self.doubleZoomGUI.doubleZoomToOrigCoord(x, y)
                self.doubleZoomGUI.doubleZoomMode = True

                self.center = (x, y)
                self.refreshCenter(updateText=True)


    def refreshCenter(self, updateText=False):
        x, y = self.center

        ax = self.imageAxes

        # Remove old lines
        self.remove_image_lines()

        # Draw new lines
        self.vline = self.imageAxes.axvline(x, color='y')
        self.hline = self.imageAxes.axhline(y, color='y')

        if updateText:
            # Update input output
            self.xInput.setText(f"{x:.2f}")
            self.yInput.setText(f"{y:.2f}")
            # self.xOutput.setText(f"{x:.2f}")
            # self.yOutput.setText(f"{y:.2f}")

        # self.imageFigure.tight_layout()
        self.imageCanvas.draw()

    def updateCenterFromInput(self):
        x = float(self.xInput.text())
        y = float(self.yInput.text())
        self.center = (x, y)
        self.refreshCenter(updateText=False)

    def doubleZoomChecked(self):
        """
        Triggered when double zoom is checked
        """
        self.doubleZoomGUI.doubleZoomChecked(
            img=self.img,
            canv=self.imageCanvas,
            center=self.center,
            is_checked=self.doubleZoom.isChecked(),
            isLogScale=self.isLogScale,
            vmin=self.vmin,
            vmax=self.vmax
        )

    def imageOnMotion(self, event):
        x = event.xdata
        y = event.ydata
        ax = self.imageAxes

        if self.doubleZoom.isChecked():
            if event.inaxes == self.doubleZoomGUI.axes:
                if not self.doubleZoomGUI.doubleZoomMode:
                    # Draw cursor location in zoom using red cross lines.
                    self.doubleZoomGUI.updateAxes(x, y)

                    self.imageCanvas.draw_idle()

            elif event.inaxes == self.imageAxes:
                if self.doubleZoomGUI.doubleZoomMode:
                    # Draw cursor location in image using blue dot.
                    self.doubleZoomGUI.beginImgMotion(x, y, self.img.shape[1], self.img.shape[0], (0, 0), self.imageAxes)

                    # Update sursor area in zoom
                    self.doubleZoomGUI.mouseHoverBehavior(
                        x,
                        y,
                        self.img,
                        self.imageCanvas,
                        self.doubleZoom.isChecked(),
                        isLogScale=self.isLogScale,
                        vmin=self.vmin,
                        vmax=self.vmax
                    )

        else:
            if event.inaxes == self.imageAxes:
                # Remove old lines
                self.remove_image_lines(labels=["Red Dot"])
                # Draw cursor location in image using red cross lines.
                axis_size = 5

                ax.plot((x - axis_size, x + axis_size), (y - axis_size, y + axis_size), color='r', label="Red Dot")
                ax.plot((x - axis_size, x + axis_size), (y + axis_size, y - axis_size), color='r', label="Red Dot")

                self.imageCanvas.draw_idle()

    def remove_image_lines(self, labels=None):
        ax = self.imageAxes

        for i in range(len(ax.lines)-1, -1, -1):
            if labels:
                if ax.lines[i].get_label() in labels:
                    ax.lines[i].remove()
            else:
                ax.lines[i].remove()

        for i in range(len(ax.patches)-1, -1, -1):
            ax.patches[i].remove()