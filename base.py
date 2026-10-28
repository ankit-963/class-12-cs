import mysql.connector as  sql
from mysql.connector import Error
from datetime import datetime
import random
import sys


# database declaration

# Database Management Banking


database_name = "bank_management"

def get_connection(database=None):
    try:
        config = {
            "host": "localhost",
            "user": "root",
            "password": "1234"
        }

        if database:
            config["database"] = database

        return sql.connect(**config)

    except Error as e:
        print("Database connection error:", e)
        return None


# ============================================================
# CREATE DATABASE AND TABLES
# ============================================================

def setup_database():
    connection = get_connection()

    if connection is None:
        return False

    try:
        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
        )

        cursor.close()
        connection.close()

        connection = get_connection(DATABASE_NAME)

        if connection is None:
            return False

        cursor = connection.cursor()

        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                account_no VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                dob VARCHAR(20),
                mobile VARCHAR(15),
                address VARCHAR(200),
                account_type VARCHAR(20),
                pin VARCHAR(10) NOT NULL,
                balance DECIMAL(12,2) DEFAULT 0.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                account_no VARCHAR(20),
                transaction_type VARCHAR(30),
                amount DECIMAL(12,2),
                description VARCHAR(200),
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_no)
                REFERENCES customers(account_no)
                ON DELETE CASCADE
            )
        """)

        connection.commit()

        cursor.close()
        connection.close()

        return True

    except Error as e:
        print("\nError setting up database:", e)
        return False


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def generate_account_number():
    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return None

    cursor = connection.cursor()

    while True:
        account_no = str(random.randint(1000000000, 9999999999))

        cursor.execute(
            "SELECT account_no FROM customers WHERE account_no = %s",
            (account_no,)
        )

        if cursor.fetchone() is None:
            cursor.close()
            connection.close()
            return account_no


def pause():
    input("\nPress Enter to continue...")


def line():
    print("-" * 70)


def get_positive_amount():
    while True:
        try:
            amount = float(input("Enter amount: "))

            if amount <= 0:
                print("Amount must be greater than 0.")
            else:
                return amount

        except ValueError:
            print("Please enter a valid number.")


# ============================================================
# CREATE ACCOUNT
# ============================================================

def create_account():
    print("\n")
    line()
    print("                 CREATE NEW ACCOUNT")
    line()

    name = input("Enter customer name: ").strip()

    if name == "":
        print("Name cannot be empty.")
        return

    dob = input("Enter date of birth (DD-MM-YYYY): ").strip()
    mobile = input("Enter mobile number: ").strip()
    address = input("Enter address: ").strip()

    print("\nAccount Types:")
    print("1. Savings")
    print("2. Current")

    choice = input("Choose account type: ")

    if choice == "1":
        account_type = "Savings"
    elif choice == "2":
        account_type = "Current"
    else:
        print("Invalid account type.")
        return

    while True:
        pin = input("Create 4-digit PIN: ")

        if len(pin) == 4 and pin.isdigit():
            break

        print("PIN must contain exactly 4 digits.")

    print("\nEnter initial deposit.")
    initial_deposit = get_positive_amount()

    account_no = generate_account_number()

    if account_no is None:
        print("Unable to generate account number.")
        return

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO customers
            (account_no, name, dob, mobile, address,
             account_type, pin, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            account_no,
            name,
            dob,
            mobile,
            address,
            account_type,
            pin,
            initial_deposit
        )

        cursor.execute(query, values)

        # Record initial deposit
        cursor.execute("""
            INSERT INTO transactions
            (account_no, transaction_type, amount, description)
            VALUES (%s, %s, %s, %s)
        """, (
            account_no,
            "Deposit",
            initial_deposit,
            "Initial account deposit"
        ))

        connection.commit()

        print("\nAccount created successfully!")
        line()
        print("Account Number :", account_no)
        print("Customer Name  :", name)
        print("Account Type   :", account_type)
        print("Initial Balance:", f"₹{initial_deposit:.2f}")
        print("PIN            :", pin)
        line()

    except Error as e:
        connection.rollback()
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# LOGIN
# ============================================================

def login():
    print("\n")
    line()
    print("                    CUSTOMER LOGIN")
    line()

    account_no = input("Enter account number: ").strip()
    pin = input("Enter PIN: ").strip()

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT account_no, name
            FROM customers
            WHERE account_no = %s AND pin = %s
        """, (account_no, pin))

        result = cursor.fetchone()

        if result:
            print("\nLogin successful!")
            print("Welcome,", result[1])
            return result[0]

        print("\nInvalid account number or PIN.")
        return None

    except Error as e:
        print("Error:", e)
        return None

    finally:
        cursor.close()
        connection.close()


