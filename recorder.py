#!/usr/bin/python3.2
# -*- coding: utf-8 -*-
import os, sys, datetime

# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("Sources"))
from yocto_api import *
from yocto_display import *

KEYFILE = "/media/usb/autoload.txt"
DATADIR = "/media/usb/"

BUFFER_LAYER = 1
INFO_LAYER = 2
MEASURE_LAYER = 3

epoch = datetime.datetime(1970, 1, 1)
td1sec = datetime.timedelta(seconds=1)

# Update date/time on mini display
def downloadData(startDate, endDate):
    global display, layer
    startStamp = (startDate - epoch) / td1sec
    endStamp = (endDate - epoch) / td1sec
    if display is not None:
        # Display "loading" banner
        layer.clear()
        layer.drawText(48, 0, YDisplayLayer.ALIGN.TOP_CENTER, 'Loading since '+startDate.strftime("%Y-%m-%d"))
        layer.drawRect(0, 9, 95, 15)
        display.swapLayerContent(BUFFER_LAYER, INFO_LAYER)
        player = display.get_displayLayer(INFO_LAYER)
    datasets = {}
    progress = {}
    # Load data from datalogger, with a global progress bar
    sensor = YSensor.FirstSensor()
    while sensor:
        name = sensor.get_logicalName()
        if name != '':
            dataset = sensor.get_recordedData(startStamp,endStamp)
            res = dataset.loadMore()
            if res < 100: progress[name] = res
            datasets[name] = dataset
        sensor = sensor.nextSensor()
    if display is not None:
        # update progress bar...
        player.drawBar(1,10,2,14)
    done = 0
    prev = 1
    for key in progress:
        print("loading from data logger: "+key)
        res = 0
        while res < 100:
            # load one piece of data
            res = datasets[key].loadMore()
            if display is not None:
                # update progress bar...
                ratio = (100*done + res) / (100*len(progress))
                next = round(3+93*ratio)
                if next > prev:
                    player.drawBar(prev, 10, next, 14)
                    prev = next
        done += 1
    # Determine file name using first named sensor device
    filename = ''
    sensor = YSensor.FirstSensor()
    while sensor:
        if sensor.get_logicalName() != '':
            filename = sensor.get_module().get_logicalName()
            if filename != '': break
        sensor = sensor.nextSensor()
    if filename == '':
        filename = 'unnamed.csv'
    else:
        filename += '.csv'
    print("Saving to "+filename)
    if display is not None:
        # Display "saving" banner
        layer.clear()
        layer.drawText(48, 0, YDisplayLayer.ALIGN.TOP_CENTER, 'Creating '+filename+' on USB')
        layer.drawRect(0, 9, 95, 15)
        display.swapLayerContent(BUFFER_LAYER, INFO_LAYER)
    # Compute list of available measure timestamps
    timeFmt = "%Y-%m-%d %H:%M:%S.%f"
    index = {}
    measures = {}
    timestamps = []
    line = "time"
    for key in datasets:
        line += ","+key
        index[key] = 0
        measures[key] = datasets[key].get_measures()
        for measure in measures[key]:
            timestamps.append(measure.get_startTimeUTC())
    timestamps = list(set(timestamps))
    timestamps.sort()
    # Save data in CSV format
    print("Creating file "+DATADIR+filename)
    f = open(DATADIR+filename,"w")
    f.write(line+'\n')
    done = 0
    prev = 0
    if len(timestamps) == 0:
        inc = 95
    else:
        inc = 95 / len(timestamps)
    for stamp in timestamps:
        # write one line of data
        line = datetime.datetime.fromtimestamp(stamp).strftime(timeFmt)[:-4]
        for key in datasets:
            idx = index[key]
            if idx < len(measures[key]):
                meas = measures[key][idx]
                while meas.get_startTimeUTC() < stamp:
                    idx += 1
                    meas = measures[key][idx]
                if meas.get_startTimeUTC() == stamp:
                    line += ","+str(meas.get_averageValue())
                    index[key] = idx + 1
                else:
                    line += ","
            else:
                line += ","
        f.write(line + '\n')
        if display is not None:
            # update progress bar
            done += inc
            next = round(done)
            if next > prev:
                player.drawBar(prev, 10, next, 14)
                prev = next
    f.close()
    # Free memory used by all measures loaded
    sensor = YSensor.FirstSensor()
    while sensor:
        sensor._clearDataStreamCache()
        sensor = sensor.nextSensor()

