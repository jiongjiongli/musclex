"""
Reusable image navigation widget with background directory scan and caching.
Provides left/right navigation, file selection, optional processing controls,
and emits signals when the current image changes or processing is requested.
"""

import os
import threading
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QSizePolicy
)
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

try:
    from ..utils.file_manager import scan_directory_images_cached
except Exception:
    scan_directory_images_cached = None


class ImageNavWidget(QWidget):
    imageChanged = Signal(str, object)  # displayName, loaderSpec
    requestProcessCurrent = Signal(str, object)
    requestProcessCurrentH5 = Signal(str)  # h5Path
    requestProcessAll = Signal()
    requestPause = Signal()

    def __init__(self, showProcessing=True, parent=None):
        super().__init__(parent)
        self._showProcessing = showProcessing

        self._dirPath = ''
        self._imgList = []
        self._specs = []
        self._index = 0
        self._provisional = False

        self._scan_thread = None
        self._scan_result = None
        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(200)
        self._scan_timer.timeout.connect(self._checkScanDone)

        self._buildUI()

    def _buildUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top bar
        top = QHBoxLayout()
        self.selectBtn = QPushButton("Select…")
        self.pathEdit = QLineEdit()
        self.countLabel = QLabel("0")
        top.addWidget(self.selectBtn)
        top.addWidget(self.pathEdit, 1)
        top.addWidget(self.countLabel)
        layout.addLayout(top)

        # Canvas
        self.figure = plt.figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas, 1)

        # Bottom bar (navigation + processing)
        bottom = QHBoxLayout()
        self.prevBtn = QPushButton("<")
        self.nextBtn = QPushButton(">")
        bottom.addWidget(self.prevBtn)
        bottom.addWidget(self.nextBtn)

        self.procCurrentBtn = QPushButton("Process Current")
        self.procCurrentH5Btn = QPushButton("Process Current H5")
        self.procAllBtn = QPushButton("Process All")
        self.pauseBtn = QPushButton("Pause")
        for b in (self.procCurrentBtn, self.procCurrentH5Btn, self.procAllBtn, self.pauseBtn):
            bottom.addWidget(b)
        layout.addLayout(bottom)

        for b in (self.procCurrentBtn, self.procCurrentH5Btn, self.procAllBtn, self.pauseBtn):
            b.setVisible(self._showProcessing)

        # Connections
        self.selectBtn.clicked.connect(self._selectClicked)
        self.prevBtn.clicked.connect(self.prev)
        self.nextBtn.clicked.connect(self.next)
        self.procCurrentBtn.clicked.connect(self._procCurrent)
        self.procCurrentH5Btn.clicked.connect(self._procCurrentH5)
        self.procAllBtn.clicked.connect(self.requestProcessAll.emit)
        self.pauseBtn.clicked.connect(self.requestPause.emit)

    def setShowProcessingButtons(self, show: bool):
        self._showProcessing = show
        for b in (self.procCurrentBtn, self.procCurrentH5Btn, self.procAllBtn, self.pauseBtn):
            b.setVisible(show)

    # Public API
    def loadPathOrFile(self, pathOrFile: str):
        pathOrFile = str(pathOrFile)
        if os.path.isdir(pathOrFile):
            self._dirPath = pathOrFile
            # Provisional scan (empty initial)
            self._imgList, self._specs = [], []
            self._index = 0
            self._provisional = True
            self._startScan()
            self._updateCount()
            self._renderNone()
        else:
            self._dirPath, name = os.path.split(pathOrFile)
            base, ext = os.path.splitext(name)
            if ext.lower() in ('.h5', '.hdf5'):
                disp = base + '_00001' + ext
                spec = ("h5", pathOrFile, 0)
            else:
                disp = name
                spec = ("tiff", pathOrFile)
            self._imgList = [disp]
            self._specs = [spec]
            self._index = 0
            self._provisional = True
            self._updateCount()
            self._renderCurrent()
            self.imageChanged.emit(disp, spec)
            self._startScan()

    def getListing(self):
        return list(self._imgList), list(self._specs)

    def getCount(self):
        return len(self._imgList), self._provisional

    # Navigation
    def prev(self):
        if not self._imgList:
            return
        self._index = (self._index - 1) % len(self._imgList)
        self._renderCurrent()
        self.imageChanged.emit(self._imgList[self._index], self._specs[self._index])

    def next(self):
        if not self._imgList:
            return
        self._index = (self._index + 1) % len(self._imgList)
        self._renderCurrent()
        self.imageChanged.emit(self._imgList[self._index], self._specs[self._index])

    # Internals
    def _selectClicked(self):
        # Let host handle file dialog. Expose path edit for info only.
        # Host should call loadPathOrFile itself.
        pass

    def _procCurrent(self):
        if not self._imgList:
            return
        self.requestProcessCurrent.emit(self._imgList[self._index], self._specs[self._index])

    def _procCurrentH5(self):
        if not self._imgList:
            return
        spec = self._specs[self._index]
        if isinstance(spec, tuple) and len(spec) >= 2 and spec[0] == 'h5':
            self.requestProcessCurrentH5.emit(spec[1])

    def _startScan(self):
        if scan_directory_images_cached is None or not self._dirPath:
            return
        self._scan_result = None
        if self._scan_thread and self._scan_thread.is_alive():
            return
        self._scan_thread = threading.Thread(target=self._doScanDir, args=(self._dirPath,))
        self._scan_thread.daemon = True
        self._scan_thread.start()
        self._scan_timer.start()

    def _doScanDir(self, dir_path):
        try:
            imgList, specs = scan_directory_images_cached(dir_path)
            self._scan_result = (imgList, specs)
        except Exception:
            self._scan_result = None

    def _checkScanDone(self):
        if self._scan_result is None:
            return
        imgList, specs = self._scan_result
        if imgList and specs:
            # Preserve current selection if present
            curr = self._imgList[self._index] if self._imgList else None
            self._imgList = imgList
            self._specs = specs
            if curr in self._imgList:
                self._index = self._imgList.index(curr)
            else:
                self._index = 0
        self._provisional = False
        self._updateCount()
        self._scan_timer.stop()

    def _updateCount(self):
        n = len(self._imgList)
        self.countLabel.setText(str(n) + ('*' if self._provisional else ''))

    def _renderNone(self):
        self.axes.cla()
        self.axes.set_facecolor('black')
        self.canvas.draw_idle()

    def _renderCurrent(self):
        if not self._imgList:
            self._renderNone()
            return
        spec = self._specs[self._index]
        img = None
        try:
            if isinstance(spec, tuple):
                if spec[0] == 'tiff' and len(spec) == 2:
                    import fabio
                    img = fabio.open(spec[1]).data
                elif spec[0] == 'h5' and len(spec) == 3:
                    import fabio
                    f = fabio.open(spec[1])
                    if getattr(f, 'nframes', 1) == 1 or spec[2] == 0:
                        img = f.data if spec[2] == 0 else f.get_frame(spec[2]).data
                    else:
                        img = f.get_frame(spec[2]).data
                    try:
                        f.close()
                    except Exception:
                        pass
        except Exception:
            img = None

        self.axes.cla()
        if img is not None:
            img = np.array(img, dtype=np.float32)
            self.axes.imshow(img, cmap='gray')
            self.axes.set_xlabel('x')
            self.axes.set_ylabel('y')
            self.axes.invert_yaxis()
        self.axes.set_facecolor('black')
        self.canvas.draw_idle()


