from PyQt6 import QtCore, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 500)

        self.verticalLayout = QtWidgets.QVBoxLayout(MainWindow)
        self.verticalLayout.setObjectName("verticalLayout")

        # DB type selector
        self.layoutDbType = QtWidgets.QHBoxLayout()
        self.layoutDbType.setObjectName("layoutDbType")
        self.labelDbType = QtWidgets.QLabel(parent=MainWindow)
        self.labelDbType.setObjectName("labelDbType")
        self.layoutDbType.addWidget(self.labelDbType)
        self.comboDbType = QtWidgets.QComboBox(parent=MainWindow)
        self.comboDbType.setObjectName("comboDbType")
        self.layoutDbType.addWidget(self.comboDbType)

        self.btnConfig = QtWidgets.QPushButton(parent=MainWindow)
        self.btnConfig.setObjectName("btnConfig")
        self.layoutDbType.addWidget(self.btnConfig)

        self.verticalLayout.addLayout(self.layoutDbType)

        # Backup group
        self.groupBoxBackup = QtWidgets.QGroupBox(parent=MainWindow)
        self.groupBoxBackup.setObjectName("groupBoxBackup")
        self.gridLayoutBackup = QtWidgets.QGridLayout(self.groupBoxBackup)
        self.gridLayoutBackup.setObjectName("gridLayoutBackup")

        self.labelSrcInfo = QtWidgets.QLabel(parent=self.groupBoxBackup)
        self.labelSrcInfo.setObjectName("labelSrcInfo")
        self.gridLayoutBackup.addWidget(self.labelSrcInfo, 0, 0, 1, 3)

        self.labelBackupPath = QtWidgets.QLabel(parent=self.groupBoxBackup)
        self.labelBackupPath.setObjectName("labelBackupPath")
        self.gridLayoutBackup.addWidget(self.labelBackupPath, 1, 0, 1, 1)

        self.lineEditBackupPath = QtWidgets.QLineEdit(parent=self.groupBoxBackup)
        self.lineEditBackupPath.setObjectName("lineEditBackupPath")
        self.gridLayoutBackup.addWidget(self.lineEditBackupPath, 1, 1, 1, 1)

        self.btnBackupBrowse = QtWidgets.QPushButton(parent=self.groupBoxBackup)
        self.btnBackupBrowse.setObjectName("btnBackupBrowse")
        self.gridLayoutBackup.addWidget(self.btnBackupBrowse, 1, 2, 1, 1)

        self.btnBackupRun = QtWidgets.QPushButton(parent=self.groupBoxBackup)
        self.btnBackupRun.setObjectName("btnBackupRun")
        self.gridLayoutBackup.addWidget(self.btnBackupRun, 2, 2, 1, 1)

        self.verticalLayout.addWidget(self.groupBoxBackup)

        # Restore group
        self.groupBoxRestore = QtWidgets.QGroupBox(parent=MainWindow)
        self.groupBoxRestore.setObjectName("groupBoxRestore")
        self.gridLayoutRestore = QtWidgets.QGridLayout(self.groupBoxRestore)
        self.gridLayoutRestore.setObjectName("gridLayoutRestore")

        self.labelTgtInfo = QtWidgets.QLabel(parent=self.groupBoxRestore)
        self.labelTgtInfo.setObjectName("labelTgtInfo")
        self.gridLayoutRestore.addWidget(self.labelTgtInfo, 0, 0, 1, 3)

        self.labelRestorePath = QtWidgets.QLabel(parent=self.groupBoxRestore)
        self.labelRestorePath.setObjectName("labelRestorePath")
        self.gridLayoutRestore.addWidget(self.labelRestorePath, 1, 0, 1, 1)

        self.lineEditRestorePath = QtWidgets.QLineEdit(parent=self.groupBoxRestore)
        self.lineEditRestorePath.setObjectName("lineEditRestorePath")
        self.gridLayoutRestore.addWidget(self.lineEditRestorePath, 1, 1, 1, 1)

        self.btnRestoreBrowse = QtWidgets.QPushButton(parent=self.groupBoxRestore)
        self.btnRestoreBrowse.setObjectName("btnRestoreBrowse")
        self.gridLayoutRestore.addWidget(self.btnRestoreBrowse, 1, 2, 1, 1)

        self.btnRestoreRun = QtWidgets.QPushButton(parent=self.groupBoxRestore)
        self.btnRestoreRun.setObjectName("btnRestoreRun")
        self.gridLayoutRestore.addWidget(self.btnRestoreRun, 2, 2, 1, 1)

        self.verticalLayout.addWidget(self.groupBoxRestore)

        # Console label
        self.labelConsole = QtWidgets.QLabel(parent=MainWindow)
        self.labelConsole.setObjectName("labelConsole")
        self.verticalLayout.addWidget(self.labelConsole)

        # Log output
        self.plainTextEditLog = QtWidgets.QPlainTextEdit(parent=MainWindow)
        self.plainTextEditLog.setReadOnly(True)
        self.plainTextEditLog.setObjectName("plainTextEditLog")
        self.verticalLayout.addWidget(self.plainTextEditLog)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "DockDbBack - Docker DB Backup & Restore"))
        self.labelDbType.setText(_translate("MainWindow", "Database type:"))
        # combo items
        if self.comboDbType.count() == 0:
            self.comboDbType.addItem("Postgres")
            self.comboDbType.addItem("MySQL")
        self.btnConfig.setText(_translate("MainWindow", "Config..."))
        self.groupBoxBackup.setTitle(_translate("MainWindow", "Backup"))
        self.labelSrcInfo.setText(_translate("MainWindow", "source:"))
        self.labelBackupPath.setText(_translate("MainWindow", "Dump file (save as):"))
        self.btnBackupBrowse.setText(_translate("MainWindow", "Browse..."))
        self.btnBackupRun.setText(_translate("MainWindow", "Run Backup"))
        self.groupBoxRestore.setTitle(_translate("MainWindow", "Restore"))
        self.labelTgtInfo.setText(_translate("MainWindow", "target:"))
        self.labelRestorePath.setText(_translate("MainWindow", "Dump file (to restore):"))
        self.btnRestoreBrowse.setText(_translate("MainWindow", "Browse..."))
        self.btnRestoreRun.setText(_translate("MainWindow", "Run Restore"))
        self.labelConsole.setText(_translate("MainWindow", "Console output:"))
