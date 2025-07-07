import sys
import os
import json
import urllib.request
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QColor, QBrush
from PyQt5.QtWidgets import QStyledItemDelegate

CLASS_ICONS = {
    "Burglar": "https://lotro-wiki.com/images/1/1e/Framed_Burglar-icon.png",
    "Captain": "https://lotro-wiki.com/images/1/16/Framed_Captain-icon.png",
    "Champion": "https://lotro-wiki.com/images/7/74/Framed_Champion-icon.png",
    "Guardian": "https://lotro-wiki.com/images/d/dc/Framed_Guardian-icon.png",
    "Hunter": "https://lotro-wiki.com/images/7/7c/Framed_Hunter-icon.png",
    "Loremaster": "https://lotro-wiki.com/images/c/c0/Framed_Lore-master-icon.png",
    "Minstrel": "https://lotro-wiki.com/images/f/f6/Framed_Minstrel-icon.png"
}

class GridLineDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        rect = option.rect

        # Vertical line (right edge, grey)
        painter.save()
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor(136, 136, 136))  # #888
        painter.setPen(pen)
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
        painter.restore()

        # Horizontal line (bottom edge, black)
        painter.save()
        pen.setWidth(2)
        pen.setColor(QColor(0, 0, 0))  # Black
        painter.setPen(pen)
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        painter.restore()

