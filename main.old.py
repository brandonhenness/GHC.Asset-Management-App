from typing import Iterator, List
import psycopg2
import psycopg2.extras
import pandas as pd
import tkinter as tk
from enum import Enum
from tkinter import filedialog
from ctypes import windll
import os
import platform
import signature_capture
import generate_pdf
import datetime

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


class Alignment(Enum):
    LEFT = "<"
    CENTER = "^"
    RIGHT = ">"


# TODO: Replace all instances of "equipment" with "asset"
# Function to connect to the PostgreSQL database
def connect_to_database():
    conn = psycopg2.connect(
        host="localhost",
        database="database",
        user="username",
        password="password",
    )
    return conn


def print_title(
    title: str,
    color: Color = Color.WHITE,
    width: int = None,
    print_bottom_border: bool = True,
) -> None:
    # Get the minimum width required to fit the title
    if width is None or width < len(title) + 4:
        width = len(title) + 4  # +4 for padding on both sides

    # Center the title within the specified width, then add ANSI color codes
    centered_title = " {:^{}} ".format(title, width - 4)
    colored_title = color.value + centered_title + "\033[0m"

    # Print the main title
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + colored_title + "│")

    # Optionally print the bottom border
    if print_bottom_border:
        print("└" + "─" * (width - 2) + "┘")


