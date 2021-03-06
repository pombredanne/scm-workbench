'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass_server_unix.py

'''
import sys
import os
import pathlib
import pwd
import stat
import threading
import tempfile
import time

#
#   attempts to use select.poll and select.select
#   failed becuase the fifo stayed readable after
#   the first message recieved.
#
#   after a select then read the fd should block!?
#


class WbGitAskPassServer(threading.Thread):
    fifo_name_client = '.ScmWorkbench.client'
    fifo_name_server = '.ScmWorkbench.server'

    def __init__( self, app, ui_component ):
        super().__init__()

        self.app = app
        self.ui_component = ui_component

        self.setDaemon( 1 )
        self.__run = True

        self.__reply_available = threading.Event()
        self.__reply_code = None
        self.__reply_value = None

    def shutdown( self ):
        self.__run = False

    def setReply( self, code, value ):
        self.__reply_code = code
        self.__reply_value = value

        self.__reply_available.set()

    def __waitForReply( self, prompt ):
        self.app.runInForeground( self.ui_component.getGitCredentials, (prompt,) )

        self.__reply_available.wait()
        self.__reply_available.clear()
        return self.__reply_code, self.__reply_value

    def run( self ):
        e = pwd.getpwuid( os.geteuid() )
        fifo_dir = pathlib.Path( tempfile.gettempdir() ) / e.pw_name

        try:
            fifo_dir.mkdir( mode=0o700, parents=True, exist_ok=True )

        except FileExistsError as e:
            self.app.log.error( 'Failed to create directory - %s' % (e,) )
            return

        client_fifo = fifo_dir / self.fifo_name_client
        server_fifo = fifo_dir / self.fifo_name_server

        try:
            for fifo_name in (client_fifo, server_fifo):
                make = True
                if fifo_name.exists():
                    if not fifo_name.is_fifo():
                        fifo_name.unlink()

                    elif fifo_name.stat().st_size == 0:
                        make = False

                    error_msg = 'failed to unlink fifo - %s'
                    fifo_name.unlink()

                error_msg = 'failed to make fifo - %s'
                os.mkfifo( str(fifo_name), stat.S_IRUSR|stat.S_IWUSR )

            error_msg = 'failed to open fifo - %s'
            fd_server = os.open( str(server_fifo), os.O_RDONLY|os.O_NONBLOCK )

        except IOError as e:
            self.app.log.error( error_msg % (e,) )
            return

        while self.__run:
            prompt = os.read( fd_server, 1024 )

            if len(prompt) > 0:
                prompt = prompt.decode( 'utf-8' )

                code, value = self.__waitForReply( prompt )

                reply = ('%d%s' % (code, value)).encode( 'utf-8' )

                try:
                    fd_client = os.open( str(client_fifo), os.O_WRONLY|os.O_NONBLOCK )

                except IOError as e:
                    self.app.log.error( 'Failed to open client fifo - %s' % (e,) )
                    continue

                size = os.write( fd_client, reply )
                if size != len(reply):
                    self.app.log.error( 'failed to write reply' )

                os.close( fd_client )

            else:
                time.sleep( 0.1 )

if __name__ == '__main__':
    class FakeApp:
        def __init__( self ):
            self.log = self

        def error( self, msg ):
            print( 'ERROR: %s' % (msg,) )

        def runInForeground( self, fn, args ):
            fn( *args )

    class FakeUiComponent():
        def __init__( self ):
            self.prompt_event = threading.Event()

        def getGitCredentials( self, prompt ):
            print( 'Prompt: %r' % (prompt,) )
            self.prompt_event.set()

    app = FakeApp()
    ui = FakeUiComponent()

    print( 'Create server' )
    server = WbGitAskPassServer( app, ui )
    print( 'Start server' )
    server.start()

    run = True
    while run:
        print( 'Wait for work' )
        ui.prompt_event.wait()
        ui.prompt_event.clear()

        sys.stdout.write( 'Reply: ',  )
        sys.stdout.flush()

        reply = sys.stdin.readline()
        if reply.startswith( 'q' ):
            run = False
            reply = '1quit'

        code = int(reply[0])
        value = reply[1:]

        server.setReply( code, value )

    print( 'Shutdown' )
    server.shutdown()

    print( 'Join' )
    server.join()

    print( 'Done' )
