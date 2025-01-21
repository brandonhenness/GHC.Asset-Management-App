# Notes to AMS script maintainers:
#   1) Global variable names are ALL UPPERCASE and should start with AMS_:
#      > config.VERSION -- reported in menu headers; this is the AMS script version
#      > config.LIVE_DATABASE -- directs AMS to use the live SQL database (True) or the test DB (False)
#      > config.VERBOSE_ERROR -- prints verbose AMS feedback; this is enabled, if you use the test DB
#      > SCRIPT_FILEPATH -- the fully qualified name of the AMS script
#      > SCRIPT_DIRECTORY -- the AMS script directory; the agreements / schedules / templates / reports files are relative to this directory
#      > AMS_WEBKIT_AVAILABLE -- used in generate_pdf.py; this blocks PDF generation (and prevents AMS crashes) if WebKit is not locally installed
#      > 
#      > 
# ==========
#   2) The reports either write to (when importing data) or write to .CSV files
#      a) CSV stands for 'comma separated variables'
#         1) ANy ISBN needs to be formatted, when you open and/or edit a file. 

### Here's how to format ISBN numbers:

#      b) Import scripts run through the CSV file one line at a time. If there is an error on line #10,
#         then lines #11 and later WILL NOT RUN. Find and fix the error on line #10, then re-run the
#         import report. Although lines #1 to #9 are already imported, it does no damage to overwrite the
#         database data with an exact copy of the existing data; in fact, import reports are useful to
#         update and/or correct data in the database.
#      c) The "File Open" dialog   **suggests**   a CSV filename for the report input or output.
#         It is perfectly OK (and wise) to create a CSV file with a different name and/or in another
#         directory. These files are an examples (which were originally lost, found, and then then imported):
#            > "T:\Business Reference Library Room 1222\import_books_details_Oct_2024.csv"
#            > "T:\Business Reference Library Room 1222\import_books_Oct_2024.csv"
# ==========
#   3) Reports control variables (for config.VERSION >= 1.5.0)
#      > AMS_import --------- whether this is a SQL import query (True) or an SQL export or report (False, the default); this controls whether the .CSV file is read as input or written as output
#      > AMS_insert_tables -- all SQL tables used in an INSERT script; this is used to query the database for (non-) nullable columns and SQL column types
#      > AMS_nullable ------- a list of SQL table columns which  MIGHT  have a 'Null' value; this script queries the database for this information; empty CSV file fields are treated as NULL
#      > AMS_notnull -------- a list of SQL table columns which MAY NOT have a 'Null' value; this script queries the database for this information; empty CSV file fields are treated as ''
#      > AMS_coltypes ------- a dictionary of SQL table columns and their data types; this script queries the database for this information
# NOTE: Errors are reported whenever any two tables in 'AMS_insert_tables' have the same column name (e.g. 'asset_id') but different nullable properties or SQL data types.
#      > AMS_coltypes_overrides -- a dictionary of SQL table columns and their data types; this script queries the database for this information
#      > AMS_returning ------ this overrides the default of reporting the first SELECT-ed column (e.g. handle "SELECT entity_id, doc_number FROM incarcerated ... RETURNING doc_number" with "AMS_returning = 'doc_number'")
#      > 
#      > 
#       Option #7 on the AMS main menu, "Run a SQL report" includes an embedded
#       DSL (a domain-specific language, which is, essentially, a self-authored
#       configuration / scripting scheme). This DSL alters how this script
#       (main.py) parses the .SQL files in the 'reports' subdirectory and
#       applies variable substitutions and SQL argument quoting. These
#       "extensions" are coded as SQL comments, starting in the first column,
#       like this example:
#          -- :defaults => { 'AMS_import': True, 'AMS_insert_tables': [ 'assets', 'laptops' ] }
#       All comments starting with '---' or which are preceeded by SQL syntax
#       (incl. any tabs or spaces) are ignored.

#       Embedded directives (e.g. 'AMS_import') which are intended to influence
#       this Python script's execution are prefixed with AMS_ to not trip up  SQL query semantics. This code is commented,
#       but there is no user's manual -- because it's quicker to change code than to document
#       it (and DSL documentation gets out of date very easily).
# ==========
#   4) View Transaction History by DOC Number (option 8, then 2)
#      This query would be EVEN MORE useful, if it also summarized the issued_assets
#      and issued_accessories for the selected DOC / Incarcerated ... Thanks in advance!

# wrap all these imports in try/except, so we can report the error, pause, and exit
try:

    from typing import Iterator, List, Tuple, Union
    import psycopg2
    import psycopg2.extras
    import pandas as pd
    import csv # for csv.DictReader
    import tkinter as tk
    from enum import Enum
    from tkinter import filedialog
    from ctypes import windll
    import os
    import sys
    import platform
    import re # for pattern matching and removing whitespace
    import signature_capture
    import generate_pdf # converts schedules / agreements to PDF file format
    import datetime
    import base64   # for parameter annotations
    import warnings # used to ignore UserWarning from pandas
    import sys      # for working out this script's working directory
    import ast      # for literal_eval( ... ) to read lists / dicts for SQL queries
    import config

except ImportError as e:

    print(
            f"\n\nFatal error: Unable to process an 'import' statement." +
            f"\n\nFatal error: This is caused by the Python packages not being properly installed." +
            f"\n\nTriage: Refer to 'AAA___readme___OSN.txt' in the 'Asset_Management_App' directory to fix this problem." +
            f"\n\nException text: {e}\n"
    )
    input( f"Press <ENTER> to exit this application... " )
    exit() # configuration involves many moving parts, so the only safe policy is to abort

SCRIPT_FILEPATH  = sys.argv[0]
SCRIPT_DIRECTORY = os.path.dirname( SCRIPT_FILEPATH )

if config.LIVE_DATABASE:
    VERSION_TITLE = f"{config.VERSION} -- EDU Database, as '{os.getlogin()}'"
else:
    VERSION_TITLE = f"{config.VERSION} -- Test Database, as '{os.getlogin()}'"

# warn that clear-screen (a.k.a. 'cls' is turned off)
if config.VERBOSE_NO_CLEAR_SCREEN:
    VERSION_TITLE = f"{config.VERSION} (no-clear-screen)"

class Color(Enum):
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    DEFAULT = "\033[0m"


class Alignment(Enum):
    LEFT = "<"
    CENTER = "^"
    RIGHT = ">"


# Print errors in red, exception text in magenta, and then pause for user to read and react to the message
def display_error( error_message: str, e: BaseException = None ) -> None:
    if error_message:
        print( Color.BRIGHT_RED.value + f"{error_message}" + Color.DEFAULT.value )

    if e is not None:
        # callstack_str = callstack_trace( e )
        print( Color.BRIGHT_MAGENTA.value + f"\nException text: {e}" + Color.DEFAULT.value )

        # Stop for the user to read the error(s) ... unless this is a 'success'
        if not re.match( '.*successfully.*', error_message):
            input_with_color( Color.BRIGHT_WHITE.value + \
                              f"Press Enter to continue..." + \
                              Color.DEFAULT.value )

    return


# Print verbose error message in MAGENTA, and then pauses for the user
# to read and react to the message; includes call stack for exceptions
def display_verbose_error( error_message: str, e: BaseException = None ) -> None:

    if ( config.LIVE_DATABASE == True  and  config.VERBOSE_ERROR == False ):
        return
    
    print( Color.BRIGHT_MAGENTA.value + f"Verbose error: {error_message}" + Color.DEFAULT.value )

    if e is not None:
        print( Color.BRIGHT_MAGENTA.value + f"\nException text: {e}" + Color.DEFAULT.value )

    input_with_color( Color.BRIGHT_WHITE.value + \
            f"Press Enter to continue..." + \
            Color.DEFAULT.value
    )

    return


# Displays an error (or inserts a blank line ...)
# Returns: an empty string, for resetting the error variable
def display_and_clear_error( error_message: str ) -> str:
    if error_message:
        print( Color.BRIGHT_RED.value + f"{error_message}" + Color.DEFAULT.value )
    else:
        print()  # insert a blank line

    return ""


# Function to connect to the PostgreSQL database
if config.LIVE_DATABASE == True:
    def connect_to_database() -> psycopg2.extras.DictConnection:
        conn = psycopg2.connect(
            connection_factory=psycopg2.extras.DictConnection,
            host=config.HOST,
            database=config.DATABASE,
            user=config.USER,
            password=config.PASSWORD,
        )
        return conn
else:
    def connect_to_database() -> psycopg2.extras.DictConnection:
        conn = psycopg2.connect(
            connection_factory=psycopg2.extras.DictConnection,
            host=config.DEV_HOST,
            database=config.DEV_DATABASE,
            user=config.DEV_USER,
            password=config.DEV_PASSWORD,
        )
        return conn


def print_title(
    title: str,
    color: Color = Color.WHITE,
    width: int = 0,
    print_bottom_border: bool = True,
) -> None:
    # Get the minimum width required to fit the title
    if width == 0 or width < len(title) + 4:
        width = len(title) + 4  # +4 for padding on both sides

    # Center the title within the specified width, then add ANSI color codes
    centered_title = " {:^{}} ".format(title, width - 4)
    colored_title = color.value + centered_title + Color.DEFAULT.value

    # Print the main title
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + colored_title + "│")

    # Optionally print the bottom border
    if print_bottom_border:
        print("└" + "─" * (width - 2) + "┘")

    return


# May throw a 'ValueError' exception
#       ==> table exceeds maximum width
def print_table(
    df: pd.DataFrame,
    title: str = "",
    title_color: Color = Color.WHITE,
    max_width: int = 0,
    alignment: Alignment = Alignment.LEFT,
    print_headers: bool = True,
) -> None:
    # Determine headers to use for calculating widths
    headers = df.columns if print_headers else range(df.shape[1])

    # Handle case when DataFrame is empty
    if df.empty:
        column_widths = [10 for _ in headers]  # Set a default width for each column
    else:
        # Calculate the maximum width required for each column including padding
        column_widths = [
            max(len(str(x)) for x in df.iloc[:, i]) + 2 for i in range(len(headers))
        ]  # +2 for padding on both sides

    # Adjust the width of the last column based on max_width (or vice versa)
    if max_width != 0:
        current_width = sum(column_widths) + len(column_widths) + 1
        if current_width < max_width:
            column_widths[-1] += max_width - current_width
        else:
            max_width = current_width # widen table, as needed

    # Check for total width exceeding max_width
    total_width = sum(column_widths) + len(column_widths) + 1
    if max_width != 0 and total_width > max_width:
        raise ValueError("Table width exceeds the specified maximum width")

    # Print the top border (with or without title)
    if title != "":
        print_title(title, title_color, total_width, print_bottom_border=False)

        # Print the separator with intersections
        print(
            "├" + "┬".join("─" * w for w in column_widths) + "┤"
        )  # Separator with intersections
    else:
        print(
            "┌" + "┬".join("─" * w for w in column_widths) + "┐"
        )  # Top border with intersections

    if print_headers:
        # Print column headers with padding
        header_row = (
            "│"
            + "│".join(
                " {:{}{}} ".format(col, alignment.value, column_widths[i] - 2)
                for i, col in enumerate(df.columns)
            )
            + "│"
        )
        print(header_row)

        # Separator under headers
        print("├" + "┼".join("─" * w for w in column_widths) + "┤")

    # Print each data row with padding
    for _, row in df.iterrows():
        row_str = (
            "│"
            + "│".join(
                " {:{}{}} ".format(str(row[col]), alignment.value, column_widths[i] - 2)
                for i, col in enumerate(df.columns)
            )
            + "│"
        )
        print(row_str)

    # Print the bottom border
    print("└" + "┴".join("─" * w for w in column_widths) + "┘")

    return


# Function to update or add students from a CSV file
# May throw a 'ValueError' exception
#       ==> file dialog cancelled  OR  invalid file name
def update_students_from_csv() -> None:
    conn = connect_to_database()
    cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

    # Use tkinter to prompt the user to choose a CSV file
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])

    # Check if the user has canceled the file dialog or has selected an invalid file
    if not file_path:
        raise ValueError("Invalid file selected or file dialog canceled")

    # Load CSV file into a pandas dataframe
    df = pd.read_csv(file_path)
    df["doc_num"] = df["doc_num"].astype(str)  # Convert doc_num to string

    # Iterate over each row in the dataframe
    for index, row in df.iterrows():
        # Check if the student already exists in the database
        cur.execute( "SELECT * FROM students WHERE doc_num = %s", ( row["doc_num"], ) )
        existing_student = cur.fetchone()

        # If the student exists, update their information
        if existing_student:
            cur.execute(
                "UPDATE students SET ctc_id = %s, first_name = %s, last_name = %s, middle_name = %s, status = %s WHERE doc_num = %s",
                (
                    row["ctc_id"],
                    row["first_name"],
                    row["last_name"],
                    row["middle_name"],
                    row["status"],
                    row["doc_num"],
                ),
            )
        # If the student does not exist, add them to the database
        else:
            cur.execute(
                "INSERT INTO students (doc_num, ctc_id, first_name, last_name, middle_name, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    row["doc_num"],
                    row["ctc_id"],
                    row["first_name"],
                    row["last_name"],
                    row["middle_name"],
                    row["status"],
                ),
            )

    conn.commit() # Save the UPDATE or INSERT
    cur.close()
    conn.close()

    return


# Function to export student data to a CSV file
def export_students_to_csv() -> None:
    conn = connect_to_database()
    cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

    # Execute a SELECT statement to get all students
    cur.execute( "SELECT * FROM students" )

    # Fetch all rows and store them in a list of tuples
    rows = cur.fetchall()

    # Create a pandas dataframe from the list of tuples
    df = pd.DataFrame(
        rows,
        columns=[
            "doc_num",
            "ctc_id",
            "first_name",
            "last_name",
            "middle_name",
            "status",
        ],
    )

    # Use tkinter to prompt the user to choose where to save the file and under what name
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
    )

    # Check if the user has canceled the file dialog or has selected an invalid file
    if not file_path:
        display_error( "Invalid file selected or file dialog canceled" )
        return

    # Export the dataframe to the chosen file
    df.to_csv(file_path, index=False)

    cur.close()
    conn.close()

    return


# Function to calculate the check digit for a GTIN barcode
# Returns: True (a valid barcode) or False (invalid / empty / zero)
def barcode_check_digit_is_valid( gtin: str ) -> bool:
    # Remove any leading zeros as they don't affect the check digit
    gtin = gtin.lstrip("0")

    # Ensure the GTIN number is not empty after removing leading zeros
    if not gtin:
        return False

    # Check if GTIN number consists only of digits
    if not gtin.isdigit():
        return False

    # Reverse the main part of the GTIN for easier calculation
    reversed_digits = [int(digit) for digit in reversed(gtin[:-1])]

    # Calculate the sum of digits, multiplying by 3 and 1 alternately
    total_sum = sum(
        reversed_digits[i] * 3 if i % 2 == 0 else reversed_digits[i]
        for i in range(len(reversed_digits))
    )

    # Calculate the check digit using modulo 10
    return (10 - total_sum % 10) % 10 == int(gtin[-1])


# Function to format a GTIN barcode as a 6-digit doc number
def convert_barcode_to_doc_number( gtin: str ) -> str:
    if not barcode_check_digit_is_valid(gtin):
        display_error( "Invalid check digit" )
        return ""  # Invalid check digit
    
    doc_num = str(gtin)[1:-1].lstrip("0")  # Remove leading zeros and check digit

    return doc_num


def clear_screen() -> None:
    # Clear the console screen based on the operating system
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


# Every screen of output always starts with these same two steps ...
def clear_screen_and_print_ams_title() -> None:
    clear_screen()
    print_title( f"Asset Management System ( {VERSION_TITLE} )", Color.BRIGHT_YELLOW, 100)

    return


# Prints an input prompt in cyan
# Returns the user's input
def input_with_color( prompt_message: str = "" ) -> str:
    user_input = ""

    if prompt_message == "":
        prompt_message = "Press Enter to continue... "

    user_input = input(
            Color.BRIGHT_CYAN.value
            + f"{prompt_message} "
            + Color.DEFAULT.value
    )

    return user_input.upper()


# Prints an input prompt in cyan
# Returns the user's input
def input_yes_no_only( prompt_message: str = "" ) -> str:
    user_input = "x" # invalid value

    if prompt_message == "":
        prompt_message = "Enter 'y' or 'n' to continue... "

    while ( user_input.upper() != 'Y' and user_input.upper() != 'N' ):
        user_input = input(
                Color.BRIGHT_CYAN.value
                + f"{prompt_message} "
                + Color.DEFAULT.value
        )

    return user_input.upper()


# PyLance complains about self-references, forward-references, and 
# (when I pre-declare these classes) re-definition of classes.
# Using " # type:ignore " here makes these problems go away.
class EduDbObject: pass                # type:ignore
class Entity( EduDbObject ): pass      # type:ignore
class User( Entity ): pass             # type:ignore
class Incarcerated( User ): pass       # type:ignore
class Student( Incarcerated ): pass    # type:ignore
class Employee( User ): pass           # type:ignore
class Location( Entity ): pass         # type:ignore
class Asset( EduDbObject ): pass       # type:ignore
class Accessory( Asset ): pass         # type:ignore
class Charger( Accessory ): pass       # type:ignore
class Headphones( Accessory ): pass    # type:ignore
class Laptop( Asset ): pass            # type:ignore
class Book( Asset ): pass              # type:ignore
class Calculator( Asset ): pass        # type:ignore
class Document( EduDbObject ): pass    # type:ignore
class Transaction( EduDbObject ): pass # type:ignore
class Course( EduDbObject ): pass      # type:ignore
class Schedule( EduDbObject ): pass    # type:ignore
class Enrollment( EduDbObject ): pass  # type:ignore


# TODO: Decide if this should be an instantiatable object,so we may have
#       concurrent DB connections. First, evaluate SQLAlchemy's support
#       for ORM and pandas' support for managing SQL queries.
class EduDbObject:

    # EduDbObject.class_map maps database 'asset_type', 'entity_type', and
    # 'user_type' to their associated classes; this helps us build objects.

