"""
Vehicle Service & Garage Management System
Reconstructed from the supplied project-report PDF.

Run: python main.py
Configure MySQL with environment variables (see README.md).
"""

import os
from decimal import Decimal, InvalidOperation

import matplotlib.pyplot as plt
import mysql.connector
import pandas as pd
import stdiomask
from colorama import Fore, Style, init
from mysql.connector import Error
from tabulate import tabulate
from sqlalchemy import URL, create_engine

init(autoreset=True)

C = {
    "title": Style.BRIGHT + Fore.CYAN,
    "success": Style.BRIGHT + Fore.GREEN,
    "error": Style.BRIGHT + Fore.RED,
    "prompt": Style.BRIGHT + Fore.YELLOW,
    "info": Fore.WHITE,
}
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "automotive_pro")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def get_db_connection(with_database=True):
    """Connect to MySQL. Create the project database if it is missing."""
    config = {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT,
    }
    try:
        if with_database:
            try:
                return mysql.connector.connect(database=DB_NAME, **config)
            except Error as exc:
                if exc.errno != 1049:  # Unknown database
                    raise
        conn = mysql.connector.connect(**config)
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cur.close()
        conn.database = DB_NAME
        return conn
    except Error as exc:
        print(f"{C['error']}MySQL connection error: {exc}")
        return None


