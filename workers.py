from PySide6.QtCore import QThread, Signal

import smc_cleaner as engine


class ScanWorker(QThread):
    completed = Signal(list, list, object)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, directories, settings):
        super().__init__()
        self.directories = directories
        self.settings = settings
        self.is_running = True

    def run(self):
        try:
            results, errors, stats = engine.scan_disk(
                directories=self.directories,
                min_size_mb=self.settings["size"],
                min_age_days=self.settings["age"],
                age_mode=self.settings["mode"],
                top_n=self.settings["top_n"],
                progress_callback=self.progress.emit,
                should_stop=lambda: not self.is_running,
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        if self.is_running:
            self.completed.emit(results, errors, stats)
        else:
            self.cancelled.emit()

    def stop(self):
        self.is_running = False

    progress = Signal(str)


class DeleteWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, items):
        super().__init__()
        self.items = items

    def run(self):
        try:
            self.completed.emit(engine.delete_files(self.items))
        except Exception as error:
            self.failed.emit(str(error))
