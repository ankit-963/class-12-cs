import mysql.connector
import random
from decimal import Decimal, InvalidOperation


#DATABASE SETTINGS

HOST = "localhost"
USER = "root"
PASSWORD = "1234"
DATABASE = "bank"


#DATABASE CONNECTION

def connect(database=DATABASE):
    return mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=database
    )


#CREATE DATABASE AND TABLES

def setup_database():
    con = connect(None)
    cur = con.cursor()

    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    cur.close()
    con.close()

    con = connect()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            account_no VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            dob VARCHAR(20),
            mobile VARCHAR(15),
            address VARCHAR(200),
            account_type VARCHAR(20),
            pin VARCHAR(10) NOT NULL,
            balance DECIMAL(12,2) DEFAULT 0.00
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
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

    cur.execute("SHOW COLUMNS FROM transactions LIKE 'transaction_date'")
    if cur.fetchone() is None:
        cur.execute("""
            ALTER TABLE transactions
            ADD COLUMN transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP
        """)

    con.commit()
    cur.close()
    con.close()


#COMMON FUNCTIONS

def get_amount():
    while True:
        try:
            amount = Decimal(input("Enter amount: "))

            if not amount.is_finite() or amount <= 0:
                print("Amount must be greater than zero.")
            elif amount.as_tuple().exponent < -2:
                print("Enter a maximum of two decimal places.")
            elif amount > Decimal("9999999999.99"):
                print("Amount is too large.")
            else:
                return amount

        except InvalidOperation:
            print("Please enter a valid amount.")


def get_pin():
    while True:
        pin = input("Enter a 4-digit PIN: ").strip()

        if len(pin) == 4 and pin.isdigit():
            return pin

        print("PIN must contain exactly 4 digits.")



def make_account_number():
    con = connect()
    cur = con.cursor()

    while True:
        number = str(random.randint(1000, 9999))

        cur.execute(
            "SELECT account_no FROM customers WHERE account_no = %s",
            (number,)
        )

        if cur.fetchone() is None:
            cur.close()
            con.close()
            return number


def add_transaction(cur, account_no, kind, amount, description):
    cur.execute("""
        INSERT INTO transactions
        (account_no, transaction_type, amount, description)
        VALUES (%s, %s, %s, %s)
    """, (account_no, kind, amount, description))


# CREATE ACCOUNT

def create_account():
    print("\n--- CREATE NEW ACCOUNT ---")

    name = input("Enter name: ").strip()

    if not name:
        print("Name cannot be empty.")
        return

    dob = input("Enter date of birth (DD-MM-YYYY): ").strip()
    mobile = input("Enter mobile number: ").strip()
    address = input("Enter address: ").strip()

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

    pin = get_pin()

    print("Enter initial deposit.")
    amount = get_amount()

    con = connect()
    cur = con.cursor()

    try:
        account_no = make_account_number()

        cur.execute("""
            INSERT INTO customers
            (account_no, name, dob, mobile, address,
             account_type, pin, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            account_no, name, dob, mobile, address,
            account_type, pin, amount
        ))

        add_transaction(
            cur, account_no, "Deposit",
            amount, "Initial deposit"
        )

        con.commit()

        print("\nAccount created successfully!")
        print("Account Number:", account_no)
        print("Customer Name:", name)
        print("Account Type:", account_type)
        print("Balance: Rs.", amount)
        print("Keep your PIN secret.")

    except mysql.connector.Error as e:
        con.rollback()
        print("Error:", e)

    finally:
        cur.close()
        con.close()


# CUSTOMER LOGIN

def login():
    print("\n--- CUSTOMER LOGIN ---")

    account_no = input("Enter account number: ").strip()
    pin = input("Enter PIN: ").strip()

    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT name FROM customers
        WHERE account_no = %s AND pin = %s
    """, (account_no, pin))

    result = cur.fetchone()

    cur.close()
    con.close()

    if result:
        print("Welcome,", result[0])
        return account_no

    print("Invalid account number or PIN.")
    return None


# ACCOUNT DETAILS