def get_engine():
    """SQLAlchemy engine used by Pandas for report queries."""
    url = URL.create(
        "mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    return create_engine(url, pool_pre_ping=True)


def create_tables():
    """Create the six tables used by the application and seed an admin."""
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Could not connect to MySQL.")
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('Admin','Mechanic','Customer') NOT NULL,
            phone VARCHAR(20),
            email VARCHAR(100) UNIQUE,
            Register_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS services (
            service_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            description VARCHAR(200)
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,
            price DECIMAL(10,2) NOT NULL
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            plate_no VARCHAR(20) NOT NULL,
            model VARCHAR(50),
            brand VARCHAR(50),
            CONSTRAINT fk_vehicle_user FOREIGN KEY (user_id)
                REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            vehicle_id INT NOT NULL,
            service_id INT NOT NULL,
            mechanic_id INT NULL,
            status ENUM('Pending','In Progress','Completed','Cancelled')
                NOT NULL DEFAULT 'Pending',
            `date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_booking_user FOREIGN KEY (user_id)
                REFERENCES users(user_id),
            CONSTRAINT fk_booking_vehicle FOREIGN KEY (vehicle_id)
                REFERENCES vehicles(vehicle_id),
            CONSTRAINT fk_booking_service FOREIGN KEY (service_id)
                REFERENCES services(service_id),
            CONSTRAINT fk_booking_mechanic FOREIGN KEY (mechanic_id)
                REFERENCES users(user_id)
        ) ENGINE=InnoDB
        """,
        """
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL UNIQUE,
            amount DECIMAL(10,2) NOT NULL,
            status ENUM('Paid','Unpaid') NOT NULL DEFAULT 'Unpaid',
            Paid_Time TIMESTAMP NULL DEFAULT NULL,
            CONSTRAINT fk_invoice_booking FOREIGN KEY (booking_id)
                REFERENCES bookings(booking_id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """,
    ]
    try:
        cur = conn.cursor()
        for statement in statements:
            cur.execute(statement)
        cur.execute(
            """
            INSERT INTO users (name, username, password, role, phone, email)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE username=username
            """,
            (
                "System Admin", "admin", "admin123", "Admin",
                "0000000000", "admin@automotive.com",
            ),
        )
        conn.commit()
        print(f"{C['success']}Database and tables are ready.")
        print(f"{C['info']}Default login: username=admin, password=admin123")
        print(f"{C['info']}Change the default password after first login.")
    except Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_data(query, params=None):
    """Run a parameterized SELECT and return rows as dictionaries."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        return cur.fetchall()
    except Error as exc:
        print(f"{C['error']}Database read error: {exc}")
        return []
    finally:
        conn.close()


def execute_query(query, params=None):
    """Run a parameterized INSERT, UPDATE or DELETE."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        return True
    except Error as exc:
        conn.rollback()
        print(f"{C['error']}Database operation failed: {exc}")
        return False
    finally:
        conn.close()


def get_input(prompt, hidden=False):
    label = f"{C['prompt']}{prompt}: "
    if hidden:
        return stdiomask.getpass(label)
    return input(label).strip()


def pause():
    input(f"\n{C['info']}Press Enter to continue...")


def show_table(rows):
    if rows:
        print(tabulate(rows, headers="keys", tablefmt="fancy_grid"))
    else:
        print("No records found.")


def get_money(prompt):
    while True:
        try:
            value = Decimal(get_input(prompt))
            if value < 0:
                raise InvalidOperation
            return value
        except (InvalidOperation, ValueError):
            print(f"{C['error']}Enter a valid non-negative amount.")


def get_int(prompt, minimum=0):
    while True:
        try:
            value = int(get_input(prompt))
            if value < minimum:
                raise ValueError
            return value
        except ValueError:
            print(f"{C['error']}Enter a whole number (minimum {minimum}).")


def login():
    print(f"\n{C['title']}LOGIN")
    identity = get_input("Username or Email")
    password = get_input("Password", hidden=True)
    users = fetch_data(
        "SELECT * FROM users WHERE (username=%s OR email=%s) AND password=%s",
        (identity, identity, password),
    )
    if users:
        print(f"{C['success']}Login successful. Welcome, {users[0]['name']}!")
        return users[0]
    print(f"{C['error']}Invalid credentials.")
    return None


def register():
    print(f"\n{C['title']}NEW CUSTOMER REGISTRATION")
    name = get_input("Full name")
    username = get_input("Username")
    password = get_input("Password", hidden=True)
    phone = get_input("Phone number")
    email = get_input("Email")
    if not all((name, username, password)):
        print(f"{C['error']}Name, username and password are required.")
        return
    if fetch_data(
        "SELECT user_id FROM users WHERE username=%s OR email=%s",
        (username, email),
    ):
        print(f"{C['error']}Username or email is already registered.")
        return
    if execute_query(
        """
        INSERT INTO users (name,username,password,role,phone,email)
        VALUES (%s,%s,%s,'Customer',%s,%s)
        """,
        (name, username, password, phone, email),
    ):
        print(f"{C['success']}Registration successful. Please log in.")


def main():
    while True:
        print(f"\n{C['title']}{'=' * 48}")
        print("       VEHICLE SERVICE & GARAGE MANAGEMENT")
        print("=" * 48)
        print("1. Login\n2. Register (New Customer)\n0. Exit")
        choice = get_input("Select option")
        if choice == "1":
            user = login()
            if user:
                {"Admin": admin_dashboard,
                 "Mechanic": mechanic_dashboard,
                 "Customer": customer_dashboard}[user["role"]](user)
        elif choice == "2":
            register()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print(f"{C['error']}Invalid choice.")
            pause()


def admin_dashboard(user):
    while True:
        print(f"\n{C['title']}ADMIN DASHBOARD — {user['name']}")
        print("1. Manage Users\n2. Manage Inventory\n3. Manage Bookings")
        print("4. Reports\n5. Manage Services\n0. Logout")
        choice = get_input("Select option")
        actions = {
            "1": manage_users, "2": manage_inventory,
            "3": manage_bookings, "4": view_reports,
            "5": manage_services,
        }
        if choice == "0":
            return
        if choice in actions:
            actions[choice]()
        else:
            print(f"{C['error']}Invalid choice.")


def customer_dashboard(user):
    uid = user["user_id"]
    while True:
        print(f"\n{C['title']}CUSTOMER DASHBOARD — {user['name']}")
        print("1. My Vehicles\n2. Book Service\n3. Booking History")
        print("4. Pay Invoice\n5. Edit Profile\n0. Logout")
        choice = get_input("Select option")
        actions = {
            "1": lambda: manage_vehicles(uid),
            "2": lambda: book_service(uid),
            "3": lambda: view_history(uid),
            "4": lambda: pay_invoice(uid),
            "5": lambda: edit_profile(uid),
        }
        if choice == "0":
            return
        if choice in actions:
            actions[choice]()
        else:
            print(f"{C['error']}Invalid choice.")


def mechanic_dashboard(user):
    mid = user["user_id"]
    while True:
        print(f"\n{C['title']}MECHANIC DASHBOARD — {user['name']}")
        print("1. View Jobs\n2. Update Job Status\n0. Logout")
        choice = get_input("Select option")
        if choice == "1":
            view_jobs(mid)
        elif choice == "2":
            update_job_status(mid)
        elif choice == "0":
            return
        else:
            print(f"{C['error']}Invalid choice.")


# ----------------------------- ADMIN FUNCTIONS -----------------------------

def manage_users():
    while True:
        print(f"\n{C['title']}MANAGE USERS")
        print("1. List/Search Users\n2. Add User\n3. Edit User")
        print("4. Delete User\n0. Back")
        choice = get_input("Select")
        if choice == "1":
            uid = get_input("User ID (blank for all)")
            rows = fetch_data(
                "SELECT user_id,name,username,role,phone,email,Register_at "
                "FROM users WHERE user_id=%s" if uid else
                "SELECT user_id,name,username,role,phone,email,Register_at FROM users",
                (uid,) if uid else None,
            )
            show_table(rows)
            pause()
        elif choice == "2":
            name = get_input("Name")
            username = get_input("Username")
            password = get_input("Password", hidden=True)
            role = get_input("Role (Admin/Mechanic/Customer)")
            if role not in ("Admin", "Mechanic", "Customer"):
                print(f"{C['error']}Invalid role.")
                continue
            phone, email = get_input("Phone"), get_input("Email")
            execute_query(
                "INSERT INTO users (name,username,password,role,phone,email) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (name, username, password, role, phone, email),
            )
        elif choice == "3":
            uid = get_input("User ID")
            rows = fetch_data("SELECT * FROM users WHERE user_id=%s", (uid,))
            if not rows:
                print("User not found.")
                continue
            old = rows[0]
            name = get_input("Name [Enter to keep]") or old["name"]
            username = get_input("Username [Enter to keep]") or old["username"]
            password = get_input("New password [Enter to keep]", hidden=True) or old["password"]
            role = get_input("Role [Enter to keep]") or old["role"]
            phone = get_input("Phone [Enter to keep]") or old["phone"]
            email = get_input("Email [Enter to keep]") or old["email"]
            if role not in ("Admin", "Mechanic", "Customer"):
                print("Invalid role.")
                continue
            execute_query(
                "UPDATE users SET name=%s,username=%s,password=%s,role=%s,"
                "phone=%s,email=%s WHERE user_id=%s",
                (name, username, password, role, phone, email, uid),
            )
        elif choice == "4":
            uid = get_input("User ID to delete")
            if uid == "1":
                print("The first/default admin account cannot be deleted here.")
                continue
            execute_query("DELETE FROM users WHERE user_id=%s", (uid,))
        elif choice == "0":
            return


def manage_inventory():
    while True:
        print(f"\n{C['title']}MANAGE INVENTORY")
        print("1. List/Search Inventory\n2. Add Item\n3. Update Stock\n0. Back")
        choice = get_input("Select")
        if choice == "1":
            term = get_input("Item name or ID (blank for all)")
            if term:
                rows = fetch_data(
                    "SELECT * FROM inventory WHERE name LIKE %s OR item_id=%s",
                    (f"%{term}%", term if term.isdigit() else -1),
                )
            else:
                rows = fetch_data("SELECT * FROM inventory")
            show_table(rows)
            pause()
        elif choice == "2":
            name = get_input("Item name")
            qty = get_int("Quantity")
            price = get_money("Price")
            execute_query(
                "INSERT INTO inventory (name,quantity,price) VALUES (%s,%s,%s)",
                (name, qty, price),
            )
        elif choice == "3":
            iid = get_input("Item ID")
            if not fetch_data("SELECT item_id FROM inventory WHERE item_id=%s", (iid,)):
                print("Item not found.")
                continue
            qty = get_int("New quantity")
            execute_query("UPDATE inventory SET quantity=%s WHERE item_id=%s", (qty, iid))
        elif choice == "0":
            return


def manage_bookings():
    statuses = ("Pending", "In Progress", "Completed", "Cancelled")
    while True:
        print(f"\n{C['title']}MANAGE BOOKINGS")
        print("1. View All Bookings\n2. Assign Mechanic\n3. Update Status")
        print("4. Cancel Booking\n0. Back")
        choice = get_input("Select")
        if choice == "1":
            status = get_input("Filter status (blank for all)")
            if status and status not in statuses:
                print("Invalid status.")
                continue
            sql = """
                SELECT b.booking_id,b.date,u.name AS customer,v.model,v.plate_no,
                       s.name AS service,m.name AS mechanic,b.status
                FROM bookings b
                JOIN users u ON b.user_id=u.user_id
                JOIN vehicles v ON b.vehicle_id=v.vehicle_id
                JOIN services s ON b.service_id=s.service_id
                LEFT JOIN users m ON b.mechanic_id=m.user_id
            """
            if status:
                sql += " WHERE b.status=%s"
            show_table(fetch_data(sql, (status,) if status else None))
            pause()
        elif choice == "2":
            bid = get_input("Booking ID")
            if not fetch_data("SELECT booking_id FROM bookings WHERE booking_id=%s", (bid,)):
                print("Booking not found.")
                continue
            mid = get_input("Mechanic user ID")
            if not fetch_data(
                "SELECT user_id FROM users WHERE user_id=%s AND role='Mechanic'",
                (mid,),
            ):
                print("That user is not a mechanic.")
                continue
            execute_query("UPDATE bookings SET mechanic_id=%s WHERE booking_id=%s", (mid, bid))
            print(f"{C['success']}Mechanic assigned.")
        elif choice == "3":
            bid = get_input("Booking ID")
            status = get_input("New status")
            if status not in statuses:
                print("Invalid status.")
                continue
            execute_query("UPDATE bookings SET status=%s WHERE booking_id=%s", (status, bid))
        elif choice == "4":
            bid = get_input("Booking ID")
            execute_query(
                "UPDATE bookings SET status='Cancelled' "
                "WHERE booking_id=%s AND status='Pending'",
                (bid,),
            )
        elif choice == "0":
            return


def view_reports():
    print(f"\n{C['title']}REPORTS")
    paid = fetch_data("SELECT COALESCE(SUM(amount),0) AS total FROM invoices WHERE status='Paid'")
    print(f"Total revenue: ₹{paid[0]['total'] if paid else 0}")
    booking_stats = fetch_data(
        "SELECT status,COUNT(*) AS count FROM bookings GROUP BY status"
    )
    print("\nBooking status:")
    show_table(booking_stats)
    if get_input("Generate graph? (y/n)").lower() != "y":
        return
    print("1. Monthly Revenue\n2. Booking Status\n3. Payment Status")
    choice = get_input("Choose graph")
    try:
        if choice == "1":
            df = pd.read_sql(
                """
                SELECT DATE_FORMAT(Paid_Time,'%Y-%m') AS month,
                       SUM(amount) AS revenue
                FROM invoices WHERE status='Paid' AND Paid_Time IS NOT NULL
                GROUP BY month ORDER BY month
                """,
                get_engine(),
            )
            if df.empty:
                print("No revenue data.")
                return
            plt.figure(figsize=(10, 5))
            plt.plot(df["month"], df["revenue"], marker="o")
            plt.title("Monthly Revenue")
            plt.xlabel("Month")
            plt.ylabel("Revenue (₹)")
            plt.grid(True)
            plt.tight_layout()
            plt.show()
        elif choice in ("2", "3"):
            table = "bookings" if choice == "2" else "invoices"
            title = "Booking Status Distribution" if choice == "2" else "Payment Status Distribution"
            df = pd.read_sql(
                f"SELECT status,COUNT(*) AS count FROM {table} GROUP BY status",
                get_engine(),
            )
            if df.empty:
                print("No data for graph.")
                return
            plt.figure(figsize=(7, 7))
            plt.pie(df["count"], labels=df["status"], autopct="%1.1f%%", startangle=140)
            plt.title(title)
            plt.tight_layout()
            plt.show()
        else:
            print("Invalid graph choice.")
    except Exception as exc:
        print(f"{C['error']}Could not generate graph: {exc}")
    finally:
        pause()


def manage_services():
    while True:
        print(f"\n{C['title']}MANAGE SERVICES")
        print("1. List Services\n2. Add Service\n3. Edit Service\n4. Delete Service\n0. Back")
        choice = get_input("Select")
        if choice == "1":
            show_table(fetch_data("SELECT * FROM services"))
            pause()
        elif choice == "2":
            name = get_input("Service name")
            price = get_money("Price")
            description = get_input("Description")
            execute_query(
                "INSERT INTO services (name,price,description) VALUES (%s,%s,%s)",
                (name, price, description),
            )
        elif choice == "3":
            sid = get_input("Service ID")
            rows = fetch_data("SELECT * FROM services WHERE service_id=%s", (sid,))
            if not rows:
                print("Service not found.")
                continue
            old = rows[0]
            name = get_input("New name [Enter to keep]") or old["name"]
            raw_price = get_input("New price [Enter to keep]")
            price = get_money("New price") if raw_price else old["price"]
            desc = get_input("New description [Enter to keep]") or old["description"]
            execute_query(
                "UPDATE services SET name=%s,price=%s,description=%s WHERE service_id=%s",
                (name, price, desc, sid),
            )
        elif choice == "4":
            sid = get_input("Service ID")
            if not fetch_data("SELECT service_id FROM services WHERE service_id=%s", (sid,)):
                print("Service not found.")
                continue
            execute_query("DELETE FROM services WHERE service_id=%s", (sid,))
        elif choice == "0":
            return


# ---------------------------- CUSTOMER FUNCTIONS ---------------------------

def manage_vehicles(uid):
    while True:
        print(f"\n{C['title']}MY VEHICLES")
        show_table(fetch_data("SELECT * FROM vehicles WHERE user_id=%s", (uid,)))
        print("1. Add Vehicle\n2. Edit Vehicle\n3. Delete Vehicle\n0. Back")
        choice = get_input("Select")
        if choice == "1":
            plate = get_input("Vehicle registration number")
            model = get_input("Model")
            brand = get_input("Brand/manufacturer")
            execute_query(
                "INSERT INTO vehicles (user_id,plate_no,model,brand) VALUES (%s,%s,%s,%s)",
                (uid, plate, model, brand),
            )
        elif choice == "2":
            vid = get_input("Vehicle ID")
            rows = fetch_data(
                "SELECT * FROM vehicles WHERE vehicle_id=%s AND user_id=%s",
                (vid, uid),
            )
            if not rows:
                print("Vehicle not found or it does not belong to you.")
                continue
            old = rows[0]
            plate = get_input("Registration number [Enter to keep]") or old["plate_no"]
            model = get_input("Model [Enter to keep]") or old["model"]
            brand = get_input("Brand [Enter to keep]") or old["brand"]
            execute_query(
                "UPDATE vehicles SET plate_no=%s,model=%s,brand=%s "
                "WHERE vehicle_id=%s AND user_id=%s",
                (plate, model, brand, vid, uid),
            )
        elif choice == "3":
            vid = get_input("Vehicle ID")
            execute_query(
                "DELETE FROM vehicles WHERE vehicle_id=%s AND user_id=%s",
                (vid, uid),
            )
        elif choice == "0":
            return


def book_service(uid):
    vehicles = fetch_data("SELECT * FROM vehicles WHERE user_id=%s", (uid,))
    if not vehicles:
        print("Add a vehicle before booking a service.")
        return
    print("Your vehicles:")
    show_table(vehicles)
    vid = get_input("Vehicle ID")
    vehicle = next((v for v in vehicles if str(v["vehicle_id"]) == vid), None)
    if vehicle is None:
        print("Invalid vehicle ID.")
        return
    services = fetch_data("SELECT * FROM services")
    if not services:
        print("No services are currently available.")
        return
    print("Available services:")
    show_table(services)
    sid = get_input("Service ID")
    service = next((s for s in services if str(s["service_id"]) == sid), None)
    if service is None:
        print("Invalid service ID.")
        return

    conn = get_db_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO bookings (user_id,vehicle_id,service_id,status) "
            "VALUES (%s,%s,%s,'Pending')",
            (uid, vid, sid),
        )
        booking_id = cur.lastrowid
        cur.execute(
            "INSERT INTO invoices (booking_id,amount,status) VALUES (%s,%s,'Unpaid')",
            (booking_id, service["price"]),
        )
        conn.commit()
        print(f"{C['success']}Service booked. Invoice generated.")
    except Error as exc:
        conn.rollback()
        print(f"{C['error']}Booking failed: {exc}")
    finally:
        conn.close()


def view_history(uid):
    rows = fetch_data(
        """
        SELECT b.booking_id,b.date,b.status,s.name AS service,
               v.plate_no AS vehicle,i.status AS payment
        FROM bookings b
        JOIN services s ON b.service_id=s.service_id
        JOIN vehicles v ON b.vehicle_id=v.vehicle_id
        LEFT JOIN invoices i ON b.booking_id=i.booking_id
        WHERE b.user_id=%s ORDER BY b.date DESC
        """,
        (uid,),
    )
    show_table(rows)
    if rows and get_input("Cancel a pending booking? (y/n)").lower() == "y":
        bid = get_input("Booking ID")
        ok = execute_query(
            "UPDATE bookings SET status='Cancelled' "
            "WHERE booking_id=%s AND user_id=%s AND status='Pending'",
            (bid, uid),
        )
        if ok:
            print("If the booking was pending, it has been cancelled.")
    pause()


def pay_invoice(uid):
    invoices = fetch_data(
        """
        SELECT i.invoice_id,i.amount,b.status AS job_status
        FROM invoices i JOIN bookings b ON i.booking_id=b.booking_id
        WHERE b.user_id=%s AND i.status='Unpaid'
          AND b.status IN ('In Progress','Completed')
        """,
        (uid,),
    )
    show_table(invoices)
    if invoices:
        iid = get_input("Invoice ID to pay")
        valid = next((x for x in invoices if str(x["invoice_id"]) == iid), None)
        if not valid:
            print("Invalid invoice ID.")
        else:
            execute_query(
                "UPDATE invoices SET status='Paid',Paid_Time=CURRENT_TIMESTAMP "
                "WHERE invoice_id=%s AND status='Unpaid'",
                (iid,),
            )
            print(f"{C['success']}Payment status updated to Paid.")
    pause()


def edit_profile(uid):
    rows = fetch_data(
        "SELECT name,phone,email,password FROM users WHERE user_id=%s",
        (uid,),
    )
    if not rows:
        print("User not found.")
        return
    old = rows[0]
    print(pd.DataFrame([{"name": old["name"], "phone": old["phone"], "email": old["email"]}]).T)
    name = get_input("New name [Enter to keep]") or old["name"]
    phone = get_input("New phone [Enter to keep]") or old["phone"]
    email = get_input("New email [Enter to keep]") or old["email"]
    password = get_input("New password [Enter to keep]", hidden=True)
    if password:
        confirm = get_input("Confirm new password", hidden=True)
        if password != confirm:
            print(f"{C['error']}Passwords do not match.")
            return
    else:
        password = old["password"]
    execute_query(
        "UPDATE users SET name=%s,phone=%s,email=%s,password=%s WHERE user_id=%s",
        (name, phone, email, password, uid),
    )
    print(f"{C['success']}Profile updated.")


# ---------------------------- MECHANIC FUNCTIONS ----------------------------

def view_jobs(mid):
    print(f"\n{C['title']}MY ASSIGNED JOBS")
    status = get_input("Filter by status (Pending/In Progress/Completed/All) [All]")
    if status and status.lower() != "all" and status not in (
        "Pending", "In Progress", "Completed", "Cancelled"
    ):
        print("Invalid status.")
        return
    query = """
        SELECT b.booking_id,b.date,b.status,v.model,v.plate_no,s.name AS service
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id=v.vehicle_id
        JOIN services s ON b.service_id=s.service_id
        WHERE b.mechanic_id=%s
    """
    params = [mid]
    if status and status.lower() != "all":
        query += " AND b.status=%s"
        params.append(status)
    show_table(fetch_data(query, tuple(params)))
    pause()


def update_job_status(mid):
    bid = get_input("Booking ID to update")
    if not fetch_data(
        "SELECT booking_id FROM bookings WHERE booking_id=%s AND mechanic_id=%s",
        (bid, mid),
    ):
        print(f"{C['error']}This job is not assigned to you.")
        return
    status = get_input("New status (In Progress/Completed/Cancelled)")
    if status not in ("In Progress", "Completed", "Cancelled"):
        print("Invalid status.")
        return
    execute_query(
        "UPDATE bookings SET status=%s WHERE booking_id=%s AND mechanic_id=%s",
        (status, bid, mid),
    )
    print(f"{C['success']}Job status updated.")


if __name__ == "__main__":
    try:
        create_tables()
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped.")
    except Exception as exc:
        print(f"{C['error']}Application error: {exc}")