def print_table(
    df: pd.DataFrame,
    title: str = None,
    title_color: Color = Color.WHITE,
    max_width: int = None,
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

    # Adjust the width of the last column based on max_width
    if max_width is not None:
        current_width = sum(column_widths) + len(column_widths) + 1
        if current_width < max_width:
            column_widths[-1] += max_width - current_width

    # Check for total width exceeding max_width
    total_width = sum(column_widths) + len(column_widths) + 1
    if max_width is not None and total_width > max_width:
        raise ValueError("Table width exceeds the specified maximum width")

    # Print the top border (with or without title)
    if title:
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

# Function to update or add students from a CSV file
def update_students():
    conn = connect_to_database()
    cur = conn.cursor()

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
        cur.execute("SELECT * FROM students WHERE doc_num = %s", (row["doc_num"],))
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

    conn.commit()
    cur.close()
    conn.close()


# Function to update or add assets from a CSV file
def export_students():
    conn = connect_to_database()
    cur = conn.cursor()

    # Execute a SELECT statement to get all students
    cur.execute("SELECT * FROM students")

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
        print("Invalid file selected or file dialog canceled")
        return

    # Export the dataframe to the chosen file
    df.to_csv(file_path, index=False)

    cur.close()
    conn.close()


# Function to calculate the check digit for a GTIN barcode
def calculate_check_digit(gtin):
    # Remove any leading zeros as they don't affect the check digit
    gtin = gtin.lstrip("0")

    # Ensure the GTIN number is not empty after removing leading zeros
    if not gtin:
        return None

    # Check if GTIN number consists only of digits
    if not gtin.isdigit():
        return None

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
def format_doc_number(gtin):
    if not calculate_check_digit(gtin):
        print("Invalid check digit")
        return None  # Invalid check digit
    doc_num = str(gtin)[1:-1].lstrip("0")  # Remove leading zeros and check digit
    # if len(doc_num) != 6 or len(doc_num) != 5:
    #     print(doc_num)
    #     print("Invalid length")
    #     return None  # Invalid length
    return doc_num


def clear_screen():
    # Clear the console screen based on the operating system
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

class Entity:
    def __init__(self, entity_id, enabled):
        self.entity_id = entity_id
        self.enabled = enabled

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.entity_id == other.entity_id
        elif isinstance(other, int):
            return self.entity_id == other
        else:
            return False

class User(Entity):
    def __init__(self, entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login,):
        super().__init__(entity_id, enabled)
        self.ctclink_id = ctclink_id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.legacy_username = legacy_username
        self.legacy_last_login = legacy_last_login
        self.osn_username = osn_username
        self.osn_last_login = osn_last_login

class Incarcerated(User):
    def __init__(self, entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login, doc_number, facility, housing_unit, housing_cell, estimated_release_date, counselor, hs_diploma,):
        super().__init__(entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login,)
        self.doc_number = doc_number
        self.facility = facility
        self.housing_unit = housing_unit
        self.housing_cell = housing_cell
        self.estimated_release_date = estimated_release_date
        self.counselor = counselor
        self.hs_diploma = hs_diploma

class Student(Incarcerated):
    def __init__(self, entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login, doc_number, facility, housing_unit, housing_cell, estimated_release_date, counselor, hs_diploma, program, program_status,):
        super().__init__(entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login, doc_number, facility, housing_unit, housing_cell, estimated_release_date, counselor, hs_diploma,)
        self.program = program
        self.program_status = program_status

class Employee(User):
    def __init__(self, entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login, employee_id,):
        super().__init__(entity_id, enabled, ctclink_id, first_name, last_name, middle_name, legacy_username, legacy_last_login, osn_username, osn_last_login,)
        self.employee_id = employee_id

class Location(Entity):
    def __init__(self, entity_id, enabled, building, room_number, room_name,):
        super().__init__(entity_id, enabled)
        self.building = building
        self.room_number = room_number
        self.room_name = room_name

class Asset:
    def __init__(self, asset_id, asset_type, charge_limit, asset_cost, asset_status,):
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.charge_limit = charge_limit
        self.asset_cost = asset_cost
        self.asset_status = asset_status

class Laptop(Asset):
    def __init__(self, asset_id, asset_type, charge_limit, asset_cost, asset_status, model, serial_number, manufacturer, drive_serial, ram, cpu, storage, bios_version,):
        super().__init__(asset_id, asset_type, charge_limit, asset_cost, asset_status,)
        self.model = model
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.drive_serial = drive_serial
        self.ram = ram
        self.cpu = cpu
        self.storage = storage
        self.bios_version = bios_version

class Book(Asset):
    def __init__(self, asset_id, asset_type, charge_limit, asset_cost, asset_status, isbn, title, author, publisher, edition, year,):
        super().__init__(asset_id, asset_type, charge_limit, asset_cost, asset_status,)
        self.isbn = isbn
        self.title = title
        self.author = author
        self.publisher = publisher
        self.edition = edition
        self.year = year

class Calculator(Asset):
    def __init__(self, asset_id, asset_type, charge_limit, asset_cost, asset_status, model, serial_number, manufacturer, manufacturer_date_code, color,):
        super().__init__(asset_id, asset_type, charge_limit, asset_cost, asset_status,)
        self.model = model
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.manufacturer_date_code = manufacturer_date_code
        self.color = color

class Transaction:
    def __init__(self, transaction_id, entity_id, asset: Asset, transaction_type, transaction_timestamp, transaction_user, transaction_notes,):
        self.transaction_id = transaction_id
        self.entity_id = entity_id
        self.asset = asset
        self.transaction_type = transaction_type
        self.transaction_timestamp = transaction_timestamp
        self.transaction_user = transaction_user
        self.transaction_notes = transaction_notes

def get_incarcerated_by_doc_number(doc_number: str) -> Incarcerated:
    conn = connect_to_database()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check for existing student
    cur.execute(
        """
        SELECT 
            e.entity_id,
            e.enabled,
            u.ctclink_id,
            u.first_name,
            u.last_name,
            u.middle_name,
            u.legacy_username,
            u.legacy_last_login,
            u.osn_username,
            u.osn_last_login,
            i.doc_number,
            i.facility,
            i.housing_unit,
            i.housing_cell,
            i.estimated_release_date,
            i.counselor,
            i.hs_diploma
        FROM 
            entities e
        JOIN 
            users u ON e.entity_id = u.entity_id
        JOIN 
            incarcerated i ON u.entity_id = i.entity_id
        LEFT JOIN 
            students s ON i.entity_id = s.entity_id
        WHERE 
            i.doc_number = %s;
        """,
        (doc_number,),
    )

    incarcerated = cur.fetchone()
    cur.close()
    conn.close()
    if not incarcerated:
        return None
    return Incarcerated(incarcerated["entity_id"], incarcerated["enabled"], incarcerated["ctclink_id"], incarcerated["first_name"], incarcerated["last_name"], incarcerated["middle_name"], incarcerated["legacy_username"], incarcerated["legacy_last_login"], incarcerated["osn_username"], incarcerated["osn_last_login"], incarcerated["doc_number"], incarcerated["facility"], incarcerated["housing_unit"], incarcerated["housing_cell"], incarcerated["estimated_release_date"], incarcerated["counselor"], incarcerated["hs_diploma"],)

def get_issued_assets_by_entity_id(entity_id: int) -> Iterator[Asset]:
    conn = connect_to_database()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check for existing student
    cur.execute(
        """
        SELECT 
            a.asset_id,
            a.asset_type,
            at.charge_limit,
            a.asset_cost,
            a.asset_status,
            l.laptop_model,
            l.laptop_serial_number,
            l.laptop_manufacturer,
            l.laptop_drive_serial_number,
            l.laptop_ram,
            l.laptop_cpu,
            l.laptop_storage,
            l.laptop_bios_version,
            b.book_isbn,
            b.book_title,
            b.book_author,
            b.book_publisher,
            b.book_edition,
            b.book_year,
            c.calculator_model,
            c.calculator_serial_number,
            c.calculator_manufacturer,
            c.calculator_manufacturer_date_code,
            c.calculator_color
        FROM 
            assets a
        JOIN 
            issued_assets ia ON a.asset_id = ia.asset_id
        LEFT JOIN
            asset_types at ON a.asset_type = at.asset_type
        LEFT JOIN 
            laptops l ON a.asset_id = l.asset_id
        LEFT JOIN 
            book_assets ba ON a.asset_id = ba.asset_id
        LEFT JOIN 
            books b ON ba.book_isbn = b.book_isbn
        LEFT JOIN 
            calculators c ON a.asset_id = c.asset_id
        LEFT JOIN
            transactions t ON ia.transaction_id = t.transaction_id
        WHERE 
            t.entity_id = %s;
        """,
        (entity_id,),
    )

    issued_assets = cur.fetchall()
    cur.close()
    conn.close()

    if not issued_assets:
        return None
    for asset in issued_assets:
        if asset["asset_type"] == "LAPTOP":
            yield Laptop(asset["asset_id"], asset["asset_type"], asset["charge_limit"], asset["asset_cost"], asset["asset_status"], asset["laptop_model"], asset["laptop_serial_number"], asset["laptop_manufacturer"], asset["laptop_drive_serial_number"], asset["laptop_ram"], asset["laptop_cpu"], asset["laptop_storage"], asset["laptop_bios_version"],)
        elif asset["asset_type"] == "BOOK":
            yield Book(asset["asset_id"], asset["asset_type"], asset["charge_limit"], asset["asset_cost"], asset["asset_status"], asset["book_isbn"], asset["book_title"], asset["book_author"], asset["book_publisher"], asset["book_edition"], asset["book_year"],)
        elif asset["asset_type"] == "CALCULATOR":
            yield Calculator(asset["asset_id"], asset["asset_type"], asset["charge_limit"], asset["asset_cost"], asset["asset_status"], asset["calculator_model"], asset["calculator_serial_number"], asset["calculator_manufacturer"], asset["calculator_manufacturer_date_code"], asset["calculator_color"],)

def on_signature_captured(signature_data, incarcerated, assets, current_time):

    generate_pdf.generate_agreement(signature_data, incarcerated, assets, current_time)

    print("Signature captured")
    # Signal the main thread that the signature has been captured
    signature_capture.signature_captured_event.set()

def issue_assets() -> None:
    last_error = ""  # Store the last error message

    while True:
        clear_screen()

        print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)

        print_title("Issue Assets", Color.BRIGHT_YELLOW, 100)

        # Display the last error message in red, if there is one
        if last_error:
            print(f"\033[91m{last_error}\033[0m")  # Red for error
            last_error = ""  # Reset the error message
        else:
            print()  # Print a blank line

        doc_num = input("\033[96mEnter DOC number: \033[0m")
        if not doc_num:
            break

        if len(doc_num) != 5 and len(doc_num) != 6 and len(doc_num) != 12:
            last_error = "Invalid doc number"
            continue
        elif len(doc_num) == 12:  # GTIN barcode
            doc_num = format_doc_number(doc_num)
            if not doc_num:
                last_error = "Invalid GTIN barcode"
                continue

        conn = connect_to_database()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        selected_entity = get_incarcerated_by_doc_number(doc_num)

        if not selected_entity:
            last_error = "Incarcerated Individual not found"
            continue

        while True:
            # Clear the screen and reprint student and asset information
            clear_screen()

            print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)

            # Convert student information into a DataFrame without column headers
            student_data = {
                "Field": ["DOC#", "CTC ID", "Name"],
                "Value": [
                    selected_entity.doc_number,
                    selected_entity.ctclink_id,
                    f"{selected_entity.last_name}, {selected_entity.first_name} {selected_entity.middle_name}",
                ],
            }
            entity_df = pd.DataFrame(student_data)

            # Print the student information
            print_table(
                entity_df,
                "Selected Incarcerated Individual",
                Color.BRIGHT_YELLOW,
                100,
                print_headers=False,
            )

            issued_assets = list(get_issued_assets_by_entity_id(selected_entity.entity_id))

            # Extract relevant attributes and create a DataFrame
            issued_assets_data = []
            for asset in issued_assets:
                if isinstance(asset, Laptop):
                    asset_data = (asset.asset_id, asset.asset_type, asset.model)  # Assuming 'model' is analogous to 'asset_name'
                elif isinstance(asset, Book):
                    asset_data = (asset.asset_id, asset.asset_type, asset.title)  # Assuming 'title' can be used as 'asset_name'
                elif isinstance(asset, Calculator):
                    asset_data = (asset.asset_id, asset.asset_type, asset.model)  # Similarly using 'model' for 'asset_name'
                else:
                    continue  # or handle other asset types if necessary

                issued_assets_data.append(asset_data)

            issued_assets_df = pd.DataFrame(
                issued_assets_data, columns=["ID", "Type", "Name"]
            )

            # Use print_table to display the data
            print_table(
                issued_assets_df, "Currently Issued Assets", Color.BRIGHT_YELLOW, 100
            )

            print_title("Issue Asset", Color.BRIGHT_YELLOW, 100)

            # Display the last error message in red, if there is one
            if last_error:
                print(f"\033[91m{last_error}\033[0m")  # Red for error
                last_error = ""  # Reset the error message
            else:
                print()  # Print a blank line

            new_asset_id = input("\033[96mEnter asset ID: \033[0m")

            #TODO move this logic to a separate function
            if not new_asset_id:
                # Check if any documents related to the transactions of the current entity are unprinted
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
                    (selected_entity.entity_id,),
                )

                unprinted_documents = cur.fetchall()

                # Filter for "AGREEMENT" type documents
                agreement_documents = [doc for doc in unprinted_documents if doc['document_type'] == 'AGREEMENT']

                if agreement_documents:
                    # If any unprinted documents, ask to print them
                    print_agreement = input("Print asset agreement? (Y/N) ")
                    if print_agreement.lower() == "y":
                        try:
                            current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                            signature_capture.launch(on_signature_captured, selected_entity, issued_assets, current_time)
                            print("Waiting for signature...")
                            signature_capture.signature_captured_event.wait()
                            print("Generating agreement...")
                            signature_capture.signature_captured_event.clear()
                            agreement_file_path = f"{ selected_entity.doc_number }_{ current_time }.pdf" 
                            # Record agreement document as printed
                            print("Marking agreement as printed...")
                            for asset in issued_assets:
                                cur.execute(
                                    """
                                    UPDATE documents
                                    SET document_printed_timestamp = CURRENT_TIMESTAMP, document_signed_timestamp = CURRENT_TIMESTAMP, document_file_name = %s
                                    FROM transaction_documents td
                                    JOIN transactions t ON td.transaction_id = t.transaction_id
                                    WHERE documents.document_id = td.document_id
                                    AND document_type = 'AGREEMENT' 
                                    AND t.asset_id = %s and t.entity_id = %s;
                                    """,
                                    (agreement_file_path, asset.asset_id, selected_entity.entity_id,)
                                )

                            conn.commit()
                            print("Printing agreement...")
                            generate_pdf.command_print("agreements/" + agreement_file_path)

                            # raise NotImplementedError("Feature not implemented")
                        except Exception as e:
                            print(f"Error: {e}")
                            input("Press Enter to continue...")
                
                label_documents = [doc for doc in unprinted_documents if doc['document_type'] == 'LABELS']

                if label_documents:
                    # print_labels = input("Print laptop labels? (Y/N) ")
                    print_labels = "y" #TODO Remove this line once the logic for printing laptop labels is implemented
                    if print_labels.lower() == "y":
                        try:
                            for asset in issued_assets:
                                # Update the document record in the database (if necessary)
                                cur.execute(
                                    """
                                    UPDATE documents
                                    SET document_printed_timestamp = CURRENT_TIMESTAMP, document_signed_timestamp = CURRENT_TIMESTAMP
                                    FROM transaction_documents td
                                    JOIN transactions t ON td.transaction_id = t.transaction_id
                                    WHERE documents.document_id = td.document_id
                                    AND document_type = 'LABELS'
                                    AND t.asset_id = %s and t.entity_id = %s;
                                    """,
                                    (asset.asset_id, selected_entity.entity_id,)
                                )

                                # Send the print command
                                # print_label(label_file_path) #TODO Implement the logic to handle the printing of laptop labels

                            conn.commit()
                            print("Labels printed successfully.")

                        except Exception as e:
                            print(f"Error: {e}")
                            input("Press Enter to continue...")
                                
                break  # Break out of the loop if no asset ID is entered
            
            #TODO move this logic to a separate function
            # Fetch the asset and its type details
            cur.execute(
                """
                SELECT 
                    a.asset_id,
                    a.asset_type,
                    at.charge_limit,
                    a.asset_status,
                    a.asset_cost,
                    ia.transaction_id,
                    t.entity_id,
                    ba.book_isbn
                FROM 
                    assets a
                LEFT JOIN 
                    asset_types at ON a.asset_type = at.asset_type
                LEFT JOIN 
                    issued_assets ia ON a.asset_id = ia.asset_id
                LEFT JOIN
                    transactions t ON ia.transaction_id = t.transaction_id
                LEFT JOIN
                    book_assets ba ON a.asset_id = ba.asset_id
                WHERE 
                    a.asset_id = %s;
                """,
                (new_asset_id,),
            )
            asset = cur.fetchone()

            # Check if the asset exists
            if not asset:
                last_error = "Asset not found"
                continue

            # Check the asset status
            if asset["asset_status"] != "IN_SERVICE":
                status_error_messages = {
                    "DECOMMISSIONED": "Error: Asset has been decommissioned.",
                    "BROKEN": "Error: Asset is currently broken.",
                    "MISSING": "Error: Asset is currently missing.",
                    "OUT_FOR_REPAIR": "Error: Asset is currently out for repair.",
                }
                last_error = status_error_messages.get(
                    asset["asset_status"], "Error: Asset is currently not available."
                )
                continue
            elif asset["entity_id"] and asset["entity_id"] != selected_entity.entity_id:
                last_error = f"Error: Asset is currently issued to entity ID {asset['entity_id']}."
                continue
            elif asset["entity_id"] and asset["entity_id"] == selected_entity.entity_id:
                last_error = (
                    "Error: Asset already charged to currently selected entity."
                )
                continue
            
            book_already_issued = False
            # Check for book assets specifically
            if asset["asset_type"] == "BOOK":
                for issued_asset in issued_assets:
                    if issued_asset.asset_type != "BOOK":
                        continue
                    if asset["book_isbn"] is not None and issued_asset.isbn == asset["book_isbn"]:
                        last_error = f"Error: A book with (ISBN: {asset['book_isbn']}) is already issued to the selected individual."
                        book_already_issued = True
                        break
            
            if book_already_issued:
                continue

            # Count the number of same-type assets already issued to the entity
            issued_same_type_count = sum(
                1
                for issued_asset in issued_assets
                if issued_asset.asset_type == asset["asset_type"]
            )

            # Enforce charge limit
            if (
                asset["charge_limit"] is not None
                and issued_same_type_count >= asset["charge_limit"]
            ):
                last_error = f"Error: Entity already has the maximum number of {asset["asset_type"]} issued."
                continue
            
            # Begin a transaction block
            cur.execute("BEGIN;")

            try:
                # Insert a new transaction for issuing the asset
                cur.execute(
                    """
                    INSERT INTO transactions (entity_id, asset_id, transaction_type) 
                    VALUES (%s, %s, %s)
                    RETURNING transaction_id;
                    """,
                    (selected_entity.entity_id, asset['asset_id'], 'ISSUED'),
                )
                transaction_id = cur.fetchone()[0]

                # Insert a record into issued_assets
                cur.execute(
                    """
                    INSERT INTO issued_assets (asset_id, transaction_id) 
                    VALUES (%s, %s);
                    """,
                    (asset['asset_id'], transaction_id),
                )

                # Check for existing unprinted agreement document for the entity
                cur.execute(
                    """
                    SELECT d.document_id
                    FROM documents d
                    JOIN transaction_documents td ON d.document_id = td.document_id
                    JOIN transactions t ON td.transaction_id = t.transaction_id
                    WHERE t.entity_id = %s AND d.document_type = 'AGREEMENT' AND d.document_printed_timestamp IS NULL
                    LIMIT 1;
                    """,
                    (selected_entity.entity_id,),
                )
                existing_document = cur.fetchone()

                if existing_document:
                    agreement_document_id = existing_document[0]
                else:
                    # Insert a new agreement document if there isn't an unprinted one
                    cur.execute(
                        """
                        INSERT INTO documents (document_type)
                        VALUES ('AGREEMENT')
                        RETURNING document_id;
                        """,
                    )
                    agreement_document_id = cur.fetchone()[0]

                # Link the document with the transaction
                cur.execute(
                    """
                    INSERT INTO transaction_documents (transaction_id, document_id)
                    VALUES (%s, %s);
                    """,
                    (transaction_id, agreement_document_id),
                )

                # If the asset is a laptop, insert into the chargers_issued table
                if asset["asset_type"] == 'LAPTOP':
                    cur.execute(
                        """
                        INSERT INTO documents (document_type)
                        VALUES ('LABELS')
                        RETURNING document_id;
                        """,
                    )
                    labels_document_id = cur.fetchone()[0]

                    # Link labels document with the transaction
                    cur.execute(
                        """
                        INSERT INTO transaction_documents (transaction_id, document_id)
                        VALUES (%s, %s);
                        """,
                        (transaction_id, labels_document_id),
                    )

                    cur.execute(
                        """
                        INSERT INTO issued_chargers (transaction_id) 
                        VALUES (%s);
                        """,
                        (transaction_id,),
                    )

                # Commit the transaction
                conn.commit()

                last_error = "\033[92mAsset issued successfully!\033[0m"  # Green for success

            except Exception as e:
                # In case of error, roll back the transaction
                conn.rollback()
                last_error = f"\033[91mError during asset issuance: {e}\033[0m"  # Red for error

        cur.close()
        conn.close()


