import sqlite3
import cx_Oracle
import mysql.connector
import webbrowser
import sqlparse
import psycopg2
import pandas as pd
import json
import csv
import requests
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.metrics import dp
from kivy.uix.codeinput import CodeInput
from pygments.lexers.sql import SqlLexer
from kivy.uix.popup import Popup
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.textinput import TextInput
from kivymd.uix.slider import MDSlider
from kivy.uix.switch import Switch
from kivy.uix.filechooser import FileChooserIconView
import os
import prettytable


class SQLAdminApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.database_type = "SQLite"
        self.conn = None
        self.cursor = None
        self.query_history = []  # Store executed queries

        self.main_layout = MDBoxLayout(orientation="horizontal", spacing=10)

        # 📂 Sidebar - Database & Tables Tree Structure
        self.sidebar = MDBoxLayout(orientation="vertical", size_hint=(0.3, 1), padding=10)
        self.db_label = MDLabel(text="📂 Databases & Tables", bold=True, halign="center")
        self.tree_view = TreeView()

        self.sidebar.add_widget(self.db_label)
        self.sidebar.add_widget(self.tree_view)

        self.main_layout.add_widget(self.sidebar)

        # 📌 Main Content
        content_layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)

        # ⚙️ Menu Button
        self.menu_button = MDIconButton(icon="dots-vertical", pos_hint={"right": 1})
        menu_items = [
            {"text": "🐞 Report Bug", "on_release": self.report_bug},
            {"text": "📤 Send to a Friend", "on_release": self.send_to_friend},
            {"text": "ℹ️ About", "on_release": self.show_about},
            {"text": "⚙️ Settings", "on_release": self.show_settings},
            {"text": "📜 Query History", "on_release": self.show_query_history},
            {"text": "📊 Export Data", "on_release": self.export_data},
            {"text": "📥 Create Database", "on_release": self.create_database},
            {"text": "📝 Register", "on_release": self.show_registration_popup},  # Register option
        ]
        self.menu = MDDropdownMenu(caller=self.menu_button, items=menu_items, width_mult=4)
        self.menu_button.bind(on_release=self.open_menu)

        # 🔄 Database Switch Button
        self.switch_db_button = MDRaisedButton(text="Switch Database", on_press=self.show_db_switcher)

        # SQL Query Input Box
        self.query_input = CodeInput(lexer=SqlLexer(), hint_text="Write your SQL Query here", size_hint_y=None, height=150)

        # Buttons
        button_layout = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        self.run_button = MDRaisedButton(text="Run Query", on_press=self.execute_query)
        self.format_query_button = MDRaisedButton(text="Format Query", on_press=self.format_query)

        button_layout.add_widget(self.switch_db_button)
        button_layout.add_widget(self.run_button)
        button_layout.add_widget(self.format_query_button)
        button_layout.add_widget(self.menu_button)

        # Label for Messages
        self.result_label = MDLabel(text="Results will appear here", theme_text_color="Secondary", halign="center", size_hint_y=None, height=30)

        # Table for Query Results (Improved)
        self.scroll_view = MDScrollView()
        self.data_table = MDDataTable(size_hint=(1, 0.7), use_pagination=True, column_data=[("Column", dp(30))], row_data=[("No data",)])
        self.scroll_view.add_widget(self.data_table)

        content_layout.add_widget(button_layout)
        content_layout.add_widget(self.query_input)
        content_layout.add_widget(self.result_label)
        content_layout.add_widget(self.scroll_view)

        self.main_layout.add_widget(content_layout)

        # Developer's Information Section
        self.developer_info = MDLabel(
            text="Built in Harshit's Laboratory, by Harshit Mishra\nVisit https://mishraharshit.vercel.app",
            theme_text_color="Primary",
            halign="center",
            size_hint_y=None,
            height=50,
        )
        self.developer_info.bind(on_touch_down=self.open_website)
        content_layout.add_widget(self.developer_info)

        # Connect to Default Database
        self.connect_to_database()

        return self.main_layout

    def open_website(self, instance, touch):
        """Open developer's website when label is clicked."""
        if instance.collide_point(*touch.pos):  # Check if the touch event is within the label
            webbrowser.open("https://mishraharshit.vercel.app")

    def create_database(self):
        """Open a popup to create a new database."""
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        self.db_name_input = TextInput(hint_text="Enter New Database Name")
        create_button = MDRaisedButton(text="Create Database", on_press=self.create_new_db)
        close_button = MDRaisedButton(text="Close", on_press=lambda x: self.db_popup.dismiss())

        layout.add_widget(self.db_name_input)
        layout.add_widget(create_button)
        layout.add_widget(close_button)

        self.db_popup = Popup(title="Create New Database", content=layout, size_hint=(0.8, 0.6))
        self.db_popup.open()

    def create_new_db(self):
        """Create a new database with the given name."""
        db_name = self.db_name_input.text.strip()
        if db_name:
            try:
                if self.database_type == "SQLite":
                    self.conn = sqlite3.connect(f"{db_name}.db")
                    self.cursor = self.conn.cursor()
                    self.result_label.text = f"✅ New SQLite Database '{db_name}' created!"
                    self.create_user_table()
                else:
                    self.result_label.text = f"❌ Only SQLite database creation is supported."
            except Exception as e:
                self.result_label.text = f"❌ Error creating database: {e}"
        self.db_popup.dismiss()

    def create_user_table(self):
        """Create the 'users' table to store user credentials."""
        try:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    name TEXT NOT NULL,
                                    email TEXT NOT NULL UNIQUE,
                                    password TEXT NOT NULL)''')
            self.conn.commit()
        except Exception as e:
            self.result_label.text = f"❌ Error creating users table: {e}"

    def export_data(self):
        """Open popup to choose export format and export data."""
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        self.export_type_input = TextInput(hint_text="Export Type (Excel/JSON/CSV/TXT)")
        self.export_button = MDRaisedButton(text="Export", on_press=self.export_query_results)

        layout.add_widget(self.export_type_input)
        layout.add_widget(self.export_button)

        self.export_popup = Popup(title="Export Data", content=layout, size_hint=(0.8, 0.6))
        self.export_popup.open()

    def export_query_results(self):
        """Export query results based on the selected format."""
        export_type = self.export_type_input.text.strip().lower()

        if export_type == "excel":
            self.export_to_excel()
        elif export_type == "json":
            self.export_to_json()
        elif export_type == "csv":
            self.export_to_csv()
        elif export_type == "txt":
            self.export_to_txt()
        else:
            self.result_label.text = "❌ Invalid Export Type!"

        self.export_popup.dismiss()

    def export_to_excel(self):
        """Export query results to Excel."""
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()

        df = pd.DataFrame(rows, columns=columns)

        filechooser = FileChooserIconView()
        filechooser.filters = ['*.xlsx']
        filechooser.bind(on_submit=self.save_excel)
        self.result_label.text = "✅ Excel Export Started!"

    def save_excel(self,  selection):
        """Save the DataFrame as Excel."""
        if selection:
            file_path = selection[0]
            df.to_excel(file_path, index=False)
            self.result_label.text = f"✅ Data exported to {file_path}"

    def export_to_json(self):
        """Export query results to JSON."""
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()

        data = [dict(zip(columns, row)) for row in rows]
        filechooser = FileChooserIconView()
        filechooser.filters = ['*.json']
        filechooser.bind(on_submit=self.save_json)
        self.result_label.text = "✅ JSON Export Started!"

    def save_json(self, selection):
        """Save the JSON data."""
        if selection:
            file_path = selection[0]
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            self.result_label.text = f"✅ Data exported to {file_path}"

    def export_to_csv(self):
        """Export query results to CSV."""
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()

        filechooser = FileChooserIconView()
        filechooser.filters = ['*.csv']
        filechooser.bind(on_submit=self.save_csv)
        self.result_label.text = "✅ CSV Export Started!"

    def save_csv(self, selection):
        """Save the CSV data."""
        if selection:
            file_path = selection[0]
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(columns)  # Write column headers
                writer.writerows(rows)  # Write data rows
            self.result_label.text = f"✅ Data exported to {file_path}"

    def export_to_txt(self):
        """Export query results to TXT."""
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()

        filechooser = FileChooserIconView()
        filechooser.filters = ['*.txt']
        filechooser.bind(on_submit=self.save_txt)
        self.result_label.text = "✅ TXT Export Started!"

    def save_txt(self, selection):
        """Save the TXT data."""
        if selection:
            file_path = selection[0]
            with open(file_path, 'w') as file:
                file.write('\t'.join(columns) + '\n')  # Write column headers
                for row in rows:
                    file.write('\t'.join(map(str, row)) + '\n')  # Write data rows
            self.result_label.text = f"✅ Data exported to {file_path}"

    def show_db_switcher(self, instance):
        """Show a popup to switch databases.""" 
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        self.db_type_input = TextInput(hint_text="Database Type (SQLite/MySQL/Oracle/PostgreSQL)")
        self.host_input = TextInput(hint_text="Host (Only for MySQL/Oracle/PostgreSQL)")
        self.user_input = TextInput(hint_text="Username (Only for MySQL/Oracle/PostgreSQL)")
        self.pass_input = TextInput(hint_text="Password (Only for MySQL/Oracle/PostgreSQL)", password=True)
        self.db_name_input = TextInput(hint_text="Database Name (For MySQL/Oracle/PostgreSQL)")

        switch_button = MDRaisedButton(text="Connect", on_press=self.switch_database)
        close_button = MDRaisedButton(text="Close", on_press=lambda x: self.db_popup.dismiss())

        layout.add_widget(self.db_type_input)
        layout.add_widget(self.host_input)
        layout.add_widget(self.user_input)
        layout.add_widget(self.pass_input)
        layout.add_widget(self.db_name_input)
        layout.add_widget(switch_button)
        layout.add_widget(close_button)

        self.db_popup = Popup(title="Switch Database", content=layout, size_hint=(0.8, 0.6))
        self.db_popup.open()

    def switch_database(self, instance):
        """Connect to the new database based on user input.""" 
        self.database_type = self.db_type_input.text.strip()

        if self.database_type == "SQLite":
            self.connect_to_database()
        else:
            host = self.host_input.text.strip()
            user = self.user_input.text.strip()
            password = self.pass_input.text.strip()
            db_name = self.db_name_input.text.strip()

            self.connect_to_database(host, user, password, db_name)

        self.db_popup.dismiss()

    def connect_to_database(self, host=None, user=None, password=None, db_name=None):
        """Connect to the selected database.""" 
        try:
            if self.database_type == "SQLite":
                self.conn = sqlite3.connect("database.db")
            elif self.database_type == "Oracle":
                dsn = cx_Oracle.makedsn(host, 1521, service_name=db_name)
                self.conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
            elif self.database_type == "MySQL":
                self.conn = mysql.connector.connect(
                    host=host, user=user, password=password, database=db_name
                )
            elif self.database_type == "PostgreSQL":
                self.conn = psycopg2.connect(
                    host=host, user=user, password=password, dbname=db_name
                )

            self.cursor = self.conn.cursor()
            self.result_label.text = f"✅ Connected to {self.database_type} Database!"
            self.load_sidebar()
        except Exception as e:
            self.result_label.text = f"❌ Connection Failed: {e}"

    def execute_query(self, instance):
        """Execute the SQL query entered by the user and display results.""" 
        query = self.query_input.text.strip()
        if not query:
            self.result_label.text = "⚠️ Please enter an SQL query."
            return

        # Append the query to history
        self.query_history.append(query)

        try:
            self.cursor.execute(query)
            self.conn.commit()

            if query.lower().startswith("select"):
                columns = [desc[0] for desc in self.cursor.description]
                rows = self.cursor.fetchall()

                column_names_str = "|".join(columns)
                result_str = f"columns: {column_names_str}\n{'-' *50}\n"

                if not rows:
                    self.result_label.text = "⚆_⚆ Query executed successfully! No data returned."
                    self.result_label.txt = result_str
                    return

                for row in rows:
                    result_str += "|".join(str(cell) for cell in row) + "\n"  
                    result_str += "-" * (len(columns) *10) + "\n"
                self.result_label.text = result_str
                self.show_results_in_cmd(columns, rows)     

                self.data_table.column_data = [(col, dp(30)) for col in columns]
                self.data_table.row_data = [tuple(row) for row in rows]

                self.result_label.text = f"✅ Query executed successfully! {len(rows)} rows fetched. SHOW Structured view in terminal."
            else:
                self.result_label.text = "✅ Query executed successfully!"
        except Exception as e:
            self.result_label.text = f"❌ Error: {str(e)}"
               
    def show_results_in_cmd(self, columns, rows):
    
        try:
        # Use prettytable to format and display results in CMD
            table = prettytable.PrettyTable(columns)
            for row in rows:
             table.add_row(row)

        # Print the table to the CMD
            print(table)
        except Exception as e:
             self.result_label.text = f"❌ Error displaying results in CMD: {str(e)}"

    def format_query(self, instance):
        """Format SQL query for readability.""" 
        self.query_input.text = sqlparse.format(self.query_input.text, reindent=True, keyword_case="upper")

    def show_query_history(self):
        """Display the history of executed queries.""" 
        if not self.query_history:
            self.show_popup("Query History", "No query history available.")
        else:
            history_text = "\n".join(self.query_history[-10:])  # Show last 10 queries
            self.show_popup("Query History", history_text)

    def show_popup(self, title, message):
        """Show a popup with a message.""" 
        popup_layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)
        popup_label = MDLabel(text=message, halign="center")
        close_button = MDRaisedButton(text="Close", on_press=lambda x: popup.dismiss())

        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4))
        popup.open()

    def load_sidebar(self):
        """Load databases & tables into sidebar tree view.""" 
        self.tree_view.clear_widgets()
        try:
            if self.database_type == "SQLite":
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            elif self.database_type == "MySQL":
                self.cursor.execute("SHOW TABLES;")
            elif self.database_type == "PostgreSQL":
                self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")

            tables = self.cursor.fetchall()
            for table in tables:
                table_name = table[0]
                node = TreeViewLabel(text=table_name)  # TreeViewLabel creates a label node
                self.tree_view.add_node(node)

                node.bind(on_release=self.on_table_click)
        except Exception as e:
            self.result_label.text = f"❌ Failed to load tables: {str(e)}"

    def on_table_click(self):
    
        table_name = instance.text  # The table name is the text of the clicked TreeViewLabel
        self.show_edit_table_popup(table_name)   

    def show_edit_table_popup(self, table_name):
      
            try:
            # Fetch the table data
                self.cursor.execute(f"SELECT * FROM {table_name}")
                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]

            # Create the layout for the popup
                layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

            # Table Name Label
                table_name_label = MDLabel(text=f"Editing Table: {table_name}", theme_text_color="Secondary", halign="center")
                layout.add_widget(table_name_label)

            # Create the grid layout to show rows and columns
                grid_layout = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(200))
                grid_layout.bind(minimum_height=grid_layout.setter('height'))

            # Create headers for the columns
                for col in columns:
                    header_label = MDLabel(text=col, theme_text_color="Primary", size_hint_y=None, height=dp(40))
                    grid_layout.add_widget(header_label)

            # Create TextInputs for each row and column in the table
                self.row_inputs = []
                for row in rows:
                    row_input = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
                for value in row:
                    input_field = TextInput(text=str(value), multiline=False)
                    row_input.add_widget(input_field)
                self.row_inputs.append(row_input)
                grid_layout.add_widget(row_input)

                layout.add_widget(grid_layout)

            # Add save and close buttons
                button_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=10)
                save_button = MDRaisedButton(text="Save Changes", on_press=lambda instance: self.save_table_changes(table_name))
                close_button = MDRaisedButton(text="Close", on_press=lambda instance: self.table_popup.dismiss())
                button_layout.add_widget(save_button)
                button_layout.add_widget(close_button)

                layout.add_widget(button_layout)

            # Create and open the popup
                self.table_popup = Popup(title=f"Edit Table: {table_name}", content=layout, size_hint=(0.8, 0.8))
                self.table_popup.open()

            except Exception as e:
                self.result_label.text = f"❌ Failed to load table data: {str(e)}"

    def save_table_changes(self, table_name):
       
        try:
            # Collect the modified data from TextInputs
            updated_rows = []
            for row_input in self.row_inputs:
                updated_row = [input_field.text for input_field in row_input.children]
                updated_rows.append(updated_row)

            # Update the table with the new values (For simplicity, assuming that table has 3 columns here)
            for i, updated_row in enumerate(updated_rows):
                set_clause = ', '.join([f"{col} = '{value}'" for col, value in zip(columns, updated_row)])
                self.cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE rowid = {i + 1}")

            # Commit the changes to the database
            self.conn.commit()
            self.result_label.text = f"✅ Changes to table {table_name} have been saved."

            # Close the popup
            self.table_popup.dismiss()

        except Exception as e:
            self.result_label.text = f"❌ Error saving changes: {str(e)}"        

    def show_settings(self):
        """Show Settings Panel with theme and font size adjustment options.""" 
        settings_layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        # **Font Size Slider**
        font_size_label = MDLabel(text="Adjust Font Size", theme_text_color="Primary", halign="center")
        self.font_size_slider = MDSlider(min=12, max=30, value=16, step=1)
        self.font_size_slider.bind(value=self.adjust_font_size)

        # **Theme Toggle Switch**
        theme_label = MDLabel(text="Dark Theme", theme_text_color="Primary", halign="center")
        self.theme_switch = Switch(active=self.theme_cls.theme_style == "Dark")
        self.theme_switch.bind(active=self.toggle_theme)

        # **Code Input Height Slider**
        code_height_label = MDLabel(text="Adjust Code Input Height", theme_text_color="Primary", halign="center")
        self.code_height_slider = MDSlider(min=100, max=500, value=self.query_input.height, step=10)
        self.code_height_slider.bind(value=self.adjust_code_input_height)

        # **Result Output Height Slider**
        result_height_label = MDLabel(text="Adjust Result Output Height", theme_text_color="Primary", halign="center")
        self.result_height_slider = MDSlider(min=100, max=500, value=self.scroll_view.height, step=10)
        self.result_height_slider.bind(value=self.adjust_result_output_height)

        # Add widgets to settings layout
        settings_layout.add_widget(font_size_label)
        settings_layout.add_widget(self.font_size_slider)
        settings_layout.add_widget(theme_label)
        settings_layout.add_widget(self.theme_switch)
        settings_layout.add_widget(code_height_label)
        settings_layout.add_widget(self.code_height_slider)
        settings_layout.add_widget(result_height_label)
        settings_layout.add_widget(self.result_height_slider)

        # Add a close button to the settings popup
        close_button = MDRaisedButton(text="Close", on_press=self.close_settings)
        settings_layout.add_widget(close_button)

        # Create and open the popup with the settings layout
        self.settings_popup = Popup(title="⚙️ Settings", content=settings_layout, size_hint=(0.8, 0.6))
        self.settings_popup.open()

    def close_settings(self, instance):
        """Close the settings popup.""" 
        self.settings_popup.dismiss()

    def adjust_font_size(self, instance, value):
        """Adjust font size dynamically based on the slider value.""" 
        self.query_input.font_size = value  # Adjust font size for the query input box
        self.result_label.font_size = value  # Adjust font size for the result label

    def adjust_code_input_height(self, instance, value):
        """Adjust the height of the code input box dynamically.""" 
        self.query_input.height = value

    def adjust_result_output_height(self, instance, value):
        """Adjust the height of the result output area dynamically.""" 
        self.scroll_view.height = value

    def toggle_theme(self, instance, value):
        """Toggle between dark and light theme based on the switch state.""" 
        if value:
            self.theme_cls.theme_style = "Dark"  # Set theme to dark
        else:
            self.theme_cls.theme_style = "Light"  # Set theme to light

    def open_menu(self, instance):
        """Open the dropdown menu when the menu button is pressed.""" 
        self.menu.open()

    def report_bug(self):
        """Open GitHub Issues Page.""" 
        webbrowser.open("https://sqlexe.vercel.app/#issue")

    def send_to_friend(self):
        """Show Share URL.""" 
        self.show_popup("📤 Share App", "Share this URL with friends:\nhttps://mishraharshit.vercel.app/sqlexe.html")

    def show_about(self):
        """Show About Section.""" 
        self.show_popup("ℹ️ About", "👨‍💻 Developed by: Harshit Mishra\n🏢 SecureCoder\n🌍 https://mishraharshit.vercel.app\n📧 mishra9759harshit@gmail.com")

    def show_registration_popup(self):
        """Open a popup for user registration.""" 
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=10)

        self.reg_name_input = TextInput(hint_text="Name", multiline=False)
        self.reg_email_input = TextInput(hint_text="Email", multiline=False)
        self.reg_password_input = TextInput(hint_text="Password", multiline=False, password=True)
        register_button = MDRaisedButton(text="Register", on_press=self.save_registration)
        close_button = MDRaisedButton(text="Close", on_press=lambda x: self.reg_popup.dismiss())

        layout.add_widget(self.reg_name_input)
        layout.add_widget(self.reg_email_input)
        layout.add_widget(self.reg_password_input)
        layout.add_widget(register_button)
        layout.add_widget(close_button)

        self.reg_popup = Popup(title="Register", content=layout, size_hint=(0.8, 0.6))
        self.reg_popup.open()

    def save_registration(self, intence):
        """Save registration details in the local database and send them to Formspree.""" 
        name = self.reg_name_input.text.strip()
        email = self.reg_email_input.text.strip()
        password = self.reg_password_input.text.strip()

        if name and email and password:
            # Send to Formspree
            payload = {'name': name, 'email': email, 'message': f"Registration details for {name}"}
            requests.post("https://formspree.io/f/xyzkpywz", data=payload)

            self.result_label.text = f"✅ Registration successful for {name}!"
        else:
            self.result_label.text = "❌ Please fill all fields!"

        self.reg_popup.dismiss()

# Run the application
if __name__ == "__main__":
    SQLAdminApp().run()

