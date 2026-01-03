from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QHeaderView, 
                             QAbstractItemView, QPushButton, QGroupBox, QFormLayout, QLineEdit, 
                             QSpinBox, QDoubleSpinBox, QComboBox, QLabel, QSplitter, 
                             QMessageBox, QColorDialog, QTableWidgetItem)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from database import db
from utils.dialogs import ItemSearchDialog
from utils.image_loader import ImageLoader

class IngredientsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        
        # --- LEVÁ ČÁST: Seznam ---
        left_layout = QVBoxLayout()
        self.ing_table = QTableWidget()
        self.ing_table.setColumnCount(3)
        self.ing_table.setHorizontalHeaderLabels(["ID Itemu", "Barva", "pH"])
        self.ing_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ing_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ing_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ing_table.clicked.connect(self.load_detail)
        left_layout.addWidget(self.ing_table)
        
        btn_box = QHBoxLayout()
        self.btn_refresh = QPushButton("Obnovit seznam")
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_add = QPushButton("Přidat novou ingredienci")
        self.btn_add.clicked.connect(self.add_new)
        btn_box.addWidget(self.btn_refresh)
        btn_box.addWidget(self.btn_add)
        left_layout.addLayout(btn_box)
        
        # --- PRAVÁ ČÁST: Detail ---
        self.detail_group = QGroupBox("Detail ingredience")
        self.detail_group.setEnabled(False)
        
        # Layout uvnitř GroupBoxu
        detail_inner_layout = QVBoxLayout()
        
        # Sekce s obrázkem a formulářem
        top_detail_layout = QHBoxLayout()
        
        # 1. Obrázek
        self.lbl_image = QLabel()
        self.lbl_image.setFixedSize(100, 100)
        self.lbl_image.setStyleSheet("border: 1px solid #555; background: #333;")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        
        img_layout = QVBoxLayout()
        img_layout.addWidget(QLabel("Náhled:"))
        img_layout.addWidget(self.lbl_image)
        img_layout.addStretch()
        top_detail_layout.addLayout(img_layout)

        # 2. Formulář
        form_layout = QFormLayout()

        self.inp_id = QLineEdit()
        self.inp_id.setReadOnly(True)
        self.inp_id.setStyleSheet("background-color: #444; color: #aaa;")
        
        self.inp_amount = QSpinBox()
        self.inp_amount.setRange(1, 255)
        self.inp_amount.setSuffix(" ml")
        
        self.inp_ph = QDoubleSpinBox()
        self.inp_ph.setRange(0, 14)
        self.inp_ph.setSingleStep(0.1)
        
        self.inp_type = QComboBox()
        self.inp_type.addItems(["bottle", "flask", "vial", "jar"])
        
        # Barvy
        color_layout = QHBoxLayout()
        self.inp_r = QSpinBox(); self.inp_r.setRange(0, 255); self.inp_r.setPrefix("R: ")
        self.inp_g = QSpinBox(); self.inp_g.setRange(0, 255); self.inp_g.setPrefix("G: ")
        self.inp_b = QSpinBox(); self.inp_b.setRange(0, 255); self.inp_b.setPrefix("B: ")
        
        for sb in [self.inp_r, self.inp_g, self.inp_b]:
            sb.valueChanged.connect(self.update_preview_color)
            color_layout.addWidget(sb)
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(40, 25)
        self.color_preview.setStyleSheet("border: 1px solid white;")
        color_layout.addWidget(self.color_preview)
        
        self.btn_pick_color = QPushButton("...")
        self.btn_pick_color.setFixedWidth(30)
        self.btn_pick_color.clicked.connect(self.open_color_picker)
        color_layout.addWidget(self.btn_pick_color)

        form_layout.addRow("ID Itemu:", self.inp_id)
        form_layout.addRow("Základní objem:", self.inp_amount)
        form_layout.addRow("pH:", self.inp_ph)
        form_layout.addRow("Typ nádoby:", self.inp_type)
        form_layout.addRow("Barva:", color_layout)
        
        top_detail_layout.addLayout(form_layout)
        detail_inner_layout.addLayout(top_detail_layout)

        # Tlačítka dole
        self.btn_save = QPushButton("Uložit změny")
        self.btn_save.setStyleSheet("background-color: #388E3C; font-weight: bold; padding: 6px;")
        self.btn_save.clicked.connect(self.save_data)
        
        self.btn_delete = QPushButton("Smazat")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; padding: 6px;")
        self.btn_delete.clicked.connect(self.delete_data)

        detail_inner_layout.addWidget(self.btn_save)
        detail_inner_layout.addWidget(self.btn_delete)
        detail_inner_layout.addStretch()
        
        self.detail_group.setLayout(detail_inner_layout)

        # --- OPRAVENÁ ČÁST: VYTVOŘENÍ PRAVÉHO LAYOUTU ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.detail_group)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        w_left = QWidget(); w_left.setLayout(left_layout)
        w_right = QWidget(); w_right.setLayout(right_layout) # Nyní right_layout existuje
        splitter.addWidget(w_left)
        splitter.addWidget(w_right)
        splitter.setSizes([450, 350])

        layout.addWidget(splitter)
        self.load_data()

    def load_data(self):
        rows = db.fetch_all("SELECT * FROM aprts_alchemist_ingredients")
        self.ing_table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            self.ing_table.insertRow(r_idx)
            self.ing_table.setItem(r_idx, 0, QTableWidgetItem(row['item_id']))
            
            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(row['r'], row['g'], row['b']))
            self.ing_table.setItem(r_idx, 1, color_item)
            
            self.ing_table.setItem(r_idx, 2, QTableWidgetItem(str(row['ph'])))
            self.ing_table.item(r_idx, 0).setData(Qt.UserRole, row)

    def load_detail(self):
        row = self.ing_table.currentRow()
        if row < 0: return
        data = self.ing_table.item(row, 0).data(Qt.UserRole)
        
        self.detail_group.setEnabled(True)
        self.inp_id.setText(data['item_id'])
        self.inp_amount.setValue(data['amount'])
        self.inp_ph.setValue(float(data['ph']))
        
        idx = self.inp_type.findText(data['type'])
        if idx >= 0:
            self.inp_type.setCurrentIndex(idx)
        else:
            self.inp_type.setCurrentIndex(0)

        self.inp_r.setValue(data['r'])
        self.inp_g.setValue(data['g'])
        self.inp_b.setValue(data['b'])
        self.update_preview_color()
        
        ImageLoader.load_image(data['item_id'], self.lbl_image)

    def update_preview_color(self):
        c = QColor(self.inp_r.value(), self.inp_g.value(), self.inp_b.value())
        self.color_preview.setStyleSheet(f"background-color: {c.name()}; border: 1px solid #777;")

    def open_color_picker(self):
        c = QColorDialog.getColor(QColor(self.inp_r.value(), self.inp_g.value(), self.inp_b.value()), self)
        if c.isValid():
            self.inp_r.setValue(c.red())
            self.inp_g.setValue(c.green())
            self.inp_b.setValue(c.blue())

    def save_data(self):
        query = """
            UPDATE aprts_alchemist_ingredients 
            SET amount=%s, ph=%s, type=%s, r=%s, g=%s, b=%s
            WHERE item_id=%s
        """
        params = (
            self.inp_amount.value(), self.inp_ph.value(), self.inp_type.currentText(),
            self.inp_r.value(), self.inp_g.value(), self.inp_b.value(),
            self.inp_id.text()
        )
        if db.execute(query, params):
            self.load_data()
            QMessageBox.information(self, "OK", "Ingredience uložena.")

    def add_new(self):
        dialog = ItemSearchDialog(self, "Přidat ingredienci")
        if dialog.exec_():
            item_id = dialog.get_selected_item()
            if not item_id: return
            
            check = db.fetch_all("SELECT * FROM aprts_alchemist_ingredients WHERE item_id=%s", (item_id,))
            if check:
                QMessageBox.warning(self, "Chyba", "Tato ingredience už existuje.")
                return

            query = """
                INSERT INTO aprts_alchemist_ingredients (item_id, r, g, b, ph, amount, type)
                VALUES (%s, 255, 255, 255, 7.0, 10, 'bottle')
            """
            if db.execute(query, (item_id,)):
                self.load_data()

    def delete_data(self):
        item_id = self.inp_id.text()
        if not item_id: return
        if QMessageBox.question(self, "Smazat", f"Opravdu smazat {item_id}?") == QMessageBox.Yes:
            db.execute("DELETE FROM aprts_alchemist_ingredients WHERE item_id=%s", (item_id,))
            self.load_data()
            self.detail_group.setEnabled(False)
            self.lbl_image.clear()