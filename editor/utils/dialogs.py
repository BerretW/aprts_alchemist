# utils/dialogs.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QTableWidget, 
                             QHeaderView, QAbstractItemView, QHBoxLayout, QPushButton, 
                             QTableWidgetItem, QLabel)
from PyQt5.QtCore import Qt
from database import db
from utils.image_loader import ImageLoader

class ItemSearchDialog(QDialog):
    def __init__(self, parent=None, title="Vybrat item"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 500) # Trochu širší
        layout = QVBoxLayout(self)
        
        # Horní část: Input + Náhled
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hledat (název nebo label)...")
        self.search_input.textChanged.connect(self.filter_items)
        
        self.img_preview = QLabel()
        self.img_preview.setFixedSize(64, 64)
        self.img_preview.setStyleSheet("border: 1px solid #444; background: #222;")
        
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.img_preview)
        layout.addLayout(top_layout)

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(2)
        self.item_table.setHorizontalHeaderLabels(["ID Itemu", "Název (Label)"])
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.item_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.item_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.item_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.item_table.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.item_table)

        btn_box = QHBoxLayout()
        self.btn_select = QPushButton("Vybrat")
        self.btn_select.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Zrušit")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_select)
        btn_box.addWidget(self.btn_cancel)
        layout.addLayout(btn_box)

        self.all_items = []
        self.load_items()

    def load_items(self):
        rows = db.fetch_all("SELECT item, label FROM items") 
        self.all_items = rows if rows else []
        self.filter_items("")

    def filter_items(self, text):
        text = text.lower()
        filtered = [i for i in self.all_items if text in i['item'].lower() or text in i['label'].lower()]
        
        self.item_table.setRowCount(0)
        for row_idx, item in enumerate(filtered):
            self.item_table.insertRow(row_idx)
            self.item_table.setItem(row_idx, 0, QTableWidgetItem(item['item']))
            self.item_table.setItem(row_idx, 1, QTableWidgetItem(item['label']))

    def on_item_clicked(self, item):
        row = item.row()
        item_id = self.item_table.item(row, 0).text()
        ImageLoader.load_image(item_id, self.img_preview, max_size=64)

    def get_selected_item(self):
        row = self.item_table.currentRow()
        if row < 0: return None
        return self.item_table.item(row, 0).text()