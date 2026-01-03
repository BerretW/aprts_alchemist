# widgets/calculator.py
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                             QSpinBox, QPushButton, QTableWidget, QHeaderView, 
                             QAbstractItemView, QFrame, QLabel, QMessageBox, QTableWidgetItem,
                             QLineEdit, QWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QIcon
from database import db
from utils.image_loader import ImageLoader

class CalculatorWidget(QGroupBox):
    def __init__(self, parent_recipe_widget):
        super().__init__("⚗️ Simulátor Míchání & Kalkulačka")
        self.parent_recipe = parent_recipe_widget
        self.ingredients_cache = [] # Data z DB
        self.beaker_contents = []   # Co je v kotlíku
        
        # Hlavní layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # --- SEKCE 1: VÝBĚR SUROVIN (Grid s ikonami) ---
        sel_group = QGroupBox("Dostupné suroviny")
        sel_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #444; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        sel_layout = QVBoxLayout(sel_group)
        
        # Filtr a počet
        filter_layout = QHBoxLayout()
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Hledat surovinu...")
        self.txt_filter.textChanged.connect(self.filter_ingredients)
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 20)
        self.spin_count.setSuffix(" ks")
        self.spin_count.setToolTip("Kolik kusů přidat kliknutím")
        
        filter_layout.addWidget(self.txt_filter)
        filter_layout.addWidget(QLabel("Množství:"))
        filter_layout.addWidget(self.spin_count)
        sel_layout.addLayout(filter_layout)

        # Mřížka (ListWidget v IconMode)
        self.grid_list = QListWidget()
        self.grid_list.setViewMode(QListWidget.IconMode)
        self.grid_list.setIconSize(QSize(48, 48))
        self.grid_list.setResizeMode(QListWidget.Adjust)
        self.grid_list.setGridSize(QSize(80, 100)) # Velikost buňky
        self.grid_list.setSpacing(5)
        self.grid_list.setMovement(QListWidget.Static)
        self.grid_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.grid_list.itemClicked.connect(self.add_ingredient_from_grid)
        # Nastavíme fixní výšku, aby to nezabíralo moc místa, ale dalo se scrollovat
        self.grid_list.setMinimumHeight(220) 
        
        sel_layout.addWidget(self.grid_list)
        layout.addWidget(sel_group)
        
        # --- SEKCE 2: OBSAH KOTLÍKU ---
        beaker_group = QGroupBox("Obsah kotlíku")
        beaker_layout = QVBoxLayout(beaker_group)
        
        self.beaker_table = QTableWidget()
        self.beaker_table.setColumnCount(4)
        self.beaker_table.setHorizontalHeaderLabels(["Surovina", "Počet", "Info", "Akce"])
        self.beaker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.beaker_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.beaker_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.beaker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.beaker_table.setMaximumHeight(180)
        
        beaker_layout.addWidget(self.beaker_table)
        
        btn_clear = QPushButton("Vylít celý kotlík")
        btn_clear.setStyleSheet("height: 20px; font-size: 11px;")
        btn_clear.clicked.connect(self.reset_beaker)
        beaker_layout.addWidget(btn_clear)
        
        layout.addWidget(beaker_group)

        # --- SEKCE 3: VÝSLEDKY ---
        res_frame = QFrame()
        res_frame.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555; border-radius: 5px; padding: 5px;")
        res_layout = QHBoxLayout(res_frame)
        
        self.lbl_res_color = QLabel()
        self.lbl_res_color.setFixedSize(50, 50)
        self.lbl_res_color.setStyleSheet("background: #000; border: 1px solid #777; border-radius: 25px;")
        
        info_layout = QVBoxLayout()
        self.lbl_ph = QLabel("pH: 7.00")
        self.lbl_ph.setStyleSheet("font-weight: bold; font-size: 14px; color: #4FC3F7;")
        self.lbl_amount = QLabel("Objem: 0 ml")
        info_layout.addWidget(self.lbl_ph)
        info_layout.addWidget(self.lbl_amount)
        
        res_layout.addWidget(self.lbl_res_color)
        res_layout.addLayout(info_layout)
        res_layout.addStretch()
        
        # Aplikovat tlačítko
        self.btn_apply = QPushButton("Použít výsledek do receptu")
        self.btn_apply.setToolTip("Nastaví výslednou barvu, pH a suroviny do aktuálního receptu")
        self.btn_apply.setStyleSheet("background-color: #1565C0; font-weight: bold; padding: 10px; font-size: 13px;")
        self.btn_apply.clicked.connect(self.apply_to_recipe)
        
        layout.addWidget(res_frame)
        layout.addWidget(self.btn_apply)

        self.setLayout(layout)
        self.current_result = None

    def load_ingredients(self):
        """Načte ingredience z DB a naplní grid."""
        self.ingredients_cache = db.fetch_all("SELECT * FROM aprts_alchemist_ingredients ORDER BY item_id")
        self.populate_grid(self.ingredients_cache)

    def populate_grid(self, items):
        self.grid_list.clear()
        for ing in items:
            # Text pod ikonou: Název + pH
            display_text = f"{ing['item_id']}\n(pH {ing['ph']})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, ing) # Uložíme celá data
            item.setToolTip(f"ID: {ing['item_id']}\npH: {ing['ph']}\nBarva RGB: {ing['r']},{ing['g']},{ing['b']}\nObjem: {ing['amount']}ml")
            item.setTextAlignment(Qt.AlignCenter)
            
            # Načtení ikony asynchronně
            ImageLoader.load_icon_to_item(ing['item_id'], item)
            
            self.grid_list.addItem(item)

    def filter_ingredients(self, text):
        text = text.lower()
        filtered = [i for i in self.ingredients_cache if text in i['item_id'].lower()]
        self.populate_grid(filtered)

    def add_ingredient_from_grid(self, item):
        data = item.data(Qt.UserRole)
        count = self.spin_count.value()
        
        # Přidáme do seznamu
        self.beaker_contents.append({"data": data, "count": count})
        
        self.update_beaker_ui()
        self.calculate_mix()
        
        # Vizuální efekt - zrušit výběr po kliknutí
        self.grid_list.clearSelection()

    def remove_item_at_row(self):
        """Callback pro tlačítko odebrat v řádku tabulky."""
        sender_btn = self.sender()
        if not sender_btn: return
        
        # Najdeme, na kterém řádku je tlačítko
        # sender_btn -> cell_widget -> table
        # Ale jednodušší je uložit index do property tlačítka
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
            
            # 1. Surovina
            item_name = QTableWidgetItem(entry['data']['item_id'])
            # Můžeme zkusit dát ikonu i sem, pokud je cachovaná
            ImageLoader.load_icon_to_item(entry['data']['item_id'], item_name)
            self.beaker_table.setItem(idx, 0, item_name)
            
            # 2. Počet
            self.beaker_table.setItem(idx, 1, QTableWidgetItem(str(entry['count'])))
            
            # 3. Info
            info = f"pH {entry['data']['ph']} | {entry['data']['amount']}ml"
            self.beaker_table.setItem(idx, 2, QTableWidgetItem(info))
            
            # 4. Akce (Tlačítko smazat)
            btn_rem = QPushButton("❌")
            btn_rem.setFixedSize(30, 20)
            btn_rem.setStyleSheet("color: red; font-weight: bold; border: none;")
            btn_rem.setProperty("row_index", idx) # Uložíme si index pro mazání
            btn_rem.clicked.connect(self.remove_item_at_row)
            
            # Musíme vložit widget do buňky
            w = QWidget()
            l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setAlignment(Qt.AlignCenter)
            l.addWidget(btn_rem)
            self.beaker_table.setCellWidget(idx, 3, w)

    def calculate_mix(self):
        if not self.beaker_contents:
            self.lbl_res_color.setStyleSheet("background: #000; border-radius: 25px;")
            self.lbl_ph.setText("pH: 7.00")
            self.lbl_amount.setText("Objem: 0 ml")
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
                
                # Vážený průměr
                mix['r'] = ((mix['r'] * total_amount) + (ing['r'] * item_total_amount)) / new_total
                mix['g'] = ((mix['g'] * total_amount) + (ing['g'] * item_total_amount)) / new_total
                mix['b'] = ((mix['b'] * total_amount) + (ing['b'] * item_total_amount)) / new_total
                mix['ph'] = ((mix['ph'] * total_amount) + (ing_ph * item_total_amount)) / new_total
                
                total_amount = new_total

        mix['amount'] = total_amount
        self.current_result = mix
        
        c_style = f"background-color: rgb({int(mix['r'])}, {int(mix['g'])}, {int(mix['b'])});"
        self.lbl_res_color.setStyleSheet(c_style + "border-radius: 25px; border: 2px solid white;")
        self.lbl_ph.setText(f"pH: {mix['ph']:.2f}")
        self.lbl_amount.setText(f"Objem: {int(total_amount)} ml")

    def apply_to_recipe(self):
        if not self.current_result: return
        self.parent_recipe.apply_simulated_data(self.current_result, self.beaker_contents)
        QMessageBox.information(self, "Hotovo", "Data z kalkulačky byla přenesena do formuláře receptu.")