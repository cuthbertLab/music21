# -*- coding: utf-8 -*-
# index.py
# A simple script to test file uploading
# Each function is accessed via /FUNCTION_NAME
# Prompts for a file, then prints out the file's contents

from mod_python import apache

# Patch for music21 import
import re
import zipfile

import os
from cgitb import html
os.environ['HOME'] = '/Library/WebServer/Documents/featureextractor/tmp/'

import featureinfo

from music21 import *

##### 
# Output constants
CSV_OUTPUT_ID = 'csv'
ORANGE_OUTPUT_ID = 'orange'
ARFF_OUTPUT_ID = 'arff'

extractorTypeNames = [
["m21","Music21-specific Extractors"],
["M","Melody-based Extractors"],
["P","Pitch-based Extractors"],
["R","Rhythm-based Extractors"],
["D","Dynamics-based Extractors"],
["T","Texture-based Extractors"]]
#####

# Welcomes to page, provides options to use default file or upload file
def index(req):
    html = "<html><body><a href='uploadform'>Feature Extractors</a></body></html>"
    
    return html

# Displays the upload form
def uploadform(req):
    html = """
        <html >
        <head>
        <script>
        // Shows or hides the description of the given extractor by id
        function toggleDesc(id) {
            desc = document.getElementById(id+'desc');
            if(desc.style.display=='none') {
                desc.style.display = '';
            } else {
                desc.style.display = 'none';
            }
        }
        // Shows or hides listing of each type of extractor
        function toggleExtractors(typeId) {
            extractorDiv = document.getElementById(typeId+'extractors');
            button = document.getElementById(typeId+'button');
            if(extractorDiv.style.display=='none') {
                extractorDiv.style.display = '';
                button.innerHTML = '[-]';
            } else {
                extractorDiv.style.display = 'none';
                button.innerHTML = '[+]';
            }
        }
        // 
        // Checks or unchecks all extractors for a given typeId, status: 1=checked 0=unchecked
        function changeAll(typeId, status) {
            form = document.getElementById('uploadform');
            for(var i =0; i< form.elements.length; i++) {
                if(form.elements[i].getAttribute('extractortype') == typeId || typeId == 'all') {
                    if(status) {
                        form.elements[i].checked = "checked"
                    } else {
                        form.elements[i].checked = ""
                    }
                }
            }
            if(typeId == 'all' && status == 1) {
                showAllExtractors();
            } else if(typeId == 'all' && status == 0) {
                hideAllExtractors();
                //toggleExtractors('m21');
            }
        }
        //
        
        /// Shows all extractors
        function showAllExtractors() {
        """
    for typeInfo in extractorTypeNames:
        typeId = typeInfo[0]
        html += "document.getElementById('" + typeId + "extractors').style.display = '';\n"
    html += "document.getElementById('m21extractors').style.display = '';\n"
    html += """
        }
        
        /// Hides all extractors
        function hideAllExtractors() {
        """
    for typeInfo in extractorTypeNames:
        typeId = typeInfo[0]
        html += "document.getElementById('" + typeId + "extractors').style.display = 'none';\n"
    html += "document.getElementById('m21extractors').style.display = 'none';\n"
    html += """
        }
        
        var numextractors = 0
        var numvectors = 0
        function updateCounts(feature,value) {
            if(feature) {
                numextractors++;
                numvectors += value;
            } else {
                numextractors--;
                numvectors -= value;
            }
            document.getElementById('numextractors').innerHTML = numextractors;
            document.getElementById('numvectors').innerHTML = numvectors;
        }
        
        </script>
        </head>
        <body style='font-family:calibri' bgcolor='#EEE' onLoad="toggleExtractors('m21')">
        <table border=0 width='100%'>
        <tr><td align='center'>
        <table border=0 width='500px' cellpadding='10px' style='background-color:#FFF'>
        <tr><td align='left'>"""
    
    # Heading and description
    html += """ <h1>Music21 Feature Extraction:</h1>
        <a href='./'>Back</a>

        <hr />
        <p style='font-size:15'>Multiple Feature Extractors on Multiple Scores using Music21 - <br />
        Upload a .zip file containing musical scores. They can be of varying formats. music21 will convert and parse .xml, .md, .krn, .abc, .mid, and others.</p>
        """
    # form info
    html += """<form id='uploadform' action="processupload" method="POST" enctype="multipart/form-data" style='font-size:14'>"""
    
    # file upload
    html += """
        <hr />
        <input type="hidden" name="subUploadForm" value=1/>
        <span style='font-size:16'><b>File Selection: </b></span><input type="file" name="fileupload"/>
        <br />
        """
    
    # class value info
    html += """
        <hr />
        <span style='font-size:16'><b>Class Value: </b></span>
        <p>By default, the Class Value for each file is set to be the directory of the file in the zip archive (e.g. if identifying composers, the directories might be Bach, Beethoven, Unknown)
        <br />
        """
    
    # output format
    html += """
        <hr />
        <span style='font-size:16'><b>Output Format: </b></span>
        <select name="outputformat">"""

    html += "<option value='" + CSV_OUTPUT_ID + "'>CSV (Comma Separated Value List)</option>"
    html += "<option value='" + ORANGE_OUTPUT_ID + "'>Orange (Tab-Delimited for use with Orange)</option>"
    html += "<option value='" + ARFF_OUTPUT_ID + "'>ARFF (Attribute-Relation File Format)</option>"

    html += """
        </select>
        """
    
    # List native music21 extractors
    html += """
        <hr />
        <p style='font-size:16'><b>Select Feature Extractors:</b></p>
        <div style='padding-left:20px'>
        """
    html += "<span style='font-size:13'><b>Select: </b><a href=\"javascript:changeAll('all',1)\">All</a>&nbsp;&nbsp;<a href=\"javascript:changeAll('all',0)\">None</a></span><br />"
        
    # List Extractors
    for typeId, typeName in extractorTypeNames:
        html += "<p onClick=\"toggleExtractors('"+typeId+"')\"  style='font-size:15'><b>" + typeName +": <span id='" + typeId + "button'>[+]<span></b></p>\n"
        html += "<div id='"+typeId+"extractors' style='display:none; padding-left:10px'>\n"
        html += "<span style='font-size:13'><b>Select: </b><a href=\"javascript:changeAll('" + typeId + "',1)\">All</a>&nbsp;&nbsp;<a href=\"javascript:changeAll('" + typeId + "',0)\">None</a></span><br />\n"
        for extractor in featureinfo.featureInfo[typeId]:
            id = extractor[0]
            name = extractor[1]
            desc = extractor[2]
            dimensions = extractor[3]
            html += "<input type='checkbox' name='features' value='" + id +"' extractortype = '" + typeId + "' onchange='updateCounts(this.checked," + dimensions + ")'/>\n" 
            html += "<span onClick=toggleDesc('"+ id + "')>"+ name + "</span><br />\n"
            html += "<div style='font-size:12;display:none;padding-left:16px;margin-bottom:7px' id ='"+id + "desc'>\n"
            html += desc + "<br />(vectors output: " + dimensions + ") " + "<br /></div>\n"
        html += "</div>\n"
    html += "</div>\n"
    
    html += """<hr />
        <input type="submit" value="Process" onclick="this.value='Processing...';submit()">
        </form>
        </td></tr></table>
        </td></tr></table>
        </body></html>"""
    return html