# TODO: This is working in a funky way. Is it getting the 'pass' version of
#       the class, and not the redefined class definition?
    class_map = {
        'LAPTOP'       : Laptop,
        'BOOK'         : Book,
        'CALCULATOR'   : Calculator,
        'CHARGER'      : Charger,
        'HEADPHONES'   : Headphones,
        'USER'         : User,
        'LOCATION'     : Location,
        'INCARCERATED' : Incarcerated,
        'EMPLOYEE'     : Employee,
        'STUDENT'      : Student,
    }

    def __init__( self ):
        self.connection = None
        self.cursor     = None
    
# TODO: Replace the existing conn/cur with these functions.
#       [ This assumes DB queries are either atomic (class attributes)
#         or run against object instances (which can leads to time outs) ]

    def connect( self ) -> EduDbObject:
        if self.connection is None:
            self.connection = connect_to_database() # trust the default connection

        if self.cursor is None:
            self.cursor = self.connection.cursor(
                    cursor_factory=psycopg2.extras.DictCursor
            )
        
        return self

    def disconnect( self ) -> bool:
        try:

            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.commit()

            if self.cursor.__class__ is psycopg2.extras.DictCursor:
                self.cursor.close()
                self.cursor = None

            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.close()
                self.connection = None

            return True
        
        except Exception as e:
            # In case of error, roll back and report the failure
            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.rollback()

            if self.cursor.__class__ is psycopg2.extras.DictCursor:
                self.cursor.close()
                self.cursor = None

            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.close()
                self.connection = None

            display_verbose_error(
                    f"Exception during EduDbObject.disconnect:"
                    , e
            )
            
            return False

    def commit( self ) -> bool:
        try:
            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.commit()

            return True
        
        except Exception as e:
            # In case of error, roll back and report the failure
            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.rollback()
                
            if self.cursor.__class__ is psycopg2.extras.DictCursor:
                self.cursor.close()
                self.cursor = None

            if self.connection.__class__ is psycopg2.extras.DictConnection:
                self.connection.close()
                self.connection = None

            display_verbose_error(
                    f"Exception during EduDbObject.commit:"
                    , e
            )

        return False
        
    @staticmethod
    def fetch_row( selectClause: str, fromClause: str, whereClause: str, parameters ) -> dict:
        """Queries the EDU database, returning a dictionary keyed by column names

        Args:
            selectClause (str): columns to fetch
            fromClause (str):   tables to query
            whereClause (str):  selection criteria to use

        Returns:
            dict: the SQL results, in dictionary form (or 'None' if no data)
        """

        # clean up variables for (potential) error messages
        selectClause = " ".join( re.split( '[\n ]+', selectClause ) )
        fromClause   = " ".join( re.split( '[\n ]+', fromClause   ) )
        whereClause  = " ".join( re.split( '[\n ]+', whereClause  ) )

        # initialize these, to make PyLance happy(-ier)
        connection = None
        cursor     = None

        try:
# TODO: Use 'self' attributes (v 1.5.0)
            connection = connect_to_database( )
            cursor     = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

            cursor.execute(
                    f" SELECT {selectClause} " +
                    f" FROM   {fromClause} " + 
                    f" WHERE  {whereClause};",
                    parameters,
                )
            
            data = cursor.fetchone()
            # Being careful with the database cursor / connection
            cursor.close()
            cursor = None 
            connection.close()
            connection = None

            # return results as a dictionary
            if data is not None:
                kwargs = { key: data[key]  for  key in data.keys() }
                return kwargs
            else:
                display_verbose_error(
                        f"Warning: Data fetch from database failed (this might be OK):" +
                        f"\n\tIf The Asset system crashes, restart it." +
                        f"\nSAVE THIS INFORMATION: Database query follows:" +
                        f"\n\tselectClause='{selectClause}'" +
                        f"\n\tfromClaus   ='{fromClause}'" +
                        f"\n\twhereClause ='{whereClause}'" +
                        f"\n\tparameters  ='{parameters}' ):" +
                        f"\n\tNo data matches the given query and parameter(s)."
                )
                return None # no data
        
        except Exception as e:
            # In case of error, roll back and report the failure
            if connection.__class__ is psycopg2.extras.DictConnection:
                connection.rollback()

            if cursor.__class__ is psycopg2.extras.DictCursor:
                cursor.close()
                cursor = None

            if connection.__class__ is psycopg2.extras.DictConnection:
                connection.close()
                connection = None
            
            display_verbose_error(
                    f"Error: Exception in EduDbObject.fetch_row(" + 
                    f"\n\tselectClause='{selectClause}'" + \
                    f"\n\tfromClaus   ='{fromClause}'" + \
                    f"\n\twhereClause ='{whereClause}'" +
                    f"\n\tparameters  ='{parameters}' ):"
                    , e
            )
            
            return None # no data


    @staticmethod
    def fetch_rows( selectClause: str, fromClause: str, whereClause: str, parameters ) -> List[dict]:
        """Queries the EDU database, returning a list of dictionaries keyed by column names

        Args:
            selectClause (str): columns to fetch
            fromClause (str):   tables to query
            whereClause (str):  selection criteria to use

        Returns:
            dict: the SQL results, in dictionary form (or an empty list if no data)
        """

        # clean up variables for (potential) error messages
        selectClause = " ".join( re.split( '[\n ]+', selectClause ) )
        fromClause   = " ".join( re.split( '[\n ]+', fromClause   ) )
        whereClause  = " ".join( re.split( '[\n ]+', whereClause  ) )

        # initialize these, to make PyLance happy(-ier)
        connection = None
        cursor     = None

        try:
# TODO: Use 'self' attributes (v 1.5.0)
            connection = connect_to_database( )
            cursor     = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

            cursor.execute(
                    f" SELECT {selectClause} " +
                    f" FROM   {fromClause} " + 
                    f" WHERE  {whereClause};",
                    parameters,
                )
            
            data = cursor.fetchall()
            # Being careful with the database cursor / connection
            cursor.close()
            cursor = None 
            connection.close()
            connection = None

            # return results as a list of dictionaries
            kwargs_list = []
            if data is not None:
                for row in data:
                    kwargs_list.append( { key: row[key]  for  key in row.keys() } )

                return kwargs_list
            else:
                display_verbose_error(
                        f"Warning: Data fetch from database failed (this might be OK):" +
                        f"\n\tIf The Asset system crashes, restart it." +
                        f"\nSAVE THIS INFORMATION: Database query follows:" +
                        f"\n\tselectClause='{selectClause}'" +
                        f"\n\tfromClaus   ='{fromClause}'" +
                        f"\n\twhereClause ='{whereClause}'" +
                        f"\n\tparameters  ='{parameters}' ):" +
                        f"\n\tNo data matches the given query and parameter(s)."
                )
                return [] # empty list

        except Exception as e:
            # In case of error, roll back and report the failure
            if connection.__class__ is psycopg2.extras.DictConnection:
                connection.rollback()

            if cursor.__class__ is psycopg2.extras.DictCursor:
                cursor.close()
                cursor = None

            if connection.__class__ is psycopg2.extras.DictConnection:
                connection.close()
                connection = None
            
            display_verbose_error(
                    f"Error: Exception in EduDbObject.fetch_row(" + 
                    f"\n\tselectClause='{selectClause}'" + \
                    f"\n\tfromClaus   ='{fromClause}'" + \
                    f"\n\twhereClause ='{whereClause}'" +
                    f"\n\tparameters  ='{parameters}' ):"
                    , e
            )
            
            return [] # empty list


class Entity( EduDbObject ):

    DB_columns = """
        entities.entity_id,
        entities.entity_type,
        entities.enabled
        """
    DB_all_columns = f"{DB_columns}"
    DB_tables = """
        entities
        """
    DB_criteria = """
        entities.entity_id = %s
        """
    DB_order_by = """
        entities.entity_id ASC
        """

    def __init__(self, entity_id, entity_type, enabled, **kwargs ):
        self.entity_id = entity_id
# TODO: Adding the following to Entity() creates errors for all subclass
#       instances. Be sure to find and fix them all.
        self.type = entity_type # 'USER', 'LOCATION'
        self.enabled = enabled

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.entity_id == other.entity_id
        elif isinstance(other, int):
            return self.entity_id == other
        else:
            return False

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Entity to a pandas dataframe
        """
        entity_data = {
            "Field": ["Entity ID", "Entity Type", "Enabled"],
            "Value": [
                self.entity_id,
                self.type,
                self.enabled,
            ],
        }
        return pd.DataFrame( entity_data )
    
    @classmethod
    def from_id( cls, entity_id: int ) -> Union[Entity, None]:
        """Instantiates an Entity (sub-)class from its entity_id

        Args:
            entity_id (int): the entity's ID to instantiate

        Returns:
            Entity: an Entity (sub-) class object
        """
        data = EduDbObject.fetch_row(
                cls.DB_all_columns, # SELECT
                cls.DB_tables,      # FROM
                cls.DB_criteria,    # WHERE
                ( entity_id, )      # entity_id = %s
                )
        
        if data:
            return cls( **data ) # type:ignore -- this always returns an Entity
        else:
            display_verbose_error(
                    f"Error: {cls.__name__}.from_id( {entity_id} ): Unable " +
                    f"to find {cls.__name__} with entity ID '{entity_id}'." )
            return None

    # You can use this form: for asset in incarcerated.assets()
    # or this ........ form: issued_assets = list( incarcerated.assets() )
    def assets( self ) -> Iterator[ Union[Asset, Accessory, None ] ]:
        """
        Creates an iterated list of Asset objects for this Entity
            Args:
                self (implicit): any entity
            Returns:
                Asset (subclass) iterator of entity's ISSUED assets
            Note: 'Accessory' is a subclass of 'Asset'
        """
        issued_assets_ids      = []
        issued_accessories_ids = []

        # initialize these, to make PyLance happy(-ier)
        connection = None
        cursor     = None

        try:
            connection = connect_to_database()
            cursor  = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

            # Check for issued assets (TODO: We can't use EduDbObject.fetch_row()
            # for asset / accessory lists, because it returns just one row)
            cursor.execute(
                """
                SELECT
                    issued_assets.asset_id
                FROM
                    issued_assets,
                    transactions
                WHERE
                    transactions.entity_id = %s
                    AND transactions.transaction_id = issued_assets.transaction_id
                """,
                ( self.entity_id, )
            )

            issued_assets_ids = cursor.fetchall()

            # Check for issued accessories 
            cursor.execute(
                """
                SELECT
                    issued_accessories.entity_id,
                    issued_accessories.asset_id
                FROM
                    issued_accessories
                WHERE
                    issued_accessories.entity_id = %s
                """,
                ( self.entity_id, )
            )

            issued_accessories_ids = cursor.fetchall()

            # close DB connection, before we switch to iteration
            # (which can take a while ...)
            cursor.close()
            connection.close()

        except Exception as e:
            display_verbose_error(
                    f"Exception during {self.__class__.__name__}.assets( ):"
                    , e
            )

            # In case of error, roll back and report the failure
            if connection.__class__ is psycopg2.extras.DictConnection:
                connection.rollback()

            if cursor.__class__ is psycopg2.extras.DictCursor:
                cursor.close()
                cursor = None

            if connection.__class__ is psycopg2.extras.DictConnection:
                connection.close()
                connection = None

        finally:
            if not issued_assets_ids and not issued_accessories_ids:
                return None
            
            for asset_id_data in issued_assets_ids:
                yield Asset.from_id(
                        asset_id_data[0] )

            for accessory_id_data in issued_accessories_ids:
                # Accessories are assets, too, with a different primary key
                yield Accessory.from_ids(
                        entity_id=accessory_id_data[0],
                        asset_id =accessory_id_data[1]  ) # type:ignore - Accessory is a subclass of Asset!


class User( Entity ):

    DB_columns = """
        users.ctclink_id,
        users.last_name,
        users.first_name,
        users.middle_name,
        users.legacy_username,
        users.legacy_last_login,
        users.osn_username,
        users.osn_last_login,
        users.user_type
        """
    DB_all_columns = f"{Entity.DB_all_columns}, {DB_columns}"
    DB_tables = """
        entities,
        users
        """
    DB_criteria = """
        users.entity_id = %s
        AND users.entity_id = entities.entity_id
        """
    DB_order_by = """
        users.last_name ASC,
        users.first_name ASC,
        users.middle_name ASC,
        users.entity_id ASC
        """

    def __init__( self, entity_id, entity_type, enabled,
                  ctclink_id, first_name, last_name, middle_name,
                  legacy_username, legacy_last_login, osn_username,
                  osn_last_login, **kwargs ):
        super().__init__( entity_id, entity_type, enabled, **kwargs )
        self.ctclink_id = ctclink_id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.legacy_username = legacy_username
        self.legacy_last_login = legacy_last_login
        self.osn_username = osn_username
        self.osn_last_login = osn_last_login

    def __str__( self ) -> str:
        """
        Returns:
            str: default print for user is: LastName, First Middle
        """
        return f"{self.last_name}, {self.first_name} {self.middle_name}"

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts a User to a pandas dataframe
        """
        entity_data = {
            "Field": ["Last Name", "First Name", "Middle Name"],
            "Value": [
                self.last_name,
                self.first_name,
                self.middle_name,
            ],
        }
        return pd.DataFrame( entity_data )


class Incarcerated( User ):
    """Create and manage Incarcerated objects

    Default initializer:
        Incarcerated( long_list ): initialize instance from attributes list
    Initialize from entity ID:
        Incarcerated.from_id(  entity_id  ) initialize from entity ID
    Initialize from DOC number:
        Incarcerated.from_doc( doc_number ) initialize from DOC number
    """

