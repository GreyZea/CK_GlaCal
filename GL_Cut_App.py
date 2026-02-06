import streamlit as st
from rectpack import newPacker

# --- 1. ระบบรหัสผ่าน ---
PASSWORD = "CK3006"


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 CK_GlaCal (Stock Optimization)")
        pwd = st.text_input("กรุณาใส่รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง")
        return False
    return True


# --- 2. ฟังก์ชันคำนวณ (เลือกแผ่นที่เหลือเศษน้อยที่สุดต่อแผ่น) ---
def calculate_optimized_stock(stocks, pieces):
    remaining_pieces = sorted(pieces, key=lambda x: x['w'] * x['h'], reverse=True)
    results = []

    while remaining_pieces:
        best_sheet_variant = None
        best_packed_indices = []
        highest_efficiency = -1

        # ลอง "ชิ้นงานที่เหลือทั้งหมด" กับ "สต็อกทุกขนาด"
        for s_item in stocks:
            # ลองทั้งแนวตั้งและแนวนอนของแผ่นสต็อก
            for sw, sh in [(s_item['w'], s_item['h']), (s_item['h'], s_item['w'])]:
                temp_packer = newPacker(rotation=True)
                temp_packer.add_bin(sw, sh)

                for i, p in enumerate(remaining_pieces):
                    temp_packer.add_rect(p['w'], p['h'], rid=i)

                temp_packer.pack()

                if len(temp_packer) > 0:
                    b = temp_packer[0]
                    # คำนวณพื้นที่ที่ใช้จริงในแผ่นนี้
                    current_used_area = sum(r.width * r.height for r in b)
                    # คำนวณความคุ้มค่า (พื้นที่ใช้ / พื้นที่แผ่น)
                    efficiency = current_used_area / (sw * sh)

                    # หัวใจสำคัญ: เลือกแผ่นที่ Efficiency สูงสุด (เหลือเศษน้อยที่สุดในตัวมันเอง)
                    # ไม่ใช่แค่แผ่นที่ยัดงานได้เยอะที่สุด
                    if efficiency > highest_efficiency:
                        highest_efficiency = efficiency
                        best_packed_indices = [r.rid for r in b]
                        best_sheet_variant = {
                            'sw': sw, 'sh': sh,
                            'eff': efficiency,
                            'used_area': current_used_area,
                            'rects': [{'w': r.width, 'h': r.height} for r in b]
                        }

        if not best_sheet_variant:
            break

        results.append(best_sheet_variant)
        # ลบชิ้นงานที่วางไปแล้วออก
        for idx in sorted(best_packed_indices, reverse=True):
            remaining_pieces.pop(idx)

    return results, remaining_pieces


# --- 3. UI ---
st.set_page_config(page_title="GlaCal Stock Optimizer", layout="wide")

if check_password():
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}, {'w': 30.0, 'h': 30.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'งานตัดชุดที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 2}]}]

    with st.sidebar:
        st.title("📦 คลังกระจก (Stock)")
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มขนาดคลัง", on_click=lambda: st.session_state.stocks.append({'w': 20.0, 'h': 20.0}))

    st.title("🖼️ GlaCal Master: ระบบบริหารสต็อก (เลือกแผ่นที่ฟิตที่สุด)")
    st.info("💡 ระบบจะเปรียบเทียบทุกขนาดในคลัง เพื่อเลือกแผ่นที่ 'เหลือเศษน้อยที่สุด' มาใช้ก่อน")

    for p_idx, proj in enumerate(st.session_state.projects):
        with st.container(border=True):
            proj['name'] = st.text_input("ชื่อโปรเจกต์", value=proj['name'], key=f"pname_{p_idx}")

            for i, it in enumerate(proj['items']):
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([0.35, 0.35, 0.2, 0.1])
                    it['w'] = c1.number_input(f"กว้าง", value=float(it['w']), key=f"w_{p_idx}_{i}")
                    it['h'] = c2.number_input(f"สูง", value=float(it['h']), key=f"h_{p_idx}_{i}")
                    it['qty'] = c3.number_input(f"จำนวน", value=int(it['qty']), min_value=1, key=f"q_{p_idx}_{i}")
                    if c4.button("❌", key=f"del_it_{p_idx}_{i}"):
                        proj['items'].pop(i);
                        st.rerun()

            if st.button("➕ เพิ่มชิ้นงาน", key=f"add_it_{p_idx}"):
                proj['items'].append({'w': 10.0, 'h': 10.0, 'qty': 1});
                st.rerun()

            if st.button(f"🚀 คำนวณ (เลือกแผ่นที่ประหยัดที่สุด)", key=f"calc_{p_idx}", type="primary"):
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]
                results, rem = calculate_optimized_stock(st.session_state.stocks, pieces_data)

                if results:
                    st.success(f"📊 สรุป: ใช้กระจกทั้งหมด {len(results)} แผ่น")
                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['sw']}x{s['sh']}", expanded=True):
                                st.write(f"📊 ความคุ้มค่า: **{s['eff'] * 100:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(s['sw'] * s['sh'] - s['used_area']):.2f}** ตร.นิ้ว")
                                st.progress(min(s['eff'], 1.0))
                                for p in s['rects']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
