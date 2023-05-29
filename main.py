import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askquestion
import pandas as pd
import math
from PIL import Image

radius = 5
class HumanPose(tk.Frame):
    """Illustrate how to drag items on a Tkinter canvas"""

    def __init__(self, parent, image):
        super(HumanPose, self).__init__(parent)
        self.parent = parent
        # default position of 18 keypoints
        default_pos_table = pd.read_csv('assets/default_pos.csv')
        default_pos_norm = list(zip(default_pos_table['x_norm'], default_pos_table['y_norm']))
        # connection of keypoints
        color_codes_df = pd.read_csv('assets/color_codes.csv')
        join_color_codes = color_codes_df['joint_color']
        self.pairs_point = color_codes_df['pair']
        self.pairs_point_color_codes = color_codes_df['pair_color']
        self.width, self.height = image.width(), image.height()
        
        # create a canvas
        self.canvas = tk.Canvas(width=self.width, height=self.height)
        self.canvas.pack(side='top', fill="both", expand=True)
        self.canvas.create_image((0,0), image=image, anchor="nw", tags="image", state='disable')

        # this data is used to keep track of an
        # item being dragged
        self._drag_data = {"x": 0, "y": 0, "item": None}
        self._point_pair = {}
        # create a couple of movable objects
        for i in range(len(default_pos_norm)):
            x = math.floor(default_pos_norm[i][0] * self.width)
            y = math.floor(default_pos_norm[i][1] * self.height)
            color = join_color_codes[i]
            self._point_pair[f"J_{i}"] = []
            self.create_token(x, y, "#"+color, f"J_{i}")
        for i in range(len(self.pairs_point)):
            if isinstance(self.pairs_point[i], str):
                p1_idx, p2_idx = self.pairs_point[i].split(',')
                p1_id = self.canvas.find_withtag('J_'+p1_idx)[0]
                p2_id = self.canvas.find_withtag('J_'+p2_idx)[0]
                p1_coords = self.canvas.coords(p1_id)
                p2_coords = self.canvas.coords(p2_id)
                p1_x = (p1_coords[0] + p1_coords[2])//2
                p1_y = (p1_coords[1] + p1_coords[3])//2
                p2_x = (p2_coords[0] + p2_coords[2])//2
                p2_y = (p2_coords[1] + p2_coords[3])//2
                color = self.pairs_point_color_codes[i]
                self._point_pair['J_'+p1_idx].append(f"P_{p1_idx},{p2_idx}")
                self._point_pair['J_'+p2_idx].append(f"P_{p1_idx},{p2_idx}")
                element = self.canvas.create_line(p1_x, p1_y, p2_x, p2_y, fill=color, width=5, tags=f"P_{p1_idx},{p2_idx}")
                self.canvas.lower(element)
        self.canvas.lower(self.canvas.find_withtag('image')[0])

        # add bindings for clicking, dragging and releasing over
        # any object with the "token" tag
        self.canvas.tag_bind("token", "<ButtonPress-1>", self.drag_start)
        self.canvas.tag_bind("token", "<ButtonRelease-1>", self.drag_stop)
        self.canvas.tag_bind("token", "<B1-Motion>", self.drag)

    def getCenterPoint(self, coords):
        x = (coords[0] + coords[2])//2
        y = (coords[1] + coords[3])//2
        return x,y
    def create_token(self, x, y, color, name=""):
        """Create a token at the given coordinate in the given color"""
        self.canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline=color,
            fill=color,
            tags=("token",name),
        )

    def drag_start(self, event):
        """Begining drag of an object"""
        # record the item and its location
        item_id = self.canvas.find_closest(event.x, event.y)[0]
        if "token" in self.canvas.gettags(item_id):
            self._drag_data["item"] = item_id
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y

    def drag_stop(self, event):
        """End drag of an object"""
        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0
    def drag(self, event):
        target_widget = self.canvas.winfo_containing(event.x_root, event.y_root)
        if target_widget is not None and self._drag_data["item"] is not None:
            """Handle dragging of an object"""
            # compute how much the mouse has moved
            delta_x = event.x - self._drag_data["x"]
            delta_y = event.y - self._drag_data["y"]
            # move the object the appropriate amount
            self.canvas.move(self._drag_data["item"], delta_x, delta_y)
            if len(self.canvas.gettags(self._drag_data["item"])) > 1:
                point_tag = self.canvas.gettags(self._drag_data["item"])[1]
                self.canvas.gettags(self._drag_data["item"])[1]
                connected_lines = self._point_pair[point_tag]
                modified_point = self.canvas.find_withtag(point_tag)
                modified_point_coords = self.canvas.coords(modified_point)
                x_p, y_p = self.getCenterPoint(modified_point_coords)
                for line in connected_lines:
                    modified_line = self.canvas.find_withtag(line)[0]

                    x0, y0, x1, y1 = self.canvas.coords(modified_line)
                    if line.split('_')[1].split(',')[0] == point_tag.split('_')[1]:
                        self.canvas.coords(line, x_p, y_p, x1, y1)
                    else:
                        self.canvas.coords(line,x0, y0, x_p, y_p)
                for i in range(len(self.pairs_point)):
                    if isinstance(self.pairs_point[i], str):
                        p1_idx, p2_idx = self.pairs_point[i].split(',')

                self._drag_data["x"] = event.x
                self._drag_data["y"] = event.y

    def export(self):
        blank = Image.new(mode="RGB", size=(self.width, self.height))
        blank.save("assets/blank.png")
        blank_bg = tk.PhotoImage(file='./assets/blank.png')
        self.canvas.itemconfig(self.canvas.find_withtag('image')[0], image=blank_bg)
        self.canvas.config(bg='black')
        self.canvas.postscript(file="result/pose.eps")
        self.parent.quit()
        # img = Image.open("result/pose.eps")
        # img.save("result/pose.png", "png")



if __name__ == "__main__":
    root = tk.Tk()
    im_path = './assets/man.png'
    loadedIm= tk.PhotoImage(file=im_path')
    humanpose = HumanPose(root, loadedIm)
    humanpose.pack(fill="both", expand=True)


    # download button handler
    def download_clicked(obj):
        result = askquestion(
            title='Save',
            message='Are you sure to save and close app!'
        )
        if result == "yes":
            obj.export()

    download_icon = tk.PhotoImage(file='./assets/download.png')

    download_button = ttk.Button(
        root,
        image=download_icon,
        text='Save',
        compound=tk.LEFT,
        command= lambda obj=humanpose: download_clicked(obj)
    )

    download_button.pack(
        expand=True
    )
    root.resizable(False, False)
    root.mainloop()
