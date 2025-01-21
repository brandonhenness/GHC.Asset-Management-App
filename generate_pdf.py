import os
from jinja2 import Environment, FileSystemLoader
import pdfkit
import datetime
from dateutil.relativedelta import relativedelta
import base64
from jinja2 import Template
import subprocess
from main import Asset, Incarcerated, Calculator, Laptop, Book, Enrollment
import tempfile

path_wkhtmltopdf = "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


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
    pdfkit.from_string(html, output_path, options=options, configuration=config)


def format_name(incarcerated):
    # Handles None values by replacing them with an empty string
    first_name = incarcerated.first_name if incarcerated.first_name is not None else ""
    middle_name = (
        incarcerated.middle_name if incarcerated.middle_name is not None else ""
    )
    last_name = incarcerated.last_name if incarcerated.last_name is not None else ""

    return f"{last_name}, {first_name} {middle_name}".strip()


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
    signature: base64, incarcerated: Incarcerated, assets: list[Asset], current_time
) -> None:
    dean_signature = encode_image_to_base64("dean_signature.png")
    logo = encode_image_to_base64("GHC-logo-horizontal-blue-web.png")
    icon_logo = encode_image_to_base64("GHC-logo-icon-blue-web.png")

    current_date = datetime.datetime.now()
    date = current_date.strftime("%m/%d/%Y")
    facility_acronym = "Stafford Creek Corrections Center"
    college_name = "Grays Harbor College"
    dean_name = "Peterson, Jayme"

    # exp_date = current_date + relativedelta(months=3)
    # exp_date = exp_date.strftime("%m/%d/%Y")
    exp_date = "03/22/2024"

    # Load your footer template
    with open("templates/agreement_footer.html", "r") as file:
        footer_template = Template(file.read())

    rendered_footer = footer_template.render(icon_logo=icon_logo)
    # Save rendered footer to a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w+"
    ) as temp_footer:
        footer_file_path = temp_footer.name
        temp_footer.write(rendered_footer)

    student_name = format_name(incarcerated)
    student_data = {"name": student_name, "doc_num": incarcerated.doc_number}
    assets_data = []

    for asset in assets:
        asset_name = ""
        if asset.asset_type == "LAPTOP" or asset.asset_type == "CALCULATOR":
            asset_name = asset.model if asset.model is not None else ""
        elif asset.asset_type == "BOOK":
            asset_name = asset.title if asset.title is not None else ""

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
    if not os.path.exists("agreements"):
        os.makedirs("agreements")

    generate_pdf_from_template(
        template_path="templates/agreement.html",
        output_path=f"agreements/{ incarcerated.doc_number }_{ current_time }.pdf",
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
            "dean_signature": dean_signature,
            "date": date,
            "exp_date": exp_date,
            "facility_acronym": facility_acronym,
            "college_name": college_name,
            "logo": logo,
            "dean_name": dean_name,
        },
    )


def generate_schedule(
    incarcerated: Incarcerated, enrolled_courses: list[Enrollment]
) -> None:
    logo = encode_image_to_base64("GHC-logo-horizontal-blue-web.png")
    icon_logo = encode_image_to_base64("GHC-logo-icon-blue-web.png")

    year = 2024
    quarter = "Winter"
    facility_acronym = "Stafford Creek Corrections Center"
    college_name = "Grays Harbor College"

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
    with open("templates/schedule_footer.html", "r") as file:
        footer_template = Template(file.read())

    rendered_footer = footer_template.render(icon_logo=icon_logo)
    # Save rendered footer to a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w+"
    ) as temp_footer:
        footer_file_path = temp_footer.name
        temp_footer.write(rendered_footer)

    student_name = format_name(incarcerated)
    student_data = {"name": student_name, "doc_num": incarcerated.doc_number}

    # create schedules folder if it doesn't exist
    if not os.path.exists("schedules"):
        os.makedirs("schedules")

    generate_pdf_from_template(
        template_path="templates/schedule.html",
        output_path=f"schedules/{ incarcerated.doc_number }.pdf",
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


# Print the PDF file
def command_print(pdf_file):
    command = "{} {}".format(
        "PDFtoPrinter.exe",
        pdf_file,
    )
    subprocess.call(command, shell=True)