def account_details(account_no):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT account_no, name, dob, mobile,
               address, account_type, balance
        FROM customers
        WHERE account_no = %s
    """, (account_no,))

    data = cur.fetchone()

    if data:
        print("\n--- ACCOUNT DETAILS ---")
        print("Account Number:", data[0])
        print("Name:", data[1])
        print("Date of Birth:", data[2])
        print("Mobile:", data[3])
        print("Address:", data[4])
        print("Account Type:", data[5])
        print("Balance: Rs.", data[6])
    else:
        print("Account not found.")

    cur.close()
    con.close()


# CHECK BALANCE

def check_balance(account_no):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT balance FROM customers
        WHERE account_no = %s
    """, (account_no,))

    result = cur.fetchone()

    if result:
        print("Current Balance: Rs.", result[0])
    else:
        print("Account not found.")

    cur.close()
    con.close()


# DEPOSIT MONEY

def deposit_money(account_no):
    print("\n--- DEPOSIT MONEY ---")
    amount = get_amount()

    con = connect()
    cur = con.cursor()

    try:
        cur.execute("""
            UPDATE customers
            SET balance = balance + %s
            WHERE account_no = %s
        """, (amount, account_no))

        if cur.rowcount == 0:
            print("Account not found.")
            con.rollback()
            return

        add_transaction(
            cur, account_no, "Deposit",
            amount, "Money deposited"
        )

        con.commit()
        print("Money deposited successfully.")
        check_balance(account_no)

    except mysql.connector.Error as e:
        con.rollback()
        print("Error:", e)

    finally:
        cur.close()
        con.close()


# WITHDRAW MONEY

def withdraw_money(account_no):
    print("\n--- WITHDRAW MONEY ---")
    amount = get_amount()

    con = connect()
    cur = con.cursor()

    try:
        cur.execute("""
            SELECT balance FROM customers
            WHERE account_no = %s
            FOR UPDATE
        """, (account_no,))

        result = cur.fetchone()

        if result is None:
            print("Account not found.")
            return

        balance = result[0]

        if amount > balance:
            print("Insufficient balance.")
            return

        cur.execute("""
            UPDATE customers
            SET balance = balance - %s
            WHERE account_no = %s
        """, (amount, account_no))

        add_transaction(
            cur, account_no, "Withdrawal",
            amount, "Money withdrawn"
        )

        con.commit()
        print("Money withdrawn successfully.")
        check_balance(account_no)

    except mysql.connector.Error as e:
        con.rollback()
        print("Error:", e)

    finally:
        cur.close()
        con.close()


# TRANSFER MONEY

def transfer_money(sender):
    print("\n--- MONEY TRANSFER ---")

    receiver = input("Enter receiver account number: ").strip()

    if receiver == sender:
        print("You cannot transfer to your own account.")
        return

    amount = get_amount()

    con = connect()
    cur = con.cursor()

    try:
        # Lock both accounts in a consistent order.
        accounts = sorted([sender, receiver])

        for number in accounts:
            cur.execute("""
                SELECT balance FROM customers
                WHERE account_no = %s
                FOR UPDATE
            """, (number,))

            result = cur.fetchone()

            if result is None:
                print("Account not found:", number)
                return

            if number == sender:
                sender_balance = result[0]

        if amount > sender_balance:
            print("Insufficient balance.")
            return

        cur.execute("""
            UPDATE customers
            SET balance = balance - %s
            WHERE account_no = %s
        """, (amount, sender))

        cur.execute("""
            UPDATE customers
            SET balance = balance + %s
            WHERE account_no = %s
        """, (amount, receiver))

        add_transaction(
            cur, sender, "Transfer",
            amount, "Sent to " + receiver
        )

        add_transaction(
            cur, receiver, "Received",
            amount, "Received from " + sender
        )

        con.commit()
        print("Transfer successful.")
        check_balance(sender)

    except mysql.connector.Error as e:
        con.rollback()
        print("Transfer failed:", e)

    finally:
        cur.close()
        con.close()


# TRANSACTION HISTORY