# ============================================================
# ACCOUNT DETAILS
# ============================================================

def account_details(account_no):
    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT account_no, name, dob, mobile,
                   address, account_type, balance, created_at
            FROM customers
            WHERE account_no = %s
        """, (account_no,))

        data = cursor.fetchone()

        if data:
            print("\n")
            line()
            print("                    ACCOUNT DETAILS")
            line()

            print("Account Number :", data[0])
            print("Name           :", data[1])
            print("Date of Birth  :", data[2])
            print("Mobile         :", data[3])
            print("Address        :", data[4])
            print("Account Type   :", data[5])
            print("Balance        :", f"₹{float(data[6]):.2f}")
            print("Created On     :", data[7])

            line()

        else:
            print("Account not found.")

    except Error as e:
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# CHECK BALANCE
# ============================================================

def check_balance(account_no):
    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name, balance
            FROM customers
            WHERE account_no = %s
        """, (account_no,))

        result = cursor.fetchone()

        if result:
            print("\nCustomer Name:", result[0])
            print("Current Balance:", f"₹{float(result[1]):.2f}")

        else:
            print("Account not found.")

    except Error as e:
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# DEPOSIT
# ============================================================

def deposit_money(account_no):
    print("\n")
    line()
    print("                      DEPOSIT MONEY")
    line()

    amount = get_positive_amount()

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE customers
            SET balance = balance + %s
            WHERE account_no = %s
        """, (amount, account_no))

        cursor.execute("""
            INSERT INTO transactions
            (account_no, transaction_type, amount, description)
            VALUES (%s, %s, %s, %s)
        """, (
            account_no,
            "Deposit",
            amount,
            "Cash deposited"
        ))

        connection.commit()

        print("\n₹{:.2f} deposited successfully.".format(amount))

        cursor.execute("""
            SELECT balance
            FROM customers
            WHERE account_no = %s
        """, (account_no,))

        new_balance = cursor.fetchone()[0]

        print("New Balance:", f"₹{float(new_balance):.2f}")

    except Error as e:
        connection.rollback()
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# WITHDRAW MONEY
# ============================================================

def withdraw_money(account_no):
    print("\n")
    line()
    print("                    WITHDRAW MONEY")
    line()

    amount = get_positive_amount()

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT balance
            FROM customers
            WHERE account_no = %s
        """, (account_no,))

        result = cursor.fetchone()

        if result is None:
            print("Account not found.")
            return

        balance = float(result[0])

        if amount > balance:
            print("\nInsufficient balance.")
            print("Available Balance:", f"₹{balance:.2f}")
            return

        cursor.execute("""
            UPDATE customers
            SET balance = balance - %s
            WHERE account_no = %s
        """, (amount, account_no))

        cursor.execute("""
            INSERT INTO transactions
            (account_no, transaction_type, amount, description)
            VALUES (%s, %s, %s, %s)
        """, (
            account_no,
            "Withdrawal",
            amount,
            "Cash withdrawn"
        ))

        connection.commit()

        print("\n₹{:.2f} withdrawn successfully.".format(amount))

        new_balance = balance - amount
        print("New Balance:", f"₹{new_balance:.2f}")

    except Error as e:
        connection.rollback()
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# MONEY TRANSFER
# ============================================================