# TODO: Decide whether to combine Incarcerated.DB_columns, User.DB_columns,
#       and Entity.DB_columns (trickier code); or, include all the combined
#       DB_columns here (repeats derivable data)
    DB_columns = """
        incarcerated.doc_number,
        incarcerated.facility,
        incarcerated.housing_unit,
        incarcerated.housing_cell,
        incarcerated.estimated_release_date,
        incarcerated.counselor,
        incarcerated.hs_diploma
        """
    DB_all_columns = f"{User.DB_all_columns}, {DB_columns}"
    DB_tables = """
        entities,
        users,
        incarcerated
        """
    DB_criteria = """
        incarcerated.entity_id = %s
        AND incarcerated.entity_id = users.entity_id
        AND users.entity_id = entities.entity_id
        """
    # We often fetch incarcerated by DOC (see Incarcerated.fromDoc( doc_number ) )
    DB_doc_criteria = """
        incarcerated.doc_number = %s
        AND incarcerated.entity_id = users.entity_id
        AND users.entity_id = entities.entity_id
        """
    DB_order_by = """
        incarcerated.doc_number ASC,
        incarcerated.entity_id ASC
        """

    def __init__( self, entity_id, entity_type, enabled,
                  ctclink_id, first_name, last_name, middle_name,
                  legacy_username, legacy_last_login, osn_username,
                  osn_last_login, doc_number, facility, housing_unit,
                  housing_cell, estimated_release_date, counselor,
                  hs_diploma, **kwargs ):
        super().__init__(
                  entity_id, entity_type, enabled, ctclink_id, first_name,
                  last_name, middle_name, legacy_username, legacy_last_login,
                  osn_username, osn_last_login, **kwargs )
        self.doc_number = doc_number
        self.facility = facility
        self.housing_unit = housing_unit
        self.housing_cell = housing_cell
        self.estimated_release_date = estimated_release_date
        self.counselor = counselor
        self.hs_diploma = hs_diploma

    @classmethod
    def from_doc( cls, doc_number: int ) -> Entity:
        """Instantiates an Incarcerated (sub-)class from its DOC number

        Args:
            doc_number (str): student's DOC or barcode

        Returns:
            Incarcerated: an Incarcerated (sub-) class object
        """
        data = EduDbObject.fetch_row(
                cls.DB_all_columns,  # SELECT
                cls.DB_tables,       # FROM
                cls.DB_doc_criteria, # WHERE
                ( doc_number, )           # doc_number = %s
                )
        
        if data:
            return cls( **data )
        else:
            display_error(
                    f"Error: {cls.__name__}.from_doc( {doc_number} ): Unable " +
                    f"to find {cls.__name__} with DOC number '{doc_number}'." )
            return None # type:ignore -- there is no alternative
            
    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Incarcerated to a pandas dataframe
        """
        entity_data = {
            "Field": ["DOC#", "CTC ID", "Name"],
            "Value": [
                self.doc_number,
                self.ctclink_id,
                f"{self}",
            ],
        }
        return pd.DataFrame( entity_data )


class Student( Incarcerated ):

# TODO: Decide whether to combine Student.DB_columns, Incarcerated.DB_columns,
#       User.DB_columns, and Entity.DB_columns (trickier code); or, include all
#       the combined DB_columns here (repeats derivable data)
    DB_columns = """
        students.program,
        students.program_status
        """
    DB_all_columns = f"{Incarcerated.DB_all_columns}, {DB_columns}"
    DB_tables = """
        entities,
        users,
        incarcerated,
        students
        """
    DB_criteria = """
        students.entity_id = %s
        AND students.entity_id = incarcerated.entity_id
        AND incarcerated.entity_id = users.entity_id
        AND users.entity_id = entities.entity_id
        """
    DB_order_by = """
        incarcerated.doc_number ASC,
        incarcerated.entity_id ASC
        """

    def __init__( self, entity_id, entity_type, enabled,
                  ctclink_id, first_name, last_name, middle_name,
                  legacy_username, legacy_last_login, osn_username,
                  osn_last_login, doc_number, facility, housing_unit,
                  housing_cell, estimated_release_date, counselor,
                  hs_diploma, program, program_status, **kwargs ):
        super().__init__(
                  entity_id, entity_type, enabled,
                  ctclink_id, first_name, last_name, middle_name,
                  legacy_username, legacy_last_login, osn_username,
                  osn_last_login, doc_number, facility, housing_unit,
                  housing_cell, estimated_release_date, counselor,
                  hs_diploma, **kwargs )
        self.program = program
        self.program_status = program_status


class Employee( User ):
    def __init__( self, entity_id, entity_type, enabled,
                  ctclink_id, first_name, last_name, middle_name,
                  legacy_username, legacy_last_login, osn_username,
                  osn_last_login, employee_id, **kwargs ):
        super().__init__(
                  entity_id, entity_type, enabled,
                  ctclink_id, first_name, last_name, middle_name,
                  legacy_username, legacy_last_login, osn_username,
                  osn_last_login, **kwargs )
        self.employee_id = employee_id


class Location( Entity ):
    def __init__( self,
                  entity_id, entity_type, enabled, building, room_number, room_name,
                  **kwargs ):
        super().__init__(
                  entity_id, entity_type, enabled)
        self.building = building
        self.room_number = room_number
        self.room_name = room_name


class Asset( EduDbObject ):
    """
    Create and manage Asset objects.
        Default initializer:
            Asset( id, type, limit, cost, status ):
                initialize instance from attributes list
        Initialize from asset ID:
            Asset.from_id( asset_id ):
                initialize (sub-)class instance from asset ID or barcode
        Returnable attribute check:
            is_returnable() -> True or False (based on asset class)
        Return this asset's related ISSUED Transaction:
            asset.issued_transaction()
        Return this asset's latest Transaction (any type):
            asset.last_transaction()
    """
    DB_columns = """
        assets.asset_id,
        assets.asset_type,
        asset_types.charge_limit,
        assets.asset_cost,
        assets.asset_status
        """
    DB_all_columns = f"{DB_columns}"
    DB_tables = """
        assets,
        asset_types
        """
    DB_criteria = """
        assets.asset_id = %s
        AND assets.asset_type = asset_types.asset_type
        """
    DB_order_by = """
        assets.asset_id ASC
        """
    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  **kwargs ):
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.charge_limit = charge_limit
        self.asset_cost = asset_cost
        self.asset_status = asset_status

    def is_returnable( self ) -> bool:
        """
        Is this asset returnable?
            Returns:
                bool: 'True', because it is
        """
        return True

    # 'cls' (and 'asset_class', when defined) is a (sub-) Asset class reference
    @classmethod
    def from_id( cls, asset_id: str, asset_class = None ) -> Union[ Asset, None ]:
        """Instantiates an Asset (sub-)class from its asset_id

        Args:
            asset_id (st): the asset's ID

        keyword-only parameter:
            asset_class (Asset): a specific Asset type to instantiate
        Returns:
            Asset: an Asset (sub-) class object
        """

        if not asset_id:
            return None # no asset ID, no asset ...

        if asset_class:
            cls = asset_class

        data = EduDbObject.fetch_row(
                cls.DB_all_columns, # SELECT
                cls.DB_tables,      # FROM
                cls.DB_criteria,    # WHERE
                ( asset_id, )       # entity_id = %s
                )
        
        # If there is no data, don't try to create an object
        if not data:
            display_verbose_error( f"Error: Unable to find a database record for {cls.__name__} ID '{asset_id}'" )
            return None
        
        class_map = {
        'LAPTOP'       : Laptop,
        'BOOK'         : Book,
        'CALCULATOR'   : Calculator,
        'CHARGER'      : Charger,
        'HEADPHONES'   : Headphones,
        }

        if cls.__name__ == "Asset":
            asset_type = data["asset_type"]
            if asset_type not in class_map:
                display_verbose_error(
                        f"Error: Asset.from_id( {asset_id} ): " +
                        f"Don't know how to build a " +
                        f"'{ data['asset_type'] }' class."
                )
                # returning a generic asset is better than returning "None"
                return Asset( **data ) # type:ignore - why is "Asset" not compatible with "Asset | None"
            
            # Use the asset_type class map to create a spcialized asset object
            asset_class = class_map[asset_type]
            asset = asset_class.from_id( asset_id ) # request class from ID            
            return asset

        return cls( **data ) # type:ignore instantiate the object

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Asset (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Asset ID", "Asset Cost", "Charge Limit", "Asset Status", "Warning"],
            "Value": [
                self.asset_type,
                self.asset_id,
                self.asset_cost,
                self.charge_limit,
                self.asset_status,
                "Unidentified Asset"
            ],
        }
        
        return pd.DataFrame( asset_data )

    def issued_transaction( self ) -> Transaction:
        """
        Finds and returns current ISSUED transaction for this asset.
        If the asset is not currently issued, returns 'None'.
            Args:
                self (implicit): asset to query
            Returns:
                The issued Transaction object
        [cf. Asset.last_transaction(), which returns the most recent transaction]
        """
        return asset_issued_transaction( self )

    def last_transaction( self ) -> Transaction:
        """
        Finds and returns the last transaction involving this asset. This could be ISSUED, RETURNED, MISSING, BROKEN, etc.
            Args:
                self (implicit): asset to query
            Returns:
                The last Transaction object related to this asset
        [cf. Asset.issued_transaction(), which only returns currently ISSUED]
        """
        return asset_latest_transaction( self )
    
    def __str__( self ) -> str:
        """
        Returns:
            str: default print for asset is: " ID / asset_type "
        """
        if self.asset_status != "IN_SERVICE": # show any non-standard status
            return f"{self.asset_id} / {self.asset_type} / " + \
                    Color.BRIGHT_RED.value + f"{self.asset_status}" + Color.DEFAULT.value
        else:
            return f"{self.asset_id} / {self.asset_type}"

    def __eq__( self, other ):
        if isinstance(other, Asset):
            return self.asset_id == other.asset_id
        elif isinstance(other, str):
            return self.asset_id == other
        else:
            return False


# TODO: Create Accessory.from_id( id ) for the Charger and Headphones classes to inherit
class Accessory( Asset ):
    """
    Create and manage Accessory objects.
        Default initializer:
            Accessory( assetID, type, limit, cost, status, accessoryID, entityID, transactionID ):
                initialize instance from attributes list
    """
    DB_columns = """
        issued_accessories.entity_id,
        issued_accessories.transaction_id
        """
    DB_all_columns = f"{Asset.DB_all_columns}, {DB_columns}"
    DB_tables = """
        issued_accessories,
        assets,
        asset_types
        """
    DB_criteria = """
        issued_accessories.asset_id  = %s  AND
        issued_accessories.entity_id = %s  AND
        issued_accessories.asset_id  = assets.asset_id  AND
        assets.asset_type = asset_types.asset_type
        """
    DB_order_by = """
        issued_accessories.asset_id ASC,
        issued_accessories.entity_id ASC
        """
    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  entity: Entity=None, entity_id: int=None,
                  transaction: Transaction=None, transaction_id: int=None,
                  # not_issued equal 'True' means an unissued accessory
                  not_issued=False,
                  **kwargs ):
        super().__init__(
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  **kwargs )

        # instantiate embedded entity object (or explicitly skip it)
        if not_issued == True:
            self.issued_to = None
        elif entity:
            self.issued_to = entity
        elif entity_id:
            self.issued_to = Incarcerated.from_id( entity_id )
        else:
            display_verbose_error(
                    f"Error: {self.__class__}: Constructor requires " +
                    f"an entity object, an entity_id, or a not_issued flag."
            )
            self == None
            return None
        
        # instantiate embedded transaction object (or explicitly skip it)
        if not_issued == True:
            self.transaction = None
        elif transaction:
            self.transaction = transaction
        elif transaction_id:
            self.transaction = Transaction.from_id( transaction_id )
        else:
            display_verbose_error(
                    f"Error: {self.__class__}: Constructor requires an " +
                    f"transaction object, a transaction_id, or a not_issued flag."
            )
            self == None
            return None

    @classmethod
    def from_id( cls, asset_id: str ) -> Accessory:
        """Instantiates a partial Accessory subclass from just an asset_id

        Args:
            asset_id (st): the asset's ID

        Returns:
            Accessory: an Accessory subclass instance, with no self.entity or
            self.transaction sub-objects.
        """

        # Query the related Asset fields for this mock-up object
        data = EduDbObject.fetch_row(
                Asset.DB_all_columns, # SELECT
                Asset.DB_tables,      # FROM
                Asset.DB_criteria,    # WHERE
                ( asset_id, )         # asset_id = %s
                )
        
        # This will suffice until we run " INSERT INTO issued_accessories "
        # to link up with an entity and a transaction
        if data:
            return cls( not_issued=True, **data )
        else:
            display_verbose_error(
                    f"Error: {cls.__name__}.from_id( {asset_id} ): " +
                    f"Don't know how to build a " +
                    f"'{data['asset_type']}' class."
            )
            return None
    
    @classmethod
    def from_ids( cls, asset_id: str, entity_id: int ) -> Asset:
        """Instantiates an Accessory (sub-)class from its " asset_id + entity_id " keys

        Args:
            asset_id (str): the asset's ID
            entity_id (int): the entity's (returner's?) ID

        Returns:
            Asset: an Asset (sub-) class object
        """
        data = EduDbObject.fetch_row(
                cls.DB_all_columns,      # SELECT
                cls.DB_tables,           # FROM
                cls.DB_criteria,         # WHERE
                ( asset_id, entity_id, ) # asset_id = %s AND entity_id = %s
                )
        
        if data:
            if cls.__name__ == "Accessory":
                # 'Accessory' is a superclass for CHARGER and HEADPHONES
                if data["asset_type"] == "CHARGER":
                    return Charger.from_ids(    asset_id, entity_id )
                elif data["asset_type"] == "HEADPHONES":
                    return Headphones.from_ids( asset_id, entity_id )
                else:
                    display_verbose_error(
                            f"Error: {cls.__name__}.from_ids( " +
                            f"asset:  '{ asset_id }', entity: '{ entity_id }' ): " +
                            f"Don't know how to build a '{ data['asset_type'] }' class."
                    )
                return None 
            else:
                return cls( **data )
        else:
            display_error(
                    f"Error: {cls.__name__}.from_ids( {asset_id}, {entity_id} ): " +
                    f"Unable to find {cls.__name__} with asset ID '{asset_id}' " +
                    f"and entity ID '{entity_id}'." )
            return None

    def __str__( self ) -> str:
        """
        Returns:
            str: default print for accessories is: " Class #{asset_id}@{person's name} "
        """
        if self.asset_status != "IN_SERVICE": # show any non-standard status
            return f"{self.__class__.__name__}: ID {self.asset_id} for {self.issued_to} " + \
                    Color.BRIGHT_RED.value + f"is {self.asset_status}" + Color.DEFAULT.value
        else:
            return f"{self.__class__.__name__}: ID {self.asset_id} for {self.issued_to}"

    def __eq__( self, other ):
        if isinstance(other, Accessory):
            return self.accessory_id == other.accessory_id
        elif isinstance(other, int):
            return self.accessory_id == other
        else:
            return False

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Accessory (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Asset ID", "Asset Cost", "Issued To" ],
            "Value": [
                self.asset_type,
                self.asset_id,
                self.asset_cost,
                self.issued_to,
            ],
        }

        return pd.DataFrame( asset_data )

class Charger( Accessory ):
    """
    Create and manage Charger objects.
        Default initializer:
            Charger( assetID, type, limit, cost, status, accessoryID, entityID, transactionID ):
                initialize instance from attributes list
    """
    # I can (safely) re-use ... DB_columns / DB_all_columns / DB_tables /
    #     DB_criteria / DB_order_by ... from my Accessory parent class

    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  entity: Entity=None, entity_id: int=None,
                  transaction: Transaction=None, transaction_id: int=None,
                  **kwargs ):
        super().__init__(
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  entity, entity_id,
                  transaction, transaction_id,
                  **kwargs )

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Asset (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Issued To", "Asset ID" ],
            "Value": [
                self.asset_type,
                self.issued_to,
                self.asset_id,
            ],
        }

        return pd.DataFrame( asset_data )


class Headphones( Accessory ):
    """
    Create and manage Headphones objects.
        Default initializer:
            Headphones( assetID, type, limit, cost, status, accessoryID, entityID, transactionID ):
                initialize instance from attributes list
        Returnable attribute check:
            is_returnable() -> False (based on these being headphones)
    """
    # I can (safely) re-use ... DB_columns / DB_all_columns / DB_tables /
    #     DB_criteria / DB_order_by ... from my Accessory parent class

    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  entity: Entity=None, entity_id: int=None,
                  transaction: Transaction=None, transaction_id: int=None,
                  **kwargs ):
        super().__init__(
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  entity, entity_id,
                  transaction, transaction_id,
                  **kwargs )

    def is_returnable( self ) -> bool:
        """
        Is this asset returnable?
            Returns:
                bool: 'False', because headphones can't be returned
        """
        return False

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Asset (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Issued To", "Asset ID" ],
            "Value": [
                self.asset_type,
                self.issued_to,
                self.asset_id,
            ],
        }

        return pd.DataFrame( asset_data )


class Laptop( Asset ):
    DB_columns = """
        laptops.laptop_model,
        laptops.laptop_serial_number,
        laptops.laptop_manufacturer,
        laptops.laptop_drive_serial_number,
        laptops.laptop_ram,
        laptops.laptop_cpu,
        laptops.laptop_storage,
        laptops.laptop_bios_version
        """
    DB_all_columns = f"{Asset.DB_all_columns}, {DB_columns}"
    DB_tables= """
        assets,
        asset_types,
        laptops
        """
    DB_criteria = """
        assets.asset_id = %s
        AND assets.asset_type = asset_types.asset_type
        AND assets.asset_id = laptops.asset_id
        """
    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost,
                  asset_status, laptop_model, laptop_serial_number,
                  laptop_manufacturer, laptop_drive_serial_number,
                  laptop_ram, laptop_cpu, laptop_storage,
                  laptop_bios_version, **kwargs ):
        super().__init__(
                  asset_id, asset_type, charge_limit, asset_cost,
                  asset_status, **kwargs )
        self.model = laptop_model
        self.serial_number = laptop_serial_number
        self.manufacturer = laptop_manufacturer
        self.drive_serial = laptop_drive_serial_number
        self.ram = laptop_ram
        self.cpu = laptop_cpu
        self.storage = laptop_storage
        self.bios_version = laptop_bios_version

    def __str__( self ) -> str:
        """
        Returns:
            str: default print for laptop is: " model "
        """
        if self.asset_status != "IN_SERVICE": # show any non-standard status
            return f"{self.model} / " + \
                    Color.BRIGHT_RED.value + f"{self.asset_status}" + Color.DEFAULT.value
        else:
            return f"{self.model}"

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Asset (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Asset ID", "Serial Number", "Drive Serial", "Manufacturer", "Model"],
            "Value": [
                self.asset_type,
                self.asset_id,
                self.serial_number,
                self.drive_serial,
                self.manufacturer,
                self.model,
            ],
        }

        return pd.DataFrame( asset_data )


class Book( Asset ):
    DB_columns = """
        books.book_isbn,
        books.book_title,
        books.book_author,
        books.book_isbn,
        books.book_publisher,
        books.book_edition,
        books.book_year
        """
    DB_all_columns = f"{Asset.DB_all_columns}, {DB_columns}"
    DB_tables= """
        assets,
        asset_types,
        book_assets,
        books
        """
    DB_criteria = """
        assets.asset_id = %s
        AND assets.asset_type = asset_types.asset_type
        AND assets.asset_id = book_assets.asset_id
        AND book_assets.book_isbn = books.book_isbn
        """
    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  book_isbn, book_title, book_author, book_publisher,
                  book_edition, book_year, **kwargs ):
        super().__init__(
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  **kwargs )
        self.isbn = book_isbn
        self.title = book_title
        self.author = book_author
        self.publisher = book_publisher
        self.edition = book_edition
        self.year = book_year

    def __str__( self ) -> str:
        """
        Returns:
            str: default print for book is: " title "
        """
        if self.asset_status != "IN_SERVICE": # show any non-standard status
            return f"{self.title} / " + \
                    Color.BRIGHT_RED.value + f"{self.asset_status}" + Color.DEFAULT.value
        else:
            return f"{self.title}"

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Asset (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Asset ID", "ISBN", "Publisher", "Author", "Title", "Edition", "Year"],
            "Value": [
                self.asset_type,
                self.asset_id,
                self.isbn, # TODO: IntelliSense fails here -- how do I re-cast Asset to Book?
                self.publisher,
                self.author,
                self.title,
                self.edition,
                self.year,
            ],
        }

        return pd.DataFrame( asset_data )


class Calculator( Asset ):
    DB_columns = """
        calculators.calculator_model,
        calculators.calculator_serial_number,
        calculators.calculator_manufacturer,
        calculators.calculator_manufacturer_date_code,
        calculators.calculator_color
        """
    DB_all_columns = f"{Asset.DB_all_columns}, {DB_columns}"
    DB_tables = """
        assets,
        asset_types,
        calculators
        """
    DB_criteria = """
        assets.asset_id = %s
            AND assets.asset_type = asset_types.asset_type
            AND assets.asset_id = calculators.asset_id
        """
    DB_order_by = """
        calculators.asset_id ASC
        """

    def __init__( self,
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  calculator_model, calculator_serial_number,
                  calculator_manufacturer, calculator_manufacturer_date_code,
                  calculator_color, **kwargs ):
        super().__init__(
                  asset_id, asset_type, charge_limit, asset_cost, asset_status,
                  **kwargs )
        self.model = calculator_model
        self.serial_number = calculator_serial_number
        self.manufacturer = calculator_manufacturer
        self.manufacturer_date_code = calculator_manufacturer_date_code
        self.color = calculator_color

    def __str__( self ) -> str:
        """
        Returns:
            str: default print for calculator is: " model "
        """
        if self.asset_status != "IN_SERVICE": # show any non-standard status
            return f"{self.model} / " + \
                    Color.BRIGHT_RED.value + f"{self.asset_status}" + Color.DEFAULT.value
        else:
            return f"{self.model}"

    def to_dataframe( self ) -> pd.DataFrame:
        """
        converts an Asset (sub-)class to a pandas dataframe
        """
        asset_data = {
            "Field": ["Asset Type", "Asset ID", "Serial Number", "Manufacturer", "Date Code", "Model", "Color"],
            "Value": [
                self.asset_type,
                self.asset_id,
                self.serial_number,
                self.manufacturer,
                self.manufacturer_date_code,
                self.model,
                self.color,
            ],
        }

        return pd.DataFrame( asset_data )


class Document( EduDbObject ):
    def __init__( self,
                  document_id: int , document_type: str,
                  **kwargs ):
        self.document_id   = document_id
        self.document_type = document_type

    def __str__( self ) -> str:
        """
        Returns:
            str: default print for document is: " document ID (type)"
        """
        return f"document { self.transaction_id } ({ self.document_type })"


class Transaction( EduDbObject ):
    def __init__( self,
                  transaction_id, entity_id, asset: Asset, transaction_type,
                  transaction_timestamp, transaction_user, transaction_notes,
                  **kwargs ):
        self.transaction_id = transaction_id
        self.entity_id = entity_id
        self.asset = asset
        self.transaction_type = transaction_type
        self.transaction_timestamp = transaction_timestamp
        self.transaction_user = transaction_user
        self.transaction_notes = transaction_notes

# TODO: add Transaction.DB_columns (etc.) here, and change this
#       from_id() function to more closely mirror Asset.from_id() ...
    def from_id( transaction_id: int ) -> Transaction:
        """
            Finds a Transaction by its ID number

            Args:
                transaction_id (int): the transaction to look up

            Returns:
                transaction: the associated Transaction object
        """

        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        # Check for existing asset
        cur.execute(
            """
            SELECT
                transactions.transaction_id,
                transactions.entity_id,
                transactions.asset_id,
                transactions.transaction_type,
                transactions.transaction_timestamp,
                transactions.transaction_user,
                transactions.transaction_notes
            FROM
                transactions
            WHERE
                transactions.transaction_id = %s
            """,
            ( transaction_id, ),
        )

        data = cur.fetchone()

        cur.close()
        conn.close()

        if not data:
            return None

        kwargs = { key: data[key]  for  key in data.keys() }
        kwargs['asset'] = Asset.from_id( kwargs['asset_id'] )
        return Transaction( **kwargs ) # pass in a dictionary


    def __str__( self ) -> str:
        """
        Returns:
            str: default print for transaction is: " transaction ID "
        """
        return f"transaction {self.transaction_id}"


# TODO: Fill this in with useful information
class Course( EduDbObject ):
    def __str__( self ) -> str:
        """
        Returns:
            str: default print for course is: " transaction ID "
        """
        return f"course {self.exception__undefined_attribute}"


# TODO: Fill this in with useful information
class Schedule( EduDbObject ):
    def __str__( self ) -> str:
        """
        Returns:
            str: default print for course is: " transaction ID "
        """
        return f"schedule {self.exception__undefined_attribute}"


class Enrollment( EduDbObject ):
    def __init__( self,
                  entity_id, schedule_id, course_id, course_prefix, course_code,
                  course_name, course_credits, course_description, course_outcomes,
                  course_start_date, course_end_date, course_days,
                  course_start_time, course_end_time, course_location,
                  course_instructor, course_quarter, course_year,
                  **kwargs ):
        self.entity_id = entity_id
        self.schedule_id = schedule_id
        self.course_id = course_id
        self.course_prefix = course_prefix
        self.course_code = course_code
        self.course_name = course_name
        self.course_credits = course_credits
        self.course_description = course_description
        self.course_outcomes = course_outcomes
        self.course_start_date = course_start_date
        self.course_end_date = course_end_date
        self.course_days = course_days
        self.course_start_time = course_start_time
        self.course_end_time = course_end_time
        self.course_location = course_location
        self.course_instructor = course_instructor
        self.course_quarter = course_quarter
        self.course_year = course_year

# TODO: Liberally borrow code from Asset.from_id(...) to
#       create an Enrollment.from_ids( entity_id, schedule_id )
    @staticmethod
    def from_ids( entity_id: int, schedule_id: int ) -> Enrollment:
        # return Enrollment( 
        #       entity_id, schedule_id, course_id, course_prefix,
        #       course_code, course_name, course_credits, course_description,
        #       course_outcomes, course_start_date, course_end_date,
        #       course_days, course_start_time, course_end_time, course_location,
        #       course_instructor, course_quarter, course_year
        # )
        pass

# TODO: Fix up to query only enrollments.entity_id / enrollments.schedule_id
#       and then iterate using Enrollment.from_ids( entity_id, schedule_id)
#       NOTE: #1 Create Enrollment.from_ids(...) using below SELECT query
#       NOTE: #2 AND THEN ... cut back on columns here to just the two
#       NOTE: #3 from_ids (notice 'ids' is plural)
    @staticmethod
    def from_entity_id( entity_id: int ) -> List[Enrollment]:
    #                                    -> Iterator[Enrollment]:
        """
        Creates an iterated list of Enrollment objects for a given entity
            Args:
                entity_id (int): entity to query
            Returns:
                Enrollment objects iterator fro entity's current classes
        """
        print("Getting enrollments for entity ID", entity_id)
        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cur.execute(
            """
            SELECT 
                enrollments.entity_id,
                enrollments.schedule_id,
                courses.course_id,
                courses.course_prefix,
                courses.course_code,
                courses.course_name,
                courses.course_credits,
                courses.course_description,
                courses.course_outcomes,
                course_schedules.course_start_date,
                course_schedules.course_end_date,
                course_schedules.course_days,
                course_schedules.course_start_time,
                course_schedules.course_end_time,
                course_schedules.course_location,
                course_schedules.course_instructor,
                course_schedules.scheduled_quarter,
                course_schedules.scheduled_year
            FROM
                enrollments,
                course_schedules,
                courses
            WHERE
                enrollments.entity_id = %s
                AND enrollments.schedule_id = course_schedules.schedule_id
                AND course_schedules.course_id = courses.course_id
            ;
            """,
            ( entity_id, ),
        )

        enrollments = cur.fetchall()
#        enrollment_entity_schedule_ids = cur.fetchall()

        # close connection, because iterators can take a while ...
        cur.close()
        conn.close()

        if not enrollments:
#        if not enrollment_entity_schedule_ids:
            return None
    
        # TODO: The above and below are all wrong! A) Query only the entity_id, schedule_id ) pairs Create an iterator that yields
        #       this Dictionary comprehension
#        kwargs = { key: data[key]  for  key in data.keys() }
#        return Laptop( **kwargs )
        return [Enrollment(
            enrollment["entity_id"],
            enrollment["schedule_id"],
            enrollment["course_id"],
            enrollment["course_prefix"],
            enrollment["course_code"],
            enrollment["course_name"],
            enrollment["course_credits"],
            enrollment["course_description"],
            enrollment["course_outcomes"],
            enrollment["course_start_date"],
            enrollment["course_end_date"],
            enrollment["course_days"],
            enrollment["course_start_time"],
            enrollment["course_end_time"],
            enrollment["course_location"],
            enrollment["course_instructor"],
            enrollment["scheduled_quarter"],
            enrollment["scheduled_year"],
        ) for enrollment in enrollments]
        # =========

        # TODO: Verify this 'for' syntax in the debugger.
        #  It 'should' work with the shortened 2-column query
        # =========
#        for ( entity_id, schedule_id ) in issued_assets_ids:
#            yield asset_from_id( asset_id )
        # =========

        return



# TODO: Requires major fix-up ( same as Enrollment.from_entity_id(...) )
#       [ Save work by using cut-paste-modify on the other fixed-up method]
    @staticmethod
    def from_schedule_id( schedule_id: int ) -> List[Enrollment]:
    #                                    -> Iterator[Enrollment]:
        """
        Creates an iterated list of Enrollment objects for a given schedule
            Args:
                schedule_id (int): schedule to query
            Returns:
                Enrollment objects iterator for selected class
        """
        print("Getting enrollments for schedule ID", schedule_id)
        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cur.execute(
            """
            SELECT 
                enrollments.entity_id,
                enrollments.schedule_id,
                courses.course_id,
                courses.course_prefix,
                courses.course_code,
                courses.course_name,
                courses.course_credits,
                courses.course_description,
                courses.course_outcomes,
                course_schedules.course_start_date,
                course_schedules.course_end_date,
                course_schedules.course_days,
                course_schedules.course_start_time,
                course_schedules.course_end_time,
                course_schedules.course_location,
                course_schedules.course_instructor,
                course_schedules.scheduled_quarter,
                course_schedules.scheduled_year
            FROM
                enrollments,
                course_schedules,
                courses
            WHERE
                enrollments.schedule_id = %s
                AND enrollments.schedule_id = course_schedules.schedule_id
                AND course_schedules.course_id = courses.course_id
            ;
            """,
            ( schedule_id, )
        )

        enrollments = cur.fetchall()
#        enrollment_entity_schedule_ids = cur.fetchall()

        # close connection, because iterators can take a while ...
        cur.close()
        conn.close()

        if not enrollments:
#        if not enrollment_entity_schedule_ids:
            return None
    
        # TODO: REPLACE THIS CODE WITH a Dictionary 
        # =========
        return [Enrollment(
            enrollment["entity_id"],
            enrollment["schedule_id"],
            enrollment["course_id"],
            enrollment["course_prefix"],
            enrollment["course_code"],
            enrollment["course_name"],
            enrollment["course_credits"],
            enrollment["course_description"],
            enrollment["course_outcomes"],
            enrollment["course_start_date"],
            enrollment["course_end_date"],
            enrollment["course_days"],
            enrollment["course_start_time"],
            enrollment["course_end_time"],
            enrollment["course_location"],
            enrollment["course_instructor"],
            enrollment["scheduled_quarter"],
            enrollment["scheduled_year"],
        ) for enrollment in enrollments]
        # =========

        # TODO: Verify this 'for' syntax in the debugger.
        #  It 'should' work with the shortened 2-column query
        # =========
#        for ( entity_id, schedule_id ) in issued_assets_ids:
#            yield asset_from_id( asset_id )
        # =========

        return


def on_signature_captured(
        signature_data: base64,
        incarcerated: Incarcerated,
        assets: list[Asset],
        current_time: str
        ) -> None:
    """
    A callback for the signature capture thread. Generates the signed agreement
    as a PDF, signaling the main thread to resume.
        Args:
            signature (base64): students' signature; incarcerated (obj): student object
            assets (list[Asset]): issued assets; current_time (str): signature's date
    """
# TODO: This would be a good place to capture the signature data.
#       There is a question of data format (both the current 'base64' form and how
#       to store and retrieve it from the database). Signatures are desirable for
#       the " college_representative " only because student signatures are in the PDFs.

    # Get the largest available 'course_end_date' using ORDER BY ++ LIMIT (1)
    data = EduDbObject.fetch_row(
            "course_end_date",  # SELECT : end date
            "course_schedules", # FROM   : schedules
                                # WHERE  : (dummy criterion) + ORDER BY / LIMIT
            """course_start_date < course_end_date
               ORDER BY course_end_date DESC
               LIMIT( 1 )
            """,
            ( '', '' ) # dummy parameter tuple
    )

    if data:
        quarter_end_date = data['course_end_date'] # obviously right
    else:
        quarter_end_date = datetime.date( 1900, 1, 1 ) # obviously wrong

    agreement_filepath = generate_pdf.generate_agreement(signature_data, incarcerated, assets, current_time, quarter_end_date )

    print( f"Signature captured and saved in '{agreement_filepath}'." )
    # Signal the main thread that the signature has been captured
    signature_capture.signature_captured_event.set()


def issue_assets() -> None:
    """
    Reads a DOC, displays student's existing assets (if any), then reads,
    validates, and (if OK) checks out a new asset(s).  When check-out is
    complete, prompts for a signature and prints a loan agreement.
        Catches:
            Any exception thrown during transaction document creation
    """
    last_error = ""  # Store the last error message

    while True:
        clear_screen_and_print_ams_title()
        print_title("Issue Assets", Color.BRIGHT_YELLOW, 100)
        last_error = display_and_clear_error( last_error )
        issued_assets = [] # clear old list

        ( doc_num, last_error ) = input_and_validate_doc()
        if last_error:
            continue # repeat loop, to show error
        if not doc_num:
            break # back out to main menu

        selected_entity = Incarcerated.from_doc( doc_num )

        if not selected_entity:
            last_error = "Incarcerated Individual not found"
            continue

        issued_assets = list( selected_entity.assets() )

        while True:
            clear_screen_and_print_ams_title()
            print_selected_incarcerated_in_table( selected_entity )
            print_issued_assets_table( issued_assets )
            print_title("Issue Asset", Color.BRIGHT_YELLOW, 100)
            last_error = display_and_clear_error( last_error )

            new_asset_barcode = input_with_color( "Enter asset ID:" )

            # If there are no more assets to add, move on to signing and printing
            if not new_asset_barcode:
                sign_and_print_documents( selected_entity, issued_assets )
                break  # Break out of the loop if no asset ID was entered
            
            ( asset, last_error ) = asset_validate_from_barcode( new_asset_barcode, selected_entity, issued_assets )

            if last_error != "":
                continue # print the error, and try again
            
            ( issued_success, last_error ) = issue_asset_to_entity( asset, selected_entity, issued_assets )

            # add the newly vetted asset to issued_assets
            if issued_success:
                issued_assets.append( asset )


def sign_and_print_documents( entity: Incarcerated, issued_assets: List[ Asset ] ) -> None:
    unprinted_documents = get_unprinted_documents_for_entity( entity.entity_id )

    # Filter for "AGREEMENT" type documents
    agreement_documents = [doc for doc in unprinted_documents if doc['document_type'] == 'AGREEMENT']

    if agreement_documents:
        # If any unprinted documents, ask to print them
        print_agreement = input_yes_no_only( "Print asset agreement? (Y/N)" )
        if print_agreement == "Y":
            capture_signature_and_print_out_agreement( entity, issued_assets )

    label_documents = [doc for doc in unprinted_documents if doc['document_type'] == 'LABELS']

    if label_documents:
        # print_document_labels = input_yes_no_only( "Print laptop labels? (Y/N)" )
        print_document_labels = "Y" #TODO Remove this line once the logic for printing laptop labels is implemented
        if print_document_labels == "Y":
            print_out_document_labels( entity, issued_assets )

    return


def asset_validate_from_barcode( barcode: str, entity: Incarcerated, issued_assets: List[ Asset ] ) -> Tuple [ Union[ Asset, None ], str ]:
    asset = Asset.from_id( barcode )

    if not asset:
        return( None, f"Asset not found, for barcode '{barcode}'" )

    if asset.asset_status != "IN_SERVICE":
        return( None, verbose_asset_status( asset ) )

    transaction = asset.issued_transaction()

    if transaction and transaction.entity_id != entity.entity_id:
        return( None, f"Error: Asset is currently issued to entity ID {transaction.entity_id}." )
    
    elif transaction and transaction.entity_id == entity.entity_id:
        return( None, "Error: Asset already charged to currently selected entity." )
    
    # Count the number of same-type assets already issued to entity, esp. books
    ( overlimit, charge_error ) = asset_validate( asset, issued_assets )

    if overlimit:
        return( None, charge_error )

    # At this point, the asset (or partial accessory) is fully vetted, so send it back
    return( asset, "" )


def issue_asset_to_entity( asset: Asset, entity: Incarcerated, issued_assets: List[ Asset ] ) -> Tuple[ bool, str]:
    try:
        transaction_id = incarcerated_create_asset_issue_transaction( asset, entity )
        agreement_document_id = incarcerated_transaction_agreement_document( entity, transaction_id )

        if asset.asset_type == 'LAPTOP':
            create_laptop_labels( transaction_id )

            for asset in issued_assets:
                if isinstance( asset, Charger ):
                    break
            else: # charger not in issued_assets ==> add one
                charger = issue_charger( transaction_id, entity )
                if charger is not None:
                    issued_assets.append( charger )

            for asset in issued_assets:
                if isinstance( asset, Headphones ):
                    break
            else: # headphones not in issued_assets ==> add one
                headphones = issue_headphones( transaction_id, entity )
                if headphones is not None:
                    issued_assets.append( headphones )

        return( True, Color.BRIGHT_GREEN.value + "Asset issued successfully!" + Color.DEFAULT.value )

    except Exception as e:
        return( False, f"Exception during issue_asset_to_entity( " +
                       f"'{asset}', '{entity}' ):" +
                       f"\nException text: {e}" )


def print_selected_incarcerated_in_table( selected_entity: Incarcerated ) -> None:
    """
    Convert student information into a table without column headers.
    Args:
        selected_entity (Incarcerated): student data object
    """

    print_table(
        selected_entity.to_dataframe(),
        "Selected Incarcerated Individual",
        Color.BRIGHT_YELLOW,
        100,
        print_headers=False,
    )
    return


# Function to print all issued Assets in table format
# Does not set 'last_error' or (directly) throw an exception
# P.S. issued_assets = list(get_issued_assets_by_entity_id(selected_entity.entity_id))
def print_issued_assets_table( issued_assets: List[ Asset ] ) -> None:
    """
    print issued assets list in table format

    Args:
        issued_assets (List[ Asset ]): a list of asset objects
    """
    issued_assets_data = []
    for asset in issued_assets:
        if asset is not None:
            asset_data = ( asset.asset_id, asset.asset_type, f"{asset}" ) # use __str__ overload
            issued_assets_data.append(asset_data)

    issued_assets_df = pd.DataFrame(
        issued_assets_data, columns=["ID", "Type", "Name"]
    )

    # Use print_table to display the data
    print_table(
        issued_assets_df, "Currently Issued Assets", Color.BRIGHT_YELLOW, 100
    )


# Function to read and validate a DOC from barcode / keyboard 
# Returns: Tuple( str doc_number, str error_message )
#          if the DOC is invalid, "" is returned for DOC
#          if there was no error, "" is returned for error
def input_and_validate_doc() -> Tuple[ str, str ]:

    doc_num = input_with_color( "Enter DOC number:" )
    if not doc_num:
        return( "", "" ) # no doc, no error

    if len(doc_num) != 5 and len(doc_num) != 6 and len(doc_num) != 12:
        return( "", "Invalid DOC number" )       # no doc, error
    elif len(doc_num) == 12:  # validate a GTIN barcode
        doc_num = convert_barcode_to_doc_number( doc_num )
        if doc_num == "":
            return( "", "Invalid GTIN barcode" ) # no doc, error

    return( doc_num, "" ) # doc, no error


# Function to check if a book (ISBN) is already checked out
# Returns: Tuple( bool book_checked_out, str error_message )
#          if this book is already checked out, return True for book_checked_out
#          if there was no error, error_message is ""
def book_is_checked_out( asset: Asset, issued_assets: List[ Asset ] ) -> Tuple[ bool, str ]:

    if not isinstance(asset, Book):
        return( False, "" ) # no book, no error

    for issued_asset in issued_assets:
        if (
                isinstance( issued_asset, Book )
            and issued_asset.isbn == asset.isbn  ):
                return( True, f"Error: A book with (ISBN: {asset.isbn}) is already issued to the selected individual." )
        
    return( False, "" ) # no conflict


# Function queries an entity's unprinted documents using an existing DB cursor
# TODO: Maybe we should return Document object(s), instead?
def get_unprinted_documents_for_entity( entity_id: int ) -> list[psycopg2.extras.DictRow]:
    # Check if any documents related to the transactions of the current entity are unprinted
    try:
        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )
        
        cur.execute(
            """
            SELECT 
                d.document_id, 
                d.document_type, 
                d.document_printed_timestamp, 
                d.document_signed_timestamp, 
                d.document_file_name
            FROM 
                transactions t
            JOIN 
                transaction_documents td ON t.transaction_id = td.transaction_id
            JOIN 
                documents d ON td.document_id = d.document_id
            WHERE 
                t.entity_id = %s AND 
                d.document_printed_timestamp IS NULL;
            """,
            ( entity_id, ),
        )

        unprinted_documents = cur.fetchall()

        cur.close()
        conn.close()

        return unprinted_documents

    except Exception as e:
        display_verbose_error(
                f"Exception during get_unprinted_documents_for_entity( {entity_id} ):"
                , e
        )
        # In case of error, roll back and report the failure
        if conn is not None:
            conn.rollback() # not needed, but it doesn't hurt
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

        return 0


# Function captures the student's signature and generates / prints their agreement
# Catches exception(s) from signature_capture and/or generate_pdf
def capture_signature_and_print_out_agreement(
        entity: Incarcerated,
        issued_assets: list[Asset]
        ) -> None:
    try:
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        signature_capture.launch(on_signature_captured, entity, issued_assets, current_time)

        print("Waiting for signature...")
        signature_capture.signature_captured_event.wait()

        print("Generating agreement...")
        signature_capture.signature_captured_event.clear()

        # This must stay in sync with variable " output_filepath " in generate_pdf.generate_agreement()
        agreement_file_name = f"{ entity.doc_number }_{ current_time }.pdf"

# TODO: Extract the below UPDATE statement into EduDbObject.update_rows() ...
# CALL: EduDbObject.update_rows(
#       update_table = "documents",
#       set_fields = "document_printed_timestamp = CURRENT_TIMESTAMP, document_signed_timestamp  = CURRENT_TIMESTAMP, document_file_name = '%(document_file_name)s'",
#       from_tables = "transaction_documents, transactions", # defaults to ''
#       where_criteria =
#       """
#           documents.document_type = 'AGREEMENT'
#           AND documents.document_id = transaction_documents.document_id
#           AND transaction_documents.transaction_id = transactions.transaction_id
#           AND transactions.asset_id = '%(asset_id)s'
#           AND transactions.entity_id = '%(entity_id)s'
#       """,
#       returning_field = 'document_file_name'
#       parameters = { 'document_file_name': agreement_file_name, 'asset_id': asset.asset_id, 'entity_id': entity.entity_id }
# )
#
# def update_rows( update_table: str, set_fields: str, from_tables: str,
#        where_criteria: str, where_parameters: dict ) -> bool:
# QUERY: f"UPDATE {update_table} SET { set_fields % parameters } FROM {from_tables} WHERE { where_criteria % parameters } RETURNING {returning_field};"
# RETURNS: the desired field (no exception) or None (exception)

        # Record agreement document as printed
        print("Marking agreement as printed...")

        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        for asset in issued_assets:
            cur.execute(
                """
                UPDATE
                    documents
                SET
                    document_printed_timestamp = CURRENT_TIMESTAMP,
                    document_signed_timestamp  = CURRENT_TIMESTAMP,
                    document_file_name = %s
                FROM
                    transaction_documents td
                JOIN transactions t ON td.transaction_id = t.transaction_id
                WHERE
                    documents.document_id = td.document_id
                    AND document_type = 'AGREEMENT'
                    AND t.asset_id = %s and t.entity_id = %s;
                """,
                ( agreement_file_name, asset.asset_id, entity.entity_id, )
            )

        conn.commit() # Save the UPDATE
        cur.close()
        conn.close()

        print("Printing agreement...")
        agreement_filepath = f"{ SCRIPT_DIRECTORY }\\agreements\\{agreement_file_name}"
        generate_pdf.command_print( agreement_filepath )

    except Exception as e:
        # In case of error, roll back and report the failure
        if conn is not None:
            conn.rollback() # not needed, but it doesn't hurt
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
        display_verbose_error(
                f"Exception during capture_signature_and_print_out_agreement(" +
                f"\n\t{entity},\n\t{issued_assets} ):"
                , e
        )

    return


