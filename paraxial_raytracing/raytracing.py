import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

class OpticalSystem:
    def __init__(self):
        self.matrices = []
        self.optical_elements = []
        self.object_height = None  # Add object height as class variable
        self.STOP_optic = None
    
    def set_object_height(self, height):
        """Set the object height"""
        self.object_height = height
    
    def add_transfer(self, distance):
        """Add transfer matrix for propagation through free space"""
        # Correct transfer matrix: [[1, distance], [0, 1]]
        # The first element of ray vector is height (y), second is angle (w)
        self.matrices.append(('transfer', np.array([[1, distance], [0, 1]]), distance))
    
    def add_refraction(self, position, power, diameter):
        """Add refraction matrix for thin lens"""
        # Correct refraction matrix: [[1, 0], [-power, 1]]
        # The negative power is because we're using y and w (not y and θ)
        self.matrices.append(('refraction', np.array([[1, 0], [-power, 1]]), 0))
        self.optical_elements.append(('lens', position, diameter))
    
    def add_iris(self, position, diameter):
        """Add iris (aperture stop) at specified position"""
        self.optical_elements.append(('iris', position, diameter))

    def find_marginal_rays(self):
        """Find marginal ray using iterative angle method"""
        def deg_to_rad(deg):
            return deg * np.pi / 180
        
        angle_step = 0.01  # Step size in degrees
        current_angle = angle_step  # Start with first step
        last_successful_path = None
        
        while True:
            path = self.trace_ray(np.tan(deg_to_rad(current_angle)), 0)
            
            all_elements_passed = True
            total_distance = sum(distance for _, _, distance in self.matrices if distance > 0)
            
            if len(path) < 2:
                all_elements_passed = False
            else:
                final_z = path[-1][0]
                if abs(final_z - total_distance) > 1e-10:
                    all_elements_passed = False
                    # Find the optical element at final_z
                    for elem_type, pos, diameter in self.optical_elements:
                        if abs(pos - final_z) < 1e-10:
                            self.STOP_optic = (elem_type, pos, diameter)
                            break
            
            if all_elements_passed:
                last_successful_path = path
                current_angle += angle_step
            else:
                if last_successful_path is not None:
                    return [(current_angle - angle_step, last_successful_path)]
                else:
                    return []
    
    def find_image_position(self, rays):
        """
        Find image position by finding where rays from same height converge
        Returns: (toe_position, toe_height, head_position, head_height)
        If no second convergence point is found, returns (None, None, None, None)
        """
        if self.object_height is None:
            raise ValueError("Object height not set")
            
        def find_convergence(rays_from_point):
            """Find where specific set of rays converge"""
            ray_paths = []
            for w0, y0 in rays_from_point:
                path = np.array(self.trace_ray(w0, y0))
                if len(path) > 1:
                    ray_paths.append(path)
            
            if len(ray_paths) < 2:
                return None, None
            
            # For each z position, find the spread of ray heights
            total_distance = sum(distance for _, _, distance in self.matrices if distance > 0)
            z_positions = np.linspace(0, total_distance, 1000)
            spreads = []  # Store all spreads to find multiple convergence points
            
            for z in z_positions:
                heights = []
                for path in ray_paths:
                    # Find height at this z position by interpolating between points
                    for i in range(len(path) - 1):
                        z1, y1 = path[i]
                        z2, y2 = path[i + 1]
                        if z1 <= z <= z2:
                            # Linear interpolation
                            t = (z - z1) / (z2 - z1)
                            height = y1 + t * (y2 - y1)
                            heights.append(height)
                            break
                
                if heights:
                    # Calculate spread of heights at this z position
                    spread = max(heights) - min(heights)
                    mean_height = np.mean(heights)
                    spreads.append((spread, z, mean_height))
            
            if not spreads:
                return None, None
            
            # Sort spreads to find local minima
            spreads.sort()  # Sort by spread value
            
            # Get the second convergence point (if it exists)
            if len(spreads) >= 2:
                # Find distinct convergence points (separated by at least 1cm)
                distinct_points = [spreads[0]]
                for spread, z, height in spreads[1:]:
                    if abs(z - distinct_points[-1][1]) > 1.0:  # 1cm separation
                        distinct_points.append((spread, z, height))
                        if len(distinct_points) >= 2:
                            # Return second convergence point
                            return distinct_points[1][1], distinct_points[1][2]
            
            # If no second convergence point found, return None
            return None, None
        
        # Separate rays from toe and head
        toe_rays = [(w0, y0) for w0, y0 in rays if abs(y0) < 1e-10]  # rays from base
        head_rays = [(w0, y0) for w0, y0 in rays if abs(y0 - self.object_height) < 1e-10]  # rays from tip
        
        # Find convergence points
        toe_x, toe_y = find_convergence(toe_rays)
        head_x, head_y = find_convergence(head_rays)
        
        return toe_x, toe_y, head_x, head_y
    
    def trace_ray(self, w0, y0):
        """Trace a ray through the optical system"""
        # Ray vector: [y, w] where y is height and w is angle
        ray = np.array([y0, w0])
        path = [(0, y0)]
        current_z = 0
        
        for i, (elem_type, matrix, distance) in enumerate(self.matrices):
            # Apply matrix transformation
            ray = matrix @ ray
            current_z += distance
            
            # Record ray position
            y = ray[0]  # Height is first element
            path.append((current_z, y))
            
            # Check if ray is blocked by any iris
            for elem_type_check, pos, diameter in self.optical_elements:
                if abs(pos - current_z) < 1e-10 and abs(y) > diameter/2:
                    return path
        
        return path