def transfer_money(sender_account):
    print("\n")
    line()
    print("                     MONEY TRANSFER")
    line()

    receiver_account = input(
        "Enter receiver account number: "
    ).strip()

    if receiver_account == sender_account:
        print("You cannot transfer money to the same account.")
        return

    amount = get_positive_amount()

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        # Check receiver
        cursor.execute("""
            SELECT name
            FROM customers
            WHERE account_no = %s
        """, (receiver_account,))

        receiver = cursor.fetchone()

        if receiver is None:
            print("Receiver account does not exist.")
            return

        # Check sender balance
        cursor.execute("""
            SELECT balance
            FROM customers
            WHERE account_no = %s
        """, (sender_account,))

        sender = cursor.fetchone()

        if sender is None:
            print("Sender account not found.")
            return

        sender_balance = float(sender[0])

        if amount > sender_balance:
            print("Insufficient balance.")
            print("Available Balance:",
                  f"₹{sender_balance:.2f}")
            return

        # Deduct from sender
        cursor.execute("""
            UPDATE customers
            SET balance = balance - %s
            WHERE account_no = %s
        """, (amount, sender_account))

        # Add to receiver
        cursor.execute("""
            UPDATE customers
            SET balance = balance + %s
            WHERE account_no = %s
        """, (amount, receiver_account))

        # Sender transaction
        cursor.execute("""
            INSERT INTO transactions
            (account_no, transaction_type, amount, description)
            VALUES (%s, %s, %s, %s)
        """, (
            sender_account,
            "Transfer",
            amount,
            "Transferred to " + receiver_account
        ))

        # Receiver transaction
        cursor.execute("""
            INSERT INTO transactions
            (account_no, transaction_type, amount, description)
            VALUES (%s, %s, %s, %s)
        """, (
            receiver_account,
            "Received",
            amount,
            "Received from " + sender_account
        ))

        connection.commit()

        print("\nTransfer successful!")
        print("Receiver:", receiver[0])
        print("Amount  :", f"₹{amount:.2f}")
        print("New Balance:",
              f"₹{sender_balance - amount:.2f}")

    except Error as e:
        connection.rollback()
        print("Transfer failed:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def transaction_history(account_no):
    print("\n")
    line()
    print("                  TRANSACTION HISTORY")
    line()

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT transaction_id,
                   transaction_type,
                   amount,
                   description,
                   transaction_date
            FROM transactions
            WHERE account_no = %s
            ORDER BY transaction_id DESC
        """, (account_no,))

        transactions = cursor.fetchall()

        if not transactions:
            print("No transactions found.")
            return

        print(
            f"{'ID':<6}"
            f"{'TYPE':<15}"
            f"{'AMOUNT':<15}"
            f"{'DESCRIPTION':<30}"
            f"{'DATE':<20}"
        )

        line()

        for transaction in transactions:
            transaction_id = transaction[0]
            transaction_type = transaction[1]
            amount = float(transaction[2])
            description = transaction[3]
            date = transaction[4]

            print(
                f"{transaction_id:<6}"
                f"{transaction_type:<15}"
                f"₹{amount:<14.2f}"
                f"{description[:28]:<30}"
                f"{str(date):<20}"
            )

    except Error as e:
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# UPDATE ACCOUNT
# ============================================================

def update_account(account_no):
    print("\n")
    line()
    print("                    UPDATE ACCOUNT")
    line()

    print("1. Update Mobile Number")
    print("2. Update Address")
    print("3. Change PIN")

    choice = input("\nEnter choice: ")

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return

    try:
        cursor = connection.cursor()

        if choice == "1":
            mobile = input("Enter new mobile number: ").strip()

            cursor.execute("""
                UPDATE customers
                SET mobile = %s
                WHERE account_no = %s
            """, (mobile, account_no))

            connection.commit()
            print("Mobile number updated successfully.")

        elif choice == "2":
            address = input("Enter new address: ").strip()

            cursor.execute("""
                UPDATE customers
                SET address = %s
                WHERE account_no = %s
            """, (address, account_no))

            connection.commit()
            print("Address updated successfully.")

        elif choice == "3":
            old_pin = input("Enter current PIN: ").strip()

            cursor.execute("""
                SELECT pin
                FROM customers
                WHERE account_no = %s
            """, (account_no,))

            result = cursor.fetchone()

            if result is None or result[0] != old_pin:
                print("Incorrect current PIN.")
                return

            while True:
                new_pin = input("Enter new 4-digit PIN: ")

                if len(new_pin) == 4 and new_pin.isdigit():
                    break

                print("PIN must contain exactly 4 digits.")

            cursor.execute("""
                UPDATE customers
                SET pin = %s
                WHERE account_no = %s
            """, (new_pin, account_no))

            connection.commit()

            print("PIN changed successfully.")

        else:
            print("Invalid choice.")

    except Error as e:
        connection.rollback()
        print("Error:", e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# CLOSE ACCOUNT
# ============================================================

def close_account(account_no):
    print("\n")
    line()
    print("                     CLOSE ACCOUNT")
    line()

    connection = get_connection(DATABASE_NAME)

    if connection is None:
        return False

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name, balance
            FROM customers
            WHERE account_no = %s
        """, (account_no,))

        result = cursor.fetchone()

        if result is None:
            print("Account not found.")
            return False

        name = result[0]
        balance = float(result[1])

        print("Account Holder:", name)
        print("Current Balance:", f"₹{balance:.2f}")

        if balance != 0:
            print("\nAccount cannot be closed.")
            print("Please withdraw/transfer the remaining balance first.")
            return False

        confirmation = input(
            "\nAre you sure you want to close this account? (Y/N): "
        ).upper()

        if confirmation == "Y":
            cursor.execute("""
                DELETE FROM customers
                WHERE account_no = %s
            """, (account_no,))

            connection.commit()

            print("\nAccount closed successfully.")
            return True

        print("Account closure cancelled.")
        return False

    except Error as e:
        connection.rollback()
        print("Error:", e)
        return False

    finally:
        cursor.close()
        connection.close()