# # Function to ask the user if they would like to print the asset agreement
# def print_asset_agreement(student_df, issued_asset_df):
#     # TODO: Implement signature prompt
#     # TODO: Implement printing of asset loan agreement and laptop labels
#     while True:
#         print_agreement = input("\033[96mPrint asset agreement? (Y/N) \033[0m")
#         if print_agreement.lower() == "y":
#             raise NotImplementedError("Feature not implemented")
#         elif print_agreement.lower() == "n":
#             break

def get_transaction_by_asset_id(asset_id: int) -> Transaction:
    conn = connect_to_database()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check for existing student
    cur.execute(
        """
        SELECT 
            a.asset_id,
            a.asset_type,
            at.charge_limit,
            a.asset_status,
            a.asset_cost,
            ia.transaction_id,
            t.entity_id,
            t.transaction_type,
            t.transaction_timestamp,
            t.transaction_user,
            t.transaction_notes,
            l.laptop_model,
            l.laptop_serial_number,
            l.laptop_manufacturer,
            l.laptop_drive_serial_number,
            l.laptop_ram,
            l.laptop_cpu,
            l.laptop_storage,
            l.laptop_bios_version,
            b.book_isbn,
            b.book_title,
            b.book_author,
            b.book_isbn,
            b.book_publisher,
            b.book_edition,
            b.book_year,
            c.calculator_model,
            c.calculator_serial_number,
            c.calculator_manufacturer,
            c.calculator_manufacturer_date_code,
            c.calculator_color
        FROM 
            assets a
        LEFT JOIN 
            asset_types at ON a.asset_type = at.asset_type
        LEFT JOIN 
            issued_assets ia ON a.asset_id = ia.asset_id
        LEFT JOIN
            transactions t ON ia.transaction_id = t.transaction_id
        LEFT JOIN
            laptops l ON a.asset_id = l.asset_id
        LEFT JOIN
            book_assets ba ON a.asset_id = ba.asset_id
        LEFT JOIN
            books b ON ba.book_isbn = b.book_isbn
        LEFT JOIN
            calculators c ON a.asset_id = c.asset_id
        WHERE 
            a.asset_id = %s;
        """,
        (asset_id,),
    )

    data = cur.fetchone()
    cur.close()
    conn.close()
    if not data:
        return None
    if data["asset_type"] == "LAPTOP":
        asset = Laptop(data["asset_id"], data["asset_type"], data["charge_limit"], data["asset_cost"], data["asset_status"], data["laptop_model"], data["laptop_serial_number"], data["laptop_manufacturer"], data["laptop_drive_serial_number"], data["laptop_ram"], data["laptop_cpu"], data["laptop_storage"], data["laptop_bios_version"],)
    elif data["asset_type"] == "BOOK":
        asset = Book(data["asset_id"], data["asset_type"], data["charge_limit"], data["asset_cost"], data["asset_status"], data["book_isbn"], data["book_title"], data["book_author"], data["book_publisher"], data["book_edition"], data["book_year"],)
    elif data["asset_type"] == "CALCULATOR":
        asset = Calculator(data["asset_id"], data["asset_type"], data["charge_limit"], data["asset_cost"], data["asset_status"], data["calculator_model"], data["calculator_serial_number"], data["calculator_manufacturer"], data["calculator_manufacturer_date_code"], data["calculator_color"],)
    else:
        return None
    return Transaction(data["transaction_id"], data["entity_id"], asset, data["transaction_type"], data["transaction_timestamp"], data["transaction_user"], data["transaction_notes"],)