# Function prints (fakes it, really...) and clears unprinted document labels
# Catches exception(s) from DB query
def print_out_document_labels(
        entity: Incarcerated,
        issued_assets: list[Asset]
        ) -> None:
    try:

        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        for asset in issued_assets:
            # Update the document record in the database (if necessary)
            cur.execute(
                """
                UPDATE
                    documents
                SET
                    document_printed_timestamp = CURRENT_TIMESTAMP,
                    document_signed_timestamp  = CURRENT_TIMESTAMP
                FROM
                    transaction_documents td
                JOIN transactions t ON td.transaction_id = t.transaction_id
                WHERE
                    documents.document_id = td.document_id
                    AND document_type = 'LABELS'
                    AND t.asset_id = %s and t.entity_id = %s;
                """,
                ( asset.asset_id, entity.entity_id, )
            )

            # Send the print command
            # print_label(label_file_path) #TODO Implement the logic to handle the printing of laptop labels

        conn.commit() # Save the UPDATE
        cur.close()
        conn.close()

        print("Labels printed successfully.")

    except Exception as e:
        # In case of error, roll back and report the failure
        if conn is not None:
            conn.rollback() # not needed, but it doesn't hurt
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

        display_verbose_error(
                f"Exception during print_out_document_labels(" +
                f"\n\t{entity},\n\t{issued_assets} ):"
                , e
        )

    return


