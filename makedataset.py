'''
Converts several datasets from World Bank into Mirador format

@copyright: Fathom Information Design 2014
'''

import sys, os, csv, codecs, shutil, math
import collections
from xml.dom.minidom import parseString
from sets import Set

def write_xml_line(line, xml_file, xml_strings):
    ascii_line = ''.join(char for char in line if ord(char) < 128)
    if len(ascii_line) < len(line):
        print "  Warning: non-ASCII character found in line: '" + line.encode('ascii', 'ignore') + "'"
    xml_file.write(ascii_line + '\n')
    xml_strings.append(ascii_line + '\n')

def init_dataset(survey_year, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Remove binary file, just in case
    if os.path.isfile(output_folder + "data.bin"):
        os.remove(output_folder + "data.bin")

    # Creating Mirador configuration file
    template_config = "config.mira"
    project_config = output_folder + "/config.mira"

    template_file = open(template_config, 'r')
    project_file = open(project_config, 'w')
    lines = template_file.readlines()
    for line in lines:
        line = line.strip()
        if line == "project.title=":
            line = line + "Behavioral Risk Factor Surveillance System Data " + survey_year
        project_file.write(line + '\n') 
    template_file.close()
    project_file.close()

def is_number(str):
    try:
        float(str)
        return True
    except ValueError:
        return False

def set_var_type(name, lbounds, ubounds, values, var_types, var_ranges):
    categorical = True
    catlock = False
    empty_values = False
    for i in range(0, len(lbounds)):
        lbound = lbounds[i]
        ubound = ubounds[i]
        value = values[i]        
        if lbound == "BLANK" or lbound == "HIDDEN": continue
        if i == 0 and value and not ubound:
            catlock = True
        if not value:
            empty_values = True
        if not catlock and is_number(lbound) and is_number(ubound): categorical = False
            
    if categorical:
        categories = collections.OrderedDict() 
        for i in range(0, len(lbounds)):
            lbound = lbounds[i]
            ubound = ubounds[i]
            value = values[i]
            if lbound == "BLANK" or lbound == "HIDDEN": continue 
            if value and (not empty_values or i > 0):
                categories[lbound] = value
            else:   
                categories[lbound] = lbound                
        if categories:        
            range_str = ""
            for cod in categories:
                if range_str: range_str = range_str + ";"
                range_str = range_str + cod + ":" + categories[cod]            
            var_types[name] = 'category'
            var_ranges[name] = range_str
#             print "Variable",name,"is categorical",range_str
    else:
        min_value = 1E9
        max_value = 0
        special_values = collections.OrderedDict()
        for i in range(0, len(lbounds)):
            lbound = lbounds[i]
            ubound = ubounds[i]
            value = values[i]
            if lbound == "BLANK" or lbound == "HIDDEN": continue 
            if lbound and ubound and is_number(lbound) and is_number(ubound):
                min_value = min(min_value, float(lbound))
                max_value = max(max_value, float(ubound))
            elif lbound and value:
                special_values[lbound] = value
        if min_value < max_value:
            range_str = str(int(math.floor(min_value))) + "," + str(int(math.ceil(max_value)))
            for cod in special_values:
                range_str = range_str + ";" + cod + ":" + special_values[cod]
            var_ranges[name] = range_str

def load_metadata(data_file, var_file, code_file, var_names, var_titles, var_types, var_ranges, var_groups):
    print "Loading metadata..."
    reader = csv.reader(open(data_file, "r"), dialect="excel")
    var_names.extend(reader.next())
    for name in var_names:
        var_types[name] = 'int'
        var_ranges[name] = '0,100000'

    reader = csv.reader(open(var_file, "rU"), dialect="excel")
    reader.next()
    for row in reader:
        grp_name = row[1].replace("&", "and")
        tbl_name = row[2].replace("&", "and")        
        tbl_index = int(row[3])
        var_index = int(row[4])
        var_name = row[5]
        var_title = row[6]
        
        if var_name in var_names:        
            if grp_name in var_groups:
                group = var_groups[grp_name]
            else:
                group = collections.OrderedDict()
                var_groups[grp_name] = group

            if tbl_name in group:
                table = group[tbl_name]
            else:
                table = []
                group[tbl_name] = table
            
            table.append(var_name)
            var_titles[var_name] = var_title
                 
    reader = csv.reader(open(code_file, "rU"), dialect="excel")
    reader.next()
    name0 = ""
    lbounds = []
    ubounds = []
    values = []    
    for row in reader:
        name = row[5]
        lbound = row[8]
        ubound = row[9]
        value = row[10]
                
        if name in var_names:
            if name0 != name and lbounds:
                set_var_type(name0, lbounds, ubounds, values, var_types, var_ranges)  
                lbounds = []
                ubounds = []
                values = []
                
            lbounds.append(row[8])
            ubounds.append(row[9])
            values.append(''.join(char for char in row[10] if ord(char) < 128))
            name0 = name

    if name0 and lbounds:
        set_var_type(name0, lbounds, ubounds, values, var_types, var_ranges)  

    print "Done"
        
def load_data(data_file, var_names, var_types, data):
    print "Loading data..."
    reader = csv.reader(open(data_file, "r"), dialect="excel")
    reader.next()
    for row0 in reader:
        row1 = []
        index = 0
        for val0 in row0:
            if val0 == '':
                val1 = missing_str
            else:
                name = var_names[index]                
                try:
                    fval = float(val0)
                    if var_types[name] == 'int' and not fval.is_integer():
                        var_types[name] = 'float'
                        print 'variable',name,'is float'
                    val1 = val0                
                except ValueError:
                    val1 = missing_str                 
            row1.append(val1) 
            index = index + 1
            
        data.append(row1)
    print "Done"
    
def save_groups(filename, var_groups):
    print "Saving groups..."
    # Writing file in utf-8 because the input html files from
    # NHANES website sometimes have characters output the ASCII range.
    xml_file = codecs.open(filename, 'w', 'utf-8')
    xml_strings = []
    write_xml_line('<?xml version="1.0"?>', xml_file, xml_strings)
    write_xml_line('<data>', xml_file, xml_strings)
    for gname in var_groups:
        write_xml_line(' <group name="' + gname + '">', xml_file, xml_strings)
        group = var_groups[gname]
        for tname in group:             
            write_xml_line('  <table name="' + tname + '">', xml_file, xml_strings)
            table = group[tname]
            for var in table:
                write_xml_line('   <variable name="' + var + '"/>', xml_file, xml_strings)
            write_xml_line('  </table>', xml_file, xml_strings)
        write_xml_line(' </group>', xml_file, xml_strings)
    write_xml_line('</data>', xml_file, xml_strings)
    xml_file.close()

    # XML validation.
    try:
        doc = parseString(''.join(xml_strings))
        doc.toxml()
        print "Done."
    except:
        sys.stderr.write("XML validation error:\n")
        raise      
    
##########################################################################################    

source_folder = "Survey/"
missing_str = "\\N"
survey_year = "2011"
output_folder = "mirador/" + survey_year

var_names = []
var_titles = {}
var_types = {}
var_ranges = {}
var_groups = collections.OrderedDict()
data = []

data_file = source_folder + "BRFS" + survey_year + ".csv"
var_file = source_folder + "varlist-" + survey_year + ".csv"
code_file = source_folder + "codebook-" + survey_year + ".csv"

init_dataset(survey_year, output_folder)
load_metadata(data_file, var_file, code_file, var_names, var_titles, var_types, var_ranges, var_groups);


save_dictionary(output_folder + "/dictionary.tsv", var_names, var_titles, var_types, var_ranges)
save_groups(output_folder + "/groups.xml", var_groups)

sys.exit(1)

load_data(data_file, var_names, var_types, data);



# load_dictionary(source_folder + "varlist-" + survey_year + ".csv", var_names, dictionary);





