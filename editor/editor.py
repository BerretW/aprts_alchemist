import sys
import json
import requests
import pymysql
from pymysql.cursors import DictCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QTabWidget, QFormLayout, QSpinBox, QDoubleSpinBox, QSplitter,
                             QMessageBox, QDialog, QComboBox, QGroupBox, QHeaderView, QAbstractItemView, QColorDialog)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QPalette, QIcon, QPixmap, QAction

import config

# ==========================================================
# DATABASE MANAGER
# ==========================================================
class DatabaseManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        try:
            # 1. Vytvoříme kopii konfigurace, abychom neupravovali původní import
            cfg = config.DB_CONFIG.copy()
            
            # 2. Pokud je v configu 'cursorclass' jako text (což způsobuje chybu), odstraníme ho
            if 'cursorclass' in cfg:
                del cfg['cursorclass']

            # 3. Předáme konfiguraci + explicitně nastavíme třídu DictCursor
            # (DictCursor máme importovaný na začátku souboru z pymysql.cursors)
            self.conn = pymysql.connect(**cfg, cursorclass=DictCursor)
            return True
        except Exception as e:
            print(f"Chyba pripojeni k DB: {e}")
            return False

    def fetch_all(self, query, params=None):
        if not self.conn or not self.conn.open:
            if not self.connect(): return []
        with self.conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute(self, query, params=None):
        if not self.conn or not self.conn.open:
            if not self.connect(): return False
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"SQL Error: {e}")
            self.conn.rollback()
            return False

db = DatabaseManager()

# ==========================================================
# UTILS & STYLES
# ==========================================================
def set_dark_theme(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

# ==========================================================
# DIALOG: ADD NEW INGREDIENT FROM ITEMS TABLE
# ==========================================================
class AddIngredientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přidat novou ingredienci")
        self.resize(500, 400)
        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hledat item (název nebo label)...")
        self.search_input.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_input)

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(2)
        self.item_table.setHorizontalHeaderLabels(["ID Itemu", "Název (Label)"])
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.item_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.item_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.item_table)

        self.btn_add = QPushButton("Přidat vybrané")
        self.btn_add.clicked.connect(self.accept)
        layout.addWidget(self.btn_add)

        self.all_items = []
        self.load_items()

    def load_items(self):
        # Načteme všechny itemy z VORP items tabulky
        # POZN: Upravte název tabulky 'items' pokud se ve vaší DB jmenuje jinak (např. 'items_templates')
        rows = db.fetch_all("SELECT item, label FROM items") 
        self.all_items = rows
        self.filter_items("")

    def filter_items(self, text):
        text = text.lower()
        filtered = [i for i in self.all_items if text in i['item'].lower() or text in i['label'].lower()]
        
        self.item_table.setRowCount(0)
        for row_idx, item in enumerate(filtered):
            self.item_table.insertRow(row_idx)
            self.item_table.setItem(row_idx, 0, QTableWidgetItem(item['item']))
            self.item_table.setItem(row_idx, 1, QTableWidgetItem(item['label']))

    def get_selected_item(self):
        row = self.item_table.currentRow()
        if row < 0: return None
        return self.item_table.item(row, 0).text()

