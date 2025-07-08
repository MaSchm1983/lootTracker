from PyQt5 import QtWidgets, QtGui, QtCore
import sys, os, json
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QStyledItemDelegate

class GridLineAndCenterDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.column() == 3:
            option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        rect = option.rect
        # Draw right border
        painter.save()
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor(136, 136, 136))
        painter.setPen(pen)
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
        painter.restore()
        # Draw bottom border
        painter.save()
        pen.setWidth(2)
        pen.setColor(QColor(0, 0, 0))
        painter.setPen(pen)
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        painter.restore()

class ShardCounterWidget(QtWidgets.QWidget):
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, initial=0, max_val=1):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.val = initial
        self.max_val = max_val
        self.minus = QtWidgets.QPushButton('-')
        self.plus = QtWidgets.QPushButton('+')
        self.label = QtWidgets.QLabel(str(self.val))
        layout.addWidget(self.minus)
        layout.addWidget(self.label)
        layout.addWidget(self.plus)
        self.minus.setFixedSize(20,20)
        self.plus.setFixedSize(20,20)
        self.label.setFixedWidth(18)
        self.minus.clicked.connect(self.decrement)
        self.plus.clicked.connect(self.increment)

    def decrement(self):
        if self.val > 0:
            self.val -= 1
            self.label.setText(str(self.val))
            self.valueChanged.emit(self.val)

    def increment(self):
        if self.val < self.max_val:
            self.val += 1
            self.label.setText(str(self.val))
            self.valueChanged.emit(self.val)