# ============================================================
# CUSTOMER MENU
# ============================================================

def customer_menu(account_no):

    while True:
        print("\n")
        line()
        print("                    CUSTOMER MENU")
        line()

        print("1. Account Details")
        print("2. Check Balance")
        print("3. Deposit Money")
        print("4. Withdraw Money")
        print("5. Transfer Money")
        print("6. Transaction History")
        print("7. Update Account")
        print("8. Close Account")
        print("9. Logout")

        line()

        choice = input("Enter your choice: ")

        if choice == "1":
            account_details(account_no)
            pause()

        elif choice == "2":
            check_balance(account_no)
            pause()

        elif choice == "3":
            deposit_money(account_no)
            pause()

        elif choice == "4":
            withdraw_money(account_no)
            pause()

        elif choice == "5":
            transfer_money(account_no)
            pause()

        elif choice == "6":
            transaction_history(account_no)
            pause()

        elif choice == "7":
            update_account(account_no)
            pause()

        elif choice == "8":
            closed = close_account(account_no)

            if closed:
                return

            pause()

        elif choice == "9":
            print("\nLogged out successfully.")
            return

        else:
            print("\nInvalid choice. Please try again.")


# ============================================================
# MAIN MENU
# ============================================================

def main():

    print("\n")
    line()
    print("             WELCOME TO BANK MANAGEMENT SYSTEM")
    line()

    if not setup_database():
        print("\nUnable to start the application.")
        print("Please check your MySQL username and password.")
        sys.exit()

    while True:

        print("\n")
        line()
        print("                       MAIN MENU")
        line()

        print("1. Create New Account")
        print("2. Customer Login")
        print("3. Exit")

        line()

        choice = input("Enter your choice: ")

        if choice == "1":
            create_account()
            pause()

        elif choice == "2":
            account_no = login()

            if account_no:
                pause()
                customer_menu(account_no)

        elif choice == "3":
            print("\nThank you for using Bank Management System!")
            print("Goodbye!")
            break

        else:
            print("\nInvalid choice. Please try again.")


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()
  