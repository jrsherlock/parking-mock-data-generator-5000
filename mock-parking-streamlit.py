import random
import csv
import json
from faker import Faker
from datetime import datetime, timedelta
import streamlit as st # type: ignore
from PIL import Image # type: ignore
import numpy as np # type: ignore
import time

fake = Faker()

# Constants for generating mock data
STATES = {
    "IL": "AB 12345",
    "IA": "ABC 123",
    "WI": "ABC-1234",
    "MN": "ABC-123 or 123-ABC",
    "IN": "123ABC",
    "OH": "ABC 1234",
    "MO": "A A1 B2C",
    "KY": "ABC123 or A1B234"
}
PAYMENT_METHODS = ['cash', 'credit_card', 'parkmobile_app']
VEHICLE_MAKES = ['Ford', 'Toyota', 'Honda', 'Chevrolet', 'Nissan', 'BMW', 'Audi', 'Tesla']
VEHICLE_MODELS = ['Focus', 'Camry', 'Civic', 'Malibu', 'Altima', '3 Series', 'A4', 'Model 3']
VEHICLE_COLORS = ['Red', 'Blue', 'Black', 'White', 'Silver', 'Gray', 'Green']
VIOLATION_REASONS = ['expired_meter', 'no_parking_zone', 'improper_parking']
ENFORCEMENT_WINDOW = 13 * 60  # 13 hours in minutes (8 AM - 9 PM)
METER_STATUS_REASONS = ['jammed', 'network_issue', 'power_failure', 'vandalized', 'unknown_error']

# Load data from GeoJSON file
def load_data_from_geojson(file):
    if isinstance(file, str):
        with open(file) as f:
            geojson_data = json.load(f)
    else:
        geojson_data = json.loads(file.read().decode('utf-8'))
    meters = []
    for feature in geojson_data['features']:
        if 'geometry' in feature and feature['geometry']['type'] == 'Point':
            meter_id = feature['properties'].get('meter_id')
            address = feature['properties'].get('address')
            coordinates = tuple(feature['geometry']['coordinates'][::-1])  # Reverse to (lat, long)
            meters.append({'meter_id': meter_id, 'address': address, 'coordinates': coordinates})
    return meters

