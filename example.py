from pyconify.qt import QIconify
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QApplication, QPushButton

app = QApplication([])

btn = QPushButton()
icon = QIconify("iconamoon:3d-fill", color="cornflowerblue")
btn.setIcon(icon)
btn.setIconSize(QSize(30, 30))
btn.show()

app.exec()