# Function to return an asset from a student
def return_assets():
    last_error = ""  # Store the last error message
    transaction = None

    while True:
        clear_screen()

        print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)

        print_title("Return Assets", Color.BRIGHT_YELLOW, 100)

        if transaction and transaction.transaction_id:
            # Convert asset information into a DataFrame without column headers
            if transaction.asset.asset_type == "LAPTOP":
                asset_data = {
                    "Field": ["Asset Type", "Asset ID", "Serial Number", "Drive Serial", "Manufacturer", "Model"],
                    "Value": [
                        transaction.asset.asset_type,
                        transaction.asset.asset_id,
                        transaction.asset.serial_number,
                        transaction.asset.drive_serial,
                        transaction.asset.manufacturer,
                        transaction.asset.model,
                    ],
                }
            elif transaction.asset.asset_type == "BOOK":
                asset_data = {
                    "Field": ["Asset Type", "Asset ID", "ISBN", "Publisher", "Author", "Title", "Edition", "Year"],
                    "Value": [
                        transaction.asset.asset_type,
                        transaction.asset.asset_id,
                        transaction.asset.isbn,
                        transaction.asset.publisher,
                        transaction.asset.author,
                        transaction.asset.title,
                        transaction.asset.edition,
                        transaction.asset.year,
                    ],
                }
            elif transaction.asset.asset_type == "CALCULATOR":
                asset_data = {
                    "Field": ["Asset Type", "Asset ID", "Serial Number", "Manufacturer", "Date Code", "Model", "Color"],
                    "Value": [
                        transaction.asset.asset_type,
                        transaction.asset.asset_id,
                        transaction.asset.serial_number,
                        transaction.asset.manufacturer,
                        transaction.asset.manufacturer_date_code,
                        transaction.asset.model,
                        transaction.asset.color,
                    ],
                }
            else:
                raise NotImplementedError("Unknown asset type")
            print_table(
                pd.DataFrame(asset_data),
                "Returned Asset Information",
                Color.BRIGHT_GREEN,
                100,
                print_headers=False,
            )

        # Display the last error message in red, if there is one
        if last_error:
            print(f"\033[91m{last_error}\033[0m")  # Red for error
            last_error = ""  # Reset the error message
        else:
            print()  # Print a blank line

        asset_id = input("\033[96mEnter asset number: \033[0m")
        if not asset_id:
            break

        transaction = get_transaction_by_asset_id(asset_id)
        if not transaction:
            last_error = "Return failed: Asset not found"
            continue
        elif transaction.transaction_id is None:
            last_error = "Return failed: Asset is not currently issued"
            continue
        
        conn = connect_to_database()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("BEGIN;")
        try:
            # Delete row from issued_assets
            cur.execute(
                """
                DELETE FROM issued_assets
                WHERE asset_id = %s;
                """,
                (transaction.asset.asset_id,),
            )

            # Add RETURNED transaction to transactions table
            cur.execute(
                """
                INSERT INTO transactions (asset_id, entity_id, transaction_type)
                VALUES (%s, %s, %s);
                """,
                (transaction.asset.asset_id, transaction.entity_id, "RETURNED"),
            )

            conn.commit()

            last_error = "\033[92mAsset returned successfully!\033[0m"
        
        except Exception as e:
            conn.rollback()
            last_error = f"\033[91mError during asset return: {e}\033[0m"

        cur.close()
        conn.close()

