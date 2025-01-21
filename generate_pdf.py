import os
import sys
from jinja2 import Environment, FileSystemLoader
import pdfkit
import datetime
from dateutil.relativedelta import relativedelta
import base64
from jinja2 import Template
import subprocess
from main import Asset, Incarcerated, Calculator, Laptop, Book, Enrollment
import tempfile

CALLER_SCRIPT_FILEPATH  = sys.argv[0]
CALLER_SCRIPT_DIRECTORY = os.path.dirname( CALLER_SCRIPT_FILEPATH )


# We intentionally uses Unix '/' directory separators
# # instead of Windows '\', because Python is smarter than Windows.
path_wkhtmltopdf = "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"

AMS_WEBKIT_AVAILABLE = False # default to assuming this is 'not installed'

# Check if WebKit *is* installed (and gracefully handle a FileNotFoundError).
try:
    statinfo = os.stat( path_wkhtmltopdf )
    # If we didn't get a 'FileNotFoundError', we have WebKit ...
    AMS_WEBKIT_AVAILABLE = True
except ( FileNotFoundError ) as e:
    print(
            f"\n\nWarning: WebKit not found." +
            f"\n\nWarning: WebKit is required to print schedules or asset loan agreements." +
            f"\n\nTriage: Refer to 'AAA___readme___OSN.txt' in the 'Asset_Management_App' directory to install this feature." +
            f"\n\nInfo: Other functions (i.e. database updates and queries ) are unaffected.\n"
    )
    input( f"Press Enter to continue... " )
    AMS_WEBKIT_AVAILABLE = False


# TODO: resume update here
if AMS_WEBKIT_AVAILABLE:
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
else:
    config = None

def generate_pdf_from_template(
    template_path: str,
    output_path: str,
    options: dict,
    context: dict,
) -> None:
    """Generates a PDF from a Jinja2 template.
    Args:
        template_path (str): The file path to the Jinja2 template.
        output_path (str): The file path where the output PDF should be saved.
        context (dict): A dictionary of variables to render the template.
    """
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
    template = env.get_template(os.path.basename(template_path))
    html = template.render(context)
    if config:
        pdfkit.from_string(html, output_path, options=options, configuration=config)
    else:
        print( f"Warning: WebKit (still) not found. Skipping asset agreement (or schedule) print-out.")
        input( f"Press Enter to continue... " )

