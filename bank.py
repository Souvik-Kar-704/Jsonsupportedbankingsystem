import json
import random
import sys
import os

DB_FILE = "bank_data_final.json"

# --- DATA CLASSES ---

class LoanAccount:
    def __init__(self, loan_id, principal, total_due, years):
        self.loan_id = str(loan_id)
        self.principal = float(principal)
        self.total_due = float(total_due)
        self.years = int(years)

    def to_dict(self):
        return {
            "loan_id": self.loan_id,
            "principal": self.principal,
            "total_due": self.total_due,
            "years": self.years
        }

class TermDepositAccount:
    def __init__(self, td_id, amount, maturity_val, years):
        self.td_id = str(td_id)
        self.amount = float(amount)
        self.maturity_val = float(maturity_val)
        self.years = int(years)

    def to_dict(self):
        return {
            "td_id": self.td_id,
            "amount": self.amount,
            "maturity_val": self.maturity_val,
            "years": self.years
        }

class MainAccount:
    def __init__(self, name, acc_number, balance=0.0):
        self.name = name
        self.acc_number = str(acc_number)
        self.balance = float(balance)
        self.loans = []         # List of LoanAccount objects
        self.term_deposits = [] # List of TermDepositAccount objects

    def get_total_td_value(self):
        return sum(td.amount for td in self.term_deposits)

    def to_dict(self):
        return {
            "name": self.name,
            "acc_number": self.acc_number,
            "balance": self.balance,
            "loans": [l.to_dict() for l in self.loans],
            "term_deposits": [t.to_dict() for t in self.term_deposits]
        }

# --- BANK SYSTEM ---

