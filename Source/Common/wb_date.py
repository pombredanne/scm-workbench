#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_date.py

'''
import sys

#
#   pytz using pkg_resource but pkg_resource is not working
#   from py2app built application for macOS.
#
#   This hack works around the problem.
#   
if sys.platform == 'darwin':
    sys.modules['pkg_resources'] = sys.modules['wb_date']
    import zipfile
    import io

    def resource_stream( package_or_requirement, resource_name ):
        for path in sys.path:
            if path.endswith( '.zip' ):
                zip_filename = path
                break

        z = zipfile.ZipFile( zip_filename )
        resource_filename = '%s/%s' % (package_or_requirement, resource_name)
        resource = z.read( resource_filename )
        return io.BytesIO( resource )

import datetime
import pytz
import tzlocal


def utcDatetime( timestamp ):
    return pytz.utc.localize( datetime.datetime.utcfromtimestamp( timestamp ) )

def localDatetime( datetime_or_timestamp ):
    if type(datetime_or_timestamp) in (int, float):
        dt = utcDatetime( datetime_or_timestamp )
    else:
        dt = datetime_or_timestamp

    local_timezone = tzlocal.get_localzone()
    local_dt = dt.astimezone( local_timezone )
    return local_dt

if __name__ == '__main__':
    import time

    t = time.time()

    utc = utcDatetime( t )
    print( '   UTC: repr %r' % (utc,) )
    print( '   UTC:  str %s' % (utc,) )

    local = localDatetime( utc )
    print( 'Local1: repr %r' % (local,) )
    print( 'Local1:  str %s' % (local,) )

    local = localDatetime( t )
    print( 'Local2: repr %r' % (local,) )
    print( 'Local2:  str %s' % (local,) )
