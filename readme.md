# Vehicle Service & Garage Management System

A console-based garage management project reconstructed from the supplied
55-page project report. It uses **Python**, **MySQL**, **Pandas**,
**Matplotlib**, **tabulate**, **Colorama**, and **stdiomask**.

## Features

### Roles
- **Admin:** manage users, services, spare-parts inventory and bookings;
  assign mechanics; view revenue and status reports.
- **Mechanic:** view assigned jobs and update job status.
- **Customer:** register/login, manage vehicles, book services, view booking
  history, cancel pending bookings, pay invoices and edit profile.

### Database tables
1. `users` — admin, mechanic and customer accounts
2. `services` — garage services and prices
3. `inventory` — spare parts and stock
4. `vehicles` — customer vehicles
5. `bookings` — service bookings and mechanic assignment
6. `invoices` — booking invoices and payment status

## Requirements

- Python 3.10 or newer
- MySQL Server 8.x (or a compatible MySQL server)
- A MySQL account allowed to create a database and tables

## Installation

1. Install and start MySQL Server.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (recommended):

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the Python packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

## MySQL configuration

Set these environment variables before starting the application.
The defaults are `localhost`, user `root`, database `automotive_pro`,
and port `3306`. The password defaults to an empty string.

**Windows PowerShell**
```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your_mysql_password"
$env:DB_NAME = "automotive_pro"
$env:DB_PORT = "3306"
```

**Windows Command Prompt**
```bat
set DB_HOST=localhost
set DB_USER=root
set DB_PASSWORD=your_mysql_password
set DB_NAME=automotive_pro
set DB_PORT=3306
```

**macOS/Linux**
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD='your_mysql_password'
export DB_NAME=automotive_pro
export DB_PORT=3306
```

The application creates the `automotive_pro` database and required tables
automatically when it starts.

## Run

```bash
python main.py
```

On the first run, the program inserts this default administrator if the
username/email is not already present:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

Log in and change this password immediately. Do not use the sample credentials
for a public or production system.

## Typical workflow

1. Log in as the administrator.
2. Add services and prices in **Manage Services**.
3. Add mechanic accounts in **Manage Users** using role `Mechanic`.
4. Register a customer account from the welcome menu.
5. As the customer, add a vehicle and book a service.
6. As the administrator, assign the booking to a mechanic.
7. The mechanic updates the job to `In Progress` and then `Completed`.
8. The customer can pay the invoice. The admin can view reports and graphs.

## Project files

```text
vehicle_garage_reconstructed/
├── main.py
├── requirements.txt
└── README.md
```

## Important notes about this reconstruction

- This is a cleaned, single-file reconstruction of the code and features
  presented in the source PDF, not a byte-for-byte copy.
- Broken line wraps, indentation problems, missing return/connection cleanup,
  and several unsafe record lookups in the extracted listing were corrected.
- Booking creation now inserts the booking and its invoice in one transaction.
- Database credentials are read from environment variables instead of being
  hard-coded in the source.
- The original report stores passwords as plain text. This reconstruction
  retains that behavior to remain compatible with the report's simple login
  flow. **It is for classroom demonstration only**; a real application must
  use password hashing, stronger authorization and additional validation.
- Payment is represented as an update to the invoice status; no real payment
  gateway or money transfer is connected.
- The program has not been tested against your local MySQL server. Configure
  the connection and test it with sample data before presenting it.

## Troubleshooting

- **Access denied:** verify `DB_USER` and `DB_PASSWORD`.
- **Can't connect to MySQL:** make sure the MySQL service is running and
  `DB_HOST`/`DB_PORT` are correct.
- **No module named ...:** activate the virtual environment and run
  `python -m pip install -r requirements.txt` again.
- **Graph window does not appear:** run the program in a desktop environment
  with a Matplotlib-supported GUI backend.
