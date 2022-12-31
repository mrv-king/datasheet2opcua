from PyPDF2 import PdfReader
  
datasheet = PdfReader("C:/Users/nikgal-local/OneDrive - ltu.se/Desktop/MAIN_FOLDER/PYTHON/OPC_UA/opcua_tree_builder/test/20.pdf")

interfaces = ["smbus", " i2c ", " spi ", " uart ", "smaart wire"]
ic_types = ["current meas", "temperature sensor", "humidity sensor", "voltage meas", "power meas", "inductive sens", " hall "]
ic_descriptions = ["CURRRENT", "TEMPERATURE", "HUMIDITY", "VOLTAGE", "POWER", "PROXIMITY", "MAGNETIC"]

def detect_ic_name_from_datasheet(datasheet, page_number):
    ic_name = ""
    page_reader = datasheet.pages[page_number]
    page = page_reader.extract_text()
    list_of_strings = page.split("\n")    
    list_of_strings = [x[x.rfind("The")+len("The"):] for x in list_of_strings if not x.find("The") == -1]
    list_of_strings = [x.replace(" ", "") for x in list_of_strings]
    list_of_strings = [x for x in list_of_strings if len(x)>0 and x[0].isupper()]
    list_of_strings = list_of_strings[0]
    accum = list_of_strings
    for x in accum:
        if (x.isupper() or x.isdigit() or x == "-"):
            ic_name = ic_name + x
        else:
            break
    return ic_name

def detect_ic_type_and_interface_from_datasheet(datasheet, interface_list, ic_types):
    accum_interface = []
    accum_type = []
    page = ""

    for i in range(0, len(datasheet.pages) - 1):
        page_reader = datasheet.pages[i]
        page = page + page_reader.extract_text().lower()

    for item in interface_list:
        if item in page:
            if page.count(item) >= 2:
                accum_interface.append(item)
    
    for i in range(0, len(ic_types)):
        if ic_types[i] in page:
            if page.count(ic_types[i]) >= 2:
                accum_type.append(ic_descriptions[i])

    if len(accum_interface) == 0:
        accum_interface.append("No Interface/Analog Output")

    if len(accum_type) == 0:
        resulting_ic_type = "UNKNOWN"
    elif len(accum_type) == 1:
        resulting_ic_type = accum_type[0] + " SENSOR"
    else:
        resulting_ic_type = ""
        for i in range (0, len(accum_type)):
            resulting_ic_type = resulting_ic_type+accum_type[i]+", "
        resulting_ic_type = resulting_ic_type[0:resulting_ic_type.rfind(",")] + " SENSOR"
    return resulting_ic_type, accum_interface

def detect_ic_partnumbers_from_datasheet(datasheet, ic_name):
    partnumber_list = []

    for i in range(round(len(datasheet.pages)/2), len(datasheet.pages) - 1):
        page_reader = datasheet.pages[i]
        page = page_reader.extract_text().lower()
        if "tape and reel" in page:
            list_of_strings = page.split("\n")
            partnumber_list.extend([x[:x.find(' ')].upper() for x in list_of_strings if x.find(ic_name[0:4].lower()) == 0]) 
    partnumber_list = list(dict.fromkeys(partnumber_list))
    return partnumber_list

def detect_operating_range_from_datasheet(datasheet, ic_name, partnumbers_list):
    operating_range = []

    for i in range(1, round(len(datasheet.pages)/3)):
        page_reader = datasheet.pages[i]
        page = page_reader.extract_text()
        if "Operating Ratings" in page or "Recommended Operating Conditions" in page:
            if "Operating Ratings" in page:
                operating_set = "Operating Ratings"
            else:
                operating_set = "Recommended Operating Conditions"
            page = page[page.find(operating_set) + len(operating_set):]
            list_of_strings = page.split("\n")
            operating_range.extend([x[:x.rfind("\N{DEGREE SIGN}")+2] for x in list_of_strings if not x.rfind(" \N{DEGREE SIGN}") == -1 and x.rfind(" \N{DEGREE SIGN}C/") == -1])

    operating_range = list(filter(None, operating_range))
    return operating_range

def detect_temperature_accuracy_error_from_datasheet(datasheet, page_number):
    accuracy_accum = []

    page_reader = datasheet.pages[page_number]
    page = page_reader.extract_text()
    list_of_strings = page.split("\n")

    for item in list_of_strings:
        if "\N{DEGREE SIGN}" in item.lower() and "±" in item.lower():
            accuracy_accum.append(item[:item.rfind("\N{DEGREE SIGN}")+2])

    return accuracy_accum

def detect_humidity_accuracy_error_from_datasheet(datasheet, page_number):
    accuracy_accum = []

    page_reader = datasheet.pages[page_number]
    page = page_reader.extract_text()
    list_of_strings = page.split("\n")

    for item in list_of_strings:
        if "accuracy" in item.lower() and "%" in item.lower():
            accuracy_accum.append(item.replace("•",""))
            break

    return accuracy_accum

