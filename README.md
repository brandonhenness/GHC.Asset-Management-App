# Asset Management App

## ⚠️ Important Notice
This repository is no longer being updated. The Asset Management App is being rewritten and included as part of the [Prometheus web app](https://github.com/brandonhenness/Prometheus). Please refer to the Prometheus repository for the latest version and updates.

## Overview
The **Asset Management App** is a solution designed to track and manage educational assets, including laptops, books, calculators, and more, at the Stafford Creek Corrections Center (SCCC) for Grays Harbor College. The application ensures efficient inventory management by storing all data in a PostgreSQL database.

## Features
- **Asset Tracking**: Keep records of laptops, books, calculators, and other equipment.
- **Search and Filtering**: Quickly locate specific items using built-in search and filter options.
- **User-Friendly Interface**: Designed for ease of use to streamline asset management tasks.
- **Secure Data Storage**: All information is securely stored in a PostgreSQL database.

## Getting Started

### Prerequisites
To run the Asset Management App, you will need:
- Python 3.x
- PostgreSQL database
- Required Python libraries (specified in `requirements.txt`)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/brandonhenness/GHC.Asset-Management-App.git
   ```
2. Navigate to the project directory:
   ```bash
   cd GHC.Asset-Management-App
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the database connection:
   - Update the database settings in `config.py` to match your PostgreSQL setup.

### Usage
1. Initialize the database:
   ```bash
   python init_db.py
   ```
   This will set up the necessary tables in the PostgreSQL database.
2. Run the application:
   ```bash
   python app.py
   ```
3. Access the app via your web browser at `http://localhost:5000`.

## Project Structure
- `app.py`: Main application file.
- `config.py`: Configuration file for database connection.
- `models/`: Contains the database models.
- `templates/`: HTML templates for the web interface.
- `static/`: Static assets like CSS and JavaScript files.
- `requirements.txt`: List of Python dependencies.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request if you have suggestions or improvements.

## License
Asset Management App is licensed under the [GNU General Public License v3.0](LICENSE).

## Contact
For any inquiries or feedback, please reach out to:
- **Brandon Henness**
- Email: [brhenness@ghcares.org](mailto:brandon.henness@doc1.wa.gov)
