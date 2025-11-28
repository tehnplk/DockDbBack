import sys
import os
import json
import datetime
import subprocess
import shutil

from PyQt6 import QtWidgets, QtCore

from DockDbBack_ui import Ui_MainWindow


def get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path() -> str:
    return os.path.join(get_base_dir(), "config.json")


BASE_DIR = get_base_dir()


def load_config() -> dict:
    config_path = get_config_path()

    if not os.path.exists(config_path):
        # ถ้ารันแบบ onefile และมี default config bundle อยู่ ให้ copy ออกมาวางข้าง exe
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            bundled_path = os.path.join(sys._MEIPASS, "config.json")
            if os.path.exists(bundled_path):
                try:
                    shutil.copyfile(bundled_path, config_path)
                except OSError:
                    pass

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def run_cmd(cmd, log_callback):
    msg = "Running: " + " ".join(cmd)
    print(msg)
    if log_callback:
        log_callback(msg)
    creationflags = 0
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(cmd, shell=False, creationflags=creationflags)
    if result.returncode != 0:
        err = f"Command failed with code {result.returncode}"
        print(err)
        if log_callback:
            log_callback(err)
        raise RuntimeError(err)


def do_backup(db_type: str, config: dict, dump_path: str, log_callback=None):
    section = config.get(db_type)
    if not section:
        raise RuntimeError(f"Config not found for db_type={db_type}")

    src = section["source"]
    container = src["container"]
    db_name = src["db_name"]
    db_user = src["db_user"]
    db_password = src["db_password"]

    container_dump_path = "/backup/" + os.path.basename(dump_path)

    # สร้างโฟลเดอร์ /backup ใน container (ถ้ายังไม่มี)
    run_cmd(["docker", "exec", container, "mkdir", "-p", "/backup"], log_callback)

    if db_type.lower() == "postgres":
        # pg_dump ใน container
        run_cmd([
            "docker", "exec", "-e", f"PGPASSWORD={db_password}", container,
            "pg_dump", "-U", db_user, "-d", db_name, "-Fc", "-C", "-f", container_dump_path,
        ], log_callback)

        # ดึงไฟล์ออกมาที่ Windows host
        run_cmd([
            "docker", "cp", f"{container}:{container_dump_path}", dump_path
        ], log_callback)

    elif db_type.lower() == "mysql":
        # mysqldump ใน container (ใช้ sh -c เพื่อ redirect ออกไฟล์)
        dump_cmd = f"mysqldump -u {db_user} {db_name} > {container_dump_path}"
        run_cmd([
            "docker", "exec", "-e", f"MYSQL_PWD={db_password}", container,
            "sh", "-c", dump_cmd,
        ], log_callback)

        run_cmd([
            "docker", "cp", f"{container}:{container_dump_path}", dump_path
        ], log_callback)
    else:
        raise RuntimeError(f"Unsupported db_type: {db_type}")

    msg = f"Backup completed to: {dump_path}"
    print(msg)
    if log_callback:
        log_callback(msg)


def do_restore(db_type: str, config: dict, dump_path: str, log_callback=None):
    section = config.get(db_type)
    if not section:
        raise RuntimeError(f"Config not found for db_type={db_type}")

    tgt = section["target"]
    container = tgt["container"]
    db_name = tgt["db_name"]
    db_user = tgt["db_user"]
    db_password = tgt["db_password"]

    file_name = os.path.basename(dump_path)
    container_dump_path = f"/backup/{file_name}"

    # สร้างโฟลเดอร์ /backup ใน container ปลายทาง (ถ้ายังไม่มี)
    run_cmd(["docker", "exec", container, "mkdir", "-p", "/backup"], log_callback)

    # copy ไฟล์จาก Windows host เข้า container
    run_cmd(["docker", "cp", dump_path, f"{container}:{container_dump_path}"], log_callback)

    if db_type.lower() == "postgres":
        # pg_restore ทับฐาน db_name โดยไม่ตั้ง owner จาก dump
        run_cmd([
            "docker", "exec", "-e", f"PGPASSWORD={db_password}", container,
            "pg_restore", "-U", db_user,
            "-d", db_name,
            "--clean", "--if-exists", "--no-owner",
            container_dump_path,
        ], log_callback)

    elif db_type.lower() == "mysql":
        # mysql restore ภายใน container ด้วย sh -c และ redirect
        restore_cmd = f"mysql -u {db_user} {db_name} < {container_dump_path}"
        run_cmd([
            "docker", "exec", "-e", f"MYSQL_PWD={db_password}", container,
            "sh", "-c", restore_cmd,
        ], log_callback)
    else:
        raise RuntimeError(f"Unsupported db_type: {db_type}")

    msg = f"Restore completed into DB: {db_name}"
    print(msg)
    if log_callback:
        log_callback(msg)


