import tkinter as tk
from tkinter import ttk, messagebox
from raytracing import OpticalSystem
import matplotlib.pyplot as plt

class OpticalSystemGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Optical System Setup")
        self.root.geometry("400x600")
        
        self.system = OpticalSystem()
        self.object_height = 0
        self.conditions = []
        self.current_position = 0  # Track current position
        
        # Start with object height input
        self.show_object_height_input()
    
    def show_object_height_input(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Enter Object Height (cm):").grid(row=0, column=0, padx=5, pady=5)
        height_var = tk.StringVar()
        height_entry = ttk.Entry(frame, textvariable=height_var)
        height_entry.grid(row=0, column=1, padx=5, pady=5)
        
        def next_step():
            try:
                self.object_height = float(height_var.get())
                self.system.set_object_height(self.object_height)
                self.show_condition_input()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
        
        ttk.Button(frame, text="Next", command=next_step).grid(row=1, column=0, columnspan=2, pady=10)
    
    def show_condition_input(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Show current conditions
        if self.conditions:
            ttk.Label(frame, text="Current Conditions:").grid(row=0, column=0, columnspan=2, pady=5)
            for i, condition in enumerate(self.conditions, 1):
                ttk.Label(frame, text=f"{i}. {condition}").grid(row=i, column=0, columnspan=2, pady=2)
            start_row = len(self.conditions) + 1
        else:
            start_row = 0
        
        # Show current position
        ttk.Label(frame, text=f"Current Position: {self.current_position} cm").grid(row=start_row, column=0, columnspan=2, pady=5)
        start_row += 1
        
        # Condition type selection
        ttk.Label(frame, text="Select Condition Type:").grid(row=start_row, column=0, pady=5)
        condition_type = ttk.Combobox(frame, values=["Transfer", "Iris", "Refraction"])
        condition_type.grid(row=start_row, column=1, pady=5)
        condition_type.set("Transfer")
        
        # Parameter frames
        param_frame = ttk.Frame(frame)
        param_frame.grid(row=start_row+1, column=0, columnspan=2, pady=5)
        
        # Parameter variables
        param_vars = []
        
        def update_params(*args):
            # Clear parameter frame
            for widget in param_frame.winfo_children():
                widget.destroy()
            param_vars.clear()
            
            if condition_type.get() == "Transfer":
                ttk.Label(param_frame, text="Distance (cm):").grid(row=0, column=0)
                var = tk.StringVar()
                param_vars.append(var)
                ttk.Entry(param_frame, textvariable=var).grid(row=0, column=1)
                
            elif condition_type.get() == "Iris":
                ttk.Label(param_frame, text="Diameter (cm):").grid(row=0, column=0)
                var = tk.StringVar()
                param_vars.append(var)
                ttk.Entry(param_frame, textvariable=var).grid(row=0, column=1)
                
            else:  # Refraction
                ttk.Label(param_frame, text="Focal Length (cm):").grid(row=0, column=0)
                var1 = tk.StringVar()
                param_vars.append(var1)
                ttk.Entry(param_frame, textvariable=var1).grid(row=0, column=1)
                
                ttk.Label(param_frame, text="Diameter (cm):").grid(row=1, column=0)
                var2 = tk.StringVar()
                param_vars.append(var2)
                ttk.Entry(param_frame, textvariable=var2).grid(row=1, column=1)
        
        condition_type.bind('<<ComboboxSelected>>', update_params)
        update_params()  # Initial update
        
        def add_condition():
            try:
                ctype = condition_type.get()
                if ctype == "Transfer":
                    distance = float(param_vars[0].get())
                    self.system.add_transfer(distance)
                    self.current_position += distance
                    self.conditions.append(f"Transfer: {distance}cm")
                elif ctype == "Iris":
                    diam = float(param_vars[0].get())
                    self.system.add_iris(self.current_position, diam)
                    self.conditions.append(f"Iris: pos={self.current_position}cm, diameter={diam}cm")
                else:  # Refraction
                    focal_length = float(param_vars[0].get())
                    diam = float(param_vars[1].get())
                    # Convert focal length to optical power (power = 1/focal_length)
                    power = 1.0 / focal_length
                    self.system.add_refraction(self.current_position, power, diam)
                    self.conditions.append(f"Lens: pos={self.current_position}cm, f={focal_length}cm, diameter={diam}cm")
                self.show_condition_input()  # Refresh with new condition
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid numbers")
            except ZeroDivisionError:
                messagebox.showerror("Error", "Focal length cannot be zero")
        
        def start_tracing():
            self.root.destroy()  # Close GUI
            # Run raytracing's main with our system
            if __name__ == '__main__':
                import raytracing
                raytracing.main(self.system, self.object_height)
        
        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=start_row+2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add Another", command=add_condition).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Start Tracing", command=start_tracing).grid(row=1, column=0, padx=5)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = OpticalSystemGUI()
    app.run()
