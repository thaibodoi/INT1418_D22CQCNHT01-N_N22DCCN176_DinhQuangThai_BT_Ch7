import json, pandas as pd, os
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
from rs_tree_lib.models import Segment, Object, Activity
from rs_tree_lib.engine import (
    build_rs_tree, build_object_array,
    find_video_with_object, find_video_with_activity,
    find_video_with_activity_and_prop, find_video_with_object_and_prop,
    find_objects_in_video, find_activities_in_video,
    find_video_boolean_search
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RSTreeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RS-Tree Video Indexer - Giám sát khu phố")
        self.geometry("1200x800")

        # State
        self.current_frame = tk.IntVar(value=0)
        self.is_playing = tk.BooleanVar(value=True)

        # Load Data
        self.load_data()
        
        # UI Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Search)
        self.sidebar = self.create_sidebar()
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 2. Main Content (Cameras + Control)
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Camera Grid
        self.camera_grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.camera_grid.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.camera_grid.grid_columnconfigure((0, 1), weight=1)
        self.camera_grid.grid_rowconfigure((0, 1), weight=1)
        
        self.cameras = []
        for i, video in enumerate(self.video_data["videos"]):
            cam = self.create_camera_view(self.camera_grid, video, i)
            self.cameras.append(cam)

        # Control Panel (Timeline)
        self.control_panel = self.create_control_panel()
        self.control_panel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # 3. Results Panel
        self.results_panel = self.create_results_panel()
        self.results_panel.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # Start Playback Loop
        self.update_playback()

    def load_data(self):
        self.video_data = {"videos": []}
        self.all_segments = []

        # Tự động xác định đường dẫn file data.csv dựa trên vị trí script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(script_dir, "data.csv")
        
        print(f"Loading data from {data_path}...")
        if not os.path.exists(data_path):
            print(f"Error: {data_path} not found!")
            return

        df = pd.read_csv(data_path, encoding="utf-8-sig")
        
        # Nhóm dữ liệu theo VideoID để xử lý từng camera
        for vid_id, group in df.groupby('VideoID'):
            video_name = group.iloc[0]['VideoName']
            video_entry = {"id": vid_id, "name": video_name, "segments": []}
            
            for _, row in group.iterrows():
                objs_data = json.loads(row['Objects'])
                acts_data = json.loads(row['Activities'])
                
                # Tạo các đối tượng model phục vụ thuật toán RS-Tree
                objs = [Object(o["id"], o["type"], o["name"], o["props"]) for o in objs_data]
                acts = [Activity(a["name"], a["props"]) for a in acts_data]
                
                start_f, end_f = int(row['Start']), int(row['End'])
                segment = Segment(vid_id, video_name, start_f, end_f, objs, acts)
                self.all_segments.append(segment)
                
                # Lưu vào video_data phục vụ hiển thị UI
                video_entry["segments"].append({
                    "start": start_f, "end": end_f,
                    "objects": objs_data, "activities": acts_data
                })
            self.video_data["videos"].append(video_entry)
        
        self.rs_tree = build_rs_tree(self.all_segments, 0, 100)
        self.object_array = build_object_array(self.all_segments)

    def create_sidebar(self):
        frame = ctk.CTkFrame(self, width=250, corner_radius=15)
        ctk.CTkLabel(frame, text="THAM SỐ TRUY VẤN", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20, padx=20)
        ctk.CTkLabel(frame, text="Chế độ truy vấn", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), padx=20, anchor="w")
        
        self.query_mode = ctk.CTkOptionMenu(frame, values=[
            "i. Tìm Video theo Đối tượng",
            "ii. Tìm Video theo Hoạt động",
            "iii. Video với Hoạt động & Thuộc tính",
            "iv. Video với Đối tượng & Thuộc tính",
            "v. Liệt kê Đối tượng trong Video",
            "vi. Liệt kê Hoạt động trong Video",
            "vii. Hoạt động & Thuộc tính trong Video",
            "viii. Đối tượng & Thuộc tính trong Video",
            "ix. Tìm kiếm Boolean (A but not B)"
        ], command=self.on_query_mode_change)
        self.query_mode.pack(pady=5, padx=20, fill="x")

        self.input_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.input_container.pack(pady=10, padx=20, fill="both")
        
        self.search_inputs = {}
        self.on_query_mode_change(self.query_mode.get())

        self.search_btn = ctk.CTkButton(frame, text="Truy vấn RS-Tree", font=ctk.CTkFont(weight="bold"), command=self.execute_search)
        self.search_btn.pack(pady=20, padx=20, fill="x", side="bottom")
        return frame

    def on_query_mode_change(self, mode):
        for widget in self.input_container.winfo_children(): widget.destroy()
        self.search_inputs = {}
        
        if mode.startswith("i.") or mode.startswith("iv.") or mode.startswith("v.") or mode.startswith("viii."):
            self.add_input("Loại đối tượng:", "search_obj", "ô tô")
        if mode.startswith("ii.") or mode.startswith("iii.") or mode.startswith("vi.") or mode.startswith("vii."):
            self.add_input("Hoạt động:", "search_act", "sang đường")
        if mode.startswith("iii.") or mode.startswith("iv."):
            self.add_input("Thuộc tính:", "search_prop", "màu sắc")
            self.add_input("Giá trị:", "search_val", "đỏ")
        if any(mode.startswith(x) for x in ["v.", "vi.", "vii.", "viii."]):
            self.add_input("Video ID:", "target_vid", "cam-01")
            self.add_input("Frame đầu:", "start_f", "10")
            self.add_input("Frame cuối:", "end_f", "50")
        if mode.startswith("ix."):
            self.add_input("Truy vấn Boolean:", "search_boolean", "ô tô, không xe máy")
            ctk.CTkLabel(self.input_container, text="* Dùng dấu phẩy ngăn cách. Ví dụ: 'ô tô, không xe máy'", font=ctk.CTkFont(size=9), text_color="gray").pack(anchor="w")

    def add_input(self, label, key, default):
        ctk.CTkLabel(self.input_container, text=label, font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", pady=(5,0))
        entry = ctk.CTkEntry(self.input_container, placeholder_text=default)
        entry.insert(0, default)
        entry.pack(fill="x", pady=2)
        self.search_inputs[key] = entry

    def create_camera_view(self, parent, video, index):
        frame = ctk.CTkFrame(parent, corner_radius=15, border_width=1, border_color="#333")
        frame.grid(row=index // 2, column=index % 2, padx=5, pady=5, sticky="nsew")
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=video["name"], font=ctk.CTkFont(weight="bold")).pack(side="left")
        rec_label = ctk.CTkLabel(header, text="● REC", text_color="#ff4444", font=ctk.CTkFont(size=10, weight="bold"))
        rec_label.pack(side="right")
        display = tk.Canvas(frame, bg="#000", highlightthickness=0)
        display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        return {"canvas": display, "video": video, "rec": rec_label}

    def create_control_panel(self):
        frame = ctk.CTkFrame(self.main_frame, height=80)
        self.play_btn = ctk.CTkButton(frame, text="⏸", width=40, command=self.toggle_playback)
        self.play_btn.pack(side="left", padx=10)
        self.slider = ctk.CTkSlider(frame, from_=0, to=99, variable=self.current_frame, command=self.on_slider_move)
        self.slider.pack(side="left", fill="x", expand=True, padx=10)
        self.frame_label = ctk.CTkLabel(frame, text="0:00", font=ctk.CTkFont(family="Courier", size=14, weight="bold"))
        self.frame_label.pack(side="right", padx=10)
        return frame

    def create_results_panel(self):
        frame = ctk.CTkFrame(self.main_frame, height=150)
        ctk.CTkLabel(frame, text="KẾT QUẢ TRUY VẤN", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        self.results_text = ctk.CTkTextbox(frame, height=100)
        self.results_text.pack(fill="both", expand=True, padx=10, pady=5)
        return frame

    def toggle_playback(self):
        self.is_playing.set(not self.is_playing.get())
        self.play_btn.configure(text="⏸" if self.is_playing.get() else "▶")

    def on_slider_move(self, val): self.update_cameras()

    def update_playback(self):
        if self.is_playing.get():
            self.current_frame.set((self.current_frame.get() + 1) % 100)
            self.update_cameras()
        self.after(200, self.update_playback)

    def update_cameras(self):
        frame_idx = self.current_frame.get()
        self.frame_label.configure(text=f"0:{frame_idx:02d}")
        for cam in self.cameras:
            canvas = cam["canvas"]
            video = cam["video"]
            canvas.delete("all")
            w, h = canvas.winfo_width(), canvas.winfo_height()
            canvas.create_line(0, h//2, w, h//2, fill="#111")
            canvas.create_line(w//2, 0, w//2, h, fill="#111")
            y_off, act_y_off = 20, h - 20
            for seg in video["segments"]:
                if seg["start"] <= frame_idx <= seg["end"]:
                    for obj in seg["objects"]:
                        canvas.create_text(10, y_off, text=f"[{obj['type'].upper()}] {obj['name']}", fill="#8b5cf6", anchor="nw", font=("Arial", 10, "bold"))
                        y_off += 20
                    for act in seg["activities"]:
                        canvas.create_text(w-10, act_y_off, text=f"ACT: {act['name']}", fill="#10b981", anchor="se", font=("Arial", 9, "italic"))
                        act_y_off -= 20
            cam["rec"].configure(text_color="#ff4444" if frame_idx % 4 < 2 else "#333")

    def execute_search(self):
        mode = self.query_mode.get()
        i = {k: v.get() for k, v in self.search_inputs.items()}
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", f"Đang thực thi {mode}...\n" + "-"*30 + "\n")
        try:
            if mode.startswith("i."): self.print_videos(find_video_with_object(self.object_array, i["search_obj"]))
            elif mode.startswith("ii."): self.print_videos(find_video_with_activity(self.rs_tree, i["search_act"]))
            elif mode.startswith("iii."): self.print_videos(find_video_with_activity_and_prop(self.rs_tree, i["search_act"], i["search_prop"], i["search_val"]))
            elif mode.startswith("iv."): self.print_videos(find_video_with_object_and_prop(self.object_array, i["search_obj"], i["search_prop"], i["search_val"]))
            elif mode.startswith("v.") or mode.startswith("viii."):
                res = find_objects_in_video(self.rs_tree, i["target_vid"], int(i["start_f"]), int(i["end_f"]))
                f = i.get("search_obj", "").strip().lower()
                for o in res:
                    if not f or f in o.type.lower() or f in o.name.lower():
                        p = f" - Thuộc tính: {o.props}" if mode.startswith("viii.") else ""
                        self.results_text.insert("end", f"• {o.name} ({o.type}){p}\n")
            elif mode.startswith("vi.") or mode.startswith("vii."):
                res = find_activities_in_video(self.rs_tree, i["target_vid"], int(i["start_f"]), int(i["end_f"]))
                f = i.get("search_act", "").strip().lower()
                for a in res:
                    if not f or f in a.name.lower():
                        p = f" - Thuộc tính: {a.props}" if mode.startswith("vii.") else ""
                        self.results_text.insert("end", f"• Hoạt động: {a.name}{p}\n")
            elif mode.startswith("ix."):
                self.print_videos(find_video_boolean_search(self.rs_tree, i["search_boolean"]))
        except Exception as e: self.results_text.insert("end", f"Lỗi: {str(e)}")

    def print_videos(self, ids):
        if not ids: self.results_text.insert("end", "Không tìm thấy video nào.")
        else:
            for vid in ids:
                name = next((v["name"] for v in self.video_data["videos"] if v["id"] == vid), vid)
                self.results_text.insert("end", f"✔ TÌM THẤY TRONG: {name} ({vid})\n")

if __name__ == "__main__":
    RSTreeApp().mainloop()
