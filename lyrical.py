from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

import os
import sys
import uuid

from pydantic import DirectoryPath


import style
import utilities
import logging

import preferencesDialog
import projectTypeDialog
import novelPropertiesDialog
import resources


FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14,
              18, 24, 36, 48, 64, 72, 96, 144, 288]
IMAGE_EXTENSIONS = ['.jpg', '.png', '.bmp']
HTML_EXTENSIONS = ['.htm', '.html', '.txt']

# When creating a QSettings object, you must pass the name of your company or organization as well as the name of your application.
ORGANIZATION_NAME = 'Lyrical-Editor'
ORGANIZATION_DOMAIN = 'lyrical-editor.com'
APPLICATION_NAME = 'Lyrical-Editor'
SETTINGS_TRAY = 'settings/tray'
TEST_TEXT = "This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence. \
This is the fifth sentence. This is the sixth sentence. This is the seventh sentence. This is the eight sentence."


def hexuuid():
    return uuid.uuid4().hex

# Split the path name into a pair root and ext.
# Here, ext stands for extension and has the extension portion of the specified path while root is everything except ext part.


def splitext(p):
    return os.path.splitext(p)[1].lower()


class TextEdit(QTextEdit):

    def can_insert_from_mime_data(self, source):

        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).can_insert_from_mime_data(source)

    def insert_from_mime_data(self, source):

        cursor = self.textCursor()
        document = self.document()

        if source.hasUrls():

            for u in source.urls():
                file_ext = splitext(str(u.toLocalFile()))
                if u.isLocalFile() and file_ext in IMAGE_EXTENSIONS:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())

                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break

            else:
                # If all were valid images, finish here.
                return

        elif source.hasImage():
            image = source.imageData()
            uuid = hexuuid()
            document.addResource(QTextDocument.ImageResource, uuid, image)
            cursor.insertImage(uuid)
            return

        super(TextEdit, self).insert_from_mime_data(source)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.load_settings()
        layout = QVBoxLayout()  # The QVBoxLayout class lines up widgets vertically
        # this is using the editor class based on QTextEdit above, this is a new member declaration
        self.editor = TextEdit()
        # Setup the QTextEdit editor configuration
        self.editor.setAutoFormatting(QTextEdit.AutoAll)
        self.editor.selectionChanged.connect(self.update_format)

        self.load_font()

        # Initialize default font size for the editor.
        font = QFont('Times', 12)
        self.editor.setFont(font)

        # We need to repeat the size to init the current format.
        self.editor.setFontPointSize(12)
        self.projectType = "Novel"
        # # enable this for a frameless window
        # # Borderless window code begins
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.center()
        # #self.setFixedSize(320, 450)
        # self.setStyleSheet(
        #     "QMainWindow{background-color: darkgray;border: 1px solid black}")
        # # Borderless window code ends

        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = None

        layout.addWidget(self.editor)

        container = QWidget()

        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.define_file_toolbar()
        self.define_edit_toolbar()
        self.define_format_toolbar()

        self.addToolBarBreak()
        self.define_style_toolbar()
        self.define_project_explorer()

        # Initialize.
        self.update_format()
        self.update_title()
        self.oldPos = self.pos()

        # self.setGeometry(100, 100, 400, 300)
        self.show()

    def load_font(self):
        fontId = QFontDatabase.addApplicationFont(
            ':/fonts/fonts/Amarante-Regular.ttf')
        if fontId < 0:
            print('font not loaded')
        else:
            self.fontFamilies = QFontDatabase.applicationFontFamilies(fontId)
            font = QFont(self.fontFamilies[0])
            # self.setFont(font)
        # id = QFontDatabase.addApplicationFont("//party.ttf")
        # _fontstr = QFontDatabase.applicationFontFamilies(id).at(0)
        # _font = QFont(_fontstr, 8)
        # _fontstr = QFontDatabase.applicationFontFamilies(id)[0]
        # app.setFont(font)

    def show_preferences(self, s):
        print("click", s)
        self.preferencesDialog = preferencesDialog.PreferencesDialog(self)

        if self.preferencesDialog.exec():
            self.projectHomeDirectory = self.preferencesDialog.projectHomeDirectoryEdit.text()
            print("Success! " + self.projectHomeDirectory)
        else:
            print("Cancel!")

    # def mouse_press_event(self, event):
    #     self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def define_format_toolbar(self):

        # # Adds a format menu option to the top level menu
        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(format_toolbar)
        format_menu = self.menuBar().addMenu("&Format")

        # # We need references to these actions/settings to update as selection changes, so attach to self.
        self.fonts = QFontComboBox()
        self.fonts.currentFontChanged.connect(self.editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])

        # # Connect to the signal producing the text of the current selection. Convert the string to float
        # # and set as the pointsize. We could also use the index + retrieve from FONT_SIZES.
        self.fontsize.currentIndexChanged[str].connect(
            lambda s: self.editor.setFontPointSize(float(s)))
        format_toolbar.addWidget(self.fontsize)

        # self.bold_action = QAction(
        #     QIcon(os.path.join('images', 'edit-bold.png')), "Bold", self)

        icon = QIcon()
        icon.addPixmap(QPixmap(
            ":/images/images/edit-bold.png"), QIcon.Normal, QIcon.Off)
        self.bold_action = QAction(
            icon, "Bold", self)

        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(
            lambda x: self.editor.setFontWeight(QFont.Bold if x else QFont.Normal))
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        # self.italic_action = QAction(
        #    QIcon(os.path.join('images', 'edit-italic.png')), "Italic", self)
        self.italic_action = QAction(
            QIcon(":/images/images/edit-italic.png"), "Italic", self)
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.editor.setFontItalic)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(
            QIcon(":/images/images/edit-underline.png"), "Underline", self)
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.editor.setFontUnderline)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        format_menu.addSeparator()

        self.alignl_action = QAction(
            QIcon(":/images/images/edit-alignment.png"), "Align left", self)
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignLeft))
        format_toolbar.addAction(self.alignl_action)
        format_menu.addAction(self.alignl_action)

        self.alignc_action = QAction(
            QIcon(":/images/images/edit-alignment-center.png"), "Align center", self)
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignCenter))
        format_toolbar.addAction(self.alignc_action)
        format_menu.addAction(self.alignc_action)

        self.alignr_action = QAction(
            QIcon(":/images/images/edit-alignment-right.png"), "Align right", self)
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignRight))
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.alignj_action = QAction(
            QIcon(":/images/images/edit-alignment-justify.png"), "Justify", self)
        self.alignj_action.setStatusTip("Justify text")
        self.alignj_action.setCheckable(True)
        self.alignj_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignJustify))
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)

        # # In some situations it is useful to group QAction objects together.
        # # For example, if you have a Left Align action, a Right Align action, a Justify action,
        # # and a Center action, only one of these actions should be active at any one time.
        # # One simple way of achieving this is to group the actions together in an action group.
        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)

        format_menu.addSeparator()

        # The underscore prefix is meant as a hint to another programmer that a variable or method starting with a single underscore
        # is intended for internal use or private in the case of a class.
        # A list of all format-related widgets/actions, so we can disable/enable signals when updating.
        self._format_actions = [
            self.fonts,
            self.fontsize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            # We don't need to disable signals for alignment, as they are paragraph-wide.
        ]
        return format_toolbar

    def define_edit_toolbar(self):
        # The QToolBar class provides a movable panel that contains a set of controls. In this instance we are creating the Edit Toolbar.
        # This will appear on the main application menu.
        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(edit_toolbar)
        # The QMainWindow Class has a menuBar property, the menuBar can contain a collection of menus
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction(
            QIcon(":/images/images/undo.png"), "Undo", self)
        undo_action.setStatusTip("Undo last change")
        undo_action.triggered.connect(self.editor.undo)
        edit_toolbar.addAction(undo_action)
        edit_menu.addAction(undo_action)

        redo_action = QAction(
            QIcon(":/images/images/redo.png"), "Redo", self)
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(
            QIcon(":/images/images/scissors.png"), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(
            QIcon(":/images/images/document-copy.png"), "Copy", self)
        copy_action.setStatusTip("Copy selected text")
        cut_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(
            QIcon(":/images/images/clipboard-paste-document-text.png"), "Paste", self)
        paste_action.setStatusTip("Paste from clipboard")
        cut_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(
            QIcon(":/images/images/selection-input.png"), "Select all", self)
        select_action.setStatusTip("Select all text")
        cut_action.setShortcut(QKeySequence.SelectAll)
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QAction(
            QIcon(":/images/images/arrow-continue.png"), "Wrap text to window", self)
        wrap_action.setStatusTip("Toggle wrap text to window")
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        preferences_action = QAction(
            QIcon(":/images/images/preferences.png"), "Lyrical Preferences", self)
        preferences_action.setStatusTip("Set Your Lyrical Preferences")
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)
        edit_toolbar.addAction(preferences_action)

    def define_file_toolbar(self):
        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        # Actions
        # Actions can be added to menus and toolbars, and will automatically keep them in sync.
        # For example, in a word processor, if the user presses a Bold toolbar button, the Bold menu item will automatically be checked.
        open_file_action = QAction(
            QIcon(":/images/images/open-document.png"), "Open file...", self)
        open_file_action.setStatusTip("Open file")
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        file_toolbar.addAction(open_file_action)

        new_project_action = QAction(
            QIcon(":/images/images/new-project.png"), "new Project...", self)
        # new_project_action = QAction('new Project...', self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)
        file_toolbar.addAction(new_project_action)

        open_project_action = QAction(
            QIcon(":/images/images/open-project.png"), "Open Project...", self)
        # open_project_action = QAction('Open Project...', self)
        open_project_action.triggered.connect(self.choose_directory)
        file_menu.addAction(open_project_action)
        file_toolbar.addAction(open_project_action)

        save_file_action = QAction(
            QIcon(":/images/images/disk.png"), "Save", self)
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        file_toolbar.addAction(save_file_action)

        saveas_file_action = QAction(
            QIcon(":/images/images/disk-pencil.png"), "Save As...", self)
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        print_action = QAction(
            QIcon(":/images/images/printer.png"), "Print...", self)
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        file_toolbar.addAction(print_action)

    def get_syllable_count(self):
        cursor = QTextCursor(self.editor.textCursor())
        # word = cursor.selectedText() # enable for selected text
        text = self.editor.toPlainText()
        if utilities.isNotBlank(text):
            text = text.lower()
            # count = style.syllable_count(word)
            count = style.calculate_average_syllables_per_word(text)
            self.status.showMessage(
                "Average Syllable Length: " + str(count), 2000)

    def generate_test_text(self):
        self.editor.setText(TEST_TEXT)

    def create_novel_structure(self, properties):
        # create an outline for our novel
        print("Success! for novel properties Prologue: {} Foreword {}".format(
            properties.prologue, properties.foreword))
        # We now need to get the name of the project and properties
        directory = QFileDialog.getSaveFileName(
            caption="Create a new Project Directory",
            directory=self.projectHomeDirectory,
            filter=""
        )
        self.status.showMessage(
            "New Project Directory: " + str(directory[0]), 2000)
        try:
            os.mkdir(str(directory[0]))
        except OSError as error:
            self.status.showMessage(
                "Failed to create: " + str(directory[0]) + " " + str(error), 10000)
        # create the requested documents

        try:
            if(properties.foreword):
                path = os.sep.join([directory[0], 'foreword.txt'])
                fp = open(path, 'x')
                fp.close()
        except OSError as error:
            self.status.showMessage(
                "Failed to create foreword: " + str(error), 10000)
        # self.foreword = False
        # self.preface = False
        # self.introduction = False
        # self.prologue = False
        # self.epilogue = False
        # self.numberOfChapters = 20
        try:
            if(properties.preface):
                path = os.sep.join([directory[0], 'preface.txt'])
                fp = open(path, 'x')
                fp.close()
        except OSError as error:
            self.status.showMessage(
                "Failed to create preface: " + str(error), 10000)
        try:
            if(properties.introduction):
                path = os.sep.join([directory[0], 'introduction.txt'])
                fp = open(path, 'x')
                fp.close()
        except OSError as error:
            self.status.showMessage(
                "Failed to create introduction: " + str(error), 10000)
        try:
            if(properties.prologue):
                path = os.sep.join([directory[0], 'prologue.txt'])
                fp = open(path, 'x')
                fp.close()
        except OSError as error:
            self.status.showMessage(
                "Failed to create prologue: " + str(error), 10000)
        try:
            if(properties.epilogue):
                path = os.sep.join([directory[0], 'epilogue.txt'])
                fp = open(path, 'x')
                fp.close()
        except OSError as error:
            self.status.showMessage(
                "Failed to create epilogue: " + str(error), 10000)
        for chapter in range(1, properties.numberOfChapters+1):
            try:
                chapterName = "chapter_" + str(chapter) + ".txt"
                path = os.sep.join([directory[0], chapterName])
                fp = open(path, 'x')
                fp.close()
            except OSError as error:
                self.status.showMessage(
                    "Failed to create chapter: " + str(chapter), 10000)

    def create_new_project(self):
        self.projectTypeDialog = projectTypeDialog.ProjectTypeDialog(self)

        if self.projectTypeDialog.exec():
            self.projectType = self.projectTypeDialog.project
            # self.projectHomeDirectory = self.projectTypeDialog.projectHomeDirectoryEdit.text()
            print("Success! " + self.projectType)
            self.novelPropertiesDialog = novelPropertiesDialog.NovelPropertiesDialog(
                self)
            if self.novelPropertiesDialog.exec():
                self.create_novel_structure(
                    self.novelPropertiesDialog.properties)
            else:
                print("Canceled! for novel properties {}".format(
                    self.novelPropertiesDialog.properties))
        else:
            print("Cancel! " + self.projectType)

        # Used when we create a new project or open an existing one

    def choose_directory(self):
        """
        Select a directory to display.
        """
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)
        directory = file_dialog.getExistingDirectory(self, "Open Directory",
                                                     self.projectHomeDirectory, QFileDialog.ShowDirsOnly)

        self.tree.setRootIndex(self.model.index(directory))
        # update the current project preferences setting
        self.projectCurrentDirectory = directory
        self.status.showMessage(
            "Project Directory: " + str(directory), 2000)

    def get_functional_word_count(self):
        cursor = QTextCursor(self.editor.textCursor())
        # selection = QTextEdit.ExtraSelection()
        # selection.cursor = self.editor.textCursor()
        # word = cursor.selectedText()
        text = self.editor.toPlainText()
        if utilities.isNotBlank(text):
            text = text.lower()
            # count = style.syllable_count(word)
            count = style.calculate_functional_word_count(text)
            self.status.showMessage(
                "Functional Word Score: " + str(count), 2000)

    # Create a dockable Project Explorer

    def define_project_explorer(self):
        """
        Defines the project explorer
        """
        """
        Set up the QTreeView so that it displays the contents
        of the Project.
        """
        self.model = QFileSystemModel()

        # setRootPath
        # Sets the directory that is being watched by the model to newPath by installing a file system watcher on it.
        # Any changes to files and directories within this directory will be reflected in the model.
        # If the path is changed, the rootPathChanged() signal will be emitted.
        # Note: This function does not change the structure of the model or modify the data available to views.
        # In other words, the "root" of the model is not changed to include only files and directories within the directory
        # specified by newPath in the file system.
        self.model.setRootPath(self.projectHomeDirectory)

        self.tree = QTreeView()
        self.tree.setIndentation(10)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.projectHomeDirectory))
        self.tree.clicked.connect(self.on_treeView_clicked)
        # Set up container and layout
        frame = QFrame()  # The QFrame class is used as a container to group and surround widgets, or to act as placeholders in GUI
        # applications. You can also apply a frame style to a QFrame container to visually separate it from nearbywidgets.
        frame_v_box = QVBoxLayout()
        frame_v_box.addWidget(self.tree)
        frame.setLayout(frame_v_box)
        # self.setCentralWidget(frame) # The central widget in the center of the window must be set if you are going to use QMainWindow as your
        # base class. For example, you could use a single QTextEdit widget or create a QWidget object to act as a parent
        # to a number of other widgets, then use setCentralWidget() , and set your central widget for the main
        # window.
        self.explorer_dock = QDockWidget("Explorer", self)
        self.explorer_dock.setWidget(self.tree)
        self.explorer_dock.setFloating(False)
        self.explorer_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.explorer_dock)

    # Create a dockable Style Bar

    def define_style_toolbar(self):
        """
        Defines the tools bar and actions associated with style analysis
        """
        style_toolbar = QToolBar("Style")
        style_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(style_toolbar)
        style_menu = self.menuBar().addMenu("&Style")

        generate_text_action = QAction(
            QIcon(":/images/images/generate-text.png"), "Generate Random Text", self)
        generate_text_action.setStatusTip("Generate Random Text")
        generate_text_action.triggered.connect(
            self.generate_test_text)
        style_menu.addAction(generate_text_action)
        style_toolbar.addAction(generate_text_action)

        count_syllable_action = QAction(
            QIcon(":/images/images/syllables.png"), "Average Syllable Length", self)
        count_syllable_action.setStatusTip("Average Syllable Length")
        count_syllable_action.triggered.connect(
            self.get_syllable_count)
        style_menu.addAction(count_syllable_action)
        style_toolbar.addAction(count_syllable_action)

        count_functional_words_action = QAction(
            QIcon(":/images/images/functional-words.png"), "Functional Word Count", self)
        count_functional_words_action.setStatusTip("Functional Word Count")
        count_functional_words_action.triggered.connect(
            self.get_functional_word_count)
        style_menu.addAction(count_functional_words_action)
        style_toolbar.addAction(count_functional_words_action)

        self.style_dock = QDockWidget("Style", self)
        self.style_dock.setWidget(style_toolbar)
        self.style_dock.setFloating(False)
        self.addDockWidget(Qt.TopDockWidgetArea, self.style_dock)

    # When the user selects some text we want the font toolbar to reflect the format of their selection

    def update_format(self):
        """
        Update the font format toolbar/actions when a new text selection is made. This is neccessary to keep
        toolbars/etc. in sync with the current edit state.
        :return:
        """
        # Disable signals for all format widgets, so changing values here does not trigger further formatting.
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.editor.currentFont())
        # Nasty, but we get the font-size as a float but want it was an int
        self.fontsize.setCurrentText(str(int(self.editor.fontPointSize())))

        self.italic_action.setChecked(self.editor.fontItalic())
        self.underline_action.setChecked(self.editor.fontUnderline())
        self.bold_action.setChecked(self.editor.fontWeight() == QFont.Bold)

        self.alignl_action.setChecked(self.editor.alignment() == Qt.AlignLeft)
        self.alignc_action.setChecked(
            self.editor.alignment() == Qt.AlignCenter)
        self.alignr_action.setChecked(self.editor.alignment() == Qt.AlignRight)
        self.alignj_action.setChecked(
            self.editor.alignment() == Qt.AlignJustify)

        self.block_signals(self._format_actions, False)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def open_file(self, path):
        try:
            with open(path, 'r') as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            # Qt will automatically try and guess the format as txt/html
            self.editor.setText(text)
            self.update_title()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open file", "", "HTML documents (*.html);Text documents (*.txt);All files (*.*)")
        self.open_file(path)

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()

        text = self.editor.toHtml() if splitext(
            self.path) in HTML_EXTENSIONS else self.editor.toPlainText()

        try:
            with open(self.path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save file", "", "HTML documents (*.html);Text documents (*.txt);All files (*.*)")

        if not path:
            # If dialog is cancelled, will return ''
            return
        # Depending on the extension, save as either html or plain text
        text = self.editor.toHtml() if splitext(
            path) in HTML_EXTENSIONS else self.editor.toPlainText()

        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle(
            "%s - Lyrical" % (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(
            1 if self.editor.lineWrapMode() == 0 else 0)

    def save_settings(self):
        settings = QSettings()
        # QSettings stores settings. Each setting consists of a QString that specifies the setting’s name (the key ) and a QVariant that stores the data associated with the key. To write a setting, use setValue()
        settings.setValue(SETTINGS_TRAY, False)  # self.check_box.isChecked()
        settings.beginGroup("MainWindow")
        # the current active project directory within the root
        settings.setValue("project_current", self.projectCurrentDirectory)
        mySize = self.size()
        settings.setValue("size", self.size())
        myPosition = self.pos()
        settings.setValue("pos", self.pos())
        settings.endGroup()
        settings.beginGroup("Preferences")
        # the default root directory for all projects
        settings.setValue("project_home", self.projectHomeDirectory)

        settings.endGroup()
        settings.sync()
        logging.info("Saved Lyrical settings")

    def load_settings(self):
        settings = QSettings()
        settings.beginGroup("Preferences")
        self.projectHomeDirectory = settings.value("project_home")
        settings.endGroup()
        settings.beginGroup("MainWindow")
        self.projectCurrentDirectory = settings.value("project_current")
        self.applicationPosition = settings.value("pos")
        self.applicationSize = settings.value("size")
        self.setGeometry(self.applicationPosition.x(), self.applicationPosition.y(
        ), self.applicationSize.width(), self.applicationSize.height())
        settings.endGroup()
        logging.info("Loaded Lyrical settings")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()
# Used to set the project root directory

    def set_directory(self):
        """
        Choose the directory.
        """
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)
        self.directory = file_dialog.getExistingDirectory(self, "Open \
        Directory", self.projectHomeDirectory, QFileDialog.ShowDirsOnly)
        if self.directory:
            self.preferencesDialog.projectHomeDirectoryEdit.setText(
                self.directory)

    def on_treeView_clicked(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)
        self.status.showMessage(
            "Selected File: " + str(filePath) + "   " + str(fileName), 10000)
        self.open_file(filePath)


if __name__ == '__main__':

    app = QApplication(sys.argv)  # create the main app
    # When creating a QSettings object, you must pass the name of your company or organization as well as the name of your application.
    QCoreApplication.setApplicationName(ORGANIZATION_NAME)
    # When the Internet domain is set, it is used on macOS and iOS instead of the organization name, since macOS and iOS applications conventionally use Internet domains to identify themselves.
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APPLICATION_NAME)
    logging.basicConfig(level=logging.DEBUG, filename="lyrical.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    logging.info("Starting Lyrical Editor")
    window = MainWindow()
    app.exec_()