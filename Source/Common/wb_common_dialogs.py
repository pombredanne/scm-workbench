'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_common_dialogs.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_platform_specific

import wb_dialog_bases

class WbRenameFilenameDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Rename') )

        self.old_name = None

        self.name = QtWidgets.QLineEdit()
        self.name.textChanged.connect( self.nameTextChanged )

        self.ok_button.setEnabled( False )

        self.addRow( T_('Name'), self.name )
        self.addButtons()

    def nameTextChanged( self, text ):
         self.ok_button.setEnabled( self.getName() != self.old_name )

    def setName( self, name ):
        self.old_name = name
        self.name.setText( self.old_name )

        # assume that the whole of the name is replaced leaving the type suffixes
        if '.' in name:
            self.name.setSelection( 0, name.index( '.' ) )

        else:
            self.name.selectAll()

    def getName( self ):
        return self.name.text().strip()


class WbNewFolderDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, parent_folder ):
        self.app = app

        self.parent_folder = parent_folder

        super().__init__( parent )

        self.setWindowTitle( T_('New Folder') )

        self.name = QtWidgets.QLineEdit()
        self.name.textChanged.connect( self.nameTextChanged )

        self.addRow( T_('Folder Name'), self.name )
        self.addButtons()

    def nameTextChanged( self, text ):
        folder_name = self.getFolderName()
        name_set = set( folder_name )
        enable = True
        if folder_name == '':
            enable = False

        if wb_platform_specific.isInvalidFilename( folder_name ):
            enable = False

        abs_folder_name = self.parent_folder /folder_name
        if abs_folder_name.exists():
            enable = False

        self.ok_button.setEnabled( enable )

    def getFolderName( self ):
        return self.name.text().strip()

def WbAreYouSureDelete( parent, all_filenames ):
    return __WbAreYouSure( parent, T_('Confirm Delete'), T_('Are you sure you wish to delete:'), all_filenames )

def WbAreYouSureRevert( parent, all_filenames ):
    return __WbAreYouSure( parent, T_('Confirm Revert'), T_('Are you sure you wish to revert:'), all_filenames )

def __WbAreYouSure( parent, title, question, all_filenames ):
    default_button = QtWidgets.QMessageBox.No

    all_parts = [question]
    all_parts.extend( [str(filename) for filename in all_filenames] )

    message = '\n'.join( all_parts )

    rc = QtWidgets.QMessageBox.question( parent, title, message, defaultButton=default_button )
    return rc == QtWidgets.QMessageBox.Yes

if __name__ == '__main__':
    def T_(s):
        return s

    def S_(s, p, n):
        if n == 1:
            return s
        else:
            return p

    app = QtWidgets.QApplication( ['foo'] )

    rename = WbRenameFilenameDialog( None, None )
    rename.setName( 'fred.txt' )
    if rename.exec_():
        print( rename.getName() )

    del rename
    del app
