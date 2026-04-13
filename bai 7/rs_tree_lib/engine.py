from typing import List, Dict, Set, Optional
from .models import Segment, Object, Activity, RSTreeNode

def build_rs_tree(segments: List[Segment], start_time: int, end_time: int, min_interval: int = 10) -> RSTreeNode:
    node = RSTreeNode(start=start_time, end=end_time, segments=[], is_leaf=(end_time - start_time) <= min_interval)
    
    for seg in segments:
        if seg.start < end_time and seg.end > start_time:
            node.segments.append(seg)
            for obj in seg.objects:
                node.object_types.add(obj.type)
            for act in seg.activities:
                node.activity_names.add(act.name)
                
    if not node.is_leaf:
        mid = (start_time + end_time) // 2
        node.left = build_rs_tree(segments, start_time, mid, min_interval)
        node.right = build_rs_tree(segments, mid, end_time, min_interval)
        
    return node

def build_object_array(segments: List[Segment]) -> Dict[str, Dict]:
    object_array = {}
    for seg in segments:
        for obj in seg.objects:
            if obj.id not in object_array:
                object_array[obj.id] = {
                    "id": obj.id,
                    "type": obj.type,
                    "name": obj.name,
                    "videos": {seg.video_id},
                    "segments": [seg]
                }
            else:
                object_array[obj.id]["videos"].add(seg.video_id)
                object_array[obj.id]["segments"].append(seg)
    return object_array

# --- 8 Query Functions ---

# i. FindVideoWithObject(o)
def find_video_with_object(object_array: Dict, object_type: str) -> List[str]:
    video_ids = set()
    for obj_id, data in object_array.items():
        if data["type"] == object_type:
            video_ids.update(data["videos"])
    return list(video_ids)

# ii. FindVideoWithActivity(a)
def find_video_with_activity(node: RSTreeNode, activity_name: str) -> List[str]:
    video_ids = set()
    def search(n: RSTreeNode):
        if activity_name not in n.activity_names:
            return
        for seg in n.segments:
            if any(act.name == activity_name for act in seg.activities):
                video_ids.add(seg.video_id)
        if n.left: search(n.left)
        if n.right: search(n.right)
    search(node)
    return list(video_ids)

# iii. FindVideoWithActivityandProp(a,p,z)
def find_video_with_activity_and_prop(node: RSTreeNode, activity_name: str, prop: str, value: str) -> List[str]:
    video_ids = set()
    def search(n: RSTreeNode):
        if activity_name not in n.activity_names:
            return
        for seg in n.segments:
            for act in seg.activities:
                if act.name == activity_name and act.props.get(prop) == value:
                    video_ids.add(seg.video_id)
        if n.left: search(n.left)
        if n.right: search(n.right)
    search(node)
    return list(video_ids)

# iv. FindVideoWithObjectandProp(o,p,z)
def find_video_with_object_and_prop(object_array: Dict, object_type: str, prop: str, value: str) -> List[str]:
    video_ids = set()
    for obj_id, data in object_array.items():
        if data["type"] == object_type:
            for seg in data["segments"]:
                if any(obj.type == object_type and obj.props.get(prop) == value for obj in seg.objects):
                    video_ids.add(seg.video_id)
    return list(video_ids)

# v. FindObjectsInVideo(v,s,e)
def find_objects_in_video(node: RSTreeNode, video_id: str, s: int, e: int) -> List[Object]:
    objects = {}
    def search(n: RSTreeNode):
        if n.start >= e or n.end <= s:
            return
        for seg in n.segments:
            if seg.video_id == video_id and seg.start < e and seg.end > s:
                for obj in seg.objects:
                    objects[obj.id] = obj
        if n.left: search(n.left)
        if n.right: search(n.right)
    search(node)
    return list(objects.values())

# vi. FindActivitiesInVideo(v,s,e)
def find_activities_in_video(node: RSTreeNode, video_id: str, s: int, e: int) -> List[Activity]:
    activities = {}
    def search(n: RSTreeNode):
        if n.start >= e or n.end <= s:
            return
        for seg in n.segments:
            if seg.video_id == video_id and seg.start < e and seg.end > s:
                for act in seg.activities:
                    activities[act.name] = act
        if n.left: search(n.left)
        if n.right: search(n.right)
    search(node)
    return list(activities.values())

# vii. FindActivitiesAndPropsInVideo(v,s,e)
def find_activities_and_props_in_video(node: RSTreeNode, video_id: str, s: int, e: int) -> List[Activity]:
    return find_activities_in_video(node, video_id, s, e)

# viii. FindObjectsAndPropsInVideo(v,s,e)
def find_objects_and_props_in_video(node: RSTreeNode, video_id: str, s: int, e: int) -> List[Object]:
    return find_objects_in_video(node, video_id, s, e)

# ix. Tìm kiếm Boolean (A but not B) - CHỨC NĂNG MỞ RỘNG
def find_video_boolean_search(node: RSTreeNode, query: str) -> List[str]:
    """
    Tìm kiếm video dựa trên điều kiện Boolean (AND/NOT).
    Cú pháp: 'ô tô, người đi bộ, không xe máy, not ô dù'
    """
    if not query: return []
    
    terms = [t.strip() for t in query.split(',')]
    include_terms = set()
    exclude_terms = set()
    negation_keywords = ["not", "không"]
    
    for t in terms:
        is_negated = False
        clean_t = t.lower()
        for kw in negation_keywords:
            if clean_t.startswith(kw + " "):
                is_negated = True
                clean_t = clean_t[len(kw)+1:].strip()
                break
        
        if is_negated: exclude_terms.add(clean_t)
        else: include_terms.add(clean_t)

    # Thu thập toàn bộ nội dung của từng video
    video_contents = {} # video_id -> set của các chuỗi (type/name/act_name)
    
    def collect(n: RSTreeNode):
        for seg in n.segments:
            if seg.video_id not in video_contents:
                video_contents[seg.video_id] = set()
            for obj in seg.objects:
                video_contents[seg.video_id].add(obj.type.lower())
                video_contents[seg.video_id].add(obj.name.lower())
            for act in seg.activities:
                video_contents[seg.video_id].add(act.name.lower())
        if n.left: collect(n.left)
        if n.right: collect(n.right)
        
    collect(node)
    
    results = []
    for vid, content in video_contents.items():
        # Video phải chứa TẤT CẢ các từ khóa include
        # (Kiểm tra xem từ khóa có xuất hiện trong bất kỳ tên/loại nào không)
        match_all_include = True
        for it in include_terms:
            if not any(it in item for item in content):
                match_all_include = False
                break
        
        if not match_all_include: continue
        
        # Video KHÔNG ĐƯỢC chứa bất kỳ từ khóa exclude nào
        match_any_exclude = False
        for et in exclude_terms:
            if any(et in item for item in content):
                match_any_exclude = True
                break
        
        if not match_any_exclude:
            results.append(vid)
            
    return results
