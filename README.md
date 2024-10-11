# Mock Parking Data Generator

This project provides a mock parking data generator to simulate realistic parking transactions for a fictitious parking company. The generated dataset includes information such as meter locations, payment methods, parking duration, and fines. The purpose of this tool is to demonstrate the potential of AI and data analytics in the parking industry.

## Features
- Generate realistic mock parking data, including occupancy rates, payment methods, and fines.
- Set parameters such as the number of days to simulate, occupancy rates, fine probabilities, parking rates, and payment weights.
- Output data to a CSV file.
- Streamlit-based GUI for user-friendly parameter selection.
- Deployable using Docker for easy sharing without dependencies installation.

## Technologies Used
- Python 3.10
- Streamlit: For creating an interactive web-based user interface.
- Faker: To generate realistic, random license plates and vehicle information.
- Docker: For containerizing the application to run without installing dependencies.
- NumPy: For random sampling.
- Pillow (PIL): For displaying images in the Streamlit interface.

## Installation
### Prerequisites
- Python 3.10 or later
- Git
- Docker (if using Docker for deployment)

### Clone the Repository
To get started, clone this repository:
```sh
git clone https://github.com/username/mock-parking-data.git
cd mock-parking-data
```

### Virtual Environment Setup (Optional)
Create and activate a virtual environment to manage dependencies:
```sh
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate    # Windows
```

### Install Dependencies
Install the necessary packages:
```sh
pip install -r requirements.txt
```

## Running the Application
### Streamlit
You can run the Streamlit application to generate mock parking data:
```sh
streamlit run mock-parking-streamlit.py
```
This will start a local server, and you can access the app at `http://localhost:8501`.

### Docker
To avoid installing dependencies, use Docker to containerize the application.

#### Build the Docker Image
```sh
docker build -t parking-mock-data-app .
```

#### Run the Docker Container
```sh
docker run -p 8501:8501 parking-mock-data-app
```
The application will be available at `http://localhost:8501`.

## Usage
1. **Upload a GeoJSON file** containing parking meter locations.
2. **Set parameters** such as occupancy rates, fine probability, and parking rates using sliders and text inputs.
3. **Generate data** by clicking the button. The mock data will be saved to a CSV file with the specified filename.

## Parameters
- **Number of Days to Simulate**: The number of days for which mock data will be generated.
- **Occupancy Rate Range**: The minimum and maximum percentage of meter occupancy.
- **Non-Functional Meter Percentage**: The percentage of meters that are non-functional during the simulation.
- **Fine Generation Probability**: The likelihood that a parking session will result in a fine.
- **Parking Rates**: Set hourly rates for downtown, medium distance, and far distance locations.
- **Payment Method Weights**: Set the percentage weight for each payment method (ParkMobile App, Credit Card, Cash).

## Files
- **`mock-parking-streamlit.py`**: Main script for running the Streamlit application.
- **`requirements.txt`**: List of required Python packages.
- **`Dockerfile`**: Instructions for building the Docker container.

## License
This project is licensed under the MIT License.

## Contributing
Feel free to submit pull requests or open issues to improve this project.

## Contact
For questions or suggestions, please contact [me] at [jrsherlock@gmail.com].