# Function turns a (terse) asset status code into a readable error message
def verbose_asset_status( asset: Asset ) -> str:
    status_error_messages = {
        "DECOMMISSIONED": f"Error: Asset '{asset.asset_type} / {asset.asset_id}' is marked as decommissioned.",
        "BROKEN":         f"Error: Asset '{asset.asset_type} / {asset.asset_id}' is marked as broken.",
        "MISSING":        f"Error: Asset '{asset.asset_type} / {asset.asset_id}' is marked as missing.",
        "OUT_FOR_REPAIR": f"Error: Asset '{asset.asset_type} / {asset.asset_id}' is marked as out for repair.",
    }

    last_error = status_error_messages.get(
        asset.asset_status, f"Error: Asset is currently not available (status={asset.asset_status})."
    )

    return last_error


# Count the number of " same type " assets already issued to the entity
# Returns: Tuple( bool charge_limit_exceeded, str error_message )
#          if the asset is over-limit, True is returned ('False' means OK)
#          if there was a problem, error_message is returned (""  means OK)
def asset_validate( asset: Asset, issued_assets: List[ Asset ] ) -> Tuple[ bool, str ]:
    
    # First, check on if this is a duplicated book
    ( overlimit, error_message) = book_is_checked_out( asset, issued_assets )
    if overlimit:
        return ( overlimit, error_message)

    if asset.charge_limit is None:
        return ( False, "" ) # No limits, no error

    # Count the number of same-type assets already issued to the entity
    issued_same_type_count = sum(
        1
        for issued_asset in issued_assets
        if issued_asset.asset_type == asset.asset_type
    )

    # Enforce charge limit, using the already-issued number of this type of asset
    if issued_same_type_count >= asset.charge_limit:
            return ( True, f"Error: Entity already has the maximum number of {asset.asset_type} issued." )
                
    return ( False, "" ) # No problem, no error


# Function creates new 'transactions' and 'issued_assets' rows in the DB
# for issuing the given asset to the given entity
#
# TODO: Might be smart to safeguard against various bad things
# TODO:   a) checking out an asset multiple times (to the same or different people)
# TODO:   b) verifying accessories are checked out in their separate table
# TODO:   c) other nefarious things I am overlooking at the moment...
# TODO: Also, proper OOP would return a Transaction, not just its ID
def incarcerated_create_asset_issue_transaction( asset: Asset, entity: Entity ) -> int:
    """
    Creates an 'ISSUED' transaction and inserts an asset or accessory into
    its appropriate checked-out table. This function assumes the asset has 
    already been vetted for checkout.

    Args:
        asset  (Asset) : the Asset to issue
        entity (Entity): the entity checking out the asset
    """
    try:
        connection = connect_to_database()
        cursor = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cursor.execute(
            """
            INSERT INTO transactions ( entity_id, asset_id, transaction_type, transaction_notes ) 
            VALUES ( %s, %s, %s, %s )
            RETURNING transaction_id;
            """,
            ( entity.entity_id, asset.asset_id, 'ISSUED', f"Issued by '{os.getlogin()}'." ),
        )
    
        transaction_id = cursor.fetchone()[0]

        connection.commit() # Save the INSERT
        
        # Insert a record into issued_assets or issued_accessories
        if isinstance( asset, Accessory ):
            # Insert a record into issued_accessories and add entity / transaction to asset
            cursor.execute(
                """
                INSERT INTO issued_accessories (asset_id, entity_id, transaction_id) 
                VALUES (%s, %s, %s);
                """,
                ( asset.asset_id, entity.entity_id, transaction_id, ),
            )
            asset.issued_to   = entity
            asset.transaction = Transaction.from_id( transaction_id )
        else:
            # Insert a record into issued_assets
            cursor.execute(
                """
                INSERT INTO issued_assets (asset_id, transaction_id) 
                VALUES (%s, %s);
                """,
                ( asset.asset_id, transaction_id, ),
            )
        
        connection.commit() # Save the INSERT
        cursor.close()
        connection.close()
        
        return transaction_id
    
    except Exception as e:
        # In case of error, roll back and report the failure
        if connection is not None:
            connection.rollback()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        
        # TODO: Make this look better (quote args & strip whitespace?)
        display_verbose_error(
                f"Exception in incarcerated_create_asset_issue_transaction(" + 
                f"\n\t'{asset}',\n\t'{entity}' ):"
                , e
        )

        return 0 # transaction ID == 0 flags an error
    
    return -1 # "You can't return from here"


# TODO: Same issues as create_transaction_from_issuing...
def incarcerated_transaction_agreement_document( entity: Incarcerated, transaction_id: int ) -> int:
    try:
        connection = connect_to_database()
        cursor = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cursor.execute(
            """
            SELECT d.document_id
            FROM documents d
            JOIN transaction_documents td ON d.document_id = td.document_id
            JOIN transactions t ON td.transaction_id = t.transaction_id
            WHERE
                t.entity_id = %s
                AND d.document_type = 'AGREEMENT'
                AND d.document_printed_timestamp IS NULL
            LIMIT 1;
            """,
            ( entity.entity_id, ),
        )

        existing_document = cursor.fetchone()

        if existing_document:
            agreement_document_id = existing_document[0]
        else:
            # Insert a new agreement document if there isn't an unprinted one
            cursor.execute(
                """
                INSERT INTO documents (document_type)
                VALUES ('AGREEMENT')
                RETURNING document_id;
                """,
            )
            agreement_document_id = cursor.fetchone()[0]
            connection.commit() # Save the INSERT

        # Link the document with the transaction
        cursor.execute(
            """
            INSERT INTO transaction_documents (transaction_id, document_id)
            VALUES (%s, %s);
            """,
            ( transaction_id, agreement_document_id, ),
        )

        connection.commit() # Save the INSERT
        cursor.close()
        connection.close()

        return agreement_document_id
    
    except Exception as e:
        # In case of error, roll back and report the failure
        if connection is not None:
            connection.rollback()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        
        # TODO: Make this look better (quote args & strip whitespace?)
        display_verbose_error(
                f"Exception in incarcerated_transaction_agreement_document(" + 
                f"\n\t'{entity}',\n\t'{transaction_id}' ):"
                , e
        )

        return 0 # agreement document ID == 0 flags an error


# Function creates a laptop labels document in the database and
# links it with the related transaction_id
def create_laptop_labels( transaction_id: int ) -> None:
    try:
        connection = connect_to_database()
        cursor = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cursor.execute(
            """
            INSERT INTO documents (document_type)
            VALUES ('LABELS')
            RETURNING document_id;
            """,
        )

        labels_document_id = cursor.fetchone()[0]

        connection.commit() # Save the INSERT

        # Link labels document with the transaction
        cursor.execute(
            """
            INSERT INTO transaction_documents (transaction_id, document_id)
            VALUES (%s, %s);
            """,
            ( transaction_id, labels_document_id, ),
        )

        connection.commit() # Save the INSERT
        cursor.close()
        connection.close()

        return
    
    except Exception as e:
        # In case of error, roll back and report the failure
        if connection is not None:
            connection.rollback()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        
        # TODO: Make this look better (quote args & strip whitespace?)
        display_verbose_error(
                f"Exception in create_laptop_labels( '{transaction_id}' ):"
                , e
        )

        return


def issue_charger( transaction_id: int, entity: Entity ) -> Charger:
    """
    Issues an entity a charger, using the transaction_id (presumably
    from the associated laptop check-out).  This function assumes the entity
    has been vetted and does not already have a charger. If they already have
    a charger, this function will print an error message.
    """
    try:
        while True:
            charger_barcode = input_with_color( "Please, scan the charger barcode for this laptop: " )

            if charger_barcode == "":
                continue # re-run the barcode prompt

            charger_asset = Asset.from_id( charger_barcode )
            if isinstance( charger_asset, Charger ):
                break # move on to issuing the charger

        connection = connect_to_database()
        cursor = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cursor.execute(
                """
                INSERT INTO issued_accessories (asset_id, entity_id, transaction_id) 
                VALUES (%s, %s, %s);
                """,
                ( charger_asset.asset_id, entity.entity_id, transaction_id, ),
        )
        # Add the entity and transaction to this Accessory object
        charger_asset.issued_to = entity
        charger_asset.transaction = Transaction.from_id( transaction_id )

        connection.commit() # Save the INSERT
        cursor.close()
        connection.close()

        return charger_asset

    except Exception as e:
        # In case of error, roll back and report the failure
        if connection is not None:
            connection.rollback()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        
        display_verbose_error(
                f"Exception in issue_charger(" +
                f" '{transaction_id}', '{entity}' )." +
                f"\nError: This person can not be issued (another?) charger."
                , e
        )

        return None


def issue_headphones( transaction_id: int, entity: Entity ) -> Headphones:
    """
    Issues an entity a set of headphones, using the transaction_id (presumably
    from the associated laptop check-out).  This function assumes the entity
    has been vetted and does not already have headphones. If they already have
    headphones, this function will print an error message.
    """
    try:
        while True:
            headphones_barcode = input_with_color( "Please, scan the HEADPHONES barcode for this laptop ('ENTER' for none): " )

            if headphones_barcode == "":
                return None # we don't have headphones or the student doesn't want them

            headphones_asset = Asset.from_id( headphones_barcode )

            if isinstance( headphones_asset, Headphones ):
                break # move on to issuing the headphones

        connection = connect_to_database()
        cursor = connection.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cursor.execute(
                """
                INSERT INTO issued_accessories (asset_id, entity_id, transaction_id) 
                VALUES (%s, %s, %s);
                """,
                ( headphones_asset.asset_id, entity.entity_id, transaction_id, ),
        )
        # Add the entity and transaction to this Accessory object
        headphones_asset.issued_to = entity
        headphones_asset.transaction = Transaction.from_id( transaction_id )

        connection.commit() # Save the INSERT
        cursor.close()
        connection.close()

        return headphones_asset

    except Exception as e:
        # In case of error, roll back and report the failure
        if connection is not None:
            connection.rollback()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        
        display_verbose_error(
                f"Exception in issue_headphones(" + 
                f" '{transaction_id}', '{entity}' ):" +
                f"\nError: This person can not be issued (another?) headphones."
                , e
        )

        return None


# Function prompts for a charger to be returned with its laptop
# Returns: True / False, indicating if the charger was returned
def return_charger( transaction: Transaction ) -> bool:
    returned_charger = input_yes_no_only( "Did student return the charger (both halves)? (Y/N)" )

    if returned_charger == "Y":
        try:
            if transaction and transaction.entity_id:
                this_entity_id = transaction.entity_id
            elif transaction and transaction.entity and transaction.entity.entity_id:
                this_entity_id = transaction.entity.entity_id
            else:
                display_verbose_error( f"Error: return_laptop_charger:\n\tNo entity (ID) reference in '{transaction}'." )
                return False
            