def student_menu():
    error_message = ""  # Initialize an empty string for the error message

    while True:
        clear_screen()  # Clear the screen at the start of the loop
        print_student_menu()

        if error_message:  # If there is an error message, print it
            print(f"\033[91m{error_message}\033[0m")
            error_message = ""  # Reset the error message

        choice = input("\033[96mEnter choice: \033[0m")

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
                update_students()
            elif choice == "6":
                export_students()
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
            error_message = str(e)  # Store the error message


def inventory_menu():
    error_message = ""  # Initialize an empty string for the error message

    while True:
        clear_screen()  # Clear the screen at the start of the loop
        print_inventory_menu()

        if error_message:  # If there is an error message, print it
            print(f"\033[91m{error_message}\033[0m")
            error_message = ""  # Reset the error message

        choice = input("\033[96mEnter choice: \033[0m")

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
            error_message = str(e)  # Store the error message


def image_menu():
    error_message = ""  # Initialize an empty string for the error message

    while True:
        clear_screen()  # Clear the screen at the start of the loop
        print_image_menu()

        if error_message:  # If there is an error message, print it
            print(f"\033[91m{error_message}\033[0m")
            error_message = ""

        choice = input("\033[96mEnter choice: \033[0m")

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
            error_message = str(e)  # Store the error message

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
        print(''.join(top_borders))

        # Print the content of each box
        for line_index in range(max_lines):
            line_str = ''
            for i, section in enumerate(row):
                lines = section.split('\n')
                line_content = lines[line_index] if line_index < len(lines) else ''
                line_str += '│ {:<{}} │'.format(line_content, content_widths.iloc[i] - 4)
            print(line_str)

        # Print the bottom borders
        print(''.join(bottom_borders))