# ==========================================================
# WIDGET: INGREDIENTS EDITOR
# ==========================================================
class IngredientsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        
        # Left: List
        left_panel = QVBoxLayout()
        self.ing_table = QTableWidget()
        self.ing_table.setColumnCount(3)
        self.ing_table.setHorizontalHeaderLabels(["ID", "RGB Preview", "pH"])
        self.ing_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ing_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ing_table.clicked.connect(self.load_detail)
        left_panel.addWidget(self.ing_table)
        
        btn_box = QHBoxLayout()
        self.btn_refresh = QPushButton("Obnovit")
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_add = QPushButton("Přidat novou")
        self.btn_add.clicked.connect(self.add_new)
        btn_box.addWidget(self.btn_refresh)
        btn_box.addWidget(self.btn_add)
        left_panel.addLayout(btn_box)
        
        # Right: Detail Form
        self.detail_group = QGroupBox("Detail ingredience")
        self.detail_group.setEnabled(False)
        form_layout = QFormLayout()

        self.inp_id = QLineEdit()
        self.inp_id.setReadOnly(True)
        self.inp_amount = QSpinBox(); self.inp_amount.setRange(1, 1000); self.inp_amount.setSuffix(" ml")
        self.inp_ph = QDoubleSpinBox(); self.inp_ph.setRange(0, 14); self.inp_ph.setSingleStep(0.1)
        self.inp_type = QComboBox(); self.inp_type.addItems(["liquid", "solid"])
        
        # Colors
        color_layout = QHBoxLayout()
        self.inp_r = QSpinBox(); self.inp_r.setRange(0, 255)
        self.inp_g = QSpinBox(); self.inp_g.setRange(0, 255)
        self.inp_b = QSpinBox(); self.inp_b.setRange(0, 255)
        
        for sb in [self.inp_r, self.inp_g, self.inp_b]:
            sb.valueChanged.connect(self.update_preview_color)
            color_layout.addWidget(sb)
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(50, 25)
        self.color_preview.setStyleSheet("background-color: #000; border: 1px solid #555;")
        color_layout.addWidget(self.color_preview)
        
        self.btn_pick_color = QPushButton("Vybrat barvu")
        self.btn_pick_color.clicked.connect(self.open_color_picker)
        color_layout.addWidget(self.btn_pick_color)

        form_layout.addRow("ID Itemu:", self.inp_id)
        form_layout.addRow("Množství (ml):", self.inp_amount)
        form_layout.addRow("pH:", self.inp_ph)
        form_layout.addRow("Typ:", self.inp_type)
        form_layout.addRow("Barva (R,G,B):", color_layout)

        self.btn_save = QPushButton("Uložit změny")
        self.btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 5px;")
        self.btn_save.clicked.connect(self.save_data)
        
        self.btn_delete = QPushButton("Smazat ingredienci")
        self.btn_delete.setStyleSheet("background-color: #c62828; color: white; padding: 5px;")
        self.btn_delete.clicked.connect(self.delete_data)

        self.detail_group.setLayout(form_layout)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.detail_group)
        right_layout.addWidget(self.btn_save)
        right_layout.addWidget(self.btn_delete)
        right_layout.addStretch()

        splitter = QSplitter()
        left_widget = QWidget(); left_widget.setLayout(left_panel)
        right_widget = QWidget(); right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 300])

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
            
            # Uložíme celá data do prvního itemu pro snadný přístup
            self.ing_table.item(r_idx, 0).setData(Qt.ItemDataRole.UserRole, row)

    def load_detail(self):
        row = self.ing_table.currentRow()
        if row < 0: return
        data = self.ing_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        self.detail_group.setEnabled(True)
        self.inp_id.setText(data['item_id'])
        self.inp_amount.setValue(data['amount'])
        self.inp_ph.setValue(float(data['ph']))
        self.inp_type.setCurrentText(data['type'])
        self.inp_r.setValue(data['r'])
        self.inp_g.setValue(data['g'])
        self.inp_b.setValue(data['b'])
        self.update_preview_color()

    def update_preview_color(self):
        c = QColor(self.inp_r.value(), self.inp_g.value(), self.inp_b.value())
        self.color_preview.setStyleSheet(f"background-color: {c.name()}; border: 1px solid #fff;")

    def open_color_picker(self):
        c = QColorDialog.getColor(QColor(self.inp_r.value(), self.inp_g.value(), self.inp_b.value()), self, "Vyber barvu")
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
            QMessageBox.information(self, "OK", "Uloženo.")

    def add_new(self):
        dialog = AddIngredientDialog(self)
        if dialog.exec():
            item_id = dialog.get_selected_item()
            if not item_id: return
            
            # Check if exists
            exists = db.fetch_all("SELECT * FROM aprts_alchemist_ingredients WHERE item_id=%s", (item_id,))
            if exists:
                QMessageBox.warning(self, "Chyba", "Tato ingredience už v databázi alchymie je.")
                return

            # Insert default
            query = """
                INSERT INTO aprts_alchemist_ingredients (item_id, r, g, b, ph, amount, type)
                VALUES (%s, 255, 255, 255, 7.0, 50, 'liquid')
            """
            if db.execute(query, (item_id,)):
                self.load_data()

    def delete_data(self):
        item_id = self.inp_id.text()
        if not item_id: return
        if QMessageBox.question(self, "Smazat", f"Opravdu smazat {item_id} z alchymie?") == QMessageBox.StandardButton.Yes:
            db.execute("DELETE FROM aprts_alchemist_ingredients WHERE item_id=%s", (item_id,))
            self.load_data()
            self.detail_group.setEnabled(False)

