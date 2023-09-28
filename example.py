from pyconify.qt import QIconify
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QApplication, QPushButton

app = QApplication([])

btn = QPushButton()
icon = QIconify("game-icons:sharp-smile", color="cornflowerblue", rotate=35)
btn.setIcon(icon)
btn.setIconSize(QSize(30, 30))
btn.show()

app.exec()