def print_schedule():
    last_error = ""
    incarcerated = None

    while True:
        clear_screen()

        print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)

        print_title("Print Schedules", Color.BRIGHT_YELLOW, 100)

        if incarcerated and incarcerated.entity_id:
            # Convert student information into a DataFrame without column headers
            student_data = {
                "Field": ["DOC#", "CTC ID", "Name"],
                "Value": [
                    incarcerated.doc_number,
                    incarcerated.ctclink_id,
                    f"{incarcerated.last_name}, {incarcerated.first_name} {incarcerated.middle_name}",
                ],
            }
            entity_df = pd.DataFrame(student_data)

            # Print the student information
            print_table(
                entity_df,
                "Selected Incarcerated Individual",
                Color.BRIGHT_YELLOW,
                100,
                print_headers=False,
            )

        # Display the last error message in red, if there is one
        if last_error:
            print(f"\033[91m{last_error}\033[0m")  # Red for error
            last_error = ""  # Reset the error message
        else:
            print()  # Print a blank line

        doc_number = input("\033[96mEnter DOC number: \033[0m")
        if not doc_number:
            break

        if len(doc_number) != 5 and len(doc_number) != 6 and len(doc_number) != 12:
            last_error = "Invalid doc number"
            continue
        elif len(doc_number) == 12:  # GTIN barcode
            doc_number = format_doc_number(doc_number)
            if not doc_number:
                last_error = "Invalid GTIN barcode"
                continue

        selected_entity = get_incarcerated_by_doc_number(doc_number)
        if not selected_entity:
            last_error = "Incarcerated Individual not found"
            continue

        enrollments = get_enrollments_by_entity_id(selected_entity.entity_id)
        if not enrollments:
            last_error = "No enrollments found"
            continue
        
        generate_pdf.generate_schedule(selected_entity, enrollments)

        generate_pdf.command_print("schedules/" + doc_number + ".pdf")

        incarcerated = selected_entity