# TODO: Put these 8 lines (+ except clause) into EduDbObject.execute_delete(try: 'DELETE ...')
            conn = connect_to_database()
            cursor  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

            # we may not have the right transaction for the charger, so look it up
            cursor.execute(
                """
                    SELECT
                        issued_accessories.asset_id
                	FROM
                        issued_accessories, assets
                    WHERE
                        assets.asset_type = 'CHARGER' AND
                        assets.asset_id = issued_accessories.asset_id AND
                        issued_accessories.entity_id = %s
                    """,
                    ( this_entity_id, ),
            )

            data = cursor.fetchone()

            if data is None:
                return False
            else:
                this_asset_id = data[0]
                # Note: It is best to refer to only ONE table in a delete.
                #       Using " table.column = %s " creates strange errors
                cursor.execute(
                    """
                        DELETE FROM
                            issued_accessories
                        WHERE
                            asset_id = %s AND
                            entity_id = %s
                    """,
                    ( this_asset_id, this_entity_id, ),
                )

            conn.commit() # Save the DELETE
            cursor.close()
            cursor = None
            conn.close()
            conn = None

            print(Color.BRIGHT_GREEN.value + "Thank you!" + Color.DEFAULT.value) # green for success

        except Exception as e:
            # In case of error, roll back and report the failure
            if conn is not None and cursor is not None:
                conn.rollback()
            if cursor is not None:
                cursor.close()
                cursor = None
            if conn is not None:
                conn.close()
                conn = None

            display_verbose_error(
                    f"Exception in return_charger(" + 
                    f" '{transaction}' ):" +
                    f"\nWarning: Charger may (or may not) have been returned, anyway."
                    , e
            )

        return True

    else:
        display_error( "Tell this student to watch for the 'GHC asset return' call-out." )
        return False

    return False # "You can't return from here"


def accessory_find_laptop_transaction_id( asset: Accessory ) -> int:
    """
    Finds the latest laptop check-out, based on accessory.issued_to.entity_id.

    Args:
        asset (Asset): an Accessory object

    Returns:
        int: transaction for the ISSUED Laptop
    """

    conn = connect_to_database()
    cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

    cur.execute(
        """
        SELECT
            transactions.transaction_id
        FROM
	        transactions
        WHERE
	        transactions.entity_id = %s
	        transactions.transaction_type = 'ISSUED'
        ORDER BY
            transactions.transaction_id DESC
        LIMIT 1;
        """,
        ( asset.issued_to.entity_id, )
    )
    
    data = cur.fetchone()

    cur.close()
    conn.close()

    if not data:
        return None
    
    return data["transaction_id"]


# TODO: If " Asset.issued_transaction( self ) " works (v 1.4), move this into the class
def asset_issued_transaction( asset: Asset ) -> Transaction:
    """
        Finds a Transaction for an asset check-out, if they are linked
        through the issued_assets table. Otherwise, this returns 'None'.

        Args:
            asset (Asset): asset to be queried

        Returns:
            transaction: the related 'ISSUED' Transaction object (or 'None')
    """

    # If this is an accessory, we already have the transaction ID
    if isinstance( asset, Accessory ):
        if asset and asset.transaction is not None:
            transaction = asset.transaction
        else:
           return None

        transaction.asset = asset # graft in accessory as our asset
        return transaction

    conn = connect_to_database()
    cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

    # Check for the ISSUED transaction ties to this asset
# TODO: Streamline this query (SELECT transaction_id) and use
#       " return Transaction.from_id( transaction_id ) "
#       to be more error-hardened and change-malleable.
    cur.execute(
        """
        SELECT
            transactions.transaction_id,
            transactions.entity_id,
            transactions.transaction_type,
            transactions.transaction_timestamp,
            transactions.transaction_user,
            transactions.transaction_notes
        FROM
            transactions, assets, issued_assets
        WHERE
            assets.asset_id = %s
            AND assets.asset_id = issued_assets.asset_id
            AND issued_assets.transaction_id = transactions.transaction_id
        ORDER BY
            transactions.transaction_timestamp DESC,
            transactions.transaction_id
        LIMIT 1;
        """,
        ( asset.asset_id, ),
    )

    data = cur.fetchone()

    cur.close()
    conn.close()

    if not data:
        return None

    return Transaction(
            data["transaction_id"],
            data["entity_id"],
            asset,
            data["transaction_type"],
            data["transaction_timestamp"],
            data["transaction_user"],
            data["transaction_notes"],
    )


# TODO: If " Asset.latest_transaction( self ) " works (v 1.4), move this into the class
def asset_latest_transaction( asset: Asset ) -> Transaction:
    """
        Finds the latest Transaction involving the given asset

        Args:
            asset (Asset object): asset to be queried

        Returns:
            Transaction: most recent transaction for this asset
    """
    conn = connect_to_database()
    cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

    # Check for existing asset
# TODO: Streamline this query -- like the last one --
#       (SELECT transaction_id) and use
#       " return Transaction.from_id( transaction_id ) "
#       to be more error-hardened and change-malleable.
    cur.execute(
        """
        SELECT 
            transactions.transaction_id,
            transactions.entity_id,
            transactions.transaction_type,
            transactions.transaction_timestamp,
            transactions.transaction_user,
            transactions.transaction_notes
        FROM 
            transactions
        WHERE
            transactions.asset_id = %s
        ORDER BY
            transactions.transaction_timestamp DESC,
            transactions.transaction_id
        LIMIT 1;
        """,
        ( asset.asset_id, ) )

    data = cur.fetchone()

    cur.close()
    conn.close()

    if not data:
        return None
    
    return Transaction(
            data["transaction_id"],
            data["entity_id"],
            asset,
            data["transaction_type"],
            data["transaction_timestamp"],
            data["transaction_user"],
            data["transaction_notes"],
    )


# Function to return an asset from a student
# May throw a 'NotImplementedError' exception
#       ==> unknown asset type
# Catches:
#       Exception
def return_assets() -> None:
    last_error = "" # Store the last error message
    transaction = None

    while True:
        clear_screen_and_print_ams_title()

        print_title("Return Assets", Color.BRIGHT_YELLOW, 100)

        if transaction:

            if transaction.asset:
                print_table(
                    transaction.asset.to_dataframe(),
                    "Returned Asset Information",
                    Color.BRIGHT_GREEN,
                    100,
                    print_headers=False,
                )

            # Use transaction (which gets set, below, in this 'while True' loop) ...
            # ... to create an Incarcerated object named returning_entity
            returning_entity = Incarcerated.from_id( transaction.entity_id )

            if not returning_entity: # IF     we can't find the returner's name
                if not last_error:   #    AND there's no (more urgent) error to report
                    last_error = "Student not found for entity {transaction.entity_id}"
            else:
                print_selected_incarcerated_in_table( returning_entity )
                issued_assets = list( returning_entity.assets() )
                print_issued_assets_table( issued_assets )

            # Release the Incarcerated object (pun intended)
            returning_entity = None

        # end ~ if transaction and transaction.asset:

        last_error = display_and_clear_error( last_error )

        asset_id = input_with_color( "Enter asset barcode to return:" )

        if not asset_id:
            break

        asset = Asset.from_id( asset_id ) # Creates an asset or a partial accessory

        if not asset:
            last_error = f"Return failed: Asset not found, for barcode '{asset_id}'"
            continue

        # Fill in an Accessory object by getting / passing in entity
        if isinstance( asset, Accessory ):
            ( doc_number, last_error ) = input_and_validate_doc()
            if last_error:
                continue # repeat loop
            if not doc_number:
                break

            selected_entity = Incarcerated.from_doc( doc_number )
            if not selected_entity:
                last_error = "Incarcerated Individual not found"
                continue
            asset = Accessory.from_ids( asset.asset_id, selected_entity.entity_id )

        if asset:
            transaction = asset_issued_transaction( asset )

        if asset and not transaction:
            transaction = asset_latest_transaction( asset )
            if not transaction:
                last_error =  "Return failed: Asset has never been issued"
            else:
                # Report asset's current state and who touched it last
                incarcerated = Incarcerated.from_id( transaction.entity_id )
                if not incarcerated:
                    display_verbose_error(
                            f"Error: return_assets: Cannot find " +
                            f"incarcerated for entity '{transaction.entity_id}'."
                    )

                last_error = f"Return failed: Asset '{asset}' was" + \
                                f" '{transaction.transaction_type}' on" + \
                                f" '{transaction.transaction_timestamp}' for" + \
                                f" '{incarcerated}'."
            continue

        # Returns an asset; 'last_error' may be a "success" message ...
        if transaction:
            ( last_error ) = transact_asset_return( transaction )

    # ...  end  of  while  True  loop  ...

    return

def get_transaction_history( object ) -> pd.DataFrame:
    base_query = """
        SELECT
            t.transaction_timestamp,
            t.transaction_id,
            t.transaction_type,
            a.asset_id,
            a.asset_type,
            i.doc_number,
            u.last_name,
            u.first_name,
            u.middle_name
        FROM transactions t
        LEFT JOIN assets a ON t.asset_id = a.asset_id
        LEFT JOIN incarcerated i ON t.entity_id = i.entity_id
        LEFT JOIN users u ON t.entity_id = u.entity_id
        WHERE {0}
        ORDER BY t.transaction_id ASC
        """
    
    if isinstance( object, Asset ):
        where_clause =  "t.asset_id = %s"
        parameters = (object.asset_id, )
    elif isinstance( object, Incarcerated ):
        where_clause =  "t.entity_id = %s"
        parameters = (object.entity_id, )
    else:
        raise ValueError("Unknown object type")
    
    # Combine the base query with the WHERE clause using string formatting
    query = base_query.format(where_clause)

    # Create a connection to the database
    try:
        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        # Execute SQL query with parameter substitution
        cur.execute(query, parameters )

        # Fetch all results from the executed query
        results = cur.fetchall()

        # Get the column names for the cursor
        column_names = [description[0] for description in cur.description]

        # Convert the results to a pandas DataFrame
        df = pd.DataFrame(results, columns=column_names)

        # Close the cursor  and connection
        cur.close()
        conn.close()
        
    except Exception as e:
        display_verbose_error(
                f"Exception during get_transaction_history( '{object}' ):"
                , e
        )

    return df


def transact_asset_return( transaction: Transaction ) -> str:
    if isinstance( transaction.asset, Accessory ):
        return transact_accessory_return(  transaction )
    else:
        return transact_true_asset_return( transaction )
    
    raise Exception( "Error: transact_asset_return(): Internal error." )


def transact_true_asset_return( transaction: Transaction ) -> str:
    try:
        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cur.execute( "BEGIN;" )

        # Delete row from issued_assets
        cur.execute(
            """
            DELETE FROM issued_assets
            WHERE asset_id = %s;
            """,
            ( transaction.asset.asset_id, ),
        )

        # Add RETURNED transaction to transactions table
        cur.execute(
            """
            INSERT INTO transactions ( entity_id, asset_id, transaction_type, transaction_notes )
            VALUES ( %s, %s, %s, %s )
            RETURNING transaction_id;
            """,
            ( transaction.entity_id, transaction.asset.asset_id, 'RETURNED', f"Returned by '{os.getlogin()}'." ),
        )

        conn.commit() # Save the DELETE and INSERT
        cur.close()
        conn.close()

        last_error = Color.BRIGHT_GREEN.value + "Asset(s) returned successfully!" + Color.DEFAULT.value # Green for success

        if transaction.asset.asset_type == "LAPTOP":
            return_charger( transaction )

    except Exception as e:
        if conn is not None:
            conn.rollback()
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
        last_error = f"Exception during transact_true_asset_return( '{transaction}' ):" + \
                     f"\nException text: {e}"

    return last_error


def transact_accessory_return( transaction: Transaction ) -> str:
    # If the accessory is headphones, deliver a scathing insult.
    # P.S. This is more general " if not transaction.asset.is_returnable(): "
    if transaction.asset.asset_type == 'HEADPHONES':
        return "Nobody wants used earwax! Keep these headphones. We insist..."

    try:
        conn = connect_to_database()
        cur  = conn.cursor( cursor_factory=psycopg2.extras.DictCursor )

        cur.execute( "BEGIN;" )

        # Delete row from issued_assets
        cur.execute(
            """
            DELETE FROM issued_accessories
            WHERE asset_id = %s  AND  entity_id = %s;
            """,
            ( transaction.asset.asset_id, transaction.entity_id, ),
        )

        # Create RETURNED transaction (Accessory and v 1.3 / v 1.4 friendly)
        cur.execute(
            """
            INSERT INTO transactions ( entity_id, asset_id, transaction_type, transaction_notes )
            VALUES ( %s, %s, %s, %s )
            RETURNING transaction_id;
            """,
            ( transaction.entity_id, transaction.asset.asset_id, 'RETURNED', f"Returned by '{os.getlogin()}'." ),
        )

        conn.commit() # Save the DELETE and INSERT.
                      # Even a one dollar donation can help save a query... :)
        cur.close()
        conn.close()
        
        last_error = Color.BRIGHT_GREEN.value + "Asset(s) returned successfully!" + Color.DEFAULT.value # Green for success

    except Exception as e:
        if conn is not None:
            conn.rollback()
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
        last_error = f"Exception during transact_accessory_return( '{transaction}' ):" + \
                     f"\nException text: {e}"

    return last_error