class Worker(QtCore.QThread):
    log_signal = QtCore.pyqtSignal(str)
    finished_signal = QtCore.pyqtSignal(bool, str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def log(self, text: str):
        self.log_signal.emit(text)

    def run(self):
        try:
            self.kwargs["log_callback"] = self.log
            self.fn(*self.args, **self.kwargs)
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class ConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent, config: dict):
        super().__init__(parent)
        self.setWindowTitle("Config")
        self.config = config

        layout = QtWidgets.QVBoxLayout(self)

        top_layout = QtWidgets.QHBoxLayout()
        label_db = QtWidgets.QLabel("Database type:", parent=self)
        self.combo_db_type = QtWidgets.QComboBox(parent=self)
        for key in sorted(self.config.keys()):
            self.combo_db_type.addItem(key)
        top_layout.addWidget(label_db)
        top_layout.addWidget(self.combo_db_type)
        layout.addLayout(top_layout)

        form = QtWidgets.QFormLayout()

        self.edit_src_container = QtWidgets.QLineEdit(parent=self)
        self.edit_src_db_name = QtWidgets.QLineEdit(parent=self)
        self.edit_src_db_user = QtWidgets.QLineEdit(parent=self)
        self.edit_src_db_password = QtWidgets.QLineEdit(parent=self)
        self.edit_src_db_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.edit_tgt_container = QtWidgets.QLineEdit(parent=self)
        self.edit_tgt_db_name = QtWidgets.QLineEdit(parent=self)
        self.edit_tgt_db_user = QtWidgets.QLineEdit(parent=self)
        self.edit_tgt_db_password = QtWidgets.QLineEdit(parent=self)
        self.edit_tgt_db_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        form.addRow("Source container:", self.edit_src_container)
        form.addRow("Source db_name:", self.edit_src_db_name)
        form.addRow("Source db_user:", self.edit_src_db_user)
        form.addRow("Source db_password:", self.edit_src_db_password)
        form.addRow("Target container:", self.edit_tgt_container)
        form.addRow("Target db_name:", self.edit_tgt_db_name)
        form.addRow("Target db_user:", self.edit_tgt_db_user)
        form.addRow("Target db_password:", self.edit_tgt_db_password)

        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.combo_db_type.currentTextChanged.connect(self._load_from_config)
        if self.combo_db_type.count() > 0:
            self._load_from_config(self.combo_db_type.currentText())

    def _load_from_config(self, db_type: str):
        section = self.config.get(db_type.lower()) or self.config.get(db_type) or {}
        src = section.get("source", {})
        tgt = section.get("target", {})

        self.edit_src_container.setText(src.get("container", ""))
        self.edit_src_db_name.setText(src.get("db_name", ""))
        self.edit_src_db_user.setText(src.get("db_user", ""))
        self.edit_src_db_password.setText(src.get("db_password", ""))

        self.edit_tgt_container.setText(tgt.get("container", ""))
        self.edit_tgt_db_name.setText(tgt.get("db_name", ""))
        self.edit_tgt_db_user.setText(tgt.get("db_user", ""))
        self.edit_tgt_db_password.setText(tgt.get("db_password", ""))

    def apply_to_config(self):
        db_key = self.combo_db_type.currentText()
        key_lower = db_key.lower()
        if key_lower in self.config:
            db_key = key_lower

        section = self.config.setdefault(db_key, {})
        src = section.setdefault("source", {})
        tgt = section.setdefault("target", {})

        src["container"] = self.edit_src_container.text().strip()
        src["db_name"] = self.edit_src_db_name.text().strip()
        src["db_user"] = self.edit_src_db_user.text().strip()
        src["db_password"] = self.edit_src_db_password.text().strip()

        tgt["container"] = self.edit_tgt_container.text().strip()
        tgt["db_name"] = self.edit_tgt_db_name.text().strip()
        tgt["db_user"] = self.edit_tgt_db_user.text().strip()
        tgt["db_password"] = self.edit_tgt_db_password.text().strip()