class Enrollment:
    def __init__(self, entity_id: str, schedule_id: str, course_id: str, course_prefix: str, course_code: str, course_name: str, course_credits: str, course_description: str, course_outcomes: str, course_start_date: str, course_end_date: str, course_days: str, course_start_time: str, course_end_time: str, course_location: str, course_instructor: str, course_quarter: str, course_year: str):
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

def get_enrollments_by_entity_id(entity_id: str) -> List[Enrollment]:
    print("Getting enrollments for entity ID", entity_id)
    conn = connect_to_database()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(
        """
        SELECT 
            e.entity_id,
            e.schedule_id,
            c.course_id,
            c.course_prefix,
            c.course_code,
            c.course_name,
            c.course_credits,
            c.course_description,
            c.course_outcomes,
            cs.course_start_date,
            cs.course_end_date,
            cs.course_days,
            cs.course_start_time,
            cs.course_end_time,
            cs.course_location,
            cs.course_instructor,
            cs.scheduled_quarter,
            cs.scheduled_year
        FROM enrollments e
        LEFT JOIN course_schedules cs ON e.schedule_id = cs.schedule_id
        JOIN courses c ON cs.course_id = c.course_id
        WHERE e.entity_id = %s;
        """,
        (entity_id,),
    )

    enrollments = cur.fetchall()
    cur.close()
    conn.close()

    if not enrollments:
        return None
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

