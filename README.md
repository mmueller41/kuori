# Kuori - A remote command shell for EalánOS

Kuori provides a commandline interface to manage cells in [EalánOS](https://github.com/mmueller41/genode.git).

## Supported commands
Currently it supports the following commands:
- creating a new cell from an XML configuration,
- destroying a running cell by a given name,
- show a list of all running cells

## Requirements
Kuori is written in Python and requires the following third-party libraries:
- [rich](https://github.com/Textualize/rich?tab=readme-ov-file), for printing nice statistics about habitats and cells.

## Usage
Currently, Kuori is just a simple python library. As such, it can be interactively used with ipython or integrated into python applications.

### Connecting to EalánOS
To connect to a running instance of EalánOS, you can use the following code
```
shell = kuori.Kuori(hostname, port)
```
where `hostname` and `port` refer to the hostname (or IP address) of the host running EalánOS and `port` to the TCP port that is used by the 
remote Kuori service. 

### Creating a new cell
In order to create a new cell you need to specify an XML file that matches the following example:
```xml
<start name="example">
    <binary name="example.elf"/>
        <resource name="RAM" quantum="200M"/>
        <config>
                <vfs> <dir name="dev">
                        <log/>
                        <inline name="rtc">2022-07-20 14:30</inline>
                        </dir>
                </vfs>
                <libc stdout="/dev/log" stderr="/dev/log" rtc="/dev/rtc"/>
        </config>
    <route>
        <service name="Timer"><child name="timer"/></service>
        <service name="Rtc"><child name="system_rtc"/></service>
                <service name="ROM" label_suffix=".lib.so"><parent/></service>
                <service name="ROM" label_last="allocating_cell"> <child name="cached_fs_rom"/></service>
                <any-service><parent/></any-service>
        </route>
</start>
```
. This will create a cell using the binary `example.elf` of the name `example` which may use up to 200 megabytes of memory. For a more detailed explanation of
the XML format, please, have a look at the documentation provided by the [Genode OS Framework](https://genode.org/).

In order to create the cell instance, you use the following command using Kuori after having connected to the remote instance (see above):
```python
shell.launch("example.xml")
```
where `example.xml` is the XML configfile for the cell to be launched.

### Destroying a cell
Destroying a cell can easily be accomplished by (using the example from before)
```python
shell.kill("example")
```
, where `example` is the name of the cell to destroy.

### Viewing a habitat
The command
```python
shell.list()
```
will give you a table of all running cells including their names, kind, assigned RAM quota and current CPU affinity.