# ==========================================================
# WIDGET: RECIPE CALCULATOR (LOGIKA PRO NAVRHOVÁNÍ PARAMETRŮ)
# ==========================================================
class CalculatorWidget(QGroupBox):
    def __init__(self, parent_recipe_widget):
        super().__init__("⚗️ Simulátor a Kalkulačka Parametrů")
        self.parent_recipe_widget = parent_recipe_widget
        self.ingredients_cache = [] # Načteno z DB
        
        layout = QVBoxLayout()
        
        # 1. Výběr surovin
        self.combo_ing = QComboBox()
        self.spin_count = QSpinBox(); self.spin_count.setRange(1, 10); self.spin_count.setSuffix(" ks")
        
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Přidat:"))
        add_layout.addWidget(self.combo_ing, 1)
        add_layout.addWidget(self.spin_count)
        btn_add = QPushButton("+"); btn_add.setFixedWidth(30)
        btn_add.clicked.connect(self.add_ingredient)
        add_layout.addWidget(btn_add)
        layout.addLayout(add_layout)
        
        # 2. Seznam v kotlíku
        self.beaker_table = QTableWidget()
        self.beaker_table.setColumnCount(3)
        self.beaker_table.setHorizontalHeaderLabels(["Surovina", "Počet", "Info"])
        self.beaker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.beaker_table.setMaximumHeight(150)
        layout.addWidget(self.beaker_table)
        
        btn_clear = QPushButton("Vylít kotlík (Reset)")
        btn_clear.clicked.connect(self.reset_beaker)
        layout.addWidget(btn_clear)

        # 3. Výsledky (Real-time)
        res_group = QGroupBox("Výsledné vlastnosti směsi")
        res_layout = QFormLayout()
        
        self.lbl_res_color = QLabel("---")
        self.lbl_res_color.setStyleSheet("background: #333; border: 1px solid #777;")
        self.lbl_res_color.setFixedSize(100, 25)
        
        self.lbl_res_ph = QLabel("7.0")
        self.lbl_res_amount = QLabel("0 ml")
        
        res_layout.addRow("Barva:", self.lbl_res_color)
        res_layout.addRow("pH:", self.lbl_res_ph)
        res_layout.addRow("Objem:", self.lbl_res_amount)
        res_group.setLayout(res_layout)
        layout.addWidget(res_group)
        
        # 4. Akce "Navrhnout do receptu"
        self.btn_apply = QPushButton("Použít tyto parametry v receptu")
        self.btn_apply.setStyleSheet("background-color: #0277bd; font-weight: bold; height: 30px;")
        self.btn_apply.clicked.connect(self.apply_to_recipe)
        layout.addWidget(self.btn_apply)

        self.setLayout(layout)
        self.beaker_contents = [] # List of {data: dict, count: int}
        self.current_result = {"r":0, "g":0, "b":0, "ph":0, "amount":0}

    def load_ingredients(self):
        self.ingredients_cache = db.fetch_all("SELECT * FROM aprts_alchemist_ingredients")
        self.combo_ing.clear()
        for ing in self.ingredients_cache:
            self.combo_ing.addItem(f"{ing['item_id']} (pH {ing['ph']}, {ing['amount']}ml)", ing)

    def add_ingredient(self):
        data = self.combo_ing.currentData()
        count = self.spin_count.value()
        
        self.beaker_contents.append({"data": data, "count": count})
        self.update_beaker_ui()
        self.calculate_mix()

    def reset_beaker(self):
        self.beaker_contents = []
        self.update_beaker_ui()
        self.calculate_mix()

    def update_beaker_ui(self):
        self.beaker_table.setRowCount(0)
        for idx, item in enumerate(self.beaker_contents):
            self.beaker_table.insertRow(idx)
            self.beaker_table.setItem(idx, 0, QTableWidgetItem(item['data']['item_id']))
            self.beaker_table.setItem(idx, 1, QTableWidgetItem(str(item['count'])))
            info = f"pH {item['data']['ph']}"
            self.beaker_table.setItem(idx, 2, QTableWidgetItem(info))

    def calculate_mix(self):
        # Stejná logika jako v LUA scriptu
        if not self.beaker_contents:
            self.lbl_res_color.setStyleSheet("background: #333;")
            self.lbl_res_ph.setText("7.0")
            self.lbl_res_amount.setText("0 ml")
            self.current_result = None
            return

        current_mix = {'r': 0, 'g': 0, 'b': 0, 'ph': 0, 'amount': 0}
        total_amount = 0

        for entry in self.beaker_contents:
            ing = entry['data']
            count = entry['count']
            item_total_amount = ing['amount'] * count
            
            if total_amount == 0:
                current_mix['r'] = ing['r']
                current_mix['g'] = ing['g']
                current_mix['b'] = ing['b']
                current_mix['ph'] = float(ing['ph'])
                total_amount = item_total_amount
            else:
                new_total = total_amount + item_total_amount
                # Weighted average formula
                current_mix['r'] = ((current_mix['r'] * total_amount) + (ing['r'] * item_total_amount)) / new_total
                current_mix['g'] = ((current_mix['g'] * total_amount) + (ing['g'] * item_total_amount)) / new_total
                current_mix['b'] = ((current_mix['b'] * total_amount) + (ing['b'] * item_total_amount)) / new_total
                current_mix['ph'] = ((current_mix['ph'] * total_amount) + (ing['ph'] * item_total_amount)) / new_total
                total_amount = new_total

        current_mix['amount'] = total_amount
        self.current_result = current_mix
        
        # Update UI
        c_style = f"background-color: rgb({int(current_mix['r'])}, {int(current_mix['g'])}, {int(current_mix['b'])});"
        self.lbl_res_color.setStyleSheet(c_style)
        self.lbl_res_ph.setText(f"{current_mix['ph']:.2f}")
        self.lbl_res_amount.setText(f"{int(total_amount)} ml")

    def apply_to_recipe(self):
        if not self.current_result:
            return
        
        # Předáme vypočtená data rodičovskému widgetu
        self.parent_recipe_widget.apply_calculated_params(
            r=int(self.current_result['r']),
            g=int(self.current_result['g']),
            b=int(self.current_result['b']),
            ph=self.current_result['ph'],
            amount=int(self.current_result['amount']),
            ingredients=self.beaker_contents # Předáme i seznam surovin pro requirements
        )
        QMessageBox.information(self, "Hotovo", "Parametry (Barva, pH, Requirements) byly nastaveny do formuláře receptu.")


