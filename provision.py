#!/usr/bin/python

import argparse
import os
import subprocess
import serial
import time

parser = argparse.ArgumentParser()
#define args
parser.add_argument('-s','--hostnames', help='list of acceptable hostnames', required=True)
parser.add_argument('-d','--devices', help='list of provisioned devices (to be written to)', required=True)


#parse args
args = parser.parse_args()


#open DB
failure = False
if os.path.isfile(args.hostnames)==False:
    print "Could not open '%s'"%args.hostnames
    failure=True
    
if os.path.isfile(args.devices)==False:
    print "Could not open '%s'"%args.devices
    failure=True
if failure:
    exit(-1)

print "Parsing Data Files.."
#open and parse hostnames and devices
hostnamesf = open(args.hostnames,"r")
devicesf = open(args.devices,"r+")

hostnames = hostnamesf.read().split("\n")
hostnames.remove("")
hostnamecount = len(hostnames)
devicelines = devicesf.read().split("\n")
devicelines.remove("")
devices=[]
#parse devices
for d in devicelines:
    if d.strip()=="":
        break
    e = d.split(" ")
    devices.append({'host':e[0],'mac':e[1],'ip':e[2]})

#Filter list by used hostnames
for d in devices:
    hostnames.remove(d['host'])

print "(%s) Devices"%len(devices)
print "(total:%s free:%s) HostNames"%(hostnamecount,len(hostnames))

#Extracted from arduino 
progline = "python esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 921600 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 80m --flash_size detect 0xe000 boot_app0.bin 0x1000 bootloader_qio_80m.bin 0x10000 WifiManagerExample.ino.ino.bin 0x8000 WifiManagerExample.ino.ino.partitions.bin"

res = subprocess.call(progline,shell=True)

if res!=0:
    print "Programming Error!"
    exit(-1)

time.sleep(3)
#open up serial port.
ser = serial.Serial("/dev/ttyUSB0",115200)
ser.readline() # discard first line

# Watch lines looking for ones that start with
# WIFIADDR- or MACADDR- and save everything
# after the - removing whitespace and newlines.
# read 10 lines before giving up

timeout = 0
wifi = ""
mac  = ""
while True:
    time.sleep(1)
    line = ser.readline()
    print ".",
    p = line.split("-")
    if p[0]=='WIFIADDR':
        wifi = p[1].strip()
    if p[0]=='MACADDR':
        mac = p[1].strip()
    if mac!="" and wifi!="":
        break
    if timeout>10:
        print "Timeout Waiting for data from device!"
        exit(-3)
        break
    timeout += 1

print "MAC:%s\tWIFI:%s"%(mac,wifi)

if len(hostnames)==0:
    print "Error, Out of usable hostnames"
    exit(-1)

for d in devices:
    if d['mac']==mac:
        print "Error: Device already has a hostname!"
        exit(-1)

hostname = hostnames.pop()
print "Assigning %s to %s" %(hostname,mac)
devicesf.write("%s %s %s\n"%(hostname,mac,wifi))
devicesf.close()
exit(0)
#dev = {'host':hostname,'mac':mac,'ip':wifi}
#devices.append(dev)


#write out dev