class RaidTracker(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Raid Tracker")
        self.data_file = "raid_data.json"
        self.columns = [
            " ", "Name", "Raids", "Quotient",
            "Helmet", "Shoulder", "Gloves", "Breast", "Legs", "Boots",
            "Storvagun Qitems", "Zaudru Qitem", "Mirdernant", "Beryl shard", "Remove"
        ]
        self.entries = []
        self.icon_map = {}
        self._load_data()
        self._load_icons()
        self._init_ui()
        self.refresh_view()
        self.populate_db_combo()

    def _load_icons(self):
        for cls, url in CLASS_ICONS.items():
            try:
                data = urllib.request.urlopen(url).read()
                pix = QPixmap()
                pix.loadFromData(data)
                self.icon_map[cls] = QIcon(pix)
            except:
                self.icon_map[cls] = None

    def _init_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)  # Padding

        # Top menu row
        top_h = QtWidgets.QHBoxLayout()
        top_h.setSpacing(10)

        self.class_input = QtWidgets.QComboBox()
        self.class_input.addItems(CLASS_ICONS.keys())
        self.class_input.setFixedWidth(120)
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setFixedWidth(120)
        self.name_input.returnPressed.connect(self._on_add)
        self.main_check = QtWidgets.QCheckBox()
        self.main_check.setChecked(True)
        self.twink_check = QtWidgets.QCheckBox()
        self.main_check.toggled.connect(lambda chk: self.twink_check.setChecked(False) if chk else None)
        self.twink_check.toggled.connect(lambda chk: self.main_check.setChecked(False) if chk else None)
        self.twink_check.toggled.connect(self._toggle_twink_of)

        self.twink_of_label = QtWidgets.QLabel("Twink of:")
        self.twink_of_combo = QtWidgets.QComboBox()
        self.twink_of_label.setVisible(False)
        self.twink_of_combo.setVisible(False)
        self.twink_of_combo.setFixedWidth(120)

        self.add_btn = QtWidgets.QPushButton("Add")
        self.add_btn.setFixedWidth(50)
        self.add_btn.clicked.connect(self._on_add)

        top_h.addWidget(QtWidgets.QLabel("Class:"))
        top_h.addWidget(self.class_input)
        top_h.addWidget(QtWidgets.QLabel("Name:"))
        top_h.addWidget(self.name_input)
        top_h.addWidget(QtWidgets.QLabel("Main:"))
        top_h.addWidget(self.main_check)
        top_h.addWidget(QtWidgets.QLabel("Twink:"))
        top_h.addWidget(self.twink_check)
        top_h.addWidget(self.twink_of_label)
        top_h.addWidget(self.twink_of_combo)
        top_h.addWidget(self.add_btn)
        top_h.addStretch()

        db_label = QtWidgets.QLabel("Choose database:")
        db_label.setContentsMargins(40, 0, 0, 0)
        self.db_combo = QtWidgets.QComboBox()
        self.db_combo.setFixedWidth(180)
        self.db_combo.currentIndexChanged.connect(self._on_db_select)
        top_h.addWidget(db_label)
        top_h.addWidget(self.db_combo)

        layout.addLayout(top_h)

        # Filter row
        filter_h = QtWidgets.QHBoxLayout()
        filter_h.setSpacing(10)
        filter_h.addWidget(QtWidgets.QLabel("Filter Name:"))
        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_h.addWidget(self.filter_input)
        filter_h.addStretch()
        layout.addLayout(filter_h)

        # Table (Tree)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(len(self.columns))
        self.tree.setHeaderLabels(self.columns)
        self.tree.setUniformRowHeights(False)
        self.tree.setIndentation(20)
        self.tree.setItemDelegate(GridLineDelegate(self.tree))
        self.tree.header().setStyleSheet("""
            QHeaderView::section {
                border-right: 2px solid #888;
                border-bottom: 5px solid black;
                padding: 2px;
                background: #f5f5f5;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.tree)

        # Set column widths and center header
        self.col_widths = [70, 120, 80, 80, 80, 80, 80, 80, 80, 80, 110, 90, 80, 40]
        self.row_height_parent = 40  # or 48 for extra tall
        self.row_height_child = 30 
        header = self.tree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        for i, w in enumerate(self.col_widths):
            self.tree.setColumnWidth(i, w)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.setFixedWidth(sum(self.col_widths) + 30)
        self.setMinimumHeight(500)

    def _toggle_twink_of(self, checked):
        self.twink_of_label.setVisible(checked)
        self.twink_of_combo.setVisible(checked)
        if checked:
            self._refresh_twink_dropdown()

    def _refresh_twink_dropdown(self):
        self.twink_of_combo.clear()
        mains = [e["Name"] for e in self.entries if e.get("is_main") and e.get("active", True)]
        self.twink_of_combo.addItems(mains)

    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file) as f:
                self.entries = json.load(f)
        else:
            self.entries = []

    def _save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.entries, f, indent=2)
        self.populate_db_combo()

    def populate_db_combo(self):
        self.db_combo.blockSignals(True)
        self.db_combo.clear()
        self.db_combo.addItem("--select character--")  # Placeholder
        for e in self.entries:
            if not e.get('active', True):
                if e.get('is_main'):
                    label = f"{e['Name']} (Main)"
                elif e.get('is_twink'):
                    label = f"{e['Name']} (Twink of {e.get('Main', '')})"
                else:
                    label = e['Name']
                self.db_combo.addItem(label)
        self.db_combo.blockSignals(False)

    def _on_add(self):
        name = self.name_input.text().strip()
        if not name:
            return
        if any(e.get("Name") == name and e.get("active", True) for e in self.entries):
            QtWidgets.QMessageBox.warning(self, "Duplicate Player", f"Player '{name}' already active.")
            return
        is_main = self.main_check.isChecked()
        is_twink = self.twink_check.isChecked()
        main_parent = None
        if is_twink:
            main_parent = self.twink_of_combo.currentText()
            if not main_parent:
                QtWidgets.QMessageBox.warning(self, "No Main Selected", "Select a Main for this Twink.")
                return
        entry = {col: 0 for col in self.columns if col not in ("Class", "Name", "Quotient", "Remove")}
        entry.update({
            "Class": self.class_input.currentText(),
            "Name": name,
            "Quotient": 1.0,
            "active": True,
            "is_main": is_main,
            "is_twink": is_twink
        })
        if is_main:
            entry["Twinks"] = []
        if is_twink:
            entry["Main"] = main_parent
            for e in self.entries:
                if e.get("Name") == main_parent and e.get("is_main"):
                    e.setdefault("Twinks", []).append(name)
        self.entries.append(entry)
        self._save_data()
        self.refresh_view()
        self.name_input.clear()
        self.main_check.setChecked(True)
        self.twink_check.setChecked(False)

    def _on_db_select(self, idx):
        if idx <= 0:
            return
        selected_label = self.db_combo.currentText()
        name = selected_label.split(" (")[0]
        for e in self.entries:
            if e['Name'] == name and not e.get('active', True):
                e['active'] = True
                if e.get('is_twink') and e.get('Main'):
                    for main in self.entries:
                        if main.get('Name') == e['Main'] and main.get('is_main'):
                            if e['Name'] not in main.get('Twinks', []):
                                main.setdefault('Twinks', []).append(e['Name'])
        self._save_data()
        self.refresh_view()
        self.db_combo.setCurrentIndex(0)

    def _make_counter_widget(self, entry, key, row_height=24):
        w = QtWidgets.QWidget()
        w.setMinimumHeight(row_height)
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(2)
        m = QtWidgets.QPushButton("-")
        m.setFixedSize(30, 24)   # Keep button height consistent (or use row_height if you prefer)
        p = QtWidgets.QPushButton("+")
        p.setFixedSize(30, 24)
        lbl = QtWidgets.QLabel(str(entry.get(key, 0)))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumHeight(row_height)
        h.addStretch()
        h.addWidget(m, alignment=Qt.AlignCenter)
        h.addWidget(lbl, alignment=Qt.AlignCenter)
        h.addWidget(p, alignment=Qt.AlignCenter)
        h.addStretch()
        h.setAlignment(Qt.AlignCenter)
        w.entry, w.key, w.lbl = entry, key, lbl
        m.clicked.connect(lambda _, w=w: self._on_counter(w, -1))
        p.clicked.connect(lambda _, w=w: self._on_counter(w, +1))
        return w

    def _make_plusonly_widget(self, entry, key, row_height=24):
        w = QtWidgets.QWidget()
        w.setMinimumHeight(row_height)
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(2)
        p = QtWidgets.QPushButton("+")
        p.setFixedSize(30, 24)
        lbl = QtWidgets.QLabel(str(entry.get(key, 0)))
        lbl.setAlignment(Qt.AlignCenter)
        h.addStretch()
        h.addWidget(lbl, alignment=Qt.AlignCenter)
        h.addWidget(p, alignment=Qt.AlignCenter)
        h.addStretch()
        h.setAlignment(Qt.AlignCenter)
        w.entry, w.key, w.lbl = entry, key, lbl
        p.clicked.connect(lambda _, w=w: self._on_counter(w, +1))
        return w


    def refresh_view(self):
        self.tree.clear()
        header = self.tree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        for i, w in enumerate(self.col_widths):
            self.tree.setColumnWidth(i, w)
        header.setDefaultAlignment(Qt.AlignCenter)
        QUOTIENT_COLS = ["Helmet", "Shoulder", "Gloves", "Breast", "Legs", "Boots", "Zaudru Qitem"]
        # --- Mains ---
        for m in [e for e in self.entries if e.get("is_main") and e.get("active", True)]:
            self.tree.setIconSize(QSize(self.row_height_parent - 2, self.row_height_parent - 2))
            parent = QtWidgets.QTreeWidgetItem(self.tree)
            parent.setSizeHint(0, QSize(0, self.row_height_parent))
            icon = self.icon_map.get(m.get("Class"))
            if icon:
                pixmap = icon.pixmap(QSize(self.row_height_parent - 2, self.row_height_parent - 2))
                parent.setIcon(0, QIcon(pixmap))
            parent.setText(1, m.get("Name"))
            parent.setTextAlignment(1, Qt.AlignVCenter | Qt.AlignLeft)
            for col in range(2, len(self.columns)):
                parent.setTextAlignment(col, Qt.AlignVCenter | Qt.AlignCenter)
            # Counter widgets and remove button
            w_r = self._make_counter_widget(m, "Raids", row_height=self.row_height_parent)
            self.tree.setItemWidget(parent, 2, w_r)
            raids = m.get('Raids', 0)
            total_equip = sum(m.get(col,0) for col in QUOTIENT_COLS)
            for tname in m.get("Twinks", []):
                t = next((x for x in self.entries if x["Name"] == tname and x.get("active", True)), None)
                if t:
                    raids += t.get("Raids",0)
                    total_equip += sum(t.get(col,0) for col in QUOTIENT_COLS)
            quotient = total_equip/raids if raids > 0 else 1.0
            lbl_q = QtWidgets.QLabel(f"{quotient:.2f}")
            lbl_q.setAlignment(Qt.AlignCenter)
            self.tree.setItemWidget(parent, 3, lbl_q)
            for i, col in enumerate(self.columns[4:-1], 4):
                w_e = self._make_counter_widget(m, col)
                self.tree.setItemWidget(parent, i, w_e)
            btn = QtWidgets.QPushButton("X")
            btn.setFixedSize(30, 24)
            btn_widget = QtWidgets.QWidget()
            btn_layout = QtWidgets.QHBoxLayout(btn_widget)
            btn_layout.addStretch()
            btn_layout.addWidget(btn, alignment=Qt.AlignCenter)
            btn_layout.addStretch()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            self.tree.setItemWidget(parent, len(self.columns)-1, btn_widget)
            btn.clicked.connect(lambda _, e=m: self._remove_entry(e))
            brush = QBrush(QColor(0, 255, 0, int(0.3*255)))
            for c in range(len(self.columns)):
                parent.setBackground(c, brush)

            # Children/twinks (no setSizeHint, default row height)
            for tname in m.get("Twinks", []):
                t = next((x for x in self.entries if x["Name"] == tname and x.get("active", True)), None)
                if not t:
                    continue
                self.tree.setIconSize(QSize(self.row_height_child - 2, self.row_height_child - 2))
                child = QtWidgets.QTreeWidgetItem(parent)
                icon_c = self.icon_map.get(t.get("Class"))
                if icon_c:
                    pixmap_c = icon_c.pixmap(QSize(self.row_height_child - 2, self.row_height_child -2))
                    child.setIcon(0, QIcon(pixmap_c))
                child.setText(1, t.get("Name"))
                child.setTextAlignment(1, Qt.AlignVCenter | Qt.AlignLeft)
                for col in range(2, len(self.columns)):
                    child.setTextAlignment(col, Qt.AlignVCenter | Qt.AlignCenter)
                w_rt = self._make_counter_widget(t, "Raids", row_height=self.row_height_child)
                self.tree.setItemWidget(child, 2, w_rt)
                # Quotient blank
                for i, col in enumerate(self.columns[4:-1], 4):
                    w_et = self._make_counter_widget(t, col)
                    self.tree.setItemWidget(child, i, w_et)
                btn2 = QtWidgets.QPushButton("X")
                btn2.setFixedSize(30, 24)
                btn2_widget = QtWidgets.QWidget()
                btn2_layout = QtWidgets.QHBoxLayout(btn2_widget)
                btn2_layout.addStretch()
                btn2_layout.addWidget(btn2, alignment=Qt.AlignCenter)
                btn2_layout.addStretch()
                btn2_layout.setContentsMargins(0, 0, 0, 0)
                self.tree.setItemWidget(child, len(self.columns)-1, btn2_widget)
                btn2.clicked.connect(lambda _, e=t: self._remove_entry(e))
                brush2 = QBrush(QColor(255, 0, 0, int(0.2*255)))
                for c in range(len(self.columns)):
                    child.setBackground(c, brush2)

        # --- Orphaned active twinks ---
        linked_twinks = {tname for e in self.entries if e.get("is_main") and e.get("active", True)
                         for tname in e.get("Twinks", [])}
        for t in [e for e in self.entries if e.get("is_twink") and e.get("active", True) and e['Name'] not in linked_twinks]:
            item = QtWidgets.QTreeWidgetItem(self.tree)
            icon = self.icon_map.get(t.get("Class"))
            if icon:
                pixmap = icon.pixmap(QSize(24, 24))
                item.setIcon(0, QIcon(pixmap))
            item.setText(1, t.get("Name"))
            item.setTextAlignment(1, Qt.AlignVCenter | Qt.AlignLeft)
            for col in range(2, len(self.columns)):
                item.setTextAlignment(col, Qt.AlignVCenter | Qt.AlignCenter)
            w_r = self._make_counter_widget(t, "Raids")
            self.tree.setItemWidget(item, 2, w_r)
            # Quotient blank
            for i, col in enumerate(self.columns[4:-1], 4):
                w_e = self._make_counter_widget(t, col)
                self.tree.setItemWidget(item, i, w_e)
            btn = QtWidgets.QPushButton("X")
            btn.setFixedSize(30, 24)
            btn_widget = QtWidgets.QWidget()
            btn_layout = QtWidgets.QHBoxLayout(btn_widget)
            btn_layout.addStretch()
            btn_layout.addWidget(btn, alignment=Qt.AlignCenter)
            btn_layout.addStretch()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            self.tree.setItemWidget(item, len(self.columns)-1, btn_widget)
            btn.clicked.connect(lambda _, e=t: self._remove_entry(e))
            brush = QBrush(QColor(255, 0, 0, 76))
            for c in range(len(self.columns)):
                item.setBackground(c, brush)

        self.tree.expandAll()
        self.populate_db_combo()

    def _apply_filter(self, text):
        text = text.lower().strip()
        def match(item):
            return text in item.text(1).lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            visible = match(parent)
            for j in range(parent.childCount()):
                child = parent.child(j)
                cvis = match(child)
                child.setHidden(not cvis)
                visible = visible or cvis
            parent.setHidden(not visible)

    def _on_counter(self, widget, delta):
        e, k = widget.entry, widget.key
        e[k] = max(0, e.get(k, 0) + delta)
        widget.lbl.setText(str(e[k]))
        self._save_data()
        self.refresh_view()

    def _remove_entry(self, entry):
        if entry.get('is_main'):
            entry['active'] = False
            for tname in entry.get('Twinks', []):
                for e in self.entries:
                    if e['Name'] == tname:
                        e['active'] = False
        else:
            entry['active'] = False
            main_name = entry.get('Main')
            if main_name:
                for e in self.entries:
                    if e.get('Name') == main_name and 'Twinks' in e:
                        if entry['Name'] in e['Twinks']:
                            e['Twinks'].remove(entry['Name'])
        self._save_data()
        self.refresh_view()

    def closeEvent(self, event):
        self._save_data()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = RaidTracker()
    w.show()
    sys.exit(app.exec_())