# Function to generate mock parking data for a specified number of days
def generate_parking_data(meters, num_days, occupancy_rate_range, non_functional_percentage, fine_probability, parking_rates, payment_weights):
    data = []
    progress_bar = st.progress(0)

    for day in range(num_days):
        date = datetime(2024, 4, 1) + timedelta(days=day)
        weekday = date.weekday()
        occupancy_rate = random.uniform(*occupancy_rate_range) if weekday != 4 else random.uniform(0.85, 0.95)  # Peak on Fridays

        # Randomly select the percentage of meters to be non-functional
        num_non_functional_meters = int(len(meters) * non_functional_percentage)
        non_functional_meters = np.random.choice(meters, num_non_functional_meters, replace=False)
        non_functional_meter_ids = {meter['meter_id'] for meter in non_functional_meters}

        for i, meter in enumerate(meters):
            meter_id = meter['meter_id']
            address = meter['address']
            lat, long = meter['coordinates']

            if meter_id in non_functional_meter_ids:
                meter_status = 'non-functional'
                status_reason = random.choice(METER_STATUS_REASONS)
                # Add record for non-functional meter
                record = [
                    meter_id,
                    address,
                    None,  # No payment method
                    0,  # No duration
                    0.0,  # No amount paid
                    0.0,  # No parking rate
                    False,  # No fine generated
                    0.0,  # No fine amount
                    None,  # No violation reason
                    None,  # No license plate number
                    None,  # No license plate state
                    None,  # No vehicle make
                    None,  # No vehicle model
                    None,  # No vehicle color
                    lat,
                    long,
                    None,  # No start time
                    None,  # No expire time
                    meter_status,
                    status_reason
                ]
                data.append(record)
            else:
                meter_status = 'functioning'
                status_reason = None

                total_minutes_occupied = int(occupancy_rate * ENFORCEMENT_WINDOW)
                minutes_remaining = total_minutes_occupied

                while minutes_remaining > 0:
                    payment_method = random.choices(['parkmobile_app', 'credit_card', 'cash'], weights=payment_weights, k=1)[0]
                    duration_minutes = min(minutes_remaining, random.choice([15 * i for i in range(1, 13)]))  # Up to 180 mins
                    duration_hours = round(duration_minutes / 60, 2)  # Convert duration to hours

                    if lat > 41.88:
                        parking_rate = parking_rates['downtown']
                    elif lat > 41.85:
                        parking_rate = parking_rates['medium']
                    else:
                        parking_rate = parking_rates['far']

                    amount_paid = round(duration_hours * parking_rate, 2)  # Amount paid based on duration and rate
                    fine_generated = random.random() < fine_probability

                    if fine_generated:
                        violation_reason = random.choice(VIOLATION_REASONS)
                        fine_amount = round(parking_rate * duration_hours, 2)
                        license_plate_state = random.choices(
                            population=list(STATES.keys()),
                            weights=[0.3 if s == "IL" else 0.4 if s == "IN" else 0.3 / (len(STATES) - 2) for s in STATES.keys()],
                            k=1
                        )[0]
                    else:
                        fine_amount = 0.0
                        violation_reason = None
                        license_plate_state = random.choice(list(STATES.keys()))

                    if license_plate_state == 'IL':
                        license_plate_number = fake.bothify(text='?? #####').upper()
                    elif license_plate_state == 'IA':
                        license_plate_number = fake.bothify(text='??? ###').upper()
                    elif license_plate_state == 'WI':
                        license_plate_number = fake.bothify(text='???-####').upper()
                    elif license_plate_state == 'MN':
                        license_plate_number = fake.bothify(text=random.choice(['???-###', '###-???'])).upper()
                    elif license_plate_state == 'IN':
                        license_plate_number = fake.bothify(text='######').upper()
                    elif license_plate_state == 'OH':
                        license_plate_number = fake.bothify(text='??? ####').upper()
                    elif license_plate_state == 'MO':
                        license_plate_number = fake.bothify(text='? ?# ?##').upper()
                    elif license_plate_state == 'KY':
                        license_plate_number = fake.bothify(text=random.choice(['######', '?#?###'])).upper()
                    else:
                        license_plate_number = 'UNKNOWN'

                    vehicle_make = random.choice(VEHICLE_MAKES)
                    vehicle_model = random.choice(VEHICLE_MODELS)
                    vehicle_color = random.choice(VEHICLE_COLORS)

                    # Generate parking start and expire times with skew towards 10 AM - 6 PM
                    if random.random() < 0.7:
                        start_hour = random.randint(10, 18)  # 70% chance between 10 AM and 6 PM
                    else:
                        start_hour = random.choice([8, 9, 19, 20])  # 30% chance for early morning or late evening
                    start_minute = random.randint(0, 59)
                    parking_start_time = datetime(date.year, date.month, date.day, start_hour, start_minute)
                    parking_expire_time = parking_start_time + timedelta(minutes=duration_minutes)

                    record = [
                        meter_id,
                        address,
                        payment_method,
                        duration_hours,
                        amount_paid,
                        parking_rate,
                        fine_generated,
                        fine_amount,
                        violation_reason,
                        license_plate_number,
                        license_plate_state,
                        vehicle_make,
                        vehicle_model,
                        vehicle_color,
                        lat,
                        long,
                        parking_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        parking_expire_time.strftime("%Y-%m-%d %H:%M:%S"),
                        meter_status,
                        status_reason
                    ]
                    data.append(record)

                    minutes_remaining -= duration_minutes

            # Update progress bar
            progress_bar.progress((i + 1) / len(meters))
            time.sleep(0.01)  # Small delay to update progress

    return data

# Function to save data to a CSV file
def save_to_csv(data, filename):
    headers = [
        'meter_id', 'address', 'payment_method', 'duration_hours', 'amount_paid', 'parking_rate', 'fine_generated',
        'fine_amount', 'violation_reason', 'license_plate_number', 'license_plate_state',
        'vehicle_make', 'vehicle_model', 'vehicle_color', 'latitude', 'longitude',
        'parking_start_time', 'parking_expire_time', 'meter_status', 'status_reason'
    ]
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