class BankSystem:
    def __init__(self):
        self.accounts = {} 
        self.load_data()

    def load_data(self):
        if not os.path.exists(DB_FILE):
            return
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                for acc_num, acc_data in data.items():
                    new_acc = MainAccount(acc_data['name'], acc_data['acc_number'], acc_data['balance'])
                    
                    # Restore Loans
                    for l in acc_data.get('loans', []):
                        loan_obj = LoanAccount(l['loan_id'], l['principal'], l['total_due'], l['years'])
                        new_acc.loans.append(loan_obj)
                        
                    # Restore TDs
                    for t in acc_data.get('term_deposits', []):
                        td_obj = TermDepositAccount(t['td_id'], t['amount'], t['maturity_val'], t['years'])
                        new_acc.term_deposits.append(td_obj)
                        
                    self.accounts[acc_num] = new_acc
            print(f"Database loaded. {len(self.accounts)} accounts found.")
        except Exception:
            print("Database error or empty. Starting fresh.")

    def save_data(self):
        data_to_save = {acc_id: acc_obj.to_dict() for acc_id, acc_obj in self.accounts.items()}
        with open(DB_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)

    # --- ACCOUNT OPERATIONS ---

    def create_account(self):
        print("\n--- Create New Main Account ---")
        name = input("Enter Account Holder Name: ")
        acc_num = str(random.randint(1000000000, 9999999999))
        while acc_num in self.accounts:
            acc_num = str(random.randint(1000000000, 9999999999))
            
        new_acc = MainAccount(name, acc_num)
        self.accounts[acc_num] = new_acc
        self.save_data()
        print(f"Account Created! Number: {acc_num}")

    def get_account(self):
        acc_num = input("Enter 10-digit Main Account Number: ").strip()
        return self.accounts.get(acc_num, None)

    def deposit(self, account):
        try:
            amount = float(input("Enter amount to deposit: "))
            if amount > 0:
                account.balance += amount
                self.save_data()
                print(f"Success: ${amount:.2f} credited.")
            else: print("Amount must be positive.")
        except ValueError: print("Invalid input.")

    def withdraw(self, account):
        try:
            amount = float(input("Enter amount to withdraw: "))
            if 0 < amount <= account.balance:
                account.balance -= amount
                self.save_data()
                print(f"Success: ${amount:.2f} debited.")
            else: print("Insufficient funds.")
        except ValueError: print("Invalid input.")

    # --- LOAN LOGIC (MAX 4) ---

    def apply_loan(self, account):
        print("\n--- Apply for Separate Loan Account ---")
        
        # 1. CHECK QUANTITY LIMIT
        if len(account.loans) >= 4:
            print("ERROR: Maximum Limit Reached.")
            print("You already have 4 active loans. Pay one off to apply for another.")
            return

        try:
            req_amount = float(input("Enter loan amount required: "))
            years = int(input("Enter duration (years): "))
            
            if req_amount <= 0:
                print("Invalid amount.")
                return

            # 2. ELIGIBILITY CHECK
            # Rule: Balance >= 10% of Loan  OR  Total TD >= 50% of Loan
            balance_req = req_amount * 0.10
            td_req = req_amount * 0.50
            
            balance_check = account.balance >= balance_req
            td_check = account.get_total_td_value() >= td_req

            print(f"Checking Financial Health...")
            print(f"- Liquid Asset Check (Needs ${balance_req:.2f}): {'PASS' if balance_check else 'FAIL'}")
            print(f"- TD Collateral Check (Needs ${td_req:.2f}): {'PASS' if td_check else 'FAIL'}")

            if balance_check or td_check:
                loan_id = str(random.randint(1000, 9999)) # 4-digit ID
                total_due = req_amount * (1 + (0.07 * years))
                
                new_loan = LoanAccount(loan_id, req_amount, total_due, years)
                account.loans.append(new_loan)
                
                account.balance += req_amount
                self.save_data()
                print(f"\nLoan Approved! Created Loan #{loan_id}")
                print(f"${req_amount:.2f} added to Main Balance.")
            else:
                print("\nLoan Denied. Financial requirements not met.")

        except ValueError: print("Invalid input.")

    # --- TERM DEPOSIT LOGIC (MAX 10) ---

    def open_term_deposit(self, account):
        print("\n--- Open New Term Deposit ---")
        
        # 1. CHECK QUANTITY LIMIT
        if len(account.term_deposits) >= 10:
            print("ERROR: Maximum Limit Reached.")
            print("You already have 10 active Term Deposits.")
            return

        try:
            amount = float(input("Enter amount to invest (Min $10,000): "))
            
            if amount < 10000:
                print("Error: Minimum TD amount is $10,000.")
                return
            if amount > account.balance:
                print("Error: Insufficient funds in Main Account.")
                return

            years = int(input("Enter duration (years): "))
            
            td_id = str(random.randint(1000000000, 9999999999)) # 10-digit ID
            maturity = amount * (1 + (0.06 * years))
            
            new_td = TermDepositAccount(td_id, amount, maturity, years)
            account.term_deposits.append(new_td)
            
            account.balance -= amount
            self.save_data()
            print(f"TD Created! ID: {td_id}")
            print(f"Maturity Value: ${maturity:.2f}")

        except ValueError: print("Invalid input.")

    def pay_loan(self, account):
        print(f"\n--- Your Active Loans ({len(account.loans)}/4) ---")
        if not account.loans:
            print("No active loans.")
            return

        for l in account.loans:
            print(f"ID: {l.loan_id} | Due: ${l.total_due:.2f}")
        
        lid = input("Enter Loan ID to pay: ")
        target_loan = next((l for l in account.loans if l.loan_id == lid), None)

        if target_loan:
            try:
                amount = float(input(f"Enter amount to pay towards Loan #{lid}: "))
                if amount > account.balance:
                    print("Insufficient Main Balance.")
                elif amount > target_loan.total_due:
                    print("Amount exceeds remaining debt.")
                else:
                    account.balance -= amount
                    target_loan.total_due -= amount
                    
                    if target_loan.total_due <= 0:
                        print("Loan Paid in Full! Account Closed.")
                        account.loans.remove(target_loan) # Frees up a slot
                    else:
                        print(f"Payment received. Remaining Due: ${target_loan.total_due:.2f}")
                    
                    self.save_data()
            except ValueError: print("Invalid input.")
        else:
            print("Loan ID not found.")

    def transfer_money(self, sender):
        print("\n--- Transfer Money ---")
        target = input("Enter Recipient Account Number: ")
        if target == sender.acc_number:
            print("Cannot transfer to self.")
            return
        recipient = self.accounts.get(target)
        if recipient:
            try:
                amt = float(input("Enter Amount: "))
                if 0 < amt <= sender.balance:
                    sender.balance -= amt
                    recipient.balance += amt
                    self.save_data()
                    print("Transfer Successful.")
                else: print("Insufficient funds.")
            except ValueError: print("Invalid input.")
        else: print("Recipient not found.")

    def show_dashboard(self, account):
        print(f"\n=== DASHBOARD: {account.name} ===")
        print(f"Main Account: {account.acc_number}")
        print(f"Liquid Balance: ${account.balance:.2f}")
        
        print(f"\n--- Active Loans ({len(account.loans)}/4) ---")
        if account.loans:
            for l in account.loans:
                print(f"[#{l.loan_id}] Due: ${l.total_due:.2f}")
        else: print("None")

        print(f"\n--- Term Deposits ({len(account.term_deposits)}/10) ---")
        if account.term_deposits:
            for t in account.term_deposits:
                print(f"[#{t.td_id}] Invested: ${t.amount:.2f}")
        else: print("None")

    def main_menu(self):
        while True:
            print("\n--- BANK SYSTEM ---")
            print("1. Create Main Account")
            print("2. Login")
            print("3. Exit")
            c = input("Select: ")
            if c == '1': self.create_account()
            elif c == '2':
                acc = self.get_account()
                if acc:
                    while True:
                        self.show_dashboard(acc)
                        print("\n[1] Deposit [2] Withdraw [3] Transfer")
                        print("[4] Apply Loan [5] Open TD [6] Pay Loan [7] Logout")
                        opt = input("Choice: ")
                        if opt == '1': self.deposit(acc)
                        elif opt == '2': self.withdraw(acc)
                        elif opt == '3': self.transfer_money(acc)
                        elif opt == '4': self.apply_loan(acc)
                        elif opt == '5': self.open_term_deposit(acc)
                        elif opt == '6': self.pay_loan(acc)
                        elif opt == '7': break
            elif c == '3': sys.exit()

if __name__ == "__main__":
    sys = BankSystem()
    sys.main_menu()
