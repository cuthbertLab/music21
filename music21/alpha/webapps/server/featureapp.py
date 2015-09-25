# -*- coding: utf-8 -*-
'''
An interface for music21 using mod_wsgi

To use, first install mod_wsgi and include it in the HTTPD.conf file.

Add this file to the server, ideally not in the document root, 
on mac this could be /Library/WebServer/wsgi-scripts/zipfileapp.py

Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
Note: unlike with mod_python, the end of the URL does not determine which function is called,
WSGIScriptAlias always calls application.

WSGIScriptAlias /music21/zipfileinterface /Library/WebServer/wsgi-scripts/zipfileapp.py

Further down the conf file, give the webserver access to this directory:

<Directory "/Library/WebServer/wsgi-scripts">
    Order allow,deny
    Allow from all
</Directory>

The mod_wsgi handler will call the application function below with the request
content in the environ variable.

To use the application, send a POST request to WEBSERVER:/music21interface
where the contents of the POST is a POST from a form containing a zip file.

'''

from music21 import common
from music21 import converter
from music21 import features

import zipfile
import cgi
import re
#

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

def music21ModWSGIFeatureApplication(environ, start_response):
    '''
    Music21 webapp to demonstrate processing of a zip file containing scores.
    Will be moved and integrated into __init__.py upon developing a standardized URL format
    as application that can perform variety of commands on user-uploaded files
    '''
    status = '200 OK'

    pathInfo = environ['PATH_INFO'] # Contents of path after mount point of wsgi app but before question mark

    if pathInfo == '/uploadForm':
        output = getUploadForm()
        response_headers = [('Content-type', 'text/html'),
            ('Content-Length', str(len(output)))]

        start_response(status, response_headers)
    
    
        return [output]


    #command = pathInfo

    formFields = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
                
    # Check if form data is present. If not found, display error
    try:
        unused_subUploadFormFile = formFields['subUploadForm']
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
            <p><a href='/music21/featureapp/uploadForm'>Try Again</a></p>
            </td></tr></table>
            </td></tr></table>
            </body></html>
            """
        response_headers = [('Content-type', 'text/html'),
            ('Content-Length', str(len(html)))]

        start_response(status, response_headers)
    
    
        return [html]

    
    # Get file from POST
    uploadedFile = formFields['fileupload'].file
    filename = formFields['fileupload'].filename
    
    uploadType = formFields['fileupload'].type

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
            <p><a href='/music21/featureapp/uploadForm'>Try Again</a></p>
            </td></tr></table>
            </td></tr></table>
            </body></html>
            """
        response_headers = [('Content-type', 'text/html'),
            ('Content-Length', str(len(html)))]

        start_response(status, response_headers)
    
    
        return [html]

    
    # Check if uploadType is zip - display no file chosen error
    if uploadType != "application/zip":
        html = """
            <html >
            <body style='font-family:calibri' bgcolor='#EEE' onLoad="toggleExtractors('m21')">
            <table border=0 width='100%'>
            <tr><td align='center'>
            <table border=0 width='500px' cellpadding='10px' style='background-color:#FFF'>
            <tr><td align='left'>
            <h1>Music 21 Feature Extraction:</h1>
            <p><b>Error:</b> File not in .zip format</p>
            <p><a href='/music21/featureapp/uploadForm'>Try Again</a></p>
            </td></tr></table>
            </td></tr></table>
            </body></html>
            """
        response_headers = [('Content-type', 'text/html'),
            ('Content-Length', str(len(html)))]

        start_response(status, response_headers)
    
    
        return [html]

        
    # Setup Feature Extractors and Data Set
    ds = features.DataSet(classLabel='Class')
    
    
    
    featureIDList = list()
    
    # Check if features have been selected. Else display error
    try:
        unused_featureFile = formFields['features']
    except:
        html = """
            <html ><body>
            <h1>Error:</h1>
            <p>No extractors selected</p>
            <p><a href='/music21/featureapp/uploadForm'>try again</a></p>
            </body></html>
            """
        return html
    
    if common.isIterable(formFields['features']):
        print(formFields['features'])
        for featureId in formFields['features']:
            featureIDList.append(str(featureId.value))
    else:
        featureIDList.append(formFields['features'].value)
    
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
    outputFormatID = formFields['outputformat'].value
    if outputFormatID == CSV_OUTPUT_ID:
        output = features.OutputCSV(ds).getString()
    elif outputFormatID == ORANGE_OUTPUT_ID:
        output = features.OutputTabOrange(ds).getString()
    elif outputFormatID == ARFF_OUTPUT_ID:
        output = features.OutputARFF(ds).getString()
    else:
        output = "invalid output format"
       
    response_headers = [('Content-type', 'text/plain'),
            ('Content-Length', str(len(output)))]

    start_response(status, response_headers)


    return [output]