# Function to print the main menu
def print_main_menu():
    print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)

    menu_df = pd.DataFrame(
        {   
            "Column1": ["1. Issue asset to incarcerated individual\n2. Issue asset to employee\n3. Issue asset to location", "4. Return asset", "5. Print schedule\n6. Print loan agreement\n7. Print laptop labels",],
        }
    )

    print_menu_sections(menu_df, min_width=100,)

def print_student_menu():
    print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)
    print_title("Student Menu", Color.BRIGHT_YELLOW, 100)

    print("\n1. View student")
    print("2. Add student")
    print("3. Edit student")
    print("4. Delete student\n")

    print("5. Update all students")
    print("6. Export all students\n")

    print("\033[93mPress Enter to return to the main menu.\033[0m\n")


def print_inventory_menu():
    print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)
    print_title("Inventory Menu", Color.BRIGHT_YELLOW, 100)

    print("\n1. Add transaction\n")

    print("2. View asset")
    print("3. Add asset")
    print("4. Edit asset")
    print("5. Delete asset\n")

    print("6. Export all transactions")
    print("7. Update all assets")
    print("8. Export all assets\n")

    print("\033[93mPress Enter to return to the main menu.\033[0m\n")


def print_image_menu():
    print_title("Asset Management System", Color.BRIGHT_YELLOW, 100)
    print_title("Image Menu", Color.BRIGHT_YELLOW, 100)

    print("\n1. View image")
    print("2. Add image")
    print("3. Edit image")
    print("4. Delete image\n")

    print("5. View software")
    print("6. Add software")
    print("7. Edit software")
    print("8. Delete software\n")

    print("9. Update all images")
    print("10. Export all images\n")

    print("11. Update all software")
    print("12. Export all software\n")

    print("\033[93mPress Enter to return to the main menu.\033[0m\n")


# Main function to display a menu of options for the user to choose from
def main():
    error_message = ""  # Initialize an empty string for the error message
    
    while True:
        clear_screen()
        print_main_menu()

        if error_message:  # If there is an error message, print it
            print(f"\033[91m{error_message}\033[0m")
            error_message = ""

        choice = input("\033[96mEnter choice: \033[0m")

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
                raise NotImplementedError("Option not implemented")
            elif choice == "":
                pass
            else:
                raise ValueError("Invalid choice")

        except (
            ValueError,
            NotImplementedError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            error_message = str(e)

if __name__ == "__main__":
    # Set the DPI awareness to Per Monitor v2
    windll.shcore.SetProcessDpiAwareness(1)
    main()