# ==========================================================
# WIDGET: RECIPE EDITOR
# ==========================================================
class RecipesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.loaded_recipe_id = None

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # LEFT: List of Recipes
        left_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID Receptu", "Label"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.clicked.connect(self.load_detail)
        left_layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Obnovit"); self.btn_refresh.clicked.connect(self.load_list)
        self.btn_create = QPushButton("Nový recept"); self.btn_create.clicked.connect(self.create_new)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_create)
        left_layout.addLayout(btn_layout)

        # RIGHT: Detail + Simulator
        right_scroll_layout = QVBoxLayout()
        
        # --- Form Basic Info ---
        self.form_group = QGroupBox("Základní info")
        form = QFormLayout()
        self.inp_name = QLineEdit() # ID
        self.inp_label = QLineEdit()
        self.inp_reward_item = QLineEdit()
        self.inp_reward_count = QSpinBox()
        self.inp_skill = QSpinBox()
        
        form.addRow("ID (name):", self.inp_name)
        form.addRow("Label (Název):", self.inp_label)
        form.addRow("Výsledek (Item ID):", self.inp_reward_item)
        form.addRow("Počet ks:", self.inp_reward_count)
        form.addRow("Min. Skill:", self.inp_skill)
        self.form_group.setLayout(form)
        
        # --- Conditions ---
        self.cond_group = QGroupBox("Podmínky a Cíle (Nastaví kalkulačka)")
        cond_layout = QFormLayout()
        
        # Color Target
        color_row = QHBoxLayout()
        self.inp_cr = QSpinBox(); self.inp_cr.setRange(0, 255)
        self.inp_cg = QSpinBox(); self.inp_cg.setRange(0, 255)
        self.inp_cb = QSpinBox(); self.inp_cb.setRange(0, 255)
        self.inp_ctol = QSpinBox(); self.inp_ctol.setValue(30); self.inp_ctol.setSuffix(" tol")
        color_row.addWidget(QLabel("R:")); color_row.addWidget(self.inp_cr)
        color_row.addWidget(QLabel("G:")); color_row.addWidget(self.inp_cg)
        color_row.addWidget(QLabel("B:")); color_row.addWidget(self.inp_cb)
        color_row.addWidget(self.inp_ctol)
        
        # pH Range
        ph_row = QHBoxLayout()
        self.inp_ph_min = QDoubleSpinBox(); self.inp_ph_min.setSingleStep(0.1)
        self.inp_ph_max = QDoubleSpinBox(); self.inp_ph_max.setSingleStep(0.1); self.inp_ph_max.setValue(14)
        ph_row.addWidget(QLabel("Min:")); ph_row.addWidget(self.inp_ph_min)
        ph_row.addWidget(QLabel("Max:")); ph_row.addWidget(self.inp_ph_max)

        self.inp_min_amount = QSpinBox(); self.inp_min_amount.setRange(1, 5000)

        cond_layout.addRow("Cílová Barva:", color_row)
        cond_layout.addRow("Rozsah pH:", ph_row)
        cond_layout.addRow("Min. Objem (ml):", self.inp_min_amount)
        self.cond_group.setLayout(cond_layout)

        # --- Process ---
        self.proc_group = QGroupBox("Proces (Teplota a Čas)")
        proc_layout = QHBoxLayout()
        
        self.inp_temp = QSpinBox(); self.inp_temp.setRange(0, 500); self.inp_temp.setSuffix("°C")
        self.inp_temp_tol = QSpinBox(); self.inp_temp_tol.setSuffix(" tol")
        
        self.inp_time = QSpinBox(); self.inp_time.setRange(0, 3600); self.inp_time.setSuffix(" sec")
        self.inp_time_tol = QSpinBox(); self.inp_time_tol.setSuffix(" tol")
        
        proc_layout.addWidget(QLabel("Teplota:"))
        proc_layout.addWidget(self.inp_temp)
        proc_layout.addWidget(self.inp_temp_tol)
        proc_layout.addWidget(QLabel("| Čas:"))
        proc_layout.addWidget(self.inp_time)
        proc_layout.addWidget(self.inp_time_tol)
        self.proc_group.setLayout(proc_layout)
        
        # --- Requirements (JSON Text Edit - simplified for now) ---
        self.req_group = QGroupBox("Požadované suroviny (JSON)")
        req_layout = QVBoxLayout()
        self.inp_requirements = QLineEdit() # Store as JSON string
        self.inp_requirements.setPlaceholderText('[{"item": "water", "minAmount": 100}]')
        req_layout.addWidget(self.inp_requirements)
        self.req_group.setLayout(req_layout)

        # --- SIMULATOR ---
        self.calculator = CalculatorWidget(self)

        # Buttons
        self.btn_save = QPushButton("💾 ULOŽIT RECEPT")
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet("background-color: #2e7d32; font-size: 14px;")
        self.btn_save.clicked.connect(self.save_recipe)
        
        self.btn_delete = QPushButton("Smazat recept")
        self.btn_delete.setStyleSheet("background-color: #c62828;")
        self.btn_delete.clicked.connect(self.delete_recipe)

        # Adding to layout
        right_scroll_layout.addWidget(self.form_group)
        right_scroll_layout.addWidget(self.cond_group)
        right_scroll_layout.addWidget(self.req_group)
        right_scroll_layout.addWidget(self.proc_group)
        right_scroll_layout.addWidget(self.calculator) # Calculator here
        right_scroll_layout.addWidget(self.btn_save)
        right_scroll_layout.addWidget(self.btn_delete)
        right_scroll_layout.addStretch()

        splitter = QSplitter()
        w_left = QWidget(); w_left.setLayout(left_layout)
        w_right = QWidget(); w_right.setLayout(right_scroll_layout)
        
        splitter.addWidget(w_left)
        splitter.addWidget(w_right)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
        
        self.toggle_inputs(False)
        self.load_list()

    def toggle_inputs(self, enable):
        self.form_group.setEnabled(enable)
        self.cond_group.setEnabled(enable)
        self.proc_group.setEnabled(enable)
        self.req_group.setEnabled(enable)
        self.btn_save.setEnabled(enable)
        self.calculator.setEnabled(enable)
        if enable:
            self.calculator.load_ingredients()

    def load_list(self):
        rows = db.fetch_all("SELECT name, label FROM aprts_alchemist_recipes")
        self.table.setRowCount(0)
        for idx, row in enumerate(rows):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(row['name']))
            self.table.setItem(idx, 1, QTableWidgetItem(row['label']))

    def load_detail(self):
        row = self.table.currentRow()
        if row < 0: return
        recipe_id = self.table.item(row, 0).text()
        
        data = db.fetch_all("SELECT * FROM aprts_alchemist_recipes WHERE name=%s", (recipe_id,))
        if not data: return
        r = data[0] # Record

        self.loaded_recipe_id = r['name']
        self.toggle_inputs(True)
        
        # Fill inputs
        self.inp_name.setText(r['name'])
        self.inp_label.setText(r['label'])
        self.inp_reward_item.setText(r['rewardItem'])
        self.inp_reward_count.setValue(r['rewardCount'])
        self.inp_skill.setValue(r['minSkillToIdentify'])
        
        self.inp_ph_min.setValue(float(r['phMin']))
        self.inp_ph_max.setValue(float(r['phMax']))
        self.inp_min_amount.setValue(r['minTotalAmount'])
        
        # Color JSON
        try:
            c = json.loads(r['color_target']) if r['color_target'] else {'r':0,'g':0,'b':0}
            self.inp_cr.setValue(c.get('r', 0))
            self.inp_cg.setValue(c.get('g', 0))
            self.inp_cb.setValue(c.get('b', 0))
        except: pass
        self.inp_ctol.setValue(r['colorTolerance'])
        
        # Process
        self.inp_temp.setValue(r['process_temp'])
        self.inp_temp_tol.setValue(r['process_tempTolerance'])
        self.inp_time.setValue(r['process_time'])
        self.inp_time_tol.setValue(r['process_timeTolerance'])
        
        # Requirements
        self.inp_requirements.setText(r['requirements'])

    def create_new(self):
        new_name = "new_recipe_" + str(pymysql.constants.ER.DUP_ENTRY) # Random placeholder
        self.loaded_recipe_id = None
        self.toggle_inputs(True)
        self.inp_name.setText("new_recipe")
        self.inp_name.setFocus()
        self.inp_requirements.setText("[]")

    def apply_calculated_params(self, r, g, b, ph, amount, ingredients):
        # 1. Barva
        self.inp_cr.setValue(r)
        self.inp_cg.setValue(g)
        self.inp_cb.setValue(b)
        
        # 2. pH - nastavíme malou toleranci kolem vypočtené hodnoty
        self.inp_ph_min.setValue(max(0, ph - 0.5))
        self.inp_ph_max.setValue(min(14, ph + 0.5))
        
        # 3. Množství
        self.inp_min_amount.setValue(amount)
        
        # 4. Requirements (Suroviny)
        # Převedeme obsah kotlíku na JSON requirements
        req_list = []
        for entry in ingredients:
            item_id = entry['data']['item_id']
            # Spočítáme celkové ml pro tuto ingredienci
            total_ml = entry['count'] * entry['data']['amount']
            req_list.append({
                "item": item_id,
                "minAmount": total_ml
            })
        
        self.inp_requirements.setText(json.dumps(req_list))

    def save_recipe(self):
        # Build JSONs
        color_target = json.dumps({"r": self.inp_cr.value(), "g": self.inp_cg.value(), "b": self.inp_cb.value()})
        requirements = self.inp_requirements.text() # Assuming user or calc put valid JSON
        
        params = (
            self.inp_label.text(),
            self.inp_skill.value(),
            color_target,
            self.inp_ctol.value(),
            self.inp_ph_min.value(),
            self.inp_ph_max.value(),
            self.inp_min_amount.value(),
            requirements,
            self.inp_reward_item.text(),
            self.inp_reward_count.value(),
            self.inp_temp.value(),
            self.inp_time.value(),
            self.inp_temp_tol.value(),
            self.inp_time_tol.value(),
            self.inp_name.text() # WHERE / ID
        )
        
        # Check if updating or inserting
        exists = False
        if self.loaded_recipe_id:
             check = db.fetch_all("SELECT name FROM aprts_alchemist_recipes WHERE name=%s", (self.loaded_recipe_id,))
             if check: exists = True

        if exists:
            query = """
                UPDATE aprts_alchemist_recipes SET
                label=%s, minSkillToIdentify=%s, color_target=%s, colorTolerance=%s,
                phMin=%s, phMax=%s, minTotalAmount=%s, requirements=%s,
                rewardItem=%s, rewardCount=%s, process_temp=%s, process_time=%s,
                process_tempTolerance=%s, process_timeTolerance=%s
                WHERE name=%s
            """
            if db.execute(query, params):
                QMessageBox.information(self, "Uloženo", "Recept aktualizován.")
        else:
            # Insert logic needs different params order
            query = """
                INSERT INTO aprts_alchemist_recipes (
                label, minSkillToIdentify, color_target, colorTolerance,
                phMin, phMax, minTotalAmount, requirements,
                rewardItem, rewardCount, process_temp, process_time,
                process_tempTolerance, process_timeTolerance, name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            if db.execute(query, params):
                QMessageBox.information(self, "Uloženo", "Recept vytvořen.")
                self.loaded_recipe_id = self.inp_name.text()
        
        self.load_list()

    def delete_recipe(self):
        if not self.loaded_recipe_id: return
        if QMessageBox.question(self, "Smazat", "Opravdu smazat recept?") == QMessageBox.StandardButton.Yes:
            db.execute("DELETE FROM aprts_alchemist_recipes WHERE name=%s", (self.loaded_recipe_id,))
            self.load_list()
            self.toggle_inputs(False)

# ==========================================================
# MAIN WINDOW
# ==========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedM Alchemist Editor")
        self.resize(1000, 700)
        
        # Connect to DB first
        if not db.connect():
            QMessageBox.critical(self, "Chyba", "Nepodařilo se připojit k databázi! Zkontrolujte config.py")
            sys.exit(1)

        tabs = QTabWidget()
        tabs.addTab(IngredientsWidget(), "Ingredience")
        tabs.addTab(RecipesWidget(), "Recepty & Tvorba")
        
        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())