def generate_xml_file(ic_name_local, ic_type_local, ic_interfaces_local, operating_range_local, ic_accuracy_local):
    f = open(ic_name_local+".xml", "w")
    f.write("""<?xml version="1.0" encoding="utf-8"?>
    <UANodeSet xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" Version="1.02" LastModified="2013-03-06T05:36:44.0862658Z" xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">"
    <UAObject NodeId="i=30001" BrowseName=\"""" + ic_name_local + """\">
        <Description>"""+ic_type_local+"""</Description>
        <References>
            <Reference ReferenceType="HasTypeDefinition">i=58</Reference>
            <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
        </References>
    </UAObject>

    <UAObject NodeId="i=30002" BrowseName="Interfaces">
        <DisplayName>Interfaces</DisplayName>
        <Description>"""+ic_name_local+""" Supported Interfaces </Description>
        <References>
            <Reference ReferenceType="Organizes" IsForward="false">i=30001</Reference>
            <Reference ReferenceType="HasTypeDefinition">i=58</Reference>
        </References>
    </UAObject>

    <UAVariable NodeId="i=30010" BrowseName="Supported Interfaces" DataType="String" AccessLevel="2" UserAccessLevel="2">
        <References>
            <Reference ReferenceType="HasTypeDefinition">i=68</Reference>
            <Reference ReferenceType="Organizes" IsForward="false">i=30002</Reference>
        </References>
        <Value>
            <String>"""+ ic_interfaces_local[0] +"""</String>
        </Value>
    </UAVariable>

    <UAObject NodeId="i=30003" BrowseName="Measurement Ranges">
        <DisplayName>Measurement Ranges</DisplayName>
        <Description>"""+ic_name_local+""" Measurement Ranges </Description>
        <References>
            <Reference ReferenceType="Organizes" IsForward="false">i=30001</Reference>
            <Reference ReferenceType="HasTypeDefinition">i=58</Reference>
        </References>
    </UAObject>

    <UAVariable NodeId="i=30011" BrowseName="Temperature Ranges" DataType="String" AccessLevel="2" UserAccessLevel="2">
        <References>
            <Reference ReferenceType="HasTypeDefinition">i=68</Reference>
            <Reference ReferenceType="Organizes" IsForward="false">i=30003</Reference>
        </References>
        <Value>
            <String>"""+ operating_range_local[0].replace("\N{DEGREE SIGN}","") +"""</String>
        </Value>
    </UAVariable>

    <UAObject NodeId="i=30004" BrowseName="Accuracy">
        <DisplayName>Accuracy</DisplayName>
        <Description>"""+ic_name_local+""" Measurement Accuracy </Description>
        <References>
            <Reference ReferenceType="Organizes" IsForward="false">i=30001</Reference>
            <Reference ReferenceType="HasTypeDefinition">i=58</Reference>
        </References>
    </UAObject>

    <UAVariable NodeId="i=30012" BrowseName="Temperature Ranges" DataType="String" AccessLevel="2" UserAccessLevel="2">
        <References>
            <Reference ReferenceType="HasTypeDefinition">i=68</Reference>
            <Reference ReferenceType="Organizes" IsForward="false">i=30004</Reference>
        </References>
        <Value>
            <String>"""+str(ic_accuracy_local[0].replace("±", "+/-" )).replace("\N{DEGREE SIGN}","")+""", """+str(ic_accuracy_local[1].replace("±", "+/-" )).replace("\N{DEGREE SIGN}","") +""", """+str(ic_accuracy_local[2].replace("±", "+/-" )).replace("\N{DEGREE SIGN}","") +""", """+str(ic_accuracy_local[3].replace("±", "+/-" )).replace("\N{DEGREE SIGN}","") +"""</String>
        </Value>
    </UAVariable>

    <UAObject NodeId="i=30005" BrowseName="Measurements">
        <DisplayName>Measurements</DisplayName>
        <Description>"""+ic_name_local+""" Measurements </Description>
        <References>
            <Reference ReferenceType="Organizes" IsForward="false">i=30001</Reference>
            <Reference ReferenceType="HasTypeDefinition">i=58</Reference>
        </References>
    </UAObject>

    <UAVariable NodeId="i=30013" BrowseName="Temperature" DataType="Int64" AccessLevel="2" UserAccessLevel="2">
        <References>
            <Reference ReferenceType="HasTypeDefinition">i=62</Reference>
            <Reference ReferenceType="Organizes" IsForward="false">i=30005</Reference>
        </References>
        <Value>
            <Int64>0</Int64>
        </Value>
    </UAVariable>

    </UANodeSet>
    """)
    f.close()

ic_name = detect_ic_name_from_datasheet(datasheet, 0)
partnumbers_list = detect_ic_partnumbers_from_datasheet(datasheet, ic_name)
operating_range = detect_operating_range_from_datasheet(datasheet, ic_name, partnumbers_list)
ic_type, ic_interfaces = detect_ic_type_and_interface_from_datasheet(datasheet, interfaces, ic_types)


print ("IC NAME: " + ic_name)
print (ic_type)
#print (partnumbers_list)
print ("OPERATING RANGE: ")
print (operating_range)
print ("SUPPORTED INTERFACES: ")
print (ic_interfaces)
if "TEMPERATURE" in ic_type:
    ic_temp_accuracy = detect_temperature_accuracy_error_from_datasheet(datasheet,0)
    print ("TEMPERATURE ACCURACY: ")
    print (ic_temp_accuracy)

if "HUMIDITY" in ic_type:
    ic_hum_accuracy = detect_humidity_accuracy_error_from_datasheet(datasheet,0)
    print ("HUMIDITY ACCURACY: ")
    print (ic_hum_accuracy)

#generate_xml_file(ic_name, ic_type, ic_interfaces, operating_range, ic_temp_accuracy)