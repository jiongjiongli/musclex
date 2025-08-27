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

import cv2
import numpy as np
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
    QDoubleSpinBox,
    QFrame,
    QScrollArea,
    QGroupBox,
    QLineEdit,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class AdjustAngleDialog(QDialog):
    def __init__(self,
                parent,
                start_img,
                img,
                center,
                angle_to_origin,
                transform,
                isLogScale,
                vmin,
                vmax
        ):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle("Adjust Angle")
        self.start_img = start_img
        self.img = img
        self.center = center
        self.angle_to_origin = angle_to_origin
        self.transform = transform
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

        self.angleSpnBox = QDoubleSpinBox()
        self.angleSpnBox.setSuffix("°")
        self.angleSpnBox.setDecimals(2)
        self.angleSpnBox.setSingleStep(1)
        self.angleSpnBox.setValue(self.angle_to_origin % 360)
        self.angleSpnBox.setRange(0, 360)
        self.angleSpnBox.setKeyboardTracking(False)

        self.setAngleGroup = QGroupBox("Set Angle")
        self.setAngleLayout = QGridLayout(self.setAngleGroup)

        angleLayoutRowIndex = 0
        self.setAngleLayout.addWidget(QLabel("Clockwise Rotation Angle (Original coords): "), angleLayoutRowIndex, 0, 1, 2)
        self.setAngleLayout.addWidget(self.angleSpnBox, angleLayoutRowIndex, 2, 1, 2)


        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn, Qt.Horizontal, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout = QVBoxLayout(self)

        self.imageLayout = QHBoxLayout()
        self.imageLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addLayout(self.imageLayout)

        self.optionsLayout = QVBoxLayout()

        # self.displayOptGrpBx = QGroupBox("Display Options")
        # self.dispOptLayout = QGridLayout(self.displayOptGrpBx)
        # self.doubleZoom = QCheckBox("Double Zoom")

        # self.dispOptLayoutRowIndex = 0
        # self.dispOptLayout.addWidget(self.doubleZoom, self.dispOptLayoutRowIndex, 0, 1, 4)
        # self.dispOptLayoutRowIndex += 1

        # self.optionsLayout.addWidget(self.displayOptGrpBx)
        # self.optionsLayout.addSpacing(10)
        self.optionsLayout.addWidget(self.setAngleGroup)
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

        self.setMinimumSize(700, 500)
        self.resize(1200, 1000 // 4 * 3)

        self.imageFigure.tight_layout()
        self.imageCanvas.draw()

        self.createConnections()

    def createConnections(self):
        self.angleSpnBox.editingFinished.connect(self.UpdateAngle)
        self.angleSpnBox.valueChanged.connect(self.UpdateAngle)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            return

        super().keyPressEvent(event)

    def get_angle(self):
        angle =  self.angleSpnBox.value() - self.angle_to_origin
        return angle


    def UpdateAngle(self):
        x, y = self.center
        height = self.start_img.shape[0]
        width = self.start_img.shape[1]

        angle = self.get_angle()

        M = cv2.getRotationMatrix2D(
            (x, y),
            angle,
            1
        )

        transform = self.merge_warps((self.transform, M))
        transformed_img = cv2.warpAffine(
            self.start_img,
            transform,
            (width, height))

        if self.isLogScale:
            self.imageAxes.imshow(
                transformed_img,
                cmap="gray",
                norm=LogNorm(vmin=max(1, self.vmin), vmax=self.vmax),
            )
        else:
            self.imageAxes.imshow(
                transformed_img,
                cmap="gray",
                norm=Normalize(vmin=self.vmin, vmax=self.vmax),
            )

        self.imageAxes.set_facecolor('black')

        self.imageAxes.set_xlim((0, transformed_img.shape[1]))
        self.imageAxes.set_ylim((0, transformed_img.shape[0]))

        self.vline = self.imageAxes.axvline(x, color='y')
        self.hline = self.imageAxes.axhline(y, color='y')
        # self.imageFigure.tight_layout()
        self.imageCanvas.draw_idle()

    def merge_warps(self, warps):
        M_total = np.eye(3, dtype=np.float32)

        for W in warps:
            # Convert 2x3 -> 3x3
            W_h = np.vstack([W, [0, 0, 1]])
            # Multiply (note: last one in list applies last)
            M_total = W_h @ M_total

        # Convert back to 2x3
        M = M_total[:2, :]
        return M
