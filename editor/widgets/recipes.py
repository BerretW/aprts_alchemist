# widgets/recipes.py
import json
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QHeaderView, 
                             QAbstractItemView, QPushButton, QTabWidget, QGroupBox, QFormLayout, 
                             QLineEdit, QSpinBox, QDoubleSpinBox, QLabel, QSplitter, QMessageBox, 
                             QTableWidgetItem)
from PyQt5.QtCore import Qt
from database import db
from utils.dialogs import ItemSearchDialog
from widgets.calculator import CalculatorWidget

class RecipesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.loaded_recipe_id = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # --- LEVÁ ČÁST: Seznam receptů ---
        left_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID Receptu", "Název (Label)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.clicked.connect(self.load_detail)
        left_layout.addWidget(self.table)
        
        btn_box = QHBoxLayout()
        self.btn_refresh = QPushButton("Obnovit")
        self.btn_refresh.clicked.connect(self.load_list)
        self.btn_new = QPushButton("Nový recept")
        self.btn_new.clicked.connect(self.create_new)
        btn_box.addWidget(self.btn_refresh)
        btn_box.addWidget(self.btn_new)
        left_layout.addLayout(btn_box)

        # --- PRAVÁ ČÁST: Detail ---
        right_layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.tabs.setEnabled(False)

        # TAB 1: Info & Cíle
        self.tab_info = QWidget()
        info_layout = QVBoxLayout(self.tab_info)
        
        gb_basic = QGroupBox("Základní informace")
        f_basic = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Generuje se automaticky podle výsledku...")
        
        self.inp_label = QLineEdit()
        
        # --- VÝBĚR VÝSLEDKU (Reward Item) ---
        reward_widget = QWidget()
        reward_layout = QHBoxLayout(reward_widget)
        reward_layout.setContentsMargins(0, 0, 0, 0)
        
        self.inp_reward_item = QLineEdit()
        self.inp_reward_item.setPlaceholderText("Vyberte nebo vepište ID itemu")
        # ZDE: Automatická synchronizace jména receptu podle itemu
        self.inp_reward_item.textChanged.connect(self.sync_recipe_name)
        
        self.btn_sel_reward = QPushButton("...")
        self.btn_sel_reward.setFixedWidth(40)
        self.btn_sel_reward.clicked.connect(self.select_reward_item)
        
        reward_layout.addWidget(self.inp_reward_item)
        reward_layout.addWidget(self.btn_sel_reward)
        # ------------------------------------

        self.inp_reward_count = QSpinBox()
        self.inp_reward_count.setRange(1, 100)
        
        self.inp_skill = QSpinBox()
        self.inp_skill.setRange(0, 1000)

        f_basic.addRow("ID Receptu:", self.inp_name)
        f_basic.addRow("Label (Název):", self.inp_label)
        f_basic.addRow("Výsledek (Item):", reward_widget)
        f_basic.addRow("Počet ks:", self.inp_reward_count)
        f_basic.addRow("Min. Skill:", self.inp_skill)
        gb_basic.setLayout(f_basic)
        
        gb_cond = QGroupBox("Cílové vlastnosti")
        f_cond = QFormLayout()
        
        h_col = QHBoxLayout()
        self.inp_cr = QSpinBox(); self.inp_cr.setRange(0, 255); self.inp_cr.setPrefix("R:")
        self.inp_cg = QSpinBox(); self.inp_cg.setRange(0, 255); self.inp_cg.setPrefix("G:")
        self.inp_cb = QSpinBox(); self.inp_cb.setRange(0, 255); self.inp_cb.setPrefix("B:")
        self.inp_ctol = QSpinBox(); self.inp_ctol.setSuffix(" tol")
        h_col.addWidget(self.inp_cr); h_col.addWidget(self.inp_cg); h_col.addWidget(self.inp_cb)
        h_col.addWidget(QLabel("| Tol:"))
        h_col.addWidget(self.inp_ctol)
        
        h_ph = QHBoxLayout()
        self.inp_ph_min = QDoubleSpinBox(); self.inp_ph_min.setSingleStep(0.1); self.inp_ph_min.setPrefix("Min: ")
        self.inp_ph_max = QDoubleSpinBox(); self.inp_ph_max.setSingleStep(0.1); self.inp_ph_max.setPrefix("Max: "); self.inp_ph_max.setValue(14)
        h_ph.addWidget(self.inp_ph_min); h_ph.addWidget(self.inp_ph_max)
        
        self.inp_min_amount = QSpinBox(); self.inp_min_amount.setRange(1, 10000); self.inp_min_amount.setSuffix(" ml")

        f_cond.addRow("Barva:", h_col)
        f_cond.addRow("Rozsah pH:", h_ph)
        f_cond.addRow("Min. objem:", self.inp_min_amount)
        gb_cond.setLayout(f_cond)
        
        info_layout.addWidget(gb_basic)
        info_layout.addWidget(gb_cond)
        info_layout.addStretch()

        # TAB 2: Requirements
        self.tab_req = QWidget()
        req_layout = QVBoxLayout(self.tab_req)
        
        self.req_table = QTableWidget()
        self.req_table.setColumnCount(2)
        self.req_table.setHorizontalHeaderLabels(["Surovina (ID)", "Min. Množství (ml)"])
        self.req_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.req_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        req_layout.addWidget(self.req_table)
        
        req_btn_box = QHBoxLayout()
        self.btn_add_req = QPushButton("Přidat surovinu")
        self.btn_add_req.clicked.connect(self.add_requirement_row)
        self.btn_rem_req = QPushButton("Odebrat označené")
        self.btn_rem_req.clicked.connect(self.remove_requirement_row)
        req_btn_box.addWidget(self.btn_add_req)
        req_btn_box.addWidget(self.btn_rem_req)
        req_layout.addLayout(req_btn_box)

        # TAB 3: Proces
        self.tab_proc = QWidget()
        proc_layout = QVBoxLayout(self.tab_proc)
        gb_proc = QGroupBox("Parametry vaření")
        f_proc = QFormLayout()
        
        self.inp_temp = QSpinBox(); self.inp_temp.setRange(0, 500); self.inp_temp.setSuffix(" °C")
        self.inp_temp_tol = QSpinBox(); self.inp_temp_tol.setSuffix(" tol")
        self.inp_time = QSpinBox(); self.inp_time.setRange(0, 3600); self.inp_time.setSuffix(" s")
        self.inp_time_tol = QSpinBox(); self.inp_time_tol.setSuffix(" tol")
        
        f_proc.addRow("Teplota:", self.inp_temp)
        f_proc.addRow("Tol. teploty:", self.inp_temp_tol)
        f_proc.addRow("Čas vaření:", self.inp_time)
        f_proc.addRow("Tol. času:", self.inp_time_tol)
        gb_proc.setLayout(f_proc)
        proc_layout.addWidget(gb_proc)
        proc_layout.addStretch()

        self.tabs.addTab(self.tab_info, "Info & Cíle")
        self.tabs.addTab(self.tab_req, "Suroviny (Requirements)")
        self.tabs.addTab(self.tab_proc, "Proces")

        self.calculator = CalculatorWidget(self)
        
        self.btn_save = QPushButton("💾 ULOŽIT RECEPT")
        self.btn_save.setEnabled(False)
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet("background-color: #388E3C; font-size: 14px; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_recipe)
        
        self.btn_del = QPushButton("Smazat recept")
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet("background-color: #D32F2F;")
        self.btn_del.clicked.connect(self.delete_recipe)

        right_layout.addWidget(self.tabs)
        right_layout.addWidget(self.calculator)
        right_layout.addWidget(self.btn_save)
        right_layout.addWidget(self.btn_del)

        splitter = QSplitter()
        w_l = QWidget(); w_l.setLayout(left_layout)
        w_r = QWidget(); w_r.setLayout(right_layout)
        splitter.addWidget(w_l)
        splitter.addWidget(w_r)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
        self.load_list()

    def toggle_inputs(self, enable):
        self.tabs.setEnabled(enable)
        self.btn_save.setEnabled(enable)
        self.btn_del.setEnabled(enable)
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
        r_name = self.table.item(row, 0).text()
        
        data = db.fetch_all("SELECT * FROM aprts_alchemist_recipes WHERE name=%s", (r_name,))
        if not data: return
        r = data[0]

        # Dočasně odpojíme signál, abychom nepřepsali jméno při načítání
        self.inp_reward_item.blockSignals(True)

        self.loaded_recipe_id = r['name']
        self.toggle_inputs(True)
        
        self.inp_name.setText(r['name'])
        self.inp_label.setText(r['label'])
        self.inp_reward_item.setText(r['rewardItem'])
        self.inp_reward_count.setValue(r['rewardCount'])
        self.inp_skill.setValue(r['minSkillToIdentify'])
        
        # Znovu zapojíme signál
        self.inp_reward_item.blockSignals(False)
        
        try:
            c = json.loads(r['color_target']) if r['color_target'] else {'r':0,'g':0,'b':0}
            self.inp_cr.setValue(c.get('r', 0))
            self.inp_cg.setValue(c.get('g', 0))
            self.inp_cb.setValue(c.get('b', 0))
        except: pass
        self.inp_ctol.setValue(r['colorTolerance'])
        self.inp_ph_min.setValue(float(r['phMin']))
        self.inp_ph_max.setValue(float(r['phMax']))
        self.inp_min_amount.setValue(r['minTotalAmount'])
        
        self.inp_temp.setValue(r['process_temp'])
        self.inp_temp_tol.setValue(r['process_tempTolerance'])
        self.inp_time.setValue(r['process_time'])
        self.inp_time_tol.setValue(r['process_timeTolerance'])
        
        self.req_table.setRowCount(0)
        try:
            reqs = json.loads(r['requirements'])
            for req in reqs:
                self._add_req_row_ui(req.get('item', ''), req.get('minAmount', 0))
        except Exception as e:
            print(f"JSON Parse Error: {e}")

    def create_new(self):
        self.loaded_recipe_id = None
        self.toggle_inputs(True)
        self.inp_name.clear()
        self.inp_label.clear()
        self.inp_reward_item.clear()
        self.req_table.setRowCount(0)
        self.inp_ph_min.setValue(6.0)
        self.inp_ph_max.setValue(8.0)
        self.inp_cr.setValue(0); self.inp_cg.setValue(0); self.inp_cb.setValue(0)
        self.inp_reward_item.setFocus()

    def sync_recipe_name(self, text):
        """Automaticky nastaví ID receptu podle výsledného itemu."""
        # Můžete přidat prefix, pokud chcete, např: f"recipe_{text}"
        self.inp_name.setText(text)

    def select_reward_item(self):
        dialog = ItemSearchDialog(self, "Vybrat výsledný item")
        if dialog.exec_():
            item_id = dialog.get_selected_item()
            if item_id:
                self.inp_reward_item.setText(item_id)
                # sync_recipe_name se zavolá automaticky přes signál

    def _add_req_row_ui(self, item_name, amount):
        row = self.req_table.rowCount()
        self.req_table.insertRow(row)
        self.req_table.setItem(row, 0, QTableWidgetItem(item_name))
        self.req_table.setItem(row, 1, QTableWidgetItem(str(amount)))

    def add_requirement_row(self):
        dialog = ItemSearchDialog(self, "Vybrat surovinu pro recept")
        if dialog.exec_():
            item_id = dialog.get_selected_item()
            if item_id:
                self._add_req_row_ui(item_id, 100)

    def remove_requirement_row(self):
        row = self.req_table.currentRow()
        if row >= 0:
            self.req_table.removeRow(row)

    def apply_simulated_data(self, result_mix, beaker_items):
        self.inp_cr.setValue(int(result_mix['r']))
        self.inp_cg.setValue(int(result_mix['g']))
        self.inp_cb.setValue(int(result_mix['b']))
        
        ph = result_mix['ph']
        self.inp_ph_min.setValue(max(0, ph - 0.5))
        self.inp_ph_max.setValue(min(14, ph + 0.5))
        self.inp_min_amount.setValue(int(result_mix['amount']))
        
        if beaker_items:
            reply = QMessageBox.question(self, "Nahradit suroviny?", 
                "Chcete přepsat tabulku 'Suroviny' podle obsahu kotlíku?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.req_table.setRowCount(0)
                aggregated = {}
                for entry in beaker_items:
                    item_id = entry['data']['item_id']
                    ml = entry['count'] * entry['data']['amount']
                    aggregated[item_id] = aggregated.get(item_id, 0) + ml
                for k, v in aggregated.items():
                    self._add_req_row_ui(k, v)

    def save_recipe(self):
        # Validace
        if not self.inp_name.text():
            QMessageBox.warning(self, "Chyba", "Recept musí mít ID (Name)!")
            return

        # Sestavení JSONů
        req_list = []
        for i in range(self.req_table.rowCount()):
            item = self.req_table.item(i, 0).text()
            try: amt = int(float(self.req_table.item(i, 1).text()))
            except: amt = 0
            req_list.append({"item": item, "minAmount": amt})
        
        requirements_json = json.dumps(req_list)
        color_target_json = json.dumps({"r": self.inp_cr.value(), "g": self.inp_cg.value(), "b": self.inp_cb.value()})

        # Zjistíme, zda existuje PŮVODNÍ záznam (podle loaded_recipe_id)
        exists = False
        if self.loaded_recipe_id:
             check = db.fetch_all("SELECT name FROM aprts_alchemist_recipes WHERE name=%s", (self.loaded_recipe_id,))
             if check: exists = True

        if exists:
            # UPDATE: Musíme použít SET name=%s ... WHERE name=%s (loaded_recipe_id)
            # Tím umožníme přejmenování receptu
            query = """
                UPDATE aprts_alchemist_recipes SET
                name=%s, label=%s, minSkillToIdentify=%s, color_target=%s, colorTolerance=%s,
                phMin=%s, phMax=%s, minTotalAmount=%s, requirements=%s,
                rewardItem=%s, rewardCount=%s, process_temp=%s, process_time=%s,
                process_tempTolerance=%s, process_timeTolerance=%s
                WHERE name=%s
            """
            params = (
                self.inp_name.text(), # SET name
                self.inp_label.text(), self.inp_skill.value(), color_target_json, self.inp_ctol.value(),
                self.inp_ph_min.value(), self.inp_ph_max.value(), self.inp_min_amount.value(), requirements_json,
                self.inp_reward_item.text(), self.inp_reward_count.value(), self.inp_temp.value(), self.inp_time.value(),
                self.inp_temp_tol.value(), self.inp_time_tol.value(),
                self.loaded_recipe_id # WHERE name
            )
            
            if db.execute(query, params):
                QMessageBox.information(self, "Uloženo", "Recept aktualizován.")
                self.loaded_recipe_id = self.inp_name.text() # Aktualizujeme ID v paměti
        else:
            # INSERT: Zde se name vkládá standardně
            query = """
                INSERT INTO aprts_alchemist_recipes (
                name, label, minSkillToIdentify, color_target, colorTolerance,
                phMin, phMax, minTotalAmount, requirements,
                rewardItem, rewardCount, process_temp, process_time,
                process_tempTolerance, process_timeTolerance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                self.inp_name.text(),
                self.inp_label.text(), self.inp_skill.value(), color_target_json, self.inp_ctol.value(),
                self.inp_ph_min.value(), self.inp_ph_max.value(), self.inp_min_amount.value(), requirements_json,
                self.inp_reward_item.text(), self.inp_reward_count.value(), self.inp_temp.value(), self.inp_time.value(),
                self.inp_temp_tol.value(), self.inp_time_tol.value()
            )
            
            if db.execute(query, params):
                QMessageBox.information(self, "Uloženo", "Nový recept vytvořen.")
                self.loaded_recipe_id = self.inp_name.text()
        
        self.load_list()

    def delete_recipe(self):
        if not self.loaded_recipe_id: return
        if QMessageBox.question(self, "Smazat", "Opravdu smazat recept?") == QMessageBox.Yes:
            db.execute("DELETE FROM aprts_alchemist_recipes WHERE name=%s", (self.loaded_recipe_id,))
            self.load_list()
            self.toggle_inputs(False)