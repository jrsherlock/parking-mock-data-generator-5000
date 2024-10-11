import random
import csv
import json
from faker import Faker
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from multiprocessing import Pool
import os

fake = Faker()

# Constants remain the same as before
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

def load_data_from_geojson(filepath: str) -> List[Dict[str, any]]:
    try:
        with open(filepath) as f:
            geojson_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading GeoJSON file: {e}")
        return []

    meters = []
    for feature in geojson_data.get('features', []):
        if 'geometry' in feature and feature['geometry']['type'] == 'Point':
            meter_id = feature['properties'].get('meter_id')
            address = feature['properties'].get('address')
            coordinates = tuple(feature['geometry']['coordinates'][::-1])  # Reverse to (lat, long)
            meters.append({'meter_id': meter_id, 'address': address, 'coordinates': coordinates})
    return meters

def calculate_occupancy_rate(current_date: date) -> float:
    weekday = current_date.weekday()
    return random.uniform(0.85, 0.95) if weekday == 4 else random.uniform(0.7, 0.95)

def select_non_functional_meters(meters: List[Dict[str, any]]) -> Set[str]:
    non_functional_percentage = random.uniform(0.02, 0.05)
    num_non_functional_meters = int(len(meters) * non_functional_percentage)
    non_functional_meters = random.sample(meters, num_non_functional_meters)
    return {meter['meter_id'] for meter in non_functional_meters}

def generate_meter_data(args: Tuple[Dict[str, any], date, float, Set[str]]) -> List[List[any]]:
    meter, current_date, occupancy_rate, non_functional_meter_ids = args
    meter_id = meter['meter_id']
    address = meter['address']
    lat, long = meter['coordinates']

    results = []

    if meter_id in non_functional_meter_ids:
        results.append([
            meter_id, address, None, 0, 0.0, 0.0, False, 0.0, None, None, None, None, None, None,
            lat, long, None, None, 'non-functional', random.choice(METER_STATUS_REASONS), 0.0, 0.0
        ])
    else:
        total_minutes_occupied = int(occupancy_rate * ENFORCEMENT_WINDOW)
        minutes_remaining = total_minutes_occupied

        while minutes_remaining > 0:
            payment_method = random.choices(PAYMENT_METHODS, weights=[0.6, 0.2, 0.2], k=1)[0]
            duration_minutes = min(minutes_remaining, random.choice([15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]))
            duration_hours = round(duration_minutes / 60, 2)
            parking_rate = 7.00 if lat > 41.88 else 5.25 if lat > 41.85 else 3.75
            amount_paid = round(duration_hours * random.uniform(3.75, 7.00), 2)
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
            license_plate_number = fake.bothify(text=license_plate_format)
            vehicle_make = random.choice(VEHICLE_MAKES)
            vehicle_model = random.choice(VEHICLE_MODELS)
            vehicle_color = random.choice(VEHICLE_COLORS)

            if random.random() < 0.7:
                start_hour = random.randint(10, 18)
            else:
                start_hour = random.choice([8, 9, 19, 20])
            start_minute = random.randint(0, 59)
            parking_start_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=start_hour, minutes=start_minute)
            parking_expire_time = parking_start_time + timedelta(minutes=duration_minutes)

            revenue_generated = amount_paid - fine_amount
            total_transaction = revenue_generated + fine_amount

            results.append([
                meter_id, address, payment_method, duration_hours, amount_paid, parking_rate,
                fine_generated, fine_amount, violation_reason, license_plate_number, license_plate_state,
                vehicle_make, vehicle_model, vehicle_color, lat, long,
                parking_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                parking_expire_time.strftime("%Y-%m-%d %H:%M:%S"),
                'functioning', None, revenue_generated, total_transaction
            ])

            minutes_remaining -= duration_minutes

    return results

def generate_parking_data(meters: List[Dict[str, any]], num_days: int) -> List[List[any]]:
    start_date = date(2024, 4, 1)
    all_data = []
    
    with Pool() as pool:
        for day in range(num_days):
            current_date = start_date + timedelta(days=day)
            occupancy_rate = calculate_occupancy_rate(current_date)
            non_functional_meter_ids = select_non_functional_meters(meters)
            
            args = [(meter, current_date, occupancy_rate, non_functional_meter_ids) for meter in meters]
            results = pool.map(generate_meter_data, args)
            
            for result in results:
                all_data.extend(result)
    
    return all_data

def save_to_csv(data: List[List[any]], filename: str) -> None:
    headers = [
        'meter_id', 'address', 'payment_method', 'duration_hours', 'amount_paid', 'parking_rate', 'fine_generated',
        'fine_amount', 'violation_reason', 'license_plate_number', 'license_plate_state',
        'vehicle_make', 'vehicle_model', 'vehicle_color', 'latitude', 'longitude',
        'parking_start_time', 'parking_expire_time', 'meter_status', 'status_reason',
        'revenue_generated', 'total_transaction'
    ]
    try:
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(data)
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

def get_positive_integer(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main() -> None:
    print("Welcome to the Parking Data Mock Generator!")
    filename = input("Enter the filename to save the data (e.g., parking_data.csv): ")
    geojson_filepath = input("Enter the path to the Chicago GeoJSON file: ")
    num_days = get_positive_integer("Enter the number of days to simulate: ")
    
    print("Loading data from GeoJSON file...")
    meters = load_data_from_geojson(geojson_filepath)
    
    if not meters:
        print("No meter data loaded. Exiting.")
        return

    print("Generating data...")
    data = generate_parking_data(meters, num_days)
    
    print(f"Saving data to {filename}...")
    save_to_csv(data, filename)
    
    print(f"Data generation complete! Data saved to {filename}.")

if __name__ == "__main__":
    main()