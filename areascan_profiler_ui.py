#!/usr/bin/env python3
"""
AreaScan Profiler - GUI Tool
PyQt6 interface for testing inference models (similar to ops-counter UI)
"""
import sys
import time
from pathlib import Path
from PIL import Image
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QComboBox, QTextEdit, QFileDialog,
    QProgressBar, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QPalette, QDragEnterEvent, QDropEvent
from clients.inference_client import InferenceClient


class DropZoneLabel(QLabel):
    """Custom QLabel that handles drag and drop"""
    files_dropped = pyqtSignal(list)
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Visual feedback
            self.setStyleSheet('''
                QLabel {
                    border: 2px dashed #2980B9;
                    border-radius: 8px;
                    background-color: #D6EAF8;
                    color: #1F618D;
                    font-size: 12px;
                }
            ''')
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        # Restore original style
        self.setStyleSheet('''
            QLabel {
                border: 2px dashed #3498DB;
                border-radius: 8px;
                background-color: #EBF5FB;
                color: #2980B9;
                font-size: 12px;
            }
        ''')
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        # Restore original style
        self.setStyleSheet('''
            QLabel {
                border: 2px dashed #3498DB;
                border-radius: 8px;
                background-color: #EBF5FB;
                color: #2980B9;
                font-size: 12px;
            }
        ''')
        
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if Path(file_path).is_file():
                # Single file
                if self.is_image_file(file_path):
                    files.append(file_path)
            elif Path(file_path).is_dir():
                # Directory - get all images
                folder_files = self.get_images_from_folder(file_path)
                files.extend(folder_files)
        
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    @staticmethod
    def is_image_file(path):
        """Check if file is an image"""
        ext = Path(path).suffix.lower()
        return ext in ['.jpg', '.jpeg', '.png', '.bmp']
    
    @staticmethod
    def get_images_from_folder(folder_path):
        """Get all image files from folder"""
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            image_files.extend(Path(folder_path).glob(ext))
        return [str(f) for f in image_files]