# Called when file is uploaded
def processupload(req):
        
    # Check if form data is present. If not found, display error
    try:
        file = req.form['subUploadForm']
    except:
        html = """
            <html >
            <body style='font-family:calibri' bgcolor='#EEE' onLoad="toggleExtractors('m21')">
            <table border=0 width='100%'>
            <tr><td align='center'>
            <table border=0 width='500px' cellpadding='10px' style='background-color:#FFF'>
            <tr><td align='left'>
            <h1>Error:</h1>
            <p>Form information not found</p>
            <p><a href='uploadform'>Try Again</a></p>
            </td></tr></table>
            </td></tr></table>
            </body></html>
            """
        return html

    
    # Get file from POST
    uploadedFile = req.form['fileupload'].file
    filename = req.form['fileupload'].filename
    type = req.form['fileupload'].type

    # Check if filename is empty - display no file chosen error
    if filename == "":
        html = """
            <html >
            <body style='font-family:calibri' bgcolor='#EEE' onLoad="toggleExtractors('m21')">
            <table border=0 width='100%'>
            <tr><td align='center'>
            <table border=0 width='500px' cellpadding='10px' style='background-color:#FFF'>
            <tr><td align='left'>
            <h1>Music 21 Feature Extraction:</h1>
            <p><b>Error:</b> No file selected</p>
            <p><a href='uploadform'>Try Again</a></p>
            </td></tr></table>
            </td></tr></table>
            </body></html>
            """
        return html
    
    # Check if type is zip - display no file chosen error
    if type != "application/zip":
        html = """
            <html >
            <body style='font-family:calibri' bgcolor='#EEE' onLoad="toggleExtractors('m21')">
            <table border=0 width='100%'>
            <tr><td align='center'>
            <table border=0 width='500px' cellpadding='10px' style='background-color:#FFF'>
            <tr><td align='left'>
            <h1>Music 21 Feature Extraction:</h1>
            <p><b>Error:</b> File not in .zip format</p>
            <p><a href='uploadform'>Try Again</a></p>
            </td></tr></table>
            </td></tr></table>
            </body></html>
            """
        return html
        
    # Setup Feature Extractors and Data Set
    ds = features.DataSet(classLabel='Class')
    
    
    
    featureIDList = list()
    
    # Check if features selected. Else disp error
    try:
        file = req.form['features']
    except:
        html = """
            <html ><body>
            <h1>Error:</h1>
            <p>No extractors selected</p>
            <p><a href='uploadform'>try again</a></p>
            </body></html>
            """
        return html
    
    if req.form['features'] is not basestring:
        for id in req.form['features']:
            featureIDList.append(str(id))
    else:
        featureIDList.append(req.form['features'])
    
    fes = features.extractorsById(featureIDList)
    ds.addFeatureExtractors(fes)
    
    # Create ZipFile Object
    zipf = zipfile.ZipFile(uploadedFile, 'r')
    
    # Loop Through Files
    for scoreFileInfo in zipf.infolist():
        
        filePath = scoreFileInfo.filename
        
        # Skip Directories
        if(filePath.endswith('/')):
            continue
        scoreFile = zipf.open(filePath)
        
        # Use Music21's converter to parse file
        parsedFile = idAndParseFile(scoreFile,filePath)
        
        # If valid music21 format, add to data set
        if parsedFile is not None:
            
            # Split into directory structure and filname
            pathPartitioned = filePath.rpartition('/')
            directory = pathPartitioned[0]
            filename = pathPartitioned[2]
            
            if directory == "":
                directory = 'uncategorized'
            
            ds.addData(parsedFile,classValue=directory,id=filename)
            
    # Process data set
    ds.process()
    
    # Get output format from POST and set appropriate output:     
    outputFormatID = req.form['outputformat']
    if outputFormatID == CSV_OUTPUT_ID:
        output = features.OutputCSV(ds).getString()
    elif outputFormatID == ORANGE_OUTPUT_ID:
        output = features.OutputTabOrange(ds).getString()
    elif outputFormatID == ARFF_OUTPUT_ID:
        output = features.OutputARFF(ds).getString()
    else:
        output = "invalid output format"
       
    return output

