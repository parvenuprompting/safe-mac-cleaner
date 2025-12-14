import sys
import os
import subprocess 

# Importeer de logica en configuratie uit uw bestaande script
from smc_cleaner import validate_and_scan, execute_deletion, get_disk_stats 
# Importeer de constanten voor de startwaarden
from smc_cleaner import TOP_N_RESULTS, MINIMUM_SIZE_MB, MINIMUM_AGE_DAYS, AGE_MODE

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                               QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QLabel, QSpacerItem, QSizePolicy,
                               QDialog, QFormLayout, QLineEdit, QComboBox)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# =======================================================
# INSTELINGEN DIALOOGVENSTER
# =======================================================

class SettingsDialog(QDialog):
    """Dialoogvenster voor het aanpassen van de scanfilters."""
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Instellingen Aanpassen")
        self.settings = settings
        self.layout = QFormLayout(self)
        
        # 1. Aantal Getoonde Items (TOP_N_RESULTS)
        self.top_n_input = QLineEdit(self)
        self.top_n_input.setText(str(self.settings['TOP_N_RESULTS']))
        self.layout.addRow("Max. Aantal Resultaten:", self.top_n_input)
        
        # 2. Minimum Ouderdom (MINIMUM_AGE_DAYS)
        self.age_input = QLineEdit(self)
        self.age_input.setText(str(self.settings['MINIMUM_AGE_DAYS']))
        self.layout.addRow("Minimale Ouderdom (Dagen):", self.age_input)
        
        # 3. Ouderdom Modus (AGE_MODE)
        self.mode_combo = QComboBox(self)
        self.mode_combo.addItems(['last_used', 'last_modified']) # 'last_modified' komt overeen met st_mtime
        self.mode_combo.setCurrentText(self.settings['AGE_MODE'])
        self.layout.addRow("Tijdscriterium:", self.mode_combo)
        
        # 4. Minimum Grootte (MINIMUM_SIZE_MB)
        self.size_input = QLineEdit(self)
        self.size_input.setText(str(self.settings['MINIMUM_SIZE_MB']))
        self.layout.addRow("Minimale Grootte (MB):", self.size_input)

        # OK/Annuleer Knoppen
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Opslaan en Sluiten")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Annuleren")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addRow(button_layout)
        
    def get_settings(self):
        """Geeft de ingevoerde en gevalideerde instellingen terug."""
        try:
            new_settings = {
                'TOP_N_RESULTS': int(self.top_n_input.text()),
                'MINIMUM_AGE_DAYS': int(self.age_input.text()),
                'AGE_MODE': self.mode_combo.currentText(),
                'MINIMUM_SIZE_MB': int(self.size_input.text())
            }
            if new_settings['TOP_N_RESULTS'] <= 0 or new_settings['MINIMUM_AGE_DAYS'] < 0 or new_settings['MINIMUM_SIZE_MB'] < 0:
                 QMessageBox.warning(self, "Ongeldige Invoer", "Voer geldige positieve nummers in.")
                 return None
            return new_settings
        except ValueError:
            QMessageBox.warning(self, "Ongeldige Invoer", "Zorg ervoor dat alle waarden hele getallen zijn.")
            return None


# =======================================================
# HOOFD APPLICATIE VENSTER
# =======================================================

class SafeMacCleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Safe Mac Cleaner") 
        self.setGeometry(100, 100, 1100, 700) 

        # Initialiseer dynamische instellingen met de standaardwaarden
        self.top_n_results = TOP_N_RESULTS
        self.minimum_age_days = MINIMUM_AGE_DAYS
        self.age_mode = AGE_MODE
        self.minimum_size_mb = MINIMUM_SIZE_MB

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        
        self.ranked_results = [] 

        self.init_menu_bar()
        self.init_ui()
        
    def init_menu_bar(self):
        """Voegt de menubalk toe met de Instellingen optie."""
        menu_bar = self.menuBar()
        
        # Instellingen Menu
        settings_menu = menu_bar.addMenu("Instellingen")
        settings_action = settings_menu.addAction("Pas Filters Aan...")
        settings_action.triggered.connect(self.show_settings_dialog)
        
    def show_settings_dialog(self):
        """Toont het dialoogvenster voor instellingen."""
        current_settings = {
            'TOP_N_RESULTS': self.top_n_results,
            'MINIMUM_AGE_DAYS': self.minimum_age_days,
            'AGE_MODE': self.age_mode,
            'MINIMUM_SIZE_MB': self.minimum_size_mb
        }
        
        dialog = SettingsDialog(self, settings=current_settings)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            if new_settings:
                self.top_n_results = new_settings['TOP_N_RESULTS']
                self.minimum_age_days = new_settings['MINIMUM_AGE_DAYS']
                self.age_mode = new_settings['AGE_MODE']
                self.minimum_size_mb = new_settings['MINIMUM_SIZE_MB']
                
                QMessageBox.information(self, "Instellingen Opgeslagen", 
                                        "Nieuwe instellingen zijn opgeslagen voor deze sessie. Voer een nieuwe scan uit om de resultaten bij te werken.")
                
                self.update_status_label()


    def update_status_label(self):
        """Update het filter label met de huidige dynamische instellingen."""
        self.status_label.setText(
            f"Filter: >{self.minimum_size_mb}MB | >{self.minimum_age_days} dagen niet gebruikt ({self.age_mode}) | Max. {self.top_n_results} items getoond."
        )


    def init_ui(self):
        # 0. Header (Totaal Schijfgebruik)
        self.disk_header_label = QLabel()
        self.disk_header_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.main_layout.addWidget(self.disk_header_label)
        
        # 1. Status/Filter Label
        self.status_label = QLabel()
        self.update_status_label() 
        self.status_label.setFont(QFont("Arial", 11))
        self.main_layout.addWidget(self.status_label)
        
        # 2. Tabel voor Resultaten
        self.table = QTableWidget()
        # 6 kolommen: Selecteer, #, Grootte, Ouderdom, Type, Bestand
        self.table.setColumnCount(6)
        
        self.table.setHorizontalHeaderLabels(["Selecteer", "#", "Grootte (MB)", "Ouderdom (Dagen)", "Type", "Bestand"])
        
        self.table.verticalHeader().setVisible(False) 
        
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch) 
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Checkbox kolom
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Nummer kolom
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows) 
        self.table.setSelectionMode(QTableWidget.NoSelection) # Geen rij selectie

        self.main_layout.addWidget(self.table)
        
        # 3. Knoppen
        button_layout = QHBoxLayout()
        button_style = "padding: 5px; font-weight: bold; min-height: 30px;"
        
        # 3a. Start Nieuwe Scan
        self.scan_button = QPushButton("🚀 Start Nieuwe Scan")
        self.scan_button.clicked.connect(self.run_scan)
        self.scan_button.setStyleSheet(button_style)
        button_layout.addWidget(self.scan_button)
        
        # 3b. Selecteer/Deselecteer Alles
        self.select_all_button = QPushButton("✅ Selecteer Alles")
        self.select_all_button.clicked.connect(self.toggle_select_all)
        self.select_all_button.setStyleSheet(button_style)
        button_layout.addWidget(self.select_all_button)
        
        button_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 3c. Toon in Finder (Inspectie)
        self.preview_button = QPushButton("🔍 Toon Selectie in Finder")
        self.preview_button.clicked.connect(self.preview_file)
        self.preview_button.setEnabled(False) 
        self.preview_button.setStyleSheet(button_style)
        button_layout.addWidget(self.preview_button)

        # 3d. Verplaats Geselecteerde naar Prullenbak
        self.delete_selected_button = QPushButton("🗑️ Verplaats Geselecteerde naar Prullenbak")
        self.delete_selected_button.clicked.connect(self.delete_selected)
        self.delete_selected_button.setEnabled(False) 
        self.delete_selected_button.setStyleSheet(button_style)
        button_layout.addWidget(self.delete_selected_button)
        
        # 3e. Leeg Prullenbak (Permanente Actie)
        self.empty_trash_button = QPushButton("🗑️ Leeg Prullenbak")
        self.empty_trash_button.clicked.connect(self.empty_trash)
        self.empty_trash_button.setStyleSheet(button_style)
        button_layout.addWidget(self.empty_trash_button)
        
        self.main_layout.addLayout(button_layout)
        
        self.run_scan()
        
    def update_disk_header(self):
        """Update de header met de schijfgebruiksinformatie."""
        stats = get_disk_stats()
        
        color = 'green' if stats['percent_free'] > 15 else ('orange' if stats['percent_free'] > 5 else 'red')
        
        header_text = (
            f"Totaal Geheugen: {stats['total_gb']:.2f} GB | "
            f"Vrij: {stats['free_gb']:.2f} GB | "
            f"<span style='color: {color};'>Nog Vrij: {stats['percent_free']:.1f}%</span>"
        )
        self.disk_header_label.setText(header_text)

    def run_scan(self):
        self.table.setRowCount(0) 
        self.status_label.setText(f"Bezig met scannen... Dit kan even duren. Filter: >{self.minimum_size_mb}MB | >{self.minimum_age_days}d")
        QApplication.processEvents() 
        
        # GEBRUIK DE DYNAMISCHE INSTELINGEN VOOR DE SCAN
        all_candidates = validate_and_scan(
            self.top_n_results, 
            self.minimum_age_days, 
            self.age_mode, 
            self.minimum_size_mb
        )
        
        # FIX: Slicing voor het filteren op TOP_N_RESULTS (Max aantal)
        self.ranked_results = all_candidates[:self.top_n_results]

        self.display_results()
        
    def display_results(self):
        self.update_disk_header() 
        
        if not self.ranked_results:
            self.status_label.setText("🎉 Scannen voltooid. Geen bestanden gevonden die voldoen aan de criteria.")
            self.preview_button.setEnabled(False)
            self.delete_selected_button.setEnabled(False)
            self.select_all_button.setEnabled(False)
            return

        total_size = sum(item['size_mb'] for item in self.ranked_results)
        self.status_label.setText(
            f"Totaal {len(self.ranked_results)} bestanden gevonden. Totale grootte: {total_size:.2f} MB. Vink rijen aan om te verwijderen."
        )

        self.table.setRowCount(len(self.ranked_results))
        for i, item in enumerate(self.ranked_results):
            # Kolom 0: Checkbox
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Unchecked)
            self.table.setItem(i, 0, check_item)
            
            # Kolom 1: Nummering
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, num_item)

            # Kolom 2 t/m 5: Data
            self.table.setItem(i, 2, QTableWidgetItem(f"{item['size_mb']:.1f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(int(item['age_days']))))
            self.table.setItem(i, 4, QTableWidgetItem(item['file_type']))
            self.table.setItem(i, 5, QTableWidgetItem(os.path.basename(item['path'].replace("file://", ""))))
            
        self.table.resizeColumnsToContents()
        self.preview_button.setEnabled(True)
        self.delete_selected_button.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.select_all_button.setText("✅ Selecteer Alles")

    def toggle_select_all(self):
        """Selecteert of deselecteert alle rijen op basis van de checkbox-status."""
        if self.table.rowCount() == 0:
            return
            
        is_checked = self.table.item(0, 0).checkState() == Qt.Checked
        new_state = Qt.Unchecked if is_checked else Qt.Checked
        
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(new_state)
            
        if new_state == Qt.Checked:
            self.select_all_button.setText("❌ Deselecteer Alles")
        else:
            self.select_all_button.setText("✅ Selecteer Alles")


    def get_checked_rows(self):
        """Retourneert een lijst met indexen van aangevinkte rijen."""
        indexes = []
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) and self.table.item(row, 0).checkState() == Qt.Checked:
                indexes.append(row)
        return indexes

    def preview_file(self):
        """Opent de Finder voor de EERSTE aangevinkte rij."""
        indexes = self.get_checked_rows()
                
        if indexes:
            first_checked_row = indexes[0]
            file_path = self.ranked_results[first_checked_row]['path'].replace("file://", "") 
            subprocess.run(['open', '-R', file_path]) 
        else:
            QMessageBox.warning(self, "Geen Selectie", "Vink een item aan om het in Finder te bekijken.")


    def delete_selected(self):
        """Verplaatst alle aangevinkte items naar de Prullenbak."""
        
        indexes_to_delete = self.get_checked_rows()

        if not indexes_to_delete:
            QMessageBox.warning(self, "Geen Selectie", "Vink de bestanden aan die u wilt verwijderen.")
            return
            
        reply = QMessageBox.question(self, 'Bevestigen', 
                                     f"Weet u zeker dat u {len(indexes_to_delete)} aangevinkte bestanden naar de Prullenbak wilt verplaatsen?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            action_log = execute_deletion(self.ranked_results, indexes_to_delete)
            
            verplaatste_bestanden = [l for l in action_log if l.startswith('VERPLAATST')]
            try:
                verplaatste_grootte = sum(float(l.split(':')[1].split(' MB')[0].strip()) for l in verplaatste_bestanden)
            except Exception:
                verplaatste_grootte = 0 
                
            total_deleted = len(verplaatste_bestanden)
            
            QMessageBox.information(self, "Opschoning Voltooid", 
                                      f"✅ {total_deleted} bestanden ({verplaatste_grootte:.2f} MB) zijn succesvol verplaatst naar de Prullenbak.\n\n"
                                      f"U kunt nu de Prullenbak legen.")
            
            self.run_scan() 

    def empty_trash(self):
        """Voert het macOS-commando uit om de Prullenbak te legen."""
        
        command = ['osascript', '-e', 'tell application "Finder" to empty trash'] 
        
        reply = QMessageBox.question(self, 'Prullenbak Legen Bevestigen', 
                                     "Weet u zeker dat u de Prullenbak permanent wilt legen? (Dit kan niet ongedaan gemaakt worden!)",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            try:
                self.status_label.setText("🗑️ Prullenbak wordt geleegd...")
                QApplication.processEvents()
                
                subprocess.run(command, check=True)
                QMessageBox.information(self, "Prullenbak Geleegd", "✅ De Prullenbak is geleegd!")
            except subprocess.CalledProcessError:
                 QMessageBox.critical(self, "Fout", "❌ Kon de Prullenbak niet legen. Controleer machtigingen.")
            
            self.update_disk_header() 
            self.update_status_label() 


if __name__ == '__main__':
    if sys.platform == 'darwin':
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
    app = QApplication(sys.argv)
    window = SafeMacCleanerApp()
    window.show()
    sys.exit(app.exec())