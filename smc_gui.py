import sys
import os
import subprocess
from pathlib import Path

# Importeer de engine
import smc_cleaner as engine

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QLabel, QSpacerItem, QSizePolicy, QDialog, 
    QFormLayout, QLineEdit, QComboBox, QMenu, QProgressBar, 
    QListWidget, QGroupBox, QFileDialog, QFrame
)
from PySide6.QtCore import Qt, QSettings, QThread, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor

# =======================================================
# 🧵 WORKER THREADS
# =======================================================

class ScanWorker(QThread):
    finished = Signal(list, list)
    progress = Signal(str)
    
    def __init__(self, directories, settings):
        super().__init__()
        self.directories = directories
        self.settings = settings
        self.is_running = True

    def run(self):
        results, errors = engine.scan_disk(
            directories=self.directories,
            min_size_mb=self.settings['size'],
            min_age_days=self.settings['age'],
            age_mode=self.settings['mode'],
            top_n=self.settings['top_n'],
            progress_callback=self.emit_progress,
            should_stop=lambda: not self.is_running
        )
        if self.is_running:
            self.finished.emit(results, errors)

    def emit_progress(self, msg):
        self.progress.emit(msg)

    def stop(self):
        self.is_running = False

class DeleteWorker(QThread):
    finished = Signal(str)

    def __init__(self, items):
        super().__init__()
        self.items = items

    def run(self):
        log = engine.delete_files(self.items)
        success_count = len([l for l in log if "VERPLAATST" in l])
        total_mb = sum(item['size_mb'] for item in self.items)
        self.finished.emit(f"✅ {success_count} bestanden ({total_mb:.1f} MB) verplaatst naar Prullenbak.")

# =======================================================
# ⚙️ INSTELLINGEN SCHERM
# =======================================================

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None, current_dirs=None):
        super().__init__(parent)
        self.setWindowTitle("Instellingen & Filters")
        self.resize(500, 600)
        self.layout = QVBoxLayout(self)

        # Filters
        filter_group = QGroupBox("Scan Filters")
        form_layout = QFormLayout()
        
        self.top_n_input = QLineEdit(str(current_settings['top_n']))
        form_layout.addRow("Max. resultaten:", self.top_n_input)
        
        self.age_input = QLineEdit(str(current_settings['age']))
        form_layout.addRow("Minimale ouderdom (dagen):", self.age_input)
        
        self.size_input = QLineEdit(str(current_settings['size']))
        form_layout.addRow("Minimale grootte (MB):", self.size_input)
        
        self.mode_combo = QComboBox()
        for key, val in engine.AGE_MODES.items():
            self.mode_combo.addItem(val, key)
            if key == current_settings['mode']:
                self.mode_combo.setCurrentText(val)
        form_layout.addRow("Tijdscriterium:", self.mode_combo)
        
        filter_group.setLayout(form_layout)
        self.layout.addWidget(filter_group)

        # Mappen
        dir_group = QGroupBox("Te Scannen Mappen")
        dir_layout = QVBoxLayout()
        
        self.dir_list = QListWidget()
        for d in current_dirs:
            self.dir_list.addItem(d)
        dir_layout.addWidget(self.dir_list)
        
        btn_box = QHBoxLayout()
        add_btn = QPushButton("➕ Map Toevoegen")
        add_btn.clicked.connect(self.add_dir)
        del_btn = QPushButton("➖ Verwijder Selectie")
        del_btn.clicked.connect(self.remove_dir)
        btn_box.addWidget(add_btn)
        btn_box.addWidget(del_btn)
        
        dir_layout.addLayout(btn_box)
        dir_group.setLayout(dir_layout)
        self.layout.addWidget(dir_group)

        # Knoppen
        ok_btn = QPushButton("Opslaan & Sluiten")
        ok_btn.clicked.connect(self.accept)
        self.layout.addWidget(ok_btn)

    def add_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Kies een map")
        if d:
            items = [self.dir_list.item(i).text() for i in range(self.dir_list.count())]
            if d not in items:
                self.dir_list.addItem(d)

    def remove_dir(self):
        for item in self.dir_list.selectedItems():
            self.dir_list.takeItem(self.dir_list.row(item))

    def get_data(self):
        idx = self.mode_combo.currentIndex()
        mode_key = self.mode_combo.itemData(idx)
        
        settings = {
            'top_n': int(self.top_n_input.text()),
            'age': int(self.age_input.text()),
            'size': int(self.size_input.text()),
            'mode': mode_key
        }
        dirs = [self.dir_list.item(i).text() for i in range(self.dir_list.count())]
        return settings, dirs

