'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_project_dialogs.py

'''
import sys
import os
import pathlib
import urllib.parse

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_dialog_bases
import wb_platform_specific
import wb_pick_path_dialogs

#------------------------------------------------------------
class WbScmAddProjectWizard(QtWidgets.QWizard):
    action_clone = 1
    action_init = 2
    action_add_existing = 3

    def __init__( self, app ):
        self.app = app
        self.all_factories = app.all_factories
        super().__init__()

        em = self.app.fontMetrics().width( 'm' )
        self.setMinimumWidth( 100*em )

        # ------------------------------------------------------------
        self.page_id_start = 1
        self.page_id_browse_existing = 2
        self.page_id_scan_for_existing = 3

        self.page_id_name = 4

        next_id = 5

        self.all_clone_pages = {}
        self.all_init_pages = {}

        for scm_name in sorted( self.all_factories ):
            f = self.all_factories[ scm_name ]
            for page in f.projectDialogClonePages( self ):
                self.all_clone_pages[ next_id ] = page
                next_id += 1

            for page in f.projectDialogInitPages( self ):
                self.all_init_pages[ next_id ] = page
                next_id += 1

        # needs all_clone_pages and all_init_pages
        self.page_start = PageAddProjectStart( self )

        self.page_browse_existing = PageAddProjectBrowseExisting()
        self.page_scan_for_existing = PageAddProjectScanForExisting()

        self.page_name = PageAddProjectName()

        self.setPage( self.page_id_start, self.page_start )

        self.setPage( self.page_id_scan_for_existing, self.page_scan_for_existing )
        self.setPage( self.page_id_browse_existing, self.page_browse_existing )

        self.setPage( self.page_id_name, self.page_name )

        for id_, page in sorted( self.all_clone_pages.items() ):
            self.setPage( id_, page )

        for id_, page in sorted( self.all_init_pages.items() ):
            self.setPage( id_, page )

        #------------------------------------------------------------
        self.all_existing_project_names = set()
        self.all_existing_project_paths = set()

        if self.app is not None:
            prefs = self.app.prefs

            for project in prefs.getAllProjects():
                self.all_existing_project_names.add( project.name.lower() )
                self.all_existing_project_paths.add( project.path )

        self.project_default_parent_folder = wb_platform_specific.getHomeFolder()

        self.scm_type = None
        self.action = None
        self.wc_path = None
        self.scm_url = None
        self.name = None

    def closeEvent( self, event ):
        # tell pages with resources to cleanup
        self.page_scan_for_existing.freeResources()

        super().closeEvent( event )

    def setScmUrl( self, scm_url ):
        self.scm_url = scm_url

    def getScmUrl( self ):
        return self.scm_url

    def setScmType( self, scm_type ):
        self.scm_type = scm_type

    def getScmType( self ):
        return self.scm_type

    def getScmFactory( self ):
        return self.all_factories[ self.scm_type ]

    def setAction( self, action ):
        self.action = action

    def getAction( self ):
        return self.action

    def setWcPath( self, wc_path ):
        if isinstance( wc_path, pathlib.Path ):
            self.wc_path = wc_path

        else:
            self.wc_path = pathlib.Path( wc_path )

    def getWcPath( self ):
        return self.wc_path

    def setProjectName( self, name ):
        self.name = name

    def getProjectName( self ):
        return self.name

    def pickWcPath( self, parent ):
        path = wb_pick_path_dialogs.pickFolder( self, self.wc_path )
        if path is not None:
            self.wc_path = path
            return True

        return False

    def detectScmTypeForFolder( self, folder ):
        scm_folder_detection = []
        for factory in self.all_factories.values():
            scm_folder_detection.extend( factory.folderDetection() )

        for special_folder, scm in scm_folder_detection:
            scm_folder = folder / special_folder
            try:
                if scm_folder.is_dir():
                    return scm

            except PermissionError:
                # ignore folders that cannot be accessed
                pass

        return None


class PageAddProjectStart(QtWidgets.QWizardPage):
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add SCM Project') )
        self.setSubTitle( T_('Where is the SCM Project?') )

        self.radio_git_init = QtWidgets.QRadioButton(  )
        self.radio_hg_init = QtWidgets.QRadioButton(  )

        self.radio_git_clone = QtWidgets.QRadioButton(  )
        self.radio_hg_clone = QtWidgets.QRadioButton(  )
        self.radio_svn_checkout = QtWidgets.QRadioButton(  )

        self.radio_browse_existing = QtWidgets.QRadioButton( T_('Browse for existing SCM repository') )
        self.radio_scan_for_existing = QtWidgets.QRadioButton( T_('Scan for existing SCM repositories') )

        self.radio_scan_for_existing.setChecked( True )
        self.radio_browse_existing.setChecked( False )

        self.grp_show = QtWidgets.QButtonGroup()
        self.grp_show.addButton( self.radio_scan_for_existing )
        self.grp_show.addButton( self.radio_browse_existing )

        self.all_clone_radio = []
        for id_, page in sorted( wizard.all_clone_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            self.all_clone_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        self.all_init_radio = []
        for id_, page in sorted( wizard.all_init_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            self.all_init_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Add a local project') ) )
        layout.addWidget( self.radio_scan_for_existing )
        layout.addWidget( self.radio_browse_existing )

        layout.addWidget( QtWidgets.QLabel( T_('Add an external project') ) )
        for id_, radio in self.all_clone_radio:
            layout.addWidget( radio )

        layout.addWidget( QtWidgets.QLabel( T_('Create an empty project') ) )
        for id_, radio in self.all_init_radio:
            layout.addWidget( radio )

        self.setLayout( layout )

    def nextId( self ):
        w = self.wizard()

        if self.radio_browse_existing.isChecked():
            return w.page_id_browse_existing

        if self.radio_scan_for_existing.isChecked():
            return w.page_id_scan_for_existing

        for id_, radio in self.all_clone_radio + self.all_init_radio:
            if radio.isChecked():
                return id_

        assert False

class PageAddProjectScmInitAndCloneBase(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.wc_path = QtWidgets.QLineEdit()
        self.wc_path.textChanged.connect( self._fieldsChanged )

        self.feedback = QtWidgets.QLabel( '' )

        layout = QtWidgets.QGridLayout()
        self.initLayout( layout )
        self.setLayout( layout )

    def initLayout( self, layout ):
        raise NotImplementedError()

    def initializePage( self ):
        self.wc_path.setText( str( self.wizard().project_default_parent_folder ) )

    def nextId( self ):
        return self.wizard().page_id_name

    def __pickDirectory( self ):
        w = self.wizard()
        w.setWcPath( self.wc_path.text() )
        if w.pickWcPath( self ):
            self.wc_path.setText( str( w.getWcPath() ) )

    def _fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        if not self.isValidPath():
            return False

        return True

    def isValidPath( self ):
        path =  self.wc_path.text().strip()
        if path == '':
            self.feedback.setText( T_('Fill in the Working Copy') )
            return False

        path = pathlib.Path( path )

        if not path.exists():
            if path.parent.exists():
                self.feedback.setText( T_('%s will be created') % (path,) )
                return True

            else:
                self.feedback.setText( T_('%s cannot be used as it does not exist') % (path,) )
                return False

        if not path.is_dir():
            self.feedback.setText( T_('%s is not a directory') % (path,) )
            return False

        is_empty = True
        for filenme in path.iterdir():
            is_empty = False
            break

        if not is_empty:
            self.feedback.setText( T_('%s is not an empty directory') % (path,) )
            return False

        self.feedback.setText( '' )
        return True

    def validatePage( self ):
        w = self.wizard()
        w.setScmType( self.getScmType() )
        w.setAction( w.action_init )
        w.setWcPath( self.wc_path.text().strip() )

        return True

    def getScmType( self ):
        raise NotImplementedError()


#--------------------------------------------------
class PageAddProjectScmCloneBase(PageAddProjectScmInitAndCloneBase):
    def __init__( self ):
        self.url = None
        super().__init__()

    def initLayout( self, layout ):
        self.url = QtWidgets.QLineEdit( '' )
        self.url.textChanged.connect( self._fieldsChanged )

        layout.addWidget( QtWidgets.QLabel( T_('URL') ), 0, 0 )
        layout.addWidget( self.url, 0, 1 )
        layout.addWidget( QtWidgets.QLabel( T_('Working Copy') ), 1, 0 )
        layout.addWidget( self.wc_path, 1, 1 )
        layout.addWidget( self.browse_button, 1, 2 )
        layout.addWidget( self.feedback, 2, 1 )

    def isComplete( self ):
        if not self.isValidUrl():
            return False

        if not self.isValidPath():
            return False

        self.feedback.setText( '' )
        return True

    def isValidUrl( self ):
        url = self.url.text().strip()
        if ':' not in url or '/' not in url:
            self.feedback.setText( T_('Fill in a repository URL') )
            return False

        result = urllib.parse.urlparse( url )
        scheme = result.scheme.lower()
        all_supported_schemes = self.allSupportedSchemes()
        if scheme not in all_supported_schemes:
            self.feedback.setText( T_('Scheme %(scheme)s is not supported. Use one of %(all_supported_schemes)s') %
                                    {'scheme': scheme
                                    ,'all_supported_schemes': ', '.join( all_supported_schemes )} )
            return False

        if result.netloc == '' or result.path == '':
            self.feedback.setText( T_('Fill in a repository URL') )
            return False

        return True

    def validatePage( self ):
        w = self.wizard()
        w.setScmType( self.getScmType() )
        w.setAction( w.action_clone )
        w.setScmUrl( self.url.text().strip() )
        w.setWcPath( self.wc_path.text() )

        return True

    def getScmType( self ):
        raise NotImplementedError()

#------------------------------------------------------------
class PageAddProjectScmInitBase(PageAddProjectScmInitAndCloneBase):
    def __init__( self ):
        super().__init__()

    def initLayout( self, layout ):
        layout.addWidget( QtWidgets.QLabel( T_('Working Copy') ), 1, 0 )
        layout.addWidget( self.wc_path, 1, 1 )
        layout.addWidget( self.browse_button, 1, 2 )
        layout.addWidget( self.feedback, 2, 1 )

    def isComplete( self ):
        if not self.isValidPath():
            return False

        return True

    def validatePage( self ):
        w = self.wizard()
        w.setScmType( self.getScmType() )
        w.setAction( w.action_init )
        w.setWcPath( self.wc_path.text().strip() )

        return True

    def getScmType( self ):
        raise NotImplementedError()

#------------------------------------------------------------
class PageAddProjectBrowseExisting(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add SCM Project') )
        self.setSubTitle( T_('Browse for the SCM repository working copy') )

        self.feedback = QtWidgets.QLabel( '' )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.wc_path = QtWidgets.QLineEdit( '' )
        self.wc_path.textChanged.connect( self.__fieldsChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('SCM Working Copy') ), 0, 0 )
        layout.addWidget( self.wc_path, 0, 1 )
        layout.addWidget( self.browse_button, 0, 2 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def nextId( self ):
        return self.wizard().page_id_name

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        path =  self.wc_path.text().strip()
        if path == '':
            return False

        w = self.wizard()

        path = pathlib.Path( path )

        scm_type = w.detectScmTypeForFolder( path )
        if scm_type is None:
            self.feedback.setText( T_('%s is not a project folder') % (path,) )
            return False

        if path in w.all_existing_project_paths:
            self.feedback.setText( T_('Project folder %s has already been added') % (path,) )
            return False

        w.setScmType( scm_type )

        self.feedback.setText( '' )
        return True

    def validatePage( self ):
        w = self.wizard()
        w.setAction( w.action_add_existing )
        w.setWcPath( self.wc_path.text() )

        return True

    def __pickDirectory( self ):
        w = self.wizard()
        w.setWcPath( self.wc_path.text() )
        if w.pickWcPath( self ):
            self.wc_path.setText( str( w.getWcPath() ) )

class PageAddProjectScanForExisting(QtWidgets.QWizardPage):
    foundRepository = QtCore.pyqtSignal( [str, str] )
    scannedOneMoreFolder = QtCore.pyqtSignal()
    scanComplete = QtCore.pyqtSignal()

    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Project') )
        self.setSubTitle( T_('Pick from the available projects') )

        self.feedback = QtWidgets.QLabel( T_('Scanning for projects...') )

        # QQQ maybe use a table to allow for SCM and PATH columns?
        self.wc_list = QtWidgets.QListWidget()
        self.wc_list.setSelectionMode( self.wc_list.SingleSelection )
        self.wc_list.setSortingEnabled( True )
        self.wc_list.itemSelectionChanged.connect( self.__selectionChanged )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( self.feedback )
        layout.addWidget( self.wc_list )

        self.setLayout( layout )

        self.thread = None

        self.foundRepository.connect( self.__foundRepository, type=QtCore.Qt.QueuedConnection )
        self.scannedOneMoreFolder.connect( self.__setFeedback, type=QtCore.Qt.QueuedConnection )
        self.scanComplete.connect( self.__scanCompleted, type=QtCore.Qt.QueuedConnection )

        self.__all_labels_to_scm_info = {}

    def freeResources( self ):
        if self.thread is None:
            return

        self.thread.stop_scan = True
        self.thread.wait()
        self.thread = None

    def initializePage( self ):
        if self.wc_list.count() != 0:
            return

        self.thread = ScanForScmRepositoriesThread( self, self.wizard(), self.wizard().project_default_parent_folder )
        self.thread.start()

    def __foundRepository( self, scm_type, project_path ):
        project_path = pathlib.Path( project_path )
        if project_path not in self.wizard().all_existing_project_paths:
            label = '%s: %s' % (scm_type, project_path)
            self.__all_labels_to_scm_info[ label ] = (scm_type, project_path)
            QtWidgets.QListWidgetItem( label, self.wc_list )

        self.__setFeedback()

    def __setFeedback( self, complete=False ):
        if self.thread is None:
            return

        if self.thread.stop_scan:
            prefix = T_('Scan interrupted.')

        elif complete:
            prefix = T_('Scan completed.')

        else:
            prefix = T_('Scanning.')

        args = {'scanned': self.thread.num_folders_scanned
               ,'found': self.thread.num_scm_repos_found}

        fmt1 = S_( 'Found 1 project.',
                  'Found %(found)d projects.',
                 self.thread.num_scm_repos_found )

        fmt2 = S_( 'Scanned 1 folder.',
                  'Scanned %(scanned)d folders.',
                 self.thread.num_folders_scanned )

        self.feedback.setText( '%s %s %s' % (prefix, fmt1 % args, fmt2 % args) )

    def __selectionChanged( self ):
        self.completeChanged.emit()

    def __scanCompleted( self ):
        self.completeChanged.emit()

        self.__setFeedback( complete=True )

    def isComplete( self ):
        if self.thread is None or not self.thread.isRunning():
            self.feedback.setText( '' )

        all_selected_items = self.wc_list.selectedItems()
        return len(all_selected_items) == 1

    def nextId( self ):
        return self.wizard().page_id_name

    def validatePage( self ):
        all_selected_items = self.wc_list.selectedItems()

        label = all_selected_items[0].text()
        scm_type, project_path = self.__all_labels_to_scm_info[ label ]
        w = self.wizard()
        w.setScmType( scm_type )
        w.setAction( w.action_add_existing )
        w.setWcPath( project_path )

        self.freeResources()

        return True

class ScanForScmRepositoriesThread(QtCore.QThread):
    def __init__( self, page, wizard, project_default_parent_folder ):
        super().__init__()

        self.page = page
        self.wizard = wizard
        self.project_default_parent_folder = project_default_parent_folder

        self.num_folders_scanned = 0
        self.num_scm_repos_found = 0

        self.stop_scan = False

        self.folders_to_scan = [self.project_default_parent_folder]

    def run( self ):
        while len(self.folders_to_scan) > 0:
            if self.stop_scan:
                return

            self.page.scannedOneMoreFolder.emit()

            folder = self.folders_to_scan.pop( 0 )
            self.num_folders_scanned += 1

            try:
                for path in folder.iterdir():
                    if self.stop_scan:
                        return

                    if path.is_dir():
                        scm_type = self.wizard.detectScmTypeForFolder( path )
                        if scm_type is not None:
                            self.num_scm_repos_found += 1
                            self.page.foundRepository.emit( scm_type, str(path) )

                        else:
                            self.folders_to_scan.append( path )

            except PermissionError:
                # iterdir or is_dir can raise PermissionError
                # is the folder is inaccessable
                pass

        self.page.scanComplete.emit()

class PageAddProjectName(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setSubTitle( T_('Name the project') )

        self.feedback = QtWidgets.QLabel( '' )

        self.name = QtWidgets.QLineEdit( '' )
        self.name.textChanged.connect( self.__nameChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Project name') ), 0, 0 )
        layout.addWidget( self.name, 0, 1 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def initializePage( self ):
        w = self.wizard()

        factory = w.getScmFactory()
        self.setTitle( T_('Add %s Project') % (factory.scmPresentationShortName(),) )

        wc_path = w.getWcPath()

        self.name.setText( wc_path.name )

    def __nameChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        name = self.name.text().strip()

        if name.lower() in self.wizard().all_existing_project_names:
            self.feedback.setText( T_('Project name %s is already in use') % (name,) )
            return False

        return name != ''

    def nextId( self ):
        return -1

    def validatePage( self ):
        self.wizard().setProjectName( self.name.text().strip() )

        return True

#------------------------------------------------------------
class ProjectSettingsDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        self.app = app
        self.prefs_project = prefs_project
        self.scm_project= scm_project

        self.old_project_name = prefs_project.name

        prefs = self.app.prefs

        self.all_other_existing_project_names = set()

        for prefs_project in prefs.getAllProjects():
            if self.old_project_name != prefs_project.name:
                self.all_other_existing_project_names.add( prefs_project.name )

        super().__init__( parent )

        self.name = QtWidgets.QLineEdit( self.prefs_project.name )

        f = self.app.getScmFactory( self.prefs_project.scm_type )

        self.setWindowTitle( T_('Project settings for %s') % (self.prefs_project.name,) )

        self.addRow( T_('Name:'), self.name )
        self.addRow( T_('SCM Type:'), f.scmPresentationLongName() )
        self.addRow( T_('Path:'), str(self.prefs_project.path) )
        self.scmSpecificAddRows()
        self.addButtons()

        self.ok_button.setEnabled( False )
        self.name.textChanged.connect( self.enableOkButton )

        em = self.app.fontMetrics().width( 'm' )
        self.setMinimumWidth( 60*em )

    def scmSpecificAddRows( self ):
        pass

    def enableOkButton( self, text=None ):
        name = self.name.text().strip().lower()

        # need a name that is not blank, is different and not in use
        self.ok_button.setEnabled( (name != '' and
                                    name != self.old_project_name.lower() and
                                    name not in self.all_other_existing_project_names) or
                                    self.scmSpecificEnableOkButton() )

    def scmSpecificEnableOkButton( self ):
        return False

    def updateProject( self ):
        prefs = self.app.prefs

        # remove under the old name
        prefs.delProject( self.old_project_name )

        # add back in under the updated name
        self.prefs_project.name = self.name.text().strip()

        self.scmSpecificUpdateProject()

        prefs.addProject( self.prefs_project )

    def scmSpecificUpdateProject( self ):
        pass

if __name__ == '__main__':
    def T_(s):
        return s

    def S_(s, p, n):
        if n == 1:
            return s
        else:
            return p

    app = QtWidgets.QApplication( ['foo'] )

    wiz = WbScmAddProjectWizard( None )
    if wiz.exec_():
        print( 'SCM', wiz.getScmType() )
        print( 'Action', wiz.getAction() )
        print( 'url', wiz.getScmUrl() )
        print( 'name', wiz.getProjectName() )
        print( 'path', wiz.getWcPath() )

    else:
        print( 'Cancelled' )

    # force objects to be cleanup to avoid segv on exit
    del wiz
    del app