class MainWindow(QtWidgets.QWidget, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.config = load_config()
        self.worker: Worker | None = None
        self.current_operation: str | None = None

        # ตั้งค่า label แสดง config สำหรับค่าเริ่มต้น (Postgres)
        self.update_info_labels("Postgres")

        # ค่าเริ่มต้นของ path backup/restore
        default_name = datetime.datetime.now().strftime("back_%Y%m%d%H%M%S.dump")
        self.lineEditBackupPath.setText(os.path.join(BASE_DIR, default_name))
        self.lineEditRestorePath.setText(os.path.join(BASE_DIR, "back_*.dump"))

        # ผูก signal/slot
        self.btnBackupBrowse.clicked.connect(self.browse_backup_path)
        self.btnBackupRun.clicked.connect(self.run_backup)
        self.btnRestoreBrowse.clicked.connect(self.browse_restore_path)
        self.btnRestoreRun.clicked.connect(self.run_restore)
        self.comboDbType.currentTextChanged.connect(self.on_db_type_changed)
        self.btnConfig.clicked.connect(self.open_config_dialog)

        # เก็บปุ่มไว้ใช้ enable/disable ระหว่างทำงาน
        self.backup_run_btn = self.btnBackupRun
        self.restore_run_btn = self.btnRestoreRun

    def current_db_type(self) -> str:
        return self.comboDbType.currentText().strip().lower() or "postgres"

    def update_info_labels(self, db_type_text: str | None = None):
        db_type = (db_type_text or self.comboDbType.currentText() or "Postgres").lower()
        section = self.config.get(db_type)
        if not section:
            self.labelSrcInfo.setText(f"source: (no config for {db_type})")
            self.labelTgtInfo.setText(f"target: (no config for {db_type})")
            return
        src = section["source"]
        tgt = section["target"]
        self.labelSrcInfo.setText(
            f"source[{db_type}]: container={src['container']}; db={src['db_name']}; user={src['db_user']}; pass={src['db_password']}"
        )
        self.labelTgtInfo.setText(
            f"target[{db_type}]: container={tgt['container']}; db={tgt['db_name']}; user={tgt['db_user']}; pass={tgt['db_password']}"
        )

    # ---- UI helpers ----
    def append_log(self, text: str):
        self.plainTextEditLog.appendPlainText(text)

    def open_config_dialog(self):
        dlg = ConfigDialog(self, self.config)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            dlg.apply_to_config()
            save_config(self.config)
            self.update_info_labels()
            QtWidgets.QMessageBox.information(self, "Config", "Config saved.")

    def browse_backup_path(self):
        default_name = datetime.datetime.now().strftime("back_%Y%m%d%H%M%S.dump")
        default_path = self.lineEditBackupPath.text() or os.path.join(BASE_DIR, default_name)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Select backup file",
            default_path,
            "Dump files (*.dump);;All files (*.*)",
        )
        if path:
            self.lineEditBackupPath.setText(path)

    def browse_restore_path(self):
        current = self.lineEditRestorePath.text()
        start_path = current if os.path.isfile(current) else BASE_DIR
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select dump file to restore",
            start_path,
            "Dump files (*.dump);;All files (*.*)",
        )
        if path:
            self.lineEditRestorePath.setText(path)

    def run_backup(self):
        dump_path = self.lineEditBackupPath.text().strip()
        if not dump_path:
            QtWidgets.QMessageBox.warning(self, "Backup", "Please select dump file path")
            return
        db_type = self.current_db_type()
        self.current_operation = "backup"
        self.start_worker(do_backup, db_type, dump_path)

    def run_restore(self):
        dump_path = self.lineEditRestorePath.text().strip()
        if not dump_path or not os.path.exists(dump_path):
            QtWidgets.QMessageBox.warning(self, "Restore", "Dump file does not exist")
            return

        db_type = self.current_db_type()
        section = self.config.get(db_type)
        db_name = section["target"]["db_name"] if section else "?"

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Restore",
            f"This will overwrite database '{db_name}' ({db_type}). Continue?",
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        self.current_operation = "restore"
        self.start_worker(do_restore, db_type, dump_path)

    def start_worker(self, fn, db_type: str, dump_path: str):
        if self.worker is not None and self.worker.isRunning():
            QtWidgets.QMessageBox.information(self, "Info", "Another operation is running")
            return

        self.backup_run_btn.setEnabled(False)
        self.restore_run_btn.setEnabled(False)

        self.worker = Worker(fn, db_type, self.config, dump_path)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, success: bool, message: str):
        self.backup_run_btn.setEnabled(True)
        self.restore_run_btn.setEnabled(True)
        if success:
            if self.current_operation == "backup":
                QtWidgets.QMessageBox.information(self, "Backup", "Backup completed successfully.")
            elif self.current_operation == "restore":
                QtWidgets.QMessageBox.information(self, "Restore", "Restore completed successfully.")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", message or "Operation failed")
        self.current_operation = None

    def on_db_type_changed(self, text: str):
        self.update_info_labels(text)


def main():
    print("Starting main...")
    try:
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle("Fusion")
        print("App created")
        window = MainWindow()
        print("Window created")
        window.show()
        print("Window shown, entering exec loop")
        sys.exit(app.exec())
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