# Main function to guide the user through data creation using Streamlit
def main():
    st.title("Parking Mock Data Generator")
    st.write("Customize the parameters below to generate realistic mock parking data.")

    # Display logo
    logo_path = "./risetek.jpeg"
    try:
        logo_image = Image.open(logo_path)
        st.image(logo_image, width=200)
    except FileNotFoundError:
        st.warning("Logo image not found.")

    # Number of days to simulate
    num_days = st.slider("Number of days to simulate:", min_value=1, max_value=30, value=1)
    st.info("Number of days to simulate: The duration for which mock parking data will be generated, ranging from 1 to 30 days.")

    # Occupancy rate sliders
    st.write("Occupancy Rate Range (%):")
    occupancy_min = st.slider("Min Occupancy", min_value=50, max_value=100, value=70)
    st.info("Min Occupancy: The minimum occupancy rate for parking meters, indicating how occupied the meters should be.")
    occupancy_max = st.slider("Max Occupancy", min_value=50, max_value=100, value=95)
    st.info("Max Occupancy: The maximum occupancy rate for parking meters, indicating how occupied the meters should be.")
    occupancy_rate_range = (occupancy_min / 100, occupancy_max / 100)  # Convert to 0-1 range

    # Non-functional meter percentage
    non_functional_percentage = st.slider("Non-Functional Meter Percentage (%):", min_value=2, max_value=10, value=5) / 100
    st.info("Non-Functional Meter Percentage: The percentage of parking meters that are non-functional during the simulation period.")

    # Fine generation probability
    fine_probability = st.slider("Fine Generation Probability (%):", min_value=0, max_value=100, value=15) / 100
    st.info("Fine Generation Probability: The likelihood that a parking session will result in a fine, expressed as a percentage.")

    # Parking rates
    st.write("Parking Rates ($/hr):")
    downtown_rate = st.number_input("Downtown Rate:", value=7.00, min_value=0.0)
    st.info("Downtown Rate: The hourly rate for parking meters located in downtown areas.")
    medium_rate = st.number_input("Medium Distance Rate:", value=5.25, min_value=0.0)
    st.info("Medium Distance Rate: The hourly rate for parking meters located in areas of medium distance from downtown.")
    far_rate = st.number_input("Far Distance Rate:", value=3.75, min_value=0.0)
    st.info("Far Distance Rate: The hourly rate for parking meters located furthest away from downtown areas.")
    parking_rates = {
        'downtown': downtown_rate,
        'medium': medium_rate,
        'far': far_rate
    }

    # Payment method weights
    st.write("Payment Method Weights (%):")
    parkmobile_weight = st.slider("ParkMobile App:", min_value=0, max_value=100, value=60)
    st.info("ParkMobile App: The percentage weight indicating how often the ParkMobile app is used as a payment method.")
    credit_card_weight = st.slider("Credit Card:", min_value=0, max_value=100, value=20)
    st.info("Credit Card: The percentage weight indicating how often credit cards are used as a payment method.")
    cash_weight = st.slider("Cash:", min_value=0, max_value=100, value=20)
    st.info("Cash: The percentage weight indicating how often cash is used as a payment method.")
    payment_weights = [parkmobile_weight, credit_card_weight, cash_weight]

    # File inputs
    geojson_file = st.file_uploader("Upload GeoJSON File:", type=["geojson"])
    output_filename = st.text_input("Output CSV Filename:", value="mock_parking_data.csv")

    # Generate data button
    if st.button("Generate Data"):
        if geojson_file is None or not output_filename:
            st.error("Please provide a GeoJSON file and output filename.")
        else:
            st.write("Loading data from GeoJSON file...")
            meters = load_data_from_geojson(geojson_file)

            st.write("Generating data...")
            data = generate_parking_data(
                meters, num_days, occupancy_rate_range, non_functional_percentage,
                fine_probability, parking_rates, payment_weights
            )

            st.write(f"Saving data to {output_filename}...")
            save_to_csv(data, output_filename)

            st.success(f"Data generation complete! Data saved to {output_filename}.")

if __name__ == "__main__":
    main()