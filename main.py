import customtkinter as ctk
import sqlite3
from datetime import datetime
from tkinter import ttk, messagebox  # Add this import for Treeview widget

# Database setup
conn = sqlite3.connect("store_inventory.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    quantity INTEGER,
    photo_path TEXT,
    date_added TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT,
    quantity INTEGER,
    total_price REAL,
    sale_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    amount REAL,
    expense_date TEXT
)
""")
conn.commit()


# Functions
def calculate_totals():
    # Calculate total sales (all-time)
    cursor.execute("SELECT SUM(total_price) FROM sales")
    total_income = cursor.fetchone()[0] or 0

    # Calculate total expenses (all-time)
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0

    # Calculate today's total sales
    cursor.execute("SELECT SUM(total_price) FROM sales WHERE date(sale_date) = ?", (datetime.now().strftime("%Y-%m-%d"),))
    today_sales_total = cursor.fetchone()[0] or 0

    # Calculate today's total expenses
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE date(expense_date) = ?", (datetime.now().strftime("%Y-%m-%d"),))
    today_expenses_total = cursor.fetchone()[0] or 0

    return total_income, total_expenses, today_sales_total, today_expenses_total


def update_dashboard():
    total_income, total_expenses, today_sales_total, today_expenses_total = calculate_totals()
    net_income = today_sales_total - today_expenses_total
    dashboard_total_income_label.configure(text=f"Net Income: ${net_income:.2f}")
    dashboard_total_expenses_label.configure(text=f"Total Expenses: ${total_expenses:.2f}")
    dashboard_today_sales_label.configure(text=f"Today's Sales: ${today_sales_total:.2f}")
    dashboard_date_label.configure(text=f"Date: {datetime.now().strftime('%Y-%m-%d')}")


def add_or_update_product():
    name = product_name_var.get()
    try:
        price = float(product_price_var.get())
        quantity = int(product_quantity_var.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter valid price and quantity.")
        return

    photo_path = product_photo_var.get()
    date_added = datetime.now().strftime("%Y-%m-%d")

    if name and price > 0 and quantity > 0:
        cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
        existing_product = cursor.fetchone()
        if existing_product:
            cursor.execute("UPDATE products SET price = ?, quantity = quantity + ?, photo_path = ? WHERE id = ?",
                           (price, quantity, photo_path, existing_product[0]))
        else:
            cursor.execute("INSERT INTO products (name, price, quantity, photo_path, date_added) VALUES (?, ?, ?, ?, ?)",
                           (name, price, quantity, photo_path, date_added))
        conn.commit()
        product_name_var.set("")
        product_price_var.set("")
        product_quantity_var.set("")
        product_photo_var.set("")
        update_products_view()
        messagebox.showinfo("Success", "Product added/updated successfully.")
    else:
        messagebox.showerror("Error", "All fields are required.")


def update_products_view():
    for row in product_tree.get_children():
        product_tree.delete(row)
    cursor.execute("SELECT id, name, price, quantity, date_added FROM products")
    for row in cursor.fetchall():
        product_tree.insert("", "end", values=row)


def sell_products():
    cart_items = cart_tree.get_children()
    if not cart_items:
        messagebox.showerror("Error", "Cart is empty. Add products to the cart first.")
        return

    for item in cart_items:
        cart_data = cart_tree.item(item)['values']
        product_id, name, price, available_quantity, quantity_to_sell = cart_data

        try:
            price = float(price)
            quantity_to_sell = int(quantity_to_sell)
        except ValueError:
            messagebox.showerror("Error", "Invalid data in cart.")
            return

        total_price = price * quantity_to_sell
        new_quantity = available_quantity - quantity_to_sell

        cursor.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, product_id))
        cursor.execute("INSERT INTO sales (product_name, quantity, total_price, sale_date) VALUES (?, ?, ?, ?)",
                       (name, quantity_to_sell, total_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    update_products_view()
    cart_tree.delete(*cart_tree.get_children())
    update_sales_view()
    update_dashboard()
    messagebox.showinfo("Success", "Sales recorded successfully.")


def add_to_cart():
    selected_item = product_tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a product to add to the cart.")
        return

    item = product_tree.item(selected_item[0])['values']
    product_id, name, price, quantity, date_added = item

    try:
        quantity_to_sell = int(sell_quantity_var.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid quantity to sell.")
        return

    if quantity_to_sell <= 0 or quantity_to_sell > quantity:
        messagebox.showerror("Error", "Invalid quantity to sell.")
        return

    cart_tree.insert("", "end", values=(product_id, name, price, quantity, quantity_to_sell))
    sell_quantity_var.set("")


def remove_from_cart():
    selected_item = cart_tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a product to remove from the cart.")
        return

    for item in selected_item:
        cart_tree.delete(item)

    messagebox.showinfo("Success", "Product removed from the cart.")


def update_sales_view():
    for row in sales_tree.get_children():
        sales_tree.delete(row)

    cursor.execute("SELECT product_name, quantity, total_price, sale_date FROM sales WHERE date(sale_date) = ?", (datetime.now().strftime("%Y-%m-%d"),))
    total_sales_today = 0

    for row in cursor.fetchall():
        sales_tree.insert("", "end", values=row)
        total_sales_today += row[2]

    daily_sales_total_label.config(text=f"Today's Total Sales: ${total_sales_today:.2f}")


def add_expense():
    description = expense_description_var.get()
    try:
        amount = float(expense_amount_var.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid amount.")
        return

    if description and amount > 0:
        expense_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO expenses (description, amount, expense_date) VALUES (?, ?, ?)",
                       (description, amount, expense_date))
        conn.commit()
        expense_description_var.set("")
        expense_amount_var.set("")
        messagebox.showinfo("Success", "Expense added successfully.")
        update_dashboard()
        update_expenses_view()
    else:
        messagebox.showerror("Error", "All fields are required.")


def update_expenses_view():
    for row in expenses_tree.get_children():
        expenses_tree.delete(row)

    cursor.execute("SELECT description, amount, expense_date FROM expenses WHERE date(expense_date) = ?", (datetime.now().strftime("%Y-%m-%d"),))
    total_expenses_today = 0

    for row in cursor.fetchall():
        expenses_tree.insert("", "end", values=row)
        total_expenses_today += row[1]

    daily_expenses_total_label.config(text=f"Today's Total Expenses: ${total_expenses_today:.2f}")


# Search functionality
def filter_products():
    search_term = search_product_var.get()
    for row in product_tree.get_children():
        product_tree.delete(row)
    cursor.execute("SELECT id, name, price, quantity, date_added FROM products WHERE name LIKE ?", (f"%{search_term}%",))
    for row in cursor.fetchall():
        product_tree.insert("", "end", values=row)


def filter_expenses():
    search_term = search_expense_var.get()
    for row in expense_tree.get_children():
        expense_tree.delete(row)
    cursor.execute("SELECT id, description, amount, expense_date FROM expenses WHERE description LIKE ?", (f"%{search_term}%",))
    for row in cursor.fetchall():
        expense_tree.insert("", "end", values=row)


def filter_sales():
    search_term = search_sales_var.get()
    for row in sales_tree.get_children():
        sales_tree.delete(row)
    cursor.execute("SELECT product_name, quantity, total_price, sale_date FROM sales WHERE product_name LIKE ?", (f"%{search_term}%",))
    for row in cursor.fetchall():
        sales_tree.insert("", "end", values=row)




# GUI Setup using CustomTkinter
root = ctk.CTk()
root.title("Zinc Store Inventory")
root.geometry("1200x700")

# Navigation
nav_frame = ctk.CTkFrame(root, width=200)
nav_frame.pack(side="left", fill="y")

# Tabs
content_frame = ctk.CTkFrame(root)
content_frame.pack(side="right", fill="both", expand=True)


def show_frame(frame):
    frame.tkraise()


dashboard_frame = ctk.CTkFrame(content_frame)

# Create a Canvas to make the tab scrollable
product_canvas = ctk.CTkCanvas(content_frame, highlightthickness=0)
product_canvas.pack(side="left", fill="both", expand=True)

# Add a vertical scrollbar to the canvas
product_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=product_canvas.yview)
product_scrollbar.pack(side="right", fill="y")

# Configure the canvas and bind the scrollbar
product_canvas.configure(yscrollcommand=product_scrollbar.set)
product_canvas.bind("<Configure>", lambda e: product_canvas.configure(scrollregion=product_canvas.bbox("all")))

# Create a frame inside the canvas for content
product_management_frame = ctk.CTkFrame(product_canvas)
product_canvas.create_window((0, 0), window=product_management_frame, anchor="nw")

daily_sales_frame = ctk.CTkFrame(content_frame)
expenses_frame = ctk.CTkFrame(content_frame)

for frame in (dashboard_frame, product_management_frame, daily_sales_frame, expenses_frame):
    frame.pack(fill="both", expand=True)


# Dashboard
ctk.CTkLabel(dashboard_frame, text="Zinc Store Inventory", font=("Arial", 24, "bold")).pack(pady=20)
dashboard_total_income_label = ctk.CTkLabel(dashboard_frame, text="Net Income: $0.00", font=("Arial", 18, "bold"))
dashboard_total_income_label.pack(pady=10)
dashboard_total_expenses_label = ctk.CTkLabel(dashboard_frame, text="Total Expenses: $0.00", font=("Arial", 18, "bold"))
dashboard_total_expenses_label.pack(pady=10)
dashboard_today_sales_label = ctk.CTkLabel(dashboard_frame, text="Today's Sales: $0.00", font=("Arial", 18, "bold"))
dashboard_today_sales_label.pack(pady=10)
dashboard_date_label = ctk.CTkLabel(dashboard_frame, text=f"Date: {datetime.now().strftime('%Y-%m-%d')}", font=("Arial", 14))
dashboard_date_label.pack(pady=10)

# Product Management
ctk.CTkLabel(product_management_frame, text="Manage Products and Sales", font=("Arial", 18, "bold")).pack(pady=20)
product_name_var = ctk.StringVar()
product_price_var = ctk.StringVar()
product_quantity_var = ctk.StringVar()
product_photo_var = ctk.StringVar()
sell_quantity_var = ctk.StringVar()

search_product_var = ctk.StringVar()
ctk.CTkLabel(product_management_frame, text="Search Product:").pack()
ctk.CTkEntry(product_management_frame, textvariable=search_product_var).pack()
ctk.CTkButton(product_management_frame, text="Search", command=filter_products).pack(pady=5)

product_row_frame = ctk.CTkFrame(product_management_frame)
product_row_frame.pack(fill="x", padx=20, pady=5)

# Product Name
ctk.CTkLabel(product_row_frame, text="Product Name:").pack(side="left", padx=5)
ctk.CTkEntry(product_row_frame, textvariable=product_name_var).pack(side="left", padx=5)

# Price
ctk.CTkLabel(product_row_frame, text="Price:").pack(side="left", padx=5)
ctk.CTkEntry(product_row_frame, textvariable=product_price_var).pack(side="left", padx=5)

# Quantity
ctk.CTkLabel(product_row_frame, text="Quantity:").pack(side="left", padx=5)
ctk.CTkEntry(product_row_frame, textvariable=product_quantity_var).pack(side="left", padx=5)

ctk.CTkLabel(product_management_frame, text="Photo Path:").pack(fill="x", padx=20, pady=5)
ctk.CTkEntry(product_management_frame, textvariable=product_photo_var).pack(fill="x", padx=20, pady=5)

ctk.CTkButton(product_management_frame, text="Add/Update Product", command=add_or_update_product).pack(pady=10)

product_tree_frame = ctk.CTkFrame(product_management_frame)
product_tree_frame.pack(pady=10, fill="both", expand=True)

product_tree = ttk.Treeview(product_tree_frame, columns=("ID", "Name", "Price", "Quantity", "Date Added"), show="headings")
product_tree.pack(side="left", fill="both", expand=True)

product_tree_scrollbar = ttk.Scrollbar(product_tree_frame, orient="vertical", command=product_tree.yview)
product_tree_scrollbar.pack(side="right", fill="y")

product_tree.configure(yscrollcommand=product_tree_scrollbar.set)

for col in ("ID", "Name", "Price", "Quantity", "Date Added"):
    product_tree.heading(col, text=col)
product_tree.bind("<ButtonRelease-1>", lambda event: show_product_details(event))

# Cart Management
ctk.CTkLabel(product_management_frame, text="Add to Cart", font=("Arial", 18, "bold")).pack(pady=20)
ctk.CTkLabel(product_management_frame, text="Quantity to Sell:").pack()
ctk.CTkEntry(product_management_frame, textvariable=sell_quantity_var).pack()
ctk.CTkButton(product_management_frame, text="Add to Cart", command=add_to_cart).pack(pady=10)

cart_tree_frame = ctk.CTkFrame(product_management_frame)
cart_tree_frame.pack(pady=10, fill="both", expand=True)

cart_tree = ttk.Treeview(cart_tree_frame, columns=("ID", "Name", "Price", "Available Quantity", "Quantity to Sell"), show="headings")
cart_tree.pack(side="left", fill="both", expand=True)

cart_tree_scrollbar = ttk.Scrollbar(cart_tree_frame, orient="vertical", command=cart_tree.yview)
cart_tree_scrollbar.pack(side="right", fill="y")

cart_tree.configure(yscrollcommand=cart_tree_scrollbar.set)

for col in ("ID", "Name", "Price", "Available Quantity", "Quantity to Sell"):
    cart_tree.heading(col, text=col)

ctk.CTkButton(product_management_frame, text="Remove from Cart", command=remove_from_cart).pack(pady=10)
ctk.CTkButton(product_management_frame, text="Complete Sale", command=sell_products).pack(pady=10)

# Daily Sales
daily_sales_total_label = ctk.CTkLabel(daily_sales_frame, text="Today's Total Sales: $0.00", font=("Arial", 14, "bold"))
daily_sales_total_label.pack(pady=10)

ctk.CTkLabel(daily_sales_frame, text="Daily Sales", font=("Arial", 18, "bold")).pack(pady=20)

search_sales_var = ctk.StringVar()
ctk.CTkLabel(daily_sales_frame, text="Search Sale:").pack()
ctk.CTkEntry(daily_sales_frame, textvariable=search_sales_var).pack()
ctk.CTkButton(daily_sales_frame, text="Search", command=filter_sales).pack(pady=5)

sales_tree_frame = ctk.CTkFrame(daily_sales_frame)
sales_tree_frame.pack(pady=10, fill="both", expand=True)

sales_tree = ttk.Treeview(sales_tree_frame, columns=("Product Name", "Quantity", "Total Price", "Sale Date"), show="headings")
sales_tree.pack(side="left", fill="both", expand=True)

sales_tree_scrollbar = ttk.Scrollbar(sales_tree_frame, orient="vertical", command=sales_tree.yview)
sales_tree_scrollbar.pack(side="right", fill="y")

sales_tree.configure(yscrollcommand=sales_tree_scrollbar.set)

for col in ("Product Name", "Quantity", "Total Price", "Sale Date"):
    sales_tree.heading(col, text=col)

# Expenses
daily_expenses_total_label = ctk.CTkLabel(expenses_frame, text="Today's Total Expenses: $0.00", font=("Arial", 14, "bold"))
daily_expenses_total_label.pack(pady=10)

ctk.CTkLabel(expenses_frame, text="Manage Expenses", font=("Arial", 18, "bold")).pack(pady=20)
expense_description_var = ctk.StringVar()
expense_amount_var = ctk.StringVar()

ctk.CTkLabel(expenses_frame, text="Description:").pack()
ctk.CTkEntry(expenses_frame, textvariable=expense_description_var).pack()
ctk.CTkLabel(expenses_frame, text="Amount:").pack()
ctk.CTkEntry(expenses_frame, textvariable=expense_amount_var).pack()
ctk.CTkButton(expenses_frame, text="Add Expense", command=add_expense).pack(pady=10)

search_expense_var = ctk.StringVar()
ctk.CTkLabel(expenses_frame, text="Search Expense:").pack()
ctk.CTkEntry(expenses_frame, textvariable=search_expense_var).pack()
ctk.CTkButton(expenses_frame, text="Search", command=filter_expenses).pack(pady=5)

expenses_tree_frame = ctk.CTkFrame(expenses_frame)
expenses_tree_frame.pack(pady=10, fill="both", expand=True)

expenses_tree = ttk.Treeview(expenses_tree_frame, columns=("Description", "Amount", "Expense Date"), show="headings")
expenses_tree.pack(side="left", fill="both", expand=True)

expenses_tree_scrollbar = ttk.Scrollbar(expenses_tree_frame, orient="vertical", command=expenses_tree.yview)
expenses_tree_scrollbar.pack(side="right", fill="y")

expenses_tree.configure(yscrollcommand=expenses_tree_scrollbar.set)

for col in ("Description", "Amount", "Expense Date"):
    expenses_tree.heading(col, text=col)

# Navigation Buttons
ctk.CTkButton(nav_frame, text="Dashboard", command=lambda: show_frame(dashboard_frame)).pack(pady=10)
ctk.CTkButton(nav_frame, text="Product Management", command=lambda: show_frame(product_management_frame)).pack(pady=10)
ctk.CTkButton(nav_frame, text="Daily Sales", command=lambda: show_frame(daily_sales_frame)).pack(pady=10)
ctk.CTkButton(nav_frame, text="Expenses", command=lambda: show_frame(expenses_frame)).pack(pady=10)

# Set initial view
show_frame(dashboard_frame)

root.mainloop()
