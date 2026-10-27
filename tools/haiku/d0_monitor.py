# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bounded read-only D0 QMP queries. No arbitrary monitor command interface."""
import json
from pathlib import Path
import socket
import time

COMMANDS={'qtree':'info qtree','mtree':'info mtree -f','ramblock':'info ramblock'}


def snapshot(path):
    results={}
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(3);connection.connect(str(Path(path)))
        buffer=b'';total=0;end=time.monotonic()+10
        def receive(expected=None):
            nonlocal buffer,total
            for _ in range(100):
                while b'\n' not in buffer:
                    if time.monotonic()>end:raise RuntimeError('monitor deadline')
                    data=connection.recv(65536)
                    if not data:raise RuntimeError('monitor EOF')
                    total+=len(data);buffer+=data
                    if total>4*1024*1024 or len(buffer)>2*1024*1024:raise RuntimeError('monitor output bound')
                line,buffer=buffer.split(b'\n',1);value=json.loads(line)
                if not isinstance(value,dict):raise RuntimeError('monitor packet type')
                if expected is None:
                    if not isinstance(value,dict) or 'QMP' not in value:raise RuntimeError('monitor greeting')
                    return value
                if 'event' in value:continue
                if value.get('id')!=expected or 'error' in value or 'return' not in value:raise RuntimeError('monitor reply mismatch')
                return value['return']
            raise RuntimeError('too many monitor events')
        def send(command,sequence,arguments=None):
            value={'execute':command,'id':sequence}
            if arguments is not None:value['arguments']=arguments
            connection.sendall((json.dumps(value)+'\r\n').encode());return receive(sequence)
        receive();send('qmp_capabilities',1)
        status=send('query-status',2)
        if not isinstance(status,dict) or status.get('status')!='running' or status.get('running') is not True:
            raise RuntimeError('guest is not running at the evidence cutoff')
        for sequence,(name,command) in enumerate(COMMANDS.items(),3):
            value=send('human-monitor-command',sequence,{'command-line':command})
            if not isinstance(value,str) or not value or len(value)>1024*1024:raise RuntimeError('missing topology response')
            results[name]=value
    return results
