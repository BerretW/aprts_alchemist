# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from database import db
from utils.theme import set_dark_theme
from widgets.ingredients import IngredientsWidget
from widgets.recipes import RecipesWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedM Alchemist Editor")
        self.resize(1100, 750)
        
        # Ověření DB při startu
        if not db.connect():
            QMessageBox.critical(self, "Chyba DB", "Nepodařilo se připojit k databázi!\nZkontrolujte config.py")
            sys.exit(1)

        self.tabs = QTabWidget()
        self.tabs.addTab(IngredientsWidget(), "🧪 Ingredience")
        self.tabs.addTab(RecipesWidget(), "📜 Recepty & Tvorba")
        
        self.setCentralWidget(self.tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())