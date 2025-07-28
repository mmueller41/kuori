import xml.etree.ElementTree as ET
import sys
import socket
from rich.console import Console
from rich.table import Table
from rich import box
from rich.syntax import Syntax

class Connection:
    accept = 0
    issue = 1
    failed = 2
    success = 3
    wait = 4

    def __init__(self, hostname, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hostname = hostname
        self.port = port
        self.sock.connect((hostname, port))

    def issue_command(self, command, length):
        encoded_command = int.to_bytes(command, 8, 'little')
        encoded_length = int.to_bytes(length, 4, 'little')
        self.sock.send(encoded_command + encoded_length)

    def send_argument(self, argument):
        self.sock.send(argument)

    def recv_response_header(self):
        response_header = self.sock.recv(12)
        command = int.from_bytes(response_header[0:3], 'little')
        state = int.from_bytes(response_header[4:7], 'little')
        length = int.from_bytes(response_header[8:11], 'little')
       

        return (command, state, length)

    def recv_response(self, command):
        c, state, length = self.recv_response_header()

        data = bytearray()
        while len(data) < length:
            packet = self.sock.recv(length - len(data))
            if not packet:
                return None
            data.extend(packet)
        return bytes(data)
        

class Kuori:
    commands = {'begin': 0, 'commit': 1, 'acknowledge': 2}

    def __init__(self, hostname, port):
        self.conn = Connection(hostname, port)
    
    def begin(self):
        self.conn.issue_command(self.commands['begin'], 1)
        raw_cfg = self.conn.recv_response(self.commands['acknowledge'])

        return ET.fromstring(raw_cfg.decode('UTF-8'))

    def commit(self, config):
        self.conn.issue_command(self.commands['commit'], len(ET.tostring(config)))
        self.conn.send_argument(ET.tostring(config))

    def launch(self, start_file):
        start_cfg = ET.ElementTree(file=start_file)
        start_node = start_cfg.getroot()

        config = self.begin()
        config.append(start_node)
        self.commit(config)

    def kill(self, name):
        config = self.begin()

        for node in config.findall('.//start[@name="%s"]'%name):
            config.remove(node)

        self.commit(config)

    def find_start_node(self, name):
        config = self.begin()

        for node in config.findall('.//start[@name="%s"'%name):
            return node

    def list(self):
        config = self.begin()
       
        habitat = config.find(".//affinity-space")
        habitat_dimensions = "%s × %s"%(habitat.get('width'), habitat.get('height'))

        console = Console()
        table = Table(title="Habitat dimensions: %s"%(habitat_dimensions), show_header=True, header_style="bold", box=box.HORIZONTALS)
        table.add_column("Name", style="cyan")
        table.add_column("Binary", style="yellow")
        table.add_column("RAM quota", justify="right", style="blue")
        table.add_column("Brick?")
        table.add_column("Affinity", style="white")

        for node in config.findall('.//start'):
            name = node.get('name')
            brick = node.get('brick')
            if brick:
                is_brick = "[green]%s[/green]"%brick
            else:
                is_brick = "[red]no[/red]"
            
            ram = node.find('.//resource[@name="RAM"]')
            ram_quota = ram.get('quantum')

            affinity = ""
            if node.find('.//affinity') is None:
                affinity = "[italic magenta]dynamic[/italic magenta]"
            else:
                x = node.find('.//affinity').get('xpos')
                y = node.find('.//affinity').get('ypos')
                w = node.find('.//affinity').get('width')
                h = node.find('.//affinity').get('height')
                affinity = "[bright_magenta](%s×%s)@(%s,%s)[/bright_magenta]"%(w,h,x,y)
            
            binary = ""
            if not node.find('.//binary'):
                binary = node.get('name')
            else:
                binary = node.find(".//binary").get("name")

            table.add_row(
                    name,
                    binary,
                    ram_quota,
                    is_brick,
                    affinity
            )
        console.print(table)

    def print_config(self):
        cfg = self.begin()
        xml = ET.tostring(cfg).decode("UTF-8")
        syntax = Syntax(xml, "xml")
        console = Console()
        console.print(syntax)