def encode_image_to_base64(
    image_path: str,
) -> str:
    """Encodes an image to base64.
    Args:
        image_path (str): The file path to the image.
    Returns:
        str: The base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_agreement(
    signature: base64, incarcerated: Incarcerated, assets: list[ Asset ], current_time, quarter_end_date
) -> str:

    # TODO: add this college-authorized signature to the signatures DB table
    college_signature = encode_image_to_base64( f"{CALLER_SCRIPT_DIRECTORY}\\college_signature.png" )
    logo = encode_image_to_base64( f"{CALLER_SCRIPT_DIRECTORY}\\GHC-logo-horizontal-blue-web.png" )
    icon_logo = encode_image_to_base64( f"{CALLER_SCRIPT_DIRECTORY}\\GHC-logo-icon-blue-web.png" )

    current_date = datetime.datetime.now()
    date = current_date.strftime("%m/%d/%Y")
    facility_acronym = "Stafford Creek Corrections Center"
    college_name = "Grays Harbor College"
    college_representative = "Henness, Brandon"

    quarter_end_date = quarter_end_date.strftime("%m/%d/%Y") # match 'date' format

    
    # Load your footer template
    with open( f"{CALLER_SCRIPT_DIRECTORY}\\templates\\agreement_footer.html", "r") as file:
        footer_template = Template(file.read())

    rendered_footer = footer_template.render(icon_logo=icon_logo)
    # Save rendered footer to a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w+"
    ) as temp_footer:
        footer_file_path = temp_footer.name
        temp_footer.write(rendered_footer)

    student_name = f"{incarcerated}"
    student_data = {"name": student_name, "doc_num": incarcerated.doc_number}
    assets_data = []

    for asset in assets:
        asset_name = f"{asset}"

        cost = f"${asset.asset_cost:.2f}" if asset.asset_cost is not None else ""

        assets_data.append(
            {
                "name": asset_name,
                "id": asset.asset_id,
                "type": asset.asset_type,
                "cost": cost,
            }
        )

    # create agreements folder if it doesn't exist
    if not os.path.exists( f"{CALLER_SCRIPT_DIRECTORY}\\agreements" ):
        os.makedirs( f"{CALLER_SCRIPT_DIRECTORY}\\agreements" )

    output_filepath = f"{CALLER_SCRIPT_DIRECTORY}\\agreements\\{ incarcerated.doc_number }_{ current_time }.pdf"

    generate_pdf_from_template(
        template_path = f"{CALLER_SCRIPT_DIRECTORY}\\templates\\agreement.html",
        output_path   = output_filepath,
        options={
            "footer-html": footer_file_path,
            "margin-top": "0.35in",
            "margin-bottom": "1.25in",
            "margin-left": "0.5in",
            "margin-right": "0.5in",
            "disable-smart-shrinking": "",
            "page-size": "Letter",
        },
        context={
            "student": student_data,
            "assets": assets_data,
            "student_signature": signature,
            "college_signature": college_signature,
            "date": date,
            "exp_date": quarter_end_date,
            "facility_acronym": facility_acronym,
            "college_name": college_name,
            "logo": logo,
            "college_representative": college_representative,
        },
    )

    return output_filepath


def generate_schedule(
    incarcerated: Incarcerated, enrolled_courses: list[Enrollment]
) -> str:
    logo = encode_image_to_base64( f"{CALLER_SCRIPT_DIRECTORY}\\GHC-logo-horizontal-blue-web.png" )
    icon_logo = encode_image_to_base64( f"{CALLER_SCRIPT_DIRECTORY}\\GHC-logo-icon-blue-web.png" )

    year             = enrolled_courses[0].course_end_date.year
    quarter          = enrolled_courses[0].course_quarter
    facility_acronym = "Stafford Creek Corrections Center"
    college_name     = "Grays Harbor College"

    schedule_file_name = f"{ incarcerated.doc_number }.pdf"
    courses = []

    for course in enrolled_courses:
        course_start_time_str = course.course_start_time.strftime("%H:%M")
        course_end_time_str = course.course_end_time.strftime("%H:%M")

        hours_str = course_start_time_str + " - " + course_end_time_str
        courses.append(
            {
                "prefix": course.course_prefix,
                "code": course.course_code,
                "name": course.course_name,
                "credits": course.course_credits,
                "days": course.course_days,
                "hours": hours_str,
                "location": course.course_location,
                "instructor": course.course_instructor,
                "description": course.course_description,
            }
        )

    # Load your footer template
    with open( f"{CALLER_SCRIPT_DIRECTORY}\\templates\\schedule_footer.html", "r") as file:
        footer_template = Template(file.read())

    rendered_footer = footer_template.render(icon_logo=icon_logo)
    # Save rendered footer to a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w+"
    ) as temp_footer:
        footer_file_path = temp_footer.name
        temp_footer.write(rendered_footer)

    student_name = f"{incarcerated}"
    student_data = {"name": student_name, "doc_num": incarcerated.doc_number}

    # create schedules folder if it doesn't exist
    if not os.path.exists( f"{CALLER_SCRIPT_DIRECTORY}\\schedules" ):
        os.makedirs( f"{CALLER_SCRIPT_DIRECTORY}\\schedules" )

    schedule_filepath = f"{CALLER_SCRIPT_DIRECTORY}\\schedules\\{schedule_file_name}"

    generate_pdf_from_template(
        template_path = f"{CALLER_SCRIPT_DIRECTORY}\\templates\\schedule.html",
        output_path   = schedule_filepath,
        options={
            "footer-html": footer_file_path,
            "margin-top": "0.35in",
            "margin-bottom": "1.25in",
            "margin-left": "0.5in",
            "margin-right": "0.5in",
            "disable-smart-shrinking": "",
            "page-size": "Letter",
        },
        context={
            "student": student_data,
            "courses": courses,
            "logo": logo,
            "facility_acronym": facility_acronym,
            "college_name": college_name,
            "year": year,
            "quarter": quarter,
        },
    )

    # tell the caller where we saved the file
    return f"{schedule_filepath}"



# Below, we call PowerShell, which then calls Internet Explorer. We call I.E
# because it can display and print almost any kind of file. We use PowerShell
# to start I.E. because subprocess.call() would otherwise stall until I.E. is
# closed. It is a better experience to not 'block' Python, except when needed.
#
# Because subprocess.call() is sensitive to the spaces in I.E.'s directory
# path, we use Window's DOS-friendly 8.3 'short names' for "Program Files"
# (progra~1) and "Internet Explorer" (intern~1).

# TODO: See if we can get an Office-automation -like effect to prompt IE to
# print the file and exit, w/o the user having to manually intervene.

# Print the PDF file
def command_print(pdf_file):

    print( "Opening 'Internet Explorer' and waiting for it to exit... " )


    subprocess_command = "{} {}".format(
        # was:  "PDFtoPrinter.exe",
        'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command c:\\progra~1\\intern~1\\iexplore.exe',
        pdf_file,
    )

    subprocess.call( subprocess_command, shell=True )

    print( "OK, 'Internet Explorer' was started up. Continuing ... " )
