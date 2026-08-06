import json
import os
import sys
from datetime import datetime

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import platform_macos

# Importeer de engine
import smc_cleaner as engine
from models import SCAN_PROFILES, ScanSettings
from workers import DeleteWorker, ScanWorker

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
        
        self.top_n_input = QSpinBox()
        self.top_n_input.setRange(1, 10000)
        self.top_n_input.setValue(current_settings['top_n'])
        form_layout.addRow("Max. resultaten:", self.top_n_input)
        
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 36500)
        self.age_input.setValue(current_settings['age'])
        form_layout.addRow("Minimale ouderdom (dagen):", self.age_input)
        
        self.size_input = QSpinBox()
        self.size_input.setRange(0, 1000000)
        self.size_input.setValue(current_settings['size'])
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
            valid_dirs, errors = engine.validate_scan_directories([d])
            if not valid_dirs:
                QMessageBox.warning(
                    self,
                    "Ongeldige scanmap",
                    "Kies een map binnen je eigen home-directory.\n\n" + "\n".join(errors),
                )
                return
            d = valid_dirs[0]
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
            'top_n': self.top_n_input.value(),
            'age': self.age_input.value(),
            'size': self.size_input.value(),
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
        
        # --- PATH FIX VOOR PYINSTALLER ---
        # Dit zorgt dat hij het logo vindt, zowel tijdens testen als in de .app
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.logo_path = os.path.join(base_path, "logo-sfc.png")
        
        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))
        
        self.prefs = QSettings("SafeMacCleaner", "Config")
        self.load_settings()
        self.scan_errors = [] 
        self.scan_stats = {}
        self.scan_history = self.load_history()

        self.setup_ui()
        self.worker = None
        
        self.start_scan()

    def load_settings(self):
        raw_dirs = self.prefs.value("scan_dirs", engine.DEFAULT_SCAN_DIRS)
        self.scan_dirs = [raw_dirs] if isinstance(raw_dirs, str) else list(raw_dirs)
        self.settings = ScanSettings.from_values(
            self.prefs.value("top_n", engine.DEFAULT_TOP_N),
            self.prefs.value("age", engine.DEFAULT_MIN_AGE_DAYS),
            self.prefs.value("size", engine.DEFAULT_MIN_SIZE_MB),
            self.prefs.value("mode", engine.DEFAULT_AGE_MODE),
        ).as_dict()

    def save_settings(self):
        self.prefs.setValue("scan_dirs", self.scan_dirs)
        self.prefs.setValue("top_n", self.settings['top_n'])
        self.prefs.setValue("age", self.settings['age'])
        self.prefs.setValue("size", self.settings['size'])
        self.prefs.setValue("mode", self.settings['mode'])

    def load_history(self):
        raw_history = self.prefs.value("scan_history", "[]")
        try:
            history = json.loads(raw_history) if isinstance(raw_history, str) else raw_history
            return history if isinstance(history, list) else []
        except (TypeError, ValueError):
            return []

    def save_history(self):
        self.prefs.setValue("scan_history", json.dumps(self.scan_history[:20]))

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
        self.table.setSortingEnabled(True)
        
        self.table.itemChanged.connect(self.on_item_checked)
        self.table.itemSelectionChanged.connect(self.update_details)
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

        self.btn_exclusions = QPushButton("🚫 Uitsluitingen")
        self.btn_exclusions.clicked.connect(self.manage_exclusions)
        btn_layout.addWidget(self.btn_exclusions)

        self.btn_history = QPushButton("🕘 Historie")
        self.btn_history.clicked.connect(self.show_history)
        btn_layout.addWidget(self.btn_history)

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

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Profiel:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(SCAN_PROFILES.keys())
        self.profile_combo.currentTextChanged.connect(self.apply_profile)
        search_layout.addWidget(self.profile_combo)
        search_layout.addWidget(QLabel("Zoeken:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter op bestandsnaam of pad...")
        self.search_input.textChanged.connect(self.filter_results)
        search_layout.addWidget(self.search_input)
        layout.insertLayout(layout.count() - 1, search_layout)

        self.detail_lbl = QLabel("Selecteer een resultaat voor details.")
        self.detail_lbl.setWordWrap(True)
        self.detail_lbl.setStyleSheet("color: #999; font-size: 12px; padding: 5px 0;")
        layout.insertWidget(layout.count() - 1, self.detail_lbl)
        
        # Footer
        layout.addSpacing(15)
        footer_lbl = QLabel("© 2026 Tiëndo Welles")
        footer_lbl.setAlignment(Qt.AlignCenter)
        footer_lbl.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(footer_lbl)

    # --- LOGICA ---

    def start_scan(self):
        if self.worker and self.worker.isRunning(): return
        
        self.table.setRowCount(0)
        self.ranked_results = []
        self.scan_errors = []
        self.scan_stats = {}
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
        self.worker.completed.connect(self.on_scan_finished)
        self.worker.cancelled.connect(self.on_scan_cancelled)
        self.worker.failed.connect(self.on_scan_failed)
        self.worker.finished.connect(self.clear_scan_worker)
        self.worker.start()

    def clear_scan_worker(self):
        if self.sender() is self.worker:
            self.worker = None

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            self.status_lbl.setText("🛑 Scan geannuleerd.")

    def on_scan_cancelled(self):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.hide()
        self.status_lbl.setText("🛑 Scan geannuleerd.")

    def on_scan_failed(self, message):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.hide()
        self.status_lbl.setText("❌ Scan mislukt.")
        QMessageBox.critical(self, "Scan mislukt", message)

    def on_scan_finished(self, results, errors, stats):
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.hide()
        
        self.ranked_results = results
        self.scan_errors = errors
        self.scan_stats = stats
        self.scan_history.insert(0, {
            "timestamp": datetime.now().astimezone().isoformat(timespec="minutes"),
            "count": len(results),
            "size_mb": round(sum(item["size_mb"] for item in results), 1),
            "errors": len(errors),
        })
        self.scan_history = self.scan_history[:20]
        self.save_history()
        
        if errors:
            self.warn_btn.setText(f"⚠️ {len(errors)} mappen overgeslagen")
            self.warn_btn.show()

        self.populate_table()
        
        self.btn_select_all.setEnabled(len(results) > 0)
        total_mb = sum(r['size_mb'] for r in results)
        inspected = stats.get("inspected_files", 0)
        skipped = stats.get("skipped_age", 0) + stats.get("skipped_size", 0)
        if results:
            status = f"✅ Klaar. {len(results)} bestanden gevonden ({total_mb:.1f} MB totaal)."
        else:
            status = (
                f"Geen geschikte bestanden gevonden. {inspected} bestanden onderzocht, "
                f"{skipped} door filters overgeslagen."
            )
        self.status_lbl.setText(status)

    def apply_profile(self, profile):
        if not hasattr(self, "settings") or not profile:
            return
        self.settings = ScanSettings.from_values(**self.settings).with_profile(profile).as_dict()
        self.save_settings()
        self.start_scan()

    def show_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Scanhistorie")
        dialog.resize(550, 350)
        dialog_layout = QVBoxLayout(dialog)
        history_list = QListWidget()
        if self.scan_history:
            for entry in self.scan_history:
                warning = f", {entry['errors']} waarschuwingen" if entry.get("errors") else ""
                history_list.addItem(
                    f"{entry.get('timestamp', 'Onbekend')}: "
                    f"{entry.get('count', 0)} bestanden, {entry.get('size_mb', 0):.1f} MB{warning}"
                )
        else:
            history_list.addItem("Nog geen scans uitgevoerd.")
        history_list.setSelectionMode(QListWidget.NoSelection)
        dialog_layout.addWidget(history_list)
        close_button = QPushButton("Sluiten")
        close_button.clicked.connect(dialog.accept)
        dialog_layout.addWidget(close_button)
        dialog.exec()

    def show_errors(self):
        if not self.scan_errors: return
        msg = "De volgende mappen konden niet worden gescand (geen toegang):\n\n"
        msg += "\n".join(self.scan_errors[:10])
        if len(self.scan_errors) > 10: msg += f"\n... en nog {len(self.scan_errors)-10} andere."
        QMessageBox.warning(self, "Scan Waarschuwing", msg)

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.ranked_results))
        self.table.blockSignals(True)
        
        for i, item in enumerate(self.ranked_results):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            chk.setData(Qt.UserRole, item["path"])
            self.table.setItem(i, 0, chk)
            
            self.table.setItem(i, 1, QTableWidgetItem(str(i+1)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{item['size_mb']:.1f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(item['age_days']))))
            self.table.setItem(i, 4, QTableWidgetItem(item['file_type']))
            self.table.setItem(i, 5, QTableWidgetItem(item['path']))
            
        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)
        self.filter_results(self.search_input.text())

    def result_for_row(self, row):
        path = self.table.item(row, 5).text()
        return next((item for item in self.ranked_results if item["path"] == path), None)

    def filter_results(self, query):
        query = query.casefold().strip()
        for row in range(self.table.rowCount()):
            path = self.table.item(row, 5).text().casefold()
            self.table.setRowHidden(row, bool(query and query not in path))

    def update_details(self):
        selected = self.table.selectedItems()
        if not selected:
            self.detail_lbl.setText("Selecteer een resultaat voor details.")
            return
        item = self.result_for_row(selected[0].row())
        if item:
            self.detail_lbl.setText(
                f"<b>{item['path']}</b> | {item['size_mb']:.1f} MB | "
                f"{int(item['age_days'])} dagen oud | Type: {item['file_type']}"
            )

    def on_item_checked(self):
        count = 0
        size = 0
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                count += 1
                item = self.result_for_row(i)
                if item:
                    size += item['size_mb']
        
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
                item = self.result_for_row(i)
                if not item:
                    continue
                path = item['path']
                platform_macos.reveal_in_finder(path)
                return

    def delete_selected(self):
        indexes = [i for i in range(self.table.rowCount()) if self.table.item(i, 0).checkState() == Qt.Checked]
        if not indexes: return
        items_to_del = [self.result_for_row(i) for i in indexes]
        items_to_del = [item for item in items_to_del if item]
        total_mb = sum(item['size_mb'] for item in items_to_del)
        preview = "\n".join(f"- {item['path']}" for item in items_to_del[:5])
        if len(items_to_del) > 5:
            preview += f"\n- ... en nog {len(items_to_del) - 5} bestanden"
        confirm = QMessageBox.question(
            self,
            "Verwijderen bevestigen",
            f"Verplaats {len(items_to_del)} bestanden ({total_mb:.1f} MB) naar de Prullenbak?\n\n{preview}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.del_worker = DeleteWorker(items_to_del)
            self.del_worker.completed.connect(self.on_delete_finished)
            self.del_worker.failed.connect(self.on_delete_failed)
            self.del_worker.finished.connect(self.del_worker.deleteLater)
            self.del_worker.start()
            self.btn_trash.setEnabled(False)
            self.status_lbl.setText("⏳ Bezig met verplaatsen...")

    def on_delete_finished(self, msg):
        result = msg
        succeeded = len(result['succeeded'])
        failed = result['failed']
        message = f"{succeeded} bestanden naar de Prullenbak verplaatst ({result['total_size_mb']:.1f} MB)."
        if failed:
            message += f"\n\n{len(failed)} bestanden konden niet worden verplaatst."
            message += "\n" + "\n".join(f"{item['path']}: {item['error']}" for item in failed[:5])
        QMessageBox.information(self, "Verwijderen voltooid", message)
        self.start_scan()

    def on_delete_failed(self, message):
        self.btn_trash.setEnabled(True)
        self.status_lbl.setText("❌ Verwijderen mislukt.")
        QMessageBox.critical(self, "Verwijderen mislukt", message)

    def empty_trash(self):
        confirm = QMessageBox.warning(self, "PAS OP", "Dit leegt de HELE Prullenbak. Dit kan niet ongedaan gemaakt worden!", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            succeeded, error = platform_macos.empty_trash()
            if not succeeded:
                QMessageBox.critical(
                    self,
                    "Prullenbak legen mislukt",
                    error,
                )
                return
            self.update_disk_stats()

    def update_disk_stats(self):
        s = engine.get_disk_stats()
        color = "#4CAF50" if s['percent_free'] > 20 else "#FF9800" if s['percent_free'] > 10 else "#F44336"
        self.header_lbl.setText(f"Vrij: {s['free_gb']:.1f} GB ({s['total_gb']:.0f} GB totaal) - <span style='color:{color}'>{s['percent_free']:.1f}% beschikbaar</span>")

    def show_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid(): return
        row = idx.row()
        item = self.result_for_row(row)
        if not item:
            return
        path = item['path']
        menu = QMenu()
        act_open = QAction("🔍 Toon in Finder", self)
        act_open.triggered.connect(lambda: platform_macos.reveal_in_finder(path))
        menu.addAction(act_open)
        act_exclude = QAction("🚫 Sluit dit bestand voortaan uit", self)
        act_exclude.triggered.connect(lambda: self.exclude_file(path))
        menu.addAction(act_exclude)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def exclude_file(self, path):
        engine.toggle_exclusion(path, True)
        self.start_scan()

    def manage_exclusions(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Uitsluitingen beheren")
        dialog.resize(650, 400)
        dialog_layout = QVBoxLayout(dialog)
        exclusion_list = QListWidget()
        exclusion_list.addItems(engine.load_exclusion_list())
        dialog_layout.addWidget(exclusion_list)

        remove_button = QPushButton("Verwijder geselecteerde uitsluiting")
        dialog_layout.addWidget(remove_button)

        def remove_selected():
            for item in exclusion_list.selectedItems():
                engine.toggle_exclusion(item.text(), False)
                exclusion_list.takeItem(exclusion_list.row(item))

        remove_button.clicked.connect(remove_selected)
        dialog.exec()
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