application = music21ModWSGIFeatureApplication
    
def idAndParseFile(fileToParse,filename):
    '''Takes in a file object and filename, identifies format, and returns parsed file'''
    matchedFormat = re.sub(r'^.*\.', '', filename)
    if matchedFormat == "":
        pass
    else:
        music21FormatName = common.findFormat(matchedFormat)[0]
        if music21FormatName is None:
            parsedFile = None
        else:
            parsedFile = converter.parse(fileToParse.read(),format=music21FormatName)
            
    return parsedFile

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


def getUploadForm():
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
            form = document.getElementById('/uploadForm');
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
        <body style='font-family:calibri' bgcolor='#CCC' onLoad="toggleExtractors('m21')">
        <table border=0 width='100%'>
        <tr><td align='center'>
        <table border=0 width='500px' cellpadding='10px' style='background-color:#FFF'>
        <tr><td align='left'>"""
    
    # Heading and description
    html += """ <h1><span style="font-family:'Courier New', Courier, monospace">music21</span> Feature Extraction:</h1>
        <a href='/music21/webapps/client'>Back</a>

        <hr />
        <p style='font-size:15'>Multiple Feature Extractors on Multiple Scores using Music21 - <br />
        Upload a .zip file containing musical scores. They can be of varying formats. music21 will convert and parse .xml, .md, .krn, .abc, .mid, and others.</p>
        """
    # form info
    html += """<form id='/uploadForm' action="/music21/featureapp" method="POST" enctype="multipart/form-data" style='font-size:14'>"""
    
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
        for extractor in featureInfo[typeId]:
            featureId = extractor[0]
            name = extractor[1]
            desc = extractor[2]
            dimensions = extractor[3]
            html += "<input type='checkbox' name='features' value='" + featureId +"' extractortype = '" + typeId + "' onchange='updateCounts(this.checked," + dimensions + ")'/>\n" 
            html += "<span onClick=toggleDesc('"+ featureId + "')>"+ name + "</span><br />\n"
            html += "<div style='font-size:12;display:none;padding-left:16px;margin-bottom:7px' id ='" + featureId + "desc'>\n"
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


featureInfo = dict()
featureInfo['m21']=[
    ['P22','Quality','Set to 0 if the key signature indicates that a recording is major, set to 1 if it indicates that it is minor and set to 0 if key signature is unknown. Music21 addition: if no key mode is found in the piece, analyze the piece to discover what mode it is most likely in.','1'],
    ['QL1','Unique Note Quarter Lengths','The number of unique note quarter lengths.','1'],
    ['QL2','Most Common Note Quarter Length','The value of the most common quarter length.','1'],
    ['QL3','Most Common Note Quarter Length Prevalence','Fraction of notes that have the most common quarter length.','1'],
    ['QL4','Range of Note Quarter Lengths','Difference between the longest and shortest quarter lengths.','1'],
    ['CS1','Unique Pitch Class Set Simultaneities','Number of unique pitch class simultaneities.','1'],
    ['CS2','Unique Set Class Simultaneities','Number of unique set class simultaneities.','1'],
    ['CS3','Most Common Pitch Class Set Simultaneity Prevalence','Fraction of all pitch class simultaneities that are the most common simultaneity.','1'],
    ['CS4','Most Common Set Class Simultaneity Prevalence','Fraction of all set class simultaneities that are the most common simultaneity.','1'],
    ['CS5','Major Triad Simultaneity Prevalence','Percentage of all simultaneities that are major triads.','1'],
    ['CS6','Minor Triad Simultaneity Prevalence','Percentage of all simultaneities that are minor triads.','1'],
    ['CS7','Dominant Seventh Simultaneity Prevalence','Percentage of all simultaneities that are dominant seventh.','1'],
    ['CS8','Diminished Triad Simultaneity Prevalence','Percentage of all simultaneities that are diminished triads.','1'],
    ['CS9','Triad Simultaneity Prevalence','Proportion of all simultaneities that form triads.','1'],
    ['CS10','Diminished Seventh Simultaneity Prevalence','Percentage of all simultaneities that are diminished seventh chords.','1'],
    ['CS11','Incorrectly Spelled Triad Prevalence','Percentage of all triads that are spelled incorrectly.','1'],
    ['MD1','Composer Popularity','Composer popularity today, as measured by the number of Google search results (log-10).','1'],
    ['MC1','Ends With Landini Melodic Contour','Boolean that indicates the presence of a Landini-like cadential figure in one or more parts.','1'],
    ['TX1','Language Feature','Languge of the lyrics of the piece given as a numeric value from text.LanguageDetector.mostLikelyLanguageNumeric().','1']]
featureInfo['P']=[
    ['P1','Most Common Pitch Prevalence','Fraction of Note Ons corresponding to the most common pitch.','1'],
    ['P2','Most Common Pitch Class Prevalence','Fraction of Note Ons corresponding to the most common pitch class.','1'],
    ['P3','Relative Strength of Top Pitches','The frequency of the 2nd most common pitch divided by the frequency of the most common pitch.','1'],
    ['P4','Relative Strength of Top Pitch Classes','The frequency of the 2nd most common pitch class divided by the frequency of the most common pitch class.','1'],
    ['P5','Interval Between Strongest Pitches','Absolute value of the difference between the pitches of the two most common MIDI pitches.','1'],
    ['P6','Interval Between Strongest Pitch Classes','Absolute value of the difference between the pitch classes of the two most common MIDI pitch classes.','1'],
    ['P7','Number of Common Pitches','Number of pitches that account individually for at least 9% of all notes.','1'],
    ['P8','Pitch Variety','Number of pitches used at least once.','1'],
    ['P9','Pitch Class Variety','Number of pitch classes used at least once.','1'],
    ['P10','Range','Difference between highest and lowest pitches.','1'],
    ['P11','Most Common Pitch','Bin label of the most common pitch divided by the number of possible pitches.','1'],
    ['P12','Primary Register','Average MIDI pitch.','1'],
    ['P13','Importance of Bass Register','Fraction of Note Ons between MIDI pitches 0 and 54.','1'],
    ['P14','Importance of Middle Register','Fraction of Note Ons between MIDI pitches 55 and 72.','1'],
    ['P15','Importance of High Register','Fraction of Note Ons between MIDI pitches 73 and 127.','1'],
    ['P16','Most Common Pitch Class','Bin label of the most common pitch class.','1'],
    ['P17','Dominant Spread','Largest number of consecutive pitch classes separated by perfect 5ths that accounted for at least 9% each of the notes.','1'],
    ['P18','Strong Tonal Centres','Number of peaks in the fifths pitch histogram that each account for at least 9% of all Note Ons.','1'],
    ['P19','Basic Pitch Histogram','A features array with bins corresponding to the values of the basic pitch histogram.','128'],
    ['P20','Pitch Class Distribution','A feature array with 12 entries where the first holds the frequency of the bin of the pitch class histogram with the highest frequency, and the following entries holding the successive bins of the histogram, wrapping around if necessary.','12'],
    ['P21','Fifths Pitch Histogram','A feature array with bins corresponding to the values of the 5ths pitch class histogram.','12'],
    ['P22','Quality','Set to 0 if the key signature indicates that a recording is major, set to 1 if it indicates that it is minor and set to 0 if key signature is unknown.','1'],
    ['P23','Glissando Prevalence','Number of Note Ons that have at least one MIDI Pitch Bend associated with them divided by total number of pitched Note Ons.','1'],
    ['P24','Average Range Of Glissandos','Average range of MIDI Pitch Bends, where "range" is defined as the greatest value of the absolute difference between 64 and the second data byte of all MIDI Pitch Bend messages falling between the Note On and Note Off messages of any note.','1'],
    ['P25','Vibrato Prevalence','Number of notes for which Pitch Bend messages change direction at least twice divided by total number of notes that have Pitch Bend messages associated with them.','1']]
featureInfo['R']=[
    ['R1','Strongest Rhythmic Pulse','Bin label of the beat bin with the highest frequency.','1'],
    ['R2','Second Strongest Rhythmic Pulse','Bin label of the beat bin of the peak with the second highest frequency.','1'],
    ['R3','Harmonicity of Two Strongest Rhythmic Pulses','The bin label of the higher (in terms of bin label) of the two beat bins of the peaks with the highest frequency divided by the bin label of the lower.','1'],
    ['R4','Strength of Strongest Rhythmic Pulse','Frequency of the beat bin with the highest frequency.','1'],
    ['R5','Strength of Second Strongest Rhythmic Pulse','Frequency of the beat bin of the peak with the second highest frequency.','1'],
    ['R6','Strength Ratio of Two Strongest Rhythmic Pulses','The frequency of the higher (in terms of frequency) of the two beat bins corresponding to the peaks with the highest frequency divided by the frequency of the lower.','1'],
    ['R7','Combined Strength of Two Strongest Rhythmic Pulses','The sum of the frequencies of the two beat bins of the peaks with the highest frequencies.','1'],
    ['R8','Number of Strong Pulses','Number of beat peaks with normalized frequencies over 0.1.','1'],
    ['R9','Number of Moderate Pulses','Number of beat peaks with normalized frequencies over 0.01.','1'],
    ['R10','Number of Relatively Strong Pulses','Number of beat peaks with frequencies at least 30% as high as the frequency of the bin with the highest frequency.','1'],
    ['R11','Rhythmic Looseness','Average width of beat histogram peaks (in beats per minute). Width is measured for all peaks with frequencies at least 30% as high as the highest peak, and is defined by the distance between the points on the peak in question that are 30% of the height of the peak.','1'],
    ['R12','Polyrhythms','Number of beat peaks with frequencies at least 30% of the highest frequency whose bin labels are not integer multiples or factors (using only multipliers of 1, 2, 3, 4, 6 and 8) (with an accepted error of +/- 3 bins) of the bin label of the peak with the highest frequency. This number is then divided by the total number of beat bins with frequencies over 30% of the highest frequency.','1'],
    ['R13','Rhythmic Variability','Standard deviation of the bin values (except the first 40 empty ones).','1'],
    ['R14','Beat Histogram','A feature array with entries corresponding to the frequency values of each of the bins of the beat histogram (except the first 40 empty ones).','161'],
    ['R15','Note Density','Average number of notes per second.','1'],
    ['R17','Average Note Duration','Average duration of notes in seconds.','1'],
    ['R18','Variability of Note Duration','Standard deviation of note durations in seconds.','1'],
    ['R19','Maximum Note Duration','Duration of the longest note (in seconds).','1'],
    ['R20','Minimum Note Duration','Duration of the shortest note (in seconds).','1'],
    ['R21','Staccato Incidence','Number of notes with durations of less than a 10th of a second divided by the total number of notes in the recording.','1'],
    ['R22','Average Time Between Attacks','Average time in seconds between Note On events (regardless of channel).','1'],
    ['R23','Variability of Time Between Attacks','Standard deviation of the times, in seconds, between Note On events (regardless of channel).','1'],
    ['R24','Average Time Between Attacks For Each Voice','Average of average times in seconds between Note On events on individual channels that contain at least one note.','1'],
    ['R25','Average Variability of Time Between Attacks For Each Voice','Average standard deviation, in seconds, of time between Note On events on individual channels that contain at least one note.','1'],
    ['R30','Initial Tempo','Tempo in beats per minute at the start of the recording.','1'],
    ['R31','Initial Time Signature','A feature array with two elements. The first is the numerator of the first occurring time signature and the second is the denominator of the first occurring time signature. Both are set to 0 if no time signature is present.','2'],
    ['R32','Compound Or Simple Meter','Set to 1 if the initial meter is compound (numerator of time signature is greater than or equal to 6 and is evenly divisible by 3) and to 0 if it is simple (if the above condition is not fulfilled).','1'],
    ['R33','Triple Meter','Set to 1 if numerator of initial time signature is 3, set to 0 otherwise.','1'],
    ['R34','Quintuple Meter','Set to 1 if numerator of initial time signature is 5, set to 0 otherwise.','1'],
    ['R35','Changes of Meter','Set to 1 if the time signature is changed one or more times during the recording','1']]
featureInfo['M']=[
    ['M1','Melodic Interval Histogram','A features array with bins corresponding to the values of the melodic interval histogram.','128'],
    ['M2','Average Melodic Interval','Average melodic interval (in semi-tones).','1'],
    ['M3','Most Common Melodic Interval','Melodic interval with the highest frequency.','1'],
    ['M4','Distance Between Most Common Melodic Intervals','Absolute value of the difference between the most common melodic interval and the second most common melodic interval.','1'],
    ['M5','Most Common Melodic Interval Prevalence','Fraction of melodic intervals that belong to the most common interval.','1'],
    ['M6','Relative Strength of Most Common Intervals','Fraction of melodic intervals that belong to the second most common interval divided by the fraction of melodic intervals belonging to the most common interval.','1'],
    ['M7','Number of Common Melodic Intervals','Number of melodic intervals that represent at least 9% of all melodic intervals.','1'],
    ['M8','Amount of Arpeggiation','Fraction of horizontal intervals that are repeated notes, minor thirds, major thirds, perfect fifths, minor sevenths, major sevenths, octaves, minor tenths or major tenths.','1'],
    ['M9','Repeated Notes','Fraction of notes that are repeated melodically.','1'],
    ['m10','Chromatic Motion','Fraction of melodic intervals corresponding to a semi-tone.','1'],
    ['M11','Stepwise Motion','Fraction of melodic intervals that corresponded to a minor or major second.','1'],
    ['M12','Melodic Thirds','Fraction of melodic intervals that are major or minor thirds.','1'],
    ['M13','Melodic Fifths','Fraction of melodic intervals that are perfect fifths.','1'],
    ['M14','Melodic Tritones','Fraction of melodic intervals that are tritones.','1'],
    ['M15','Melodic Octaves','Fraction of melodic intervals that are octaves.','1'],
    ['m17','Direction of Motion','Fraction of melodic intervals that are rising rather than falling.','1'],
    ['M18','Duration of Melodic Arcs','Average number of notes that separate melodic peaks and troughs in any channel.','1'],
    ['M19','Size of Melodic Arcs','Average melodic interval separating the top note of melodic peaks and the bottom note of melodic troughs.','1']]
featureInfo['D']=[
    ['D1','Overall Dynamic Range','The maximum loudness minus the minimum loudness value.','1'],
    ['D2','Variation of Dynamics','Standard deviation of loudness levels of all notes.','1'],
    ['D3','Variation of Dynamics In Each Voice','The average of the standard deviations of loudness levels within each channel that contains at least one note.','1'],
    ['D4','Average Note To Note Dynamics Change','Average change of loudness from one note to the next note in the same channel (in MIDI velocity units).','1']]
featureInfo['T']=[
    ['T1','Maximum Number of Independent Voices','Maximum number of different channels in which notes have sounded simultaneously. Here, Parts are treated as channels.','1'],
    ['T2','Average Number of Independent Voices','Average number of different channels in which notes have sounded simultaneously. Rests are not included in this calculation. Here, Parts are treated as voices','1'],
    ['T3','Variability of Number of Independent Voices','Standard deviation of number of different channels in which notes have sounded simultaneously. Rests are not included in this calculation.','1'],
    ['T4','Voice Equality - Number of Notes','Standard deviation of the total number of Note Ons in each channel that contains at least one note.','1'],
    ['T5','Voice Equality - Note Duration','Standard deviation of the total duration of notes in seconds in each channel that contains at least one note.','1'],
    ['T6','Voice Equality - Dynamics','Standard deviation of the average volume of notes in each channel that contains at least one note.','1'],
    ['T7','Voice Equality - Melodic Leaps','Standard deviation of the average melodic leap in MIDI pitches for each channel that contains at least one note.','1'],
    ['T8','Voice Equality - Range','Standard deviation of the differences between the highest and lowest pitches in each channel that contains at least one note.','1'],
    ['T9','Importance of Loudest Voice','Difference between the average loudness of the loudest channel and the average loudness of the other channels that contain at least one note.','1'],
    ['T10','Relative Range of Loudest Voice','Difference between the highest note and the lowest note played in the channel with the highest average loudness divided by the difference between the highest note and the lowest note overall in the piece.','1'],
    ['T12','Range of Highest Line','Difference between the highest note and the lowest note played in the channel with the highest average pitch divided by the difference between the highest note and the lowest note in the piece.','1'],
    ['T13','Relative Note Density of Highest Line','Number of Note Ons in the channel with the highest average pitch divided by the average number of Note Ons in all channels that contain at least one note.','1'],
    ['T15','Melodic Intervals in Lowest Line','Average melodic interval in semitones of the channel with the lowest average pitch divided by the average melodic interval of all channels that contain at least two notes.','1'],
    ['T20','Voice Separation','Average separation in semi-tones between the average pitches of consecutive channels (after sorting based/non average pitch) that contain at least one note.','1']]

