'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_credential_dialogs.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_dialog_bases

class WbHgGetLoginDialog(wb_dialog_bases.WbDialog):
    def __init__( self, parent, url, realm ):
        super().__init__( parent )

        self.setWindowTitle( T_('Mercurial Credentials') )

        self.username = QtWidgets.QLineEdit( '' )
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        em = self.fontMetrics().width( 'M' )
        self.username.setMinimumWidth( 50*em )

        self.addRow( T_('URL'), url )
        self.addRow( T_('Realm'), realm )
        self.addRow( T_('Username'), self.username )
        self.addRow( T_('Password'), self.password )

        self.addButtons()

    def completeInit( self ):
        # set focus
        self.username.setFocus()


    def nameTextChanged( self, text ):
         self.ok_button.setEnabled( self.getUsername() != '' and self.getPassword() != '' )

    def getUsername( self ):
        return self.username.text().strip()

    def getPassword( self ):
        return self.password.text().strip()
