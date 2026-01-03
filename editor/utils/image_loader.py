# utils/image_loader.py
import requests
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QLabel, QListWidgetItem
import config

IMAGE_CACHE = {}

class ImageWorker(QThread):
    finished = pyqtSignal(QPixmap)

    def __init__(self, item_name):
        super().__init__()
        self.item_name = item_name

    def run(self):
        if self.item_name in IMAGE_CACHE:
            self.finished.emit(IMAGE_CACHE[self.item_name])
            return

        # Zkusíme různé varianty URL (s příponou i bez)
        urls_to_try = [
            f"{config.IMAGE_BASE_URL}/{self.item_name}.png",
            f"{config.IMAGE_BASE_URL}/{self.item_name}",
        ]

        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        IMAGE_CACHE[self.item_name] = pixmap
                        self.finished.emit(pixmap)
                        return
            except:
                pass
        
        self.finished.emit(QPixmap()) # Prázdný, pokud selže

class ImageLoader:
    
    @staticmethod
    def load_image(item_name, target_label: QLabel, max_size=100):
        target_label.clear()
        target_label.setText("...")
        
        worker = ImageWorker(item_name)
        
        def on_loaded(pixmap: QPixmap):
            if not pixmap.isNull():
                scaled = pixmap.scaled(max_size, max_size, 1, 1)
                target_label.setPixmap(scaled)
                target_label.setText("")
            else:
                target_label.setText("❌")
        
        worker.finished.connect(on_loaded)
        target_label._worker = worker 
        worker.start()

    @staticmethod
    def load_icon_to_item(item_name, item):
        """Načte obrázek a nastaví ho jako ikonu pro QListWidgetItem nebo QTableWidgetItem."""
        worker = ImageWorker(item_name)
        
        def on_loaded(pixmap: QPixmap):
            if not pixmap.isNull():
                icon = QIcon(pixmap)
                item.setIcon(icon)
        
        worker.finished.connect(on_loaded)
        # Uložíme referenci na workera do itemu (hack přes setData nebo dynamický atribut není u QListItem safe, 
        # ale QThread se sám smaže po skončení, pokud není parentován, v PyQt to většinou stačí držet v lokální scope, 
        # ale tady to riskujeme. Pro stabilitu v produkci by to chtělo silnější manager, ale pro editor stačí:)
        item._img_worker = worker 
        worker.start()