# =======================================================
# 📱 HOOFDSCHERM
# =======================================================

class SafeMacCleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Safe Mac Cleaner")
        self.setGeometry(100, 100, 1200, 800)
        
        # --- LOGO SETUP ---
        script_dir = Path(__file__).parent
        self.logo_path = str(script_dir / "logo-sfc.png")
        
        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))
        
        self.prefs = QSettings("SafeMacCleaner", "Config")
        self.load_settings()
        self.scan_errors = [] 

        self.setup_ui()
        self.worker = None
        
        self.start_scan()

    def load_settings(self):
        self.scan_dirs = self.prefs.value("scan_dirs", engine.DEFAULT_SCAN_DIRS)
        self.settings = {
            'top_n': int(self.prefs.value("top_n", engine.DEFAULT_TOP_N)),
            'age': int(self.prefs.value("age", engine.DEFAULT_MIN_AGE_DAYS)),
            'size': int(self.prefs.value("size", engine.DEFAULT_MIN_SIZE_MB)),
            'mode': self.prefs.value("mode", engine.DEFAULT_AGE_MODE)
        }

    def save_settings(self):
        self.prefs.setValue("scan_dirs", self.scan_dirs)
        self.prefs.setValue("top_n", self.settings['top_n'])
        self.prefs.setValue("age", self.settings['age'])
        self.prefs.setValue("size", self.settings['size'])
        self.prefs.setValue("mode", self.settings['mode'])

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25) 

        # --- HEADER (HORIZONTAAL) ---
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 10)

        # 1. INFO (LINKS)
        left_box = QVBoxLayout()
        
        # NIEUW: App Titel
        self.title_lbl = QLabel("Safe Mac Cleaner")
        self.title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        left_box.addWidget(self.title_lbl)
        
        self.header_lbl = QLabel("Schijfruimte aan het berekenen...")
        self.header_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #E0E0E0;")
        left_box.addWidget(self.header_lbl)
        
        self.warn_btn = QPushButton("⚠️ Waarschuwingen")
        self.warn_btn.setObjectName("warningButton")
        self.warn_btn.setCursor(Qt.PointingHandCursor)
        self.warn_btn.clicked.connect(self.show_errors)
        self.warn_btn.hide()
        left_box.addWidget(self.warn_btn)
        
        header_row.addLayout(left_box)

        # 2. SPACER
        header_row.addStretch()

        # 3. LOGO (RECHTS)
        if os.path.exists(self.logo_path):
            logo_lbl = QLabel()
            pixmap = QPixmap(self.logo_path)
            scaled_pixmap = pixmap.scaled(140, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(scaled_pixmap)
            logo_lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)
            header_row.addWidget(logo_lbl)
        
        layout.addLayout(header_row)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: #2A2A2A; } QProgressBar::chunk { background: #007AFF; }")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Klaar voor scan.")
        self.status_lbl.setStyleSheet("color: #888; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(self.status_lbl)

        # --- TABEL (NAADLOOS) ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "#", "Grootte (MB)", "Dagen oud", "Type", "Pad"])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False) 
        self.table.setFocusPolicy(Qt.NoFocus) 
        
        self.table.itemChanged.connect(self.on_item_checked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)

        # Knoppenbalk
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        self.btn_scan = QPushButton("🚀 Start Scan")
        self.btn_scan.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.btn_scan)

        self.btn_stop = QPushButton("🛑 Stop")
        self.btn_stop.clicked.connect(self.stop_scan)
        self.btn_stop.setEnabled(False)
        btn_layout.addWidget(self.btn_stop)

        self.btn_settings = QPushButton("⚙️ Instellingen")
        self.btn_settings.clicked.connect(self.open_settings)
        btn_layout.addWidget(self.btn_settings)

        self.btn_select_all = QPushButton("✅ Selecteer Alles")
        self.btn_select_all.clicked.connect(self.toggle_select_all)
        self.btn_select_all.setEnabled(False)
        btn_layout.addWidget(self.btn_select_all)

        self.btn_preview = QPushButton("🔍 Toon in Finder")
        self.btn_preview.clicked.connect(self.preview_file)
        self.btn_preview.setEnabled(False) 
        btn_layout.addWidget(self.btn_preview)

        btn_layout.addStretch()

        self.btn_trash = QPushButton("🗑️ Verwijder Selectie")
        self.btn_trash.setEnabled(False)
        self.btn_trash.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.btn_trash)

        self.btn_empty = QPushButton("⚠️ Leeg Prullenbak")
        self.btn_empty.clicked.connect(self.empty_trash)
        btn_layout.addWidget(self.btn_empty)

        layout.addLayout(btn_layout)
        
        # NIEUW: Footer
        layout.addSpacing(15)
        footer_lbl = QLabel("© 2025 Safe Mac Cleaner door T. Welles")
        footer_lbl.setAlignment(Qt.AlignCenter)
        footer_lbl.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(footer_lbl)

    # --- LOGICA ---

    def start_scan(self):
        if self.worker and self.worker.isRunning(): return
        
        self.table.setRowCount(0)
        self.ranked_results = []
        self.scan_errors = []
        self.warn_btn.hide() 

        self.btn_scan.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_trash.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_select_all.setEnabled(False)
        self.progress_bar.show()
        
        self.update_disk_stats()

        self.worker = ScanWorker(self.scan_dirs, self.settings)
        self.worker.progress.connect(self.status_lbl.setText)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.status_lbl.setText("🛑 Scan geannuleerd.")
            self.on_scan_finished([], [])

    def on_scan_finished(self, results, errors):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.hide()
        
        if not self.worker.is_running and not results and not errors: return

        self.ranked_results = results
        self.scan_errors = errors
        
        if errors:
            self.warn_btn.setText(f"⚠️ {len(errors)} mappen overgeslagen")
            self.warn_btn.show()

        self.populate_table()
        
        self.btn_select_all.setEnabled(len(results) > 0)
        total_mb = sum(r['size_mb'] for r in results)
        self.status_lbl.setText(f"✅ Klaar. {len(results)} bestanden gevonden ({total_mb:.1f} MB totaal).")

    def show_errors(self):
        if not self.scan_errors: return
        msg = "De volgende mappen konden niet worden gescand (geen toegang):\n\n"
        msg += "\n".join(self.scan_errors[:10])
        if len(self.scan_errors) > 10: msg += f"\n... en nog {len(self.scan_errors)-10} andere."
        QMessageBox.warning(self, "Scan Waarschuwing", msg)

    def populate_table(self):
        self.table.setRowCount(len(self.ranked_results))
        self.table.blockSignals(True)
        
        for i, item in enumerate(self.ranked_results):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            self.table.setItem(i, 0, chk)
            
            self.table.setItem(i, 1, QTableWidgetItem(str(i+1)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{item['size_mb']:.1f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(item['age_days']))))
            self.table.setItem(i, 4, QTableWidgetItem(item['file_type']))
            self.table.setItem(i, 5, QTableWidgetItem(item['path']))
            
        self.table.blockSignals(False)

    def on_item_checked(self):
        count = 0
        size = 0
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                count += 1
                size += self.ranked_results[i]['size_mb']
        
        if count > 0:
            self.btn_trash.setText(f"🗑️ Verwijder {count} items ({size:.1f} MB)")
            self.btn_trash.setEnabled(True)
            self.btn_preview.setEnabled(True)
        else:
            self.btn_trash.setText("🗑️ Verwijder Selectie")
            self.btn_trash.setEnabled(False)
            self.btn_preview.setEnabled(False)

    def toggle_select_all(self):
        if self.table.rowCount() == 0: return
        self.table.blockSignals(True)
        first_checked = self.table.item(0, 0).checkState() == Qt.Checked
        new_state = Qt.Unchecked if first_checked else Qt.Checked
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(new_state)
        self.table.blockSignals(False)
        self.on_item_checked()

    def preview_file(self):
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                path = self.ranked_results[i]['path']
                subprocess.run(['open', '-R', path])
                return

    def delete_selected(self):
        indexes = [i for i in range(self.table.rowCount()) if self.table.item(i, 0).checkState() == Qt.Checked]
        if not indexes: return
        items_to_del = [self.ranked_results[i] for i in indexes]
        confirm = QMessageBox.question(self, "Bevestigen", f"Verplaats {len(items_to_del)} bestanden naar Prullenbak?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.del_worker = DeleteWorker(items_to_del)
            self.del_worker.finished.connect(self.on_delete_finished)
            self.del_worker.start()
            self.btn_trash.setEnabled(False)
            self.status_lbl.setText("⏳ Bezig met verplaatsen...")

    def on_delete_finished(self, msg):
        QMessageBox.information(self, "Voltooid", msg)
        self.start_scan()

    def empty_trash(self):
        confirm = QMessageBox.warning(self, "PAS OP", "Dit leegt de HELE Prullenbak. Dit kan niet ongedaan gemaakt worden!", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            subprocess.run(['osascript', '-e', 'tell application "Finder" to empty trash'])
            self.update_disk_stats()

    def update_disk_stats(self):
        s = engine.get_disk_stats()
        color = "#4CAF50" if s['percent_free'] > 20 else "#FF9800" if s['percent_free'] > 10 else "#F44336"
        self.header_lbl.setText(f"Vrij: {s['free_gb']:.1f} GB ({s['total_gb']:.0f} GB totaal) - <span style='color:{color}'>{s['percent_free']:.1f}% beschikbaar</span>")

    def show_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid(): return
        row = idx.row()
        path = self.ranked_results[row]['path']
        menu = QMenu()
        act_open = QAction("🔍 Toon in Finder", self)
        act_open.triggered.connect(lambda: subprocess.run(['open', '-R', path]))
        menu.addAction(act_open)
        act_exclude = QAction("🚫 Sluit dit bestand voortaan uit", self)
        act_exclude.triggered.connect(lambda: self.exclude_file(path))
        menu.addAction(act_exclude)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def exclude_file(self, path):
        engine.toggle_exclusion(path, True)
        self.start_scan()

    def open_settings(self):
        dlg = SettingsDialog(self, self.settings, self.scan_dirs)
        if dlg.exec():
            new_settings, new_dirs = dlg.get_data()
            self.settings = new_settings
            self.scan_dirs = new_dirs
            self.save_settings()
            self.start_scan()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # --- ULTRA CLEAN DARK THEME ---
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1E1E1E;
        }
        QLabel {
            color: #E0E0E0;
        }
        QTableWidget {
            background-color: #1E1E1E;
            color: #E0E0E0;
            border: none;
            gridline-color: #2A2A2A;
        }
        QTableWidget::item { 
            padding: 8px; 
            border-bottom: 1px solid #2A2A2A;
        }
        QTableWidget::item:selected {
            background-color: #334455;
            color: white;
        }
        QHeaderView::section { 
            background-color: #1E1E1E;
            color: #999;
            text-transform: uppercase;
            font-size: 11px;
            font-weight: bold;
            padding: 6px;
            border: none;
            border-bottom: 2px solid #333;
        }
        QScrollBar:vertical {
            border: none;
            background: #1E1E1E;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #444;
            min-height: 20px;
            border-radius: 5px;
        }
        
        /* KNOPPEN */
        QPushButton {
            background-color: #2D2D2D;
            color: #CCCCCC;
            border: 1px solid #3E3E3E;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #383838;
            border-color: #555555;
            color: white;
        }
        QPushButton:pressed {
            background-color: #222222;
        }
        QPushButton:disabled {
            background-color: #222222;
            color: #555555;
            border-color: #2A2A2A;
        }
        
        QPushButton#warningButton {
            background-color: #D4AF37; 
            color: #222222;
            border: none;
            font-weight: bold;
        }
    """)
    
    window = SafeMacCleanerApp()
    window.show()
    sys.exit(app.exec())