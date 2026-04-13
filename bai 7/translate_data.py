import pandas as pd
import json

df = pd.read_csv('data.csv', encoding='utf-8-sig')

translation_map = {
    'oto': 'ô tô',
    'xe-may': 'xe máy',
    'xe-dap': 'xe đạp',
    'nguoi': 'người',
    'cho': 'chó',
    'meo': 'mèo',
    'do': 'đỏ',
    'xanh': 'xanh',
    'trắng': 'trắng',
    'đen': 'đen',
    'vàng': 'vàng',
    'chay-thang': 'chạy thẳng',
    're-trai': 'rẽ trái',
    'sang-duong': 'sang đường',
    'dat-cho-di-dao': 'dắt chó đi dạo',
    'tap-the-duc': 'tập thể dục',
    'san-moi': 'săn mồi',
    'do-xe': 'đỗ xe',
    'leo-rao': 'leo rào',
    'tuoi-cay': 'tưới cây',
    'dung-xe': 'dừng xe',
    'mua-sam': 'mua sắm',
    'di-ngang-qua': 'đi ngang qua',
    'Nga tu Main & Oak': 'Ngã tư Chính & Oak',
    'Cong vien Green Park': 'Công viên Xanh',
    'Khu dan cu Sunrise': 'Khu dân cư Sunrise',
    'Cua hang tien loi 24/7': 'Cửa hàng tiện lợi 24/7',
    'color': 'màu sắc',
    'speed': 'tốc độ',
    'fast': 'nhanh',
    'medium': 'vừa',
    'direction': 'hướng',
    'north': 'phía bắc',
    'lane': 'làn đường',
    'inner': 'trong',
    'location': 'vị trí',
    'crosswalk': 'vạch kẻ đường',
    'breed': 'giống',
    'brown': 'nâu',
    'action': 'hành động',
    'walking': 'đang đi bộ',
    'leash': 'xích',
    'intensity': 'cường độ',
    'high': 'cao',
    'status': 'trạng thái',
    'stray': 'thả rông',
    'target': 'mục tiêu',
    'bird': 'con chim',
    'brand': 'nhãn hiệu',
    'eyes': 'mắt',
    'green': 'xanh lá',
    'height': 'độ cao',
    'hat': 'mũ',
    'age': 'tuổi',
    'senior': 'cao tuổi',
    'tool': 'công cụ',
    'hose': 'vòi nước',
    'duration': 'thời lượng',
    'short': 'ngắn',
    'bag': 'túi',
    'shopping': 'mua sắm',
    'blue': 'xanh dương',
    'item': 'mặt hàng',
    'groceries': 'thực phẩm',
    'west': 'phía tây',
    'white': 'trắng',
    'black': 'đen',
    'red': 'đỏ',
    'yellow': 'vàng'
}

def translate_data_item(data_list):
    for item in data_list:
        if 'type' in item:
            item['type'] = translation_map.get(item['type'], item['type'])
        if 'name' in item:
            item['name'] = translation_map.get(item['name'], item['name'])
        if 'props' in item:
            new_props = {}
            for k, v in item['props'].items():
                new_k = translation_map.get(k, k)
                new_v = translation_map.get(v, v)
                new_props[new_k] = new_v
            item['props'] = new_props
    return data_list

# Apply translation
df['VideoName'] = df['VideoName'].map(lambda x: translation_map.get(x, x))
df['Objects'] = df['Objects'].apply(lambda x: json.dumps(translate_data_item(json.loads(x)), ensure_ascii=False))
df['Activities'] = df['Activities'].apply(lambda x: json.dumps(translate_data_item(json.loads(x)), ensure_ascii=False))

df.to_csv('data.csv', index=False, encoding='utf-8-sig')
print("Dịch thành công dữ liệu sang Tiếng Việt!")