class InferenceWorker(QThread):
    """Background worker for inference - keeps UI responsive"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, client, image_path, model_type, confidence):
        super().__init__()
        self.client = client
        self.image_path = image_path
        self.model_type = model_type
        self.confidence = confidence
    
    def run(self):
        try:
            # Load and resize image
            self.progress.emit('Loading image...')
            img = Image.open(self.image_path)
            img_resized = img.resize((2560, 2048))
            img_array = np.array(img_resized)
            
            # Handle different image formats
            if img_array.ndim == 2:  # Grayscale
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]
            
            image_bytes = img_array.tobytes()
            
            results = {
                'image_name': Path(self.image_path).name,
                'detections': None,
                'segmentations': None
            }
            
            # Run object detection
            if self.model_type in ['Object Detection', 'Both Models']:
                self.progress.emit('Running object detection...')
                start = time.time()
                result = self.client.detect_objects(
                    image_bytes, 2560, 2048,
                    confidence_threshold=self.confidence
                )
                duration = (time.time() - start) * 1000
                
                results['detections'] = {
                    'count': result['prediction_count'],
                    'latency_ms': duration,
                    'predictions': result['predictions']
                }
            
            # Run sheet segmentation
            if self.model_type in ['Sheet Segmentation', 'Both Models']:
                self.progress.emit('Running sheet segmentation...')
                start = time.time()
                result = self.client.segment_sheets(
                    image_bytes, 2560, 2048,
                    confidence_threshold=self.confidence
                )
                duration = (time.time() - start) * 1000
                
                results['segmentations'] = {
                    'count': result['prediction_count'],
                    'latency_ms': duration,
                    'predictions': result['predictions']
                }
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))


class AreaScanProfilerUI(QMainWindow):
    """AreaScan Profiler - Python/PyQt6 UI with improved visibility"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AreaScan Profiler - Independent Mode (Python)')
        self.setGeometry(100, 100, 1400, 800)
        
        # Set application-wide style
        self.set_app_style()
        
        self.client = None
        self.current_image_path = None
        self.loaded_images = []
        
        self.init_ui()
        self.init_client()
    
    def set_app_style(self):
        """Set modern, visible color scheme"""
        palette = QPalette()
        
        # Base colors - Light theme for better visibility
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 250))
        palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(33, 33, 33))
        
        QApplication.setPalette(palette)
    
    def init_ui(self):
        """Initialize UI - matches WPF layout with better colors"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #F0F0F5;")
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left sidebar (280px)
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Center image preview
        image_preview = self.create_image_preview()
        main_layout.addWidget(image_preview, stretch=1)
        
        # Right controls panel (380px)
        controls_panel = self.create_controls_panel()
        main_layout.addWidget(controls_panel)
    
    def create_sidebar(self):
        """Left sidebar - Upload section with working drag & drop"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background-color: #FFFFFF; padding: 15px; border-radius: 8px;")
        layout = QVBoxLayout()
        sidebar.setLayout(layout)
        
        # Title
        title = QLabel('Preview Model')
        title.setStyleSheet('font-size: 18px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;')
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Upload section
        upload_label = QLabel('Upload Image')
        upload_label.setStyleSheet('font-weight: bold; font-size: 13px; color: #34495E;')
        layout.addWidget(upload_label)
        
        layout.addSpacing(10)
        
        # Drop zone with custom widget
        self.drop_zone = DropZoneLabel('Drop file(s) or folder here\n\nor')
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setFixedHeight(120)
        self.drop_zone.setStyleSheet('''
            QLabel {
                border: 2px dashed #3498DB;
                border-radius: 8px;
                background-color: #EBF5FB;
                color: #2980B9;
                font-size: 12px;
            }
        ''')
        # Connect signal
        self.drop_zone.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(self.drop_zone)
        
        layout.addSpacing(10)
        
        # Select files button
        select_btn = QPushButton('Select File(s)')
        select_btn.setFixedHeight(35)
        select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498DB;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        ''')
        select_btn.clicked.connect(self.select_files)
        layout.addWidget(select_btn)
        
        layout.addSpacing(20)
        
        # Path input
        path_label = QLabel('Image URL or Path')
        path_label.setStyleSheet('font-weight: 600; font-size: 12px; color: #34495E;')
        layout.addWidget(path_label)
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText('Enter file path...')
        self.path_input.setFixedHeight(32)
        self.path_input.setStyleSheet('''
            QLineEdit {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #2C3E50;
            }
            QLineEdit:focus {
                border: 1px solid #3498DB;
            }
        ''')
        self.path_input.returnPressed.connect(self.load_from_path)
        layout.addWidget(self.path_input)
        
        # Model selection
        layout.addSpacing(20)
        model_label = QLabel('Model')
        model_label.setStyleSheet('font-weight: bold; font-size: 13px; color: #34495E;')
        layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            'Object Detection',
            'Sheet Segmentation',
            'Both Models'
        ])
        self.model_combo.setCurrentText('Both Models')
        self.model_combo.setFixedHeight(35)
        self.model_combo.setStyleSheet('''
            QComboBox {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #2C3E50;
            }
            QComboBox:hover {
                border: 1px solid #3498DB;
            }
            QComboBox::drop-down {
                border: none;
            }
        ''')
        layout.addWidget(self.model_combo)
        
        # Image info
        layout.addSpacing(20)
        self.image_info_label = QLabel('')
        self.image_info_label.setStyleSheet('font-size: 11px; color: #7F8C8D;')
        self.image_info_label.setWordWrap(True)
        layout.addWidget(self.image_info_label)
        
        layout.addStretch()
        
        return sidebar
    
    def on_files_dropped(self, files):
        """Handle files dropped onto drop zone"""
        if files:
            self.loaded_images = files
            self.show_preview(files[0])
            self.update_image_info()
            self.run_btn.setEnabled(True)
            
            # Show feedback
            if len(files) == 1:
                self.status_label.setText(f'✓ Loaded 1 image')
            else:
                self.status_label.setText(f'✓ Loaded {len(files)} images')
            self.status_label.setStyleSheet('font-size: 11px; color: #27AE60;')
    
    def create_image_preview(self):
        """Center image preview area"""
        preview_widget = QWidget()
        preview_widget.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        layout = QVBoxLayout()
        preview_widget.setLayout(layout)
        
        self.image_label = QLabel('No image selected\n\nSelect an image to begin profiling')
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet('''
            QLabel {
                background-color: #2C3E50;
                color: #95A5A6;
                font-size: 14px;
                border: 2px solid #34495E;
                border-radius: 8px;
                padding: 20px;
            }
        ''')
        self.image_label.setMinimumSize(400, 400)
        layout.addWidget(self.image_label)
        
        return preview_widget
    
    def create_controls_panel(self):
        """Right controls panel"""
        controls = QWidget()
        controls.setFixedWidth(380)
        controls.setStyleSheet("background-color: #FFFFFF; padding: 15px; border-radius: 8px;")
        layout = QVBoxLayout()
        controls.setLayout(layout)
        
        # Confidence threshold
        conf_label = QLabel('Confidence Threshold:')
        conf_label.setStyleSheet('font-weight: 600; font-size: 12px; color: #34495E;')
        layout.addWidget(conf_label)
        
        slider_layout = QHBoxLayout()
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(50)
        self.confidence_slider.setStyleSheet('''
            QSlider::groove:horizontal {
                height: 6px;
                background: #ECF0F1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498DB;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        ''')
        self.confidence_value_label = QLabel('50%')
        self.confidence_value_label.setFixedWidth(45)
        self.confidence_value_label.setStyleSheet('font-weight: bold; color: #2C3E50; font-size: 13px;')
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_value_label.setText(f'{v}%')
        )
        slider_layout.addWidget(self.confidence_slider)
        slider_layout.addWidget(self.confidence_value_label)
        layout.addLayout(slider_layout)
        
        layout.addSpacing(15)
        
        # Overlap threshold
        overlap_label = QLabel('Overlap Threshold:')
        overlap_label.setStyleSheet('font-weight: 600; font-size: 12px; color: #34495E;')
        layout.addWidget(overlap_label)
        
        overlap_layout = QHBoxLayout()
        self.overlap_slider = QSlider(Qt.Orientation.Horizontal)
        self.overlap_slider.setRange(0, 100)
        self.overlap_slider.setValue(50)
        self.overlap_slider.setStyleSheet('''
            QSlider::groove:horizontal {
                height: 6px;
                background: #ECF0F1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498DB;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        ''')
        self.overlap_value_label = QLabel('50%')
        self.overlap_value_label.setFixedWidth(45)
        self.overlap_value_label.setStyleSheet('font-weight: bold; color: #2C3E50; font-size: 13px;')
        self.overlap_slider.valueChanged.connect(
            lambda v: self.overlap_value_label.setText(f'{v}%')
        )
        overlap_layout.addWidget(self.overlap_slider)
        overlap_layout.addWidget(self.overlap_value_label)
        layout.addLayout(overlap_layout)
        
        layout.addSpacing(15)
        
        # Opacity threshold
        opacity_label = QLabel('Opacity Threshold:')
        opacity_label.setStyleSheet('font-weight: 600; font-size: 12px; color: #34495E;')
        layout.addWidget(opacity_label)
        
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(75)
        self.opacity_slider.setStyleSheet('''
            QSlider::groove:horizontal {
                height: 6px;
                background: #ECF0F1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498DB;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        ''')
        self.opacity_value_label = QLabel('75%')
        self.opacity_value_label.setFixedWidth(45)
        self.opacity_value_label.setStyleSheet('font-weight: bold; color: #2C3E50; font-size: 13px;')
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_value_label.setText(f'{v}%')
        )
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value_label)
        layout.addLayout(opacity_layout)
        
        layout.addSpacing(30)
        
        # Run inference button
        self.run_btn = QPushButton('▶  Run Inference')
        self.run_btn.setFixedHeight(45)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setStyleSheet('''
            QPushButton {
                background-color: #9B59B6;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
                color: #7F8C8D;
            }
        ''')
        self.run_btn.clicked.connect(self.run_inference)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)
        
        layout.addSpacing(15)
        
        # Predictions section
        pred_label = QLabel('Predictions')
        pred_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #2C3E50;')
        layout.addWidget(pred_label)
        
        self.predictions_text = QTextEdit()
        self.predictions_text.setReadOnly(True)
        self.predictions_text.setStyleSheet('''
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 10px;
                color: #2C3E50;
            }
        ''')
        self.predictions_text.setFixedHeight(300)
        layout.addWidget(self.predictions_text)
        
        # Status and progress
        layout.addSpacing(10)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                border: none;
                background-color: #ECF0F1;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
                border-radius: 2px;
            }
        ''')
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel('Ready')
        self.status_label.setStyleSheet('font-size: 11px; color: #7F8C8D; margin-top: 5px;')
        layout.addWidget(self.status_label)
        
        return controls
    
    def init_client(self):
        """Initialize gRPC client"""
        try:
            self.client = InferenceClient()
            if self.client.check_health():
                self.status_label.setText(
                    f'✓ Connected to AreaScanInference on {self.client.address}'
                )
                self.status_label.setStyleSheet('font-size: 11px; color: #27AE60;')
            else:
                self.status_label.setText('⚠ Service not responding')
                self.status_label.setStyleSheet('font-size: 11px; color: #E67E22;')
        except Exception as e:
            QMessageBox.warning(
                self,
                'Connection Error',
                f'Failed to connect to AreaScanInference service:\n{e}\n\n'
                'Make sure the service is running.'
            )
            self.status_label.setText('✗ Connection failed')
            self.status_label.setStyleSheet('font-size: 11px; color: #E74C3C;')
    
    def select_files(self):
        """Select image files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Images',
            '',
            'Images (*.png *.jpg *.jpeg *.bmp)'
        )
        
        if files:
            self.loaded_images = files
            self.show_preview(files[0])
            self.update_image_info()
            self.run_btn.setEnabled(True)
    
    def load_from_path(self):
        """Load image from path input"""
        path = self.path_input.text().strip()
        if path and Path(path).exists():
            self.loaded_images = [path]
            self.show_preview(path)
            self.update_image_info()
            self.run_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, 'Invalid Path', 'The specified file does not exist.')
    
    def show_preview(self, image_path):
        """Show image preview"""
        self.current_image_path = image_path
        try:
            pixmap = QPixmap(image_path)
            
            # Scale to fit while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled)
        except Exception as e:
            self.image_label.setText(f'Error loading image:\n{e}')
    
    def update_image_info(self):
        """Update image info label"""
        if not self.loaded_images:
            self.image_info_label.setText('')
        elif len(self.loaded_images) == 1:
            path = Path(self.loaded_images[0])
            size_kb = path.stat().st_size // 1024
            self.image_info_label.setText(
                f'File: {path.name}\nSize: {size_kb:,} KB'
            )
        else:
            self.image_info_label.setText(
                f'{len(self.loaded_images)} images loaded'
            )
    
    def run_inference(self):
        """Run inference on current image"""
        if not self.current_image_path:
            return
        
        # Disable UI during inference
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Get parameters
        model_type = self.model_combo.currentText()
        confidence = self.confidence_slider.value() / 100.0
        
        # Run in background thread
        self.worker = InferenceWorker(
            self.client,
            self.current_image_path,
            model_type,
            confidence
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_inference_complete)
        self.worker.error.connect(self.on_inference_error)
        self.worker.start()
    
    def on_progress(self, message):
        """Update progress"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet('font-size: 11px; color: #3498DB;')
    
    def on_inference_complete(self, results):
        """Handle inference completion"""
        # Format results with better readability
        output = []
        output.append('═' * 65)
        output.append('    AREASCAN PROFILER - INDEPENDENT MODE')
        output.append(f'    Image: {results["image_name"]}')
        output.append('═' * 65)
        output.append('')
        
        if results['detections']:
            det = results['detections']
            output.append('[Object Detection - Default Model]')
            output.append(f'  Found: {det["count"]} objects')
            output.append(f'  Latency: {det["latency_ms"]:.2f} ms')
            output.append('')
            
            if det['predictions']:
                for i, pred in enumerate(det['predictions'][:10], 1):
                    output.append(
                        f'  {i:2d}. {pred["class"]:<18} '
                        f'confidence: {pred["confidence"]:6.2%}  '
                        f'center: ({pred["center_x"]:4.0f}, {pred["center_y"]:4.0f})'
                    )
            else:
                output.append('  No predictions above confidence threshold')
            output.append('')
        
        if results['segmentations']:
            seg = results['segmentations']
            output.append('[Sheet Segmentation - Default Model]')
            output.append(f'  Found: {seg["count"]} segments')
            output.append(f'  Latency: {seg["latency_ms"]:.2f} ms')
            output.append('')
            
            if seg['predictions']:
                for i, pred in enumerate(seg['predictions'][:10], 1):
                    poly_count = len(pred.get('polygon_points', []))
                    output.append(
                        f'  {i:2d}. {pred["class"]:<18} '
                        f'confidence: {pred["confidence"]:6.2%}  '
                        f'polygon: {poly_count} points'
                    )
            else:
                output.append('  No predictions above confidence threshold')
            output.append('')
        
        output.append('═' * 65)
        output.append('    PROFILING COMPLETED')
        output.append('═' * 65)
        
        self.predictions_text.setPlainText('\n'.join(output))
        
        # Re-enable UI
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText('✓ Profiling complete')
        self.status_label.setStyleSheet('font-size: 11px; color: #27AE60;')
    
    def on_inference_error(self, error):
        """Handle inference error"""
        QMessageBox.critical(
            self,
            'Inference Error',
            f'Error during inference:\n{error}'
        )
        
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText('✗ Error occurred')
        self.status_label.setStyleSheet('font-size: 11px; color: #E74C3C;')


def main():
    app = QApplication(sys.argv)
    
    # Set application style to Fusion for consistent look
    app.setStyle('Fusion')
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = AreaScanProfilerUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()