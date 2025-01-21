# Asset Management App

> ## ⚠️ Important Notice
> This repository is no longer being updated. The Asset Management App is being rewritten and included as part of the [Prometheus web app](https://github.com/brandonhenness/Prometheus). Please refer to the Prometheus repository for the latest version and updates.

## Overview
The **Asset Management App** is a solution designed to track and manage educational assets, including laptops, books, calculators, and more, at the Stafford Creek Corrections Center (SCCC) for Grays Harbor College. The application ensures efficient inventory management by storing all data in a PostgreSQL database.

## Features
- **Asset Tracking**: Keep records of laptops, books, calculators, and other equipment.
- **Error Handling and Recovery**: Warnings and error messages guide users through resolution steps.
- **Search and Filtering**: Quickly locate specific items using built-in search and filter options.
- **Printing Support**: Generate and print schedules or loan agreements with WebKit integration.
- **Signature Pad Compatibility**: Supports digital signatures for asset agreements.
- **Secure Data Storage**: All information is securely stored in a PostgreSQL database.

---

## Getting Started

### Prerequisites
To run the Asset Management App, you will need:
- Python 3.12
- PostgreSQL database
- Required Python libraries (specified in `requirements.txt`)
- **WebKit** for printing capabilities
- **SigPlus Software** for signature pad functionality

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/brandonhenness/GHC.Asset-Management-App.git
   ```
2. Navigate to the project directory:
   ```bash
   cd GHC.Asset-Management-App
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install WebKit and SigPlus software:
   - **WebKit**: Install `wkhtmltox-0.12.6-1.msvc2015-win64.exe` as an administrator.
   - **SigPlus**: Install `SigPlusOCXx64.msi` with admin credentials, selecting the correct model.

5. Configure the database connection:
   - Create a `config.py` file in the root of the project with the following content:

     ```python
     # config.py
     # Contains configuration settings for the AMS program.

     # General settings
     APP_NAME = "Asset Management System"
     VERSION = "1.5.1"

     # Debug settings
     LIVE_DATABASE = True  # True --> use live database; False --> use test database (+ verbose errors)
     VERBOSE_ERROR = True  # True --> prints verbose errors in MAGENTA; False --> skips live errors
     VERBOSE_NO_CLEAR_SCREEN = False  # True --> stops clear_screen() from clearing program output (creates visual problems)

     # Database settings
     HOST = "localhost"
     DATABASE = "db"
     USER = "postgres"
     PASSWORD = "password"

     # Dev Database settings
     DEV_HOST = "localhost"
     DEV_DATABASE = "dev_db"
     DEV_USER = "postgres"
     DEV_PASSWORD = "password"
     ```

6. Verify installation:
   - Ensure Python 3.12 is installed correctly in `C:\Program Files\Python312`.
   - Check that `requirements.txt` dependencies are installed without errors.

---

## Usage

### Running the Application
1. **Set up the default printer**:
   - Configure the printer to print double-sided by default.
   - Example for OSN:
     ```
     \\osnflabr1500\OSNpABR1007
     ```

2. Plug in the **signature pad** and configure the **barcode scanner**:
   - Barcode scanner settings should add an **ENTER** after each scan.

3. Launch the app:
   ```bash
   python app.py
   ```
4. Access the app via your web browser at `http://localhost:5000`.

5. Follow any on-screen instructions for errors or warnings.

### Exiting the Application
1. Return to the main menu by pressing `ENTER`.
2. Exit the app by pressing `q`.

---

## Troubleshooting

### Errors During Startup
- **Fatal Error: No module named 'psycopg2'**:
  Ensure Python dependencies are installed correctly.
  Refer to `AAA___readme___OSN.txt` for detailed setup steps.

- **Warning: WebKit Not Found**:
  Install WebKit if you need to print schedules or agreements.

### Common Fixes
- For Python errors, re-run the installation steps for Python 3.12 and the required packages.
- Printing issues can often be resolved by reinstalling WebKit.

---

## Contributing
Contributions are welcome! Please open an issue or submit a pull request if you have suggestions or improvements.

---

## License
Asset Management App is licensed under the [GNU General Public License v3.0](LICENSE).

---

## Contact
For any inquiries or feedback, please reach out to:
- **Brandon Henness**
- Email: [brhenness@ghcares.org](mailto:brhenness@ghcares.org)

