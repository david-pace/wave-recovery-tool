import sys
from argparse import Namespace
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QMessageBox,
    QProgressBar,
    QHBoxLayout,
)
from PyQt5.QtCore import QThread, pyqtSignal
import io
from contextlib import redirect_stdout
from waveheaderprocessor import WaveHeaderProcessor
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QIntValidator

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str, bool)

    def __init__(self, args):
        super().__init__()
        self.args = args

    def run(self):
        try:
            with io.StringIO() as buf, redirect_stdout(buf):
                processor = WaveHeaderProcessor()
                total_files = processor.repair_audio_file_headers(
                    self.args.source_path,
                    self.args.destination_path,
                    self.args.sample_rate,
                    self.args.bits_per_sample,
                    self.args.channels,
                    self.args.verbose,
                    self.args.force,
                    self.args.application,
                    self.args.offset,
                    self.args.end_offset,
                )
                output = buf.getvalue()

            self.update_progress.emit(total_files)
            self.update_log.emit(output, False)

        except Exception as e:
            error_message = f'Error: {str(e)}'
            self.update_log.emit(error_message, True)
            QMessageBox.critical(self.args.gui, 'Error', error_message)
        finally:
            self.args.gui.restore_button.setDisabled(False)

class WaveRecoveryToolGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize a list of worker threads
        self.worker_threads = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Wave Recovery Tool GUI')
        self.setGeometry(100, 100, 200, 200)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.initRestoreForm()

    def initRestoreForm(self):
        form_layout = QFormLayout()

        source_path_layout = QHBoxLayout()
        self.source_path_label = QLabel('Source Path:')
        self.source_path_text = QTextEdit()
        self.source_path_text.setPlaceholderText("Enter source path")
        self.source_path_text.setMaximumHeight(30)
        self.source_path_text.setAcceptRichText(False)
        self.browse_source_button = QPushButton('Browse')
        self.browse_source_button.setFixedWidth(80)
        self.browse_source_button.clicked.connect(self.browse_source)
        source_path_layout.addWidget(self.source_path_text)
        source_path_layout.addWidget(self.browse_source_button)

        dest_path_layout = QHBoxLayout()
        self.dest_path_label = QLabel('Destination Path:')
        self.dest_path_text = QTextEdit()
        self.dest_path_text.setPlaceholderText("Enter destination path")
        self.dest_path_text.setMaximumHeight(30)
        self.dest_path_text.setAcceptRichText(False)
        self.browse_dest_button = QPushButton('Browse')
        self.browse_dest_button.setFixedWidth(80)
        self.browse_dest_button.clicked.connect(self.browse_dest)
        dest_path_layout.addWidget(self.dest_path_text)
        dest_path_layout.addWidget(self.browse_dest_button)

        self.sample_rate_label = QLabel('Sample Rate:')
        self.sample_rate_combobox = QComboBox()
        self.sample_rate_combobox.setEditable(True)

        # Add predefined sample rates to the combobox
        sample_rates = ['8000', '44100', '48000', '88200', '96000', '192000']
        self.sample_rate_combobox.addItems(sample_rates)

        # Set the default/pre-selected sample rate
        default_sample_rate = '44100'
        self.sample_rate_combobox.setCurrentText(default_sample_rate)

        # Set validator to allow only numeric input
        validator = QIntValidator()
        self.sample_rate_combobox.setValidator(validator)

        self.sample_rate_label = QLabel('Sample Rate:')
        self.sample_rate_spinbox = QSpinBox()
        self.sample_rate_spinbox.setMinimum(1)
        self.sample_rate_spinbox.setMaximum(999999)
        self.sample_rate_spinbox.setValue(44100)

        self.bits_per_sample_label = QLabel('Bits Per Sample:')
        self.bits_per_sample_combobox = QComboBox()
        self.bits_per_sample_combobox.setEditable(True)

        # Add predefined bits per sample to the combobox
        bits_per_sample_values = ['8', '16', '24', '32']
        self.bits_per_sample_combobox.addItems(bits_per_sample_values)

        # Set the default/pre-selected bits per sample
        default_bits_per_sample = '16'
        self.bits_per_sample_combobox.setCurrentText(default_bits_per_sample)

        # Set validator to allow only numeric input
        validator = QIntValidator()
        self.bits_per_sample_combobox.setValidator(validator)

        self.channels_label = QLabel('Channels:')
        self.channels_combobox = QComboBox()
        self.channels_combobox.setEditable(True)

        # Add predefined channel values to the combobox
        channel_values = ['1', '2']
        channel_labels = ['1 (Mono)', '2 (Stereo)']
        self.channels_combobox.addItems(channel_labels)

        # Set the default/pre-selected number of channels
        default_channels = '1'
        self.channels_combobox.setCurrentText(default_channels)

        # Set validator to allow only numeric input
        validator = QIntValidator()
        self.channels_combobox.setValidator(validator)

        self.force_checkbox = QCheckBox('Force Restoration (No Error Check)')

        self.application_label = QLabel('Application:')
        self.application_combo = QComboBox()
        self.application_combo.addItem('logic')
        self.application_combo.addItem('live')
        self.application_combo.addItem('djvu')

        self.use_offset_checkbox = QCheckBox('Specify Custom Offsets')
        self.use_offset_checkbox.stateChanged.connect(self.toggle_offset_fields)

        self.offset_label = QLabel('Start Offset:')
        self.offset_spinbox = QSpinBox()
        self.offset_spinbox.setMinimum(-999999)
        self.offset_spinbox.setMaximum(999999)

        self.end_offset_label = QLabel('End Offset:')
        self.end_offset_spinbox = QSpinBox()
        self.end_offset_spinbox.setMinimum(-999999)
        self.end_offset_spinbox.setMaximum(999999)

        self.version_checkbox = QCheckBox('Version (-v)')
        self.verbose_checkbox = QCheckBox('Verbose (-V)')

        form_layout.addRow(self.source_path_label, source_path_layout)
        form_layout.addRow(self.dest_path_label, dest_path_layout)
        form_layout.addRow(self.sample_rate_label, self.sample_rate_spinbox)
        form_layout.addRow(self.bits_per_sample_label, self.bits_per_sample_combobox)
        form_layout.addRow(self.channels_label, self.channels_combobox)
        form_layout.addWidget(self.force_checkbox)
        form_layout.addRow(self.application_label, self.application_combo)
        form_layout.addRow(self.use_offset_checkbox)
        form_layout.addRow(self.offset_label, self.offset_spinbox)
        form_layout.addRow(self.end_offset_label, self.end_offset_spinbox)
        form_layout.addWidget(self.version_checkbox)
        form_layout.addWidget(self.verbose_checkbox)

        # Apply styles to buttons and "Browse" buttons
        button_style = '''
            QPushButton, QTextEdit {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }

            QPushButton:hover, QTextEdit:hover {
                background-color: #005F99;
            }
        '''

        self.restore_button = QPushButton('Restore')
        self.restore_button.clicked.connect(self.restore)
        self.restore_button.setStyleSheet(button_style)  # Apply the style to the button
        form_layout.addRow(self.restore_button)

        self.browse_source_button.setStyleSheet(button_style)  # Apply the style to the "Browse" button
        self.browse_dest_button.setStyleSheet(button_style)  # Apply the style to the "Browse" button

        self.cancel_all_button = QPushButton('Cancel All')
        self.cancel_all_button.clicked.connect(self.cancel_all_threads)
        self.cancel_all_button.setStyleSheet(button_style)  # Apply the style to the button
        form_layout.addRow(self.cancel_all_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; } QProgressBar { text-align: center; color: white; border-radius: 10px; }")
        form_layout.addRow(self.progress_bar)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        form_layout.addRow(self.log_box)

        self.central_widget.setLayout(form_layout)

    def toggle_offset_fields(self):
        enabled = self.use_offset_checkbox.isChecked()
        self.offset_label.setEnabled(enabled)
        self.offset_spinbox.setEnabled(enabled)
        self.end_offset_label.setEnabled(enabled)
        self.end_offset_spinbox.setEnabled(enabled)

    def browse_source(self):
        source_path = QFileDialog.getExistingDirectory(self, 'Select Source Directory')
        self.source_path_text.setPlainText(source_path)

    def browse_dest(self):
        dest_path = QFileDialog.getExistingDirectory(self, 'Select Destination Directory')
        self.dest_path_text.setPlainText(dest_path)

    def restore(self):
        self.restore_button.setDisabled(True)

        source_path = self.source_path_text.toPlainText()
        dest_path = self.dest_path_text.toPlainText()
        if not source_path:
            QMessageBox.critical(self, "Error", "Please select a source file or folder before starting the recovery.")
            self.restore_button.setDisabled(False)
            return
            if not dest_path:
                QMessageBox.critical(self, "Error", "Please select a destination file or folder before starting the recovery.")
                self.restore_button.setDisabled(False)
                return

        sample_rate = self.sample_rate_spinbox.value()
        bits_per_sample = int(self.bits_per_sample_combobox.currentText())
        channels = int(self.channels_combobox.currentText().split()[0])
        force = self.force_checkbox.isChecked()
        application = self.application_combo.currentText()
        offset = self.offset_spinbox.value() if self.use_offset_checkbox.isChecked() else None
        end_offset = self.end_offset_spinbox.value() if self.use_offset_checkbox.isChecked() else None
        version = self.version_checkbox.isChecked()
        verbose = self.verbose_checkbox.isChecked()

        args = Namespace(
            restore=True,
            source_path=source_path,
            destination_path=dest_path,
            verbose=verbose,
            application=application,
            offset=offset,
            end_offset=end_offset,
            sample_rate=sample_rate,
            bits_per_sample=bits_per_sample,
            channels=channels,
            force=force,
            version=version,
            gui=self
        )

        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('%p%')

        worker_thread = WorkerThread(args)
        worker_thread.update_progress.connect(self.update_progress)
        worker_thread.update_log.connect(self.update_log)
        worker_thread.finished.connect(self.restore_completed)

        self.worker_threads.append(worker_thread)

        worker_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, log_message, is_error=False):
        log_color = 'green' if not is_error else 'red'
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(log_color))

        text_cursor = self.log_box.textCursor()
        text_cursor.mergeCharFormat(text_format)

        if self.verbose_checkbox.isChecked():
            self.log_box.insertPlainText(log_message)
            self.log_box.moveCursor(QTextCursor.End)
            self.log_box.ensureCursorVisible()

    def restore_completed(self):
        self.restore_button.setDisabled(False)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat('100%')

        sender_thread = self.sender()
        self.worker_threads.remove(sender_thread)

    def cancel_all_threads(self):
        for thread in self.worker_threads:
            thread.quit()
            thread.wait()

def main():
    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")  # Apply Fusion style for rounded corners
    window = WaveRecoveryToolGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