# Update date/time on mini display
def showTime():
    global display, layer
    date = datetime.datetime.today().strftime("%Y-%m-%d")
    time = datetime.datetime.today().strftime("%H:%M:%S")
    layer.clear()
    layer.drawText(0, 0, YDisplayLayer.ALIGN.TOP_LEFT, date)
    layer.drawText(69, 0, YDisplayLayer.ALIGN.TOP_LEFT, time)
    display.swapLayerContent(BUFFER_LAYER, INFO_LAYER)

# Log and display new measures
def functionValueChangeCallback(fct, value):
    global display, layer
    info = fct.get_userData()
    infoTxt = info['name'] + ": " + value + " " + info['unit']
    print(infoTxt)
    if display is not None:
        # Update measure on mini display
        layer.clear()
        layer.drawText(0, 16, YDisplayLayer.ALIGN.BOTTOM_LEFT, infoTxt)
        display.swapLayerContent(BUFFER_LAYER, MEASURE_LAYER)

# Handle USB sensor plug
def deviceArrival(m):
    global display, layer
    serial = m.get_serialNumber()
    print('Device connected : ' + serial)
    # check if a display has just been connected
    fctcount = m.functionCount()
    for i in range(fctcount):
        if m.functionId(i) == 'display':
            print('Display connected')
            display = YDisplay.FindDisplay(serial+'.display')
            display.resetAll()
            layer = display.get_displayLayer(BUFFER_LAYER)
            layer.hide()
    # enumerate sensor functions for the connected device
    sensor = YSensor.FirstSensor()
    while sensor:
        if sensor.get_module().get_serialNumber() == serial:
            functionId = sensor.get_functionId()
            name = sensor.get_logicalName()
            # only register functions with a specific logical name
            if name != '':
                print('- using ' + name + '(' + functionId + ')')
                sensor.set_userData({'name': name, 'unit': sensor.get_unit()})
                sensor.registerValueCallback(functionValueChangeCallback)
            else:
                print('- ' + functionId + ' ignored (no name defined)')
        sensor = sensor.nextSensor()

# Handle USB sensor unplug
def deviceRemoval(m):
    global display
    print('Device disconnected: ' + m.get_serialNumber())
    if display is not None:
        if not display.isOnline():
            print('Display disconnected')
            display = None

errmsg = YRefParam()

# No exception please
YAPI.DisableExceptions()

# Setup the API to use local USB devices
if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
    sys.exit("Init error: " + errmsg.value)

YAPI.RegisterDeviceArrivalCallback(deviceArrival)
YAPI.RegisterDeviceRemovalCallback(deviceRemoval)

# Search for the display
display = YDisplay.FirstDisplay()
if display is not None:
    display.resetAll()
    layer = display.get_displayLayer(BUFFER_LAYER)
    layer.hide()

while True:
    # Handle plug/unplug events
    YAPI.UpdateDeviceList(errmsg)
    # Check if an USB key os plugged in to load data
    if os.path.isfile(KEYFILE):
        f = open(KEYFILE,"r")
        dateRange = f.read().strip().split()
        f.close()
        startDate = datetime.datetime.strptime(dateRange[0], "%Y-%m-%d")
        if len(dateRange) > 1:
            endDate = datetime.datetime.strptime(dateRange[1], "%Y-%m-%d")
            print("Loading data from " + startDate.strftime("%Y-%m-%d") + " to " + endDate.strftime("%Y-%m-%d"))
        else:
            endDate = datetime.datetime.today()
            print("Loading data from " + startDate.strftime("%Y-%m-%d"))
        # Stop displaying measures
        if display is not None:
            display.get_displayLayer(MEASURE_LAYER).hide()
        # Download data
        downloadData(startDate, endDate)
        if display is not None:
            # Display completion banner
            layer.clear()
            layer.drawText(48, 0, YDisplayLayer.ALIGN.TOP_CENTER, 'You can remove the USB disk')
            display.swapLayerContent(1, INFO_LAYER)
            # Wait for USB key removal
            while os.path.isfile(KEYFILE):
                YAPI.UpdateDeviceList(errmsg)
                YAPI.Sleep(1000, errmsg)
            YAPI.UpdateDeviceList(errmsg)
            if display is not None and display.isOnline:
                display.get_displayLayer(MEASURE_LAYER).unhide()
    else:
        if display is not None:
            showTime()
    # Handle other types of events
    YAPI.Sleep(1000, errmsg)
