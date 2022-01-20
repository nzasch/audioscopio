import csv
import alsaaudio

import math
import struct
import array
import time
import scipy.spatial
import numpy
import argparse
import os
import Tkinter


#################################
# config #

L_ear_pos = (-10,0,0)
R_ear_pos = (10,0,0)

samplerate = 22050
soundspeed = 5000
framesize = 1024

sourcesfile = 'sources.csv'

keys = ["w", "a", "s", "d", "f", "g"]
#################################

def key(event):
    if event.char == event.keysym:
        msg = 'Key %r' % event.char
        label1.config(text=msg)
        if (event.char == 'q'):
            print 'bye!'
            stop()
        try:
            try:
                source_num = int(event.char)
            except ValueError:
                if event.char in keys:
                    source_num = keys.index(event.char)
            print str(source_num) + " pressed"
            if(source_num < len(args.source) ):
                if (enabled[source_num] == "disabled"):
                    enabled[source_num] = args.source[source_num]
                    print str(args.source[source_num]) + " enabled"
                    stop()
                    start()
        except ValueError:
            return False

        
def keyrelease(event):
    try:
        source_num = int(event.char)
    except ValueError:
        if event.char in keys:
            source_num = keys.index(event.char)
    print str(source_num) + " released"
    if(source_num < len(args.source) ):
        enabled[source_num] = "disabled"
        print str(args.source[source_num]) + " disabled"
        # reload
        stop()
        start()
                                                      

# x, y, z, freq, amp

def ISL(amplitude,distance):
    amplitude = amplitude / (4 * math.pi * math.pow(distance,2))
    return amplitude;

def parsefile(sfile):
    global source
    global sources
    global num_sources
    
    with open(sfile, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='|')
        print "enabled: "+str(enabled)
        for row in reader: 
            print "processing "+row['name']
            source = numpy.zeros((1, 2, 4))
            
            source[0][0][0] = float(row['freq'])/samplerate
            source[0][1][0] = float(row['freq'])/samplerate
            
            distance_L = scipy.spatial.distance.euclidean(numpy.array(map(float, (row['x'], row['y'], row['z']))),L_ear_pos)
            distance_R = scipy.spatial.distance.euclidean(numpy.array(map(float, (row['x'], row['y'], row['z']))),R_ear_pos)
            print 'distance: ' + str(distance_L) + ',' + str(distance_R)
            
            if (not enabled or any(row['name'] in s for s in enabled)):
                source[0][0][2] = ISL(float(row['amp']),distance_L)
                source[0][1][2] = ISL(float(row['amp']),distance_R)
            else:
                print "not processing " + row['name']
                source[0][0][2] = 0
                source[0][1][2] = 0

            source[0][0][3] = distance_L/soundspeed
            source[0][1][3] = distance_R/soundspeed
            
            print 'source:\n [%s]' % ', '.join(map(str, source))
            
            try:
                sources = numpy.concatenate((sources, source), axis=0)
            except ValueError:
                    sources = source
                    
                    
        if (sources  != None):
            num_sources = len(sources)
        else:
            num_sources = 0
        print str(num_sources) + " sorgenti\n"

# genera buffer
def buffer_populate():
    samplebuffer = []
    for x in range(0, framesize):
        sources[:,:,1] += sources[:,:,0]
        samplebuffer.extend(numpy.sum(numpy.sin(sources[:,:,1] + sources[:,:,3]) * sources[:,:,2], axis=0))
    data = struct.pack(format, *samplebuffer)
    return (data)

def start():
    global go
    go = 1
    parsefile(sourcesfile)
    while go:
        indata = buffer_populate()
        out.write(indata)
        root.update()
                
def stop():
    global go
    global num_sources
    global sources
    num_sources = 0
    sources = None
    go = 0

# variabili
go = 0
source = []
sources = None
num_sources = 0
format = '%sf' % 2*framesize
    
# parsa argomenti
parser = argparse.ArgumentParser(description='Play sines defined in ' + sourcesfile)
parser.add_argument('source', metavar='source', nargs='*', help='source id')
args = parser.parse_args()
enabled = list(args.source)

# grafica
print "turn on GUI"
root = Tkinter.Tk()
prompt = 'in key'
label1 = Tkinter.Label(root, text=prompt, width=len(prompt), bg='yellow')
label1.pack()
root.bind_all('<Key>', key)
root.bind_all("<KeyRelease>", keyrelease)
os.system('xset r on')

## alsaaudio
print "turn on audio"
out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK)
out.setchannels(2)
out.setrate(samplerate)
out.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
out.setperiodsize(framesize)

# spegne autorepeat
os.system("xset r off")

# fai
print "start\n"
start()

# ripristina
os.system("xset r on")