def draw_arrow(plt, position, height, inverted=False):
    """Helper function to draw arrow at any position"""
    trunk_width = height/16
    head_width = trunk_width*1.5
    head_start = height*0.9
    
    if inverted:
        height = -height
        head_start = -head_start
    
    verts = [
        (position, 0),
        (position + trunk_width/2, 0),
        (position + trunk_width/2, head_start),
        (position + head_width, head_start),
        (position, height),
        (position - head_width, head_start),
        (position - trunk_width/2, head_start),
        (position - trunk_width/2, 0),
        (position, 0),
    ]
    codes = [Path.MOVETO] + [Path.LINETO] * 8
    
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='gray', edgecolor='black', alpha=0.3)
    plt.gca().add_patch(patch)

def main(system=None, object_height=None):
    """Main function that can be called with an existing system or create a new one"""
    if system is None:
        # Initial values
        object_height = 4  # cm
        
        # Create optical system
        system = OpticalSystem()
        system.set_object_height(object_height)
        
        # Add optical elements
        system.add_transfer(10)           # Transfer 10cm
        system.add_iris(10, 6)           # Iris with 6cm diameter
        system.add_transfer(2)            # Transfer 2cm
        system.add_refraction(12, 1/6, 6) # Lens with power 1/6 and diameter 6cm
        system.add_transfer(2)            # Transfer 2cm
        system.add_iris(14, 4)           # Iris with 4cm diameter
        system.add_transfer(10)           # Transfer 10cm
    
    # Define rays
    rays = []
    angles = [i * 5 for i in range(-10, 11)]  # 21 angles from -0.1 to 0.1 degrees
    
    # Convert degrees to radians and then to slopes
    slopes = [np.tan(np.radians(angle)) for angle in angles]
    
    # Add rays from head and toe
    for slope in slopes:
        rays.append((slope, system.object_height))
        rays.append((slope, 0))
    
    # Find marginal rays and image position
    marginal_rays = system.find_marginal_rays()
    toe_x, toe_y, head_x, head_y = system.find_image_position(rays)
    print(f"Image position: {toe_x:.2f} cm")
    print(f"Image height: {abs(head_y - toe_y):.2f} cm")
    
    # Create plot
    plt.figure(figsize=(12, 8))
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # Draw object arrow
    draw_arrow(plt, 0, system.object_height)
    
    # Plot optical elements
    for elem_type, pos, diameter in system.optical_elements:
        if elem_type == 'lens':
            plt.axvline(x=pos, color='blue', linestyle='-', alpha=0.5, label='Lens')
            plt.plot([pos, pos], [-diameter/2, diameter/2], 'b-', linewidth=3)
            # Mark STOP if this is the blocking element
            if system.STOP_optic and system.STOP_optic[0] == 'lens' and abs(system.STOP_optic[1] - pos) < 1e-10:
                plt.text(pos, diameter/2, 'STOP', 
                        color='red', fontsize=10,
                        horizontalalignment='right', verticalalignment='bottom',
                        bbox=dict(facecolor='white', edgecolor='red', alpha=0.7))
        else:  # iris
            max_height = max(abs(system.object_height), 6) * 1.5
            plt.plot([pos, pos], [-max_height, -diameter/2], 'r-', linewidth=2, alpha=0.5, label='Iris')
            plt.plot([pos, pos], [diameter/2, max_height], 'r-', linewidth=2, alpha=0.5)
            # Mark STOP if this is the blocking element
            if system.STOP_optic and system.STOP_optic[0] == 'iris' and abs(system.STOP_optic[1] - pos) < 1e-10:
                plt.text(pos, diameter/2, 'STOP', 
                        color='red', fontsize=10,
                        horizontalalignment='right', verticalalignment='bottom',
                        bbox=dict(facecolor='white', edgecolor='red', alpha=0.7))
    
    # Plot regular rays with arrows
    for w0, y0 in rays:
        path = system.trace_ray(w0, y0)
        path = np.array(path)
        
        # Plot each segment with an arrow
        for i in range(len(path)-1):
            x1, y1 = path[i]
            x2, y2 = path[i+1]
            
            # Calculate arrow properties
            dx = x2 - x1
            dy = y2 - y1
            arrow_length = np.sqrt(dx**2 + dy**2)
            
            # Use green for rays from head (y=object_height) and blue for rays from toe (y=0)
            color = 'green' if abs(y0 - system.object_height) < 1e-10 else 'blue'
            
            # Only add arrow if segment is long enough
            if arrow_length > 0.1:
                plt.arrow(x1, y1, dx, dy, 
                         head_width=0.2, head_length=0.3, 
                         fc=color, ec=color, alpha=0.5,
                         length_includes_head=True,
                         label='Regular Ray' if i==0 else "")
    
    # Plot marginal rays with arrows
    for angle, path in marginal_rays:
        path = np.array(path)
        
        # Plot each segment with an arrow
        for i in range(len(path)-1):
            x1, y1 = path[i]
            x2, y2 = path[i+1]
            
            # Calculate arrow properties
            dx = x2 - x1
            dy = y2 - y1
            arrow_length = np.sqrt(dx**2 + dy**2)
            
            # Only add arrow if segment is long enough
            if arrow_length > 0.1:
                plt.arrow(x1, y1, dx, dy, 
                         head_width=0.2, head_length=0.3, 
                         fc='red', ec='red', alpha=0.9, 
                         linewidth=2,
                         length_includes_head=True,
                         label='Marginal Ray' if i==0 else "")
            
    # Draw image arrow between convergence points
    if toe_x is not None and head_x is not None and toe_y is not None and head_y is not None:
        image_height = head_y - toe_y
        draw_arrow(plt, toe_x, image_height)
        
        # Calculate and display magnification
        magnification = abs(image_height / system.object_height)

        # Add text annotations
        plt.text(0, system.object_height + 0.5, f'Object\nHeight: {system.object_height:.1f}cm', 
                horizontalalignment='center', verticalalignment='bottom')
        plt.text(toe_x, head_y + 0.5, f'Image\nHeight: {abs(image_height):.1f}cm\nMagnification: {magnification:.2f}x', 
                horizontalalignment='center', verticalalignment='bottom')
    
    plt.grid(True)
    plt.xlabel('Distance (cm)')
    plt.ylabel('Height (cm)')
    plt.title('Ray Tracing with Marginal Rays')
    
    # Remove duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    
    plt.axis('equal')
    plt.ylim(-system.object_height - 2, system.object_height + 2)
    plt.xlim(-2, 26)
    plt.show()

if __name__ == "__main__":
    main()
