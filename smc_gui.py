import sys
import os
import subprocess 

# Importeer de logica, uitsluitingsfuncties en configuratie uit uw bestaande script
from smc_cleaner import (validate_and_scan, execute_deletion, get_disk_stats, 
                         load_exclusion_list, add_to_exclusion_list, remove_from_exclusion_list)
# Importeer de constanten voor de startwaarden en de vertaling van modes
from smc_cleaner import TOP_N_RESULTS, MINIMUM_SIZE_MB, MINIMUM_AGE_DAYS, AGE_MODE, AGE_MODES

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                               QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QLabel, QSpacerItem, QSizePolicy,
                               QDialog, QFormLayout, QLineEdit, QComboBox,
                               QMenu) # <-- QMenu toegevoegd
from PySide6.QtGui import QFont, QAction # <-- QAction toegevoegd
from PySide6.QtCore import Qt, QSettings # <-- QSettings toegevoegd

# =======================================================
# INSTELINGEN DIALOOGVENSTER
# =======================================================

class SettingsDialog(QDialog):
    """Dialoogvenster voor het aanpassen van de scanfilters."""
    # FIX: Accepteert de QSettings instantie
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Instellingen Aanpassen")
        self.settings = settings
        self.layout = QFormLayout(self)
        
        # 1. Aantal Getoonde Items (TOP_N_RESULTS)
        # FIX: Haal de waarde op uit QSettings of de standaardwaarde
        self.top_n_input = QLineEdit(self)
        self.top_n_input.setText(str(self.settings.value('TOP_N_RESULTS', TOP_N_RESULTS, type=int)))
        self.layout.addRow("Max. Aantal Resultaten:", self.top_n_input)
        
        # 2. Minimum Ouderdom (MINIMUM_AGE_DAYS)
        self.age_input = QLineEdit(self)
        self.age_input.setText(str(self.settings.value('MINIMUM_AGE_DAYS', MINIMUM_AGE_DAYS, type=int)))
        self.layout.addRow("Minimale Ouderdom (Dagen):", self.age_input)
        
        # 3. Ouderdom Modus (AGE_MODE)
        self.mode_combo = QComboBox(self)
        
        # FIX: Gebruik AGE_MODES voor leesbare weergave
        mode_keys = list(AGE_MODES.keys())
        mode_values = list(AGE_MODES.values())
        self.mode_combo.addItems(mode_values) 
        
        current_mode_key = self.settings.value('AGE_MODE', AGE_MODE, type=str)
        if current_mode_key in mode_keys:
             current_mode_index = mode_keys.index(current_mode_key)
             self.mode_combo.setCurrentIndex(current_mode_index)

        self.layout.addRow("Tijdscriterium:", self.mode_combo)
        
        # 4. Minimum Grootte (MINIMUM_SIZE_MB)
        self.size_input = QLineEdit(self)
        self.size_input.setText(str(self.settings.value('MINIMUM_SIZE_MB', MINIMUM_SIZE_MB, type=int)))
        self.layout.addRow("Minimale Grootte (MB):", self.size_input)

        # OK/Annuleer Knoppen
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Opslaan en Sluiten")
        # De accept() zorgt ervoor dat QDialog.Accepted wordt geretourneerd
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Annuleren")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addRow(button_layout)
        
    def get_settings(self):
        """Geeft de ingevoerde en gevalideerde instellingen terug."""
        try:
            # FIX: Vertaal de leesbare tekst terug naar de logische sleutel
            selected_mode_key = list(AGE_MODES.keys())[self.mode_combo.currentIndex()]
            
            new_settings = {
                'TOP_N_RESULTS': int(self.top_n_input.text()),
                'MINIMUM_AGE_DAYS': int(self.age_input.text()),
                'AGE_MODE': selected_mode_key,
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
        self.setGeometry(100, 100, 1200, 800) # Groter venster

        # FIX: Implementeer QSettings voor persistentie
        self.settings = QSettings("SafeMacCleaner", "App")

        # Initialiseer dynamische instellingen met persistente/standaardwaarden
        self.top_n_results = self.settings.value('TOP_N_RESULTS', TOP_N_RESULTS, type=int)
        self.minimum_age_days = self.settings.value('MINIMUM_AGE_DAYS', MINIMUM_AGE_DAYS, type=int)
        self.age_mode = self.settings.value('AGE_MODE', AGE_MODE, type=str)
        self.minimum_size_mb = self.settings.value('MINIMUM_SIZE_MB', MINIMUM_SIZE_MB, type=int)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        
        self.ranked_results = [] 
        self.selected_size_mb = 0.0 # FIX: Voor directe feedback van geselecteerde grootte

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
        """Toont het dialoogvenster voor instellingen en slaat op."""
        
        # FIX: Geef de QSettings instantie door
        dialog = SettingsDialog(self, settings=self.settings)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            if new_settings:
                
                # FIX: Sla de nieuwe instellingen permanent op
                for key, value in new_settings.items():
                    self.settings.setValue(key, value)
                self.settings.sync() 

                # Update de dynamische attributen
                self.top_n_results = new_settings['TOP_N_RESULTS']
                self.minimum_age_days = new_settings['MINIMUM_AGE_DAYS']
                self.age_mode = new_settings['AGE_MODE']
                self.minimum_size_mb = new_settings['MINIMUM_SIZE_MB']
                
                QMessageBox.information(self, "Instellingen Opgeslagen", 
                                        "Nieuwe instellingen zijn opgeslagen. Voer een nieuwe scan uit om de resultaten bij te werken.")
                
                self.update_status_label()


    def update_status_label(self):
        """Update het filter label met de huidige dynamische instellingen."""
        
        # FIX: Gebruik de vertaalde AGE_MODE
        translated_age_mode = AGE_MODES.get(self.age_mode, self.age_mode)
        
        self.status_label.setText(
            f"Filter: >{self.minimum_size_mb}MB | >{self.minimum_age_days} dagen ({translated_age_mode}) | Max. {self.top_n_results} items getoond."
        )


    def update_selection_size_label(self):
        """Update de delete knop met de totale grootte van de geselecteerde items."""
        selected_size = 0.0
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) and self.table.item(row, 0).checkState() == Qt.Checked:
                # Kolom 2 bevat de grootte
                try:
                    # Vervang komma door punt voor betrouwbare float-conversie
                    size_text = self.table.item(row, 2).text().replace(',', '.') 
                    selected_size += float(size_text)
                except Exception:
                    continue
                    
        self.selected_size_mb = selected_size
        
        if selected_size > 0.0:
            # FIX: Toon de geselecteerde grootte op de knop
            self.delete_selected_button.setText(f"🗑️ Verplaats {self.selected_size_mb:.2f} MB naar Prullenbak")
            self.delete_selected_button.setEnabled(True)
            self.preview_button.setEnabled(True)
        else:
            self.delete_selected_button.setText("🗑️ Verplaats Geselecteerde naar Prullenbak")
            self.delete_selected_button.setEnabled(False)
            self.preview_button.setEnabled(False)

        # Update de Select All knop status
        checked_count = len(self.get_checked_rows())
        if checked_count > 0 and checked_count == self.table.rowCount():
            self.select_all_button.setText("❌ Deselecteer Alles")
        else:
            self.select_all_button.setText("✅ Selecteer Alles")


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
        # 6 kolommen: Selecteer, #, Grootte, Ouderdom, Type, Bestandspad
        self.table.setColumnCount(6)
        
        # FIX: "Bestand" gewijzigd naar "Bestandspad"
        self.table.setHorizontalHeaderLabels(["Selecteer", "#", "Grootte (MB)", "Ouderdom (Dagen)", "Type", "Bestandspad"])
        
        self.table.verticalHeader().setVisible(False) 
        
        # FIX: Kolom 5 (Bestandspad) neemt de resterende ruimte
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch) 
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Checkbox kolom
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Nummer kolom
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows) 
        self.table.setSelectionMode(QTableWidget.NoSelection)

        # FIX: Schakel Context Menu in
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu_request)
        
        # FIX: Koppel de stateChanged signal om de totale grootte bij te werken
        self.table.itemChanged.connect(self.handle_item_change)

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
        # De tekst wordt dynamisch bijgewerkt door update_selection_size_label
        self.delete_selected_button = QPushButton("🗑️ Verplaats Geselecteerde naar Prullenbak")
        self.delete_selected_button.clicked.connect(self.delete_selected)
        self.delete_selected_button.setEnabled(False) 
        # FIX: Rode achtergrond voor de delete actie
        self.delete_selected_button.setStyleSheet("background-color: #ffcccc; color: black; " + button_style) 
        button_layout.addWidget(self.delete_selected_button)
        
        # 3e. Leeg Prullenbak (Permanente Actie)
        self.empty_trash_button = QPushButton("🗑️ Leeg Prullenbak")
        self.empty_trash_button.clicked.connect(self.empty_trash)
        # FIX: Donkerdere rode achtergrond voor de permanente actie
        self.empty_trash_button.setStyleSheet("background-color: red; color: white; " + button_style) 
        button_layout.addWidget(self.empty_trash_button)
        
        self.main_layout.addLayout(button_layout)
        
        self.run_scan()
        
    def handle_item_change(self, item):
        """Wordt geactiveerd wanneer een item (checkbox) wordt gewijzigd."""
        if item.column() == 0:
            self.update_selection_size_label()

    def context_menu_request(self, pos):
        """Toont het contextmenu bij een rechtermuisklik in de tabel."""
        
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        
        menu = QMenu(self)
        
        # 1. Toon in Finder
        finder_action = QAction("🔍 Toon in Finder", self)
        # Lambda functie om de juiste rij door te geven
        finder_action.triggered.connect(lambda: self._preview_single_file(row))
        menu.addAction(finder_action)
        
        # 2. Exclusie Actie
        file_path = self.ranked_results[row]['path']
        
        # Bepaal of het al is uitgesloten
        exclusions = load_exclusion_list()
        if file_path in exclusions:
            exclude_action = QAction("✅ Verwijder van Uitsluitingslijst", self)
            exclude_action.triggered.connect(lambda: self.exclude_file_from_scan(row, False))
            menu.addAction(exclude_action)
        else:
            exclude_action = QAction("❌ Sluit dit Bestand uit van Scan", self)
            exclude_action.triggered.connect(lambda: self.exclude_file_from_scan(row, True))
            menu.addAction(exclude_action)
            
        menu.addSeparator()

        # 3. Verplaats naar Prullenbak
        delete_action = QAction("🗑️ Verplaats naar Prullenbak", self)
        delete_action.triggered.connect(lambda: self._delete_single_file(row))
        menu.addAction(delete_action)
        
        # Toon het menu
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _preview_single_file(self, row):
        """Helper om één bestand te openen via het contextmenu."""
        file_path = self.ranked_results[row]['path']
        subprocess.run(['open', '-R', file_path]) 

    def _delete_single_file(self, row):
        """Helper om één bestand naar de Prullenbak te verplaatsen via het contextmenu."""
        # De delete_selected methode wordt hergebruikt met een geforceerde index
        self.delete_selected(forced_indexes=[row])
        

    def exclude_file_from_scan(self, row, exclude=True):
        """Voegt/verwijdert het bestand toe/van de uitsluitingslijst."""
        file_path = self.ranked_results[row]['path']
        
        if exclude:
            if add_to_exclusion_list(file_path):
                QMessageBox.information(self, "Uitgesloten", f"'{os.path.basename(file_path)}' is toegevoegd aan de uitsluitingslijst.")
            else:
                QMessageBox.critical(self, "Fout", "Kon de uitsluitingslijst niet opslaan.")
        else:
            if remove_from_exclusion_list(file_path):
                 QMessageBox.information(self, "Hersteld", f"'{os.path.basename(file_path)}' is verwijderd van de uitsluitingslijst.")
            else:
                QMessageBox.critical(self, "Fout", "Kon de uitsluitingslijst niet opslaan.")
                
        # Herstart de scan om de gewijzigde resultaten weer te geven
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
        self.update_selection_size_label() # Reset de knoptekst
        QApplication.processEvents() 
        
        # GEBRUIK DE DYNAMISCHE INSTELINGEN VOOR DE SCAN
        all_candidates = validate_and_scan(
            self.top_n_results, 
            self.minimum_age_days, 
            self.age_mode, 
            self.minimum_size_mb
        )
        
        # Slicing voor het filteren op TOP_N_RESULTS (Max aantal)
        self.ranked_results = all_candidates[:self.top_n_results]

        self.display_results()
        
    def display_results(self):
        # Verbreek de connectie tijdelijk om te voorkomen dat update_selection_size_label bij elke rij wordt aangeroepen
        self.table.itemChanged.disconnect(self.handle_item_change) 

        self.update_disk_header() 
        
        if not self.ranked_results:
            self.status_label.setText("🎉 Scannen voltooid. Geen bestanden gevonden die voldoen aan de criteria.")
            self.delete_selected_button.setEnabled(False)
            self.select_all_button.setEnabled(False)
            self.preview_button.setEnabled(False)
            self.update_selection_size_label()
            
            # Herstel de connectie
            self.table.itemChanged.connect(self.handle_item_change) 
            return

        total_size = sum(item['size_mb'] for item in self.ranked_results)
        # FIX: Toon de gebruikte leeftijdscriterium
        translated_age_mode = AGE_MODES.get(self.age_mode, self.age_mode)
        self.status_label.setText(
            f"Totaal {len(self.ranked_results)} bestanden gevonden. Totale grootte: {total_size:.2f} MB. "
            f"Tijdscriterium: {translated_age_mode}. Vink rijen aan om te verwijderen."
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

            # Kolom 2: Grootte (rechts uitlijnen)
            size_item = QTableWidgetItem(f"{item['size_mb']:.1f}")
            size_item.setFlags(Qt.ItemIsEnabled)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # FIX: Rechts uitlijnen
            self.table.setItem(i, 2, size_item)
            
            # Kolom 3: Ouderdom (rechts uitlijnen)
            age_item = QTableWidgetItem(str(int(item['age_days'])))
            age_item.setFlags(Qt.ItemIsEnabled)
            age_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # FIX: Rechts uitlijnen
            self.table.setItem(i, 3, age_item)
            
            # Kolom 4: Type
            type_item = QTableWidgetItem(item['file_type'])
            type_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 4, type_item)
            
            # Kolom 5: Bestandspad (volledige pad)
            # FIX: Toon het volledige pad
            path_item = QTableWidgetItem(item['path'])
            path_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 5, path_item)
            
        self.table.resizeColumnsToContents()
        self.select_all_button.setEnabled(True)
        
        # Reset selectie status
        self.update_selection_size_label()

        # Herstel de connectie
        self.table.itemChanged.connect(self.handle_item_change) 
        
    def toggle_select_all(self):
        """Selecteert of deselecteert alle rijen op basis van de checkbox-status."""
        if self.table.rowCount() == 0:
            return
            
        # Verbreek de connectie tijdelijk om meervoudige events te voorkomen
        self.table.itemChanged.disconnect(self.handle_item_change) 
            
        is_checked = self.table.item(0, 0).checkState() == Qt.Checked
        new_state = Qt.Unchecked if is_checked else Qt.Checked
        
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(new_state)
            
        # Herstel de connectie en roep de update handmatig aan
        self.table.itemChanged.connect(self.handle_item_change) 
        self.update_selection_size_label() 


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
            # FIX: De paden hebben de 'file://' prefix niet meer nodig
            file_path = self.ranked_results[first_checked_row]['path'] 
            subprocess.run(['open', '-R', file_path]) 
        else:
            QMessageBox.warning(self, "Geen Selectie", "Vink een item aan om het in Finder te bekijken.")


    def delete_selected(self, forced_indexes=None):
        """Verplaatst alle aangevinkte items naar de Prullenbak."""
        
        indexes_to_delete = forced_indexes if forced_indexes is not None else self.get_checked_rows()

        if not indexes_to_delete:
            QMessageBox.warning(self, "Geen Selectie", "Vink de bestanden aan die u wilt verwijderen.")
            return
            
        # FIX: Gebruik de berekende geselecteerde grootte
        selected_size_display = self.selected_size_mb if forced_indexes is None else sum(self.ranked_results[i]['size_mb'] for i in indexes_to_delete)
            
        reply = QMessageBox.question(self, 'Bevestigen', 
                                     f"Weet u zeker dat u {len(indexes_to_delete)} bestanden ({selected_size_display:.2f} MB) naar de Prullenbak wilt verplaatsen?",
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
        
        # FIX: Duidelijkere waarschuwing
        reply = QMessageBox.question(self, 'Prullenbak Legen Bevestigen', 
                                     "⚠️ LET OP: Weet u zeker dat u DE HELE macOS Prullenbak permanent wilt legen? Alle items, inclusief de zojuist verplaatste bestanden, zullen permanent worden verwijderd! (Dit kan NIET ongedaan gemaakt worden!)",
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
        # FIX: Verbeterde Hoge DPI ondersteuning
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
    app = QApplication(sys.argv)
    window = SafeMacCleanerApp()
    window.show()
    sys.exit(app.exec())