class RemoveButtonWidget(QtWidgets.QPushButton):
    def __init__(self):
        super().__init__("✕")
        self.setFixedSize(20,20)

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carn Dûm Beryl Shard Tracker")
        self.setMinimumHeight(400)
        self.data_file = "shard_count.json"
        self.entries = []
        self.columns = ["", "Name", "Shards", "remove"]
        self.col_widths = [60, 120, 100, 60]
        self.row_height_parent = 40
        self.row_height_child = 30
        layout = QtWidgets.QVBoxLayout(self)
        
        title = QtWidgets.QLabel("Carn Dûm Beryl Shard Tracker")
        title.setStyleSheet("font-weight: bold; font-size: 18px; padding-bottom: 6px;")
        layout.insertWidget(0, title)
        
        self.tree = QtWidgets.QTreeWidget()
        self.setFixedWidth(sum(self.col_widths) + 30)
        self.tree.setColumnCount(len(self.columns))
        self.tree.setHeaderLabels(self.columns)
        self.tree.header().setSectionsClickable(False)
        self.tree.setUniformRowHeights(False)  # allow different heights
        self.tree.setIndentation(20)
        self.tree.setRootIsDecorated(True)  # Show expand/collapse arrow for groups
        layout.addWidget(self.tree)

        self.tree.setItemDelegate(GridLineAndCenterDelegate(self.tree))

        add_button = QtWidgets.QPushButton("+ Add Group")
        add_button.clicked.connect(self.add_group)
        layout.insertWidget(0, add_button)

        header = self.tree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        for i, w in enumerate(self.col_widths):
            self.tree.setColumnWidth(i, w)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QHeaderView::section {
                border-right: 2px solid #888;
                border-bottom: 5px solid black;
                padding: 2px;
                background: #f5f5f5;
                font-weight: bold;
            }
        """)
        self.tree.setHeaderLabels(["⯆"] + self.columns[1:])
        self.tree.header().sectionClicked.connect(self._header_clicked)
        self.is_collapsed = False
        
        self.tree.itemCollapsed.connect(self._on_item_collapsed_or_expanded)
        self.tree.itemExpanded.connect(self._on_item_collapsed_or_expanded)

        # Now load data
        self._load_data()

    def center_widget(self, widget):
        wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(wrapper)
        layout.setContentsMargins(0,0,0,0)
        layout.addStretch()
        layout.addWidget(widget, alignment=Qt.AlignCenter)
        layout.addStretch()
        return wrapper

    def add_group(self):
        num, ok = QtWidgets.QInputDialog.getInt(self, "Group Members", "Number of players (2-6):", min=2, max=6)
        if not ok:
            return
        names = []
        for i in range(num):
            name, ok = QtWidgets.QInputDialog.getText(self, "Player Name", f"Name player {i+1}:")
            if not ok or not name:
                QtWidgets.QMessageBox.warning(self, "Missing Name", "Player name required!")
                return
            names.append(name)
        group_item = QtWidgets.QTreeWidgetItem(self.tree)
        group_item.setText(1, f"Group {self.tree.topLevelItemCount()}")
        group_item.setExpanded(False)
        for col in range(self.tree.columnCount()):
            group_item.setSizeHint(col, QtCore.QSize(self.col_widths[col], self.row_height_parent))
        group_item.setTextAlignment(2, Qt.AlignCenter)
        group_item.setTextAlignment(3, Qt.AlignCenter)
        self.update_group_background(group_item)
        for name in names:
            player_item = QtWidgets.QTreeWidgetItem(group_item)
            player_item.setText(1, name)
            for col in range(self.tree.columnCount()):
                player_item.setSizeHint(col, QtCore.QSize(self.col_widths[col], self.row_height_child))
            player_item.setTextAlignment(2, Qt.AlignCenter)
            player_item.setTextAlignment(3, Qt.AlignCenter)                
            self.update_player_background(player_item, 0)
            # Shard counter widget
            counter = ShardCounterWidget()
            counter.valueChanged.connect(lambda v, item=player_item: self.player_counter_changed(item, v))
            self.tree.setItemWidget(player_item, 2, self.center_widget(counter))
            # Remove button
            btn = RemoveButtonWidget()
            btn.clicked.connect(lambda _, item=player_item: self.remove_player(item))
            self.tree.setItemWidget(player_item, 3, self.center_widget(btn))
        self.update_group_sum(group_item)
        btn = RemoveButtonWidget()
        btn.clicked.connect(lambda _, item=group_item: self.remove_group(item))
        self.tree.setItemWidget(group_item, 3, self.center_widget(btn))
        group_item.setExpanded(True)
        self._save_data()

    def player_counter_changed(self, item, value):
        self.update_player_background(item, value)
        group = item.parent()
        self.update_group_sum(group)
        self.update_group_background(group)
        self._save_data()

    def remove_player(self, item):
        group = item.parent()
        group.removeChild(item)
        self.update_group_sum(group)
        self.update_group_background(group)
        self._save_data()

    def remove_group(self, item):
        idx = self.tree.indexOfTopLevelItem(item)
        self.tree.takeTopLevelItem(idx)
        self._save_data()

    def update_player_background(self, item, val):
        color = QtGui.QColor(0, 210, 0, int(0.3 * 255)) if val == 1 else QtGui.QColor(210, 0, 0, int(0.2 * 255))
        for col in range(4):
            item.setBackground(col, QtGui.QBrush(color))

    def update_group_sum(self, group_item):
        shard_sum = 0
        n = group_item.childCount()
        for i in range(n):
            wrapper = self.tree.itemWidget(group_item.child(i), 2)
            counter_widget = None
            if wrapper is not None:
                counter_widget = wrapper.findChild(ShardCounterWidget)
            val = counter_widget.val if counter_widget else 0
            shard_sum += val
        group_item.setText(2, str(shard_sum))

    def update_group_background(self, group_item):
        n = group_item.childCount()
        if n == 0:
            color = QtGui.QColor(255, 255, 255)
        else:
            shard_sum = int(group_item.text(2))
            color = QtGui.QColor(0, 210, 0, int(0.3 * 255)) if shard_sum == n else QtGui.QColor(210, 0, 0, int(0.2 * 255))
        for col in range(4):
            group_item.setBackground(col, QtGui.QBrush(color))

    def _header_clicked(self, section):
        if section == 0:
            if not self.is_collapsed:
                self.collapse_all_rows()
                self.tree.headerItem().setText(0, "⯈")
                self.is_collapsed = True
            else:
                self.expand_all_rows()
                self.tree.headerItem().setText(0, "⯆")
                self.is_collapsed = False


    def collapse_all_rows(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            self.tree.collapseItem(parent)

    def expand_all_rows(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            self.tree.expandItem(parent)

    def _on_item_collapsed_or_expanded(self, item):
        if item.parent() is None:
            self.update_group_background(item)


    def _save_data(self):
        all_groups = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            group = {
                "group": group_item.text(1),
                "players": []
            }
            for j in range(group_item.childCount()):
                player_item = group_item.child(j)
                player_name = player_item.text(1)
                wrapper = self.tree.itemWidget(player_item, 2)
                counter_widget = None
                if wrapper is not None:
                    counter_widget = wrapper.findChild(ShardCounterWidget)
                shards = counter_widget.val if counter_widget else 0
                group["players"].append({"name": player_name, "shards": shards})
            all_groups.append(group)
        with open(self.data_file, 'w', encoding="utf-8") as f:
            json.dump(all_groups, f, indent=2, ensure_ascii=False)

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, encoding="utf-8") as f:
                    all_groups = json.load(f)
            except json.JSONDecodeError:
                all_groups = []
        else:
            all_groups = []
        for group_info in all_groups:
            group_name = group_info["group"]
            players = group_info.get("players", [])
            group_item = QtWidgets.QTreeWidgetItem(self.tree)
            group_item.setText(1, group_name)
            group_item.setExpanded(False)
            group_item.setSizeHint(0, QtCore.QSize(0, self.row_height_parent))
            self.update_group_background(group_item)
            for player in players:
                player_item = QtWidgets.QTreeWidgetItem(group_item)
                player_item.setText(1, player["name"])
                player_item.setSizeHint(0, QtCore.QSize(0, self.row_height_child))
                self.update_player_background(player_item, player["shards"])
                counter = ShardCounterWidget(initial=player["shards"])
                counter.valueChanged.connect(lambda v, item=player_item: self.player_counter_changed(item, v))
                self.tree.setItemWidget(player_item, 2, counter)
                btn = RemoveButtonWidget()
                btn.clicked.connect(lambda _, item=player_item: self.remove_player(item))
                self.tree.setItemWidget(player_item, 3, btn)
            self.update_group_sum(group_item)
            btn = RemoveButtonWidget()
            btn.clicked.connect(lambda _, item=group_item: self.remove_group(item))
            self.tree.setItemWidget(group_item, 3, btn)
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                group_item = root.child(i)
                self.update_group_background(group_item)

    def closeEvent(self, event):
        self._save_data()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
