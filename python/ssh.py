# -*- coding: utf-8 -*-
import paramiko
class SSHClient:
    def __init__(self, host, port, user, pkey):
        self.ssh_host = host
        self.ssh_port = port
        self.ssh_user = user
        self.private_key = paramiko.RSAKey.from_private_key_file(pkey)
        self.ssh = None
        self._connect()
    def _connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(hostname=self.ssh_host, port=self.ssh_port,username=self.ssh_user, pkey=self.private_key, timeout=10)
        except:
            return 'ssh connect fail'
    def execute_command(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(command)