# Takes in a file object and filename, identifies format, and returns parsed file:
def idAndParseFile(fileToParse,filename):
    matchedFormat = re.sub('^.*\.', '', filename)
    if matchedFormat == "":
        pass ### nice error...
    else:
        music21FormatName = common.findFormat(matchedFormat)[0]
        if music21FormatName is None:
            parsedFile = None
        else:
            parsedFile = converter.parse(fileToParse.read(),format=music21FormatName)
            
    return parsedFile

def test():
    return featureinfo.featureInfo['m21'][0][2]

def getFeatureInfo():
    output = "featureInfo = dict()\n"
    output += "featureInfo['m21']=[\n"
    feList = features.native.featureExtractors
    for feName in feList:
        if feName is None:
            continue
        fe = feName()
        output += "\t['" + fe.id + "','" + fe.name + "','" + fe.description + "','" + str(fe.dimensions) + "'],\n"
    output = output[:-2]
    output += "]\n"
    
    
    jsExtractorTypes = {
        "M":"Melody-based Extractors",
        "P":"Pitch-based Extractors",
        "R":"Rhythm-based Extractors",
        "D":"Dynamics-based Extractors",
        "T":"Texture-based Extractors"}
    # List jSymbolic Extractors
    for typeInfo in jsExtractorTypes:
        typeId = typeInfo[0]
        output += "featureInfo['" + typeId + "']=[\n"
        feList = features.jSymbolic.extractorsById[typeId]
        for feName in feList:
            if feName is None:
                continue
            fe = feName()
            output += "\t['" + fe.id + "','" + fe.name + "','" + fe.description + "','" + str(fe.dimensions) + "'],\n"
        output = output[:-2]
        output += "]\n"
    return output
