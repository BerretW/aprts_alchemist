# widgets/calculator.py
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                             QSpinBox, QPushButton, QTableWidget, QHeaderView, 
                             QAbstractItemView, QFrame, QLabel, QMessageBox, QTableWidgetItem,
                             QLineEdit, QWidget, QSplitter)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QIcon, QFont
from database import db
from utils.image_loader import ImageLoader

class CalculatorWidget(QGroupBox):
    def __init__(self, parent_recipe_widget):
        super().__init__("⚗️ Simulátor Míchání & Kalkulačka")
        self.parent_recipe = parent_recipe_widget
        self.ingredients_cache = [] 
        self.beaker_contents = []   
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # ==========================================
        # 1. SEKCE: VÝBĚR SUROVIN (GRID)
        # ==========================================
        sel_group = QWidget()
        sel_layout = QVBoxLayout(sel_group)
        sel_layout.setContentsMargins(0,0,0,0)
        
        # Horní lišta: Refresh | Filtr | Počet
        top_bar = QHBoxLayout()
        
        # Tlačítko pro obnovení (NOVÉ)
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedWidth(30)
        self.btn_refresh.setToolTip("Znovu načíst ingredience z DB")
        self.btn_refresh.clicked.connect(self.load_ingredients)
        
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Hledat surovinu...")
        self.txt_filter.textChanged.connect(self.filter_ingredients)
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 20)
        self.spin_count.setSuffix(" ks")
        self.spin_count.setFixedWidth(80)
        
        top_bar.addWidget(self.btn_refresh) # Přidáno tlačítko
        top_bar.addWidget(self.txt_filter)
        top_bar.addWidget(QLabel("Množství:"))
        top_bar.addWidget(self.spin_count)
        
        sel_layout.addLayout(top_bar)

        # Mřížka (ListWidget v IconMode)
        self.grid_list = QListWidget()
        self.grid_list.setViewMode(QListWidget.IconMode)
        self.grid_list.setIconSize(QSize(48, 48))
        self.grid_list.setResizeMode(QListWidget.Adjust)
        self.grid_list.setGridSize(QSize(85, 110)) 
        self.grid_list.setSpacing(5)
        self.grid_list.setMovement(QListWidget.Static)
        self.grid_list.setSelectionMode(QAbstractItemView.SingleSelection)
        # Stylování pro lepší viditelnost
        self.grid_list.setStyleSheet("""
            QListWidget { background-color: #222; border: 1px solid #444; }
            QListWidget::item { 
                background-color: #333; 
                border-radius: 5px; 
                padding: 5px; 
                color: #eee;
            }
            QListWidget::item:hover { background-color: #444; }
            QListWidget::item:selected { background-color: #0277bd; border: 1px solid #4FC3F7; }
        """)
        self.grid_list.itemClicked.connect(self.add_ingredient_from_grid)
        self.grid_list.setMinimumHeight(200) 
        
        sel_layout.addWidget(self.grid_list)
        layout.addWidget(sel_group)
        
        # ==========================================
        # 2. SEKCE: KOTLÍK A VÝSLEDEK
        # ==========================================
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0,0,0,0)

        # --- LEVÁ ČÁST: Tabulka ---
        beaker_group = QGroupBox("Obsah kotlíku")
        beaker_layout = QVBoxLayout(beaker_group)
        
        self.beaker_table = QTableWidget()
        self.beaker_table.setColumnCount(4)
        self.beaker_table.setHorizontalHeaderLabels(["Surovina", "Ks", "Info", ""])
        self.beaker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.beaker_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.beaker_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.beaker_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.beaker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.beaker_table.verticalHeader().setVisible(False)
        self.beaker_table.setStyleSheet("QTableWidget { border: none; background: #2b2b2b; }")
        
        beaker_layout.addWidget(self.beaker_table)
        
        btn_clear = QPushButton("🗑️ Vylít celý kotlík")
        btn_clear.setStyleSheet("background-color: #c62828; color: white; padding: 4px; font-size: 11px;")
        btn_clear.clicked.connect(self.reset_beaker)
        beaker_layout.addWidget(btn_clear)

        # --- PRAVÁ ČÁST: Výsledek ---
        res_group = QGroupBox("Výsledek")
        res_group.setFixedWidth(200)
        res_layout = QVBoxLayout(res_group)
        
        self.lbl_res_color = QLabel()
        self.lbl_res_color.setFixedSize(80, 80)
        self.lbl_res_color.setStyleSheet("background-color: #111; border: 2px solid #555; border-radius: 40px;")
        self.lbl_res_color.setAlignment(Qt.AlignCenter)
        
        self.lbl_ph = QLabel("pH: 7.00")
        self.lbl_ph.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7; margin-top: 5px;")
        self.lbl_ph.setAlignment(Qt.AlignCenter)
        
        self.lbl_amount = QLabel("0 ml")
        self.lbl_amount.setStyleSheet("color: #aaa;")
        self.lbl_amount.setAlignment(Qt.AlignCenter)
        
        self.btn_apply = QPushButton("Použít v receptu\n⬇️")
        self.btn_apply.setFixedHeight(50)
        self.btn_apply.setStyleSheet("""
            QPushButton { background-color: #2e7d32; font-weight: bold; font-size: 13px; border-radius: 4px; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.btn_apply.clicked.connect(self.apply_to_recipe)

        res_layout.addStretch()
        res_layout.addWidget(self.lbl_res_color, 0, Qt.AlignCenter)
        res_layout.addWidget(self.lbl_ph)
        res_layout.addWidget(self.lbl_amount)
        res_layout.addSpacing(15)
        res_layout.addWidget(self.btn_apply)
        res_layout.addStretch()

        bottom_layout.addWidget(beaker_group, 2)
        bottom_layout.addWidget(res_group, 1)
        
        layout.addWidget(bottom_widget)
        self.setLayout(layout)
        
        # --- DŮLEŽITÉ: Načíst data hned při startu ---
        self.load_ingredients()

    def load_ingredients(self):
        """Načte ingredience z DB a naplní grid."""
        try:
            # Debug print do konzole
            print("DEBUG: Načítám ingredience pro kalkulačku...") 
            
            rows = db.fetch_all("SELECT * FROM aprts_alchemist_ingredients ORDER BY item_id")
            self.ingredients_cache = rows
            
            print(f"DEBUG: Nalezeno {len(rows)} záznamů.")
            
            self.populate_grid(self.ingredients_cache)
        except Exception as e:
            print(f"CHYBA při načítání ingrediencí: {e}")

    def populate_grid(self, items):
        self.grid_list.clear()
        for ing in items:
            short_name = ing['item_id']
            if len(short_name) > 12: short_name = short_name[:10] + "..."
            
            display_text = f"{short_name}\n(pH {ing['ph']})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, ing)
            item.setToolTip(f"ID: {ing['item_id']}\npH: {ing['ph']}\nBarva RGB: {ing['r']},{ing['g']},{ing['b']}\nObjem: {ing['amount']}ml")
            item.setTextAlignment(Qt.AlignCenter)
            
            ImageLoader.load_icon_to_item(ing['item_id'], item)
            
            self.grid_list.addItem(item)

    def filter_ingredients(self, text):
        text = text.lower()
        filtered = [i for i in self.ingredients_cache if text in i['item_id'].lower()]
        self.populate_grid(filtered)

    def add_ingredient_from_grid(self, item):
        data = item.data(Qt.UserRole)
        count = self.spin_count.value()
        self.beaker_contents.append({"data": data, "count": count})
        self.update_beaker_ui()
        self.calculate_mix()
        self.grid_list.clearSelection()

    def remove_item_at_row(self):
        sender_btn = self.sender()
        if not sender_btn: return
        index = sender_btn.property("row_index")
        if index is not None and 0 <= index < len(self.beaker_contents):
            del self.beaker_contents[index]
            self.update_beaker_ui()
            self.calculate_mix()

    def reset_beaker(self):
        self.beaker_contents = []
        self.update_beaker_ui()
        self.calculate_mix()

    def update_beaker_ui(self):
        self.beaker_table.setRowCount(0)
        for idx, entry in enumerate(self.beaker_contents):
            self.beaker_table.insertRow(idx)
            
            item_name = QTableWidgetItem(entry['data']['item_id'])
            self.beaker_table.setItem(idx, 0, item_name)
            self.beaker_table.setItem(idx, 1, QTableWidgetItem(str(entry['count'])))
            info = f"pH {entry['data']['ph']}"
            self.beaker_table.setItem(idx, 2, QTableWidgetItem(info))
            
            btn_rem = QPushButton("❌")
            btn_rem.setFixedSize(24, 20)
            btn_rem.setStyleSheet("color: #ff5252; font-weight: bold; border: none; background: transparent;")
            btn_rem.setCursor(Qt.PointingHandCursor)
            btn_rem.setProperty("row_index", idx)
            btn_rem.clicked.connect(self.remove_item_at_row)
            
            w = QWidget()
            l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setAlignment(Qt.AlignCenter)
            l.addWidget(btn_rem)
            self.beaker_table.setCellWidget(idx, 3, w)

    def calculate_mix(self):
        if not self.beaker_contents:
            self.lbl_res_color.setStyleSheet("background: #111; border: 2px solid #555; border-radius: 40px;")
            self.lbl_ph.setText("pH: 7.00")
            self.lbl_amount.setText("0 ml")
            self.current_result = None
            return

        mix = {'r': 0, 'g': 0, 'b': 0, 'ph': 0.0, 'amount': 0}
        total_amount = 0

        for entry in self.beaker_contents:
            ing = entry['data']
            count = entry['count']
            item_total_amount = ing['amount'] * count
            ing_ph = float(ing['ph'])
            
            if total_amount == 0:
                mix['r'] = ing['r']
                mix['g'] = ing['g']
                mix['b'] = ing['b']
                mix['ph'] = ing_ph
                total_amount = item_total_amount
            else:
                new_total = total_amount + item_total_amount
                mix['r'] = ((mix['r'] * total_amount) + (ing['r'] * item_total_amount)) / new_total
                mix['g'] = ((mix['g'] * total_amount) + (ing['g'] * item_total_amount)) / new_total
                mix['b'] = ((mix['b'] * total_amount) + (ing['b'] * item_total_amount)) / new_total
                mix['ph'] = ((mix['ph'] * total_amount) + (ing_ph * item_total_amount)) / new_total
                total_amount = new_total

        mix['amount'] = total_amount
        self.current_result = mix
        
        c_style = f"background-color: rgb({int(mix['r'])}, {int(mix['g'])}, {int(mix['b'])});"
        self.lbl_res_color.setStyleSheet(c_style + "border: 2px solid white; border-radius: 40px;")
        self.lbl_ph.setText(f"pH: {mix['ph']:.2f}")
        self.lbl_amount.setText(f"{int(total_amount)} ml")

    def apply_to_recipe(self):
        if not self.current_result:
            QMessageBox.warning(self, "Pozor", "Kotlík je prázdný.")
            return
        self.parent_recipe.apply_simulated_data(self.current_result, self.beaker_contents)
        QMessageBox.information(self, "Hotovo", "Výsledné hodnoty byly nastaveny do receptu.")