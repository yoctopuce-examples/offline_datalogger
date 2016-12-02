# Logging and retrieving measures without network access

Even in the Internet of Things era, there are automation and measuring applications that require to work in a completely autonomous way, without any network connection of any kind. This example shows how to implement a system based on Yoctopuce sensors and built-in datalogger that does not require any network connection but uses a USB key to retrieve the data.

## Prerequisite

This script only makes sense when the computer to which the sensors are connected has a valid date and time set. If the system does not have network access, that means the computer must have a real time clock (RTC). For our tests, we used a SolidRun CuBox-i2eX mini-PC. 

This system is intended to work with [Yoctopuce sensors](https://www.yoctopuce.com/EN/productcategories.php).

## Principle

The scenario is the following: 

Normally, the Yoctopuce sensor registers the measures internally. The computer is used only to provide the exact time to the sensor for a correct time stamp.

From time to time, an operator comes to retrieve the data with a USB key. The USB key contains a file indicating the time period for which we want to retrieve the measures. The operator connects the key and can check, with a mini USB screen [Yocto-MiniDisplay](https://www.yoctopuce.com/EN/products/usb-displays/yocto-minidisplay), that the transfer is performed as planned. The data are stored in a CSV file with a name specific to the saved sensor. The operator is informed when it is possible to remove the USB key.
![Schema](https://www.yoctopuce.com/pubarchive/2016-12/offline-datalogger-schema_1.png)

## Implementation

To easily detect when a USB key is connected, you must install the usbmount package with the command: 

sudo apt-get install usbmount

Thanks to this, the USB key magically appears under /media/usb when it is connected. We ask the operator to create on the key a text file called autoload.txt, which simply contains the date from which the data must be retrieved, in the YYYY-MM-DD format. Every second, the Python program checks if this file appears under /media/usb and if it is the case, the data retrieval process is triggered. 

Reading the data is performed one sensor after another, using the get_recordedData() method. As this operation can be time consuming, we display a global progress bar on the Yocto-MiniDisplay while downloading the data of all the sensors, using the mini-display drawing primitives. 

To fit all the data returned by all the sensors in a single CSV table, we must take into account that all the sensors may not be recording measures at the same rate. So we start by establishing the list of all the timestamps found among the logged measures, we sort it, and we then generate the CSV file with a distinct line for each timestamp, checking for each sensor whether it has a measure for this specific time. If not, the cell is left empty. 

The file is written line by line, again with a global progress bar. At the end, a message asks the operator to remove the key. usbmount standard settings guarantee that the data are written on the USB disk without delay, so that no manual operation should be required before disconnecting the key. 

Full description: [See Yoctopuce blog](https://www.yoctopuce.com/EN/article/logging-and-retrieving-measures-without-network-access)