# May throw a 'NotImplementedError' exception
#       ==> unimplemented menu options
# May throw a 'ValueError' exception
#       ==> invalid menu choice
# Catches:
#       ValueError
#       NotImplementedError
#       pd.errors.EmptyDataError
#       pd.errors.ParserError
def student_menu() -> None:
    error_message = ""  # Initialize an empty string for the error message

    while True:
        print_student_menu()

        error_message = display_and_clear_error( error_message )

        choice = input_with_color( "Enter choice:" )

        try:
            if choice == "1":
                raise NotImplementedError("Option not implemented")
            elif choice == "2":
                raise NotImplementedError("Option not implemented")
            elif choice == "3":
                raise NotImplementedError("Option not implemented")
            elif choice == "4":
                raise NotImplementedError("Option not implemented")
            elif choice == "5":
                update_students_from_csv()
            elif choice == "6":
                export_students_to_csv()
            elif choice == "":
                break
            else:
                raise ValueError("Invalid choice")

        except (
            ValueError,
            NotImplementedError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            error_message = f"Error: student_menu:" + \
                            f"\nException text: {e}"


# May throw a 'NotImplementedError' exception
#       ==> unimplemented menu options
# May throw a 'ValueError' exception
#       ==> invalid menu choice
# Catches:
#       ValueError
#       NotImplementedError
#       pd.errors.EmptyDataError
#       pd.errors.ParserError
def inventory_menu() -> None:
    error_message = ""  # Initialize an empty string for the error message

    while True:
        print_inventory_menu()

        error_message = display_and_clear_error( error_message )

        choice = input_with_color( "Enter choice:" )

        try:
            if choice == "1":
                raise NotImplementedError("Option not implemented")
            elif choice == "2":
                raise NotImplementedError("Option not implemented")
            elif choice == "3":
                raise NotImplementedError("Option not implemented")
            elif choice == "4":
                raise NotImplementedError("Option not implemented")
            elif choice == "5":
                raise NotImplementedError("Option not implemented")
            elif choice == "6":
                raise NotImplementedError("Option not implemented")
            elif choice == "7":
                raise NotImplementedError("Option not implemented")
            elif choice == "8":
                raise NotImplementedError("Option not implemented")
            elif choice == "":
                break
            else:
                raise ValueError("Invalid choice")

        except (
            ValueError,
            NotImplementedError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            error_message = f"Error: inventory_menu:" + \
                           f"\nException text: {e}"


# May throw a 'NotImplementedError' exception
#       ==> unimplemented menu options
# May throw a 'ValueError' exception
#       ==> invalid menu choice
# Catches:
#       ValueError
#       NotImplementedError
#       pd.errors.EmptyDataError
#       pd.errors.ParserError
def image_menu() -> None:
    error_message = ""  # Initialize an empty string for the error message

    while True:
        print_image_menu()

        error_message = display_and_clear_error( error_message )

        choice = input_with_color( "Enter choice:" )

        try:
            if choice == "1":
                raise NotImplementedError("Option not implemented")
            elif choice == "2":
                raise NotImplementedError("Option not implemented")
            elif choice == "3":
                raise NotImplementedError("Option not implemented")
            elif choice == "4":
                raise NotImplementedError("Option not implemented")
            elif choice == "5":
                raise NotImplementedError("Option not implemented")
            elif choice == "6":
                raise NotImplementedError("Option not implemented")
            elif choice == "7":
                raise NotImplementedError("Option not implemented")
            elif choice == "8":
                raise NotImplementedError("Option not implemented")
            elif choice == "9":
                raise NotImplementedError("Option not implemented")
            elif choice == "10":
                raise NotImplementedError("Option not implemented")
            elif choice == "11":
                raise NotImplementedError("Option not implemented")
            elif choice == "12":
                raise NotImplementedError("Option not implemented")
            elif choice == "":
                break
            else:
                raise ValueError("Invalid choice")

        except (
            ValueError,
            NotImplementedError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            error_message = f"Error: image_menu:" + \
                           f"\nException text: {e}"


def render_list_as_menu( raw_list: list[str] ) -> None:
    """Render a Python list as a numbered menu.
    Also pretty-prints '.sql' file names (when present).

    Args:
        raw_list (list[str]): a list of strings to display
    """
    menu_list = ""
    show_title = True # HACK: show title, if this is not the .sql reports menu

    for idx in range(  len( raw_list )  ):
        if idx != 0:
            if raw_list[idx].endswith(".sql"):
                menu_item  = raw_list[idx][0].upper() # Capitalize first letter
                menu_item += raw_list[idx][1:-4]      # rest of string (w/o '.sql')
                menu_item  = " ".join( re.split( '_', menu_item ) ) # replace all '_'
                show_title = False                    # (supress title)
            else:
                menu_item  = raw_list[idx]            # Do not change the raw text
            if menu_list: menu_list += f"\n" # insert newline
            menu_list += f"{idx}. {menu_item}"
            
    menu_df = pd.DataFrame(
        {   
            "Column1": [
                menu_list,

                "Press Enter to exit the reports menu."
            ],
        }
    )

    if show_title:
        print_title( raw_list[0], width=100 )

    print_menu_sections(menu_df, min_width=100,)
    
    return


def print_reports_menu() -> List[ str ]:
    # clear_screen_and_print_ams_title()
    print_title("Reports", Color.BRIGHT_YELLOW, 100)

    raw_reports = collect_report_names()
    render_list_as_menu( raw_reports )

    return raw_reports


def collect_report_names() -> List[str]:
    reports_directory = f"{ SCRIPT_DIRECTORY }\\reports"
    
    report_files = [ reports_directory ] # element #0 is the directory

    for filename in os.listdir( reports_directory ):
        if filename.endswith( ".sql" ):
            report_files.append( filename )

    return report_files


def reports_menu() -> None:
    error_message = ""  # Initialize an empty string for the error message
    clear_screen() # Clear screen outside 'while' loop, so no messages get erased

    while True:
        # Print title, error/success message, then 'Reports' banner
        print_title( f"Asset Management System ( {VERSION_TITLE} )", Color.BRIGHT_YELLOW, 100)
        error_message = display_and_clear_error( error_message )
        reports = print_reports_menu()

        selection = 0
        choice = input_with_color( "Enter choice:" )
        if choice == "":
            break
        if choice.isdigit():
            selection = int( choice )
        if not selection:
            continue

        try:
            if selection >= 1 and selection < len(reports):
                error_message = process_report( selection, reports ) # may be 'success'
            else:
                error_message = f"Error: Invalid option, '{choice}'. Try again."
        except BaseException as e: # PsycoPG / Pandas / SQL throw various exceptions
            error_message = f"Error: Caught a (possibly fatal) exception in reports_menu:" + \
                           f"\nException text: {e}"

    return


def process_report( selected, report_names: List[str] ) -> str:

    if      not report_names or len( report_names ) <= 1 or \
            not isinstance( selected, int ) or selected < 1 or selected > ( len(report_names) -1 ):
        return f"Error: process_report( '{selected}', '{report_names}' )" + \
               f"\n\tInvalid selection, or report list is missing or empty."

    SQL_file    = report_names[selected] # name only
    SQLfilepath = os.path.join( report_names[0], SQL_file ) # relative path
    SQL_query   = "" # Build up SQL query string here
    kwargs      = {} # Build parameters dictionary here

    SQLinput = open( SQLfilepath, 'r' )
    for line in SQLinput:
        (SQL_query, kwargs) = replace_SQL_variables( line, SQL_query, **kwargs )

    return execute_sql_query( SQL_query, report_names[0], SQL_file, **kwargs )


# TODO: Shorten this function by splitting it into
# #     execute_sql_import() and execute_sql_export()
def execute_sql_query( SQL_query: str, report_dir: str, SQL_file: str, **kwargs ) -> str:
    """Excute_report: Runs a SQL query, which reads/writes data
    from/to a CSV file. Inserts parameters using dict keys.
    Args:
        SQL_query     (str): the SQL query to run
        report_dir    (str): relative path to SQL file
        SQL_file      (str): script name
        kwargs (dictionary): SQL query parameters
    Returns:
        str: a printable success / failure message
    """

    report_csv     = f"{SQL_file[:-4]}.csv" # name only + '.CSV'
    AMS_import     = kwargs.get( 'AMS_import', False)
    skip_filesave  = False # skip this, if pd.read_sql_query( ... ) throws an exception
    file_path      = None  # ensure this is always defined before its use, below
    import_success = False # Set 'True', if we do an import and it suceeds

    if AMS_import:
        try:
            file_path = open_input_csv( report_dir, report_csv )
            if file_path is None:
                return f"Warning: Import for '{report_csv}' was cancelled."
            process_input_csv( file_path, SQL_query, **kwargs )
            skip_filesave = True # no need to save an import to CSV output (or is there?)
            import_success = True
            dummy = input_with_color() # pause, so user sees "Imported / updated: ... " lines

        except Exception as e: # intercept and print any Exception (it's probably ours)
            display_error( f"Error: execute_sql_query(): SQL import failed from files:" +
                    f"\n\tSQL script: '{SQL_file}' and import values {file_path}" +
                    f"\nException text: {e}" )
            skip_filesave = True

    else: # CSV file is for output (and) SQL query is fully qualified
        try:
            database = EduDbObject()
            database.connect()

            with warnings.catch_warnings():
                warnings.simplefilter("ignore") # ignore "pandas only supports SQLAlchemy / sqlite"
                df = pd.read_sql_query( SQL_query, database.connection )
            database.disconnect() # clean up
        except Exception as e: # intercept and print any Exception
            display_error( f"Error: execute_sql_query(): SQL query failed with file:" +
                    f"\n\tSQL script: '{SQL_file}'" +
                    f"\nException text: {e}" )
            if isinstance( e, TypeError ):
                print( "Triage: 'NoneType not iterable' means your last SQL statement needs a 'RETURNING xxx' clause." )
            database.disconnect() # clean up
            skip_filesave = True

    if not skip_filesave:
        file_path = open_output_csv( report_dir, report_csv )

        if file_path:
            # Export the dataframe
            df.to_csv( file_path, index=False )
            return Color.BRIGHT_GREEN.value + \
                f"SQL query results saved to '{file_path}'." + \
                Color.DEFAULT.value
        else:
            return f"Warning: Report for '{report_csv}' was cancelled."

    else:
        if  ( skip_filesave and not import_success ) \
            or file_path is None:
            return f"Warning: Report for '{report_csv}' was cancelled."
        else:
            if AMS_import:
                return Color.BRIGHT_GREEN.value + \
                       f"SQL insert executed from input file, '{file_path}'." + \
                       Color.DEFAULT.value
            else:
                return Color.BRIGHT_GREEN.value + \
                       f"SQL query results saved to '{file_path}'." + \
                       Color.DEFAULT.value


# Helper function, opens an input filename
def open_input_csv( report_dir, report_csv ) -> str:
    # Use tkinter to prompt the user to choose where to save the file and under what name
    tk_directory  = os.path.join( SCRIPT_DIRECTORY, report_dir )
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
            defaultextension = ".csv",
            filetypes   = [ ( "CSV Files", "*.csv" ) ],
            initialdir  = tk_directory,
            initialfile = report_csv
    )
    return file_path


def open_output_csv( report_dir, report_csv ) -> str:
    # Use tkinter to prompt the user to choose where to save the file and under what name
    tk_directory  = os.path.join( SCRIPT_DIRECTORY, report_dir )
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(
            defaultextension = ".csv",
            filetypes   = [ ( "CSV Files", "*.csv" ) ],
            initialdir  = tk_directory,
            initialfile = report_csv
    )

    return file_path


# TODO: Break this up into " for column_name " chunk and " rest "
#       (re-evaluate each new subroutine's length)
def process_input_csv( file_path, SQL_query, **kwargs ) -> str:
    database = EduDbObject()
    database.connect()
    DeBuG = False # 'DEBUG' is a built-in, so mix it up ...
    
    kwargs = get_database_column_properties( **kwargs )

    with open( file_path, mode='r', newline='' ) as csvfile:
        reader = csv.reader( csvfile )

        # read columns, then remove the byte-order mark from column 0
        columns = reader.__next__()
        # '.*?' matches as little as possible, ideally nothing at all
        match = re.match( r"^(.*?)([a-zA-Z0-9_]*)$", columns[0] )
        ( bom, first_col ) = ( match.group(1), match.group(2) )
        columns[0] = first_col

        AMS_nullable = kwargs.get("AMS_nullable", [])
        AMS_coltypes = kwargs.get("AMS_coltypes", {})

        for row in reader:
            if len( row ) == 0: # skip over blank rows
                continue

            row_dict = dict(  zip( columns, row )  ) # column->key, datum->value
            row_kwargs = kwargs | row_dict # merges defaults with row-specific keys

            # apply AMS_nullable, where needed
            for column_name in AMS_coltypes:
                data_type    = row_kwargs['AMS_coltypes'].get( column_name, 'NO_DATA_TYPE' )
                column_value = row_kwargs.get( column_name, 'NO_VALUE' )
                if column_name in AMS_nullable:
                    is_nullable   = True
                else:
                    is_nullable   = False

                if DeBuG: print( f"Debug: Examining '{column_name}'\t\tValue?: '{column_value}'\t\tNullable?: '{is_nullable}'\t\tData type: '{data_type}'." )
                if column_value == '' and is_nullable:
                    if DeBuG: print( f"Debug: Detected '{column_name}' (== '{column_value}') is empty and nullable." )
                    row_kwargs[column_name] = "NULL"
                elif data_type == 'numeric' or data_type == 'integer':
                    if DeBuG: print( f"Debug: Detected '{column_name}' (== '{column_value}' / '{data_type}') is numeric. (not quoted)" )
                    pass
                elif column_value != 'NO_VALUE': # quote this parameter
                        if DeBuG: print( f"Debug: Detected '{column_name}' (== '{column_value}') is defined and/or non-nullable." )
                        # column_value =~ s/'/''/ BOOGA BLEGGA
                        column_value = re.sub(r"'", r"''", column_value )
                        row_kwargs[column_name] = f"'{column_value}'"

            try:
                # See replace_python_parameters() for the other use of '%'
                SQL_import_row = SQL_query % row_kwargs
            except KeyError as e:
                display_error( f"Error: execute_sql_query(): Python 'string % dict' failed for the following query:" +
                            f"\nException text: {e}" +
                            f"\nSQL query     : '{SQL_query}'" )
                raise e # Jump back to reports_menu( ... )
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore") # ignore "pandas only supports SQLAlchemy / sqlite"
                df = pd.read_sql_query( SQL_import_row, database.connection )
                # dataframe, indexed by first column's name, first item in list
                # If the SQL query has " RETURNING not_column_0 " then 'AMS_returning'
                # needs to be defined in the SQL query's :defaults => { 'AMS_returning':
                # 'book_title' }. The usual assumption is RETURNING sends back column 0.
                update_column = row_kwargs.get( 'AMS_returning', columns[0] )
                row_identifier = df[ update_column ][0]
                print( f"Imported / updated: '{row_identifier}'" )

    database.commit() # save the database changes

    return


def get_database_column_properties( **kwargs ) -> dict:
    """Reads the column properties from the information_schema for each
    table listed in " kwargs['AMS_insert_tables'] ", so we know which columns
    are numeric (not to be quoted), text (requiring quotes), and timestamps
    (not seen in a SQL insert yet -- perhaps as " #time# "?)

    Returns:
        kwargs: A key-word arguments dictionary with these added entries:
            'AMS_nullable' -- columns which may   be NULL (empty CSV strings are NULL)
             'AMS_notnull' -- columns which can't be NULL (empty CSV strings are  '' )
            'AMS_coltypes' -- the type of each column (a cache, for debugging queries)
    """
    database = EduDbObject()
    # collect column_name values WHERE is_nullable == 'YES' / 'NO'
    kwargs['AMS_nullable'] = [] # start with an empty list
    kwargs['AMS_notnull' ] = [] # start with an empty list
    kwargs['AMS_coltypes'] = {} # start with an empty dictionary

    for table in kwargs.get( 'AMS_insert_tables' , [] ):
        columns_list_dict = database.fetch_rows(
                "column_name, is_nullable, data_type", # SELECT
                "information_schema.columns",          # FROM
                "table_name = %s",                     # WHERE
                (table,)                               # param(s) w/ trailing ','
        )
        for coldict in columns_list_dict:
            column_name   = coldict['column_name'] # aliases for dict keys and the
            is_nullable   = coldict['is_nullable'] # existing type (if defined) for
            data_type     = coldict['data_type'  ] # the current column's data type
            prior_coltype = kwargs['AMS_coltypes'].get( column_name, 'AMS_UNDEF')

            # Save the current column's data type and nullability
            # (May overwrite the data type or generate conflicting nullability setting)
            kwargs['AMS_coltypes'][column_name] = data_type

            if      is_nullable == 'YES':
                kwargs['AMS_nullable'].append( column_name )
            elif    is_nullable == 'NO':
                kwargs['AMS_notnull' ].append( column_name )
            else:
                display_error( f"Error: execute_sql_query(): " + \
                                f"Column '{column_name}'" + \
                                f" in table '{table}' should have " + \
                                f"an is_nullable value of YES/NO, but" + \
                                f" it is '{is_nullable}'!" )

            # Highlight any inter-table inconsistency with data type / nullable values
            # for same-named columns
            if      ( column_name in kwargs['AMS_nullable'] and is_nullable == 'NO'  ) or \
                    ( column_name in kwargs['AMS_notnull' ] and is_nullable == 'YES' ):
                display_error( f"Warning: {column_name} has inconsistent " + \
                               f"'is_nullable' properties in two or more of " + \
                               f"these tables:\n" + \
                               f"{kwargs['AMS_insert_tables']}" )
            if      data_type != prior_coltype  and prior_coltype != 'AMS_UNDEF':
                display_error( f"Warning: {column_name} has inconsistent 'data_type' " + \
                               f"properties ('{prior_coltype}' and '{data_type}') in " + \
                               f"two or more of these tables:\n" + \
                               f"{kwargs['AMS_insert_tables']}" )
        # end ~~ for column in table
    # end ~~ for table in tables

    # If we have import file "column names" of an unknown type to the database,
    # then we can use a line like this in the import file to set the right column types:
    # #   -- :defaults => { 'AMS_coltypes_overrides': { 'DOC_NUMBER': 'character varying', ... } }
    for entry in kwargs.get( 'AMS_coltypes_overrides' , {} ):
            kwargs['AMS_coltypes'][entry] = kwargs['AMS_coltypes_overrides'][entry]

    return kwargs


# SQLAlchemy parameter replacement syntax is like this:
#     SELECT * from assets WHERE asset_id = ':asset_id'
#
# Python printf-like syntax is like this:
#     SELECT * from assets WHERE asset_id = %(asset_id)s
#
# Substitute the first kind, always, and substitute the second
# kind, if this is not an import script (in which case, we will
# get to it later).
#
def replace_SQL_variables( line: str, SQL_query: str = '', **kwargs ) -> Tuple[ str, dict ]:
    """
    Replaces ':this_kind' of variables in a SQL query. If the query is not
    marked as an 'AMS_import' query, '%(these_kind)s' of variables are also
    replaced. If the SQL query line starts with '-- ' it may be a parameter
    definition as a list, dictionary, or prompt.

    Args:
        line (str): Current line of SQL to scan &/or substitute into
        SQL_query:  The 'SQL_query' lines (so far...)
        kwargs:     A dictionary of known options

    Returns:
        SQL_query: The input 'SQL_query' with 'line' suffixed with
        SQLAlchemy (and printf-style?) parameters replaced.
        kwargs:    Updated dictionary of SQL parameters
    """
    AMS_import = kwargs.get( 'AMS_import', False ) # 'False' if undefined

    if line.startswith("---") or line.startswith("\n"):
        return ( SQL_query, kwargs ) # no directive or SQL text? Skip it!
    
    elif line.startswith("-- "):
        ( SQL_query, kwargs ) = read_SQL_report_parameter( line, SQL_query, **kwargs )
        return ( SQL_query, kwargs )
    
    else:
        # process a SQL query fragment:
        # A) Replace parameters " :like_this "
        ( SQL_line, kwargs ) = replace_SQLAlchemy_parameters( line, SQL_query, **kwargs )
        # B) Replace parameters " %(like_this)s "
        #    (these replacements are deferred for import scripts)
        if not AMS_import:
            ( SQL_line, kwargs ) = replace_Python_parameters( SQL_line, SQL_query, **kwargs )
        # C) add the fragment to the built-up SQL query string
        SQL_query += SQL_line
        return ( SQL_query, kwargs )

    return( SQL_query, kwargs ) # If the code changes, this may be returned...


def replace_SQLAlchemy_parameters( line: str, SQL_query: str, **kwargs ) -> Tuple[ str, dict ]:
    """
    Make these parameter substitutions, returning modified line:
       SELECT asset_id FROM assets WHERE asset_id = ':asset_id'
    Arguments:
        line      (str): line in which to look for parameters
        SQL_query (str): Pre-screened SQL query text (read-only)
        kwargs   (dict): known parameters dictionary (modifed)
    Returns a tuple of:
        SQL_line (str): modified 'line'
        kwargs  (dict): updated parameters dictionary
    """
    SQL_line = line # assume no changes

    # SQLAlchemy requires parameters " :like_this "
    #    (But, we must skip any " :: " we see, so there
    #     is a " (?<!:) " zero-width negative look-behind assertion
    while re.search( r"(?<!:)\:[a-zA-Z0-9_]",  SQL_line ):
        parameter_isolation = re.match(
                r"""            # (raw) triple-quoted regular expression
                ^ (.*?)         # group(1) matches everything before the first ':'
                (?<!:)          # zero-width negative look-behind assertion
                                # (this skips past any doubled ':' characters)
                \:              # " :parameter " starts with " : "
                ([a-zA-Z0-9_]+) # group(2) matches the parameter name (alphanumeric + '_')
                (.*?) $ """,    # group(3) matches everything after :{parameter}
                SQL_line,       # <-- MATCH IN THIS STRING
                re.VERBOSE      # ignore comments/whitespace in the r'' string
        )

        if parameter_isolation:
            pre_match  = parameter_isolation.group(1)
            parameter  = parameter_isolation.group(2)
            post_match = parameter_isolation.group(3)

            if kwargs.get( parameter, None ) is None:
                # Print a descriptive warning message
                display_error( Color.BRIGHT_YELLOW.value + f"Warning: Parameter, " +
                        f"'{parameter}' undefined in current SQL fragment:" +
                        f"\n\n{SQL_query}\n{SQL_line}\n\t{pre_match}  " +
                        Color.BRIGHT_RED.value +
                        f"MISSING PARAMETER --> :{parameter} <-- MISSING PARAMETER" + 
                        Color.BRIGHT_YELLOW.value +
                        f"  {post_match}" +
                        Color.DEFAULT.value
                )
                # Use replace_SQL_variables( ... ) to prompt for a value
                try:
                    (SQL_line, kwargs) = replace_SQL_variables(
                            f"-- :{parameter} => Enter a value for this parameter (<ENTER> will leave it blank)",
                            SQL_line,
                            **kwargs
                    )
                except Exception as e: # intercept and print any Exception
                    display_error( f"Error: replace_SQLAlchemy_parameters(): Can't handle '{SQL_line}'" +
                           f"\nException text: {e}" )

            SQL_line = f"{ pre_match }" + \
                       f"{ kwargs.get( parameter, '' ) }" + \
                       f"{ post_match }"

    # end ~ while search for ':this' in SQL_line ...

    return( SQL_line, kwargs )


def replace_Python_parameters( line: str, SQL_query: str, **kwargs ) -> Tuple[ str, dict ]:
    """
    Make these parameter substitutions, returning modified line:
       SELECT asset_id FROM assets WHERE asset_id = %(asset_id)s
    Arguments:
        line      (str): line in which to look for parameters
        SQL_query (str): Pre-screened SQL query text (read-only)
        kwargs   (dict): known parameters dictionary (modifed)
    Returns a tuple of:
        SQL_line (str): modified 'line'
        kwargs  (dict): updated parameters dictionary
    """
    SQL_line = line # assume no changes

    parameters = re.findall( r'%\(([a-zA-Z0-9_]+)\)', SQL_line )
    made_a_replacement = False # prevent over-eager use of string '%'

    for param in parameters:
        print(f"replace_Python_parameters: Examining '{param}'.")
        made_a_replacement = True
        if kwargs.get( param, None) == None:
            # Unknown key? Add it to the dictionary
            (SQL_query, kwargs) = replace_SQL_variables(
                    f"-- :{param} => Enter a value for this parameter (<ENTER> will leave it blank)",
                    SQL_query,
                    **kwargs
            )

    try:
        # Avoid processing SQL wildcards like this:
        # >>>  WHERE scheduled_quarter LIKE '%Summer%'
        # If the text needs both %(this)s and SQL '%' wildcards,
        # in the same line, double up the SQL wildcard, as '%%'.
        if made_a_replacement:
            # See also execute_sql_query() for the other use of '%'
            SQL_line = line % kwargs # substitute, using dictionary keys/values

    except KeyError as e:
        display_error( f"Error: replace_Python_parameters(): Python 'string % dict' failed for '{SQL_line}'" +
                       f"\nException text: {e}" )
        raise e # Jump back to reports_menu( ... )

    return( SQL_line, kwargs )


def read_SQL_report_parameter( line: str, SQL_query: str, **kwargs ) -> Tuple[ str, dict ]:
    """There are three kinds of parameters to read:
    A  )  List ---- :param    => ['option a', 'option b', 'option c']
     B )  Dict ---- :defaults => {'source': 'BOOK', 'Columbus': 1492}
    C  )  Prompt -- :year     => Enter a four-digit year
    This function reads the parameter from the file and (unless it's a dict)
    presents it to the user for a decision. Dicts set parameter defaults."""

    # A) Parse a list -- :param => ['a', 'b', 'c']
    key_list = re.match( r"""   # (raw) triple-quoted regular expression
            ^ -- \s+ :  # Start of line, leading dashes, space(s), colon ':'
            (.*?) \s+   # group(1) matches variable (not the ':') and space(s)
            \=\> \s+    # followed by '=>' and more whitespace(s)
            (\[.*\])    # group(2) matches '[' then list item(s) then ']'
            \s* $ """,  # with optional trailing whitespace and end of line
            line,       # <-- MATCH IN THIS STRING
            re.VERBOSE  # ignore comments/whitespace in the r'' string
    )
    
    if key_list:
        key      = key_list.group(1)
        raw_list = key_list.group(2)
        real_list: List[str] = ast.literal_eval( raw_list )
        real_list.insert(
                0, # inserts this header before all the options
                f":{key} - choose one of the below options, " +
                f"or enter a parameter value"
        )
        value = report_parameter_from_list( real_list )
        if value == '':
            raise Exception( "Exited the reports menu.")
        kwargs[key] = value # save the chosen value for later use
        # return 'SQL_query' unchanged and 'kwargs' with an added entry
        return ( SQL_query, kwargs )

    # Parse a dict -- :defaults => {'source': 'BOOK', 'Columbus': 1492}
    key_dict = re.match( r"""   # (raw) triple-quoted regular expression
            ^ -- \s+ :  # Start of line, leading dashes, space(s), colon ':'
            (.*?) \s+   # group(1) matches variable (not the ':') and space(s)
            \=\> \s+    # followed by '=>' and more whitespace(s)
            (\{.*\})    # group(2) matches '{' then dict item(s) then '}'
            \s* $ """,  # with optional trailing whitespace and end of line
            line,       # <-- MATCH IN THIS STRING
            re.VERBOSE  # ignore comments/whitespace in the r'' string
    )

    if key_dict:
        key      = key_dict.group(1)
        raw_dict = key_dict.group(2)
        real_dict: dict[str,str] = ast.literal_eval( raw_dict )
        kwargs = real_dict | kwargs # copy real_dict, then override with kwargs
        # return 'SQL_query' unchanged and 'kwargs' with an added entry(-ies)
        return ( SQL_query, kwargs )

    # Parse a prompt -- :param Enter a year, or something clever
    key_prompt = re.match( r"""   # (raw) triple-quoted regular expression
            ^ -- \s+ :  # Start of line, leading dashes, space(s), colon ':'
            (.*?) \s+   # group(1) matches variable (not the ':') and space(s)
            \=\> \s+    # followed by '=>' and more whitespace(s)
            (.*?)       # group(2) matches any kind of text
            \s* $ """,  # with optional trailing whitespace and end of line
            line,       # <-- MATCH IN THIS STRING
            re.VERBOSE  # ignore comments/whitespace in the r'' string
    )

    if key_prompt:
        key    = key_prompt.group(1)
        prompt = key_prompt.group(2)
        real_list = [
            f":{key} - enter a parameter value",
            prompt,
        ]
        value = report_parameter_from_list( real_list )

        blank_keys = kwargs.get( 'AMS_blank', [] ) # check if key may be omitted
        for blank_key in blank_keys:
            if key == blank_key:
                break
        else: # prompted value is not in (optional) 'AMS_blank' list
            if value == '':
                raise Exception( "Exited the reports menu.")
            
        kwargs[key] = value # save the chosen value for later use
        # return 'SQL_query' unchanged and 'kwargs' with an added entry
        return ( SQL_query, kwargs )
    
    # If we didn't parse a parameter, print this comment
    print(
            Color.BRIGHT_GREEN.value +  line  + Color.DEFAULT.value,
            end='' # the variable {line} already has a '\n'
    )
    return ( SQL_query, kwargs )
    

def report_parameter_from_list( options_list: List[str] ):

    error_message = ''

    while True:    
        render_list_as_menu( options_list )

        error_message = display_and_clear_error( error_message )

        selection = 0
        choice = input_with_color( "Enter choice:" )
        if choice == "":
            break
        if choice.isdigit():
            selection = int( choice )
            if selection >= 1 and selection < len( options_list ):
                return options_list[ selection ]
            else:
                return choice # user may chose 2025, which is a valid number
        else:
            return choice # if they type in a string, assume it's valid
        
    return '' # user exited the loop with <ENTER>


# May throw a 'NotImplementedError' exception
#       ==> unimplemented menu options
# May throw a 'ValueError' exception
#       ==> invalid menu choice
# Catches:
#       ValueError
#       NotImplementedError
#       pd.errors.EmptyDataError
#       pd.errors.ParserError
def transaction_history_menu() -> None:
    error_message = ""  # Initialize an empty string for the error message

    while True:
        print_transaction_history_menu()

        error_message = display_and_clear_error( error_message )

        choice = input_with_color( "Enter choice:" )

        try:
            if choice == "1":
                view_transaction_history_by_asset()
            elif choice == "2":
                view_transaction_history_by_doc()
            elif choice == "":
                break
            else:
                raise ValueError("Invalid choice")

        except (
            ValueError,
            NotImplementedError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            error_message = f"Error: transaction_history_menu:" + \
                           f"\nException text: {e}"

def print_menu_sections(df: pd.DataFrame, min_width: int = 80) -> None:
    # Calculate the required width for each column based on content
    content_widths = df.apply(lambda col: col.apply(lambda x: max(len(line) for line in x.split('\n')) + 4)).max()

    # Calculate total content width without spaces between boxes
    total_content_width = content_widths.sum()

    # Adjust column widths if total is less than min_width
    if total_content_width < min_width:
        extra_width = min_width - total_content_width
        extra_per_column = extra_width // len(df.columns)
        content_widths = content_widths + extra_per_column

        # Distribute any remaining width to the last column (if not evenly divisible)
        remaining_width = extra_width % len(df.columns)
        content_widths.iloc[-1] += remaining_width

    for _, row in df.iterrows():
        # Calculate the maximum number of lines in the current row
        max_lines = max(len(str(cell).split('\n')) for cell in row)

        # Prepare the top and bottom borders for each box in the row
        top_borders = ['┌' + '─' * (content_widths.iloc[i] - 2) + '┐' for i in range(len(content_widths))]
        bottom_borders = ['└' + '─' * (content_widths.iloc[i] - 2) + '┘' for i in range(len(content_widths))]

        # Print the top borders
        print("".join(top_borders))

        # Print the content of each box
        for line_index in range(max_lines):
            line_str = ""
            for i, section in enumerate(row):
                lines = section.split('\n')
                line_content = lines[line_index] if line_index < len(lines) else ""
                line_str += '│ {:<{}} │'.format(line_content, content_widths.iloc[i] - 4)
            print(line_str)

        # Print the bottom borders
        print("".join(bottom_borders))


def print_schedule() -> None:
    last_error = ""
    incarcerated = None

    while True:
        clear_screen_and_print_ams_title()

        print_title("Print Schedules", Color.BRIGHT_YELLOW, 100)

        if incarcerated and isinstance( incarcerated, Incarcerated ):
            print_table(
                incarcerated.to_dataframe(),
                "Selected Incarcerated Individual",
                Color.BRIGHT_YELLOW,
                100,
                print_headers=False,
            )

        # Display the last error message in red, if there is one
        last_error = display_and_clear_error( last_error )

        ( doc_number, last_error ) = input_and_validate_doc()
        if last_error:
            continue # repeat loop
        if not doc_number:
            break

        selected_entity = Incarcerated.from_doc( doc_number )
        if not selected_entity:
            last_error = "Incarcerated Individual not found"
            continue

        enrollments = Enrollment.from_entity_id( selected_entity.entity_id )
        if not enrollments:
            last_error = "No enrollments found"
            continue
        
        schedule_filepath = generate_pdf.generate_schedule( selected_entity, enrollments )

        generate_pdf.command_print( schedule_filepath )

        incarcerated = selected_entity


# Function to return an asset from a student
# May throw a 'NotImplementedError' exception
#       ==> unknown asset type
# Catches:
#       Exception
def view_transaction_history_by_asset() -> None:
    last_error = "" # Store the last error message
    asset: Asset = None
    transactions = None

    while True:
        clear_screen_and_print_ams_title()

        print_title("View Transaction History by Asset", Color.BRIGHT_YELLOW, 100)

        if transactions is not None and asset:

            print_table(
                asset.to_dataframe(),
                "Returned Asset Information",
                Color.BRIGHT_GREEN,
                100,
                print_headers=False,
            )

            print_table(
                transactions, "", Color.BRIGHT_YELLOW, 100,
            )

        last_error = display_and_clear_error( last_error )

        asset_id = input_with_color( "Enter asset barcode:" )

        if not asset_id:
            break

        asset = Asset.from_id( asset_id )
        if not asset:
            last_error = f"Lookup failed: Asset not found, for barcode '{asset_id}'"
            continue

### TODO: Finish coding this extension for chargers and headphones
###       E.g. Look up transaction history for HEADPHONES and notice
###       that headphones for *__EVERYONE__* are included in the report!
### ===

        # # Fill in an Accessory object by getting / passing in entity
        # if isinstance( asset, Accessory ):
        #     ( doc_number, last_error ) = input_and_validate_doc()
        #     if last_error:
        #         continue # repeat loop
        #     if not doc_number:
        #         break

        #     selected_entity = Incarcerated.from_doc( doc_number )
        #     if not selected_entity:
        #         last_error = "Incarcerated Individual not found"
        #         continue
        #     asset = Accessory.from_ids( asset.asset_id, selected_entity.entity_id )

### ===

        transactions = get_transaction_history( asset )
        if transactions is None:
            last_error =  f"Lookup failed: Asset has no transaction history, for barcode '{asset_id}'"
            continue

    # ...  end  of  while  True  loop  ...

    return


# Function to return an asset from a student
# May throw a 'NotImplementedError' exception
#       ==> unknown asset type
# Catches:
#       Exception
def view_transaction_history_by_doc() -> None:
    last_error = "" # Store the last error message
    selected_entity = None
    transactions = None

    while True:
        clear_screen_and_print_ams_title()

        print_title("View Transaction History by Asset", Color.BRIGHT_YELLOW, 100)

        if transactions is not None and selected_entity:
            print_selected_incarcerated_in_table( selected_entity )
            print_table(
                transactions, "", Color.BRIGHT_YELLOW, 150,
            )
            pass
            # TODO: Implement displaying df of transaction history logic.

        # end ~ if transaction and transaction.transaction_id:

        last_error = display_and_clear_error( last_error )

        ( doc_num, last_error ) = input_and_validate_doc()
        if last_error:
            continue # repeat loop
        if not doc_num:
            break

        selected_entity = Incarcerated.from_doc( doc_num )

        if not selected_entity:
            last_error = f"Incarcerated Individual not found for DOC number: '{doc_num}'"
            continue

        transactions = get_transaction_history( selected_entity )
        if transactions is None:
            last_error =  f"Lookup failed: No transaction history for DOC number: '{doc_num}'"
            continue

    # ...  end  of  while  True  loop  ...

    return

# Function to print the main menu
def print_main_menu() -> None:
    clear_screen_and_print_ams_title()

    menu_df = pd.DataFrame(
        {   
            "Column1": [
                "1. Issue asset to incarcerated individual\n" +
                "2. Issue asset to employee\n" +
                "3. Issue asset to location",

                "4. Return asset",

                "5. Print schedule\n" +
                "6. Print laptop labels",

                "7. Run a SQL report\n" +
                "8. View Transaction History",

                "0. Exit application"
            ],
        }
    )

    print_menu_sections(menu_df, min_width=100,)


def print_student_menu() -> None:
    clear_screen_and_print_ams_title()
    print_title("Student Menu", Color.BRIGHT_YELLOW, 100)

    print("\n1. View student")
    print("2. Add student")
    print("3. Edit student")
    print("4. Delete student\n")

    print("5. Update all students from CSV")
    print("6. Export all students to CSV\n")

    print("Press Enter to return to the main menu.")


def print_inventory_menu() -> None:
    clear_screen_and_print_ams_title()
    print_title("Inventory Menu", Color.BRIGHT_YELLOW, 100)

    print("\n1. Add transaction\n")

    print("2. View asset")
    print("3. Add asset")
    print("4. Edit asset")
    print("5. Delete asset\n")

    print("6. Export all transactions")
    print("7. Update all assets")
    print("8. Export all assets\n")

    print("Press Enter to return to the main menu.")


def print_image_menu() -> None:
    clear_screen_and_print_ams_title()
    print_title("Image Menu", Color.BRIGHT_YELLOW, 100)

    print("\n 1. View image")
    print(" 2. Add image")
    print(" 3. Edit image")
    print(" 4. Delete image\n")

    print(" 5. View software")
    print(" 6. Add software")
    print(" 7. Edit software")
    print(" 8. Delete software\n")

    print(" 9. Update all images")
    print("10. Export all images\n")

    print("11. Update all software")
    print("12. Export all software\n")

    print("Press Enter to return to the main menu.")

def print_transaction_history_menu() -> None:
    clear_screen_and_print_ams_title()
    print_title("Transaction History", Color.BRIGHT_YELLOW, 100)

    menu_df = pd.DataFrame(
        {   
            "Column1": [
                "1. View Transaction History by Asset\n" +
                "2. View Transaction History by DOC Number",

                "Press Enter to return to the main menu."
            ],
        }
    )

    print_menu_sections(menu_df, min_width=100,)


# Main function to display a menu of options for the user to choose from
# May throw a 'NotImplementedError' exception
#       ==> unimplemented menu options
# May throw a 'ValueError' exception
#       ==> invalid menu choice
# Catches:
#       ValueError
#       NotImplementedError
#       pd.errors.EmptyDataError
#       pd.errors.ParserError
def main() -> None:
    error_message = ""  # Initialize an empty string for the error message
    
    while True:
        print_main_menu()

        error_message = display_and_clear_error( error_message )

        choice = input_with_color( "Enter choice:" )

        try:
            if choice == "1":
                issue_assets()
            elif choice == "2":
                raise NotImplementedError("Option not implemented")
            elif choice == "3":
                raise NotImplementedError("Option not implemented")
            elif choice == "4":
                return_assets()
            elif choice == "5":
                print_schedule()
            elif choice == "6":
                raise NotImplementedError("Option not implemented")
            elif choice == "7":
                reports_menu()
            elif choice == "8":
                transaction_history_menu()
            elif choice == "0" or choice == "q":
                break           # exit the program
            elif choice == "":
                pass
            else:
                raise ValueError("Invalid choice")

# Catch every kind of Exception (even if it is something we can't avoid
# or fix), so the program user can see all error messages.
        except BaseException as e:
            error_message = f"Error: Caught a (possibly fatal) exception in main()" + \
                            f"\nException text: {e}"


if __name__ == "__main__":
    # Set the DPI awareness to Per Monitor v2
    windll.shcore.SetProcessDpiAwareness(1)
    
    main()
