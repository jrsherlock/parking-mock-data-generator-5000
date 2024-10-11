import random
import csv
import json
from faker import Faker
from datetime import datetime, timedelta
import calendar

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
def load_data_from_geojson(filepath):
    with open(filepath) as f:
        geojson_data = json.load(f)
    meters = []
    for feature in geojson_data['features']:
        if 'geometry' in feature and feature['geometry']['type'] == 'Point':
            meter_id = feature['properties'].get('meter_id')
            address = feature['properties'].get('address')
            coordinates = tuple(feature['geometry']['coordinates'][::-1])  # Reverse to (lat, long)
            meters.append({'meter_id': meter_id, 'address': address, 'coordinates': coordinates})
    return meters

# Function to generate mock parking data for a specified number of days
def generate_parking_data(meters, num_days):
    data = []

    for day in range(num_days):
        date = datetime(2024, 4, 1) + timedelta(days=day)
        weekday = date.weekday()
        occupancy_rate = random.uniform(0.7, 0.95) if weekday != 4 else random.uniform(0.85, 0.95)  # Peak on Fridays

        # Randomly select between 2% and 5% of meters to be non-functional
        non_functional_percentage = random.uniform(0.02, 0.05)
        num_non_functional_meters = int(len(meters) * non_functional_percentage)
        non_functional_meters = random.sample(meters, num_non_functional_meters)
        non_functional_meter_ids = {meter['meter_id'] for meter in non_functional_meters}

        for meter in meters:
            meter_id = meter['meter_id']
            address = meter['address']
            lat, long = meter['coordinates']

            if meter_id in non_functional_meter_ids:
                meter_status = 'non-functional'
                status_reason = random.choice(METER_STATUS_REASONS)
            else:
                meter_status = 'functioning'
                status_reason = None

                total_minutes_occupied = int(occupancy_rate * ENFORCEMENT_WINDOW)
                minutes_remaining = total_minutes_occupied

                while minutes_remaining > 0:
                    payment_method = random.choices(['parkmobile_app', 'credit_card', 'cash'], weights=[0.6, 0.2, 0.2], k=1)[0]
                    duration_minutes = min(minutes_remaining, random.choice([15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]))
                    duration_hours = round(duration_minutes / 60, 2)  # Convert duration to hours
                    parking_rate = 7.00 if lat > 41.88 else 5.25 if lat > 41.85 else 3.75
                    amount_paid = round(duration_hours * parking_rate, 2)  # Amount paid based on duration and rate
                    parking_rate = 7.00 if lat > 41.88 else 5.25 if lat > 41.85 else 3.75
                    fine_generated = random.random() < 0.15

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

                    license_plate_format = STATES[license_plate_state]
                    if license_plate_state == 'IL':
                        license_plate_number = fake.bothify(text='?? #####').upper()
                    elif license_plate_state == 'IA':
                        license_plate_number = fake.bothify(text='??? ###').upper()
                    elif license_plate_state == 'WI':
                        license_plate_number = fake.bothify(text='???-####').upper()
                    elif license_plate_state == 'MN':
                        license_plate_number = fake.bothify(text=random.choice(['???-###', '###-???']))
                    elif license_plate_state == 'IN':
                        license_plate_number = fake.bothify(text='######').upper()
                    elif license_plate_state == 'OH':
                        license_plate_number = fake.bothify(text='??? ####').upper()
                    elif license_plate_state == 'MO':
                        license_plate_number = fake.bothify(text='? ?# ?##').upper()
                    elif license_plate_state == 'KY':
                        license_plate_number = fake.bothify(text=random.choice(['######', '?#?###']))
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

                    revenue_generated = amount_paid - fine_amount
                    total_transaction = revenue_generated + fine_amount

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
                        status_reason,
                        revenue_generated,
                        total_transaction
                    ]
                    data.append(record)

                    minutes_remaining -= duration_minutes

            # If the meter is non-functional, add a record with the status
            if meter_status == 'non-functional':
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
                    status_reason,
                    0.0,  # No revenue generated
                    0.0  # No total transaction
                ]
                data.append(record)

    return data

# Function to save data to a CSV file
def save_to_csv(data, filename):
    headers = [
        'meter_id', 'address', 'payment_method', 'duration_hours', 'amount_paid', 'parking_rate', 'fine_generated',
        'fine_amount', 'violation_reason', 'license_plate_number', 'license_plate_state',
        'vehicle_make', 'vehicle_model', 'vehicle_color', 'latitude', 'longitude',
        'parking_start_time', 'parking_expire_time', 'meter_status', 'status_reason',
        'revenue_generated', 'total_transaction'
    ]
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

# Main function to guide the user through data creation
def main():
    print("Welcome to the Parking Data Mock Generator!")
    filename = input("Enter the filename to save the data (e.g., parking_data.csv): ")
    geojson_filepath = input("Enter the path to the Chicago GeoJSON file: ")
    num_days = int(input("Enter the number of days to simulate: "))
    
    print("Loading data from GeoJSON file...")
    meters = load_data_from_geojson(geojson_filepath)
    
    print("Generating data...")
    data = generate_parking_data(meters, num_days)
    
    print(f"Saving data to {filename}...")
    save_to_csv(data, filename)
    
    print(f"Data generation complete! Data saved to {filename}.")

if __name__ == "__main__":
    main()