def transaction_history(account_no):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT id, transaction_type, amount,
               description, transaction_date
        FROM transactions
        WHERE account_no = %s
        ORDER BY id DESC
    """, (account_no,))

    records = cur.fetchall()

    print("\n--- TRANSACTION HISTORY ---")

    if not records:
        print("No transactions found.")

    for record in records:
        print("\nTransaction ID:", record[0])
        print("Type:", record[1])
        print("Amount: Rs.", record[2])
        print("Description:", record[3])
        print("Date:", record[4])

    cur.close()
    con.close()


# UPDATE ACCOUNT

def update_account(account_no):
    print("\n--- UPDATE ACCOUNT ---")
    print("1. Update mobile number")
    print("2. Update address")
    print("3. Change PIN")

    choice = input("Enter choice: ")

    con = connect()
    cur = con.cursor()

    try:
        if choice == "1":
            value = input("Enter new mobile number: ").strip()
            field = "mobile"

        elif choice == "2":
            value = input("Enter new address: ").strip()
            field = "address"

        elif choice == "3":
            cur.execute("""
                SELECT pin FROM customers
                WHERE account_no = %s
            """, (account_no,))

            result = cur.fetchone()
            old_pin = input("Enter current PIN: ").strip()

            if result is None or result[0] != old_pin:
                print("Incorrect PIN.")
                return

            value = get_pin()
            field = "pin"

        else:
            print("Invalid choice.")
            return

        # Only fixed column names from the choices above are used.
        cur.execute(
            f"UPDATE customers SET {field} = %s WHERE account_no = %s",
            (value, account_no)
        )

        con.commit()
        print("Account updated successfully.")

    except mysql.connector.Error as e:
        con.rollback()
        print("Error:", e)

    finally:
        cur.close()
        con.close()


# CLOSE ACCOUNT

def close_account(account_no):
    con = connect()
    cur = con.cursor()

    try:
        cur.execute("""
            SELECT balance FROM customers
            WHERE account_no = %s
            FOR UPDATE
        """, (account_no,))

        result = cur.fetchone()

        if result is None:
            print("Account not found.")
            return False

        if result[0] != Decimal("0.00"):
            print("Withdraw or transfer the remaining balance first.")
            return False

        confirm = input(
            "Are you sure you want to close your account? (Y/N): "
        ).strip().upper()

        if confirm == "Y":
            cur.execute("""
                DELETE FROM customers
                WHERE account_no = %s
            """, (account_no,))

            con.commit()
            print("Account closed successfully.")
            return True

        print("Account closure cancelled.")
        return False

    except mysql.connector.Error as e:
        con.rollback()
        print("Error:", e)
        return False

    finally:
        cur.close()
        con.close()


# CUSTOMER MENU

def customer_menu(account_no):
    while True:
        print("\n========== CUSTOMER MENU ==========")
        print("1. Account Details")
        print("2. Check Balance")
        print("3. Deposit Money")
        print("4. Withdraw Money")
        print("5. Transfer Money")
        print("6. Transaction History")
        print("7. Update Account")
        print("8. Close Account")
        print("9. Logout")

        choice = input("Enter choice: ")

        try:
            if choice == "1":
                account_details(account_no)

            elif choice == "2":
                check_balance(account_no)

            elif choice == "3":
                deposit_money(account_no)

            elif choice == "4":
                withdraw_money(account_no)

            elif choice == "5":
                transfer_money(account_no)

            elif choice == "6":
                transaction_history(account_no)

            elif choice == "7":
                update_account(account_no)

            elif choice == "8":
                if close_account(account_no):
                    return

            elif choice == "9":
                print("Logged out successfully.")
                return

            else:
                print("Invalid choice.")

        except mysql.connector.Error as e:
            print("Database error:", e)

        input("\nPress Enter to continue...")


# MAIN PROGRAM

def main():
    try:
        setup_database()
        print("Database is ready.")

        while True:
            print("\n====== BANK MANAGEMENT SYSTEM ======")
            print("1. Create Account")
            print("2. Customer Login")
            print("3. Exit")

            choice = input("Enter choice: ")

            try:
                if choice == "1":
                    create_account()

                elif choice == "2":
                    account_no = login()

                    if account_no:
                        customer_menu(account_no)

                elif choice == "3":
                    print("Thank you for using our bank system.")
                    break

                else:
                    print("Invalid choice.")

            except mysql.connector.Error as e:
                print("Database error:", e)

    except mysql.connector.Error as e:
        print("Unable to connect to MySQL:", e)
        print("Check your MySQL username and password.")


if __name__ == "__main__":
    main()